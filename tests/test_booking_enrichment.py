
from models import Event
from booking_enrichment import extract_booking_link, enrich_events

def test_extract_prefers_explicit_ticket_cta():
    html='<a href="/info">Läs mer</a><a href="https://secure.tickster.com/e/1">Köp biljetter</a>'
    hit=extract_booking_link(html,"https://venue.example/event/1")
    assert hit["url"]=="https://secure.tickster.com/e/1"
    assert hit["kind"]=="ticket"

def test_relative_booking_link_becomes_absolute():
    hit=extract_booking_link('<a href="/book/42">Boka</a>',"https://venue.example/event/42")
    assert hit["url"]=="https://venue.example/book/42"

def test_no_cta_means_no_guess():
    assert extract_booking_link('<a href="/event/1">Läs mer</a>',"https://venue.example/") is None

def test_enrichment_failure_preserves_events(monkeypatch):
    e=Event(id="1",title="X",event_type="Konsert",category="Musik",start_date="2026-09-10",
        end_date=None,start_time=None,venue="V",city="Örebro",region="Örebro",country="SE",
        official_url="https://bad.example/e")
    import booking_enrichment
    def boom(*a,**k): raise RuntimeError("no")
    monkeypatch.setattr(booking_enrichment,"enrich_event",boom)
    rows=enrich_events([e],max_fetches=1,workers=1)
    assert rows[0].official_url=="https://bad.example/e"
    assert rows[0].booking_url is None
