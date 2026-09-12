
from datetime import datetime
from zoneinfo import ZoneInfo
from models import Event
from go_now import go_now_info, go_now_match, go_now_shortlist, go_now_remaining

TZ=ZoneInfo("Europe/Stockholm")

def e(i='1', start_date='2026-09-07', start_time='08:00'):
    return Event(
        id=i,title=f'E{i}',event_type='Konsert',category='Konsert',
        start_date=start_date,end_date=None,start_time=start_time,
        venue='V',city='Örebro',region='Örebro',country='SE'
    )

def test_near_event_can_qualify_with_45_minutes():
    now=datetime(2026,9,7,7,0,tzinfo=TZ)
    info=go_now_info(e(start_time='08:00'),distance_km=8,now=now)
    assert info is not None
    assert info.band=='Nära'

def test_25km_requires_more_margin():
    now=datetime(2026,9,7,7,0,tzinfo=TZ)
    assert not go_now_match(e(start_time='08:00'),distance_km=20,now=now)
    assert go_now_match(e(start_time='08:30'),distance_km=20,now=now)

def test_50km_requires_two_hours():
    now=datetime(2026,9,7,7,0,tzinfo=TZ)
    assert not go_now_match(e(start_time='08:30'),distance_km=40,now=now)
    assert go_now_match(e(start_time='09:00'),distance_km=40,now=now)

def test_unknown_distance_or_time_is_excluded():
    now=datetime(2026,9,7,7,0,tzinfo=TZ)
    assert not go_now_match(e(start_time=None),distance_km=5,now=now)
    assert not go_now_match(e(),distance_km=None,now=now)

def test_more_than_four_hours_is_excluded():
    now=datetime(2026,9,7,7,0,tzinfo=TZ)
    assert not go_now_match(e(start_time='12:00'),distance_km=5,now=now)

def test_shortlist_preserves_organic_order():
    now=datetime(2026,9,7,7,0,tzinfo=TZ)
    events=[e('a','2026-09-07','08:30'),e('b','2026-09-07','09:00'),e('c','2026-09-07','10:00')]
    distances={'a':5,'b':20,'c':40}
    picks=go_now_shortlist(events,distance_lookup=lambda x:distances[x.id],now=now,limit=2)
    assert [x.id for x in picks]==['a','b']

def test_remaining_only_removes_shortlist():
    events=[e('a'),e('b'),e('c')]
    assert [x.id for x in go_now_remaining(events,[events[0]])]==['b','c']
