from datetime import timedelta
from pathlib import Path

import pytest
import streamlit as st
from bs4 import BeautifulSoup
from streamlit.testing.v1 import AppTest

import db
import engagement
import sources
from models import Event
from ui_logic import compact_date_label, local_today


@pytest.mark.parametrize("with_optional_details", [False, True])
def test_repeated_event_details_use_html_without_markdown_code_blocks(monkeypatch, tmp_path, with_optional_details):
    st.cache_data.clear()
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "events.db")
    monkeypatch.setattr(engagement, "TRACKING_DB", tmp_path / "engagement.db")
    today = local_today()
    events = [
        Event(
            id=f"performance-{offset}", title="Den gudomliga komedin", event_type="Teater",
            category="Scen", start_date=(today + timedelta(days=offset)).isoformat(),
            end_date=None, start_time=None, venue="Örebro Teater", city="Örebro",
            region="Örebro", country="Sverige", source_names=["Teatern", "Visit Örebro"],
            source_count=2, official_url=f"https://example.com/performance/{offset}",
            door_time="18:00" if with_optional_details else None,
            age_limit="13 år" if with_optional_details else None,
            description='En berättelse om <livet> & kärleken.\n\n    Andra akten.' if with_optional_details else "",
        )
        for offset in [1, 3]
    ]
    monkeypatch.setattr(sources, "load_events", lambda *args, **kwargs: (events, []))
    try:
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10).run()
        assert not app.exception
        buttons = [button for button in app.button if button.key.startswith("details-btn-discover-")]
        assert len(buttons) == 1  # Repeat performances share a single discovery card.
        buttons[0].click().run()
        assert not app.exception
        # st.html bypasses the Markdown parser, even with missing optional fields
        # or blank lines and indentation inside a published description.
        detail_html = next(element.proto.body for element in app.get("html") if 'class="inline-detail"' in element.proto.body)
        detail = BeautifulSoup(detail_html, "html.parser")
        assert detail.select_one(".detail-trust").get_text() == "Bekräftat från 2 källor · Teatern, Visit Örebro"
        assert compact_date_label(events[1], today) in detail.select_one(".alternate-dates").get_text()
        assert not detail.select("pre, code, script")
        assert not any('class="inline-detail"' in element.value for element in app.markdown)
        assert any("performance/3" in element.proto.url for element in app.get("link_button"))
        if with_optional_details:
            assert "Dörrar/insläpp 18:00" in detail.get_text()
            assert "Åldersgräns: 13 år" in detail.get_text()
            assert "<livet> & kärleken" in detail.p.get_text()
            assert detail.select_one("livet") is None
    finally:
        st.cache_data.clear()
