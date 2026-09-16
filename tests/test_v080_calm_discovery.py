from pathlib import Path


APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_v080_removes_decorative_district_row_and_limits_quick_choices():
    assert 'APP_VERSION = "0.84.0"' in APP
    assert "q1, q2, q3, q4 = st.columns(4)" in APP
    assert '"Nu & snart"' in APP
    assert '<div class="festival-district"><b>' not in APP


def test_cards_limit_status_noise_and_do_not_render_source_html():
    assert "flags = flags[:2]" in APP
    assert '<div class="source">' not in APP


def test_primary_filters_share_one_desktop_row():
    assert "r1c1, r1c2, r1c3, r1c4 = st.columns(4)" in APP
