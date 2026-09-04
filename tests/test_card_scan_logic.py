from datetime import date
from models import Event
from ui_logic import compact_date_label, compact_location_label


def event(**overrides):
    base = dict(id="1", title="Test", event_type="Sport", category="Sport", start_date="2026-09-04", end_date=None,
                start_time="19:05:00", venue="Behrn Arena", city="Örebro", region="Örebro", country="Sverige")
    base.update(overrides)
    return Event(**base)


def test_compact_date_uses_today_and_time():
    assert compact_date_label(event(), date(2026, 9, 4)) == "Idag · 19:05"


def test_compact_date_uses_tomorrow():
    assert compact_date_label(event(start_date="2026-09-05", start_time=None), date(2026, 9, 4)) == "Imorgon"


def test_compact_date_uses_swedish_weekday():
    assert compact_date_label(event(start_date="2026-09-06", start_time="14:00"), date(2026, 9, 4)) == "sön 6 sep · 14:00"


def test_location_combines_venue_city_and_exact_distance():
    assert compact_location_label(event(), 3, approximate=False) == "Behrn Arena, Örebro · 3 km"


def test_location_marks_centroid_distance_as_approximate():
    assert compact_location_label(event(), 12, approximate=True) == "Behrn Arena, Örebro · ca 12 km"


def test_location_never_duplicates_same_venue_and_city():
    assert compact_location_label(event(venue="Örebro"), None) == "Örebro"
