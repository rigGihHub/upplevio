from datetime import date

from candidate_local_sources import parse_karlslund_public_calendar, candidate_value_audit


def test_karlslund_requires_explicit_date_and_parses_time_and_free():
    html = """<main>
      <article><h3><a href="/karlslund/hostmarknad">Höstmarknad</a></h3>
      <p>Höstmarknad med skördetema och hantverk. Söndag 20 september 2026 kl. 11:00–16:00. Fri entré.</p></article>
      <section><h3>Besök Barnens trädgård</h3><p>Kom och lek året runt.</p></section>
    </main>"""
    rows=parse_karlslund_public_calendar(html,page_url="https://extra.orebro.se/karlslund",today=date(2026,9,7))
    assert len(rows)==1
    e=rows[0]
    assert e.title=="Höstmarknad"
    assert e.start_date=="2026-09-20"
    assert e.start_time=="11:00"
    assert e.price_status=="free"
    assert "outdoor" in e.tags
    assert "marknad" in e.tags


def test_karlslund_does_not_invent_free_or_nature_tag():
    html="""<article><h3>Konsert i Manegen</h3><p>Konsert 25 september 2026 kl. 19:00. Biljetter säljs på plats.</p></article>"""
    rows=parse_karlslund_public_calendar(html,today=date(2026,9,7))
    assert len(rows)==1
    assert rows[0].price_status=="unknown"
    assert "natur" not in rows[0].tags and "outdoor" not in rows[0].tags


def test_karlslund_can_fill_nature_frontier_when_source_text_supports_it():
    html="""<article><h3>Skördevandring i trädgården</h3><p>Vandring i natur och park 20 september 2026 kl. 12:00.</p></article>"""
    candidate=parse_karlslund_public_calendar(html,today=date(2026,9,7))[0]
    rows=candidate_value_audit([], [candidate], today=date(2026,9,7))
    row=next(r for r in rows if r["source"]=="Karlslund")
    assert "Natur & utomhus" in row["unique_frontier_segments"]
    assert row["unique_events_in_underserved_segments"]==1
