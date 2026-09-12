from datetime import date

from detail_coverage import detail_coverage_audit
from detail_gap_prioritizer import detail_gap_priorities
from models import Event


def event(id, source="Conventum", **kw):
    base = dict(
        id=id, title="X", event_type="Konsert", category="Musik",
        start_date="2026-09-20", end_date=None, start_time="19:00",
        venue="Conventum Kongress", city="Örebro", region="Örebro län", country="Sverige",
        source_names=[source], price_status="unknown",
    )
    base.update(kw)
    return Event(**base)


def test_high_priority_uses_clean_single_source_gap():
    events = [event(str(i), end_time=None) for i in range(5)]
    audit = detail_coverage_audit(events, today=date(2026, 9, 9))
    rows = detail_gap_priorities(audit)
    end = next(r for r in rows if r["field"] == "end_time")
    assert end["priority"] == "Hög prioritet"
    assert end["single_source_missing_events"] == 5
    assert "5 av 5 enkällsevent" in end["reason"]
    assert "score" not in end


def test_tiny_sample_is_not_promoted():
    audit = detail_coverage_audit([event("1")], today=date(2026, 9, 9))
    rows = detail_gap_priorities(audit)
    assert rows
    assert all(r["priority"] == "För lite data" for r in rows)


def test_multi_source_gap_is_explicitly_weaker_signal():
    events = [event(str(i), source="A", source_names=["A", "B"], end_time=None) for i in range(6)]
    audit = detail_coverage_audit(events, today=date(2026, 9, 9))
    rows = detail_gap_priorities(audit)
    a_end = next(r for r in rows if r["source"] == "A" and r["field"] == "end_time")
    assert a_end["priority"] == "Hög prioritet · fler-källsignal"
    assert a_end["single_source_missing_events"] == 0
    assert "proveniensen" in a_end["reason"]


def test_well_covered_field_is_omitted_by_default():
    events = [event(str(i), end_time="21:00", price_status="known", price_min=100,
                    age_limit="18 år", door_time="18:00", booking_url="https://tickster.com/x") for i in range(5)]
    audit = detail_coverage_audit(events, today=date(2026, 9, 9))
    rows = detail_gap_priorities(audit)
    assert not any(r["field"] == "end_time" for r in rows)
    assert not any(r["field"] == "price" for r in rows)


def test_cleaner_missing_opportunity_sorts_before_weaker_one():
    events = [event(str(i), source="A", end_time=None) for i in range(5)]
    events += [event(f"b{i}", source="B", source_names=["B", "C"], end_time=None) for i in range(6)]
    rows = detail_gap_priorities(detail_coverage_audit(events, today=date(2026, 9, 9)))
    end_rows = [r for r in rows if r["field"] == "end_time"]
    assert end_rows[0]["source"] == "A"
