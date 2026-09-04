from datetime import date, timedelta

PRICE_FILTERS = {
    "Alla priser": None,
    "Gratis": 0,
    "Max 100 kr": 100,
    "Max 250 kr": 250,
    "Max 500 kr": 500,
}

DATE_FILTER_DAYS = {
    "Idag": 0,
    "I helgen": None,
    "Nästa 7 dagar": 7,
    "Nästa 30 dagar": 30,
    "Nästa 3 månader": 92,
}


def price_matches(event, price_filter: str) -> bool:
    limit = PRICE_FILTERS.get(price_filter)
    if limit is None:
        return True
    status = getattr(event, "price_status", "unknown") or "unknown"
    if limit == 0:
        return status == "free"
    if status == "free":
        return True
    if status != "known":
        return False
    price_min = getattr(event, "price_min", None)
    return price_min is not None and price_min <= limit


def date_matches(event_date: date, preset: str, today: date) -> bool:
    if event_date < today:
        return False
    if preset == "Idag":
        return event_date == today
    if preset == "I helgen":
        days_to_sat = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_to_sat)
        sunday = saturday + timedelta(days=1)
        return saturday <= event_date <= sunday
    days = DATE_FILTER_DAYS.get(preset)
    if days is None:
        return True
    return event_date <= today + timedelta(days=days)


def price_label(event) -> str:
    status = getattr(event, "price_status", "unknown") or "unknown"
    currency = getattr(event, "currency", "SEK") or "SEK"
    suffix = " kr" if currency.upper() == "SEK" else f" {currency.upper()}"
    if status == "free":
        return "Gratis"
    if status != "known":
        return "Pris saknas"
    low = getattr(event, "price_min", None)
    high = getattr(event, "price_max", None)
    if low is None:
        return "Pris saknas"
    if high is not None and high > low:
        return f"{low:g}–{high:g}{suffix}"
    return f"Från {low:g}{suffix}"


def event_period_matches(event, preset: str, today: date) -> bool:
    """Match date presets against an event interval, not only its start date."""
    try:
        start = date.fromisoformat(event.start_date)
    except Exception:
        return False
    try:
        end = date.fromisoformat(event.end_date) if getattr(event, "end_date", None) else start
    except Exception:
        end = start
    if end < today:
        return False
    effective_start = max(start, today)
    if preset == "Idag":
        return start <= today <= end
    if preset == "I helgen":
        days_to_sat = (5 - today.weekday()) % 7
        saturday = today + timedelta(days=days_to_sat)
        sunday = saturday + timedelta(days=1)
        return effective_start <= sunday and end >= saturday
    days = DATE_FILTER_DAYS.get(preset)
    if days is None:
        return True
    window_end = today + timedelta(days=days)
    return effective_start <= window_end and end >= today


SWEDISH_WEEKDAYS = ["mån", "tis", "ons", "tors", "fre", "lör", "sön"]
SWEDISH_MONTHS = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]

def compact_date_label(event, today: date) -> str:
    """Short Swedish date label optimized for event cards."""
    try:
        start = date.fromisoformat(event.start_date)
    except Exception:
        return "Datum saknas"
    if start == today:
        base = "Idag"
    elif start == today + timedelta(days=1):
        base = "Imorgon"
    else:
        base = f"{SWEDISH_WEEKDAYS[start.weekday()]} {start.day} {SWEDISH_MONTHS[start.month-1]}"
    time = (getattr(event, "start_time", None) or "").strip()
    if time:
        # APIs often return seconds; minutes are enough for discovery cards.
        time = time[:5] if len(time) >= 5 else time
        return f"{base} · {time}"
    return base

def compact_location_label(event, distance=None, approximate=False) -> str:
    venue = (getattr(event, "venue", None) or "").strip()
    city = (getattr(event, "city", None) or "").strip()
    if venue and city and venue.casefold() != city.casefold():
        place = f"{venue}, {city}"
    else:
        place = venue or city or "Plats ej angiven"
    if distance is not None:
        prefix = "ca " if approximate else ""
        place += f" · {prefix}{distance:g} km"
    return place

DISCOVERY_DEFAULTS = {
    "city": "Örebro",
    "when": "Nästa 7 dagar",
    "radius_km": 50,
    "price": "Alla priser",
}


def discovery_context_label(city: str, when: str, radius_km: int | None, price_filter: str) -> str:
    """Compact human-readable summary of the active core discovery choices."""
    parts = [city or "Hela Sverige", when]
    if city and city != "Hela Sverige" and radius_km is not None:
        parts.append(f"inom {int(radius_km)} km")
    if price_filter and price_filter != "Alla priser":
        parts.append(price_filter.lower())
    return " · ".join(parts)
