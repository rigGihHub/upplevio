
from datetime import date
from models import Event
from discovery import discovery_rank
from commercial import campaign_active, sponsored_candidates
from engagement import booking_target, company_metrics, record_action

def ev(i, title="Event", sponsored=False, **kw):
    base = dict(id=str(i), title=title, event_type="Aktivitet", category="Familj",
        start_date="2026-09-06", end_date=None, start_time="12:00", venue="Test",
        city="Örebro", region="Örebro", country="SE", is_sponsored=sponsored)
    base.update(kw)
    return Event(**base)

def test_campaign_requires_dates_and_identity():
    e = ev(1, sponsored=True, sponsor_campaign_id="c1", sponsor_company="Bolag",
           sponsor_start_date="2026-09-01", sponsor_end_date="2026-09-30")
    assert campaign_active(e, date(2026,9,5))
    assert not campaign_active(e, date(2026,10,1))

def test_sponsor_cannot_rescue_irrelevant_event():
    good = ev(1, title="Familjedag")
    paid = ev(2, title="Betald långt bort", sponsored=True, city="Stockholm",
        sponsor_campaign_id="c", sponsor_company="Bolag", sponsor_priority=999,
        sponsor_start_date="2026-09-01", sponsor_end_date="2026-09-30")
    # Explicit scores make the policy under test obvious and independent of future ranking tuning.
    class R:
        def __init__(self, score): self.score=score
    placements = sponsored_candidates([(R(100), good),(R(60), paid)], today=date(2026,9,5), origin_city="Örebro")
    assert placements == []

def test_sponsor_must_match_geo_when_campaign_scoped():
    e = ev(1, sponsored=True, sponsor_campaign_id="c", sponsor_company="Bolag",
        sponsor_geo_areas=["Karlstad"], sponsor_start_date="2026-09-01", sponsor_end_date="2026-09-30")
    class R:
        score=100
    assert sponsored_candidates([(R(), e)], today=date(2026,9,5), origin_city="Örebro") == []

def test_booking_target_prefers_affiliate_booking_url():
    e = ev(1, ticket_url="https://ticket", booking_url="https://partner")
    assert booking_target(e) == "https://partner"

def test_company_metrics_funnel(tmp_path):
    db = tmp_path/"metrics.db"
    record_action("sponsored_impression", company="Boda", event_id="1", campaign_id="c", db_path=db)
    record_action("sponsored_impression", company="Boda", event_id="1", campaign_id="c", db_path=db)
    record_action("sponsored_click", company="Boda", event_id="1", campaign_id="c", db_path=db)
    record_action("activity_open", company="Boda", event_id="1", db_path=db)
    record_action("booking_outbound", company="Boda", event_id="1", partner="Partner", db_path=db)
    m = company_metrics("Boda", db_path=db)
    assert m["impressions"] == 2
    assert m["activity_visits"] == 1
    assert m["booking_clicks"] == 1
    assert m["ctr"] == 0.5
