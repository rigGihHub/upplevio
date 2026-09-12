
from datetime import date
from official_sources import parse_orebro_konserthus_event_page, parse_orebro_teater_calendar_html

def test_konserthus_parses_explicit_price_date_time():
    html="""<html><h1>Visitkort</h1><div>Konsertsalen</div><div>260 - 400 kronor</div>
    <div>onsdag 23 september 2026 kl 18:00</div><a href='https://tickets.example/x'>Köp biljetter</a></html>"""
    e=parse_orebro_konserthus_event_page(html,"https://www.orebrokonserthus.com/evenemang/visitkort/")
    assert e.title=="Visitkort"
    assert e.start_date=="2026-09-23"
    assert e.start_time=="18:00"
    assert e.price_status=="known"
    assert e.price_min==260 and e.price_max==400

def test_konserthus_free_only_when_explicit():
    html="<h1>Önskekonserten 2026</h1><p>lördag 22 augusti 2026 kl 14:00</p><p>fri entré</p>"
    e=parse_orebro_konserthus_event_page(html,"https://www.orebrokonserthus.com/evenemang/o/")
    assert e.price_status=="free"
    assert e.price_min is None

def test_konserthus_missing_price_is_unknown():
    html="<h1>Konsert X</h1><p>onsdag 23 september 2026 kl 18:00</p>"
    e=parse_orebro_konserthus_event_page(html,"https://www.orebrokonserthus.com/evenemang/x/")
    assert e.price_status=="unknown"

def test_teater_calendar_keeps_separate_performance_dates():
    html="""<h2>12 september 2026</h2>
    <a href='/forestallning/den-gudomliga-komedin/'>Den gudomliga komedin</a>
    <a href='/ticket/x'>Köp biljett</a>
    <h2>15 september 2026</h2>
    <a href='/forestallning/den-gudomliga-komedin/'>Den gudomliga komedin</a>"""
    rows=parse_orebro_teater_calendar_html(html)
    dates=sorted(e.start_date for e in rows)
    assert dates==["2026-09-12","2026-09-15"]
    assert all(e.source_names==["Örebro Teater"] for e in rows)

def test_teater_ignores_cta_text_as_event():
    html="<h2>29 september 2026</h2><a href='/buy'>Köp biljett</a>"
    assert parse_orebro_teater_calendar_html(html)==[]
