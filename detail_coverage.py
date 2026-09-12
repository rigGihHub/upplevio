from collections import defaultdict
from datetime import date, timedelta


_GENERIC_VENUES = {
    "", "örebro", "orebro", "örebro län", "orebro lan", "conventum",
    "online", "digitalt", "digital", "se arrangörens sida", "plats ej angiven",
}


def _event_date(event):
    try:
        return date.fromisoformat(getattr(event, "start_date", ""))
    except Exception:
        return None


def _sources(event):
    names = {str(s).strip() for s in (getattr(event, "source_names", None) or []) if str(s).strip()}
    if not names:
        for record in (getattr(event, "source_records", None) or []):
            name = str(getattr(record, "source", "") or "").strip()
            if name:
                names.add(name)
    return sorted(names)


def _has_value(value):
    return bool(str(value or "").strip())


def _has_precise_venue(event):
    venue = str(getattr(event, "venue", "") or "").strip()
    if not venue:
        return False
    normalized = venue.casefold()
    if normalized in _GENERIC_VENUES:
        return False
    city = str(getattr(event, "city", "") or "").strip().casefold()
    if city and normalized == city:
        return False
    return True


def _known_price(event):
    return getattr(event, "price_status", "unknown") in {"known", "free"}


def _pct(count, total):
    return count / total if total else None


def _flags(row):
    total = row["represented_events"]
    if total < 3:
        return ["För lite data"]

    flags = []
    start = row["start_time_coverage"] or 0
    end = row["end_time_coverage"] or 0
    venue = row["precise_venue_coverage"] or 0
    price = row["price_coverage"] or 0
    age = row["age_limit_coverage"] or 0
    doors = row["door_time_coverage"] or 0

    practical_fields = sum(x >= 0.20 for x in (end, price, age, doors))
    if start >= 0.80 and venue >= 0.80 and practical_fields >= 2:
        flags.append("Stark praktisk data")
    if start >= 0.60 and end < 0.25:
        flags.append("Sluttid saknas ofta")
    if venue < 0.70:
        flags.append("Plats behöver förbättras")
    if price < 0.20:
        flags.append("Pris saknas ofta")
    if practical_fields == 0:
        flags.append("Begränsad detaljdata")
    return flags or ["Jämn grunddata"]


def detail_coverage_audit(events, *, horizon_days=30, today=None):
    """Measure practical detail coverage on final deduplicated events.

    Per-source rows describe events represented by that source after dedupe. They do not
    claim source-specific provenance for a field when multiple sources represent an event.
    single_source_events is exposed as the cleaner attribution subset.
    """
    today = today or date.today()
    horizon_days = max(1, int(horizon_days))
    end = today + timedelta(days=horizon_days)
    rows = [
        e for e in events
        if not getattr(e, "is_demo", False)
        and (d := _event_date(e))
        and today <= d <= end
    ]

    counters = defaultdict(lambda: defaultdict(int))
    overall = defaultdict(int)

    def count_into(bucket, event):
        bucket["events"] += 1
        bucket["start_time"] += int(_has_value(getattr(event, "start_time", None)))
        bucket["end_time"] += int(_has_value(getattr(event, "end_time", None)))
        bucket["time_range"] += int(
            _has_value(getattr(event, "start_time", None))
            and _has_value(getattr(event, "end_time", None))
        )
        bucket["venue"] += int(_has_value(getattr(event, "venue", None)))
        bucket["precise_venue"] += int(_has_precise_venue(event))
        bucket["price"] += int(_known_price(event))
        bucket["age_limit"] += int(_has_value(getattr(event, "age_limit", None)))
        bucket["door_time"] += int(_has_value(getattr(event, "door_time", None)))
        bucket["booking"] += int(_has_value(getattr(event, "booking_url", None) or getattr(event, "ticket_url", None)))
        bucket["multi_source"] += int(len(_sources(event)) > 1)

    for event in rows:
        names = _sources(event)
        count_into(overall, event)
        for source in names:
            count_into(counters[source], event)
            if len(names) == 1:
                counters[source]["single_source"] += 1
                counters[source]["single_start_time"] += int(_has_value(getattr(event, "start_time", None)))
                counters[source]["single_end_time"] += int(_has_value(getattr(event, "end_time", None)))
                counters[source]["single_precise_venue"] += int(_has_precise_venue(event))
                counters[source]["single_price"] += int(_known_price(event))
                counters[source]["single_age_limit"] += int(_has_value(getattr(event, "age_limit", None)))
                counters[source]["single_door_time"] += int(_has_value(getattr(event, "door_time", None)))
                counters[source]["single_booking"] += int(_has_value(getattr(event, "booking_url", None) or getattr(event, "ticket_url", None)))

    result = []
    for source, c in counters.items():
        total = c["events"]
        row = {
            "source": source,
            "represented_events": total,
            "single_source_events": c["single_source"],
            "multi_source_events": c["multi_source"],
            "start_time_events": c["start_time"],
            "start_time_coverage": _pct(c["start_time"], total),
            "end_time_events": c["end_time"],
            "end_time_coverage": _pct(c["end_time"], total),
            "time_range_events": c["time_range"],
            "time_range_coverage": _pct(c["time_range"], total),
            "venue_events": c["venue"],
            "venue_coverage": _pct(c["venue"], total),
            "precise_venue_events": c["precise_venue"],
            "precise_venue_coverage": _pct(c["precise_venue"], total),
            "price_events": c["price"],
            "price_coverage": _pct(c["price"], total),
            "age_limit_events": c["age_limit"],
            "age_limit_coverage": _pct(c["age_limit"], total),
            "door_time_events": c["door_time"],
            "door_time_coverage": _pct(c["door_time"], total),
            "booking_events": c["booking"],
            "booking_coverage": _pct(c["booking"], total),
            "single_start_time_events": c["single_start_time"],
            "single_end_time_events": c["single_end_time"],
            "single_precise_venue_events": c["single_precise_venue"],
            "single_price_events": c["single_price"],
            "single_age_limit_events": c["single_age_limit"],
            "single_door_time_events": c["single_door_time"],
            "single_booking_events": c["single_booking"],
        }
        row["flags"] = _flags(row)
        result.append(row)

    # More observations first; no synthetic quality score.
    result.sort(key=lambda r: (-r["represented_events"], r["source"].casefold()))
    total = overall["events"]
    summary = {
        "events": total,
        "start_time_coverage": _pct(overall["start_time"], total),
        "end_time_coverage": _pct(overall["end_time"], total),
        "time_range_coverage": _pct(overall["time_range"], total),
        "precise_venue_coverage": _pct(overall["precise_venue"], total),
        "price_coverage": _pct(overall["price"], total),
        "age_limit_coverage": _pct(overall["age_limit"], total),
        "door_time_coverage": _pct(overall["door_time"], total),
        "booking_coverage": _pct(overall["booking"], total),
    }
    return {
        "horizon_days": horizon_days,
        "events_considered": total,
        "summary": summary,
        "sources": result,
    }
