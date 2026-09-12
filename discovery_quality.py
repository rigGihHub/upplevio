"""Conservative quality diagnostics for Upplevio's visible discovery results.

The diagnostics are guardrails, not hidden filters. They flag patterns that can
make a technically correct result list feel noisy or repetitive without
assuming that incomplete long-tail event metadata means the event is invalid.
"""
from __future__ import annotations

from collections import Counter
from difflib import SequenceMatcher
import re
import unicodedata

_GENERIC_TITLES = {
    "event", "evenemang", "aktivitet", "aktiviteter", "program", "kalender",
    "konsert", "match", "teater", "show", "festival", "mässa", "utställning",
    "workshop", "föreläsning", "familjeaktivitet", "sport",
}


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def _sources(event) -> tuple[str, ...]:
    return tuple(sorted({str(x).strip() for x in (getattr(event, "source_names", []) or []) if str(x).strip()}))


def _title_issue(event) -> str | None:
    title = (getattr(event, "title", "") or "").strip()
    normalized = _norm(title)
    if not normalized:
        return "Titel saknas"
    if len(normalized) < 4:
        return "Mycket kort titel"
    if normalized in _GENERIC_TITLES:
        return "För generell titel"
    taxonomy = {_norm(getattr(event, "event_type", "")), _norm(getattr(event, "category", ""))}
    if normalized in taxonomy and normalized:
        return "Titeln upprepar bara kategorin"
    return None


def _metadata_issues(event) -> list[str]:
    issues = []
    if not (getattr(event, "venue", "") or "").strip() and not (getattr(event, "city", "") or "").strip():
        issues.append("Plats saknas")
    elif not (getattr(event, "venue", "") or "").strip():
        issues.append("Venue saknas")
    if not (getattr(event, "start_date", "") or "").strip():
        issues.append("Datum saknas")
    # Missing start time is common and not automatically a quality defect. It is
    # only notable when the event also lacks a concrete venue.
    if not getattr(event, "start_time", None) and not (getattr(event, "venue", "") or "").strip():
        issues.append("Tid och venue saknas")
    if not (getattr(event, "official_url", None) or getattr(event, "ticket_url", None)):
        issues.append("Ingen extern länk")
    return issues


def _near_duplicate_pairs(events, threshold: float = 0.84) -> list[dict]:
    pairs = []
    for i, a in enumerate(events):
        ta = _norm(getattr(a, "title", ""))
        if not ta:
            continue
        for b in events[i + 1:]:
            # Same-date candidates are most likely to be duplicate clutter. A
            # recurring event on another date should not be treated as a duplicate.
            if getattr(a, "start_date", None) != getattr(b, "start_date", None):
                continue
            city_a, city_b = _norm(getattr(a, "city", "")), _norm(getattr(b, "city", ""))
            if city_a and city_b and city_a != city_b:
                continue
            tb = _norm(getattr(b, "title", ""))
            if not tb:
                continue
            similarity = SequenceMatcher(None, ta, tb).ratio()
            if similarity >= threshold:
                pairs.append({
                    "title_a": getattr(a, "title", ""),
                    "title_b": getattr(b, "title", ""),
                    "date": getattr(a, "start_date", ""),
                    "similarity": similarity,
                })
    return sorted(pairs, key=lambda x: (-x["similarity"], x["date"], x["title_a"].lower()))


def _concentration(events, getter) -> dict | None:
    if not events:
        return None
    counts = Counter()
    for event in events:
        values = getter(event)
        if isinstance(values, str):
            values = [values]
        values = [x for x in (values or []) if x]
        for value in set(values):
            counts[value] += 1
    if not counts:
        return None
    name, count = counts.most_common(1)[0]
    return {"name": name, "count": count, "share_percent": count / len(events) * 100.0}


def discovery_quality_report(events, top_n: int = 10) -> dict:
    """Inspect the visible top results without changing or suppressing them."""
    top_n = max(1, int(top_n))
    top = list(events)[:top_n]

    title_rows = []
    metadata_rows = []
    for event in top:
        title_issue = _title_issue(event)
        if title_issue:
            title_rows.append({"title": getattr(event, "title", ""), "issue": title_issue})
        issues = _metadata_issues(event)
        if issues:
            metadata_rows.append({"title": getattr(event, "title", ""), "issues": issues})

    duplicate_pairs = _near_duplicate_pairs(top)
    source_concentration = _concentration(top, _sources)
    type_concentration = _concentration(top, lambda e: getattr(e, "event_type", "") or getattr(e, "category", ""))

    warnings = []
    if duplicate_pairs:
        warnings.append(f"{len(duplicate_pairs)} möjlig nästan-dublett i toppresultaten")
    if source_concentration and len(top) >= 5 and source_concentration["share_percent"] >= 70:
        warnings.append(
            f'{source_concentration["name"]} förekommer i {source_concentration["share_percent"]:.0f} % av toppresultaten'
        )
    if type_concentration and len(top) >= 5 and type_concentration["share_percent"] >= 70:
        warnings.append(
            f'{type_concentration["name"]} utgör {type_concentration["share_percent"]:.0f} % av toppresultaten'
        )
    if len(title_rows) >= max(2, len(top) // 3):
        warnings.append("Flera toppresultat har svaga eller generella titlar")
    severe_metadata = [row for row in metadata_rows if "Plats saknas" in row["issues"] or "Datum saknas" in row["issues"]]
    if severe_metadata:
        warnings.append(f"{len(severe_metadata)} toppresultat saknar central plats- eller datuminformation")

    return {
        "top_n_requested": top_n,
        "events_analyzed": len(top),
        "weak_title_events": title_rows,
        "metadata_issue_events": metadata_rows,
        "near_duplicate_pairs": duplicate_pairs,
        "source_concentration": source_concentration,
        "type_concentration": type_concentration,
        "warnings": warnings,
    }
