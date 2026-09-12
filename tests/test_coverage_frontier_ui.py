from pathlib import Path
APP=Path(__file__).resolve().parents[1]/"app.py"

def test_frontier_admin_ui_present():
    t=APP.read_text()
    assert "Örebro Coverage Frontier · 30/60/90 dagar" in t
    assert "saknas i aktuell import" in t.casefold()
    assert "Enkällsberoende" in t

def test_local_audit_wording_is_precise():
    assert "Eventtyper bland egna unika event" in APP.read_text()

def test_coverage_frontier_survives_future_releases():
    assert "Örebro Coverage Frontier" in APP.read_text()
