
from models import Event
from booking_partners import identify_booking_partner, attribution_for_url, apply_booking_partner_attribution, partner_report

def ev(i, url=None):
    return Event(id=str(i),title=f"E{i}",event_type="Konsert",category="Musik",
        start_date="2026-09-10",end_date=None,start_time=None,venue="V",
        city="Örebro",region="Örebro",country="SE",booking_url=url)

def test_identifies_tickster_subdomain():
    p=identify_booking_partner("https://secure.tickster.com/sv/abc")
    assert p and p.name=="Tickster"

def test_identifies_eventim():
    p=identify_booking_partner("https://www.eventim.se/event/foo")
    assert p and p.key=="eventim"

def test_unknown_booking_domain_is_direct_not_fake_partner():
    d=attribution_for_url("https://orebrokonserthus.com/boka/123")
    assert d["key"]=="direct"
    assert d["direct"] is True
    assert d["affiliate_status"]=="unassessed"

def test_known_partner_is_not_claimed_affiliate_enabled():
    d=attribution_for_url("https://ticketmaster.se/event/1")
    assert d["name"]=="Ticketmaster"
    assert d["affiliate_status"]=="unassessed"

def test_apply_attribution_populates_event_fields():
    e=ev(1,"https://nortic.se/ticket/event/1")
    apply_booking_partner_attribution([e])
    assert e.booking_partner=="Nortic"
    assert e.booking_partner_key=="nortic"
    assert e.booking_partner_domain=="nortic.se"

def test_partner_report_counts_normalized_partners():
    a=ev(1,"https://secure.tickster.com/a")
    b=ev(2,"https://www.tickster.com/b")
    c=ev(3,"https://venue.example/book")
    r=partner_report([a,b,c])
    tickster=next(x for x in r["partners"] if x["key"]=="tickster")
    assert tickster["bookable_events"]==2
    assert r["total_bookable"]==3
