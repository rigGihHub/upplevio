
from datetime import date
from models import Event
from local_source_audit import local_source_audit

def ev(i, source_names, event_type="Konsert", booking_url=None):
    return Event(
        id=str(i), title=f"E{i}", event_type=event_type, category=event_type,
        start_date="2026-09-20", end_date=None, start_time=None,
        venue="V", city="Örebro", region="Örebro", country="SE",
        source_names=source_names, booking_url=booking_url
    )

def test_unique_and_overlap_are_separate():
    rows=[
        ev(1,["Örebro Konserthus"],"Konsert"),
        ev(2,["Örebro Konserthus","Visit Örebro – redaktionella eventlistor"],"Konsert"),
        ev(3,["Örebro Teater"],"Teater"),
    ]
    r=local_source_audit(rows,today=date(2026,9,1))
    by={x["source"]:x for x in r["sources"]}
    assert by["Örebro Konserthus"]["represented_events"]==2
    assert by["Örebro Konserthus"]["unique_events"]==1
    assert by["Örebro Konserthus"]["overlap_events"]==1
    assert by["Örebro Teater"]["unique_events"]==1

def test_booking_coverage_is_source_level():
    rows=[
        ev(1,["Conventum"],booking_url="https://secure.tickster.com/x"),
        ev(2,["Conventum"]),
    ]
    r=local_source_audit(rows,today=date(2026,9,1))
    row=next(x for x in r["sources"] if x["source"]=="Conventum")
    assert row["bookable_events"]==1
    assert row["booking_coverage"]==0.5

def test_category_breadth_is_exposed_without_fake_score():
    rows=[
        ev(1,["City Örebro"],"Marknad"),
        ev(2,["City Örebro"],"Familj"),
        ev(3,["City Örebro","Conventum"],"Konsert"),
    ]
    r=local_source_audit(rows,today=date(2026,9,1))
    row=next(x for x in r["sources"] if x["source"]=="City Örebro")
    assert row["category_count"]==3
    assert row["unique_category_count"]==2
    assert "score" not in row

def test_non_local_sources_are_excluded():
    rows=[ev(1,["Ticketmaster"])]
    r=local_source_audit(rows,today=date(2026,9,1))
    assert r["sources"]==[]
