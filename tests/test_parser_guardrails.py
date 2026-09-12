from parser_guardrails import GUARDRAILS, run_guardrail_registry


def test_registry_has_positive_and_negative_cases_across_critical_fields():
    fields = {c.field for c in GUARDRAILS}
    kinds = {c.kind for c in GUARDRAILS}
    assert {"start_time", "end_time", "price", "booking_url", "door_time", "age_limit", "venue"} <= fields
    assert {"positive", "negative"} <= kinds
    assert len(GUARDRAILS) >= 15


def test_all_registered_parser_guardrails_pass():
    report = run_guardrail_registry()
    assert report["failed"] == 0, [r for r in report["rows"] if not r["passed"]]
    assert report["all_passed"] is True


def test_registry_exposes_source_level_summary():
    report = run_guardrail_registry()
    assert report["by_source"]["Conventum"]["total"] >= 8
    assert report["by_source"]["Generell booking safety"]["failed"] == 0
