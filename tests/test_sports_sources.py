from sports_sources import (
    parse_laget_next_match_html,
    parse_osk_schedule_html,
    parse_orebro_hockey_article_html,
    parse_orebro_hockey_schedule_payload,
)
from datetime import date


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


def test_hockey_schedule_only_emits_orebro_home_games_at_behrn():
    payload = {"gameInfo": [
        {
            "uuid": "home-1", "startDateTime": "2026-09-24T18:00:00+02:00",
            "homeTeam": {"teamNames": {"long": "Örebro HK"}},
            "awayTeam": {"displayName": "Björklöven"},
            "arena": {"name": "Behrn Arena"},
        },
        {
            "uuid": "away-1", "startDateTime": "2026-09-19T18:00:00+02:00",
            "homeTeam": {"displayName": "Färjestad BK"},
            "awayTeam": {"displayName": "Örebro HK"},
            "arena": {"name": "Löfbergs Arena"},
        },
        {
            "uuid": "wrong-venue", "startDateTime": "2026-10-01T19:00:00+02:00",
            "homeTeam": {"displayName": "Örebro HK"},
            "awayTeam": {"displayName": "Luleå Hockey"},
            "arena": {"name": "Okänd arena"},
        },
    ]}
    rows = parse_orebro_hockey_schedule_payload(payload, source_url="https://hockey.example/schedule")
    assert len(rows) == 1
    assert rows[0].title == "Örebro HK – Björklöven"
    assert rows[0].start_date == "2026-09-24"
    assert rows[0].start_time == "18:00"
    assert rows[0].official_url == "https://hockey.example/schedule"


def test_laget_next_match_imports_explicit_local_match():
    html = """<div>Nästa match för Herr A</div><div>Pirates Basketball</div>
    <div>26 sep, 15:00</div><div>Idrottshuset, stora hallen</div>"""
    rows = parse_laget_next_match_html(
        html, source_key="kfum_orebro_basket", source_url="https://basket.example",
        team_name="KFUM Örebro Basket", sport="Basket", today=date(2026, 9, 15),
    )
    assert len(rows) == 1
    assert rows[0].title == "KFUM Örebro Basket – Pirates Basketball"
    assert rows[0].start_date == "2026-09-26"
    assert rows[0].venue == "Idrottshuset, stora hallen"


def test_laget_next_match_rejects_away_or_unknown_location():
    html = "<div>Nästa match</div><div>Motståndarna</div><div>20 sep, 14:00</div><div>Sporthallen, Västerås</div>"
    assert parse_laget_next_match_html(
        html, source_key="ibf_orebro", source_url="https://example.test",
        team_name="IBF Örebro", sport="Innebandy", today=date(2026, 9, 15),
    ) == []
