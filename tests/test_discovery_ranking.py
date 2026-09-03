from datetime import date

from discovery import discovery_rank, rank_discovery
from models import Event


def ev(**kw):
    base = dict(
        id="x", title="Konsert", event_type="Konsert", category="Musik",
        start_date="2026-09-10", end_date=None, start_time=None,
        venue="Conventum", city="Örebro", region="Örebro", country="Sverige",
        latitude=59.274, longitude=15.207, source_names=["Conventum"],
        source_count=1, data_quality="source_verified", price_status="unknown",
    )
    base.update(kw)
    return Event(**base)


def test_near_and_soon_ranks_above_far_and_later():
    near = ev(id="near", title="Nära", start_date="2026-09-05")
    far = ev(id="far", title="Långt", city="Stockholm", latitude=59.3293, longitude=18.0686, start_date="2026-09-25")
    ranked = rank_discovery([far, near], origin_city="Örebro", today=date(2026, 9, 3))
    assert ranked[0][1].id == "near"


def test_explicit_title_query_is_strong_relevance_signal():
    title_hit = ev(id="title", title="Pokémonmässa", start_date="2026-09-20")
    description_hit = ev(id="desc", title="Helgaktivitet", description="Pokémon och spel", start_date="2026-09-05")
    a = discovery_rank(title_hit, "Örebro", query="pokemon", today=date(2026, 9, 3))
    b = discovery_rank(description_hit, "Örebro", query="pokemon", today=date(2026, 9, 3))
    assert a.score > b.score
    assert "matchar din sökning tydligt" in a.reasons


def test_unknown_price_gets_no_value_bonus():
    unknown = ev(price_status="unknown")
    free = ev(id="free", price_status="free", price_min=0)
    a = discovery_rank(unknown, "Örebro", price_filter="Alla priser", today=date(2026, 9, 3))
    b = discovery_rank(free, "Örebro", price_filter="Alla priser", today=date(2026, 9, 3))
    assert b.score > a.score
    assert "gratis" in b.reasons
    assert all("budget" not in r for r in a.reasons)


def test_source_trust_is_only_small_tiebreaker():
    relevant = ev(id="relevant", title="Pokémon festival", source_names=["Okänd källa"], data_quality="partial")
    trusted = ev(id="trusted", title="Annan aktivitet", source_names=["Ticketmaster", "Conventum"], source_count=2, data_quality="multi_source")
    a = discovery_rank(relevant, "Örebro", query="pokemon", today=date(2026, 9, 3))
    b = discovery_rank(trusted, "Örebro", query="", today=date(2026, 9, 3))
    assert a.score > b.score


def test_rank_reasons_are_short_and_explainable():
    e = ev(price_status="free", price_min=0, source_names=["Ticketmaster", "Conventum"], source_count=2, data_quality="multi_source")
    rank = discovery_rank(e, "Örebro", query="konsert", today=date(2026, 9, 3))
    assert 1 <= len(rank.reasons) <= 3
    assert all(isinstance(reason, str) and reason for reason in rank.reasons)


def test_interest_profile_boosts_matching_event_without_filtering_others():
    cards = ev(id="cards", title="Pokémon Card Show", category="Samlarkort", tags=["Samlarkort"])
    other = ev(id="other", title="Lokal föreläsning", category="Övrigt", tags=[])
    a = discovery_rank(cards, "Örebro", today=date(2026, 9, 3), interests=["Samlarkort & TCG"])
    b = discovery_rank(other, "Örebro", today=date(2026, 9, 3), interests=["Samlarkort & TCG"])
    assert a.score > b.score
    assert any("Samlarkort & TCG" in reason for reason in a.reasons)


def test_interest_profile_does_not_override_strong_explicit_query():
    query_hit = ev(id="q", title="Jazzkväll", category="Musik")
    interest_hit = ev(id="i", title="Pokémonmässa", category="Samlarkort", tags=["Samlarkort"])
    a = discovery_rank(query_hit, "Örebro", query="jazz", today=date(2026, 9, 3), interests=["Samlarkort & TCG"])
    b = discovery_rank(interest_hit, "Örebro", query="jazz", today=date(2026, 9, 3), interests=["Samlarkort & TCG"])
    assert a.score > b.score


def test_query_filter_normalizes_accents_too():
    from discovery import event_matches_query
    pokemon = ev(title="Pokémonmässa")
    assert event_matches_query(pokemon, "pokemon") is True
