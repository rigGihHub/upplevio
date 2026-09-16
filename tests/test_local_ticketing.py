from local_ticketing import parse_tickster_orebro_html


def test_tickster_orebro_requires_explicit_local_place_and_keeps_links():
    html = '''
    <div class="c-tile" data-requestcode="ABC123">
      <a class="c-tile__head" href="/se/sv/events/abc/2026-09-18/test"><h2 class="c-tile__title">Late Night Jam</h2></a>
      <div><span class="c-tile__label">18 sep 2026, Örebro Jazz, Örebro</span>
      <a class="c-button" href="https://secure.tickster.com/sv/abc">Köp</a></div>
    </div>
    <div class="c-tile" data-requestcode="AWAY">
      <a class="c-tile__head" href="/away"><h2 class="c-tile__title">Bortaevenemang</h2></a>
      <span class="c-tile__label">19 sep 2026, Konserthuset, Västerås</span>
    </div>'''
    rows = parse_tickster_orebro_html(html, source_url="https://www.tickster.com/se/sv/events/in/%C3%B6rebro")
    assert len(rows) == 1
    assert rows[0].title == "Late Night Jam"
    assert rows[0].start_date == "2026-09-18"
    assert rows[0].venue == "Örebro Jazz"
    assert rows[0].official_url == "https://www.tickster.com/se/sv/events/abc/2026-09-18/test"
    assert rows[0].ticket_url == "https://secure.tickster.com/sv/abc"
    assert rows[0].event_type == "Konsert"
    assert rows[0].category == "Musik"
    assert rows[0].price_status == "unknown"


def test_tickster_orebro_uses_only_explicit_category_signals():
    html = '''
    <div class="c-tile" data-requestcode="FOOD">
      <a class="c-tile__head" href="/food"><h2 class="c-tile__title">Vinmakarmiddag</h2></a>
      <span class="c-tile__label">24 sep 2026, Makeriet, Örebro</span>
    </div>
    <div class="c-tile" data-requestcode="CLUB">
      <a class="c-tile__head" href="/club"><h2 class="c-tile__title">Fredag på Ritz</h2></a>
      <span class="c-tile__label">25 sep 2026, The Ritz, Örebro</span>
    </div>'''
    rows = parse_tickster_orebro_html(html, source_url="https://www.tickster.com/se/sv/events/in/%C3%B6rebro")
    assert [(row.event_type, row.category) for row in rows] == [
        ("Mat & dryck", "Mat & dryck"),
        ("Nattliv", "Nattliv"),
    ]
