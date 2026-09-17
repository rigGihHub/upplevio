from visitorebro_adapter import parse_visitorebro_html


def test_rejects_page_without_explicit_event_date():
    html = '<html><body><h2>Konsert i Örebro</h2><p>Välkommen till en fantastisk kväll.</p></body></html>'
    assert parse_visitorebro_html(html) == []


def test_rejects_date_without_event_title():
    html = '<html><body><p>24 september 2026</p></body></html>'
    assert parse_visitorebro_html(html) == []


def test_does_not_invent_location_or_price():
    html = '<html><body><article><h2>Testkonsert</h2><time datetime="2026-09-24">24 september</time></article></body></html>'
    events = parse_visitorebro_html(html)
    for event in events:
        assert getattr(event, "price_status", "unknown") == "unknown"
        assert not getattr(event, "venue", None)


def test_parser_is_deterministic():
    html = '<html><body><article><h2>Testkonsert</h2><time datetime="2026-09-24">24 september</time></article></body></html>'
    first = parse_visitorebro_html(html)
    second = parse_visitorebro_html(html)
    assert [(e.title, e.start_date) for e in first] == [(e.title, e.start_date) for e in second]
