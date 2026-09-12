
from collections import Counter, defaultdict
from datetime import date, timedelta

from booking_intent import cta_quality

LOCAL_SOURCES = {
    "City Örebro",
    "Lov Örebro",
    "Visit Örebro – redaktionella eventlistor",
    "Visit Örebro",
    "Conventum",
    "Örebro Konserthus",
    "Örebro Teater",
    "ÖSK Fotboll",
    "Örebro Hockey",
}

def _event_date(event):
    try:
        return date.fromisoformat(event.start_date)
    except Exception:
        return None

def _sources(event):
    return sorted({s.strip() for s in (getattr(event, "source_names", None) or []) if s and s.strip()})

def _category(event):
    return (getattr(event, "event_type", None) or getattr(event, "category", None) or "Okänd").strip()

def local_source_audit(events, *, horizon_days=30, today=None):
    today = today or date.today()
    end = today + timedelta(days=max(1, int(horizon_days)))
    rows = [e for e in events if not getattr(e, "is_demo", False)
            and (d := _event_date(e)) and today <= d <= end]

    represented = Counter()
    unique = Counter()
    overlap = Counter()
    bookable = Counter()
    categories = defaultdict(set)
    unique_categories = defaultdict(set)

    for e in rows:
        names = [s for s in _sources(e) if s in LOCAL_SOURCES]
        if not names:
            continue
        cat = _category(e)
        q = cta_quality(e)
        for s in names:
            represented[s] += 1
            categories[s].add(cat)
            if q["status"] == "bookable":
                bookable[s] += 1
        if len(_sources(e)) == 1:
            for s in names:
                unique[s] += 1
                unique_categories[s].add(cat)
        elif len(_sources(e)) > 1:
            for s in names:
                overlap[s] += 1

    result=[]
    for source in sorted(LOCAL_SOURCES):
        total=represented[source]
        if total == 0:
            continue
        unique_count=unique[source]
        result.append({
            "source": source,
            "represented_events": total,
            "unique_events": unique_count,
            "overlap_events": overlap[source],
            "unique_share": unique_count / total if total else None,
            "categories": sorted(categories[source]),
            "category_count": len(categories[source]),
            "unique_categories": sorted(unique_categories[source]),
            "unique_category_count": len(unique_categories[source]),
            "bookable_events": bookable[source],
            "booking_coverage": bookable[source] / total if total else None,
        })

    result.sort(key=lambda r:(-r["unique_events"],-r["unique_category_count"],-r["bookable_events"],r["source"].casefold()))

    return {
        "horizon_days": max(1, int(horizon_days)),
        "events_considered": len(rows),
        "sources": result,
    }
