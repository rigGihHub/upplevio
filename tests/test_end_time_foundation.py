from datetime import date, datetime
from zoneinfo import ZoneInfo
from models import Event
from showtimes import event_end_datetime, showtime_status
from ui_logic import compact_date_label
from candidate_local_sources import _explicit_time_range

TZ=ZoneInfo("Europe/Stockholm")

def event(**kw):
    base=dict(id="x",title="X",event_type="Evenemang",category="Övrigt",start_date="2026-09-20",end_date=None,start_time="11:00",venue="V",city="Örebro",region="Örebro län",country="Sverige")
    base.update(kw)
    return Event(**base)

def test_event_has_real_optional_end_time_field():
    e=event()
    assert e.end_time is None
    e2=event(end_time="16:00")
    assert e2.end_time == "16:00"

def test_explicit_time_range_accepts_hours_and_minutes():
    assert _explicit_time_range("Höstmarknad kl. 11–16") == ("11:00","16:00")
    assert _explicit_time_range("Live 20:30-23:15") == ("20:30","23:15")
    assert _explicit_time_range("Start kl 19:00") == (None,None)

def test_compact_label_shows_explicit_range_only_when_known():
    today=date(2026,9,20)
    assert compact_date_label(event(end_time="16:00"),today) == "Idag · 11:00–16:00"
    assert compact_date_label(event(end_time=None),today) == "Idag · 11:00"

def test_showtime_ongoing_uses_model_end_time():
    e=event(start_time="18:00",end_time="20:00",start_date="2026-09-20")
    s=showtime_status(e,now=datetime(2026,9,20,19,0,tzinfo=TZ))
    assert s and s.key == "now"

def test_cross_midnight_end_time_is_supported_without_guessing_duration():
    e=event(start_time="22:00",end_time="01:00")
    end=event_end_datetime(e)
    assert end.date().isoformat() == "2026-09-21"
    assert end.strftime("%H:%M") == "01:00"
