from models import Event
from source_health import assess_source_health, safe_import_error, source_health_summary


def event(source="Conventum", url="https://example.test/e", city="Örebro", start_date="2026-09-10"):
    return Event(
        id="x", title="Testevent", event_type="Evenemang", category="Övrigt",
        start_date=start_date, end_date=None, start_time=None, venue="Test", city=city,
        region="Örebro", country="Sverige", official_url=url, ticket_url=None,
        source_names=[source], source_count=1, is_demo=False
    )


def test_zero_active_source_is_flagged_but_seasonal_empty_is_not():
    rows = [
        ("Conventum", "OK", 0, "Officiell kalender"),
        ("Lov Örebro", "Säsongstom", 0, "Lovkalender"),
    ]
    report = assess_source_health(rows, [])
    assert report[0].state == "Kontrollera"
    assert report[1].state == "Säsongstom"


def test_import_failure_triggers_public_warning():
    report = assess_source_health([("Visit Sweden", "Fel", 0, "Importen misslyckades")], [])
    summary = source_health_summary(report)
    assert report[0].state == "Fel"
    assert summary["has_public_warning"] is True


def test_many_missing_urls_flags_likely_parser_regression():
    rows = [("Conventum", "OK", 3, "Officiell kalender")]
    events = [event(url=None) for _ in range(3)]
    report = assess_source_health(rows, events)
    assert report[0].state == "Kontrollera"
    assert "saknar käll-/biljettlänk" in report[0].summary


def test_single_missing_url_does_not_create_noise():
    rows = [("Conventum", "OK", 1, "Officiell kalender")]
    report = assess_source_health(rows, [event(url=None)])
    assert report[0].state == "OK"


def test_safe_error_never_echoes_exception_message_or_url():
    exc = RuntimeError("secret-key=abc123 https://example.test/?apikey=abc123")
    message = safe_import_error(exc)
    assert "abc123" not in message
    assert "http" not in message
