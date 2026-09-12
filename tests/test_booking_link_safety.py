from booking_enrichment import extract_booking_link

PAGE = "https://venue.example/event/42"


def test_rejects_unsafe_schemes():
    for href in ("javascript:alert(1)", "data:text/html,hi", "mailto:a@example.com", "tel:+46123"):
        html = f'<a href="{href}">Boka nu</a>'
        assert extract_booking_link(html, PAGE) is None


def test_rejects_fragment_only_link():
    assert extract_booking_link('<a href="#booking">Boka</a>', PAGE) is None


def test_rejects_social_media_even_with_strong_cta():
    for url in ("https://facebook.com/events/1", "https://instagram.com/p/abc", "https://x.com/event/1"):
        assert extract_booking_link(f'<a href="{url}">Köp biljetter</a>', PAGE) is None


def test_rejects_unknown_external_host_even_with_strong_cta():
    html = '<a href="https://untrusted.example/pay/1">Köp biljetter</a>'
    assert extract_booking_link(html, PAGE) is None


def test_rejects_root_homepage_as_booking_target():
    html = '<a href="https://venue.example/">Boka nu</a>'
    assert extract_booking_link(html, PAGE) is None


def test_accepts_valid_relative_same_host_strong_cta():
    hit = extract_booking_link('<a href="/book/42">Boka nu</a>', PAGE)
    assert hit and hit["url"] == "https://venue.example/book/42"


def test_accepts_same_host_strong_cta_without_ticketish_path():
    hit = extract_booking_link('<a href="/reservation/42">Boka</a>', PAGE)
    assert hit and hit["url"] == "https://venue.example/reservation/42"


def test_accepts_known_ticket_partner_external_host():
    hit = extract_booking_link('<a href="https://secure.tickster.com/abc">Köp biljetter</a>', PAGE)
    assert hit and hit["url"] == "https://secure.tickster.com/abc"


def test_medium_biljetter_requires_partner_or_ticketish_same_host_path():
    assert extract_booking_link('<a href="/about">Biljetter</a>', PAGE) is None
    same = extract_booking_link('<a href="/biljetter/42">Biljetter</a>', PAGE)
    assert same and same["url"] == "https://venue.example/biljetter/42"
    partner = extract_booking_link('<a href="https://www.ticketmaster.se/event/123">Biljetter</a>', PAGE)
    assert partner and "ticketmaster.se" in partner["url"]


def test_english_book_is_not_treated_as_cta():
    assert extract_booking_link('<a href="/book/42">Book</a>', PAGE) is None
