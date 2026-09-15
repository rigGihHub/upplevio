from types import SimpleNamespace

from dedupe import collapse_productions, same_production


def event(id, title, date, venue="Örebro Teater", city="Örebro", event_type="Teater"):
    return SimpleNamespace(id=id, title=title, start_date=date, venue=venue, city=city, event_type=event_type, category="Scen", tags=[])


def test_repeated_production_different_dates_collapses_for_discovery_and_keeps_alt_date():
    a = event("a", "Den gudomliga komedin", "2026-09-15")
    b = event("b", "Den gudomliga komedin", "2026-09-17")
    assert same_production(a, b) is True
    collapsed = collapse_productions([a, b])
    assert [e.id for e in collapsed] == ["a"]
    assert collapsed[0]._alternate_dates == ["2026-09-17"]
    assert [e.id for e in collapsed[0]._alternate_events] == ["b"]


def test_repeated_production_keeps_all_alternate_events_in_date_order():
    a = event("a", "Den gudomliga komedin", "2026-09-15")
    c = event("c", "Den gudomliga komedin", "2026-09-19")
    b = event("b", "Den gudomliga komedin", "2026-09-17")
    collapsed = collapse_productions([a, c, b])
    assert collapsed[0]._alternate_dates == ["2026-09-17", "2026-09-19"]
    assert [e.id for e in collapsed[0]._alternate_events] == ["b", "c"]


def test_same_title_different_city_does_not_collapse():
    a = event("a", "Exit Poll", "2026-09-15", city="Örebro")
    b = event("b", "Exit Poll", "2026-09-16", city="Stockholm")
    assert same_production(a, b) is False


def test_different_titles_same_venue_do_not_collapse():
    a = event("a", "Exit Poll", "2026-09-15")
    b = event("b", "Den gudomliga komedin", "2026-09-16")
    assert same_production(a, b) is False


def test_sport_repeats_are_not_collapsed_across_dates():
    a = event("a", "Örebro SK - Nordic United FC", "2026-09-13", venue="Behrn Arena", event_type="Sport")
    b = event("b", "Örebro SK - Nordic United FC", "2026-10-20", venue="Behrn Arena", event_type="Sport")
    a.category = b.category = "Sport"
    assert same_production(a, b) is False
    assert [e.id for e in collapse_productions([a, b])] == ["a", "b"]
