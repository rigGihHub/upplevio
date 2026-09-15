from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"


def text():
    return APP.read_text(encoding="utf-8")


def test_main_and_saved_two_column_loops_use_actual_column_count():
    t = text()
    assert "cols = st.columns(2)" in t
    assert "with cols[i % len(cols)]:" in t
    assert "with cols[i % 3]:" not in t


def test_compact_action_row_uses_icon_only_save_control():
    t = text()
    assert "st.columns([4, 1])" in t
    assert 'save_label = "♥" if e.id in fav_ids else "♡"' in t
    assert 'save_help = "Ta bort från sparat" if e.id in fav_ids else "Spara event"' in t


def test_repeated_dates_have_compact_badge_and_card_titles_are_clamped():
    t = text()
    assert "badge-dates" in t
    assert "+{len(alternate_dates)} DATUM" in t
    assert "-webkit-line-clamp:2" in t
    assert 'getattr(e, "_alternate_events", [])' in t
    assert "Fler datum" in t


def test_desktop_canvas_is_wider_and_district_descriptions_are_visually_reduced():
    t = text()
    assert "max-width:1440px" in t
    assert ".festival-districts{display:none}" in t
