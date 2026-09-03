from datetime import date, timedelta
from dataclasses import dataclass
from typing import Optional
import unicodedata
import re

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

INTEREST_PROFILES = {
    "Musik": ("musik", "konsert", "festival", "rock", "metal", "jazz", "artist"),
    "Stand-up": ("stand up", "stand-up", "komiker", "comedy", "humor"),
    "Sport": ("sport", "fotboll", "hockey", "innebandy", "match", "mästerskap"),
    "Familj": ("familj", "barn", "kids", "lov", "lek", "cirkus"),
    "Samlarkort & TCG": ("samlarkort", "sportkort", "pokemon", "tcg", "magic", "lorcana", "yu gi oh", "card show"),
    "Gaming & retro": ("gaming", "tv spel", "retro", "retromania", "nintendo", "playstation", "xbox"),
    "Mat & dryck": ("mat", "food", "dryck", "vin", "ol", "beer", "smak"),
    "Teater & show": ("teater", "musikal", "show", "scen", "theatre", "musical"),
    "Mässor": ("massa", "expo", "fair", "utstallning", "konferens"),
    "Teknik & industri": ("teknik", "tech", "industri", "industrial", "hallbarhet", "miljo", "fordon"),
}

PRICE_LIMITS = {
    "Gratis": 0,
    "Max 100 kr": 100,
    "Max 250 kr": 250,
    "Max 500 kr": 500,
}


@dataclass(frozen=True)
class DiscoveryRank:
    score: int
    reasons: tuple[str, ...]
    distance_km: Optional[int]


def _days_until(event, today=None):
    today = today or date.today()
    try:
        return (date.fromisoformat(event.start_date) - today).days
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


def _search_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def event_matches_query(event, query: str) -> bool:
    q = _search_text(query)
    if not q:
        return True
    haystack = " ".join([
        event.title or "", event.event_type or "", event.category or "", event.venue or "",
        event.city or "", event.region or "", event.description or "", *(event.tags or [])
    ])
    return q in _search_text(haystack)


def _interest_points(event, interests) -> tuple[int, Optional[str]]:
    selected = [x for x in (interests or []) if x in INTEREST_PROFILES]
    if not selected:
        return 0, None
    hay = _search_text(" ".join([
        event.title or "", event.event_type or "", event.category or "",
        event.description or "", *(event.tags or [])
    ]))
    matches = []
    for label in selected:
        if any(_search_text(keyword) in hay for keyword in INTEREST_PROFILES[label]):
            matches.append(label)
    if not matches:
        return 0, None
    # Explicit preferences matter, but cannot overpower a strong query or huge distance difference.
    points = min(18, 12 + 3 * (len(matches) - 1))
    return points, "matchar " + ", ".join(matches[:2])


def _query_relevance(event, query: str) -> tuple[int, Optional[str]]:
    q = _search_text(query)
    if not q:
        return 0, None
    if q in _search_text(event.title):
        return 26, "matchar din sökning tydligt"
    if q in _search_text(event.venue) or q in _search_text(event.city):
        return 16, "matchar platsen du söker"
    taxonomy = " ".join([event.event_type or "", event.category or "", *(event.tags or [])])
    if q in _search_text(taxonomy):
        return 13, "matchar kategorin du söker"
    if q in _search_text(event.description):
        return 5, "matchar din sökning"
    return 0, None


def _distance_points(distance_km: Optional[int]) -> tuple[int, Optional[str]]:
    if distance_km is None:
        return 0, None
    if distance_km <= 10:
        return 30, "mycket nära"
    if distance_km <= 25:
        return 25, "nära"
    if distance_km <= 50:
        return 20, "rimligt nära"
    if distance_km <= 100:
        return 12, "inom vald radie"
    if distance_km <= 200:
        return 6, "inom vald radie"
    return 2, "inom vald radie"


def _time_points(days: int) -> tuple[int, Optional[str]]:
    if days < 0:
        return -100, None
    if days == 0:
        return 30, "händer idag"
    if days <= 2:
        return 25, "händer snart"
    if days <= 7:
        return 20, "den närmaste veckan"
    if days <= 14:
        return 15, "inom två veckor"
    if days <= 30:
        return 10, "inom en månad"
    return 4, None


def _price_points(event, price_filter: str) -> tuple[int, Optional[str]]:
    status = getattr(event, "price_status", "unknown") or "unknown"
    if status == "free":
        return 14, "gratis"
    if status != "known":
        # Unknown price is neither cheap nor expensive. Do not fabricate value.
        return 0, None

    low = getattr(event, "price_min", None)
    if low is None:
        return 0, None
    limit = PRICE_LIMITS.get(price_filter)
    if limit and limit > 0:
        if low <= limit * 0.5:
            return 10, "gott om marginal i budgeten"
        return 5, "inom din budget"
    return 2, None


def _trust_points(event) -> tuple[int, Optional[str]]:
    # Trust is only a small tie-breaker. It must never make an irrelevant event relevant.
    source_count = len(set(getattr(event, "source_names", []) or []))
    quality = getattr(event, "data_quality", "")
    if source_count >= 2 or quality == "multi_source":
        return 5, f"bekräftat från {source_count or 2} källor"
    if quality == "source_verified":
        return 2, None
    return 0, None


def discovery_rank(event, origin_city=None, price_filter="Alla priser", query="", today=None, interests=None):
    """Explainable ranking for the main discovery flow.

    The score reflects the user's explicit context: query, distance, timing and budget.
    Source confidence is intentionally capped as a small tie-breaker rather than a
    relevance signal. Missing price or geodata is never converted into favourable data.
    """
    today = today or date.today()
    score = 0
    reasons = []

    q_points, q_reason = _query_relevance(event, query)
    score += q_points
    if q_reason:
        reasons.append(q_reason)

    i_points, i_reason = _interest_points(event, interests)
    score += i_points
    if i_reason:
        reasons.append(i_reason)

    dist = distance_from_city(event, origin_city) if origin_city and origin_city != "Hela Sverige" else None
    d_points, d_reason = _distance_points(dist)
    score += d_points
    if d_reason:
        reasons.append(d_reason)

    t_points, t_reason = _time_points(_days_until(event, today))
    score += t_points
    if t_reason:
        reasons.append(t_reason)

    p_points, p_reason = _price_points(event, price_filter)
    score += p_points
    if p_reason:
        reasons.append(p_reason)

    trust_points, trust_reason = _trust_points(event)
    score += trust_points
    if trust_reason:
        reasons.append(trust_reason)

    if getattr(event, "is_demo", False):
        score -= 100

    # Keep explanations short enough for event cards.
    return DiscoveryRank(score=int(score), reasons=tuple(reasons[:3]), distance_km=dist)


def rank_discovery(events, origin_city=None, price_filter="Alla priser", query="", today=None, interests=None):
    ranked = [(discovery_rank(e, origin_city, price_filter, query, today, interests), e) for e in events]
    ranked.sort(key=lambda item: (-item[0].score, item[1].start_date, (item[1].title or "").lower()))
    return ranked


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
