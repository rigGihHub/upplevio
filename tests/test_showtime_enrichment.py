from models import Event
from showtime_enrichment import extract_explicit_showtime
import booking_enrichment


def event(**kw):
    base=dict(id="1",title="X",event_type="Evenemang",category="Övrigt",start_date="2026-09-25",
              end_date=None,start_time=None,venue="Conventum",city="Örebro",region="Örebro län",country="Sverige",
              official_url="https://www.conventum.se/arrangemang/x",quality_notes=[])
    base.update(kw)
    return Event(**base)


def test_extracts_explicit_event_range_with_context():
    hit=extract_explicit_showtime('<main>Seniordagen pågår kl. 10.00–16.00 och har fri entré.</main>')
    assert hit["start_time"] == "10:00"
    assert hit["end_time"] == "16:00"


def test_existing_start_time_can_anchor_exact_range():
    hit=extract_explicit_showtime('<main>Fredag kl. 18:00–23:00 förvandlas arenan.</main>', current_start_time="18:00")
    assert hit["end_time"] == "23:00"


def test_exact_slut_marker_requires_existing_start():
    assert extract_explicit_showtime('<main>TIDER 23:00 – Slut</main>') is None
    hit=extract_explicit_showtime('<main>TIDER 18:00 – Dörrarna öppnar 23:00 – Slut</main>', current_start_time="18:00")
    assert hit["start_time"] == "18:00"
    assert hit["end_time"] == "23:00"


def test_does_not_derive_from_duration_or_approximate_end():
    html='<main>Datum 9 september kl 18:00. Längd ca. 60 minuter utan paus.</main>'
    assert extract_explicit_showtime(html, current_start_time="18:00") is None
    html2='<main>Repetitionen pågår till ca 12.55.</main>'
    assert extract_explicit_showtime(html2, current_start_time="11:35") is None


def test_rejects_unrelated_opening_hours():
    html='<footer>Biljettkassa öppettider kl 10.00–12.00. Telefon 019-123.</footer>'
    assert extract_explicit_showtime(html) is None


def test_booking_enrichment_reuses_same_detail_fetch_for_showtime(monkeypatch):
    e=event()
    class R:
        text='<main>Seniordagen pågår kl. 10.00–16.00.</main>'
        def raise_for_status(self): pass
    monkeypatch.setattr(booking_enrichment.requests, 'get', lambda *a,**k: R())
    booking_enrichment.enrich_event(e)
    assert e.start_time == "10:00"
    assert e.end_time == "16:00"
    assert any("start-/sluttid" in n for n in e.quality_notes)


def test_enrichment_never_overwrites_verified_existing_times(monkeypatch):
    e=event(start_time="19:00",end_time="21:00")
    class R:
        text='<main>Tider 19:00–23:00</main>'
        def raise_for_status(self): pass
    monkeypatch.setattr(booking_enrichment.requests, 'get', lambda *a,**k: R())
    booking_enrichment.enrich_event(e)
    assert e.start_time == "19:00"
    assert e.end_time == "21:00"


def test_extracts_exact_standalone_start_marker():
    hit=extract_explicit_showtime('<main>TIDER 18:00 – dörrar öppnar till foaje 20:00 – start ca 22:00 – slut</main>')
    assert hit["start_time"] == "20:00"
    assert hit["end_time"] is None
    assert hit["evidence"] == "explicit_start_marker"


def test_standalone_start_marker_does_not_override_existing_verified_start():
    hit=extract_explicit_showtime('<main>TIDER 20:00 – start</main>', current_start_time="19:30")
    assert hit is None


def test_approximate_end_marker_stays_unparsed():
    hit=extract_explicit_showtime('<main>TIDER 20:00 – start ca 22:30 – slut</main>')
    assert hit["start_time"] == "20:00"
    assert hit["end_time"] is None
