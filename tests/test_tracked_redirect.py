from models import Event
from tracked_redirect import make_redirect_token, verify_redirect_token, build_tracked_url, process_redirect
from conversion_attribution import attribution_report

SECRET = "x" * 40

def ev(**kw):
    base=dict(
        id="e1",title="Test",event_type="Konsert",category="Musik",
        start_date="2026-09-20",end_date=None,start_time="19:00",venue="V",
        city="Örebro",region="Örebro",country="SE"
    )
    base.update(kw)
    return Event(**base)

def test_signed_token_round_trip():
    token=make_redirect_token(event=ev(),destination_url="https://secure.tickster.com/e/1",secret=SECRET,now=1000)
    payload=verify_redirect_token(token,secret=SECRET,now=1001)
    assert payload["event_id"]=="e1"
    assert payload["partner_key"]=="tickster"
    assert payload["destination_url"]=="https://secure.tickster.com/e/1"

def test_tampered_token_is_rejected():
    token=make_redirect_token(event=ev(),destination_url="https://eventim.se/e/1",secret=SECRET,now=1000)
    body,sig=token.split(".",1)
    bad=body[:-1] + ("A" if body[-1] != "A" else "B") + "." + sig
    try:
        verify_redirect_token(bad,secret=SECRET,now=1001)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered token must fail")

def test_expired_token_is_rejected():
    token=make_redirect_token(event=ev(),destination_url="https://eventim.se/e/1",secret=SECRET,now=1000)
    try:
        verify_redirect_token(token,secret=SECRET,now=4000,ttl_seconds=1800)
    except ValueError as e:
        assert "expired" in str(e).lower()
    else:
        raise AssertionError("expired token must fail")

def test_http_destination_is_rejected():
    try:
        make_redirect_token(event=ev(),destination_url="http://example.com/e/1",secret=SECRET,now=1000)
    except ValueError:
        pass
    else:
        raise AssertionError("non-HTTPS redirect must fail")

def test_missing_config_falls_back_to_direct_destination():
    destination="https://ticketmaster.se/event/1"
    assert build_tracked_url(event=ev(),destination_url=destination,public_base_url=None,secret=None)==destination
    assert build_tracked_url(event=ev(),destination_url=destination,public_base_url="https://upplevio.streamlit.app",secret="short")==destination

def test_tracked_url_points_to_public_app():
    url=build_tracked_url(
        event=ev(),destination_url="https://ticketmaster.se/event/1",
        public_base_url="https://upplevio.streamlit.app/",secret=SECRET
    )
    assert url.startswith("https://upplevio.streamlit.app/?go=")

def test_processing_same_token_is_idempotent(tmp_path):
    db=tmp_path/"attr.db"
    token=make_redirect_token(event=ev(),destination_url="https://nortic.se/ticket/1",secret=SECRET,now=1000)
    a=process_redirect(token,secret=SECRET,db_path=db,now=1001)
    b=process_redirect(token,secret=SECRET,db_path=db,now=1002)
    assert a.click_id==b.click_id
    report=attribution_report(db_path=db)
    assert report["clicks"]==1


def test_redirect_persists_funnel_dimensions(tmp_path):
    db=tmp_path/"attr.db"
    event=ev(source_names=["City Örebro"],event_type="Konsert")
    token=make_redirect_token(event=event,destination_url="https://secure.tickster.com/e/1",secret=SECRET,now=1000)
    payload=verify_redirect_token(token,secret=SECRET,now=1001)
    assert payload["source"]=="City Örebro"
    assert payload["event_type"]=="Konsert"
    process_redirect(token,secret=SECRET,db_path=db,now=1001)
