"""Independent benchmark coverage helpers.

A benchmark is a dated, manually curated reference sample from sources that are
not treated as the application's own imported event list. Coverage reported
here is coverage of that explicit sample only — never of all real-world events.
"""
from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class BenchmarkEvent:
    id: str
    title: str
    start_date: str
    city: str
    venue: str
    category: str
    reference_source: str
    reference_url: str
    checked_at: str


def normalize_title(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    text = text.replace("&", " och ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def load_benchmark(path: str | Path) -> list[BenchmarkEvent]:
    rows: list[BenchmarkEvent] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(BenchmarkEvent(**{field: (row.get(field) or "").strip() for field in BenchmarkEvent.__dataclass_fields__}))
    return rows


def _title_score(a: str, b: str) -> float:
    na, nb = normalize_title(a), normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    # Sequence similarity plus containment handles common source suffixes such
    # as "Sweden Tour '26" without making date/city optional.
    seq = SequenceMatcher(None, na, nb).ratio()
    if (na in nb or nb in na) and min(len(na), len(nb)) >= 10:
        containment = 0.9
    else:
        containment = 0.0
    ta, tb = set(na.split()), set(nb.split())
    token_overlap = len(ta & tb) / max(1, len(ta | tb))
    return max(seq, containment, token_overlap)


def _same_city(reference_city: str, event_city: str) -> bool:
    return normalize_title(reference_city) == normalize_title(event_city)



DEFAULT_DISCOVERY_SEGMENTS = (
    "Musik",
    "Scen & teater",
    "Sport",
    "Familj",
    "Mässa & marknad",
    "Mat & dryck",
    "Förening & prova på",
    "Kultur & museum",
)


def _segment_for_category(category: str) -> str:
    """Map free-form benchmark categories to broad discovery segments.

    The mapping is intentionally coarse. Its job is to expose blind spots in
    the benchmark sample, not to redefine Upplevio's product taxonomy.
    """
    value = normalize_title(category)
    if any(token in value for token in ("konsert", "musik", "dans", "musikal")):
        return "Musik"
    if any(token in value for token in ("teater", "scen", "show", "stand up", "standup", "underhallning")):
        return "Scen & teater"
    if any(token in value for token in ("sport", "fotboll", "hockey", "innebandy", "match")):
        return "Sport"
    if any(token in value for token in ("familj", "barn", "lov", "pyssel")):
        return "Familj"
    if any(token in value for token in ("massa", "marknad", "loppis")):
        return "Mässa & marknad"
    if any(token in value for token in ("mat", "dryck", "festival")):
        return "Mat & dryck"
    if any(token in value for token in ("forening", "prova pa", "aktivitet")):
        return "Förening & prova på"
    if any(token in value for token in ("museum", "utstallning", "kultur", "visning")):
        return "Kultur & museum"
    return "Övrigt"


def benchmark_sample_quality(
    reference_events: Iterable[BenchmarkEvent],
    expected_segments: Iterable[str] = DEFAULT_DISCOVERY_SEGMENTS,
) -> dict:
    """Describe how representative the benchmark *sample* is.

    This deliberately does not produce a magic quality score. With a small,
    manually curated reference set such a number would imply more precision
    than the evidence supports. Instead it exposes concentration and blind
    spots so Admin can warn when coverage figures are easy to over-interpret.
    """
    refs = list(reference_events)
    total = len(refs)
    category_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    segment_counts: dict[str, int] = {}

    for ref in refs:
        category = ref.category or "Okänd"
        source = ref.reference_source or "Okänd"
        segment = _segment_for_category(category)
        category_counts[category] = category_counts.get(category, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1
        segment_counts[segment] = segment_counts.get(segment, 0) + 1

    def dominant(counts: dict[str, int]) -> dict | None:
        if not counts or not total:
            return None
        name, count = max(counts.items(), key=lambda item: (item[1], item[0]))
        return {"name": name, "count": count, "share_percent": round(100 * count / total, 1)}

    expected = list(dict.fromkeys(expected_segments))
    missing_segments = [name for name in expected if segment_counts.get(name, 0) == 0]
    represented_segments = [name for name in expected if segment_counts.get(name, 0) > 0]
    warnings: list[str] = []

    dom_category = dominant(category_counts)
    dom_source = dominant(source_counts)
    if total < 40:
        warnings.append("Liten referensmängd: dra inte generella slutsatser om hela marknaden.")
    if dom_category and dom_category["share_percent"] >= 50:
        warnings.append(f'Referensen domineras av kategorin {dom_category["name"]} ({dom_category["share_percent"]:.0f} %).')
    if dom_source and dom_source["share_percent"] >= 60:
        warnings.append(f'Referensen domineras av källan {dom_source["name"]} ({dom_source["share_percent"]:.0f} %).')
    if missing_segments:
        warnings.append("Saknar helt referensevent i flera viktiga discovery-segment.")

    return {
        "reference_events": total,
        "category_counts": category_counts,
        "source_counts": source_counts,
        "segment_counts": segment_counts,
        "dominant_category": dom_category,
        "dominant_source": dom_source,
        "expected_segments": expected,
        "represented_segments": represented_segments,
        "missing_segments": missing_segments,
        "represented_segment_count": len(represented_segments),
        "expected_segment_count": len(expected),
        "warnings": warnings,
    }

def benchmark_report(reference_events: Iterable[BenchmarkEvent], app_events: Iterable, threshold: float = 0.78) -> dict:
    """Match an independent reference sample against current Upplevio events.

    Matching is intentionally conservative: same start date and city are
    required, then title similarity must clear ``threshold``. Each Upplevio
    event can satisfy at most one benchmark row.
    """
    refs = list(reference_events)
    events = [e for e in app_events if not getattr(e, "is_demo", False)]
    used_event_ids: set[str] = set()
    matched = []
    missed = []

    for ref in refs:
        candidates = []
        for event in events:
            if getattr(event, "id", "") in used_event_ids:
                continue
            if (getattr(event, "start_date", "") or "") != ref.start_date:
                continue
            if not _same_city(ref.city, getattr(event, "city", "") or ""):
                continue
            score = _title_score(ref.title, getattr(event, "title", "") or "")
            if score >= threshold:
                candidates.append((score, event))
        if candidates:
            score, event = max(candidates, key=lambda item: item[0])
            used_event_ids.add(getattr(event, "id", ""))
            matched.append({
                "benchmark": ref,
                "event": event,
                "score": round(score, 3),
            })
        else:
            missed.append(ref)

    total = len(refs)
    sources = {}
    for ref in refs:
        bucket = sources.setdefault(ref.reference_source or "Okänd", {"reference_events": 0, "matched": 0, "missed": 0})
        bucket["reference_events"] += 1
    matched_ids = {item["benchmark"].id for item in matched}
    for ref in refs:
        bucket = sources[ref.reference_source or "Okänd"]
        if ref.id in matched_ids:
            bucket["matched"] += 1
        else:
            bucket["missed"] += 1
    for bucket in sources.values():
        bucket["coverage_percent"] = round(100 * bucket["matched"] / bucket["reference_events"], 1) if bucket["reference_events"] else None

    categories = {}
    venues = {}
    segments = {}
    matched_ids = {item["benchmark"].id for item in matched}

    for ref in refs:
        category_name = ref.category or "Okänd"
        cat = categories.setdefault(category_name, {"reference_events": 0, "matched": 0, "missed": 0})
        cat["reference_events"] += 1

        segment_name = _segment_for_category(ref.category)
        seg = segments.setdefault(segment_name, {"reference_events": 0, "matched": 0, "missed": 0})
        seg["reference_events"] += 1

        venue_name = ref.venue or "Okänd"
        venue = venues.setdefault(venue_name, {"reference_events": 0, "matched": 0, "missed": 0})
        venue["reference_events"] += 1

        if ref.id in matched_ids:
            cat["matched"] += 1
            seg["matched"] += 1
            venue["matched"] += 1
        else:
            cat["missed"] += 1
            seg["missed"] += 1
            venue["missed"] += 1

    for bucket in list(categories.values()) + list(segments.values()) + list(venues.values()):
        bucket["coverage_percent"] = round(100 * bucket["matched"] / bucket["reference_events"], 1) if bucket["reference_events"] else None

    category_gaps = [
        {"category": name, **stats}
        for name, stats in categories.items() if stats["missed"] > 0
    ]
    category_gaps.sort(key=lambda row: (-row["missed"], row["coverage_percent"], row["category"].lower()))

    venue_gaps = [
        {"venue": name, **stats}
        for name, stats in venues.items() if stats["missed"] > 0
    ]
    venue_gaps.sort(key=lambda row: (-row["missed"], row["coverage_percent"], row["venue"].lower()))

    segment_gaps = [
        {"segment": name, **stats}
        for name, stats in segments.items() if stats["missed"] > 0
    ]
    segment_gaps.sort(key=lambda row: (-row["missed"], row["coverage_percent"], row["segment"].lower()))

    missed_source_counts = {}
    for ref in missed:
        name = ref.reference_source or "Okänd"
        missed_source_counts[name] = missed_source_counts.get(name, 0) + 1
    source_gap_priority = [
        {
            "reference_source": name,
            "missed": count,
            "reference_events": sources[name]["reference_events"],
            "coverage_percent": sources[name]["coverage_percent"],
        }
        for name, count in missed_source_counts.items()
    ]
    source_gap_priority.sort(key=lambda row: (-row["missed"], row["coverage_percent"], row["reference_source"].lower()))

    return {
        "reference_events": total,
        "matched": len(matched),
        "missed": len(missed),
        "coverage_percent": round(100 * len(matched) / total, 1) if total else None,
        "matches": matched,
        "missed_events": missed,
        "by_reference_source": sources,
        "by_category": categories,
        "by_segment": segments,
        "by_venue": venues,
        "category_gaps": category_gaps,
        "segment_gaps": segment_gaps,
        "venue_gaps": venue_gaps,
        "source_gap_priority": source_gap_priority,
    }
