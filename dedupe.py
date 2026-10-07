import re
import unicodedata
from copy import copy
from functools import lru_cache
from difflib import SequenceMatcher
from typing import Iterable

from source_registry import SOURCES


@lru_cache(maxsize=16384)
def normalize_text(value: str):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = re.sub(r"\b(live|official|tickets?|biljetter|tour|202[0-9])\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def similarity(a: str, b: str):
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _tokens(value: str):
    return set(normalize_text(value).split())


def _token_overlap(a: str, b: str):
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _source_identity(event) -> set[tuple[str, str]]:
    out = set()
    for record in getattr(event, "source_records", []) or []:
        source = normalize_text(getattr(record, "source", ""))
        external_id = str(getattr(record, "external_id", "") or "").strip()
        if source and external_id:
            out.add((source, external_id))
    return out


def _same_external_record(a, b):
    return bool(_source_identity(a) & _source_identity(b))


def _title_identity(event):
    return _normalized_title(getattr(event, "title", "") or "")


@lru_cache(maxsize=16384)
def _normalized_title(title):
    title = re.sub(r"stand[\s-]?up", "standup", title, flags=re.I)
    title = re.sub(r"\bÖSK\b", "Örebro SK", title, flags=re.I)
    title = re.sub(r"\s*(?:[-–]\s*|kl\.?\s*)\d{1,2}[:.]\d{2}\s*$", "", title, flags=re.I)
    title = re.sub(r"\s*[-–]\s*extrainsatt matinéföreställning\s*$", "", title, flags=re.I)
    return normalize_text(title)


def _title_match(a, b, minimum=0.52):
    ta, tb = _title_identity(a), _title_identity(b)
    if not ta or not tb:
        return 0.0
    if ta == tb or set(ta.split()) == set(tb.split()):
        return 1.0
    # A distinctive production title may have a presenter credit in one source.
    short, long = sorted((ta, tb), key=len)
    if len(short) >= 12 and long.startswith(short + " med "):
        return 1.0
    token_score = _token_overlap(ta, tb)
    sequence = SequenceMatcher(None, ta, tb)
    if max(sequence.quick_ratio(), token_score) < minimum:
        return 0.0
    return max(sequence.ratio(), token_score)


def _start_time(event):
    value = getattr(event, "start_time", None) or ""
    match = re.match(r"(\d{1,2}):(\d{2})", value)
    if not match:
        match = re.search(r"(?:kl\.?\s*|[-–]\s*)(\d{1,2})[:.](\d{2})\s*$", getattr(event, "title", ""), re.I)
    return f"{int(match[1]):02d}:{match[2]}" if match else None


def _is_sport(event):
    return "sport" in normalize_text(" ".join([getattr(event, "event_type", ""), getattr(event, "category", "")])).split()


def _venue_similarity(a, b):
    va, vb = normalize_text(a), normalize_text(b)
    rooms = ("stora scenen", "lilla scenen", "foajen", "konsertsalen", "arena", "kongress")
    room_a = next((room for room in rooms if va.endswith(" " + room)), None)
    room_b = next((room for room in rooms if vb.endswith(" " + room)), None)
    if room_a and room_b and room_a != room_b:
        return 0.0
    short, long = sorted((va, vb), key=len)
    # Some calendars specify the building, others the room inside it.
    if short and long.startswith(short + " ") and long[len(short) + 1:] in rooms:
        return 1.0
    return similarity(va, vb)


def duplicate_score(a, b):
    """Conservative similarity score for two normalized Event objects.

    Hard contradictions in date/city block automatic matching. Exact source identity is
    treated as the same record. The score intentionally favors title + geography over
    looser metadata to avoid false merges.
    """
    if a.start_date != b.start_date:
        return 0.0
    time_a, time_b = _start_time(a), _start_time(b)
    if time_a and time_b and time_a != time_b:
        return 0.0

    city_a, city_b = normalize_text(a.city), normalize_text(b.city)
    if city_a and city_b and city_a != city_b:
        return 0.0
    if _same_external_record(a, b):
        return 1.0

    title = _title_match(a, b)
    # Similar team names are not evidence that two fixtures are the same match.
    if (_is_sport(a) or _is_sport(b)) and _title_identity(a) != _title_identity(b):
        return 0.0

    venue_a, venue_b = normalize_text(a.venue), normalize_text(b.venue)
    venue_same = bool(venue_a and venue_b and venue_a == venue_b)
    venue_sim = _venue_similarity(a.venue, b.venue) if venue_a and venue_b else 0.0
    venue_same = venue_same or venue_sim == 1.0
    city_same = bool(city_a and city_b and city_a == city_b)
    if venue_a and venue_b and venue_a != city_a and venue_b != city_b and venue_sim < 0.70:
        return 0.0

    # Very different titles should not be rescued solely by a shared venue/city.
    if title < 0.52:
        return 0.0

    score = title * 0.76
    score += 0.14 if city_same else 0.0
    if venue_same:
        score += 0.10
    elif venue_sim >= 0.82:
        score += 0.06
    return min(score, 1.0)


def production_identity(event):
    """Normalized title identity used only to reduce repeated productions in discovery."""
    return _title_identity(event)


def _repeatable_production(event):
    """Limit cross-date collapsing to staged productions where repeated dates are expected."""
    tags = getattr(event, "tags", None) or []
    if isinstance(tags, str):
        tags = [tags]
    text = normalize_text(" ".join([
        getattr(event, "event_type", "") or "",
        getattr(event, "category", "") or "",
        *tags,
    ]))
    return any(word in text for word in ("teater", "scen", "show", "musikal", "forestallning", "dans"))


def same_production(a, b):
    """True for repeated staged productions at a non-contradictory city/venue."""
    city_a, city_b = normalize_text(getattr(a, "city", "")), normalize_text(getattr(b, "city", ""))
    if city_a and city_b and city_a != city_b:
        return False
    title_a, title_b = production_identity(a), production_identity(b)
    if not title_a or not title_b:
        return False
    if _is_sport(a) or _is_sport(b):
        return False
    title_match = _title_match(a, b, minimum=0.92)
    if title_match < 0.92:
        return False
    repeatable_a, repeatable_b = _repeatable_production(a), _repeatable_production(b)
    exact_title = title_a == title_b
    interval_a = bool(getattr(a, "end_date", None) and getattr(a, "end_date", None) != getattr(a, "start_date", None))
    interval_b = bool(getattr(b, "end_date", None) and getattr(b, "end_date", None) != getattr(b, "start_date", None))
    # Broad calendars sometimes publish a generic date range while venue calendars
    # publish the individual staged performances. Treat the exact-title range only
    # as a presentation alias; underlying event deduplication remains untouched.
    city_a, city_b = normalize_text(getattr(a, "city", "")), normalize_text(getattr(b, "city", ""))
    if city_a and city_b and city_a != city_b:
        return False
    venue_a, venue_b = normalize_text(getattr(a, "venue", "")), normalize_text(getattr(b, "venue", ""))
    if venue_a and venue_a == city_a:
        venue_a = ""
    if venue_b and venue_b == city_b:
        venue_b = ""
    if venue_a and venue_b and _venue_similarity(venue_a, venue_b) < 0.82:
        return False
    staged = (repeatable_a and repeatable_b) or (exact_title and ((repeatable_a and interval_b) or (repeatable_b and interval_a)))
    # Exhibitions, fairs and other recurring events also belong on one card when
    # title and a specific venue agree. Preserve each occurrence for details.
    shared_page = bool(getattr(a, "official_url", None) and getattr(a, "official_url", None) == getattr(b, "official_url", None) and "/events/" in getattr(a, "official_url", ""))
    return staged or (exact_title and bool(city_a and city_a == city_b) and ((bool(venue_a and venue_b) and venue_a == venue_b) or shared_page))


def collapse_productions(events):
    """Keep one discovery card per staged production and preserve alternative dates as presentation metadata."""
    collapsed = []
    for event in events:
        representative = next((existing for existing in collapsed if same_production(existing, event)), None)
        if representative is None:
            representative = copy(event)
            setattr(representative, "_alternate_dates", [])
            setattr(representative, "_alternate_events", [])
            collapsed.append(representative)
            continue
        dates = getattr(representative, "_alternate_dates", [])
        candidate_date = getattr(event, "start_date", None)
        if candidate_date and candidate_date != getattr(representative, "start_date", None) and candidate_date not in dates:
            dates.append(candidate_date)
            dates.sort()
        setattr(representative, "_alternate_dates", dates)
        alternate_events = getattr(representative, "_alternate_events", [])
        if not any(getattr(existing, "id", None) == getattr(event, "id", None) for existing in alternate_events):
            alternate_events.append(event)
            alternate_events.sort(key=lambda item: (getattr(item, "start_date", "") or "", getattr(item, "start_time", "") or ""))
        setattr(representative, "_alternate_events", alternate_events)
    return collapsed


_SOURCE_BY_NAME = {normalize_text(s.name): s for s in SOURCES}
# Aliases used in Event.source_names versus registry display names.
_SOURCE_ALIASES = {
    normalize_text("Visit Örebro"): "visitorebro_editorial",
    normalize_text("Conventum"): "conventum",
    normalize_text("Ticketmaster"): "ticketmaster",
    normalize_text("Visit Sweden"): "visitsweden",
    normalize_text("Showtic"): "showtic",
    normalize_text("Kortcentralen"): "kortcentralen",
    normalize_text("Tickster"): "tickster_collectors",
}
_SOURCE_BY_KEY = {s.key: s for s in SOURCES}
_TRUST_SCORE = {"high": 3, "medium_high": 2, "medium": 1, "low": 0}


def source_trust(source_name: str) -> int:
    normalized = normalize_text(source_name)
    definition = _SOURCE_BY_NAME.get(normalized)
    if definition is None:
        alias_key = _SOURCE_ALIASES.get(normalized)
        definition = _SOURCE_BY_KEY.get(alias_key) if alias_key else None
    return _TRUST_SCORE.get(getattr(definition, "trust_level", ""), 1)


def event_trust(event) -> int:
    names = getattr(event, "source_names", []) or []
    return max((source_trust(name) for name in names), default=1)


def _record_key(record):
    return (
        normalize_text(getattr(record, "source", "")),
        str(getattr(record, "external_id", "") or "").strip(),
        str(getattr(record, "source_url", "") or "").strip(),
    )


def _merge_records(a_records: Iterable, b_records: Iterable):
    merged = []
    seen = set()
    for record in list(a_records or []) + list(b_records or []):
        key = _record_key(record)
        if key in seen:
            continue
        seen.add(key)
        merged.append(record)
    return merged


def _prefer_text(current, incoming, prefer_incoming=False):
    current = current or ""
    incoming = incoming or ""
    if not current:
        return incoming
    if not incoming:
        return current
    if prefer_incoming:
        return incoming
    return current


def _merge_price(best, event, prefer_incoming=False):
    # Never infer free. Prefer explicit known/free values over unknown; when both are
    # explicit and conflict, retain the higher-trust record and flag the conflict.
    a_status = getattr(best, "price_status", "unknown") or "unknown"
    b_status = getattr(event, "price_status", "unknown") or "unknown"
    if a_status == "unknown" and b_status != "unknown":
        best.price_status = b_status
        best.price_min = event.price_min
        best.price_max = event.price_max
        best.currency = event.currency
        return
    if b_status == "unknown" or a_status == b_status:
        if a_status == "known" and b_status == "known":
            mins = [v for v in (best.price_min, event.price_min) if v is not None]
            maxs = [v for v in (best.price_max, event.price_max) if v is not None]
            best.price_min = min(mins) if mins else None
            best.price_max = max(maxs) if maxs else None
        return
    # Explicit free vs known-price disagreement is meaningful; don't hide it.
    note = f"Priskonflikt mellan källor: {a_status} / {b_status}"
    if note not in best.quality_notes:
        best.quality_notes.append(note)
    if prefer_incoming:
        best.price_status = b_status
        best.price_min = event.price_min
        best.price_max = event.price_max
        best.currency = event.currency


def merge_event(best, event):
    """Merge a confirmed duplicate into *best* while preserving provenance."""
    prefer_incoming = event_trust(event) > event_trust(best)

    best.source_names = sorted(set((best.source_names or []) + (event.source_names or [])))
    best.source_count = len(best.source_names)
    best.source_records = _merge_records(best.source_records, event.source_records)

    # Keep stable canonical identity from the first event; provenance records preserve
    # all source IDs. Fill gaps, and only replace descriptive fields with higher-trust data.
    best.title = _prefer_text(best.title, event.title, prefer_incoming and len(event.title or "") >= len(best.title or ""))
    generic_types = {"", "Evenemang", "Event", "Okänt", "Okategoriserat"}
    if best.event_type in generic_types and event.event_type not in generic_types:
        best.event_type = event.event_type
    if best.category in generic_types | {"Lokalt"} and event.category not in generic_types:
        best.category = event.category
    best.venue = _prefer_text(best.venue, event.venue, prefer_incoming)
    best.city = _prefer_text(best.city, event.city, prefer_incoming)
    best.region = _prefer_text(best.region, event.region, prefer_incoming)
    best.country = _prefer_text(best.country, event.country, prefer_incoming)
    best.start_time = best.start_time or event.start_time
    best.end_time = getattr(best, "end_time", None) or getattr(event, "end_time", None)
    best.end_date = best.end_date or event.end_date
    best.image_url = best.image_url or event.image_url
    best.official_url = best.official_url or event.official_url
    best.ticket_url = best.ticket_url or event.ticket_url
    best.latitude = best.latitude if best.latitude is not None else event.latitude
    best.longitude = best.longitude if best.longitude is not None else event.longitude
    best.venue_latitude = best.venue_latitude if best.venue_latitude is not None else event.venue_latitude
    best.venue_longitude = best.venue_longitude if best.venue_longitude is not None else event.venue_longitude
    if event.description and (not best.description or (prefer_incoming and len(event.description) > len(best.description))):
        best.description = event.description
    best.tags = sorted(set((best.tags or []) + (event.tags or [])))
    best.quality_notes = list(dict.fromkeys((best.quality_notes or []) + (event.quality_notes or [])))
    _merge_price(best, event, prefer_incoming)

    # Verification semantics are based on independent named sources, not vague "verified" flags.
    if best.source_count >= 2:
        best.data_quality = "multi_source"
    elif event_trust(best) >= 3:
        best.data_quality = "source_verified"
    else:
        best.data_quality = "partial"
    return best


def _normalize_single_source_quality(event):
    # Legacy adapters used "verified" too broadly. Convert to explicit semantics.
    if len(set(event.source_names or [])) >= 2:
        event.data_quality = "multi_source"
    elif event_trust(event) >= 3:
        event.data_quality = "source_verified"
    elif event.data_quality == "verified":
        event.data_quality = "partial"
    return event


def deduplicate(events):
    merged, review = [], []
    for event in events:
        _normalize_single_source_quality(event)
        best = None
        best_score = 0.0
        for candidate in merged:
            score = duplicate_score(candidate, event)
            if score > best_score:
                best, best_score = candidate, score
        if best and best_score >= 0.88:
            merge_event(best, event)
        else:
            if best and 0.70 <= best_score < 0.88:
                review.append((best, event, best_score))
            merged.append(event)
    return merged, review


def verification_label(event):
    count = len(set(getattr(event, "source_names", []) or []))
    if count >= 2:
        return f"Bekräftat från {count} källor"
    if event_trust(event) >= 3:
        return "Källverifierad"
    if getattr(event, "data_quality", "") == "review":
        return "Behöver verifieras"
    return "Källa behöver kontrolleras"
