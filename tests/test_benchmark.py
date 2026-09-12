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


def test_benchmark_reports_category_gaps_sorted_by_missed_count():
    refs = [
        BenchmarkEvent("r1", "A", "2026-09-08", "Örebro", "Venue 1", "Konsert", "Source A", "https://a.test/1", "2026-09-03"),
        BenchmarkEvent("r2", "B", "2026-09-09", "Örebro", "Venue 2", "Konsert", "Source A", "https://a.test/2", "2026-09-03"),
        BenchmarkEvent("r3", "C", "2026-09-10", "Örebro", "Venue 3", "Mässa", "Source B", "https://b.test/3", "2026-09-03"),
    ]
    report = benchmark_report(refs, [event("e1", "C", "2026-09-10")])
    assert report["category_gaps"][0]["category"] == "Konsert"
    assert report["category_gaps"][0]["missed"] == 2
    assert report["by_category"]["Mässa"]["coverage_percent"] == 100.0


def test_benchmark_reports_venue_and_source_gap_priorities():
    refs = [
        BenchmarkEvent("r1", "A", "2026-09-08", "Örebro", "Brunnsparken", "Konsert", "Visit Örebro", "https://v.test/1", "2026-09-03"),
        BenchmarkEvent("r2", "B", "2026-09-09", "Örebro", "Brunnsparken", "Konsert", "Visit Örebro", "https://v.test/2", "2026-09-03"),
        BenchmarkEvent("r3", "C", "2026-09-10", "Örebro", "Conventum", "Mässa", "Conventum", "https://c.test/3", "2026-09-03"),
    ]
    report = benchmark_report(refs, [event("e1", "C", "2026-09-10")])
    assert report["venue_gaps"][0]["venue"] == "Brunnsparken"
    assert report["venue_gaps"][0]["missed"] == 2
    assert report["source_gap_priority"][0]["reference_source"] == "Visit Örebro"
    assert report["source_gap_priority"][0]["missed"] == 2


def test_gap_diagnostics_exclude_fully_covered_buckets():
    refs = [BenchmarkEvent("r1", "A", "2026-09-08", "Örebro", "Arena", "Konsert", "Official", "https://x.test", "2026-09-03")]
    report = benchmark_report(refs, [event("e1", "A", "2026-09-08")])
    assert report["category_gaps"] == []
    assert report["venue_gaps"] == []
    assert report["source_gap_priority"] == []


def test_sample_quality_exposes_missing_discovery_segments_without_fake_score():
    from benchmark import benchmark_sample_quality

    refs = [
        BenchmarkEvent("r1", "Konsert A", "2026-09-08", "Örebro", "Arena", "Konsert", "Visit Örebro", "https://v.test/1", "2026-09-03"),
        BenchmarkEvent("r2", "Konsert B", "2026-09-09", "Örebro", "Arena", "Konsert", "Visit Örebro", "https://v.test/2", "2026-09-03"),
        BenchmarkEvent("r3", "Match", "2026-09-10", "Örebro", "Arena", "Fotboll", "ÖSK", "https://o.test/3", "2026-09-03"),
    ]
    quality = benchmark_sample_quality(refs)
    assert quality["segment_counts"]["Musik"] == 2
    assert quality["segment_counts"]["Sport"] == 1
    assert "Familj" in quality["missing_segments"]
    assert "score" not in quality
    assert quality["represented_segment_count"] == 2


def test_sample_quality_warns_when_category_and_source_dominate():
    from benchmark import benchmark_sample_quality

    refs = [
        BenchmarkEvent(f"r{i}", f"Konsert {i}", f"2026-09-{8+i:02d}", "Örebro", "Arena", "Konsert", "Visit Örebro", f"https://v.test/{i}", "2026-09-03")
        for i in range(4)
    ]
    quality = benchmark_sample_quality(refs)
    assert quality["dominant_category"]["name"] == "Konsert"
    assert quality["dominant_category"]["share_percent"] == 100.0
    assert quality["dominant_source"]["share_percent"] == 100.0
    assert any("domineras av kategorin" in warning for warning in quality["warnings"])
    assert any("domineras av källan" in warning for warning in quality["warnings"])


def test_release_benchmark_expansion_is_verified_and_broader():
    from pathlib import Path
    from benchmark import load_benchmark, benchmark_sample_quality

    path = Path(__file__).resolve().parents[1] / "data" / "benchmark_orebro_2026-09.csv"
    refs = load_benchmark(path)
    quality = benchmark_sample_quality(refs)
    assert len(refs) >= 32
    assert quality["segment_counts"]["Scen & teater"] >= 1
    assert quality["segment_counts"]["Familj"] >= 3
    assert quality["segment_counts"]["Sport"] >= 1
    added = [r for r in refs if r.checked_at == "2026-09-04"]
    assert len(added) >= 7
    assert all(r.reference_url.startswith("https://") for r in added)
    assert {"Visit Örebro", "Örebro Teater"}.issubset({r.reference_source for r in added})


def test_benchmark_reports_discovery_segment_gaps():
    refs = [
        BenchmarkEvent("r1", "Food A", "2026-09-08", "Örebro", "City", "Mat & dryck", "Official", "https://x.test/1", "2026-09-04"),
        BenchmarkEvent("r2", "Match A", "2026-09-09", "Örebro", "Arena", "Sport", "Official", "https://x.test/2", "2026-09-04"),
    ]
    report = benchmark_report(refs, [event("e1", "Match A", "2026-09-09")])
    assert report["by_segment"]["Sport"]["coverage_percent"] == 100.0
    assert report["segment_gaps"][0]["segment"] == "Mat & dryck"
    assert report["segment_gaps"][0]["missed"] == 1


def test_release_benchmark_now_represents_all_expected_segments():
    from pathlib import Path
    from benchmark import load_benchmark, benchmark_sample_quality
    path = Path(__file__).resolve().parents[1] / "data" / "benchmark_orebro_2026-09.csv"
    refs = load_benchmark(path)
    quality = benchmark_sample_quality(refs)
    assert len(refs) == 35
    assert quality["missing_segments"] == []
    assert quality["represented_segment_count"] == quality["expected_segment_count"]
