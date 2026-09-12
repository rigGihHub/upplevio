
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Optional

@dataclass(frozen=True)
class BookingCTA:
    label: str
    url: str
    kind: str              # booking | ticket | schedule | info
    confidence: str        # high | medium | low
    track_as_booking: bool

_GENERIC_PATHS = {"", "/", "/sv", "/sv/", "/en", "/en/"}
_BOOKING_HINTS = ("book", "boka", "booking", "reserve", "reservation", "checkout")
_TICKET_HINTS = ("ticket", "biljett", "tickets", "biljetter", "eventim", "ticketmaster")
_SCHEDULE_HINTS = ("time", "times", "tider", "schedule", "calendar", "kalender")

def _path(url: Optional[str]) -> str:
    if not url:
        return ""
    try:
        return (urlparse(url).path or "/").lower()
    except Exception:
        return ""

def is_generic_landing_page(url: Optional[str]) -> bool:
    return bool(url) and _path(url) in _GENERIC_PATHS

def classify_url(url: Optional[str]) -> tuple[str, str]:
    """Conservative URL-only classification. We never call an info page a booking."""
    if not url:
        return ("none", "low")
    low = url.lower()
    path = _path(url)
    if any(x in low for x in _BOOKING_HINTS):
        return ("booking", "high")
    if any(x in low for x in _TICKET_HINTS):
        return ("ticket", "high")
    if any(x in low for x in _SCHEDULE_HINTS):
        return ("schedule", "medium")
    if is_generic_landing_page(url):
        return ("info", "low")
    # Deep event/product pages are useful, but not enough evidence to claim "Boka".
    if path.count("/") >= 2:
        return ("info", "medium")
    return ("info", "low")

def booking_cta(event) -> Optional[BookingCTA]:
    """Choose honest CTA wording. Explicit booking_url is trusted over inferred URLs."""
    explicit = getattr(event, "booking_url", None)
    if explicit:
        return BookingCTA("Boka", explicit, "booking", "high", True)

    ticket = getattr(event, "ticket_url", None)
    if ticket:
        kind, confidence = classify_url(ticket)
        if kind in {"booking", "ticket"}:
            return BookingCTA("Köp biljett" if kind == "ticket" else "Boka",
                              ticket, kind, confidence, True)
        if kind == "schedule":
            return BookingCTA("Se tider", ticket, kind, confidence, False)
        return BookingCTA("Läs mer", ticket, "info", confidence, False)

    official = getattr(event, "official_url", None)
    if official:
        kind, confidence = classify_url(official)
        if kind == "schedule":
            return BookingCTA("Se tider", official, kind, confidence, False)
        # Do not turn a generic/deep official info page into a booking claim.
        return BookingCTA("Läs mer", official, "info", confidence, False)
    return None

def cta_quality(event) -> dict:
    cta = booking_cta(event)
    if not cta:
        return {"status": "missing", "reason": "Ingen extern länk", "cta": None}
    if cta.kind == "info" and is_generic_landing_page(cta.url):
        return {"status": "weak", "reason": "Länken går till en generell startsida", "cta": cta}
    if cta.track_as_booking:
        return {"status": "bookable", "reason": "Tydlig boknings-/biljettväg", "cta": cta}
    return {"status": "useful", "reason": "Relevant extern väg utan bokningspåstående", "cta": cta}
