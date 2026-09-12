from datetime import date
from candidate_local_sources import CANDIDATES, parse_orebro_county_museum_calendar, candidate_value_audit


def test_museum_candidate_registered():
    assert CANDIDATES["orebro_county_museum"]["name"] == "Örebro läns museum"


def test_parses_calendar_card_without_inventing_city_or_time():
    html='''<article><span>Visning</span><a href="/kalender/visning-av-kullangsstugan/">Visning av Kullängsstugan</a><span>12 september</span></article>'''
    rows=parse_orebro_county_museum_calendar(html,today=date(2026,9,7))
    assert len(rows)==1
    e=rows[0]
    assert e.start_date=="2026-09-12"
    assert e.start_time is None
    assert e.city==""
    assert e.region=="Örebro län"
    assert e.event_type=="Evenemang" or e.event_type=="Utställning" or e.event_type=="Evenemang"


def test_parses_range_and_culture_tags():
    html='''<li><a href="/kalender/bergslagens-historiedagar/">Bergslagens historiedagar</a> 19 - 27 september Arkeologi Föreläsning Hantverk Utställning Visning</li>'''
    rows=parse_orebro_county_museum_calendar(html,today=date(2026,9,7))
    assert len(rows)==1
    assert rows[0].start_date=="2026-09-19"
    assert rows[0].end_date=="2026-09-27"
    assert "utställning" in rows[0].tags


def test_rejects_navigation_without_date():
    assert parse_orebro_county_museum_calendar('<a href="/utstallningar/">Utställningar</a>',today=date(2026,9,7))==[]


def test_candidate_audit_reports_frontier_segments():
    html='''<article><a href="/kalender/x/">Konst och utställning i museet</a><span>20 september</span></article>'''
    rows=parse_orebro_county_museum_calendar(html,today=date(2026,9,7))
    audit=candidate_value_audit([],rows)
    museum=next(r for r in audit if r["source"]=="Örebro läns museum")
    assert "Museum & utställning" in museum["frontier_segments"]
