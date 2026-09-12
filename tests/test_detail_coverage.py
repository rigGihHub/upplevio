from datetime import date

from detail_coverage import detail_coverage_audit
from models import Event


def event(id="1", sources=None, **kw):
    base = dict(
        id=id, title="X", event_type="Konsert", category="Musik",
        start_date="2026-09-20", end_date=None, start_time="19:00",
        venue="Conventum Kongress", city="Örebro", region="Örebro län", country="Sverige",
        source_names=sources or ["Conventum"], price_status="unknown",
    )
    base.update(kw)
    return Event(**base)


def test_audit_measures_detail_fields_per_represented_source():
    events = [
        event("1", end_time="21:00", door_time="18:00", age_limit="13 år", price_status="known", price_min=395),
        event("2", venue="Conventum Arena"),
    ]
    report = detail_coverage_audit(events, today=date(2026, 9, 9), horizon_days=30)
    row = report["sources"][0]
    assert row["source"] == "Conventum"
    assert row["represented_events"] == 2
    assert row["single_source_events"] == 2
    assert row["start_time_coverage"] == 1.0
    assert row["end_time_coverage"] == 0.5
    assert row["price_coverage"] == 0.5
    assert row["age_limit_coverage"] == 0.5
    assert row["door_time_coverage"] == 0.5
    assert row["precise_venue_coverage"] == 1.0


def test_generic_venue_is_not_counted_as_precise():
    report = detail_coverage_audit(
        [event(venue="Conventum")], today=date(2026, 9, 9), horizon_days=30
    )
    row = report["sources"][0]
    assert row["venue_coverage"] == 1.0
    assert row["precise_venue_coverage"] == 0.0


def test_multi_source_event_is_visible_but_not_claimed_as_single_source():
    report = detail_coverage_audit(
        [event(sources=["Conventum", "Visit Örebro"], end_time="21:00")],
        today=date(2026, 9, 9), horizon_days=30,
    )
    rows = {r["source"]: r for r in report["sources"]}
    assert rows["Conventum"]["represented_events"] == 1
    assert rows["Conventum"]["single_source_events"] == 0
    assert rows["Visit Örebro"]["single_source_events"] == 0


def test_price_requires_known_or_free_status_not_numeric_field_alone():
    report = detail_coverage_audit(
        [event(price_min=99, price_status="unknown")],
        today=date(2026, 9, 9), horizon_days=30,
    )
    assert report["sources"][0]["price_coverage"] == 0.0


def test_flags_are_explainable_and_do_not_use_score():
    events = [
        event("1", end_time=None, venue="Conventum"),
        event("2", end_time=None, venue="Conventum"),
        event("3", end_time=None, venue="Conventum"),
    ]
    row = detail_coverage_audit(events, today=date(2026, 9, 9))["sources"][0]
    assert "Sluttid saknas ofta" in row["flags"]
    assert "Plats behöver förbättras" in row["flags"]
    assert "Pris saknas ofta" in row["flags"]
    assert "score" not in row


def test_future_horizon_and_demo_filter_are_respected():
    events = [
        event("in"),
        event("old", start_date="2026-09-01"),
        event("far", start_date="2026-12-31"),
        event("demo", is_demo=True),
    ]
    report = detail_coverage_audit(events, today=date(2026, 9, 9), horizon_days=30)
    assert report["events_considered"] == 1
