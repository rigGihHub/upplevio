
from models import Event
from ad_inventory import AD_SLOTS, enabled_slots
from discovery_value import is_local_discovery_tip
from discovery import rank_discovery

def ev(i, source, sponsored=False, priority=0):
    return Event(id=str(i), title=f"Event {i}", event_type="Aktivitet", category="Lokalt",
        start_date="2026-09-06", end_date=None, start_time=None, venue="Plats",
        city="Örebro", region="Örebro", country="SE", source_names=[source],
        is_sponsored=sponsored, sponsor_priority=priority)

def test_ads_disabled_by_default():
    assert AD_SLOTS
    assert enabled_slots("discovery") == []

def test_local_tip_is_editorial_not_paid():
    e = ev(1, "City Örebro")
    assert is_local_discovery_tip(e)
    assert not e.is_sponsored

def test_sponsor_priority_does_not_change_organic_ranking():
    a = ev(1, "City Örebro", sponsored=False)
    b = ev(2, "City Örebro", sponsored=True, priority=999999)
    ranked = rank_discovery([a,b], origin_city="Örebro")
    # Sponsor priority is not an input to organic discovery ranking.
    assert [x[1].id for x in ranked] == ["1","2"]
