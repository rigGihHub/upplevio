from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import re

import requests
from bs4 import BeautifulSoup

from models import Event, SourceRecord
from source_registry import source_by_key

_MONTHS = {
    "januari": 1, "februari": 2, "mars": 3, "april": 4, "maj": 5, "juni": 6,
    "juli": 7, "augusti": 8, "september": 9, "oktober": 10, "november": 11, "december": 12,
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _stable_id(value: str) -> str:
    return "lovorebro-" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:20]


def _parse_date_range(text: str, year: int) -> tuple[str, str | None] | None:
    text = re.sub(r"\s+", " ", (text or "").strip()).lower()
    single = re.fullmatch(r"(\d{1,2})\s+([a-zåäö]+)", text)
    if single:
        month = _MONTHS.get(single.group(2))
        if not month:
            return None
        d = date(year, month, int(single.group(1)))
        return d.isoformat(), None
    span = re.fullmatch(r"(\d{1,2})(?:\s+([a-zåäö]+))?\s*[–-]\s*(\d{1,2})\s+([a-zåäö]+)", text)
    if not span:
        return None
    end_month = _MONTHS.get(span.group(4))
    start_month = _MONTHS.get(span.group(2)) if span.group(2) else end_month
    if not start_month or not end_month:
        return None
    start = date(year, start_month, int(span.group(1)))
    end = date(year, end_month, int(span.group(3)))
    return start.isoformat(), end.isoformat()


def parse_lov_orebro_html(html_text: str, *, source_url: str, year: int) -> list[Event]:
    """Parse activity cards from Örebro municipality's Lov Örebro calendar.

    The listing is intentionally used as a discovery source. We only retain title,
    short listing summary, date range and explicit free status/categories. Missing
    price never becomes free. Activities without a parseable date are ignored.
    """
    soup = BeautifulSoup(html_text or "", "html.parser")
    headings = soup.find_all(["h3", "h4"])
    out: list[Event] = []
    seen: set[tuple[str, str]] = set()
    source = source_by_key("lov_orebro")
    source_name = source.name if source else "Lov Örebro"

    for h in headings:
        title = re.sub(r"\s+", " ", h.get_text(" ", strip=True)).strip()
        if not title or title.lower() in {"lov örebro", "tips på fler aktiviteter"}:
            continue
        block_parts: list[str] = []
        node = h.previous_sibling
        # Capture a nearby label line such as "Gratis Idrott och rörelse".
        for _ in range(3):
            if node is None:
                break
            if getattr(node, "get_text", None):
                t = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
                if t:
                    block_parts.insert(0, t)
            node = node.previous_sibling
        node = h.next_sibling
        while node is not None:
            name = getattr(node, "name", None)
            if name in {"h3", "h4"}:
                break
            if getattr(node, "get_text", None):
                t = re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()
                if t:
                    block_parts.append(t)
            node = node.next_sibling
        block = " ".join(block_parts)
        date_match = re.search(r"\b\d{1,2}(?:\s+[a-zåäö]+)?\s*[–-]\s*\d{1,2}\s+[a-zåäö]+\b|\b\d{1,2}\s+[a-zåäö]+\b", block, re.I)
        if not date_match:
            continue
        parsed = _parse_date_range(date_match.group(0), year)
        if not parsed:
            continue
        start_date, end_date = parsed
        key = (title.casefold(), start_date)
        if key in seen:
            continue
        seen.add(key)

        is_free = bool(re.search(r"\bgratis\b", block, re.I))
        categories = []
        for label in ["Lek och spel", "Idrott och rörelse", "Djur och natur", "Föreställning", "Kultur och kreativitet", "Musik och dans"]:
            if label.casefold() in block.casefold():
                categories.append(label)
        # Keep description deliberately short; listing text is a lead, not copied article content.
        desc = ""
        for p in h.find_all_next("p", limit=2):
            txt = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
            if txt and not re.search(r"\d{1,2}\s+[a-zåäö]+", txt, re.I):
                desc = txt[:240]
                break

        ext = f"{title}|{start_date}|{end_date or ''}"
        out.append(Event(
            id=_stable_id(ext), title=title, event_type="Aktivitet", category="Familj & lokalt",
            start_date=start_date, end_date=end_date, start_time=None,
            venue="", city="Örebro", region="Örebro län", country="Sverige",
            official_url=source_url, status="confirmed",
            source_names=[source_name], source_count=1,
            source_records=[SourceRecord(source=source_name, external_id=ext, source_url=source_url, fetched_at=_now_iso(), raw_title=title)],
            verified_at=_now_iso(), created_at=_now_iso(), updated_at=_now_iso(),
            description=desc, tags=["Familj", "Barn", *categories], is_demo=False,
            data_quality="source_verified",
            quality_notes=["Officiell kommunal lovkalender; plats kan behöva detaljverifieras innan exakt avstånd visas"],
            price_status="free" if is_free else "unknown",
        ))
    return out


def lov_orebro_events(*, today: date | None = None) -> list[Event]:
    today = today or date.today()
    url = "https://guide.orebro.se/lovorebro/"
    r = requests.get(url, timeout=20, headers={"User-Agent": "Upplevio/0.20 (+event discovery prototype)"})
    r.raise_for_status()
    rows = parse_lov_orebro_html(r.text, source_url=url, year=today.year)
    # Keep future and currently ongoing activities. Expired seasonal rows must not leak into discovery.
    return [e for e in rows if date.fromisoformat(e.end_date or e.start_date) >= today]
