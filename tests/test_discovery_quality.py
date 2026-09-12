from models import Event
from discovery_quality import discovery_quality_report


def ev(id, title, *, date="2026-09-06", venue="Conventum", city="Örebro", event_type="Konsert", sources=None, url="https://example.com"):
    return Event(
        id=id, title=title, event_type=event_type, category=event_type,
        start_date=date, end_date=None, start_time="19:00", venue=venue,
        city=city, region="Örebro", country="SE", source_names=sources or ["Källa A"],
        official_url=url,
    )


def test_flags_generic_title_without_hiding_event():
    report = discovery_quality_report([ev("1", "Konsert")])
    assert report["events_analyzed"] == 1
    assert report["weak_title_events"][0]["issue"] in {"För generell titel", "Titeln upprepar bara kategorin"}


def test_detects_same_day_near_duplicate_titles():
    report = discovery_quality_report([
        ev("1", "Örebro Jazz Festival"),
        ev("2", "Örebro Jazzfestival"),
    ])
    assert len(report["near_duplicate_pairs"]) == 1
    assert report["near_duplicate_pairs"][0]["similarity"] >= 0.84


def test_recurring_event_on_other_date_is_not_near_duplicate():
    report = discovery_quality_report([
        ev("1", "Sagostund", date="2026-09-06"),
        ev("2", "Sagostund", date="2026-09-13"),
    ])
    assert report["near_duplicate_pairs"] == []


def test_source_concentration_warning_requires_meaningful_sample():
    events = [ev(str(i), f"Event {i}", sources=["City Örebro"]) for i in range(7)]
    report = discovery_quality_report(events)
    assert report["source_concentration"]["share_percent"] == 100.0
    assert any("City Örebro" in warning for warning in report["warnings"])


def test_missing_time_alone_is_not_treated_as_quality_failure():
    event = ev("1", "Bra titel")
    event.start_time = None
    report = discovery_quality_report([event])
    assert report["metadata_issue_events"] == []
