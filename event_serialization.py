"""Plain cache payloads survive Streamlit reloading dataclass modules."""
from dataclasses import asdict
from copy import deepcopy


def event_to_payload(event):
    return asdict(event)


def event_from_payload(payload):
    # Resolve current classes here, rather than retaining pre-reload imports.
    from models import Event, SourceRecord
    values = deepcopy(payload)
    values["source_records"] = [SourceRecord(**record) for record in values.get("source_records", [])]
    return Event(**values)
