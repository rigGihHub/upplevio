
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Optional

@dataclass(frozen=True)
class SponsoredPlacement:
    event_id: str
    campaign_id: str
    company: str
    priority: int

def campaign_active(event, today: Optional[date] = None) -> bool:
    today = today or date.today()
    if not getattr(event, "is_sponsored", False):
        return False
    start = getattr(event, "sponsor_start_date", None)
    end = getattr(event, "sponsor_end_date", None)
    try:
        if start and today < date.fromisoformat(start):
            return False
        if end and today > date.fromisoformat(end):
            return False
    except ValueError:
        return False
    return bool(getattr(event, "sponsor_campaign_id", None) and getattr(event, "sponsor_company", None))

def sponsored_candidates(
    organic_ranked,
    *,
    today: Optional[date] = None,
    origin_city: Optional[str] = None,
    interests: Optional[Iterable[str]] = None,
    max_organic_rank: int = 12,
    score_gap: int = 12,
):
    """Return eligible sponsored placements without changing organic ranking.

    A paid campaign may only be selected from events that already rank near the top
    organically. Payment can choose among relevant candidates, never manufacture relevance.
    """
    if not organic_ranked:
        return []
    best_score = organic_ranked[0][0].score
    interest_set = {str(x).strip().lower() for x in (interests or []) if str(x).strip()}
    rows = []
    for organic_position, (rank, event) in enumerate(organic_ranked[:max_organic_rank], start=1):
        if not campaign_active(event, today):
            continue
        if rank.score < best_score - score_gap:
            continue
        geo = {str(x).strip().lower() for x in (getattr(event, "sponsor_geo_areas", []) or [])}
        if geo and origin_city and origin_city.lower() not in geo:
            continue
        audiences = {str(x).strip().lower() for x in (getattr(event, "sponsor_audiences", []) or [])}
        if audiences and interest_set and not (audiences & interest_set):
            continue
        rows.append((getattr(event, "sponsor_priority", 0), -organic_position, event))
    rows.sort(key=lambda x: (-x[0], -x[1], (x[2].title or "").lower()))
    return [SponsoredPlacement(
        event_id=e.id,
        campaign_id=e.sponsor_campaign_id,
        company=e.sponsor_company,
        priority=getattr(e, "sponsor_priority", 0),
    ) for _, _, e in rows]
