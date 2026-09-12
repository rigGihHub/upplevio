from models import Event, SourceRecord
from result_trust import event_noise_assessment, is_high_confidence_noise, result_trust_report


def ev(title, source="City Örebro"):
    return Event(
        id=title, title=title, event_type="Aktivitet", category="Aktivitet",
        start_date="2026-09-06", end_date=None, start_time=None,
        venue="", city="Örebro", region="Örebro", country="SE",
        source_names=[source], official_url="https://example.com",
    )


def test_navigation_text_is_high_confidence_noise():
    assert is_high_confidence_noise(ev("Läs mer"))
    assert event_noise_assessment(ev("Köp biljett"))["severity"] == "high"


def test_date_only_title_is_high_confidence_noise():
    assert is_high_confidence_noise(ev("6/9/2026"))


def test_thin_but_legitimate_long_tail_event_remains_visible():
    event = ev("Sagostund")
    event.venue = ""
    event.start_time = None
    assert event_noise_assessment(event)["severity"] == "none"
    assert not is_high_confidence_noise(event)


def test_generic_possible_event_is_not_automatically_suppressed():
    assert not is_high_confidence_noise(ev("Konsert"))


def test_source_raw_title_disagreement_is_review_only():
    event = ev("Sammanfogad titel")
    event.source_records = [
        SourceRecord(source="A", external_id="1", raw_title="Titel A"),
        SourceRecord(source="B", external_id="2", raw_title="Titel B"),
    ]
    result = event_noise_assessment(event)
    assert result["severity"] == "review"
    assert not is_high_confidence_noise(event)


def test_report_groups_noise_by_source():
    report = result_trust_report([ev("Läs mer", "A"), ev("Boka nu", "A"), ev("Sagostund", "B")])
    assert report["suppressed_high_confidence"] == 2
    assert report["source_rows"][0]["source"] == "A"
    assert report["source_rows"][0]["high_confidence_noise"] == 2
