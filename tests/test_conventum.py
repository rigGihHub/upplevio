from datetime import date
from official_sources import _event, _parse_conventum_date, parse_conventum_html


def test_compact_conventum_date_uses_current_year_for_upcoming_event():
    assert _parse_conventum_date("tisdag 8/9", today=date(2026, 9, 3)) == "2026-09-08"


def test_compact_conventum_date_rolls_to_next_year_when_month_is_past():
    assert _parse_conventum_date("fredag 8/1", today=date(2026, 9, 3)) == "2027-01-08"


def test_conventum_parser_accepts_only_event_links_with_date_and_title():
    html = '''
    <div class="event-card">
      <span>tisdag 8/9</span>
      <h2>Seniordagen</h2>
      <a href="/arrangemang/4408/">Läs mer</a>
    </div>
    <div><h2>Nyheter</h2><a href="/om-oss/">Läs</a></div>
    '''
    rows = parse_conventum_html(html, today=date(2026, 9, 3))
    assert len(rows) == 1
    assert rows[0].title == "Seniordagen"
    assert rows[0].start_date == "2026-09-08"
    assert rows[0].city == "Örebro"
    assert rows[0].official_url == "https://www.conventum.se/arrangemang/4408/"


def test_conventum_parser_deduplicates_duplicate_links():
    html = '''
    <div><span>fredag 25/9</span><h2>Örebro Oktoberfest 2026</h2><a href="/arrangemang/oktoberfest/">Bild</a><a href="/arrangemang/oktoberfest/">Titel</a></div>
    '''
    rows = parse_conventum_html(html, today=date(2026, 9, 3))
    assert len(rows) == 1


def test_official_event_ids_are_stable_sha1_not_python_hash():
    one = _event("conventum", "https://example.test/e/1", "Testevent", "8 september 2026", "Conventum", "Örebro")
    two = _event("conventum", "https://example.test/e/1", "Testevent", "8 september 2026", "Conventum", "Örebro")
    assert one.id == two.id
    assert one.id.startswith("conventum-")
