"""Turn recurring parser evidence into a reviewable fix recommendation.

This module is intentionally advisory. It never edits parser code or Event data.
Recommendations are emitted only when batch evidence is strong enough.
"""
from __future__ import annotations

from collections import Counter


FIELD_RULES = {
    "start_time": {
        "label": "starttid",
        "module": "showtime_enrichment.py",
        "function": "extract_explicit_showtime",
        "rule": "Utöka den konservativa matchningen för uttryckliga starttider, men behåll kravet på ett faktiskt klockslag och blockera öppettider/servicetider.",
        "positive": "ett uttryckligt klockslag på en eventsida ska extraheras som starttid",
        "negative": "öppettider, biljettkassa och relativa formuleringar får inte bli starttid",
    },
    "end_time": {
        "label": "sluttid",
        "module": "showtime_enrichment.py",
        "function": "extract_explicit_showtime",
        "rule": "Utöka matchningen för uttryckliga tidsintervall eller explicit märkt sluttid. Räkna aldrig fram sluttid från längd eller ungefärlig varaktighet.",
        "positive": "ett explicit intervall som 19:00–22:30 ska ge end_time=22:30",
        "negative": "\"ca 60 minuter\" eller \"40–70 min\" får inte skapa end_time",
    },
    "door_time": {
        "label": "dörr-/insläppstid",
        "module": "booking_enrichment.py",
        "function": "extract_detail_facts",
        "rule": "Utöka matchningen för explicit märkt dörr-, insläpps- eller foajétid. Acceptera bara ett faktiskt klockslag, aldrig relativa formuleringar.",
        "positive": "\"Dörrar 18:30\" ska ge door_time=18:30",
        "negative": "\"dörrarna öppnar en timme före\" får inte räknas om till ett klockslag",
    },
    "age_limit": {
        "label": "åldersgräns",
        "module": "booking_enrichment.py",
        "function": "extract_detail_facts",
        "rule": "Utöka matchningen för uttryckligt märkta åldersgränser utan att tolka andra åldersreferenser i brödtext som entrékrav.",
        "positive": "\"Åldersgräns 18 år\" ska ge age_limit=18 år",
        "negative": "en artistbeskrivning som nämner en persons ålder får inte bli åldersgräns",
    },
    "price": {
        "label": "pris",
        "module": "booking_enrichment.py",
        "function": "extract_detail_facts",
        "rule": "Utöka endast matchning nära tydliga etiketter som Biljettpris/Entrépris/Pris. Första bästa belopp på sidan får aldrig bli eventpris.",
        "positive": "\"Biljettpris: 395 kr\" ska ge verifierat pris",
        "negative": "garderobsavgift, matpris eller andra lösa belopp får inte bli eventpris",
    },
    "precise_venue": {
        "label": "exakt venue",
        "module": "booking_enrichment.py",
        "function": "extract_detail_facts",
        "rule": "Utöka matchningen för explicit märkt lokal/plats och tillåt bara en tydligare venue än befintligt generiskt värde.",
        "positive": "\"Plats: Conventum Kongress\" ska kunna precisera ett generiskt \"Conventum\"",
        "negative": "stad, adressbrödtext eller navigationsrubriker får inte ersätta venue",
    },
}


def build_parser_fix_recommendation(batch, *, source: str):
    """Return a transparent parser-fix recommendation from a batch audit."""
    batch = batch or {}
    field = str(batch.get("field") or "")
    spec = FIELD_RULES.get(field)
    rows = list(batch.get("rows") or [])
    candidates = [r for r in rows if r.get("status") == "Parserkandidat"]

    if not spec:
        return {
            "ready": False, "reason": "Fältet har ingen säker rekommendationsmall.",
            "source": source, "field": field,
        }
    if batch.get("classification") != "Återkommande parserkandidat":
        return {
            "ready": False, "reason": "Batchen visar ännu ingen återkommande parserkandidat.",
            "source": source, "field": field,
        }
    if len(candidates) < 3:
        return {
            "ready": False, "reason": "Minst tre konkreta parserkandidater krävs.",
            "source": source, "field": field,
        }

    kinds = Counter(str(r.get("kind") or "okänd") for r in candidates)
    dominant_kind, dominant_count = kinds.most_common(1)[0]
    examples = []
    for row in candidates[:3]:
        examples.append({
            "title": row.get("title", ""), "date": row.get("date", ""),
            "url": row.get("url", ""), "value": row.get("value"),
            "snippet": row.get("snippet", ""), "kind": row.get("kind", ""),
        })

    tests = [
        f"Positivt regressionstest: {spec['positive']}.",
        f"Negativt regressionstest: {spec['negative']}.",
        "Behåll ett test där sidan saknar det valda fältet och parsern fortsatt lämnar värdet tomt.",
    ]
    if field in {"start_time", "end_time"}:
        tests.append("Behåll skydd mot att biljettkassans/telefonens öppettider feltolkas som eventtid.")

    return {
        "ready": True,
        "source": source,
        "field": field,
        "field_label": spec["label"],
        "target_module": spec["module"],
        "target_function": spec["function"],
        "recommendation": spec["rule"],
        "evidence_summary": (
            f"{len(candidates)} av {batch.get('analyzable', len(rows))} analyserbara sidor är parserkandidater "
            f"({(batch.get('candidate_rate') or 0)*100:.0f} %). Dominerande evidenstyp är {dominant_kind} "
            f"({dominant_count}/{len(candidates)} kandidater)."
        ),
        "dominant_kind": dominant_kind,
        "examples": examples,
        "required_tests": tests,
        "guardrail": "Rekommendationen är endast underlag. Ingen parserkod eller eventdata ändras automatiskt.",
    }
