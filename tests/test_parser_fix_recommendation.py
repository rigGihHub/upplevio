from parser_fix_recommendation import build_parser_fix_recommendation


def batch(field="end_time", classification="Återkommande parserkandidat", n=4):
    rows=[]
    for i in range(n):
        rows.append({"title":f"E{i}","date":"2026-09-20","url":f"https://x/{i}",
                     "status":"Parserkandidat","kind":"explicit_time","value":"22:30","snippet":"19:00–22:30"})
    return {"field":field,"classification":classification,"analyzable":n,
            "parser_candidates":n,"candidate_rate":1.0,"rows":rows}


def test_recommendation_targets_showtime_parser_for_end_time():
    r=build_parser_fix_recommendation(batch(), source="Conventum")
    assert r["ready"] is True
    assert r["target_module"] == "showtime_enrichment.py"
    assert r["target_function"] == "extract_explicit_showtime"
    assert "Räkna aldrig" in r["recommendation"]
    assert len(r["examples"]) == 3


def test_detail_fields_target_detail_fact_parser():
    r=build_parser_fix_recommendation(batch(field="price"), source="X")
    assert r["target_module"] == "booking_enrichment.py"
    assert r["target_function"] == "extract_detail_facts"
    assert any("garderobsavgift" in t for t in r["required_tests"])


def test_no_recommendation_without_recurring_evidence():
    r=build_parser_fix_recommendation(batch(classification="Blandad evidens"), source="X")
    assert r["ready"] is False


def test_requires_three_concrete_candidates_even_if_classification_is_wrongly_set():
    r=build_parser_fix_recommendation(batch(n=2), source="X")
    assert r["ready"] is False


def test_unknown_field_is_not_guessed():
    r=build_parser_fix_recommendation(batch(field="booking"), source="X")
    assert r["ready"] is False
    assert "ingen säker" in r["reason"]
