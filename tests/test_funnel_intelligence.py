
from engagement import record_action
from conversion_attribution import create_or_get_outbound_click
from funnel_intelligence import funnel_report, session_impression_key
from models import Event

def ev():
    return Event(
        id="e1",title="Test",event_type="Konsert",category="Musik",
        start_date="2026-09-20",end_date=None,start_time="19:00",venue="V",
        city="Örebro",region="Örebro",country="SE",
        source_names=["City Örebro"],booking_partner="Tickster"
    )

def test_session_impression_key_changes_with_filter():
    assert session_impression_key("e1","a") == "a:e1"
    assert session_impression_key("e1","a") != session_impression_key("e1","b")

def test_funnel_report_counts_real_stages(tmp_path):
    engagement_db=tmp_path/"eng.db"
    attribution_db=tmp_path/"attr.db"

    record_action(
        "impression",event_id="e1",partner="Tickster",
        context={"source":"City Örebro","event_type":"Konsert","surface":"discover"},
        db_path=engagement_db
    )
    record_action(
        "activity_open",event_id="e1",partner="Tickster",
        context={"source":"City Örebro","event_type":"Konsert","surface":"discover"},
        db_path=engagement_db
    )
    create_or_get_outbound_click(
        click_id="upc_123",event_id="e1",partner_key="tickster",partner_name="Tickster",
        destination_url="https://tickster.com/e/1",
        context={"source":"City Örebro","event_type":"Konsert","partner":"Tickster"},
        db_path=attribution_db
    )

    r=funnel_report([ev()],engagement_db=engagement_db,attribution_db=attribution_db)
    assert r["totals"]["impressions"] == 1
    assert r["totals"]["opens"] == 1
    assert r["totals"]["booking_clicks"] == 1
    assert r["totals"]["open_rate"] == 1.0
    assert r["totals"]["booking_click_rate"] == 1.0

    src=r["by_source"][0]
    assert src["source"] == "City Örebro"
    assert src["booking_clicks"] == 1

def test_click_without_current_event_uses_persisted_context(tmp_path):
    engagement_db=tmp_path/"eng.db"
    attribution_db=tmp_path/"attr.db"
    create_or_get_outbound_click(
        click_id="upc_abc",event_id="old-event",partner_key="eventim",partner_name="Eventim",
        destination_url="https://eventim.se/e/1",
        context={"source":"Conventum","event_type":"Show","partner":"Eventim"},
        db_path=attribution_db
    )
    r=funnel_report([],engagement_db=engagement_db,attribution_db=attribution_db)
    assert r["by_source"][0]["source"] == "Conventum"
    assert r["by_event_type"][0]["event_type"] == "Show"
    assert r["by_partner"][0]["partner"] == "Eventim"

def test_zero_denominator_rates_are_none(tmp_path):
    r=funnel_report([],engagement_db=tmp_path/"missing-eng.db",attribution_db=tmp_path/"missing-attr.db")
    assert r["totals"]["open_rate"] is None
    assert r["totals"]["booking_click_rate"] is None
