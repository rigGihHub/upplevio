from datetime import datetime, timezone

from candidate_decision import record_candidate_snapshot
from candidate_portfolio import candidate_portfolio


def _audit(source, unique, total=None, gap=0, unique_share=None):
    total = unique if total is None else total
    overlap=max(0,total-unique)
    if unique_share is None and total:
        unique_share=unique/total
    return [{
        "source":source,
        "candidate_events":total,
        "represented_after_dedupe":total,
        "unique_events":unique,
        "overlap_events":overlap,
        "unique_share":unique_share,
        "bookable":0,
        "event_types":["Evenemang"],
        "unique_event_types":["Evenemang"] if unique else [],
        "frontier_segments":["Lokalt & community"],
        "unique_frontier_segments":["Lokalt & community"] if unique else [],
        "underserved_segments":["Lokalt & community"] if gap else [],
        "unique_events_in_underserved_segments":gap,
    }]


def _health(source,status="Ok"):
    return [{"source":source,"status":status,"events":1,"error":None}]


def _record_days(path, source, rows):
    for day,audit,status in rows:
        record_candidate_snapshot(audit,_health(source,status),db_path=path,
            recorded_at=datetime(2026,9,day,10,0,tzinfo=timezone.utc))


def test_portfolio_prioritises_candidate_with_frontier_value(tmp_path):
    db=tmp_path/"candidate.db"
    rows=[]
    for day in (1,2,3):
        rows.append((day,_audit("Källa A",2,total=4,gap=1),"Ok"))
    _record_days(db,"Källa A",rows)
    row=candidate_portfolio(db_path=db)[0]
    assert row.priority in {"Aktiveringskandidat","Prioritera mätning"}
    assert row.median_gap_events == 1
    assert row.evidence == "Aktiveringsbart underlag"


def test_portfolio_flags_repeated_zero_unique_value(tmp_path):
    db=tmp_path/"candidate.db"
    rows=[]
    for day in (1,2,3,4):
        rows.append((day,_audit("Källa B",0,total=2,gap=0,unique_share=0.0),"Ok"))
    _record_days(db,"Källa B",rows)
    row=candidate_portfolio(db_path=db)[0]
    assert row.priority == "Låg prioritet"
    assert row.zero_unique_success_rate == 1.0


def test_portfolio_flags_parser_instability(tmp_path):
    db=tmp_path/"candidate.db"
    for day,status in [(1,"Ok"),(2,"Fel"),(3,"Fel"),(4,"Fel")]:
        audit=_audit("Källa C",1,total=1,gap=0) if status=="Ok" else []
        record_candidate_snapshot(audit,_health("Källa C",status),db_path=db,
            recorded_at=datetime(2026,9,day,10,0,tzinfo=timezone.utc))
    row=candidate_portfolio(db_path=db)[0]
    # CandidateDecision may already say Avstå; either way it must not be normal measurement work.
    assert row.priority in {"Parserproblem","Låg prioritet"}
    assert row.parser_success_rate == 0.25


def test_portfolio_does_not_promote_one_day_snapshot(tmp_path):
    db=tmp_path/"candidate.db"
    record_candidate_snapshot(_audit("Källa D",10,total=10,gap=5),_health("Källa D"),db_path=db,
        recorded_at=datetime(2026,9,1,10,0,tzinfo=timezone.utc))
    row=candidate_portfolio(db_path=db)[0]
    assert row.priority == "Fortsätt mäta"
    assert row.evidence == "För lite underlag"
