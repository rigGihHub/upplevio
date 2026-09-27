"""Conservative parser for dated Visit Örebro editorial event lists.

These pages are useful complements to the client-side calendar because the
published article body contains explicit date + title rows. We only accept
simple list-like lines and never turn surrounding prose into events.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from models import Event, SourceRecord
from taxonomy import classify

SOURCE_NAME = "Visit Örebro redaktion"
ARTICLE_URLS = (
    "https://www.visitorebro.se/artikel/sevart-scen-orebro/",
    "https://www.visitorebro.se/artikel/lopp-och-tavlingar-i-orebro/",
)
MONTHS = {
    "jan":1,"feb":2,"mar":3,"apr":4,"maj":5,"jun":6,"jul":7,"aug":8,
    "sep":9,"okt":10,"nov":11,"dec":12,
}
ROW_RE = re.compile(
    r"^\s*(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?\s*/\s*(\d{1,2})\s+(.+?)\s*$"
)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _article_year(soup, default_year=None):
    text = " ".join(soup.get_text(" ", strip=True).split())
    m = re.search(r"Uppdaterad\s+(20\d{2})-", text, re.I)
    if not m:
        m = re.search(r"\b(20\d{2})\b", text)
    return int(m.group(1)) if m else (default_year or datetime.now().year)


def _clean_title(raw):
    # Venue/free-entry notes are valuable context, but title identity should stay
    # compact. Split only on the first sentence boundary; never invent a venue.
    raw = " ".join((raw or "").split()).strip(" .")
    return raw.split(". ", 1)[0].strip()


def parse_editorial_html(html, *, page_url, default_year=None):
    host = (urlparse(page_url).hostname or "").lower()
    if host != "www.visitorebro.se" and not host.endswith(".visitorebro.se"):
        return []
    soup = BeautifulSoup(html or "", "html.parser")
    year = _article_year(soup, default_year)
    events, seen = [], set()

    # Text nodes preserve editorial line boundaries better than page-wide text.
    for node in soup.find_all(string=True):
        line = " ".join(str(node).split())
        m = ROW_RE.match(line)
        if not m:
            continue
        day1, day2, month, rest = m.groups()
        try:
            start = datetime(year, int(month), int(day1)).date().isoformat()
            end = datetime(year, int(month), int(day2)).date().isoformat() if day2 else None
        except ValueError:
            continue
        title = _clean_title(rest)
        if len(title) < 3:
            continue
        key = (title.casefold(), start, end)
        if key in seen:
            continue
        seen.add(key)
        c = classify(title, rest, "Evenemang", "Okategoriserat")
        ext = hashlib.sha1(f"{title}|{start}|{end or ''}|{page_url}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"visitorebro-editorial-{ext}", title=title,
            event_type=c.event_type, category=c.category,
            start_date=start, end_date=end, start_time=None,
            venue="", city="Örebro", region="Örebro", country="Sverige",
            image_url=None, official_url=page_url, ticket_url=None, status="confirmed",
            source_names=[SOURCE_NAME], source_count=1,
            source_records=[SourceRecord(source=SOURCE_NAME, external_id=ext, source_url=page_url, fetched_at=_now_iso(), raw_title=title)],
            verified_at=_now_iso(), created_at=_now_iso(), updated_at=_now_iso(),
            description=rest[:1200], tags=c.tags, is_demo=False,
            data_quality="partial",
            quality_notes=["Explicit datum och titel hämtade från Visit Örebros redaktionella evenemangslista; detaljsida kan saknas."],
        ))
    return events


def visitorebro_editorial_events(timeout=20):
    all_events, health = [], []
    headers = {"User-Agent": "Upplevio/0.92 (+public event discovery)"}
    for url in ARTICLE_URLS:
        try:
            r = requests.get(url, timeout=timeout, headers=headers)
            r.raise_for_status()
            rows = parse_editorial_html(r.text, page_url=r.url)
            all_events.extend(rows)
            health.append({"url": r.url, "status": "OK" if rows else "Tom", "count": len(rows)})
        except Exception as exc:
            health.append({"url": url, "status": "Fel", "count": 0, "error": type(exc).__name__})
    unique = {}
    for e in all_events:
        unique[(e.title.casefold(), e.start_date, e.end_date)] = e
    return list(unique.values()), health
