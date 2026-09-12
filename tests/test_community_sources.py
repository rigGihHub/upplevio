from datetime import date

from community_sources import parse_lov_orebro_html
from ui_logic import event_period_matches


def test_lov_orebro_parses_free_activity_and_date_range():
    html = '''<main>
      <div class="card"><div>Gratis Lek och spel Idrott och rörelse</div><h4>Vivalla: Familjejympa med Friskis&amp;Svettis</h4><p>Rolig träning för barn och vuxna.</p><p>9 juni–11 augusti</p></div>
      <div class="card"><div>Kultur och kreativitet</div><h4>Wadköping: Sagolördag</h4><p>Berättelser för hela familjen.</p><p>14 augusti</p></div>
    </main>'''
    rows = parse_lov_orebro_html(html, source_url="https://guide.orebro.se/lovorebro/", year=2026)
    assert len(rows) == 2
    first = rows[0]
    assert first.title == "Vivalla: Familjejympa med Friskis&Svettis"
    assert first.start_date == "2026-06-09"
    assert first.end_date == "2026-08-11"
    assert first.price_status == "free"
    assert "Familj" in first.tags and "Idrott och rörelse" in first.tags
    assert rows[1].price_status == "unknown"


def test_lov_orebro_ids_are_stable():
    html = '<div><div>Gratis</div><h4>Örebro skatepark</h4><p>Sommaröppet.</p><p>13 juni–16 augusti</p></div>'
    a = parse_lov_orebro_html(html, source_url="https://example.test", year=2026)
    b = parse_lov_orebro_html(html, source_url="https://example.test", year=2026)
    assert a and b and a[0].id == b[0].id


def test_ongoing_multiday_activity_matches_today_and_next_7_days():
    html = '<div><div>Gratis</div><h4>Örebro skatepark</h4><p>Sommaröppet.</p><p>13 juni–16 augusti</p></div>'
    event = parse_lov_orebro_html(html, source_url="https://example.test", year=2026)[0]
    today = date(2026, 7, 10)
    assert event_period_matches(event, "Idag", today)
    assert event_period_matches(event, "Nästa 7 dagar", today)


def test_ended_activity_does_not_match_today():
    html = '<div><div>Gratis</div><h4>Avslutad aktivitet</h4><p>Test.</p><p>1 juni–5 juni</p></div>'
    event = parse_lov_orebro_html(html, source_url="https://example.test", year=2026)[0]
    assert not event_period_matches(event, "Idag", date(2026, 7, 10))

from community_sources import parse_city_orebro_html


def test_city_orebro_parses_local_long_tail_cards_without_inventing_price():
    html='''<main>
      <article><div>Familjevänligt, Övrigt</div><h3><a href="/evenemang/barnens-dag/">Barnens dag i city</a></h3><p>12 sep</p></article>
      <article><div>Konst</div><h3><a href="https://cityorebro.com/evenemang/wonderland/">Wonderland</a></h3><p>14 maj - 11 okt</p></article>
    </main>'''
    rows=parse_city_orebro_html(html,source_url="https://cityorebro.com/evenemang/",year=2026)
    assert len(rows)==2
    assert rows[0].title=="Barnens dag i city"
    assert rows[0].start_date=="2026-09-12"
    assert rows[0].price_status=="unknown"
    assert "Familjevänligt" in rows[0].tags
    assert rows[1].start_date=="2026-05-14" and rows[1].end_date=="2026-10-11"


def test_city_orebro_requires_explicit_date():
    html='<article><h3><a href="/evenemang/no-date/">Event utan datum</a></h3><p>Välkommen!</p></article>'
    assert parse_city_orebro_html(html,source_url="https://cityorebro.com/evenemang/",year=2026)==[]
