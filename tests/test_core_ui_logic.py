from datetime import date
from models import Event
from ui_logic import date_matches, price_matches, price_label


def ev(**kw):
    base = dict(id="x", title="X", event_type="Konsert", category="Rock", start_date="2026-09-05", end_date=None, start_time=None, venue="Arena", city="Örebro", region="Örebro", country="Sverige")
    base.update(kw)
    return Event(**base)


def test_unknown_price_is_never_treated_as_free_or_under_budget():
    e = ev(price_status="unknown")
    assert not price_matches(e, "Gratis")
    assert not price_matches(e, "Max 250 kr")
    assert price_matches(e, "Alla priser")


def test_known_and_free_price_filters():
    assert price_matches(ev(price_status="free", price_min=0), "Gratis")
    assert price_matches(ev(price_status="known", price_min=199), "Max 250 kr")
    assert not price_matches(ev(price_status="known", price_min=299), "Max 250 kr")


def test_price_labels_are_honest():
    assert price_label(ev(price_status="unknown")) == "Pris saknas"
    assert price_label(ev(price_status="free", price_min=0)) == "Gratis"
    assert price_label(ev(price_status="known", price_min=150, price_max=250)) == "150–250 kr"


def test_weekend_preset_uses_upcoming_weekend():
    today = date(2026, 9, 3)  # Thursday
    assert date_matches(date(2026, 9, 5), "I helgen", today)
    assert date_matches(date(2026, 9, 6), "I helgen", today)
    assert not date_matches(date(2026, 9, 7), "I helgen", today)


def test_ticketmaster_price_range_is_normalized():
    from unittest.mock import patch
    import sources

    class R:
        def raise_for_status(self):
            return None
        def json(self):
            return {
                "_embedded": {"events": [{
                    "id": "priced",
                    "name": "Priced event",
                    "dates": {"start": {"localDate": "2026-09-20"}, "status": {"code": "onsale"}},
                    "_embedded": {"venues": [{"name": "Arena", "city": {"name": "Örebro"}, "country": {"name": "Sweden"}}]},
                    "classifications": [{"segment": {"name": "Music"}, "genre": {"name": "Rock"}}],
                    "priceRanges": [{"min": 195.0, "max": 395.0, "currency": "SEK"}],
                    "url": "https://example.test/priced"
                }]},
                "page": {"totalPages": 1, "totalElements": 1}
            }

    with patch("sources.requests.get", return_value=R()):
        events, _ = sources.ticketmaster_events("key", max_pages=1)
    e = events[0]
    assert e.price_status == "known"
    assert e.price_min == 195.0
    assert e.price_max == 395.0
    assert e.currency == "SEK"
