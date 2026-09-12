
from dataclasses import dataclass


@dataclass(frozen=True)
class TonightPick:
    event: object
    position: int
    label: str


def tonight_shortlist(ranked_events, limit=3):
    """Keep the existing discovery order; only expose a compact shortlist."""
    if limit <= 0:
        return []
    labels = ["Bäst ikväll", "Nästa val", "Också starkt"]
    result = []
    for idx, event in enumerate(list(ranked_events)[:limit]):
        result.append(
            TonightPick(
                event=event,
                position=idx + 1,
                label=labels[idx] if idx < len(labels) else f"Val {idx + 1}",
            )
        )
    return result


def tonight_remaining(ranked_events, shortlist):
    shown = {pick.event.id for pick in shortlist}
    return [event for event in ranked_events if event.id not in shown]


def tonight_summary(event, *, distance=None, price_text=None):
    """Build a compact, factual decision line without inventing missing data."""
    parts = []
    start = (getattr(event, "start_time", None) or "").strip()
    if start:
        parts.append(f"Start {start[:5]}")
    if distance is not None:
        parts.append(f"{distance:g} km")
    if price_text:
        parts.append(price_text)
    return " · ".join(parts)
