
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

STOCKHOLM = ZoneInfo("Europe/Stockholm")


@dataclass(frozen=True)
class ShowtimeStatus:
    key: str
    label: str
    confidence: str  # high | medium
    starts_at: datetime | None = None


def _parse_clock(raw):
    value=(raw or "").strip()
    if not value:
        return None
    for fmt in ("%H:%M:%S","%H:%M"):
        try:
            return datetime.strptime(value,fmt).time()
        except ValueError:
            pass
    return None


def event_start_datetime(event, *, tz=STOCKHOLM):
    try:
        d=date.fromisoformat(event.start_date)
    except Exception:
        return None
    t=_parse_clock(getattr(event,"start_time",None))
    if t is None:
        return None
    return datetime.combine(d,t,tzinfo=tz)


def event_end_datetime(event, *, tz=STOCKHOLM):
    raw=getattr(event,"end_time",None)
    t=_parse_clock(raw)
    if t is None:
        return None
    try:
        d=date.fromisoformat(getattr(event,"end_date",None) or event.start_date)
    except Exception:
        return None
    end=datetime.combine(d,t,tzinfo=tz)
    start=event_start_datetime(event,tz=tz)
    if start and end < start and d == start.date():
        end += timedelta(days=1)
    return end


def showtime_status(event, *, now=None, soon_minutes=90):
    """Return a high-signal timing label without guessing missing end times."""
    now=now or datetime.now(STOCKHOLM)
    if now.tzinfo is None:
        now=now.replace(tzinfo=STOCKHOLM)
    else:
        now=now.astimezone(STOCKHOLM)

    start=event_start_datetime(event)
    if start is None:
        try:
            d=date.fromisoformat(event.start_date)
        except Exception:
            return None
        if d == now.date()+timedelta(days=1):
            return ShowtimeStatus("tomorrow","Imorgon","medium",None)
        return None

    end=event_end_datetime(event)
    if end is not None and start <= now <= end:
        return ShowtimeStatus("now","Pågår nu","high",start)

    if start.date() == now.date():
        delta=(start-now).total_seconds()/60
        hhmm=start.strftime("%H:%M")
        if 0 <= delta <= soon_minutes:
            return ShowtimeStatus("soon",f"Börjar snart · {hhmm}","high",start)
        if delta > soon_minutes:
            if start.time() >= time(17,0):
                return ShowtimeStatus("tonight",f"Ikväll · {hhmm}","high",start)
            return ShowtimeStatus("later_today",f"Senare idag · {hhmm}","high",start)
        # Start has passed but no reliable end time: do not claim it is ongoing.
        return ShowtimeStatus("started",f"Startade {hhmm}","high",start)

    if start.date() == now.date()+timedelta(days=1):
        return ShowtimeStatus("tomorrow",f"Imorgon · {start.strftime('%H:%M')}","high",start)
    return None


def evening_match(event, *, now=None):
    """Conservative 'tonight' matcher: known start time today at/after 17:00 and not already started."""
    now=now or datetime.now(STOCKHOLM)
    if now.tzinfo is None:
        now=now.replace(tzinfo=STOCKHOLM)
    else:
        now=now.astimezone(STOCKHOLM)
    start=event_start_datetime(event)
    return bool(start and start.date()==now.date() and start.time()>=time(17,0) and start>=now)
