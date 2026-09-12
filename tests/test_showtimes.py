
from datetime import datetime
from zoneinfo import ZoneInfo
from models import Event
from showtimes import showtime_status, evening_match

TZ=ZoneInfo("Europe/Stockholm")

def e(start_date="2026-09-06", start_time="19:00", end_date=None):
    return Event(
        id="x",title="Test",event_type="Konsert",category="Konsert",
        start_date=start_date,end_date=end_date,start_time=start_time,
        venue="V",city="Örebro",region="Örebro",country="SE"
    )

def test_begins_soon_with_known_time():
    s=showtime_status(e(start_time="20:30"),now=datetime(2026,9,6,19,45,tzinfo=TZ))
    assert s.key=="soon"
    assert s.label=="Börjar snart · 20:30"

def test_tonight_when_later_and_after_17():
    s=showtime_status(e(start_time="22:00"),now=datetime(2026,9,6,18,0,tzinfo=TZ))
    assert s.key=="tonight"
    assert s.label=="Ikväll · 22:00"

def test_later_today_before_17():
    s=showtime_status(e(start_time="16:00"),now=datetime(2026,9,6,12,0,tzinfo=TZ))
    assert s.key=="later_today"

def test_started_does_not_claim_ongoing_without_end_time():
    s=showtime_status(e(start_time="18:00"),now=datetime(2026,9,6,19,0,tzinfo=TZ))
    assert s.key=="started"
    assert "Startade" in s.label

def test_ongoing_requires_explicit_end_time():
    event=e(start_time="18:00")
    event.end_time="20:00"
    s=showtime_status(event,now=datetime(2026,9,6,19,0,tzinfo=TZ))
    assert s.key=="now"
    assert s.label=="Pågår nu"

def test_tomorrow_with_time():
    s=showtime_status(e(start_date="2026-09-07",start_time="10:00"),now=datetime(2026,9,6,19,0,tzinfo=TZ))
    assert s.key=="tomorrow"
    assert s.label=="Imorgon · 10:00"

def test_evening_match_is_conservative():
    now=datetime(2026,9,6,18,0,tzinfo=TZ)
    assert evening_match(e(start_time="19:30"),now=now)
    assert not evening_match(e(start_time=None),now=now)
    assert not evening_match(e(start_time="16:00"),now=now)
    assert not evening_match(e(start_time="17:30"),now=now)
