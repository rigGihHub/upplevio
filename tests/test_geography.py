from models import Event
from geography import distance_info, normalize_city, resolve_event_location


def ev(**kw):
    base = dict(id="geo", title="Geo", event_type="Event", category="Övrigt", start_date="2026-09-20", end_date=None,
                start_time=None, venue="Arena", city="Örebro", region="Örebro", country="Sverige")
    base.update(kw)
    return Event(**base)


def test_orebro_event_with_exact_coordinates_gets_exact_distance():
    distance, confidence = distance_info(ev(latitude=59.2753, longitude=15.2134), "Örebro")
    assert distance == 0
    assert confidence == "exact"


def test_venue_coordinates_are_used_when_event_coordinates_are_missing():
    distance, confidence = distance_info(ev(latitude=None, longitude=None, venue_latitude=59.2753, venue_longitude=15.2134), "Örebro")
    assert distance == 0
    assert confidence == "venue"


def test_orebro_city_fallback_survives_missing_coordinates():
    distance, confidence = distance_info(ev(city="  Orebro kommun ", latitude=None, longitude=None), "Örebro")
    assert distance == 0
    assert confidence == "city"
    assert normalize_city("ÖREBRO STAD") == "Örebro"


def test_stockholm_without_coordinates_is_not_within_100km_of_orebro():
    distance, confidence = distance_info(ev(city="Stockholm", latitude=None, longitude=None), "Örebro")
    assert distance is not None and distance > 100
    assert confidence == "city"


def test_unknown_city_never_gets_fabricated_distance():
    distance, confidence = distance_info(ev(city="Okänd liten ort", latitude=None, longitude=None), "Örebro")
    assert distance is None
    assert confidence == "unknown"
    resolved = resolve_event_location(ev(city="Okänd liten ort"))
    assert resolved.latitude is None and resolved.longitude is None
