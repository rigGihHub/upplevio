"""Small, deterministic helpers for keeping the Streamlit result view light."""

INITIAL_RESULT_LIMIT = 12
RESULT_BATCH_SIZE = 12


def result_filter_signature(*, origin_city, when, radius_km, price_filter, query, type_filter, only_new, interests):
    """Return a stable signature for the filters that define the current result list.

    UI-only state such as the current visible batch is deliberately excluded.
    """
    return (
        origin_city or "",
        when or "",
        radius_km,
        price_filter or "",
        (query or "").strip(),
        type_filter or "",
        bool(only_new),
        tuple(sorted(interests or [])),
    )


def clamp_result_limit(total: int, requested: int | None = None, *, initial: int = INITIAL_RESULT_LIMIT) -> int:
    total = max(0, int(total or 0))
    requested = initial if requested is None else max(0, int(requested))
    return min(total, requested)


def next_result_limit(total: int, current: int, *, batch: int = RESULT_BATCH_SIZE) -> int:
    total = max(0, int(total or 0))
    current = max(0, int(current or 0))
    batch = max(1, int(batch or 1))
    return min(total, current + batch)


def remaining_result_count(total: int, visible: int) -> int:
    return max(0, int(total or 0) - max(0, int(visible or 0)))


def event_id_signature(event_ids) -> str:
    """Stable signature used to avoid repeating ingestion DB writes on UI-only reruns."""
    import hashlib
    clean = sorted({str(x) for x in (event_ids or []) if x})
    return hashlib.sha1("\n".join(clean).encode("utf-8")).hexdigest()
