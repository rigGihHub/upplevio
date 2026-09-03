from unittest.mock import patch
from official_sources import (
    _parse_visitorebro_date_prefix,
    parse_visitorebro_editorial_html,
    visitorebro_editorial_events,
)


def test_visitorebro_date_prefix_variants():
    assert _parse_visitorebro_date_prefix("4/9 Rigmor Gustafsson. Svampen", 2026)[:2] == ("2026-09-04", "2026-09-04")
    assert _parse_visitorebro_date_prefix("2-5/9 Live At Heart. Örebro", 2026)[:2] == ("2026-09-02", "2026-09-05")
    assert _parse_visitorebro_date_prefix("1/9-13/9 Exit poll. Örebro Teater", 2026)[:2] == ("2026-09-01", "2026-09-13")
    assert _parse_visitorebro_date_prefix("28/9-4/10 Litteraturen live. Kulturkvarteret", 2026)[:2] == ("2026-09-28", "2026-10-04")


def test_visitorebro_parser_extracts_title_venue_and_free_status():
    html = """
    <html><body>
      <p>Publicerad 2025-09-05 / Uppdaterad 2026-09-01</p>
      <p>4/9 Rigmor Gustafsson. 58 meter upp, Svampen.</p>
      <p>5/9 Brickpile. Taco Bar Örebro (Fri entré).</p>
      <p>Det här är vanlig redaktionell text och ska ignoreras.</p>
    </body></html>
    """
    rows = parse_visitorebro_editorial_html(html, "https://www.visitorebro.se/artikel/test/")
    assert len(rows) == 2
    assert rows[0].start_date == "2026-09-04"
    assert rows[0].title == "Rigmor Gustafsson"
    assert rows[0].venue == "58 meter upp, Svampen"
    assert rows[0].price_status == "unknown"
    assert rows[1].price_status == "free"
    assert rows[1].price_min == 0.0


def test_visitorebro_parser_uses_stable_ids_and_no_article_description_copy():
    html = '<p>Uppdaterad 2026-09-01</p><p>25/9 Sibille Attar. Örebro Konserthus.</p>'
    a = parse_visitorebro_editorial_html(html, "https://www.visitorebro.se/artikel/a/")[0]
    b = parse_visitorebro_editorial_html(html, "https://www.visitorebro.se/artikel/a/")[0]
    assert a.id == b.id
    assert a.id.startswith("visitorebro-")
    assert a.description == ""


def test_visitorebro_multi_page_import_deduplicates_overlapping_rows():
    class R:
        def raise_for_status(self):
            return None
        text = '<p>Uppdaterad 2026-09-01</p><p>25/9 The Proclaimers. Conventum Club 700.</p>'

    with patch("official_sources.requests.get", return_value=R()):
        rows = visitorebro_editorial_events()
    assert len(rows) == 1
    assert rows[0].title == "The Proclaimers"
