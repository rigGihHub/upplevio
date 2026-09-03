import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable

from source_registry import SOURCES


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


def duplicate_score(a, b):
    """Conservative similarity score for two normalized Event objects.

    Hard contradictions in date/city block automatic matching. Exact source identity is
    treated as the same record. The score intentionally favors title + geography over
    looser metadata to avoid false merges.
    """
    if _same_external_record(a, b):
        return 1.0
    if a.start_date != b.start_date:
        return 0.0

    city_a, city_b = normalize_text(a.city), normalize_text(b.city)
    if city_a and city_b and city_a != city_b:
        return 0.0

    title_seq = similarity(a.title, b.title)
    title_tokens = _token_overlap(a.title, b.title)
    title = max(title_seq, title_tokens)

    venue_a, venue_b = normalize_text(a.venue), normalize_text(b.venue)
    venue_same = bool(venue_a and venue_b and venue_a == venue_b)
    venue_sim = similarity(a.venue, b.venue) if venue_a and venue_b else 0.0
    city_same = bool(city_a and city_b and city_a == city_b)

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
    best.venue = _prefer_text(best.venue, event.venue, prefer_incoming)
    best.city = _prefer_text(best.city, event.city, prefer_incoming)
    best.region = _prefer_text(best.region, event.region, prefer_incoming)
    best.country = _prefer_text(best.country, event.country, prefer_incoming)
    best.start_time = best.start_time or event.start_time
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
