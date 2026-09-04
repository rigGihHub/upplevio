from datetime import date

from fallback_discovery import build_fallback_suggestions
from models import Event


def ev(id, *, start_date="2026-09-05", city="Örebro", lat=59.2741, lon=15.2066,
       price_status="unknown", price_min=None, title="Event", event_type="Konsert", tags=None):
    return Event(
        id=id,
        title=title,
        event_type=event_type,
        category=event_type,
        start_date=start_date,
        end_date=None,
        start_time=None,
        venue="Arena",
        city=city,
        region="Örebro",
        country="Sverige",
        latitude=lat,
        longitude=lon,
        price_status=price_status,
        price_min=price_min,
        tags=tags or [],
    )


def base_kwargs(**overrides):
    values = dict(
        when="Idag",
        today=date(2026, 9, 3),
        origin_city="Örebro",
        radius_km=25,
        price_filter="Alla priser",
        query="",
        type_filter="Alla",
        only_new=False,
        is_new=lambda e: False,
        interests=[],
    )
    values.update(overrides)
    return values


def test_suggests_longer_period_without_changing_other_filters():
    suggestions = build_fallback_suggestions([ev("later", start_date="2026-09-05")], **base_kwargs())
    assert suggestions
    assert suggestions[0].kind == "time"
    assert suggestions[0].relaxed_when == "Nästa 7 dagar"
    assert suggestions[0].relaxed_radius_km == 25
    assert suggestions[0].relaxed_price_filter == "Alla priser"


def test_suggests_nearest_radius_that_actually_has_results():
    # Karlskoga city centre is ~40 km from Örebro, so 25 km should fail and 50 km should work.
    e = ev("karlskoga", city="Karlskoga", lat=59.3267, lon=14.5239, start_date="2026-09-03")
    suggestions = build_fallback_suggestions([e], **base_kwargs())
    radius = next(s for s in suggestions if s.kind == "radius")
    assert radius.relaxed_radius_km == 50


def test_price_relaxation_is_explicit_and_unknown_price_is_not_free():
    paid = ev("paid", start_date="2026-09-03", price_status="known", price_min=300)
    unknown = ev("unknown", start_date="2026-09-03", price_status="unknown")
    suggestions = build_fallback_suggestions(
        [paid, unknown],
        **base_kwargs(price_filter="Gratis"),
    )
    price = next(s for s in suggestions if s.kind == "price")
    assert price.relaxed_price_filter == "Alla priser"
    assert {e.id for e in price.events} == {"paid", "unknown"}


def test_query_and_type_are_never_relaxed_to_fill_empty_state():
    event = ev("wrong", start_date="2026-09-05", title="Rockkonsert", event_type="Konsert")
    suggestions = build_fallback_suggestions(
        [event],
        **base_kwargs(query="pokemon", type_filter="Mässa"),
    )
    assert suggestions == []


def test_only_new_can_be_relaxed_explicitly():
    event = ev("seen", start_date="2026-09-03")
    suggestions = build_fallback_suggestions(
        [event],
        **base_kwargs(only_new=True),
    )
    new_filter = next(s for s in suggestions if s.kind == "new")
    assert new_filter.relaxed_only_new is False


def test_combined_time_radius_is_only_used_when_single_changes_do_not_help():
    event = ev("trip", start_date="2026-09-05", city="Karlskoga", lat=59.3267, lon=14.5239)
    suggestions = build_fallback_suggestions([event], **base_kwargs())
    # Time alone already works because the event is inside the configured radius only if geo says so;
    # use a farther coordinate so neither time nor radius alone is enough.
    far_later = ev("far-later", start_date="2026-09-05", city="Västerås", lat=59.6099, lon=16.5448)
    suggestions = build_fallback_suggestions([far_later], **base_kwargs())
    assert len(suggestions) == 1
    assert suggestions[0].kind == "time_radius"
    assert suggestions[0].relaxed_when == "Nästa 7 dagar"
    assert suggestions[0].relaxed_radius_km >= 100
