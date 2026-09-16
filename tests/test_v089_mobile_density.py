from pathlib import Path


APP = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")


def test_mobile_discovery_uses_compact_keyed_grids():
    assert 'APP_VERSION = "0.89.0"' in APP
    assert 'st.container(key="quick_choices")' in APP
    assert 'st.container(key="core_filters")' in APP
    assert '.st-key-quick_choices [data-testid="stHorizontalBlock"]' in APP
    assert 'grid-template-columns:repeat(2,minmax(0,1fr))' in APP
    assert 'type_filter = st.selectbox("🎟️ Vad?", types, key="discover_type")' in APP
    core_filters = APP.split('with st.container(key="core_filters"):', 1)[1].split('with st.expander("Fler val"', 1)[0]
    assert "💰 Budget?" not in core_filters


def test_mobile_hero_removes_secondary_slogans_only_at_mobile_breakpoint():
    mobile = APP.split("@media(max-width:800px){", 1)[1].split("</style>", 1)[0]
    assert ".hero-kicker,.future-marquee{display:none}" in mobile
    assert ".hero h1{font-size:1.85rem" in mobile
    assert '[data-testid="stToolbar"]{display:none!important}' in mobile
