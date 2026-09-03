"""Conservative geographic discovery helpers for Upplevio.

Exact/venue coordinates are preferred. A curated city centroid is only used when
we can normalize the event city to a known place. Unknown places never receive
an invented distance.
"""
from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt
import re
import unicodedata

CITY_COORDS = {
    "Örebro": (59.2753, 15.2134),
    "Stockholm": (59.3293, 18.0686),
    "Göteborg": (57.7089, 11.9746),
    "Malmö": (55.6050, 13.0038),
    "Jönköping": (57.7826, 14.1618),
    "Uppsala": (59.8586, 17.6389),
    "Västerås": (59.6099, 16.5448),
    "Linköping": (58.4108, 15.6214),
    "Norrköping": (58.5877, 16.1924),
    "Karlstad": (59.3793, 13.5036),
    "Eskilstuna": (59.3712, 16.5098),
    "Karlskoga": (59.3267, 14.5239),
    "Kumla": (59.1277, 15.1434),
    "Lindesberg": (59.5920, 15.2304),
    "Nora": (59.5193, 15.0398),
    "Hallsberg": (59.0657, 15.1117),
    "Arboga": (59.3939, 15.8388),
    "Köping": (59.5140, 15.9926),
    "Oslo": (59.9139, 10.7522),
    "Köpenhamn": (55.6761, 12.5683),
}


def _key(value):
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\b(kommun|stad|city|sweden|sverige)\b", " ", text, flags=re.I)
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


_CITY_BY_KEY = {_key(city): city for city in CITY_COORDS}
# Only explicit, unambiguous aliases belong here.
_CITY_BY_KEY.update({"copenhagen": "Köpenhamn", "gothenburg": "Göteborg", "malmoe": "Malmö"})


def normalize_city(value):
    """Return a curated canonical city name, or None when the place is unknown."""
    return _CITY_BY_KEY.get(_key(value))


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * radius * atan2(sqrt(a), sqrt(1 - a))


@dataclass(frozen=True)
class GeoResolution:
    latitude: float | None
    longitude: float | None
    confidence: str  # exact | venue | city | unknown
    canonical_city: str | None = None


def resolve_event_location(event):
    lat = getattr(event, "latitude", None)
    lon = getattr(event, "longitude", None)
    if lat is not None and lon is not None:
        return GeoResolution(float(lat), float(lon), "exact", normalize_city(getattr(event, "city", "")))

    venue_lat = getattr(event, "venue_latitude", None)
    venue_lon = getattr(event, "venue_longitude", None)
    if venue_lat is not None and venue_lon is not None:
        return GeoResolution(float(venue_lat), float(venue_lon), "venue", normalize_city(getattr(event, "city", "")))

    canonical = normalize_city(getattr(event, "city", ""))
    if canonical:
        city_lat, city_lon = CITY_COORDS[canonical]
        return GeoResolution(city_lat, city_lon, "city", canonical)
    return GeoResolution(None, None, "unknown", None)


def distance_info(event, origin_city):
    origin = normalize_city(origin_city)
    if not origin:
        return None, "unknown"
    target = resolve_event_location(event)
    if target.latitude is None or target.longitude is None:
        return None, "unknown"
    origin_lat, origin_lon = CITY_COORDS[origin]
    distance = round(haversine_km(origin_lat, origin_lon, target.latitude, target.longitude))
    return distance, target.confidence


def distance_from_city(event, origin_city):
    return distance_info(event, origin_city)[0]


def coordinates_for_event(event):
    resolved = resolve_event_location(event)
    if resolved.latitude is None or resolved.longitude is None:
        return None
    return resolved.latitude, resolved.longitude
