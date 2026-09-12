"""Deterministic regression guardrails for critical parser behaviour.

The registry is intentionally local and network-free. Cases are based on real formats
seen in supported event sources, but are reduced to the smallest HTML fixture needed
to protect the behaviour. This lets every future parser change replay historical
positive and negative expectations in the normal test suite.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from booking_enrichment import extract_booking_link, extract_detail_facts
from showtime_enrichment import extract_explicit_showtime


@dataclass(frozen=True)
class ParserGuardrail:
    id: str
    source: str
    field: str
    kind: str  # positive | negative | preserve
    html: str
    expected: Any
    page_url: str = "https://www.conventum.se/arrangemang/test/"
    current_start_time: str | None = None
    note: str = ""


def _showtime(case: ParserGuardrail):
    hit = extract_explicit_showtime(case.html, current_start_time=case.current_start_time)
    if case.field == "start_time":
        return hit.get("start_time") if hit else None
    if case.field == "end_time":
        return hit.get("end_time") if hit else None
    raise ValueError(case.field)


def _detail(case: ParserGuardrail):
    return extract_detail_facts(case.html).get(case.field)


def _booking(case: ParserGuardrail):
    hit = extract_booking_link(case.html, case.page_url)
    return hit.get("url") if hit else None


_EXTRACTORS: dict[str, Callable[[ParserGuardrail], Any]] = {
    "start_time": _showtime,
    "end_time": _showtime,
    "price": _detail,
    "door_time": _detail,
    "age_limit": _detail,
    "venue": _detail,
    "booking_url": _booking,
}


GUARDRAILS: tuple[ParserGuardrail, ...] = (
    ParserGuardrail(
        "conventum-start-marker", "Conventum", "start_time", "positive",
        "<main>TIDER 18:00 – dörrar öppnar till foaje 20:00 – start ca 22:00 – slut</main>",
        "20:00", note="Exakt märkt starttid ska fångas även när sluttiden är ungefärlig.",
    ),
    ParserGuardrail(
        "conventum-explicit-range-start", "Conventum", "start_time", "positive",
        "<main>Evenemang tider 19:00–22:30</main>", "19:00",
        note="Explicit tidsintervall ska bevara starttid.",
    ),
    ParserGuardrail(
        "conventum-explicit-range-end", "Conventum", "end_time", "positive",
        "<main>Evenemang tider 19:00–22:30</main>", "22:30",
        note="Explicit tidsintervall ska bevara sluttid.",
    ),
    ParserGuardrail(
        "conventum-approx-end-blocked", "Conventum", "end_time", "negative",
        "<main>TIDER 20:00 – start ca 22:30 – slut</main>", None,
        note="Ungefärlig sluttid får aldrig bli exakt end_time.",
    ),
    ParserGuardrail(
        "service-hours-blocked", "Generell", "start_time", "negative",
        "<footer>Biljettkassa öppettider kl 10.00–12.00. Telefon 019-123.</footer>", None,
        note="Biljettkassans öppettider är inte eventtid.",
    ),
    ParserGuardrail(
        "conventum-entre-price", "Conventum", "price", "positive",
        "<main><p>Entré 120 kr (+ serviceavgift)</p></main>", 120.0,
        note="Tydligt märkt entrépris ska fångas.",
    ),
    ParserGuardrail(
        "service-fee-not-price", "Conventum", "price", "negative",
        "<main><p>Serviceavgift 20 kr</p><p>Garderob 30 kr</p></main>", None,
        note="Serviceavgift och garderob får inte bli eventpris.",
    ),
    ParserGuardrail(
        "conventum-ticket-price", "Conventum", "price", "positive",
        "<main><p>Biljettpris: 395 kr</p></main>", 395.0,
        note="Explicit biljettpris ska fortsätta fungera.",
    ),
    ParserGuardrail(
        "conventum-door-time", "Conventum", "door_time", "positive",
        "<main><p>Dörrarna öppnar 18:00</p><p>20:00 – start</p></main>", "18:00",
        note="Explicit dörrtid ska hållas skild från starttid.",
    ),
    ParserGuardrail(
        "conventum-age-limit", "Conventum", "age_limit", "positive",
        "<main><p>Åldersgräns: 18 år</p></main>", "18 år",
        note="Arrangörens uttryckliga åldersgräns ska bevaras.",
    ),
    ParserGuardrail(
        "conventum-venue-kongress", "Conventum", "venue", "positive",
        "<main><h2>HITTA TILL CONVENTUM KONGRESS</h2></main>", "Conventum Kongress",
        note="Specifik Conventum-lokal ska kunna ersätta generisk venue.",
    ),
    ParserGuardrail(
        "tickster-strong-cta", "Generell booking safety", "booking_url", "positive",
        '<main><a href="https://secure.tickster.com/e/123">Köp biljetter</a></main>',
        "https://secure.tickster.com/e/123",
        note="Känd biljettpartner med stark CTA ska tillåtas.",
    ),
    ParserGuardrail(
        "relative-same-host-booking", "Generell booking safety", "booking_url", "positive",
        '<main><a href="/book/42">Boka</a></main>', "https://www.conventum.se/book/42",
        note="Relativ bokningslänk på officiell host ska tillåtas.",
    ),
    ParserGuardrail(
        "social-booking-blocked", "Generell booking safety", "booking_url", "negative",
        '<main><a href="https://facebook.com/example">Köp biljetter</a></main>', None,
        note="Sociala länkar får inte bli bokningslänkar.",
    ),
    ParserGuardrail(
        "javascript-booking-blocked", "Generell booking safety", "booking_url", "negative",
        '<main><a href="javascript:alert(1)">Köp biljetter</a></main>', None,
        note="Osäkra URL-schemes ska förbli blockerade.",
    ),
    ParserGuardrail(
        "unknown-external-booking-blocked", "Generell booking safety", "booking_url", "negative",
        '<main><a href="https://unknown.example/pay">Köp biljetter</a></main>', None,
        note="Okänd extern host får inte accepteras bara på CTA-text.",
    ),
)


def run_guardrail(case: ParserGuardrail) -> dict[str, Any]:
    extractor = _EXTRACTORS.get(case.field)
    if not extractor:
        return {"id": case.id, "source": case.source, "field": case.field, "kind": case.kind,
                "expected": case.expected, "actual": None, "passed": False, "note": case.note,
                "error": "Ingen extractor registrerad"}
    try:
        actual = extractor(case)
        error = ""
    except Exception as exc:  # guardrail runner must report rather than hide failures
        actual = None
        error = type(exc).__name__
    return {"id": case.id, "source": case.source, "field": case.field, "kind": case.kind,
            "expected": case.expected, "actual": actual, "passed": not error and actual == case.expected,
            "note": case.note, "error": error}


def run_guardrail_registry(cases=GUARDRAILS) -> dict[str, Any]:
    rows = [run_guardrail(c) for c in cases]
    passed = sum(1 for r in rows if r["passed"])
    by_source: dict[str, dict[str, int]] = {}
    for r in rows:
        slot = by_source.setdefault(r["source"], {"total": 0, "passed": 0, "failed": 0})
        slot["total"] += 1
        if r["passed"]:
            slot["passed"] += 1
        else:
            slot["failed"] += 1
    return {
        "total": len(rows), "passed": passed, "failed": len(rows) - passed,
        "all_passed": passed == len(rows), "by_source": by_source, "rows": rows,
    }
