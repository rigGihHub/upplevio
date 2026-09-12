from datetime import date
from candidate_local_sources import CANDIDATES, parse_orebro_church_public_calendar


def test_church_candidate_registered():
    assert CANDIDATES["orebro_church"]["name"] == "Svenska kyrkan i Örebro"


def test_public_lecture_is_candidate_and_keeps_explicit_time_and_free_status():
    html='''<article><h3><a href="/orebro/nyheter/skymningssamtal">Skymningssamtal och vernissage</a></h3><p>9/9 kl. 18:30. Fri entré. Föreläsning och vernissage.</p></article>'''
    rows=parse_orebro_church_public_calendar(html,today=date(2026,9,7))
    assert len(rows)==1
    e=rows[0]
    assert e.start_date=="2026-09-09"
    assert e.start_time=="18:30"
    assert e.price_status=="free"
    assert "community" in e.tags


def test_guided_tour_with_swedish_date_is_candidate():
    html='''<article><h3><a href="/orebro/visning">Guidad visning av Olaus Petri kyrka</a></h3><p>17 september kl. 16.30–17.30. Ingen kostnad.</p></article>'''
    rows=parse_orebro_church_public_calendar(html,today=date(2026,9,7))
    assert len(rows)==1
    assert rows[0].start_date=="2026-09-17"
    assert rows[0].start_time=="16:30"


def test_ordinary_service_and_prayer_group_are_rejected():
    html='''<ul><li><a href="/orebro/gudstjanst">Gudstjänst 13 september kl. 10.00</a></li><li><a href="/orebro/bon">Bönegrupp 15 september kl. 18.00</a></li></ul>'''
    assert parse_orebro_church_public_calendar(html,today=date(2026,9,7))==[]


def test_repeating_bible_study_is_rejected_even_if_it_says_forelasning():
    html='''<article><h3>Bibelstudium och föreläsning</h3><p>15 september kl 19.00</p></article>'''
    assert parse_orebro_church_public_calendar(html,today=date(2026,9,7))==[]
