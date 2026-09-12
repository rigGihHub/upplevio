
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/"app.py"

def test_tonight_mode_ui_present():
    t=APP.read_text()
    assert "Vad ska jag göra ikväll?" in t
    assert "TOPP 3 · SAMMA DISCOVERY-RANKING" in t
    assert "Fler ikväll" in t

def test_tonight_mode_does_not_define_second_ranker():
    t=APP.read_text()
    assert "rank_tonight" not in t
    assert "tonight_score" not in t

def test_tonight_surface_is_tracked():
    t=APP.read_text()
    assert '"tonight" if _tonight_active' in t

def test_tonight_identity_survives_future_releases():
    assert "Vad ska jag göra ikväll?" in APP.read_text()
