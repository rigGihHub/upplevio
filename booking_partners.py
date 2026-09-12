
from dataclasses import dataclass
from urllib.parse import urlparse
from collections import Counter

@dataclass(frozen=True)
class BookingPartner:
    key: str
    name: str
    domains: tuple[str, ...]
    affiliate_status: str = "unassessed"  # unassessed | potential | enabled | unavailable

PARTNERS = (
    BookingPartner("ticketmaster", "Ticketmaster", ("ticketmaster.se","ticketmaster.com")),
    BookingPartner("tickster", "Tickster", ("tickster.com","secure.tickster.com")),
    BookingPartner("eventim", "Eventim", ("eventim.se","eventim.com")),
    BookingPartner("nortic", "Nortic", ("nortic.se",)),
    BookingPartner("billetto", "Billetto", ("billetto.se","billetto.com")),
)

def hostname(url: str | None) -> str:
    if not url:
        return ""
    try:
        host=(urlparse(url).hostname or "").lower().strip(".")
    except Exception:
        return ""
    return host[4:] if host.startswith("www.") else host

def identify_booking_partner(url: str | None) -> BookingPartner | None:
    host=hostname(url)
    if not host:
        return None
    for partner in PARTNERS:
        for domain in partner.domains:
            if host == domain or host.endswith("." + domain):
                return partner
    return None

def attribution_for_url(url: str | None) -> dict:
    partner=identify_booking_partner(url)
    if partner:
        return {
            "key": partner.key,
            "name": partner.name,
            "domain": hostname(url),
            "affiliate_status": partner.affiliate_status,
            "direct": False,
        }
    host=hostname(url)
    if host:
        return {
            "key": "direct",
            "name": host,
            "domain": host,
            "affiliate_status": "unassessed",
            "direct": True,
        }
    return {
        "key": "unknown", "name": "Okänd", "domain": "",
        "affiliate_status": "unassessed", "direct": False,
    }

def apply_booking_partner_attribution(events):
    for event in events:
        url=getattr(event,"booking_url",None) or getattr(event,"ticket_url",None)
        if not url:
            continue
        data=attribution_for_url(url)
        event.booking_partner_key=data["key"]
        event.booking_partner=data["name"]
        event.booking_partner_domain=data["domain"]
        event.affiliate_status=data["affiliate_status"]
    return events

def partner_report(events):
    rows=Counter()
    total_bookable=0
    for event in events:
        url=getattr(event,"booking_url",None) or getattr(event,"ticket_url",None)
        if not url:
            continue
        total_bookable += 1
        data=attribution_for_url(url)
        rows[(data["key"],data["name"],data["affiliate_status"],data["direct"])] += 1
    result=[
        {"key":k,"name":name,"affiliate_status":status,"direct":direct,"bookable_events":count}
        for (k,name,status,direct),count in rows.items()
    ]
    result.sort(key=lambda r:(-r["bookable_events"],r["name"].casefold()))
    return {"partners":result,"total_bookable":total_bookable}
