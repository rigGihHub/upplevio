from benchmark import BenchmarkEvent, benchmark_report, normalize_title
from models import Event


def event(eid, title, day, city="Örebro"):
    return Event(
        id=eid, title=title, event_type="Konsert", category="Musik",
        start_date=day, end_date=None, start_time=None,
        venue="Arena", city=city, region="Örebro", country="Sverige",
        source_names=["Test"], source_count=1,
    )


def ref(rid, title, day, city="Örebro"):
    return BenchmarkEvent(
        id=rid, title=title, start_date=day, city=city, venue="Arena",
        category="Konsert", reference_source="Official", reference_url="https://example.test",
        checked_at="2026-09-03",
    )


def test_title_normalization_handles_swedish_diacritics_and_punctuation():
    assert normalize_title("Örebro – Våra Liv!") == "orebro vara liv"


def test_benchmark_matches_same_event_with_source_suffix_difference():
    report = benchmark_report(
        [ref("r1", "The Proclaimers", "2026-09-25")],
        [event("e1", "The Proclaimers Sweden Tour '26", "2026-09-25")],
    )
    assert report["matched"] == 1
    assert report["coverage_percent"] == 100.0


def test_benchmark_requires_same_date_and_city():
    refs = [ref("r1", "Seniordagen", "2026-09-08")]
    wrong_date = event("e1", "Seniordagen", "2026-09-09")
    wrong_city = event("e2", "Seniordagen", "2026-09-08", city="Stockholm")
    report = benchmark_report(refs, [wrong_date, wrong_city])
    assert report["matched"] == 0
    assert report["missed"] == 1


def test_one_app_event_cannot_cover_two_reference_rows():
    refs = [
        ref("r1", "Testkonsert", "2026-09-20"),
        ref("r2", "Testkonsert", "2026-09-20"),
    ]
    report = benchmark_report(refs, [event("e1", "Testkonsert", "2026-09-20")])
    assert report["matched"] == 1
    assert report["missed"] == 1


def test_benchmark_reports_coverage_by_reference_source():
    refs = [
        BenchmarkEvent("r1", "A", "2026-09-08", "Örebro", "A", "Konsert", "Conventum", "https://c.test/1", "2026-09-03"),
        BenchmarkEvent("r2", "B", "2026-09-09", "Örebro", "B", "Konsert", "Visit Örebro", "https://v.test/2", "2026-09-03"),
    ]
    report = benchmark_report(refs, [event("e1", "A", "2026-09-08")])
    assert report["by_reference_source"]["Conventum"]["coverage_percent"] == 100.0
    assert report["by_reference_source"]["Visit Örebro"]["coverage_percent"] == 0.0
