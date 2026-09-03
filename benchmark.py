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

    return {
        "reference_events": total,
        "matched": len(matched),
        "missed": len(missed),
        "coverage_percent": round(100 * len(matched) / total, 1) if total else None,
        "matches": matched,
        "missed_events": missed,
        "by_reference_source": sources,
    }
