
from conversion_attribution import create_outbound_click, record_conversion, attribution_report

def test_click_id_is_unique_and_traceable(tmp_path):
    db=tmp_path/"attr.db"
    a=create_outbound_click(
        event_id="e1", partner_key="tickster", partner_name="Tickster",
        destination_url="https://tickster.com/e/1", campaign_id="camp-1", db_path=db
    )
    b=create_outbound_click(
        event_id="e1", partner_key="tickster", partner_name="Tickster",
        destination_url="https://tickster.com/e/1", campaign_id="camp-1", db_path=db
    )
    assert a.click_id.startswith("upc_")
    assert a.click_id != b.click_id
    assert a.event_id=="e1"
    assert a.campaign_id=="camp-1"

def test_conversion_requires_known_click(tmp_path):
    db=tmp_path/"attr.db"
    try:
        record_conversion(click_id="upc_missing",status="confirmed",db_path=db)
    except KeyError:
        pass
    else:
        raise AssertionError("unknown click must be rejected")

def test_conversion_is_idempotent_per_partner_conversion_id(tmp_path):
    db=tmp_path/"attr.db"
    c=create_outbound_click(
        event_id="e1",partner_key="eventim",partner_name="Eventim",
        destination_url="https://eventim.se/e/1",db_path=db
    )
    assert record_conversion(
        click_id=c.click_id,status="confirmed",partner_conversion_id="order-123",
        order_value=500,currency="SEK",commission_value=25,commission_currency="SEK",db_path=db
    ) is True
    assert record_conversion(
        click_id=c.click_id,status="confirmed",partner_conversion_id="order-123",
        order_value=500,currency="SEK",commission_value=25,commission_currency="SEK",db_path=db
    ) is False

def test_report_separates_clicks_from_confirmed_conversions(tmp_path):
    db=tmp_path/"attr.db"
    c1=create_outbound_click(
        event_id="e1",partner_key="tickster",partner_name="Tickster",
        destination_url="https://tickster.com/e/1",db_path=db
    )
    create_outbound_click(
        event_id="e2",partner_key="tickster",partner_name="Tickster",
        destination_url="https://tickster.com/e/2",db_path=db
    )
    record_conversion(
        click_id=c1.click_id,status="confirmed",partner_conversion_id="x",
        commission_value=10,commission_currency="SEK",db_path=db
    )
    r=attribution_report(db_path=db)
    assert r["clicks"]==2
    assert r["conversions"]==1
    assert r["confirmed"]==1
    assert r["commission"]==10.0
