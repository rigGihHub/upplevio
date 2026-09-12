from datetime import date

from detail_gap_workflow import detail_gap_cases, gap_workflow_summary
from models import Event, SourceRecord


def event(id, source="Conventum", **kw):
    base = dict(
        id=id, title=f"Event {id}", event_type="Konsert", category="Musik",
        start_date="2026-09-20", end_date=None, start_time="19:00",
        venue="Conventum Kongress", city="Örebro", region="Örebro län", country="Sverige",
        source_names=[source], source_records=[SourceRecord(source=source, external_id=id, source_url=f"https://example.se/{id}")],
        official_url=f"https://official.example/{id}", price_status="unknown",
    )
    base.update(kw)
    return Event(**base)


def test_clean_missing_case_is_returned_with_source_url():
    rows = detail_gap_cases([event("1", end_time=None)], source="Conventum", field="end_time", today=date(2026, 9, 9))
    assert len(rows) == 1
    assert rows[0]["attribution"] == "Enkällsevent"
    assert rows[0]["url"] == "https://example.se/1"
    assert rows[0]["url_basis"] == "Källans URL"


def test_present_field_is_not_returned():
    rows = detail_gap_cases([event("1", end_time="21:00")], source="Conventum", field="end_time", today=date(2026, 9, 9))
    assert rows == []


def test_multi_source_prefers_selected_sources_record_url():
    e = event(
        "1", source_names=["A", "B"],
        source_records=[
            SourceRecord(source="A", external_id="a", source_url="https://a.se/e/1"),
            SourceRecord(source="B", external_id="b", source_url="https://b.se/e/1"),
        ],
        official_url="https://a.se/e/1", end_time=None,
    )
    rows = detail_gap_cases([e], source="B", field="end_time", today=date(2026, 9, 9))
    assert rows[0]["url"] == "https://b.se/e/1"
    assert rows[0]["attribution"] == "Fler-källsevent"


def test_clean_cases_sort_before_multi_source_cases():
    clean = event("clean", start_date="2026-09-22", end_time=None)
    multi = event("multi", start_date="2026-09-20", source_names=["Conventum", "B"], end_time=None)
    rows = detail_gap_cases([multi, clean], source="Conventum", field="end_time", today=date(2026, 9, 9))
    assert rows[0]["event_id"] == "clean"


def test_summary_exposes_attribution_and_url_coverage():
    cases = [
        {"clean_attribution": True, "url": "https://a.se"},
        {"clean_attribution": False, "url": ""},
    ]
    summary = gap_workflow_summary(cases)
    assert summary == {
        "cases": 2, "clean_cases": 1, "multi_source_cases": 1,
        "cases_with_url": 1, "url_coverage": 0.5,
    }


def test_demo_and_outside_horizon_are_ignored():
    rows = detail_gap_cases([
        event("demo", is_demo=True, end_time=None),
        event("far", start_date="2026-12-20", end_time=None),
    ], source="Conventum", field="end_time", today=date(2026, 9, 9))
    assert rows == []
