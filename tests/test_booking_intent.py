
from models import Event
from booking_intent import booking_cta, cta_quality, is_generic_landing_page
from engagement import booking_target

def ev(**kw):
    base=dict(id="1", title="Test", event_type="Aktivitet", category="Kultur",
        start_date="2026-09-23", end_date=None, start_time="18:00", venue="Plats",
        city="Örebro", region="Örebro", country="SE")
    base.update(kw)
    return Event(**base)

def test_explicit_booking_url_is_boka():
    e=ev(booking_url="https://partner.example/book/123")
    c=booking_cta(e)
    assert c.label=="Boka" and c.track_as_booking

def test_ticketmaster_like_url_is_ticket_cta():
    e=ev(ticket_url="https://tickets.example/event/123")
    c=booking_cta(e)
    assert c.label=="Köp biljett" and c.track_as_booking

def test_generic_official_homepage_never_claims_booking():
    e=ev(official_url="https://example.org/")
    c=booking_cta(e)
    assert c.label=="Läs mer" and not c.track_as_booking
    assert booking_target(e) is None
    assert cta_quality(e)["status"]=="weak"

def test_deep_official_event_page_is_read_more_not_fake_booking():
    e=ev(official_url="https://example.org/evenemang/visitkort/")
    c=booking_cta(e)
    assert c.label=="Läs mer"
    assert not c.track_as_booking

def test_schedule_url_is_se_tider():
    e=ev(official_url="https://example.org/calendar/event-1")
    c=booking_cta(e)
    assert c.label=="Se tider"
    assert not c.track_as_booking

def test_explicit_booking_beats_ticket_and_info():
    e=ev(booking_url="https://affiliate.example/booking/1",
         ticket_url="https://tickets.example/event/1",
         official_url="https://venue.example/events/1")
    c=booking_cta(e)
    assert c.url=="https://affiliate.example/booking/1"

def test_no_link_has_no_cta():
    e=ev()
    assert booking_cta(e) is None
    assert cta_quality(e)["status"]=="missing"
