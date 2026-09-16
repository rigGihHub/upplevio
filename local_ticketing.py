from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Event, SourceRecord
from taxonomy import classify


MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "maj": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12,
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _classify_listing(title: str, venue: str):
    """Use only explicit wording and strong venue signals from the result tile."""
    cls = classify(title, venue, "Evenemang", "Lokalt")
    if cls.event_type != "Evenemang" or cls.category != "Lokalt":
        return cls
    text = f"{title} {venue}".casefold()
    if any(word in text for word in ("middag", "vinprovning", "ölprovning", "matmarknad")):
        cls.event_type = cls.category = "Mat & dryck"
    elif any(word in text for word in ("ritz", "nattklubb", "klubbkväll", "dj ", "danskväll", "dansband")):
        cls.event_type = cls.category = "Nattliv"
    elif any(word in text for word in ("rockbar", "jazz", "konsert", "live", " late night jam", "jam ")):
        cls.event_type = "Konsert"
        cls.category = "Musik"
    elif "dockteater" in text:
        cls.event_type = cls.category = "Teater"
    return cls


def parse_tickster_orebro_html(html_text: str, *, source_url: str) -> list[Event]:
    """Parse Tickster's public Örebro result tiles without guessing details."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    events = []
    seen = set()
    for tile in soup.select(".c-tile[data-requestcode]"):
        title_node = tile.select_one(".c-tile__title")
        label_node = tile.select_one(".c-tile__label")
        head = tile.select_one("a.c-tile__head[href]")
        if not title_node or not label_node or not head:
            continue
        title = re.sub(r"\s+", " ", title_node.get_text(" ", strip=True)).strip()
        label = re.sub(r"\s+", " ", label_node.get_text(" ", strip=True)).strip()
        match = re.fullmatch(r"(\d{1,2})\s+([a-zåäö]{3})\s+(20\d{2}),\s*(.+)", label, re.I)
        if not title or not match or match.group(2).lower() not in MONTHS:
            continue
        location = match.group(4).strip()
        if "örebro" not in location.casefold():
            continue
        start_date = f"{int(match.group(3)):04d}-{MONTHS[match.group(2).lower()]:02d}-{int(match.group(1)):02d}"
        venue = re.sub(r",?\s*örebro\s*$", "", location, flags=re.I).strip(" ,") or "Örebro"
        official_url = urljoin(source_url, head.get("href"))
        buy = tile.select_one('a[href*="tickster.com"], a.c-button[href]')
        ticket_url = urljoin(source_url, buy.get("href")) if buy else None
        request_code = (tile.get("data-requestcode") or "").strip()
        identity = request_code or f"{title}|{start_date}|{venue}"
        if identity in seen:
            continue
        seen.add(identity)
        cls = _classify_listing(title, venue)
        stamp = _now()
        events.append(Event(
            id="tickster-orebro-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:20],
            title=title, event_type=cls.event_type, category=cls.category,
            start_date=start_date, end_date=None, start_time=None,
            venue=venue, city="Örebro", region="Örebro län", country="Sverige",
            official_url=official_url, ticket_url=ticket_url, status="confirmed",
            source_names=["Tickster Örebro"], source_count=1,
            source_records=[SourceRecord(source="Tickster Örebro", external_id=identity, source_url=official_url, fetched_at=stamp, raw_title=title)],
            verified_at=stamp, created_at=stamp, updated_at=stamp,
            description="", tags=cls.tags, is_demo=False, data_quality="source_verified",
            quality_notes=["Importerad från Ticksters publika Örebro-lista", "Tid och pris lämnas okända när de inte visas i listningen"],
            price_status="unknown",
        ))
    return events


def tickster_orebro_events() -> list[Event]:
    url = "https://www.tickster.com/se/sv/events/in/%C3%B6rebro"
    response = requests.get(url, timeout=10, headers={"User-Agent": "Upplevio/0.84 (+event discovery)"})
    response.raise_for_status()
    return parse_tickster_orebro_html(response.text, source_url=url)
