from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest

from discovery import discovery_rank, this_weekend
from models import Event
from ui_logic import (
    clear_price_preset, clear_time_preset, date_matches,
    event_period_matches, local_today, price_matches,
)


def event(**overrides):
    values = dict(
        id="test", title="Konsert", event_type="Konsert", category="Musik",
        start_date="2026-10-11", end_date=None, start_time=None,
        venue="Arena", city="Örebro", region="Örebro", country="Sverige",
    )
    values.update(overrides)
    return Event(**values)


@pytest.mark.parametrize("day", range(5, 12))
def test_weekend_includes_remaining_days_of_current_week(day):
    today = date(2026, 10, day)
    assert date_matches(date(2026, 10, 11), "I helgen", today)
    assert date_matches(date(2026, 10, 10), "I helgen", today) == (day <= 10)
    assert not date_matches(date(2026, 10, 17), "I helgen", today)


def test_weekend_discovery_includes_overlapping_multiday_events_on_sunday():
    sunday = date(2026, 10, 11)
    ongoing = event(start_date="2026-10-08", end_date="2026-10-12")
    next_week = event(id="next", start_date="2026-10-17")
    ended = event(id="ended", start_date="2026-10-10")
    assert event_period_matches(ongoing, "I helgen", sunday)
    assert this_weekend([ongoing, next_week, ended], today=sunday) == [ongoing]


def test_bad_dates_do_not_crash_or_remove_an_otherwise_valid_start():
    today = date(2026, 10, 11)
    assert not event_period_matches(event(start_date="bad"), "Alla datum", today)
    assert event_period_matches(event(end_date="bad"), "Idag", today)
    assert event_period_matches(event(end_date="2026-10-09"), "Idag", today)


@pytest.mark.parametrize("currency", ["EUR", "USD", "NOK", "", None])
def test_foreign_or_missing_currency_does_not_pass_a_krona_budget(currency):
    e = event(price_status="known", price_min=50, currency=currency)
    assert not price_matches(e, "Max 100 kr")
    assert price_matches(e, "Alla priser")
    rank = discovery_rank(e, price_filter="Max 100 kr", today=date(2026, 10, 5))
    assert all("budget" not in reason for reason in rank.reasons)


@pytest.mark.parametrize("amount", [-1, float("nan"), float("inf"), "50", True])
def test_invalid_prices_do_not_pass_a_budget_or_affect_value_ranking(amount):
    e = event(price_status="known", price_min=amount)
    assert not price_matches(e, "Max 100 kr")
    rank = discovery_rank(e, price_filter="Max 100 kr", today=date(2026, 10, 5))
    assert all("budget" not in reason for reason in rank.reasons)


def test_free_events_still_pass_a_budget_without_currency_conversion():
    assert price_matches(event(price_status="free", currency="EUR"), "Gratis")
    assert price_matches(event(price_status="free", currency="EUR"), "Max 100 kr")


@pytest.mark.parametrize("preset", ["Go Now", "Last Minute", "Ikväll", "I helgen"])
def test_manual_date_change_removes_only_the_time_shortcut(preset):
    state = {"nightline_preset": preset, "discover_when": "Nästa 30 dagar", "discover_price": "Gratis"}
    clear_time_preset(state)
    assert state == {"nightline_preset": None, "discover_when": "Nästa 30 dagar", "discover_price": "Gratis"}


def test_date_change_preserves_non_time_shortcuts_and_budget_change_clears_free_label():
    state = {"nightline_preset": "Gratis", "discover_price": "Alla priser"}
    clear_time_preset(state)
    assert state["nightline_preset"] == "Gratis"
    clear_price_preset(state)
    assert state["nightline_preset"] is None


def test_local_date_uses_stockholm_after_utc_midnight_boundary():
    with patch("ui_logic.datetime") as clock:
        clock.now.side_effect = lambda tz: datetime(2026, 10, 5, 22, 30, tzinfo=timezone.utc).astimezone(tz)
        assert local_today() == date(2026, 10, 6)
