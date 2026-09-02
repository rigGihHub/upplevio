from datetime import date, timedelta
from coverage import distance_from_city

DEFAULT_INTERESTS = {
    "Rock", "Hårdrock/metal", "Teknik", "Samlarkort", "Sportkort", "Retro & nostalgi",
    "Miljö & hållbarhet", "Industri", "Fordon", "Gaming"
}

MAJOR_VENUES = {
    "Stockholmsmässan": 8,
    "Elmia": 8,
    "Svenska Mässan": 8,
    "Svenska Mässan Gothia Towers": 8,
    "Malmömässan": 7,
    "Strawberry Arena": 8,
    "Avicii Arena": 7,
    "Ullevi": 8,
    "Scandinavium": 6,
}

MAJOR_HINTS = {
    "international": 4, "nordic": 3, "scandinavia": 3, "world": 4,
    "expo": 2, "festival": 3, "championship": 4, "mässa": 2,
    "fair": 2, "show": 2
}

def _days_until(event):
    try:
        return (date.fromisoformat(event.start_date) - date.today()).days
    except Exception:
        return 9999

def interest_match(event, interests):
    hay = " ".join([event.event_type, event.category, *event.tags]).lower()
    hits = [x for x in interests if x.lower() in hay]
    return hits

def event_importance(event):
    score = 0
    reasons = []
    if event.source_count > 1:
        score += min(10, 4 + event.source_count * 2)
        reasons.append(f"bekräftat av {event.source_count} källor")
    venue_score = MAJOR_VENUES.get(event.venue, 0)
    if venue_score:
        score += venue_score
        reasons.append("stor etablerad arena/mässanläggning")
    text = f"{event.title} {event.description}".lower()
    for hint, points in MAJOR_HINTS.items():
        if hint in text:
            score += points
    if event.event_type == "Mässa":
        score += 2
    if event.event_type == "Festival":
        score += 3
    return score, reasons

def travel_score(event, origin_city, interests):
    dist = distance_from_city(event, origin_city) if origin_city else None
    interest_hits = interest_match(event, interests)
    importance, reasons = event_importance(event)
    score = importance

    if interest_hits:
        score += min(30, 12 + 6 * len(interest_hits))
        reasons.append("matchar " + ", ".join(interest_hits[:3]))

    if dist is not None:
        if 80 <= dist <= 250:
            score += 12
            reasons.append(f"rimligt reseavstånd ({dist} km)")
        elif 250 < dist <= 550:
            score += 8
            reasons.append(f"möjlig weekendresa ({dist} km)")
        elif dist < 80:
            score -= 8
            reasons.append("ligger nära dig")
        elif dist > 700:
            score -= 10

    days = _days_until(event)
    if 10 <= days <= 120:
        score += 8
        reasons.append("lagom långt fram för planering")
    elif days > 365:
        score -= 4

    if event.is_demo:
        score -= 40

    return score, reasons, dist

def recommended_for_you(events, interests, limit=12):
    ranked = []
    for e in events:
        hits = interest_match(e, interests)
        importance, reasons = event_importance(e)
        score = len(hits) * 20 + importance
        if hits:
            reasons = ["matchar " + ", ".join(hits[:3])] + reasons
        if e.is_demo:
            score -= 30
        ranked.append((score, e, reasons))
    ranked.sort(key=lambda x: (-x[0], x[1].start_date))
    return [x for x in ranked if x[0] > 0][:limit]

def worth_a_trip(events, origin_city, interests, limit=8):
    ranked = []
    for e in events:
        score, reasons, dist = travel_score(e, origin_city, interests)
        if dist is not None and dist >= 80 and score > 8:
            ranked.append((score, e, reasons, dist))
    ranked.sort(key=lambda x: (-x[0], x[1].start_date))
    return ranked[:limit]

def newly_announced(events, is_new_fn, limit=10):
    return sorted([e for e in events if is_new_fn(e)], key=lambda e: e.start_date)[:limit]

def this_weekend(events):
    today = date.today()
    days_to_sat = (5 - today.weekday()) % 7
    saturday = today + timedelta(days=days_to_sat)
    sunday = saturday + timedelta(days=1)
    return [e for e in events if e.start_date in (saturday.isoformat(), sunday.isoformat())]

def big_fairs(events, limit=10):
    ranked = []
    for e in events:
        if e.event_type != "Mässa":
            continue
        score, reasons = event_importance(e)
        if e.is_demo:
            score -= 30
        ranked.append((score, e, reasons))
    ranked.sort(key=lambda x: (-x[0], x[1].start_date))
    return ranked[:limit]
