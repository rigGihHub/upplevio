
from booking_enrichment import extract_booking_link

def test_city_orebro_kop_biljett_har_extracts_direct_link():
    html='<a href="https://secure.tickster.com/abc">Köp biljett här</a>'
    hit=extract_booking_link(html,"https://cityorebro.com/evenemang/konsert/test")
    assert hit["kind"]=="ticket"
    assert hit["url"]=="https://secure.tickster.com/abc"

def test_city_detail_without_booking_cta_is_not_guessed():
    html='<a href="https://arrangor.se/info">Mer information</a>'
    assert extract_booking_link(html,"https://cityorebro.com/evenemang/ovrigt/test") is None
