from datetime import date
from models import Event
from coverage_frontier import classify_frontier, coverage_frontier

def ev(i,title,typ,day,sources):
    return Event(id=str(i),title=title,event_type=typ,category=typ,start_date=day,end_date=None,start_time=None,venue="Örebro",city="Örebro",region="Örebro",country="SE",source_names=sources)

def test_classifies_university_and_talks():
    e=ev(1,"Öppen föreläsning på Campus","Föreläsning","2026-09-10",["Örebro universitet"])
    hits=classify_frontier(e)
    assert "Samtal & föreläsning" in hits
    assert "Student & universitet" in hits

def test_frontier_uses_30_60_90_presence():
    events=[
        ev(1,"Konsert A","Konsert","2026-09-10",["Conventum"]),
        ev(2,"Konsert B","Konsert","2026-10-15",["Örebro Konserthus"]),
        ev(3,"Konsert C","Konsert","2026-11-20",["Visit Örebro"]),
    ]
    row=next(r for r in coverage_frontier(events,today=date(2026,9,7))["rows"] if r["segment"]=="Stora konserter")
    assert row["events_30"]==1
    assert row["events_60"]==2
    assert row["events_90"]==3

def test_missing_means_missing_in_current_import():
    report=coverage_frontier([],today=date(2026,9,7))
    assert all(r["status"]=="Saknas i aktuell import" for r in report["rows"])

def test_single_source_dependency_is_explicit():
    events=[ev(1,"Fotbollsmatch","Sport","2026-09-10",["ÖSK Fotboll"])]
    row=next(r for r in coverage_frontier(events,today=date(2026,9,7))["rows"] if r["segment"]=="Publiksport")
    assert row["single_source_dependency"] is True
