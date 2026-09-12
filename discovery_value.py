
LOCAL_DISCOVERY_SOURCES = {"City Örebro", "Lov Örebro"}

def is_local_discovery_tip(event) -> bool:
    """Editorial badge only; it does not alter organic ranking."""
    sources = set(getattr(event, "source_names", []) or [])
    return bool(sources & LOCAL_DISCOVERY_SOURCES)
