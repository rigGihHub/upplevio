from datetime import date
from unittest.mock import patch

from candidate_local_sources import promoted_local_discovery_events
from models import Event


def event(**overrides):
    values=dict(id="x",title="Publik konsert",event_type="Konsert",category="Konsert",start_date="2026-09-20",end_date=None,start_time="19:00",venue="Kulturkvarteret",city="Örebro",region="Örebro län",country="Sverige",official_url="https://example.test/event",source_names=["Kulturkvarteret"],quality_notes=["Kandidatimport – officiell kalender", "Påverkar inte publik discovery"],data_quality="partial")
    values.update(overrides)
    return Event(**values)


def test_promotion_requires_future_local_event_and_official_url():
    candidates=[
        event(),
        event(id="old",start_date="2026-09-01"),
        event(id="away",city="Karlskoga"),
        event(id="no-url",official_url=None),
    ]
    with patch("candidate_local_sources.fetch_candidate_sources",return_value=(candidates,[{"source":"Kulturkvarteret","status":"OK","events":4,"error":None}])):
        rows,health=promoted_local_discovery_events(today=date(2026,9,15))
    assert [row.id for row in rows] == ["x"]
    assert rows[0].data_quality == "source_verified"
    assert "Godkänd för publik discovery" in " ".join(rows[0].quality_notes)
    assert health[0][0] == "Kulturkvarteret"
