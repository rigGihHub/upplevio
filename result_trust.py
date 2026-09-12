"""Trust and noise diagnostics for imported events.

Only high-confidence parser/navigation artefacts are eligible for automatic
suppression. Thin metadata remains visible; Upplevio must not bias discovery
against legitimate long-tail events simply because small organisers publish
less structured data.
"""
from __future__ import annotations

from collections import Counter
import re
import unicodedata

_HARD_NOISE_TITLES = {
    "las mer", "läs mer", "read more", "mer info", "mer information",
    "boka", "boka nu", "boka biljett", "boka biljetter", "kop biljett",
    "köp biljett", "kop biljetter", "köp biljetter", "tickets", "biljetter",
    "event", "evenemangskalender", "kalender", "program",
    "till evenemanget", "visa evenemang", "se evenemang",
}
_DATE_ONLY = re.compile(r"^(?:mon|tis|ons|tor|fre|lor|lör|son|sön)?\s*\d{1,2}(?:[./-]\d{1,2})?(?:[./-]\d{2,4})?(?:\s+[a-zåäö]{3,10})?$", re.I)
_TIME_ONLY = re.compile(r"^(?:kl\.?\s*)?\d{1,2}[:.]\d{2}$", re.I)


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def event_noise_assessment(event) -> dict:
    """Classify likely parser noise conservatively.

    severity:
      - high: safe enough to suppress automatically
      - review: suspicious, but remains visible
      - none: no parser-noise signal
    """
    title = (getattr(event, "title", "") or "").strip()
    normalized = _norm(title)
    reasons = []
    severity = "none"

    if not normalized:
        return {"severity": "high", "reasons": ["Titel saknas"]}

    if normalized in {_norm(x) for x in _HARD_NOISE_TITLES}:
        severity = "high"
        reasons.append("Titeln ser ut som navigations- eller knapptext")
    elif _DATE_ONLY.match(title) or _TIME_ONLY.match(title):
        severity = "high"
        reasons.append("Titeln består bara av datum eller tid")
    elif normalized.startswith(("http ", "https ", "www ")):
        severity = "high"
        reasons.append("Titeln ser ut som en URL")

    # Soft review signals must never suppress the event on their own.
    if severity != "high":
        if len(normalized) <= 3:
            severity = "review"
            reasons.append("Ovanligt kort titel")
        raw_titles = {
            _norm(getattr(record, "raw_title", "") or "")
            for record in (getattr(event, "source_records", []) or [])
            if _norm(getattr(record, "raw_title", "") or "")
        }
        if len(raw_titles) >= 2 and normalized not in raw_titles:
            severity = "review"
            reasons.append("Källornas råtitlar skiljer sig från den sammanslagna titeln")

    return {"severity": severity, "reasons": reasons}


def is_high_confidence_noise(event) -> bool:
    return event_noise_assessment(event)["severity"] == "high"


def result_trust_report(events) -> dict:
    rows = []
    source_high = Counter()
    source_review = Counter()

    for event in events:
        assessment = event_noise_assessment(event)
        if assessment["severity"] == "none":
            continue
        sources = sorted({str(x).strip() for x in (getattr(event, "source_names", []) or []) if str(x).strip()})
        rows.append({
            "title": getattr(event, "title", ""),
            "date": getattr(event, "start_date", ""),
            "sources": sources,
            "severity": assessment["severity"],
            "reasons": assessment["reasons"],
        })
        counter = source_high if assessment["severity"] == "high" else source_review
        for source in sources or ["Okänd källa"]:
            counter[source] += 1

    high = [x for x in rows if x["severity"] == "high"]
    review = [x for x in rows if x["severity"] == "review"]
    source_rows = []
    for source in sorted(set(source_high) | set(source_review)):
        source_rows.append({
            "source": source,
            "high_confidence_noise": source_high[source],
            "review": source_review[source],
        })
    source_rows.sort(key=lambda x: (-x["high_confidence_noise"], -x["review"], x["source"].lower()))

    return {
        "events_analyzed": len(events),
        "suppressed_high_confidence": len(high),
        "review_events": len(review),
        "high_confidence_events": high,
        "review_rows": review,
        "source_rows": source_rows,
    }
