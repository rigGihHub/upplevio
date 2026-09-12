"""Diagnostics for source overlap and unique discovery value.

This module deliberately measures only what the current imported event set can
support. It does not estimate total market coverage or a long-term ROI for a
source. "Unique" means that, after Upplevio's conservative deduplication, an
event is represented by only one named source in the selected horizon.
"""
from collections import Counter
from datetime import date, timedelta
from itertools import combinations


def _event_start(event):
    try:
        return date.fromisoformat(event.start_date)
    except Exception:
        return None


def _normalized_sources(event):
    return sorted({str(name).strip() for name in (getattr(event, "source_names", []) or []) if str(name).strip()})


def _signal(unique_events: int, represented_events: int) -> str:
    if represented_events < 3:
        return "För litet underlag"
    share = unique_events / represented_events if represented_events else 0.0
    if unique_events >= 3 and share >= 0.50:
        return "Högt unikt tillskott"
    if represented_events >= 5 and share <= 0.20:
        return "Stor överlappning"
    return "Blandat tillskott"


def source_value_report(events, horizon_days: int = 30, today: date | None = None) -> dict:
    """Summarise source-level unique value and pairwise overlap.

    The report is intentionally a snapshot. It should be compared across time
    before deciding to remove or deprioritise a source.
    """
    today = today or date.today()
    end = today + timedelta(days=max(1, int(horizon_days)))

    upcoming = []
    for event in events:
        if getattr(event, "is_demo", False):
            continue
        start = _event_start(event)
        if start is None or not (today <= start <= end):
            continue
        sources = _normalized_sources(event)
        if not sources:
            continue
        upcoming.append((event, sources))

    represented = Counter()
    unique = Counter()
    overlap = Counter()
    pair_counts = Counter()

    for _, sources in upcoming:
        for source in sources:
            represented[source] += 1
        if len(sources) == 1:
            unique[sources[0]] += 1
        else:
            for source in sources:
                overlap[source] += 1
            for a, b in combinations(sources, 2):
                pair_counts[(a, b)] += 1

    source_rows = []
    for source in sorted(represented, key=lambda name: (-represented[name], name.lower())):
        total = represented[source]
        unique_count = unique[source]
        overlap_count = overlap[source]
        unique_share = (unique_count / total * 100.0) if total else None
        source_rows.append({
            "source": source,
            "represented_events": total,
            "unique_events": unique_count,
            "overlap_events": overlap_count,
            "unique_share_percent": unique_share,
            "signal": _signal(unique_count, total),
        })

    pair_rows = [
        {"source_a": a, "source_b": b, "shared_events": count}
        for (a, b), count in sorted(pair_counts.items(), key=lambda item: (-item[1], item[0][0].lower(), item[0][1].lower()))
    ]

    multi_source_events = sum(1 for _, sources in upcoming if len(sources) > 1)
    sole_source_events = len(upcoming) - multi_source_events
    return {
        "horizon_days": max(1, int(horizon_days)),
        "events": len(upcoming),
        "sole_source_events": sole_source_events,
        "multi_source_events": multi_source_events,
        "sources": source_rows,
        "overlap_pairs": pair_rows,
    }
