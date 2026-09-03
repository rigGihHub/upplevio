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
