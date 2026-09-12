
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"

def test_future_carnival_identity_is_present():
    text=APP.read_text()
    assert "FUTURE CARNIVAL" in text
    assert "--pink:#ff4fd8" in text
    assert "--cyan:#67e8f9" in text
    assert "future-marquee" in text

def test_core_product_promise_remains():
    text=APP.read_text()
    assert "Hitta det du inte vill missa." in text

def test_ui_avoids_heavy_media_dependencies():
    text=APP.read_text()
    assert "<video" not in text.lower()
    assert "background-image:url(" not in text.replace(" ","").lower()

def test_admin_keeps_control_room_treatment():
    text=APP.read_text()
    assert "Kontrollrum" in text
    assert "admin-note" in text

def test_future_carnival_identity_survives_future_releases():
    text=APP.read_text()
    assert "FUTURE CARNIVAL" in text
