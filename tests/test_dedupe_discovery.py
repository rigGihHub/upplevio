from copy import deepcopy
from test_dedupe_trust import evt
from test_production_collapse import event
from dedupe import deduplicate, duplicate_score, collapse_productions


def test_live_cross_source_title_variants():
    cases = [
        ('Kardborreshowen', 'Kardborreshowen med Per Andersson'),
        ('Norra Brunn Comedy Stand-up sessions', 'Norra Brunn Standup Comedy sessions'),
        ('Oh What A Night', 'OH WHAT A NIGHT – extrainsatt matinéföreställning'),
        ('Oh What A Night', 'Oh What a Night - 14.30'),
        ('ÖSK – Ljungskile SK', 'Örebro SK – Ljungskile SK'),
    ]
    for a_title, b_title in cases:
        a, b = evt('a', a_title, 'Conventum'), evt('b', b_title, 'City Örebro', venue='')
        assert len(deduplicate([a, b])[0]) == 1, (a_title, b_title)


def test_start_times_override_same_source_identity():
    a, b = evt('a', 'Oh What A Night', 'Conventum'), evt('b', 'Oh What A Night', 'Conventum')
    b.source_records = deepcopy(a.source_records)
    a.start_time, b.start_time = '14:30', '19:30'
    assert duplicate_score(a, b) == 0
    b.start_time = None
    b.title = 'Oh What A Night - 19.30'
    assert duplicate_score(a, b) == 0
    b.start_date = '2026-09-13'
    assert duplicate_score(a, b) == 0


def test_similar_opponents_are_separate_matches():
    a, b = evt('a', 'Örebro SK – Östers IF', 'ÖSK Fotboll'), evt('b', 'Örebro SK – Östersunds FK', 'City Örebro')
    a.event_type = 'Sport'
    assert duplicate_score(a, b) == 0


def test_local_calendar_duplicate_keeps_specific_sport_classification():
    a, b = evt('a', 'ÖSK – Ljungskile SK', 'City Örebro'), evt('b', 'Örebro SK – Ljungskile SK', 'ÖSK Fotboll')
    a.event_type, a.category = 'Evenemang', 'Lokalt'
    b.event_type = b.category = 'Sport'
    merged, _ = deduplicate([a, b])
    assert len(merged) == 1 and merged[0].event_type == merged[0].category == 'Sport'


def test_distinct_venues_and_generic_presenter_titles_stay_separate():
    a, b = evt('a', 'Konsert', 'Conventum'), evt('b', 'Konsert med Annas band', 'City Örebro')
    assert len(deduplicate([a, b])[0]) == 2
    b.title, b.venue = a.title, 'Backahallen'
    assert duplicate_score(a, b) == 0


def test_fair_recurrence_has_one_card_and_retains_occurrence_links():
    a, b = event('a', 'Fokus Hjälpmedel', '2026-10-07', event_type='Evenemang'), event('b', 'Fokus Hjälpmedel', '2026-10-08', event_type='Evenemang')
    a.category = b.category = 'Mässa'
    a.official_url, b.official_url = 'https://example.se/day1', 'https://example.se/day2'
    cards = collapse_productions([a, b])
    assert len(cards) == 1
    assert cards[0]._alternate_events[0].official_url == b.official_url
    assert not hasattr(a, '_alternate_events')
    assert collapse_productions([a])[0]._alternate_events == []


def test_same_day_performances_keep_both_times_in_one_card():
    a, b = event('a', 'En särskild föreställning', '2026-10-08'), event('b', 'En särskild föreställning', '2026-10-08')
    a.start_time, b.start_time = '14:00', '19:00'
    cards = collapse_productions([a, b])
    assert len(cards) == 1
    assert cards[0]._alternate_events[0].start_time == '19:00'
