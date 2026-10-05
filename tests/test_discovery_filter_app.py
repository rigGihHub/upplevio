from datetime import timedelta
from pathlib import Path

from streamlit.testing.v1 import AppTest

import db
import engagement
import sources
from models import Event
from ui_logic import local_today


def test_manual_filter_changes_remove_stale_shortcuts_in_app(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "events.db")
    monkeypatch.setattr(engagement, "TRACKING_DB", tmp_path / "engagement.db")
    tomorrow = Event(
        id="tomorrow", title="Test imorgon", event_type="Konsert", category="Musik",
        start_date=(local_today() + timedelta(days=1)).isoformat(), end_date=None,
        start_time="12:00", venue="Testarena", city="Örebro", region="Örebro",
        country="Sverige", source_names=["Testkälla"],
    )
    monkeypatch.setattr(sources, "load_events", lambda *args, **kwargs: ([tomorrow], []))
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10).run()
    assert not app.exception
    app.button(key="nightline-Ikväll").click().run()
    assert not app.exception
    assert app.selectbox(key="discover_when").value == "Idag"
    assert app.session_state["nightline_preset"] == "Ikväll"
    # The empty view can explicitly suggest tomorrow as a wider-date alternative.
    assert any('class="result-summary"><b>0</b> event' in element.value for element in app.markdown)

    app.selectbox(key="discover_when").select("Nästa 7 dagar").run()
    assert not app.exception
    assert app.session_state["nightline_preset"] is None
    assert any('class="result-summary"><b>1</b> event' in element.value for element in app.markdown)
    assert any("Test imorgon" in element.value for element in app.markdown)

    app.button(key="nightline-Gratis").click().run()
    assert not app.exception
    assert app.selectbox(key="discover_price").value == "Gratis"
    app.selectbox(key="discover_price").select("Alla priser").run()
    assert not app.exception
    assert app.session_state["nightline_preset"] is None
    assert any("Test imorgon" in element.value for element in app.markdown)
