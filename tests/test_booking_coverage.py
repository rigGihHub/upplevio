
from models import Event
from booking_coverage import booking_coverage_report

def ev(i,source,**kw):
    base=dict(id=str(i),title=f"Event {i}",event_type="Aktivitet",category="Lokalt",start_date="2026-09-10",
        end_date=None,start_time=None,venue="V",city="Örebro",region="Örebro",country="SE",source_names=[source])
    base.update(kw)
    return Event(**base)

def test_coverage_counts_only_real_booking_paths():
    rows=[
        ev(1,"City Örebro",booking_url="https://tickster.com/e/1",booking_partner="tickster.com"),
        ev(2,"City Örebro",official_url="https://cityorebro.com/evenemang/x"),
        ev(3,"Conventum",ticket_url="https://www.eventim.se/event/3"),
    ]
    report=booking_coverage_report(rows)
    by={r["source"]:r for r in report["sources"]}
    assert by["City Örebro"]["bookable"]==1
    assert by["City Örebro"]["total"]==2
    assert by["City Örebro"]["booking_coverage"]==0.5
    assert by["City Örebro"]["partners"]=={"Tickster":1}
    assert by["Conventum"]["bookable"]==1

def test_empty_coverage_is_safe():
    r=booking_coverage_report([])
    assert r["totals"]["booking_coverage"]==0.0
