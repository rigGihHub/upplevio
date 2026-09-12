from datetime import date

from models import Event
from source_value import source_value_report


def event(event_id, sources, start="2026-09-10", demo=False):
    return Event(
        id=event_id,
        title=event_id,
        event_type="Övrigt",
        category="Övrigt",
        start_date=start,
        end_date=None,
        start_time=None,
        venue="Örebro",
        city="Örebro",
        region="Örebro län",
        country="Sverige",
        source_names=list(sources),
        source_count=len(sources),
        is_demo=demo,
    )


def test_source_value_separates_unique_and_overlap():
    events = [
        event("a-only", ["A"]),
        event("a-b", ["A", "B"]),
        event("b-only", ["B"]),
        event("a-only-2", ["A"]),
    ]
    report = source_value_report(events, horizon_days=30, today=date(2026, 9, 4))
    rows = {row["source"]: row for row in report["sources"]}

    assert report["events"] == 4
    assert report["sole_source_events"] == 3
    assert report["multi_source_events"] == 1
    assert rows["A"]["represented_events"] == 3
    assert rows["A"]["unique_events"] == 2
    assert rows["A"]["overlap_events"] == 1
    assert round(rows["A"]["unique_share_percent"], 1) == 66.7
    assert rows["B"]["unique_events"] == 1
    assert report["overlap_pairs"] == [{"source_a": "A", "source_b": "B", "shared_events": 1}]


def test_source_value_excludes_demo_outside_horizon_and_invalid_dates():
    events = [
        event("valid", ["A"]),
        event("demo", ["A"], demo=True),
        event("old", ["A"], start="2026-09-01"),
        event("far", ["A"], start="2026-11-01"),
        event("bad", ["A"], start="not-a-date"),
    ]
    report = source_value_report(events, horizon_days=30, today=date(2026, 9, 4))
    assert report["events"] == 1
    assert report["sources"][0]["represented_events"] == 1


def test_signal_avoids_strong_claim_on_small_sample():
    report = source_value_report(
        [event("one", ["Tiny"]), event("two", ["Tiny"])],
        horizon_days=30,
        today=date(2026, 9, 4),
    )
    assert report["sources"][0]["signal"] == "För litet underlag"
