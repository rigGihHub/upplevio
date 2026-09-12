
from datetime import datetime
from zoneinfo import ZoneInfo

from last_minute import last_minute_info, last_minute_match, last_minute_shortlist, last_minute_remaining
from models import Event

TZ=ZoneInfo("Europe/Stockholm")

def e(i="1", start_date="2026-09-07", start_time="01:30"):
    return Event(
        id=i,title=f"E{i}",event_type="Konsert",category="Konsert",
        start_date=start_date,end_date=None,start_time=start_time,
        venue="V",city="Örebro",region="Örebro",country="SE"
    )

def test_eligible_inside_window():
    now=datetime(2026,9,7,0,0,tzinfo=TZ)
    info=last_minute_info(e(start_time="01:30"),now=now)
    assert info is not None
    assert info.minutes_to_start==90
    assert info.urgency_label=="Om 1 h 30 min"

def test_too_soon_is_excluded():
    now=datetime(2026,9,7,0,0,tzinfo=TZ)
    assert not last_minute_match(e(start_time="00:20"),now=now)

def test_too_far_away_is_excluded():
    now=datetime(2026,9,7,0,0,tzinfo=TZ)
    assert not last_minute_match(e(start_time="03:30"),now=now)

def test_missing_time_is_excluded():
    now=datetime(2026,9,7,0,0,tzinfo=TZ)
    assert not last_minute_match(e(start_time=None),now=now)

def test_shortlist_preserves_existing_rank_order():
    now=datetime(2026,9,7,0,0,tzinfo=TZ)
    events=[e("a",start_time="01:00"),e("b",start_time="01:30"),e("c",start_time="02:00"),e("d",start_time="02:30")]
    picked=last_minute_shortlist(events,now=now,limit=3)
    assert [x.id for x in picked]==["a","b","c"]

def test_remaining_excludes_shortlist_only():
    now=datetime(2026,9,7,0,0,tzinfo=TZ)
    events=[e("a",start_time="01:00"),e("b",start_time="01:30"),e("c",start_time="02:00"),e("d",start_time="02:30")]
    picked=last_minute_shortlist(events,now=now,limit=2)
    assert [x.id for x in last_minute_remaining(events,picked)]==["c","d"]
