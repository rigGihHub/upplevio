from sports_sources import parse_osk_schedule_html, parse_orebro_hockey_article_html


def test_osk_imports_only_home_matches_at_behrn_arena():
    html = '''
    <main>
      <div class="match"><div>Helsingborgs IF</div><div>vs</div><div>Örebro SK</div><div>Superettan Herrlaget</div><div>Datum</div><div>1 september 2026</div><div>Avspark</div><div>19:00</div><div>Plats</div><div>Olympia</div></div>
      <div class="match"><div>Örebro SK</div><div>vs</div><div>Östersunds FK</div><div>Superettan Herrlaget</div><div>Datum</div><div>7 september 2026</div><div>Avspark</div><div>19:05</div><div>Plats</div><div>Behrn Arena</div></div>
      <div class="match"><div>Örebro SK</div><div>vs</div><div>Nordic United FC</div><div>Superettan Herrlaget</div><div>Datum</div><div>14 september 2026</div><div>Avspark</div><div>19:00</div><div>Plats</div><div>Behrn Arena</div></div>
    </main>'''
    rows = parse_osk_schedule_html(html, source_url="https://osk.example/schedule", team_label="ÖSK Herr")
    assert [x.title for x in rows] == ["Örebro SK – Östersunds FK", "Örebro SK – Nordic United FC"]
    assert rows[0].start_date == "2026-09-07"
    assert rows[0].start_time == "19:05"
    assert rows[0].city == "Örebro"
    assert rows[0].category == "Sport"
    assert rows[0].price_status == "unknown"


def test_osk_stable_ids():
    html = '<div>Örebro SK</div><div>vs</div><div>Jitex BK</div><div>Elitettan Damlaget</div><div>Datum</div><div>20 september 2026</div><div>Avspark</div><div>14:00</div><div>Plats</div><div>Behrn Arena</div>'
    a = parse_osk_schedule_html(html, source_url="https://osk.example/dam", team_label="ÖSK Dam")
    b = parse_osk_schedule_html(html, source_url="https://osk.example/dam", team_label="ÖSK Dam")
    assert a and b and a[0].id == b[0].id


def test_hockey_article_only_emits_orebro_home_games():
    html = '''<article>
    <p>Lördag 19 september Färjestad vs Örebro</p><p>Matchen spelas i Löfbergs Arena.</p>
    <p>Torsdag 24 september Örebro vs Björklöven</p><p>Nedsläpp kl 18:00</p><p>Matchen spelas i Behrn Arena.</p>
    <p>Lördag 26 september Örebro vs Skellefteå</p><p>Nedsläpp kl 18:00</p><p>Matchen spelas i Behrn Arena.</p>
    </article>'''
    rows = parse_orebro_hockey_article_html(html, source_url="https://hockey.example/schedule")
    assert len(rows) == 2
    assert rows[0].title == "Örebro – Björklöven"
    assert rows[0].start_date == "2026-09-24"
    assert rows[0].start_time == "18:00"
    assert rows[0].venue == "Behrn Arena"


def test_hockey_unknown_price_is_not_free():
    html = '<p>Torsdag 24 september Örebro vs Björklöven</p><p>Matchen spelas i Behrn Arena. Nedsläpp kl 18:00</p>'
    rows = parse_orebro_hockey_article_html(html, source_url="https://hockey.example/schedule")
    assert rows[0].price_status == "unknown"
    assert rows[0].price_min is None
