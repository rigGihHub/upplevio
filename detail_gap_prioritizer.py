"""Transparent next-action priorities for event detail coverage gaps.

This module deliberately avoids a synthetic quality score. Ranking is based on
explicit priority bands, clean single-source opportunity, total missing events,
and a documented practical field order.
"""

FIELD_SPECS = (
    ("start_time", "Starttid", "start_time_coverage", "start_time_events", "single_start_time_events", 0),
    ("precise_venue", "Preciserad plats", "precise_venue_coverage", "precise_venue_events", "single_precise_venue_events", 1),
    ("end_time", "Sluttid", "end_time_coverage", "end_time_events", "single_end_time_events", 2),
    ("booking", "Bokningslänk", "booking_coverage", "booking_events", "single_booking_events", 3),
    ("price", "Pris", "price_coverage", "price_events", "single_price_events", 4),
    ("door_time", "Dörr/insläpp", "door_time_coverage", "door_time_events", "single_door_time_events", 5),
    ("age_limit", "Åldersgräns", "age_limit_coverage", "age_limit_events", "single_age_limit_events", 6),
)


def _priority_band(*, represented, single, missing, single_missing, coverage):
    # The cleanest attribution signal gets precedence. A field must affect several
    # real events before it is called a high-priority parser opportunity.
    if represented < 3:
        return "För lite data", 3
    if single >= 3 and single_missing >= 3 and coverage < 0.50:
        return "Hög prioritet", 0
    if missing >= 5 and coverage < 0.50:
        return "Hög prioritet · fler-källsignal", 1
    if (single_missing >= 2 or missing >= 3) and coverage < 0.75:
        return "Medelprioritet", 2
    return "Låg prioritet", 3


def _reason(label, *, represented, single, missing, single_missing, coverage):
    pct = round(coverage * 100)
    if represented < 3:
        return f"Bara {represented} event i mätningen; samla mer data innan parserarbete prioriteras."
    if single >= 3 and single_missing >= 3 and coverage < 0.50:
        return f"{single_missing} av {single} enkällsevent saknar {label.lower()} och total täckning är {pct}%."
    if missing >= 5 and coverage < 0.50:
        return f"{missing} av {represented} representerade event saknar {label.lower()} ({pct}% täckning); proveniensen är delvis fler-källa."
    if (single_missing >= 2 or missing >= 3) and coverage < 0.75:
        return f"{missing} event saknar {label.lower()}, varav {single_missing} är enkällsevent; täckning {pct}%."
    return f"Täckningen är {pct}% eller luckan berör för få event för att prioriteras nu."


def detail_gap_priorities(detail_audit, *, include_low=False):
    """Return source + field improvement opportunities from a detail coverage audit.

    No opaque score is produced. Ordering is deterministic and explainable:
    priority band -> clean single-source missing events -> all missing events ->
    practical field order -> source name.
    """
    rows = []
    for source_row in detail_audit.get("sources", []):
        represented = int(source_row.get("represented_events") or 0)
        single = int(source_row.get("single_source_events") or 0)
        for key, label, cov_key, count_key, single_count_key, field_order in FIELD_SPECS:
            coverage = float(source_row.get(cov_key) or 0)
            present = int(source_row.get(count_key) or 0)
            single_present = int(source_row.get(single_count_key) or 0)
            missing = max(0, represented - present)
            single_missing = max(0, single - single_present)
            band, band_order = _priority_band(
                represented=represented, single=single, missing=missing,
                single_missing=single_missing, coverage=coverage,
            )
            if band == "Låg prioritet" and not include_low:
                continue
            rows.append({
                "source": source_row.get("source", ""),
                "field": key,
                "field_label": label,
                "priority": band,
                "coverage": coverage,
                "represented_events": represented,
                "missing_events": missing,
                "single_source_events": single,
                "single_source_missing_events": single_missing,
                "reason": _reason(
                    label, represented=represented, single=single, missing=missing,
                    single_missing=single_missing, coverage=coverage,
                ),
                "_band_order": band_order,
                "_field_order": field_order,
            })
    rows.sort(key=lambda r: (
        r["_band_order"],
        -r["single_source_missing_events"],
        -r["missing_events"],
        r["_field_order"],
        r["source"].casefold(),
    ))
    for row in rows:
        row.pop("_band_order", None)
        row.pop("_field_order", None)
    return rows
