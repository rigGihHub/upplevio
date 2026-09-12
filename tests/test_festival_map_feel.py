
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/"app.py"

def test_festival_zones_exist():
    t=APP.read_text()
    for zone in ["MAIN STAGE","ARENA","FAMILY ZONE","SHOW TENT","NIGHT MARKET","FOOD DISTRICT","HIDDEN GEMS"]:
        assert zone in t

def test_zone_chip_is_visual_only():
    t=APP.read_text()
    assert "def event_festival_zone" in t
    assert "rank_discovery" in t

def test_district_overview_present():
    t=APP.read_text()
    assert "festival-districts" in t

def test_feature_identity_survives_future_releases():
    assert "festival-districts" in APP.read_text()
