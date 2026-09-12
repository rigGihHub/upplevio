
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/'app.py'

def test_go_now_ui_exists():
    t=APP.read_text()
    assert '➜ Go Now' in t
    assert 'TID + AVSTÅND · INTE RESTIDSLOFTE' in t
    assert 'Kontrollera alltid faktisk restid innan du åker.' in t

def test_go_now_not_a_second_ranker():
    t=APP.read_text()
    assert 'go_now_score' not in t
    assert 'rank_go_now' not in t

def test_go_now_tracks_own_surface():
    assert '"go_now" if _go_now_active' in APP.read_text()

def test_go_now_requires_city_distance():
    t=APP.read_text()
    assert 'distance_from_city(e, origin_city)' in t

def test_go_now_identity_survives_future_releases():
    assert "Go Now" in APP.read_text()
