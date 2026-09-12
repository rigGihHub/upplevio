
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from showtimes import event_start_datetime

STOCKHOLM = ZoneInfo("Europe/Stockholm")


@dataclass(frozen=True)
class GoNowInfo:
    minutes_to_start: int
    distance_km: float
    band: str
    planning_note: str


def _minutes_to_start(event, now=None):
    now = now or datetime.now(STOCKHOLM)
    if now.tzinfo is None:
        now = now.replace(tzinfo=STOCKHOLM)
    else:
        now = now.astimezone(STOCKHOLM)
    start = event_start_datetime(event)
    if start is None:
        return None
    return int((start - now).total_seconds() // 60)


def go_now_info(event, *, distance_km, now=None):
    """Conservative planning envelope. It is not a travel-time calculation."""
    if distance_km is None or distance_km < 0:
        return None
    minutes = _minutes_to_start(event, now=now)
    if minutes is None or minutes < 45 or minutes > 240:
        return None

    distance = float(distance_km)
    if distance <= 10 and minutes >= 45:
        return GoNowInfo(minutes, distance, "Nära", "Gott om planeringsmarginal")
    if distance <= 25 and minutes >= 75:
        return GoNowInfo(minutes, distance, "Rimligt nära", "Planera avfärd snart")
    if distance <= 50 and minutes >= 120:
        return GoNowInfo(minutes, distance, "Lite längre bort", "Kontrollera faktisk restid")
    return None


def go_now_match(event, *, distance_km, now=None):
    return go_now_info(event, distance_km=distance_km, now=now) is not None


def go_now_shortlist(ranked_events, *, distance_lookup, now=None, limit=3):
    """Preserve organic discovery order among events inside the planning envelope."""
    result = []
    for event in ranked_events:
        distance = distance_lookup(event)
        if go_now_match(event, distance_km=distance, now=now):
            result.append(event)
            if len(result) >= max(0, limit):
                break
    return result


def go_now_remaining(ranked_events, shortlist):
    shown = {event.id for event in shortlist}
    return [event for event in ranked_events if event.id not in shown]
