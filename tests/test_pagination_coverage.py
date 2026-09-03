from unittest.mock import patch

import sources
from coverage import coverage_snapshot
from models import Event


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        return None
    def json(self):
        return self._payload


def tm_event(eid, name="Test", day="2026-09-20"):
    return {
        "id": eid,
        "name": name,
        "dates": {"start": {"localDate": day}, "status": {"code": "onsale"}},
        "_embedded": {"venues": [{"name": "Arena", "city": {"name": "Örebro"}, "country": {"name": "Sweden"}}]},
        "classifications": [{"segment": {"name": "Music"}, "genre": {"name": "Rock"}}],
        "url": f"https://example.test/{eid}",
    }


def test_ticketmaster_paginates_and_stops_at_total_pages():
    payloads = [
        {"_embedded": {"events": [tm_event("1")]}, "page": {"totalPages": 2, "totalElements": 2}},
        {"_embedded": {"events": [tm_event("2")]}, "page": {"totalPages": 2, "totalElements": 2}},
    ]
    with patch("sources.requests.get", side_effect=[FakeResponse(x) for x in payloads]) as get:
        events, meta = sources.ticketmaster_events("key", page_size=1, max_pages=5)
    assert [e.id for e in events] == ["tm-1", "tm-2"]
    assert meta["pages_fetched"] == 2
    assert meta["truncated"] is False
    assert get.call_count == 2


def test_ticketmaster_marks_safety_cap_as_truncated():
    payload = {"_embedded": {"events": [tm_event("1")]}, "page": {"totalPages": 10, "totalElements": 10}}
    with patch("sources.requests.get", side_effect=[FakeResponse(payload), FakeResponse(payload)]):
        _, meta = sources.ticketmaster_events("key", page_size=1, max_pages=2)
    assert meta["pages_fetched"] == 2
    assert meta["truncated"] is True


def vs_payload(items):
    return {"@graph": items}


def vs_event(eid, name="Event"):
    return {"@id": eid, "name": name, "startDate": "2026-09-20"}


def test_visitsweden_uses_raw_page_size_for_pagination():
    # First page has 2 raw records but only 1 usable event. We must still request page 2.
    responses = [
        FakeResponse(vs_payload([vs_event("a"), {"@id": "bad", "name": "No date"}])),
        FakeResponse(vs_payload([vs_event("b")])),
    ]
    with patch("sources.requests.get", side_effect=responses) as get:
        events, meta = sources.visitsweden_events(page_size=2, max_pages=5)
    assert len(events) == 2
    assert meta["pages_fetched"] == 2
    assert meta["truncated"] is False
    assert get.call_count == 2


def test_coverage_snapshot_does_not_invent_market_coverage_percentage():
    e = Event(
        id="1", title="X", event_type="Konsert", category="Rock",
        start_date="2026-09-20", end_date=None, start_time=None,
        venue="Arena", city="Örebro", region="Örebro", country="Sverige",
        source_names=["Ticketmaster"], source_count=1,
    )
    snapshot = coverage_snapshot([e], [], horizon_days=30)
    assert "coverage_percent" not in snapshot
    assert snapshot["events"] >= 0
