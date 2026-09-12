"""Replay-based impact audit for evidence-backed parser fixes.

Compares current parsers with the pre-v0.74 behaviour on the same HTML pages.
This is diagnostic only and does not claim production impact before deployment.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from booking_enrichment import extract_detail_facts
from parser_fix_evidence import _safe_public_http_url
from showtime_enrichment import extract_explicit_showtime


def _text(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()


def _legacy_start(html: str, current_start_time: str | None = None):
    """Pre-v0.74 showtime behaviour: intervals/end markers, no '20:00 – start'."""
    text = _text(html)
    if not text:
        return None
    current = (current_start_time or "").strip()[:5] or None
    blocked_terms = ("öppettid", "biljettkassa", "telefon", "telefontid", "kundservice", "reception")
    strong_terms = ("pågår", "tider", "tid:", "tid ", "slut", "föreställning", "evenemang")
    candidates = []
    for m in re.finditer(r"(?<!\d)(\d{1,2})[:.](\d{2})\s*[–—-]\s*(\d{1,2})[:.](\d{2})(?!\d)", text):
        sh, sm, eh, em = map(int, m.groups())
        if not (0 <= sh <= 23 and 0 <= sm <= 59 and 0 <= eh <= 23 and 0 <= em <= 59):
            continue
        start, end = f"{sh:02d}:{sm:02d}", f"{eh:02d}:{em:02d}"
        context = text[max(0, m.start()-90):min(len(text), m.end()+90)].lower()
        blocked = any(t in context for t in blocked_terms)
        strong = any(t in context for t in strong_terms)
        matches = bool(current and start == current)
        if blocked and not matches:
            continue
        if not matches and not strong:
            continue
        candidates.append((0 if matches else 1, m.start(), start, end))
    if current:
        for m in re.finditer(r"(?<!\d)(\d{1,2})[:.](\d{2})\s*[–—-]\s*slut\b", text, re.I):
            h, minute = int(m.group(1)), int(m.group(2))
            if not (0 <= h <= 23 and 0 <= minute <= 59):
                continue
            context = text[max(0, m.start()-90):min(len(text), m.end()+90)].lower()
            if any(t in context for t in blocked_terms):
                continue
            candidates.append((0, m.start(), current, f"{h:02d}:{minute:02d}"))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]))
    return candidates[0][2]


def _legacy_price(html: str):
    """Pre-v0.74 price behaviour: no standalone 'Entré 120 kr' label."""
    soup = BeautifulSoup(html or "", "html.parser")
    lines = [" ".join(x.split()) for x in soup.get_text("\n", strip=True).splitlines()]
    for line in lines:
        m = re.match(r"(?i)^(?:biljettpris|entrépris|pris)\s*[:–-]?\s*(?:från\s*)?(\d{1,5})(?:[.,]00)?\s*(?:kr|kronor)\b", line)
        if m:
            return float(m.group(1))
    return None


def compare_parser_versions(html: str, *, field: str, current_start_time: str | None = None):
    """Compare current parser output to the pre-v0.74 parser for one page."""
    if field == "start_time":
        legacy = _legacy_start(html, current_start_time=current_start_time)
        hit = extract_explicit_showtime(html, current_start_time=current_start_time)
        current = hit.get("start_time") if hit else None
    elif field == "price":
        legacy = _legacy_price(html)
        current = extract_detail_facts(html).get("price")
    else:
        return {"supported": False, "legacy": None, "current": None, "outcome": "Ej v0.74-fix"}

    if legacy == current:
        outcome = "Oförändrat"
    elif legacy is None and current is not None:
        outcome = "Återvunnet värde"
    elif legacy is not None and current is None:
        outcome = "Regression"
    else:
        outcome = "Ändrat värde"
    return {"supported": True, "legacy": legacy, "current": current, "outcome": outcome}


def parser_fix_impact_audit(cases, *, field: str, limit=9, timeout=8, max_workers=4, fetcher=None):
    """Replay selected pages through legacy and current parser behaviour."""
    selected = [dict(c) for c in cases if str(c.get("url") or "").strip()][:max(1, int(limit))]
    if not selected:
        return {"field": field, "reviewed": 0, "analyzable": 0, "recovered": 0, "regressions": 0,
                "changed": 0, "classification": "Inga granskningsbara fall", "rows": []}

    def default_fetch(url):
        if not _safe_public_http_url(url):
            raise ValueError("URL är inte en publik HTTP/HTTPS-adress")
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Upplevio/0.75 impact-audit"})
        r.raise_for_status()
        return r.text

    fetch = fetcher or default_fetch
    rows_by_i = {}
    workers = max(1, min(int(max_workers), len(selected), 6))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, c["url"]): (i, c) for i, c in enumerate(selected)}
        for future in as_completed(futures):
            i, case = futures[future]
            try:
                html = future.result()
                cmp = compare_parser_versions(html, field=field, current_start_time=case.get("start_time") or None)
                row = {**case, **cmp, "error": ""}
            except Exception as exc:
                row = {**case, "supported": field in {"start_time", "price"}, "legacy": None, "current": None,
                       "outcome": "Kunde inte granska", "error": type(exc).__name__}
            rows_by_i[i] = row

    rows = [rows_by_i[i] for i in range(len(selected))]
    analyzable = sum(1 for r in rows if r["outcome"] != "Kunde inte granska" and r.get("supported"))
    recovered = sum(1 for r in rows if r["outcome"] == "Återvunnet värde")
    regressions = sum(1 for r in rows if r["outcome"] == "Regression")
    changed = sum(1 for r in rows if r["outcome"] == "Ändrat värde")

    if field not in {"start_time", "price"}:
        classification = "Ingen v0.74-fix för detta fält"
    elif analyzable < 3:
        classification = "För lite underlag"
    elif regressions or changed:
        classification = "Granska avvikelse"
    elif recovered >= 2:
        classification = "Mätbar förbättring i replay"
    elif recovered == 0:
        classification = "Ingen mätbar replay-effekt"
    else:
        classification = "Liten replay-effekt"

    return {"field": field, "reviewed": len(rows), "analyzable": analyzable, "recovered": recovered,
            "regressions": regressions, "changed": changed, "classification": classification, "rows": rows,
            "note": "Replay jämför samma HTML mot pre-v0.74 och aktuell parser. Det är inte samma sak som verifierad produktionspåverkan."}
