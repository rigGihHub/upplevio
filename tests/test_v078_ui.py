from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "app.py").read_text()


def test_v078_uses_two_column_main_results_and_compact_actions():
    assert 'APP_VERSION = "0.86.0"' in APP
    assert 'cols = st.columns(2)\n        for i, e in enumerate(visible_events):' in APP
    assert 'def render_card_actions' in APP
    assert 'render_card_actions(e, surface="discover")' in APP


def test_v078_collapses_repeated_productions_after_ranking():
    assert 'collapse_productions([e for _, e in ranked_results])' in APP
