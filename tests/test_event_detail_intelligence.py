from models import Event
import booking_enrichment
from booking_enrichment import extract_detail_facts


def event(**kw):
    base=dict(id="1", title="X", event_type="Konsert", category="Musik", start_date="2026-10-24",
              end_date=None, start_time="19:00", venue="Conventum", city="Örebro", region="Örebro län", country="Sverige",
              official_url="https://www.conventum.se/arrangemang/x", quality_notes=[])
    base.update(kw)
    return Event(**base)


def test_extracts_explicit_doors_age_and_exact_conventum_venue():
    html='''<main>\nTIDER\n18:00 – dörrar öppnar till foaje och bar\n18:30 – dörrar öppnar till salong\n19:00 – start\nÅLDERSGRÄNS\n7 år\nHITTA TILL CONVENTUM KONGRESS\nFabriksgatan 19\n</main>'''
    facts=extract_detail_facts(html)
    assert facts["door_time"] == "18:00"
    assert facts["age_limit"] == "7 år"
    assert facts["venue"] == "Conventum Kongress"


def test_preserves_descriptive_age_rule():
    facts=extract_detail_facts('<main>ÅLDERSGRÄNS\n18 år, yngre OK i vuxet sällskap</main>')
    assert facts["age_limit"] == "18 år, yngre OK i vuxet sällskap"


def test_does_not_turn_relative_door_wording_into_exact_time():
    facts=extract_detail_facts('<main>Föreställning kl. 16:00. Dörrarna öppnar en timma innan föreställningen.</main>')
    assert facts["door_time"] is None


def test_garderobe_fee_is_not_event_price():
    facts=extract_detail_facts('<main>GARDEROB Garderob pris 30 kr betalas med Swish.</main>')
    assert facts["price"] is None


def test_only_explicit_price_label_is_used():
    facts=extract_detail_facts('<main>Biljettpris: 495 kr\nGarderob pris 30 kr</main>')
    assert facts["price"] == 495.0


def test_enrichment_adds_practical_info_without_overwriting_existing(monkeypatch):
    e=event(age_limit="Ingen åldersgräns")
    class R:
        text='''<main>18:00 – dörrar öppnar till foaje\nÅLDERSGRÄNS\n13 år\nHITTA TILL CONVENTUM KONGRESS</main>'''
        def raise_for_status(self): pass
    monkeypatch.setattr(booking_enrichment.requests, 'get', lambda *a,**k: R())
    booking_enrichment.enrich_event(e)
    assert e.door_time == "18:00"
    assert e.age_limit == "Ingen åldersgräns"
    assert e.venue == "Conventum Kongress"
    assert any("praktisk eventinfo" in n for n in e.quality_notes)


def test_existing_booking_url_does_not_block_detail_enrichment(monkeypatch):
    e=event(booking_url="https://secure.tickster.com/e/1")
    class R:
        text='<main>ÅLDERSGRÄNS\n13 år</main>'
        def raise_for_status(self): pass
    monkeypatch.setattr(booking_enrichment.requests, 'get', lambda *a,**k: R())
    booking_enrichment.enrich_event(e)
    assert e.age_limit == "13 år"
    assert e.booking_url == "https://secure.tickster.com/e/1"


def test_explicit_entre_price_without_word_pris_is_accepted():
    facts=extract_detail_facts('<main>Entré 120 kr (+ serviceavgift). Serviceavgift: 20 kr.</main>')
    assert facts["price"] == 120.0


def test_service_fee_alone_is_not_event_price():
    facts=extract_detail_facts('<main>Serviceavgift: 20 kr. Garderob pris 30 kr.</main>')
    assert facts["price"] is None
