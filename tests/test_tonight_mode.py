
from models import Event
from tonight_mode import tonight_shortlist, tonight_remaining, tonight_summary

def e(i, start_time="19:00", price_status="unknown", price_min=None):
    return Event(
        id=str(i), title=f"E{i}", event_type="Konsert", category="Konsert",
        start_date="2026-09-06", end_date=None, start_time=start_time,
        venue="V", city="Örebro", region="Örebro", country="SE",
        price_status=price_status, price_min=price_min
    )

def test_shortlist_preserves_existing_order():
    events=[e(1),e(2),e(3),e(4)]
    picks=tonight_shortlist(events,3)
    assert [p.event.id for p in picks]==["1","2","3"]

def test_shortlist_has_clear_labels():
    picks=tonight_shortlist([e(1),e(2),e(3)],3)
    assert [p.label for p in picks]==["Bäst ikväll","Nästa val","Också starkt"]

def test_remaining_excludes_shortlist_without_reordering():
    events=[e(1),e(2),e(3),e(4),e(5)]
    picks=tonight_shortlist(events,3)
    assert [x.id for x in tonight_remaining(events,picks)]==["4","5"]

def test_summary_uses_only_known_facts():
    assert tonight_summary(e(1,start_time="20:30"),distance=4.2,price_text="Gratis")=="Start 20:30 · 4.2 km · Gratis"

def test_summary_does_not_invent_distance():
    assert tonight_summary(e(1,start_time="20:30"),distance=None,price_text="Pris saknas")=="Start 20:30 · Pris saknas"
