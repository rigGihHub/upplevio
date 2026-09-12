from datetime import date

from discovery import discovery_rank, rank_discovery
from discovery_data_quality import discovery_data_quality_assessment, discovery_data_quality_report
from models import Event


def ev(**kw):
    base = dict(
        id="x", title="Lokal konsert", event_type="Konsert", category="Musik",
        start_date="2026-09-11", end_date=None, start_time=None,
        venue="Conventum", city="Örebro", region="Örebro", country="Sverige",
        latitude=59.274, longitude=15.207, source_names=["Conventum"],
        source_count=1, data_quality="source_verified", price_status="unknown",
    )
    base.update(kw)
    return Event(**base)


def test_missing_secondary_metadata_is_not_penalised():
    event = ev(start_time=None, end_time=None, door_time=None, age_limit=None, price_status="unknown", ticket_url=None)
    assessment = discovery_data_quality_assessment(event)
    assert assessment["level"] == "pass"
    rank = discovery_rank(event, "Örebro", today=date(2026, 9, 11))
    assert "ofullständig kärndata" not in rank.reasons


def test_missing_both_venue_and_city_caps_score_but_keeps_event_visible():
    broken = ev(id="broken", title="Pokémon Expo", venue="", city="")
    healthy = ev(id="healthy", title="Vanlig konsert")
    broken_rank = discovery_rank(broken, "Örebro", query="pokemon", today=date(2026, 9, 11))
    assert broken_rank.score <= 18
    assert "ofullständig kärndata" in broken_rank.reasons
    ranked = rank_discovery([broken, healthy], origin_city="Örebro", query="", today=date(2026, 9, 11))
    assert {e.id for _, e in ranked} == {"broken", "healthy"}


def test_end_before_start_is_restricted():
    event = ev(start_date="2026-09-12", end_date="2026-09-11")
    assessment = discovery_data_quality_assessment(event)
    assert assessment["level"] == "restricted"
    assert any("före startdatum" in x for x in assessment["restricted_reasons"])


def test_price_inconsistency_is_review_only_not_rank_penalty():
    event = ev(price_status="known", price_min=None)
    assessment = discovery_data_quality_assessment(event)
    assert assessment["level"] == "review"
    rank = discovery_rank(event, "Örebro", today=date(2026, 9, 11))
    assert rank.score > 18
    assert "ofullständig kärndata" not in rank.reasons


def test_report_separates_restricted_review_and_pass():
    report = discovery_data_quality_report([
        ev(id="ok"),
        ev(id="restricted", venue="", city=""),
        ev(id="review", price_status="known", price_min=None),
    ])
    assert report["events_analyzed"] == 3
    assert report["pass"] == 1
    assert report["restricted"] == 1
    assert report["review"] == 1
