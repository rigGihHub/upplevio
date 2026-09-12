"""Batch evidence audit for a selected detail gap.

Read-only diagnostics over a small set of concrete event pages. It reuses the
single-page evidence rules and never mutates Event or parser state.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

from parser_fix_evidence import fetch_gap_evidence


def _case_key(case):
    return str(case.get("event_id") or case.get("url") or case.get("title") or "")


def evidence_batch_audit(cases, *, field, limit=9, timeout=8, max_workers=4, fetcher=None):
    """Review several URL-backed cases and summarize recurring evidence.

    Clean single-source cases should already be sorted first by detail_gap_cases;
    this function preserves input order. Network failures stay visible and are
    excluded from parser-candidate-rate calculations.
    """
    fetcher = fetcher or fetch_gap_evidence
    selected = [dict(c) for c in cases if str(c.get("url") or "").strip()][:max(1, int(limit))]
    if not selected:
        return {
            "field": field, "requested": 0, "reviewed": 0, "analyzable": 0,
            "parser_candidates": 0, "candidate_rate": None, "status_counts": {},
            "clean_reviewed": 0, "classification": "Inga granskningsbara fall", "rows": [],
        }

    results = {}
    workers = max(1, min(int(max_workers), len(selected), 6))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {
            pool.submit(
                fetcher, c["url"], field=field,
                current_start_time=c.get("start_time") or None, timeout=timeout,
            ): c for c in selected
        }
        for future in as_completed(future_map):
            case = future_map[future]
            try:
                result = future.result()
            except Exception as exc:  # diagnostics must survive one bad page
                result = {
                    "status": "Kunde inte granska", "kind": "batch_exception",
                    "snippet": "", "value": None,
                    "explanation": f"Batchgranskningen misslyckades för sidan: {type(exc).__name__}.",
                    "http_status": None,
                }
            results[_case_key(case)] = result

    rows = []
    for case in selected:
        result = results.get(_case_key(case), {})
        rows.append({
            "event_id": case.get("event_id", ""), "title": case.get("title", ""),
            "date": case.get("date", ""), "attribution": case.get("attribution", ""),
            "clean_attribution": bool(case.get("clean_attribution")), "url": case.get("url", ""),
            "status": result.get("status", "Kunde inte granska"), "kind": result.get("kind", ""),
            "value": result.get("value"), "snippet": result.get("snippet", ""),
            "explanation": result.get("explanation", ""), "http_status": result.get("http_status"),
        })

    counts = Counter(r["status"] for r in rows)
    failed = counts.get("Kunde inte granska", 0)
    analyzable = len(rows) - failed
    candidates = counts.get("Parserkandidat", 0)
    rate = candidates / analyzable if analyzable else None
    clean_reviewed = sum(1 for r in rows if r["clean_attribution"] and r["status"] != "Kunde inte granska")

    if analyzable < 3:
        classification = "För lite evidens"
    elif candidates >= 3 and rate is not None and rate >= 0.60:
        classification = "Återkommande parserkandidat"
    elif candidates == 0:
        classification = "Ingen parsertrend hittad"
    else:
        classification = "Blandad evidens"

    return {
        "field": field, "requested": len(selected), "reviewed": len(rows),
        "analyzable": analyzable, "parser_candidates": candidates,
        "candidate_rate": rate, "status_counts": dict(counts),
        "clean_reviewed": clean_reviewed, "classification": classification, "rows": rows,
    }
