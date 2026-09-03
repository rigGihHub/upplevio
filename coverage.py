from collections import Counter
from datetime import date, timedelta
from math import radians, sin, cos, sqrt, atan2

from geography import CITY_COORDS, coordinates_for_event, distance_from_city, haversine_km

def _event_date(event):
    try:
        return date.fromisoformat(event.start_date)
    except Exception:
        return None

def coverage_snapshot(events, review_pairs=None, horizon_days=30):
    """Return honest, internal coverage diagnostics.

    This deliberately does NOT claim a percentage of all real-world events,
    because Upplevio has no independent ground-truth catalogue yet.
    """
    review_pairs = review_pairs or []
    today = date.today()
    end = today + timedelta(days=max(1, horizon_days))
    upcoming = [e for e in events if (d := _event_date(e)) and today <= d <= end and not e.is_demo]
    source_counts = Counter()
    for e in upcoming:
        for source in set(e.source_names):
            source_counts[source] += 1

    missing_city = sum(not (e.city or "").strip() for e in upcoming)
    missing_coordinates = sum(coordinates_for_event(e) is None for e in upcoming)
    missing_url = sum(not (e.official_url or e.ticket_url) for e in upcoming)
    multi_source = sum(e.source_count > 1 for e in upcoming)
    needs_review = sum(e.data_quality == "review" for e in upcoming)
    partial = sum(e.data_quality == "partial" for e in upcoming)

    return {
        "horizon_days": horizon_days,
        "events": len(upcoming),
        "multi_source": multi_source,
        "missing_city": missing_city,
        "missing_coordinates": missing_coordinates,
        "missing_url": missing_url,
        "partial": partial,
        "needs_review": needs_review,
        "duplicate_candidates": len(review_pairs),
        "sources": dict(sorted(source_counts.items(), key=lambda item: (-item[1], item[0]))),
    }
