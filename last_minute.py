
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from showtimes import event_start_datetime

STOCKHOLM = ZoneInfo("Europe/Stockholm")


@dataclass(frozen=True)
class LastMinuteInfo:
    minutes_to_start: int
    urgency_label: str


def last_minute_info(event, *, now=None, min_minutes=30, max_minutes=180):
    """Return Last Minute status only when a real start time is known and inside the window."""
    now = now or datetime.now(STOCKHOLM)
    if now.tzinfo is None:
        now = now.replace(tzinfo=STOCKHOLM)
    else:
        now = now.astimezone(STOCKHOLM)

    start = event_start_datetime(event)
    if start is None:
        return None

    delta = int((start - now).total_seconds() // 60)
    if delta < min_minutes or delta > max_minutes:
        return None

    if delta < 60:
        label = f"Om {delta} min"
    else:
        hours, mins = divmod(delta, 60)
        label = f"Om {hours} h" if mins == 0 else f"Om {hours} h {mins} min"
    return LastMinuteInfo(delta, label)


def last_minute_match(event, *, now=None, min_minutes=30, max_minutes=180):
    return last_minute_info(
        event, now=now, min_minutes=min_minutes, max_minutes=max_minutes
    ) is not None


def last_minute_shortlist(ranked_events, *, now=None, limit=3):
    """Preserve organic discovery order and only retain eligible Last Minute events."""
    eligible = [
        event for event in ranked_events
        if last_minute_match(event, now=now)
    ]
    return eligible[:max(0, limit)]


def last_minute_remaining(ranked_events, shortlist):
    shown = {event.id for event in shortlist}
    return [event for event in ranked_events if event.id not in shown]
