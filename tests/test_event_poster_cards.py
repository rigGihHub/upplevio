
from pathlib import Path

APP=Path(__file__).resolve().parents[1]/"app.py"

def text():
    return APP.read_text()

def test_poster_themes_exist():
    t=text()
    for theme in ["theme-music","theme-sport","theme-family","theme-stage","theme-market","theme-food","theme-other"]:
        assert theme in t

def test_visual_theme_does_not_touch_ranking_module():
    t=text()
    assert "event_visual_theme" in t
    assert "rank_discovery" in t

def test_poster_sigil_present():
    t=text()
    assert "poster-sigil" in t

def test_mobile_poster_adjustment_present():
    t=text()
    assert ".poster-sigil{width:36px" in t

def test_event_poster_identity_survives_future_releases():
    assert "theme-music" in text()
