"""Visit Stockholm's documented public-v1 API (CC BY 4.0).

The live API uses localized dictionaries and integer pagination despite the
schema's string fields. No image rights, prices or opening times are inferred.
"""
from datetime import date, datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import math
import re

import requests
from bs4 import BeautifulSoup

from models import Event, SourceRecord

API_URL = "https://api.visitstockholm.com/api/public-v1/events/"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
ATTRIBUTION = "Stockholm Business Region AB · CC BY 4.0 · Uppgifter normaliserade av Upplevio"


def _localized(value):
    if isinstance(value, dict):
        value = value.get("sv") or value.get("en") or ""
    return value.strip() if isinstance(value, str) else ""


def _date(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        return None


def _clock(value):
    if isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value):
        return value[:5]
    return None


def _url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username else None


def _coordinate(value, limit):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and abs(number) <= limit else None
    except (TypeError, ValueError):
        return None


def parse_stockholm_event(raw):
    if not isinstance(raw, dict):
        return []
    title, external_id = _localized(raw.get("title")), str(raw.get("id") or "")
    city = _localized(raw.get("city"))
    if not title or not external_id or not city:
        return []
    slug = raw.get("url") or ""
    info_url = f"https://www.visitstockholm.com/events/{slug}/" if isinstance(slug, str) and re.fullmatch(r"[\w-]+", slug) else None
    info_url = info_url or _url(raw.get("external_website_url"))
    if not info_url:
        return []
    categories = [c.get("slug") for c in raw.get("categories", []) if isinstance(c, dict)]
    category_types = {
        "exhibitions": "Utställning", "music": "Konsert", "sports": "Sport",
        "stage-film": "Scen & film", "guided-tours": "Guidning",
        "family": "Familj", "food-drink": "Mat & dryck", "markets": "Marknad",
    }
    kind = next((category_types[c] for c in categories if c in category_types), "Evenemang")
    description = BeautifulSoup(_localized(raw.get("description")), "html.parser").get_text(" ", strip=True)
    schedule = raw.get("schedule")
    occurrences = []
    ranges = []
    if isinstance(schedule, dict):
        span = schedule.get("range")
        if isinstance(span, dict):
            start, end = _date(span.get("start")), _date(span.get("end"))
            if start and end and start <= end:
                excluded = sorted({d for v in span.get("excluded", []) if (d := _date(v)) and start <= d <= end})
                occurrences.append((start, end, None, None, excluded))
        ranges = list(occurrences)
        for item in schedule.get("dates", []) or []:
            if not isinstance(item, dict) or not (day := _date(item.get("date"))):
                continue
            # The API may return historical dates alongside an active date range.
            if any(start <= day <= end and day not in excluded for start, end, _, _, excluded in ranges):
                continue
            occurrences.append((day, day, _clock(item.get("start_time")), _clock(item.get("end_time")), []))
    else:
        start, end = _date(raw.get("start_date")), _date(raw.get("end_date"))
        if start and (not end or start <= end):
            multi_day = end and end != start
            occurrences.append((start, end or start, None if multi_day else _clock(raw.get("start_time")), None if multi_day else _clock(raw.get("end_time")), []))
    location = raw.get("location") or {}
    if not isinstance(location, dict):
        location = {}
    now = datetime.now(timezone.utc).isoformat()
    result, seen = [], set()
    for start, end, clock, end_clock, excluded in occurrences:
        # Ongoing ranges move their start to today's date in the API. Keep the
        # identity stable so saved events and first-seen dates survive tomorrow.
        is_range = (start, end, clock, end_clock, excluded) in ranges
        occurrence_id = f"{external_id}:range" if is_range else f"{external_id}:{start}:{clock or ''}"
        if occurrence_id in seen:
            continue
        seen.add(occurrence_id)
        result.append(Event(
            id=f"visitstockholm-{occurrence_id}", title=title, event_type=kind, category=kind,
            start_date=start, end_date=end if end != start else None, start_time=clock, end_time=end_clock,
            excluded_dates=excluded, venue=_localized(raw.get("venue_name")), city=city,
            region="Stockholms län" if city == "Stockholm" else "", country="Sverige", official_url=info_url,
            latitude=_coordinate(location.get("latitude"), 90), longitude=_coordinate(location.get("longitude"), 180),
            source_names=["Visit Stockholm"], source_records=[SourceRecord(
                source="Visit Stockholm", external_id=occurrence_id, source_url=info_url,
                fetched_at=now, raw_title=title, payload={"attribution": ATTRIBUTION, "license_url": LICENSE_URL},
            )], description=description, tags=[kind], verified_at=now,
            created_at=raw.get("created_at"), updated_at=raw.get("modified_at"),
            quality_notes=[ATTRIBUTION], price_status="unknown",
        ))
    return result


def stockholm_events(page_size=100, max_pages=12):
    from ui_logic import local_today
    today = local_today().isoformat()
    page_size = min(100, max(1, int(page_size)))
    max_pages = min(20, max(1, int(max_pages)))
    result, seen = [], set()
    meta = {"pages_fetched": 0, "total_elements": 0, "truncated": False, "failed_pages": 0}

    def fetch_page(page):
        response = requests.get(API_URL, params={"page": page, "size": page_size}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError("Visit Stockholm: unexpected API response")
        return payload

    def consume(payload):
        meta["pages_fetched"] += 1
        meta["total_elements"] = payload.get("count", 0)
        for raw in payload["results"]:
            for event in parse_stockholm_event(raw):
                if event.id not in seen and (event.end_date or event.start_date) >= today:
                    result.append(event)
                    seen.add(event.id)

    first = fetch_page(1)
    consume(first)
    total_pages = first.get("total_pages")
    if isinstance(total_pages, int) and not isinstance(total_pages, bool) and total_pages > 0:
        # Once the server publishes the page count, independent pages can be
        # fetched together. Consume in page order so canonical IDs stay stable.
        last = min(total_pages, max_pages)
        meta["truncated"] = total_pages > max_pages
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(fetch_page, page) for page in range(2, last + 1)]
            for future in futures:
                try:
                    consume(future.result())
                except (requests.RequestException, ValueError):
                    meta["failed_pages"] += 1
                    meta["truncated"] = True
        return result, meta

    payload = first
    for page in range(1, max_pages + 1):
        # Keep requests on the documented host; never follow a supplied next URL.
        more = bool(payload.get("next"))
        if not more:
            break
        if not payload["results"] or page == max_pages:
            meta["truncated"] = True
            break
        payload = fetch_page(page + 1)
        consume(payload)
    return result, meta
