
from pathlib import Path
APP=Path(__file__).resolve().parents[1]/"app.py"

def test_last_minute_ui_exists():
    t=APP.read_text()
    assert "⚡ Last Minute" in t
    assert "30–180 MIN · SÄKER STARTTID" in t
    assert "Fler som börjar snart" in t

def test_last_minute_is_not_a_second_ranker():
    t=APP.read_text()
    assert "last_minute_score" not in t
    assert "rank_last_minute" not in t

def test_last_minute_surface_is_tracked():
    assert '"last_minute"' in APP.read_text()

def test_booking_signal_requires_actual_booking_cta():
    t=APP.read_text()
    assert "_cta = booking_cta(_e)" in t
    assert "_cta.track_as_booking" in t

def test_last_minute_identity_survives_future_releases():
    assert "⚡ Last Minute" in APP.read_text()
