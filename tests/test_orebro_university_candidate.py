from candidate_local_sources import (
    CANDIDATES,
    parse_orebro_university_public_calendar,
)


def test_candidate_is_registered_but_not_a_default_source_registry_item():
    assert CANDIDATES["orebro_university"]["name"] == "Örebro universitet"


def test_parses_explicit_open_public_orebro_event_with_time():
    html = '''
    <ul><li><a href="/kalendarium/event/social-impact-day/">
    Social Impact Day – upptäck idéer och innovationer som gör skillnad
    10 september 2026 10:00 – 18:45 Innovasalen, Örebro universitet
    Öppet för alla Välkommen till Örebro universitet.
    </a></li></ul>
    '''
    rows = parse_orebro_university_public_calendar(html)
    assert len(rows) == 1
    e = rows[0]
    assert e.title.startswith("Social Impact Day")
    assert e.start_date == "2026-09-10"
    assert e.start_time == "10:00"
    assert e.city == "Örebro"
    assert e.source_names == ["Örebro universitet"]
    assert "öppet för alla" in e.tags


def test_rejects_event_without_explicit_open_for_all_marker():
    html = '''<a href="/x">Docenturföreläsning: Test Person 8 september 2026 10:00 Hörsal M, Örebro universitet</a>'''
    assert parse_orebro_university_public_calendar(html) == []


def test_rejects_student_or_staff_only_even_if_marker_is_malformed_nearby():
    html = '''<a href="/x">Valet 2026 10 september 2026 13:15 – 15:00 Hörsal G, Örebro universitet Öppet för alla Föreläsningarna är endast öppna för studenter och anställda.</a>'''
    assert parse_orebro_university_public_calendar(html) == []


def test_rejects_grythyttan_for_orebro_local_candidate_audit():
    html = '''<a href="/x">Årets kockelever 15 september 2026 09:00 Campus Grythyttan Öppet för alla Örebro universitet arrangerar.</a>'''
    assert parse_orebro_university_public_calendar(html) == []


def test_rejects_remote_stockholm_event():
    html = '''<a href="/x">Digital Sovereignty in the Age of AI 8 oktober 2026 13:00 IVA Konferenscenter, Stockholm Öppet för alla Örebro universitet.</a>'''
    assert parse_orebro_university_public_calendar(html) == []


def test_rejects_digital_event_from_local_candidate():
    html = '''<a href="/x">Dance for Health 10 september 2026 14:30 Örebro universitet Öppet för alla Digitalt seminarium.</a>'''
    assert parse_orebro_university_public_calendar(html) == []


def test_duplicate_same_link_across_markup_only_returns_once():
    html = '''
    <div><a href="/x">Fira Nobeldagen med forskning 10 december 2026 10:00 Aula Nova - Campus Örebro Öppet för alla Örebro universitet.</a></div>
    <div><a href="/x">Fira Nobeldagen med forskning 10 december 2026 10:00 Aula Nova - Campus Örebro Öppet för alla Örebro universitet.</a></div>
    '''
    rows = parse_orebro_university_public_calendar(html)
    assert len(rows) == 1
