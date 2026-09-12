from parser_fix_impact import compare_parser_versions, parser_fix_impact_audit


def test_start_marker_is_recovered_by_v074_parser():
    html = "<main><p>20:00 – start</p></main>"
    r = compare_parser_versions(html, field="start_time")
    assert r["legacy"] is None
    assert r["current"] == "20:00"
    assert r["outcome"] == "Återvunnet värde"


def test_existing_interval_is_unchanged():
    html = "<main><p>Evenemang tider 19:00–22:30</p></main>"
    r = compare_parser_versions(html, field="start_time")
    assert r["legacy"] == "19:00"
    assert r["current"] == "19:00"
    assert r["outcome"] == "Oförändrat"


def test_standalone_entre_price_is_recovered():
    html = "<main><p>Entré 120 kr (+ serviceavgift)</p></main>"
    r = compare_parser_versions(html, field="price")
    assert r["legacy"] is None
    assert r["current"] == 120.0
    assert r["outcome"] == "Återvunnet värde"


def test_service_fee_does_not_become_price():
    html = "<main><p>Serviceavgift 20 kr</p><p>Garderob 30 kr</p></main>"
    r = compare_parser_versions(html, field="price")
    assert r["legacy"] is None
    assert r["current"] is None
    assert r["outcome"] == "Oförändrat"


def test_batch_reports_measurable_replay_improvement_without_regression():
    cases = [
        {"url": "https://example.test/a", "title": "A", "start_time": None},
        {"url": "https://example.test/b", "title": "B", "start_time": None},
        {"url": "https://example.test/c", "title": "C", "start_time": None},
    ]
    pages = {
        "https://example.test/a": "<p>20:00 – start</p>",
        "https://example.test/b": "<p>18:30 – start</p>",
        "https://example.test/c": "<p>Evenemang tider 19:00–22:00</p>",
    }
    report = parser_fix_impact_audit(cases, field="start_time", fetcher=lambda url: pages[url])
    assert report["analyzable"] == 3
    assert report["recovered"] == 2
    assert report["regressions"] == 0
    assert report["classification"] == "Mätbar förbättring i replay"


def test_batch_does_not_claim_unsupported_fix():
    cases = [{"url": "https://example.test/a"}] * 3
    report = parser_fix_impact_audit(cases, field="end_time", fetcher=lambda url: "<p>19:00–22:00</p>")
    assert report["classification"] == "Ingen v0.74-fix för detta fält"
