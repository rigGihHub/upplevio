
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/"app.py"

def test_nightline_quick_choices_exist():
    t=APP.read_text()
    for label in ["Ikväll","I helgen","Gratis","Nära vald stad","Hidden Gems","För familjen"]:
        assert label in t

def test_nearby_does_not_claim_gps():
    t=APP.read_text()
    assert "Nära vald stad" in t
    assert '"Nära mig"' not in t

def test_hidden_gems_uses_existing_signals():
    t=APP.read_text()
    assert 'event_festival_zone(e)[0] == "HIDDEN GEMS"' in t
    assert "is_local_discovery_tip(e)" in t

def test_nightline_can_be_cleared():
    assert "Rensa snabbval" in APP.read_text()

def test_nightline_identity_survives_future_releases():
    assert "nightline_preset" in APP.read_text()
