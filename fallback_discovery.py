from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterable, Optional, Sequence

from discovery import event_matches_query, rank_discovery
from geography import distance_from_city
from ui_logic import event_period_matches, price_matches


DATE_RELAXATIONS = {
    "Idag": ["Nästa 7 dagar", "Nästa 30 dagar", "Nästa 3 månader"],
    "I helgen": ["Nästa 7 dagar", "Nästa 30 dagar", "Nästa 3 månader"],
    "Nästa 7 dagar": ["Nästa 30 dagar", "Nästa 3 månader"],
    "Nästa 30 dagar": ["Nästa 3 månader"],
    "Nästa 3 månader": [],
}

RADIUS_STEPS = [25, 50, 100, 200, 300]


@dataclass(frozen=True)
class FallbackSuggestion:
    kind: str
    title: str
    explanation: str
    events: tuple
    relaxed_when: str
    relaxed_radius_km: int
    relaxed_price_filter: str
    relaxed_only_new: bool


def _base_matches(
    event,
    *,
    when: str,
    today: date,
    origin_city: str,
    radius_km: int,
    price_filter: str,
    query: str,
    type_filter: str,
    only_new: bool,
    is_new: Callable,
) -> bool:
    if not event_period_matches(event, when, today):
        return False
    if type_filter != "Alla" and event.event_type != type_filter:
        return False
    if only_new and not is_new(event):
        return False
    if not price_matches(event, price_filter):
        return False
    if origin_city != "Hela Sverige":
        dist = distance_from_city(event, origin_city)
        if dist is None or dist > radius_km:
            return False
    if query and not event_matches_query(event, query):
        return False
    return True


def _rank(events, *, origin_city, price_filter, query, today, interests, limit):
    ranked = rank_discovery(
        events,
        origin_city=origin_city,
        price_filter=price_filter,
        query=query,
        today=today,
        interests=interests,
    )
    return tuple(event for _, event in ranked[:limit])


def _candidate(
    events: Sequence,
    *,
    kind: str,
    title: str,
    explanation: str,
    when: str,
    radius_km: int,
    price_filter: str,
    only_new: bool,
    today: date,
    origin_city: str,
    query: str,
    type_filter: str,
    is_new: Callable,
    interests: Optional[Iterable[str]],
    limit: int,
):
    matches = [
        event
        for event in events
        if _base_matches(
            event,
            when=when,
            today=today,
            origin_city=origin_city,
            radius_km=radius_km,
            price_filter=price_filter,
            query=query,
            type_filter=type_filter,
            only_new=only_new,
            is_new=is_new,
        )
    ]
    if not matches:
        return None
    ranked = _rank(
        matches,
        origin_city=origin_city,
        price_filter=price_filter,
        query=query,
        today=today,
        interests=interests,
        limit=limit,
    )
    return FallbackSuggestion(
        kind=kind,
        title=title,
        explanation=explanation,
        events=ranked,
        relaxed_when=when,
        relaxed_radius_km=radius_km,
        relaxed_price_filter=price_filter,
        relaxed_only_new=only_new,
    )


def build_fallback_suggestions(
    events: Sequence,
    *,
    when: str,
    today: date,
    origin_city: str,
    radius_km: int,
    price_filter: str,
    query: str,
    type_filter: str,
    only_new: bool,
    is_new: Callable,
    interests: Optional[Iterable[str]] = None,
    max_suggestions: int = 3,
    events_per_suggestion: int = 3,
):
    """Find nearby alternatives without silently changing the user's active search.

    Search text and event type are never relaxed. Each primary suggestion changes only
    one constraint, making the trade-off explicit. A combined time+radius fallback is
    considered only when no single-step relaxation finds anything.
    """
    suggestions = []

    # 1) Extend time to the first wider window that actually finds something.
    for wider_when in DATE_RELAXATIONS.get(when, []):
        suggestion = _candidate(
            events,
            kind="time",
            title=f"Titta längre fram: {wider_when.lower()}",
            explanation=f"Samma sökning, men perioden ändras från {when.lower()} till {wider_when.lower()}.",
            when=wider_when,
            radius_km=radius_km,
            price_filter=price_filter,
            only_new=only_new,
            today=today,
            origin_city=origin_city,
            query=query,
            type_filter=type_filter,
            is_new=is_new,
            interests=interests,
            limit=events_per_suggestion,
        )
        if suggestion:
            suggestions.append(suggestion)
            break

    # 2) Expand radius to the nearest larger distance that produces results.
    if origin_city != "Hela Sverige":
        for wider_radius in [r for r in RADIUS_STEPS if r > radius_km]:
            suggestion = _candidate(
                events,
                kind="radius",
                title=f"Utöka till {wider_radius} km",
                explanation=f"Samma datum och budget, men sökradien ökas från {radius_km} till {wider_radius} km.",
                when=when,
                radius_km=wider_radius,
                price_filter=price_filter,
                only_new=only_new,
                today=today,
                origin_city=origin_city,
                query=query,
                type_filter=type_filter,
                is_new=is_new,
                interests=interests,
                limit=events_per_suggestion,
            )
            if suggestion:
                suggestions.append(suggestion)
                break

    # 3) Relax price only when the user actively constrained it.
    if price_filter != "Alla priser":
        suggestion = _candidate(
            events,
            kind="price",
            title="Visa även andra priser",
            explanation=f"Samma plats och period, men budgetfiltret {price_filter.lower()} släpps.",
            when=when,
            radius_km=radius_km,
            price_filter="Alla priser",
            only_new=only_new,
            today=today,
            origin_city=origin_city,
            query=query,
            type_filter=type_filter,
            is_new=is_new,
            interests=interests,
            limit=events_per_suggestion,
        )
        if suggestion:
            suggestions.append(suggestion)

    # 4) "Only new" is secondary discovery metadata and can be explicitly relaxed.
    if only_new:
        suggestion = _candidate(
            events,
            kind="new",
            title="Visa även tidigare upptäckta event",
            explanation="Samma sökning, men filtret Endast nytt i Upplevio släpps.",
            when=when,
            radius_km=radius_km,
            price_filter=price_filter,
            only_new=False,
            today=today,
            origin_city=origin_city,
            query=query,
            type_filter=type_filter,
            is_new=is_new,
            interests=interests,
            limit=events_per_suggestion,
        )
        if suggestion:
            suggestions.append(suggestion)

    if suggestions:
        return suggestions[:max_suggestions]

    # If no single change helps, try one clearly labelled combined relaxation.
    wider_when_options = DATE_RELAXATIONS.get(when, [])
    wider_radius_options = [r for r in RADIUS_STEPS if r > radius_km] if origin_city != "Hela Sverige" else []
    if wider_when_options and wider_radius_options:
        for wider_when in wider_when_options:
            for wider_radius in wider_radius_options:
                suggestion = _candidate(
                    events,
                    kind="time_radius",
                    title=f"Bredda till {wider_when.lower()} och {wider_radius} km",
                    explanation="Inget hittades med en enda liten ändring. Här breddas både tid och avstånd; övriga val behålls.",
                    when=wider_when,
                    radius_km=wider_radius,
                    price_filter=price_filter,
                    only_new=only_new,
                    today=today,
                    origin_city=origin_city,
                    query=query,
                    type_filter=type_filter,
                    is_new=is_new,
                    interests=interests,
                    limit=events_per_suggestion,
                )
                if suggestion:
                    return [suggestion]

    return []
