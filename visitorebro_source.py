"""Visit Örebro source adapter.

Kept isolated from the production loader until parser fixtures/guardrails pass.
The calendar is a curated public discovery source; this adapter only emits
records when it can establish a title and a real calendar date.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Event, SourceRecord
from taxonomy import classify

CALENDAR_URL = "https://www.visitorebro.se/evenemangskalender/"
SOURCE_NAME = "Visit Örebro"

MONTHS = {
    "jan": 1, "januari": 1, "feb": 2, "februari": 2, "mar": 3, "mars": 3,
    "apr": 4, "april": 4, "maj": 5, "jun": 6, "juni": 6, "jul": 7, "juli": 7,
    "aug": 8, "augusti": 8, "sep": 9, "september": 9, "okt": 10, "oktober": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _date_from_text(text: str, *, default_year: int | None = None):
    """Parse explicit Swedish dates only; never guess a missing day/month."""
    if not text:
        return None
    default_year = default_year or datetime.now().year
    clean = " ".join(text.lower().replace("–", "-").split())
    iso = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", clean)
    if iso:
        try:
            return datetime(int(iso.group(1)), int(iso.group(2)), int(iso.group(3))).date().isoformat()
        except ValueError:
            return None
    sw = re.search(r"\b(\d{1,2})\s+(jan(?:uari)?|feb(?:ruari)?|mar(?:s)?|apr(?:il)?|maj|jun(?:i)?|jul(?:i)?|aug(?:usti)?|sep(?:tember)?|okt(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+(20\d{2}))?\b", clean)
    if not sw:
        return None
    day = int(sw.group(1)); month = MONTHS.get(sw.group(2)); year = int(sw.group(3) or default_year)
    try:
        return datetime(year, month, day).date().isoformat()
    except (TypeError, ValueError):
        return None


def parse_visitorebro_html(html: str, *, page_url: str = CALENDAR_URL, default_year: int | None = None):
    """Conservative HTML fallback parser.

    It intentionally prefers missing an item over manufacturing an event. Only
    links/cards with an explicit date in their own local text are accepted.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    events = []
    seen = set()
    for link in soup.find_all("a", href=True):
        href = urljoin(page_url, link.get("href"))
        if "visitorebro.se" not in href:
            continue
        card = link
        for _ in range(4):
            if card.parent is None:
                break
            card = card.parent
            text = " ".join(card.get_text(" ", strip=True).split())
            if len(text) >= 20:
                break
        text = " ".join(card.get_text(" ", strip=True).split())
        start_date = _date_from_text(text, default_year=default_year)
        title = " ".join(link.get_text(" ", strip=True).split())
        if not title or len(title) < 3 or not start_date:
            continue
        identity = (title.casefold(), start_date, href)
        if identity in seen:
            continue
        seen.add(identity)
        classification = classify(title, text, "Evenemang", "Okategoriserat")
        ext = hashlib.sha1(f"{title}|{start_date}|{href}".encode("utf-8")).hexdigest()[:20]
        events.append(Event(
            id=f"visitorebro-{ext}", title=title,
            event_type=classification.event_type, category=classification.category,
            start_date=start_date, end_date=None, start_time=None,
            venue="", city="Örebro", region="Örebro", country="Sverige",
            image_url=None, official_url=href, ticket_url=None, status="confirmed",
            source_names=[SOURCE_NAME], source_count=1,
            source_records=[SourceRecord(source=SOURCE_NAME, external_id=ext, source_url=href, fetched_at=_now_iso(), raw_title=title)],
            verified_at=_now_iso(), created_at=_now_iso(), updated_at=_now_iso(),
            description=text[:1200], tags=classification.tags, is_demo=False,
            data_quality="partial", quality_notes=["Datum och titel hämtade från Visit Örebros publika kalender; detaljuppgifter kan saknas."],
        ))
    return events


def visitorebro_events(timeout=20):
    headers = {"User-Agent": "Upplevio/0.92 (+public event discovery)"}
    response = requests.get(CALENDAR_URL, timeout=timeout, headers=headers)
    response.raise_for_status()
    events = parse_visitorebro_html(response.text, page_url=response.url)
    return events, {
        "status": "OK" if events else "Tom",
        "count": len(events),
        "url": response.url,
        "parser": "conservative-html",
    }
