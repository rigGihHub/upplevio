from models import Event, SourceRecord
from dedupe import deduplicate, duplicate_score, verification_label


def evt(id_, title, source, city="Örebro", venue="Conventum", date="2026-09-12", quality="partial", price_status="unknown", price_min=None):
    return Event(
        id=id_, title=title, event_type="Konsert", category="Musik", start_date=date,
        end_date=date, start_time=None, venue=venue, city=city, region="Örebro län",
        country="Sverige", source_names=[source], source_count=1,
        source_records=[SourceRecord(source=source, external_id=id_)], data_quality=quality,
        price_status=price_status, price_min=price_min,
    )


def test_cross_source_same_event_merges_and_preserves_provenance():
    a = evt("tm-1", "The Proclaimers", "Ticketmaster")
    b = evt("conv-1", "The Proclaimers – live", "Conventum")
    merged, review = deduplicate([a, b])
    assert len(merged) == 1
    assert not review
    assert merged[0].source_count == 2
    assert set(merged[0].source_names) == {"Ticketmaster", "Conventum"}
    assert len(merged[0].source_records) == 2
    assert merged[0].data_quality == "multi_source"
    assert verification_label(merged[0]) == "Bekräftat från 2 källor"


def test_conflicting_city_never_auto_merges():
    a = evt("a", "The Proclaimers", "Ticketmaster", city="Örebro")
    b = evt("b", "The Proclaimers", "Ticketmaster", city="Stockholm")
    assert duplicate_score(a, b) == 0.0
    merged, _ = deduplicate([a, b])
    assert len(merged) == 2


def test_different_titles_same_venue_do_not_merge():
    a = evt("a", "Seniordagen", "Conventum")
    b = evt("b", "Örebro Oktoberfest", "Visit Örebro")
    merged, _ = deduplicate([a, b])
    assert len(merged) == 2


def test_single_high_trust_source_is_source_verified_not_multi_source():
    a = evt("tm-1", "Konsert A", "Ticketmaster", quality="verified")
    merged, _ = deduplicate([a])
    assert merged[0].data_quality == "source_verified"
    assert verification_label(merged[0]) == "Källverifierad"


def test_unknown_price_never_turns_into_free():
    a = evt("tm-1", "Konsert A", "Ticketmaster", price_status="unknown")
    b = evt("conv-1", "Konsert A", "Conventum", price_status="unknown")
    merged, _ = deduplicate([a, b])
    assert merged[0].price_status == "unknown"


def test_explicit_price_conflict_is_flagged():
    a = evt("tm-1", "Konsert A", "Ticketmaster", price_status="known", price_min=200)
    b = evt("conv-1", "Konsert A", "Conventum", price_status="free")
    merged, _ = deduplicate([a, b])
    assert len(merged) == 1
    assert any("Priskonflikt" in note for note in merged[0].quality_notes)
