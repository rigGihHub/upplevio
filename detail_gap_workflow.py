"""Turn a prioritized detail gap into concrete event/page review cases.

The workflow preserves provenance: single-source events are clean parser cases;
for multi-source events it prefers the selected source's own SourceRecord URL.
It does not infer that a missing field belongs to a source when provenance is unclear.
"""
from datetime import date, timedelta

from detail_coverage import _has_precise_venue, _known_price


def _event_date(event):
    try:
        return date.fromisoformat(getattr(event, "start_date", ""))
    except Exception:
        return None


def _source_names(event):
    names = {str(s).strip() for s in (getattr(event, "source_names", None) or []) if str(s).strip()}
    if not names:
        for record in (getattr(event, "source_records", None) or []):
            name = str(getattr(record, "source", "") or "").strip()
            if name:
                names.add(name)
    return sorted(names)


def _missing(event, field):
    if field == "start_time":
        return not bool(str(getattr(event, "start_time", "") or "").strip())
    if field == "end_time":
        return not bool(str(getattr(event, "end_time", "") or "").strip())
    if field == "precise_venue":
        return not _has_precise_venue(event)
    if field == "booking":
        return not bool(str(getattr(event, "booking_url", None) or getattr(event, "ticket_url", None) or "").strip())
    if field == "price":
        return not _known_price(event)
    if field == "door_time":
        return not bool(str(getattr(event, "door_time", "") or "").strip())
    if field == "age_limit":
        return not bool(str(getattr(event, "age_limit", "") or "").strip())
    raise ValueError(f"Unknown detail field: {field}")


def _source_url(event, source):
    # Prefer the selected source's record. This matters after dedupe, where the
    # event-level official URL may belong to a different source.
    for record in (getattr(event, "source_records", None) or []):
        if str(getattr(record, "source", "") or "").strip() == source:
            url = str(getattr(record, "source_url", "") or "").strip()
            if url:
                return url, "Källans URL"
    url = str(getattr(event, "official_url", "") or "").strip()
    if url:
        return url, "Eventets officiella URL"
    url = str(getattr(event, "ticket_url", "") or "").strip()
    if url:
        return url, "Biljett-URL"
    return "", "URL saknas"


def detail_gap_cases(events, *, source, field, horizon_days=30, today=None, limit=50):
    """Return concrete events represented by source where field is missing.

    Cases are sorted with clean single-source attribution first, then by date/title.
    No network requests are made; this is a diagnosis view over current imported data.
    """
    today = today or date.today()
    end = today + timedelta(days=max(1, int(horizon_days)))
    cases = []
    for event in events:
        if getattr(event, "is_demo", False):
            continue
        d = _event_date(event)
        if not d or not (today <= d <= end):
            continue
        names = _source_names(event)
        if source not in names or not _missing(event, field):
            continue
        url, url_basis = _source_url(event, source)
        clean = len(names) == 1
        cases.append({
            "event_id": str(getattr(event, "id", "") or ""),
            "title": str(getattr(event, "title", "") or ""),
            "date": str(getattr(event, "start_date", "") or ""),
            "start_time": str(getattr(event, "start_time", "") or ""),
            "venue": str(getattr(event, "venue", "") or ""),
            "url": url,
            "url_basis": url_basis,
            "attribution": "Enkällsevent" if clean else "Fler-källsevent",
            "source_count": len(names),
            "sources": " · ".join(names),
            "clean_attribution": clean,
        })
    cases.sort(key=lambda r: (
        not r["clean_attribution"],
        r["date"],
        r["start_time"] or "99:99",
        r["title"].casefold(),
    ))
    return cases[:max(1, int(limit))]


def gap_workflow_summary(cases):
    """Small transparent summary for an admin-selected gap."""
    total = len(cases)
    clean = sum(1 for c in cases if c.get("clean_attribution"))
    with_url = sum(1 for c in cases if c.get("url"))
    return {
        "cases": total,
        "clean_cases": clean,
        "multi_source_cases": total - clean,
        "cases_with_url": with_url,
        "url_coverage": (with_url / total) if total else None,
    }
