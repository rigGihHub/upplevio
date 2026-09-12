"""Conservative data-quality gate for organic discovery ranking.

The gate protects top ranking from events with broken *core* integrity while
keeping legitimate long-tail events discoverable. Missing secondary metadata
(start/end time, price, age limit, door time, booking link) is never penalised.
"""
from __future__ import annotations

from datetime import date

CORE_SCORE_CAP = 18


def _date(value):
    try:
        return date.fromisoformat(str(value or ""))
    except Exception:
        return None


def discovery_data_quality_assessment(event) -> dict:
    """Return a narrow ranking gate assessment.

    level:
      - pass: no core-integrity problem
      - review: suspicious consistency issue, diagnostic only
      - restricted: may remain visible but cannot dominate top ranking
    """
    restricted = []
    review = []

    title = (getattr(event, "title", "") or "").strip()
    start_raw = (getattr(event, "start_date", "") or "").strip()
    end_raw = (getattr(event, "end_date", "") or "").strip()
    venue = (getattr(event, "venue", "") or "").strip()
    city = (getattr(event, "city", "") or "").strip()

    start = _date(start_raw)
    end = _date(end_raw) if end_raw else None

    if not title:
        restricted.append("titel saknas")
    if not start:
        restricted.append("startdatum saknas eller är ogiltigt")
    if start and end_raw and not end:
        restricted.append("slutdatum är ogiltigt")
    if start and end and end < start:
        restricted.append("slutdatum ligger före startdatum")
    if not venue and not city:
        restricted.append("både venue och ort saknas")

    status = (getattr(event, "price_status", "unknown") or "unknown").strip().lower()
    price_min = getattr(event, "price_min", None)
    if status == "known" and price_min is None:
        review.append("prisstatus är känd men pris saknas")
    if status == "free" and price_min not in (None, 0, 0.0):
        review.append("gratisstatus och prisdata motsäger varandra")

    if restricted:
        level = "restricted"
    elif review:
        level = "review"
    else:
        level = "pass"

    return {
        "level": level,
        "restricted_reasons": restricted,
        "review_reasons": review,
        "score_cap": CORE_SCORE_CAP if restricted else None,
    }


def apply_discovery_quality_gate(score: int, event) -> tuple[int, str | None]:
    """Cap only events with broken core integrity; never reward missing data."""
    assessment = discovery_data_quality_assessment(event)
    if assessment["level"] != "restricted":
        return int(score), None
    return min(int(score), CORE_SCORE_CAP), "ofullständig kärndata"


def discovery_data_quality_report(events) -> dict:
    rows = []
    counts = {"pass": 0, "review": 0, "restricted": 0}
    for event in events:
        assessment = discovery_data_quality_assessment(event)
        counts[assessment["level"]] += 1
        if assessment["level"] == "pass":
            continue
        rows.append({
            "title": getattr(event, "title", ""),
            "date": getattr(event, "start_date", ""),
            "sources": sorted(set(getattr(event, "source_names", []) or [])),
            "level": assessment["level"],
            "reasons": assessment["restricted_reasons"] + assessment["review_reasons"],
        })
    rows.sort(key=lambda x: (0 if x["level"] == "restricted" else 1, x["date"] or "", (x["title"] or "").lower()))
    return {"events_analyzed": len(events), **counts, "rows": rows}
