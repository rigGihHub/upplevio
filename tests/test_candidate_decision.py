
from datetime import datetime, timezone
from candidate_decision import record_candidate_snapshot, candidate_history, candidate_decisions, decide_candidate

def audit(source="Kulturkvarteret", unique=4, overlap=2, share=None, unique_types=None):
    total=unique+overlap
    return [{
        "source":source,
        "candidate_events":total,
        "represented_after_dedupe":total,
        "unique_events":unique,
        "overlap_events":overlap,
        "unique_share": (unique/total if total else None) if share is None else share,
        "bookable":1,
        "event_types":["Konsert","Familj"],
        "unique_event_types": unique_types if unique_types is not None else ["Familj"],
    }]

def health(source="Kulturkvarteret", status="OK"):
    return [{"source":source,"status":status,"events":6,"error":None}]

def test_same_day_replaces_snapshot(tmp_path):
    db=tmp_path/"cand.db"
    t=datetime(2026,9,1,8,tzinfo=timezone.utc)
    record_candidate_snapshot(audit(unique=4),health(),db_path=db,recorded_at=t)
    record_candidate_snapshot(audit(unique=5),health(),db_path=db,recorded_at=t)
    rows=candidate_history(db_path=db)
    assert len(rows)==1
    assert rows[0]["unique_events"]==5

def test_three_days_of_strong_unique_value_can_activate(tmp_path):
    db=tmp_path/"cand.db"
    for day in [1,2,3]:
        record_candidate_snapshot(
            audit(unique=4,overlap=2,unique_types=["Familj"]),
            health(),
            db_path=db,
            recorded_at=datetime(2026,9,day,8,tzinfo=timezone.utc),
        )
    d=candidate_decisions(db_path=db)[0]
    assert d.decision=="Aktivera"
    assert d.snapshots==3
    assert d.distinct_days==3

def test_one_snapshot_never_activates(tmp_path):
    db=tmp_path/"cand.db"
    record_candidate_snapshot(audit(unique=20,overlap=0),health(),db_path=db,recorded_at=datetime(2026,9,1,tzinfo=timezone.utc))
    d=candidate_decisions(db_path=db)[0]
    assert d.decision=="Fortsätt mäta"

def test_persistent_overlap_without_category_value_can_reject(tmp_path):
    db=tmp_path/"cand.db"
    for day in [1,2,3,4]:
        record_candidate_snapshot(
            audit(unique=0,overlap=10,share=0.0,unique_types=[]),
            health(),
            db_path=db,
            recorded_at=datetime(2026,9,day,tzinfo=timezone.utc),
        )
    d=candidate_decisions(db_path=db)[0]
    assert d.decision=="Avstå"
    assert any("Ingen unik eventtyp" in r for r in d.reasons)

def test_parser_instability_can_reject_after_four_snapshots(tmp_path):
    db=tmp_path/"cand.db"
    for day,status in [(1,"Fel"),(2,"Fel"),(3,"OK"),(4,"Fel")]:
        rows=audit(unique=3,overlap=1) if status=="OK" else []
        record_candidate_snapshot(
            rows,health(status=status),db_path=db,
            recorded_at=datetime(2026,9,day,tzinfo=timezone.utc),
        )
    d=candidate_decisions(db_path=db)[0]
    assert d.decision=="Avstå"
    assert d.parser_success_rate==0.25

def test_booking_is_not_required_for_activation():
    rows=[]
    for day in [1,2,3]:
        rows.append({
            "source":"Wadköping","snapshot_day":f"2026-09-0{day}","status":"OK",
            "unique_events":4,"unique_share":0.5,"unique_event_types":["Familj"],
        })
    d=decide_candidate("Wadköping",rows)
    assert d.decision=="Aktivera"


def test_frontier_value_is_persisted_and_exposed(tmp_path):
    db=tmp_path/"cand.db"
    row=audit(source="Örebro läns museum",unique=3,overlap=1,unique_types=[])[0]
    row.update({
        "frontier_segments":["Museum & utställning"],
        "unique_frontier_segments":["Museum & utställning"],
        "underserved_segments":["Museum & utställning"],
        "unique_events_in_underserved_segments":2,
    })
    for day in [1,2,3]:
        record_candidate_snapshot([row],health(source="Örebro läns museum"),db_path=db,
                                  recorded_at=datetime(2026,9,day,tzinfo=timezone.utc))
    saved=candidate_history(source="Örebro läns museum",db_path=db)[0]
    assert saved["underserved_segments"]==["Museum & utställning"]
    d=candidate_decisions(db_path=db)[0]
    assert d.decision=="Aktivera"
    assert d.median_unique_events_in_underserved_segments==2.0
    assert d.observed_underserved_segments==("Museum & utställning",)
