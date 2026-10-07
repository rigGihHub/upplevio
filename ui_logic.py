from datetime import date, datetime, timedelta
from math import isfinite

from showtimes import STOCKHOLM


def local_today():
    return datetime.now(STOCKHOLM).date()

PRICE_FILTERS = {
    "Alla priser": None,
    "Gratis": 0,
    "Max 100 kr": 100,
    "Max 250 kr": 250,
    "Max 500 kr": 500,
}

DATE_FILTER_DAYS = {"Idag": 0, "I helgen": None, "Nästa 7 dagar": 7, "Nästa 30 dagar": 30, "Nästa 3 månader": 92}

def known_price_in_sek(event):
    """Only compare an explicit, valid SEK amount with a budget in kronor."""
    if getattr(event, "price_status", "unknown") != "known":
        return None
    currency = getattr(event, "currency", None)
    if not isinstance(currency, str) or currency.strip().upper() != "SEK":
        return None
    low = getattr(event, "price_min", None)
    if isinstance(low, bool) or not isinstance(low, (int, float)):
        return None
    return low if isfinite(low) and low >= 0 else None

def price_matches(event, price_filter: str) -> bool:
    limit = PRICE_FILTERS.get(price_filter)
    if limit is None: return True
    status = getattr(event, "price_status", "unknown") or "unknown"
    if limit == 0: return status == "free"
    if status == "free": return True
    if status != "known": return False
    price_min = known_price_in_sek(event)
    return price_min is not None and price_min <= limit

def date_window(preset: str, today: date):
    if preset == "I helgen":
        # A Sunday still belongs to this weekend, rather than the next one.
        saturday = today + timedelta(days=5 - today.weekday())
        return max(today, saturday), saturday + timedelta(days=1)
    days = DATE_FILTER_DAYS.get(preset)
    return today, today + timedelta(days=days) if days is not None else date.max

def date_matches(event_date: date, preset: str, today: date) -> bool:
    window_start, window_end = date_window(preset, today)
    return window_start <= event_date <= window_end

def price_label(event) -> str:
    status = getattr(event, "price_status", "unknown") or "unknown"
    currency = getattr(event, "currency", "SEK") or "SEK"
    suffix = " kr" if currency.upper() == "SEK" else f" {currency.upper()}"
    if status == "free": return "Gratis"
    if status != "known": return "Pris saknas"
    low, high = getattr(event, "price_min", None), getattr(event, "price_max", None)
    if low is None: return "Pris saknas"
    if high is not None and high > low: return f"{low:g}–{high:g}{suffix}"
    return f"Från {low:g}{suffix}"

def event_period_matches(event, preset: str, today: date) -> bool:
    try: start = date.fromisoformat(event.start_date)
    except Exception: return False
    try: end = date.fromisoformat(event.end_date) if getattr(event, "end_date", None) else start
    except Exception: end = start
    end = max(start, end)
    window_start, window_end = date_window(preset, today)
    overlap_start, overlap_end = max(start, window_start), min(end, window_end)
    if overlap_start > overlap_end:
        return False
    excluded = {d for raw in getattr(event, "excluded_dates", []) if isinstance(raw, str) and (d := _valid_date(raw)) and overlap_start <= d <= overlap_end}
    return (overlap_end - overlap_start).days + 1 > len(excluded)


def _valid_date(raw):
    try:
        return date.fromisoformat(raw)
    except (ValueError, TypeError):
        return None


def clear_time_preset(state):
    """Manual date selection must not leave a hidden time filter active."""
    if state.get("nightline_preset") in {"Go Now", "Last Minute", "Ikväll", "I helgen"}:
        state["nightline_preset"] = None


def clear_price_preset(state):
    if state.get("nightline_preset") == "Gratis":
        state["nightline_preset"] = None

SWEDISH_WEEKDAYS = ["mån", "tis", "ons", "tors", "fre", "lör", "sön"]
SWEDISH_MONTHS = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]

def compact_date_label(event, today: date) -> str:
    try: start = date.fromisoformat(event.start_date)
    except Exception: return "Datum saknas"
    try: end = date.fromisoformat(event.end_date) if getattr(event, "end_date", None) else None
    except Exception: end = None
    if start < today and end and end >= today: return f"Pågår till {SWEDISH_WEEKDAYS[end.weekday()]} {end.day} {SWEDISH_MONTHS[end.month-1]}"
    if start == today: base = "Idag"
    elif start == today + timedelta(days=1): base = "Imorgon"
    else: base = f"{SWEDISH_WEEKDAYS[start.weekday()]} {start.day} {SWEDISH_MONTHS[start.month-1]}"
    time = (getattr(event, "start_time", None) or "").strip()
    end_time = (getattr(event, "end_time", None) or "").strip()
    if time:
        time = time[:5] if len(time) >= 5 else time
        if end_time:
            end_time = end_time[:5] if len(end_time) >= 5 else end_time
            return f"{base} · {time}–{end_time}"
        return f"{base} · {time}"
    return base

def compact_location_label(event, distance=None, approximate=False) -> str:
    venue = (getattr(event, "venue", None) or "").strip(); city = (getattr(event, "city", None) or "").strip()
    place = f"{venue}, {city}" if venue and city and venue.casefold() != city.casefold() else (venue or city or "Plats ej angiven")
    if distance is not None: place += f" · {'ca ' if approximate else ''}{distance:g} km"
    return place

DISCOVERY_DEFAULTS = {"city": "Örebro", "when": "Nästa 30 dagar", "radius_km": 50, "price": "Alla priser"}

def discovery_context_label(city: str, when: str, radius_km: int | None, price_filter: str) -> str:
    parts = [city or "Hela Sverige", when]
    if city and city != "Hela Sverige" and radius_km is not None: parts.append(f"inom {int(radius_km)} km")
    if price_filter and price_filter != "Alla priser": parts.append(price_filter.lower())
    return " · ".join(parts)
