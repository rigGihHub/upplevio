"""Visit Örebro source adapter.

Isolated from production until source-shape tests pass. The public calendar is
curated, but its current landing page can be mostly descriptive text while event
entries are supplied elsewhere/client-side. We therefore fail closed: no event
is emitted unless title + explicit date are present in the same local card.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urljoin, urlparse

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
GENERIC_TITLES = {
    "evenemang", "evenemangskalender", "läs mer", "mer information", "visit örebro",
    "vad händer i örebro", "visa mer", "se alla", "öppna", "boka",
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _date_from_text(text: str, *, default_year: int | None = None):
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
    day, month = int(sw.group(1)), MONTHS.get(sw.group(2))
    year = int(sw.group(3) or default_year)
    try:
        return datetime(year, month, day).date().isoformat()
    except (TypeError, ValueError):
        return None


def _is_internal_visitorebro(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == "visitorebro.se" or host.endswith(".visitorebro.se")


def _usable_title(title: str) -> bool:
    clean = " ".join((title or "").split())
    return len(clean) >= 3 and clean.casefold() not in GENERIC_TITLES


def parse_visitorebro_html(html: str, *, page_url: str = CALENDAR_URL, default_year: int | None = None):
    """Parse only self-contained dated event cards; never infer from page-wide text."""
    soup = BeautifulSoup(html or "", "html.parser")
    events, seen = [], set()
    for link in soup.find_all("a", href=True):
        href = urljoin(page_url, link.get("href"))
        if not _is_internal_visitorebro(href):
            continue
        title = " ".join(link.get_text(" ", strip=True).split())
        if not _usable_title(title):
            continue

        # Restrict context to a compact ancestor. Large containers can accidentally
        # combine a navigation link with a date belonging to another event.
        card = link
        local_text = title
        for _ in range(3):
            parent = card.parent
            if parent is None:
                break
            candidate = " ".join(parent.get_text(" ", strip=True).split())
            if len(candidate) > 700:
                break
            card = parent
            local_text = candidate
            if _date_from_text(local_text, default_year=default_year):
                break

        start_date = _date_from_text(local_text, default_year=default_year)
        if not start_date:
            continue
        identity = (title.casefold(), start_date, href)
        if identity in seen:
            continue
        seen.add(identity)
        classification = classify(title, local_text, "Evenemang", "Okategoriserat")
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
            description=local_text[:1200], tags=classification.tags, is_demo=False,
            data_quality="partial", quality_notes=["Titel och uttryckligt datum verifierade i samma lokala Visit Örebro-kort; övriga detaljer kan saknas."],
        ))
    return events


def visitorebro_events(timeout=20):
    headers = {"User-Agent": "Upplevio/0.92 (+public event discovery)"}
    response = requests.get(CALENDAR_URL, timeout=timeout, headers=headers)
    response.raise_for_status()
    events = parse_visitorebro_html(response.text, page_url=response.url)
    return events, {
        "status": "OK" if events else "Tom",
        "count": len(events), "url": response.url,
        "parser": "conservative-local-card-html",
        "note": "Tomt resultat är tillåtet när landningssidan saknar server-renderade daterade eventkort.",
    }
