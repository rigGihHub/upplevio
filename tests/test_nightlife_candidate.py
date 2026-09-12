from datetime import date
from candidate_local_sources import CANDIDATES, parse_makeriet_nightlife_calendar


def test_makeriet_candidate_registered():
    assert CANDIDATES["makeriet"]["name"] == "Makeriet i Örebro"


def test_makeriet_accepts_comedy_and_club_events():
    html="""<div><h3><a href='/event/comedy'>Norra Brunn Comedy Stand-up sessions</a></h3><p>10 september 2026 19:00 - 22:00</p></div>
    <div><h3><a href='/event/rainbow'>Rainbow Room klubbkväll</a></h3><p>19 september 2026 22:00 - 02:00</p></div>"""
    rows=parse_makeriet_nightlife_calendar(html,today=date(2026,9,8))
    assert [r.title for r in rows]==["Norra Brunn Comedy Stand-up sessions","Rainbow Room klubbkväll"]
    assert rows[0].start_time=="19:00"
    assert "comedy" in rows[0].tags
    assert "club" in rows[1].tags


def test_makeriet_rejects_food_and_drink_promotions():
    html="""<div><h3>Musselfrossa- ät så mycket du orkar för 229kr</h3><p>9 september 2026 16:30 - 22:00</p></div>
    <div><h3>Kvällens Aperitif</h3><p>11 september 2026 16:30 - 22:00</p></div>"""
    assert parse_makeriet_nightlife_calendar(html,today=date(2026,9,8))==[]


def test_makeriet_does_not_invent_free_or_accept_opening_hours():
    html="""<div><h3>DJ-klubb fredag</h3><p>12 september 2026 kl. 22:00. Biljetter i dörren.</p></div>
    <div><h3>Klubbens öppettider</h3><p>13 september 2026 12:00</p></div>"""
    rows=parse_makeriet_nightlife_calendar(html,today=date(2026,9,8))
    assert len(rows)==1
    assert rows[0].price_status=="unknown"
