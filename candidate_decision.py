
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone, date
from pathlib import Path
from statistics import median

SNAPSHOT_DB = Path("upplevio_candidate_snapshots.db")

@dataclass(frozen=True)
class CandidateDecision:
    source: str
    decision: str  # Aktivera | Fortsätt mäta | Avstå
    reasons: tuple[str, ...]
    snapshots: int
    distinct_days: int
    median_unique_events: float | None
    median_unique_share: float | None
    observed_unique_event_types: tuple[str, ...]
    observed_unique_frontier_segments: tuple[str, ...]
    observed_underserved_segments: tuple[str, ...]
    median_unique_events_in_underserved_segments: float | None
    parser_success_rate: float | None


def _connect(path: Path):
    con=sqlite3.connect(path)
    con.execute(
        "CREATE TABLE IF NOT EXISTS candidate_snapshots("
        "source TEXT NOT NULL,"
        "snapshot_day TEXT NOT NULL,"
        "recorded_at TEXT NOT NULL,"
        "status TEXT NOT NULL,"
        "candidate_events INTEGER NOT NULL,"
        "represented_after_dedupe INTEGER NOT NULL,"
        "unique_events INTEGER NOT NULL,"
        "overlap_events INTEGER NOT NULL,"
        "unique_share REAL,"
        "bookable INTEGER NOT NULL,"
        "event_types_json TEXT NOT NULL,"
        "unique_event_types_json TEXT NOT NULL,"
        "frontier_segments_json TEXT NOT NULL DEFAULT '[]',"
        "unique_frontier_segments_json TEXT NOT NULL DEFAULT '[]',"
        "underserved_segments_json TEXT NOT NULL DEFAULT '[]',"
        "unique_events_in_underserved_segments INTEGER NOT NULL DEFAULT 0,"
        "PRIMARY KEY(source,snapshot_day))"
    )
    existing={r[1] for r in con.execute("PRAGMA table_info(candidate_snapshots)")}
    migrations={
        "frontier_segments_json": "TEXT NOT NULL DEFAULT '[]'",
        "unique_frontier_segments_json": "TEXT NOT NULL DEFAULT '[]'",
        "underserved_segments_json": "TEXT NOT NULL DEFAULT '[]'",
        "unique_events_in_underserved_segments": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, ddl in migrations.items():
        if column not in existing:
            con.execute(f"ALTER TABLE candidate_snapshots ADD COLUMN {column} {ddl}")
    return con


def record_candidate_snapshot(audit_rows, health_rows, *, db_path=None, recorded_at=None):
    path=Path(db_path or SNAPSHOT_DB)
    now=recorded_at or datetime.now(timezone.utc)
    if isinstance(now,str):
        now=datetime.fromisoformat(now)
    day=now.date().isoformat()
    health={r["source"]:r for r in (health_rows or [])}
    con=_connect(path)
    try:
        for row in audit_rows or []:
            source=row["source"]
            h=health.get(source,{})
            status=h.get("status") or "Okänd"
            con.execute(
                "INSERT OR REPLACE INTO candidate_snapshots("
                "source,snapshot_day,recorded_at,status,candidate_events,represented_after_dedupe,"
                "unique_events,overlap_events,unique_share,bookable,event_types_json,unique_event_types_json,"
                "frontier_segments_json,unique_frontier_segments_json,underserved_segments_json,unique_events_in_underserved_segments"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    source,day,now.isoformat(),status,
                    int(row.get("candidate_events") or 0),
                    int(row.get("represented_after_dedupe") or 0),
                    int(row.get("unique_events") or 0),
                    int(row.get("overlap_events") or 0),
                    row.get("unique_share"),
                    int(row.get("bookable") or 0),
                    json.dumps(row.get("event_types") or [],ensure_ascii=False,sort_keys=True),
                    json.dumps(row.get("unique_event_types") or [],ensure_ascii=False,sort_keys=True),
                    json.dumps(row.get("frontier_segments") or [],ensure_ascii=False,sort_keys=True),
                    json.dumps(row.get("unique_frontier_segments") or [],ensure_ascii=False,sort_keys=True),
                    json.dumps(row.get("underserved_segments") or [],ensure_ascii=False,sort_keys=True),
                    int(row.get("unique_events_in_underserved_segments") or 0),
                ),
            )
        # Persist failed-source health even when no audit row could be produced.
        audited={r["source"] for r in (audit_rows or [])}
        for source,h in health.items():
            if source in audited:
                continue
            con.execute(
                "INSERT OR REPLACE INTO candidate_snapshots("
                "source,snapshot_day,recorded_at,status,candidate_events,represented_after_dedupe,"
                "unique_events,overlap_events,unique_share,bookable,event_types_json,unique_event_types_json,"
                "frontier_segments_json,unique_frontier_segments_json,underserved_segments_json,unique_events_in_underserved_segments"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (source,day,now.isoformat(),h.get("status") or "Fel",0,0,0,0,None,0,"[]","[]","[]","[]","[]",0),
            )
        con.commit()
    finally:
        con.close()


def candidate_history(*, source=None, db_path=None):
    path=Path(db_path or SNAPSHOT_DB)
    if not path.exists():
        return []
    con=_connect(path)
    try:
        sql=("SELECT source,snapshot_day,recorded_at,status,candidate_events,represented_after_dedupe,"
             "unique_events,overlap_events,unique_share,bookable,event_types_json,unique_event_types_json,"
             "frontier_segments_json,unique_frontier_segments_json,underserved_segments_json,unique_events_in_underserved_segments "
             "FROM candidate_snapshots")
        params=()
        if source:
            sql += " WHERE source=?"
            params=(source,)
        sql += " ORDER BY snapshot_day,source"
        rows=con.execute(sql,params).fetchall()
    finally:
        con.close()
    out=[]
    for r in rows:
        out.append({
            "source":r[0],"snapshot_day":r[1],"recorded_at":r[2],"status":r[3],
            "candidate_events":r[4],"represented_after_dedupe":r[5],
            "unique_events":r[6],"overlap_events":r[7],"unique_share":r[8],
            "bookable":r[9],"event_types":json.loads(r[10] or "[]"),
            "unique_event_types":json.loads(r[11] or "[]"),
            "frontier_segments":json.loads(r[12] or "[]"),
            "unique_frontier_segments":json.loads(r[13] or "[]"),
            "underserved_segments":json.loads(r[14] or "[]"),
            "unique_events_in_underserved_segments":r[15],
        })
    return out


def decide_candidate(source, snapshots):
    rows=[r for r in snapshots if r.get("source")==source]
    days=len({r["snapshot_day"] for r in rows})
    n=len(rows)
    if not rows:
        return CandidateDecision(source,"Fortsätt mäta",("Ingen mätdata ännu.",),0,0,None,None,(),(),(),None,None)

    successes=[r for r in rows if str(r.get("status","")).casefold()=="ok"]
    success_rate=len(successes)/n if n else None
    uniques=[r["unique_events"] for r in successes]
    shares=[r["unique_share"] for r in successes if r["unique_share"] is not None]
    med_unique=float(median(uniques)) if uniques else None
    med_share=float(median(shares)) if shares else None
    unique_types=sorted({t for r in successes for t in (r.get("unique_event_types") or [])})
    unique_frontier=sorted({t for r in successes for t in (r.get("unique_frontier_segments") or [])})
    underserved=sorted({t for r in successes for t in (r.get("underserved_segments") or [])})
    underserved_counts=[int(r.get("unique_events_in_underserved_segments") or 0) for r in successes]
    med_underserved=float(median(underserved_counts)) if underserved_counts else None

    reasons=[]
    decision="Fortsätt mäta"

    # Severe parser instability can justify rejecting after enough evidence.
    if n >= 4 and success_rate is not None and success_rate <= 0.50:
        decision="Avstå"
        reasons.append(f"Parsern lyckades bara i {success_rate*100:.0f}% av mätningarna.")
    # Persistent high-overlap/no-new-category candidate can be rejected.
    elif n >= 4 and med_share is not None and med_share <= 0.10 and not unique_types and not unique_frontier:
        decision="Avstå"
        reasons.append(f"Median unik andel är bara {med_share*100:.0f}% efter minst fyra mätningar.")
        reasons.append("Ingen unik eventtyp eller Coverage Frontier-nytta har observerats.")
    # Activation requires repeated evidence, stable parsing, and real unique value.
    elif n >= 3 and days >= 3 and success_rate is not None and success_rate >= 0.80:
        strong_volume=(med_unique is not None and med_unique >= 3)
        strong_share=(med_share is not None and med_share >= 0.35)
        category_value=bool(unique_types or unique_frontier)
        frontier_value=bool(underserved) and med_underserved is not None and med_underserved >= 1
        if (strong_volume or strong_share) and (category_value or frontier_value or (med_unique is not None and med_unique >= 5)):
            decision="Aktivera"
            reasons.append(f"Parsern har varit stabil i {success_rate*100:.0f}% av mätningarna.")
            if strong_volume:
                reasons.append(f"Medianen är {med_unique:.0f} unika event per snapshot.")
            if strong_share:
                reasons.append(f"Median unik andel är {med_share*100:.0f}%.")
            if unique_types:
                reasons.append("Har tillfört unik eventtyp: " + ", ".join(unique_types) + ".")
            if frontier_value:
                reasons.append("Tillför återkommande unika event i svagt täckta segment: " + ", ".join(underserved) + ".")
        else:
            reasons.append("Tillräckligt många mätningar finns, men unik nyttan är ännu inte stark nog.")
    else:
        if n < 3 or days < 3:
            reasons.append(f"Behöver minst 3 snapshots på 3 olika dagar; har {n} snapshots på {days} dagar.")
        if success_rate is not None and success_rate < 0.80:
            reasons.append(f"Parserstabilitet {success_rate*100:.0f}% är under aktiveringsnivån 80%.")
        if med_unique is not None:
            reasons.append(f"Median unika event hittills: {med_unique:.0f}.")
        if med_share is not None:
            reasons.append(f"Median unik andel hittills: {med_share*100:.0f}%.")

    return CandidateDecision(
        source=source,decision=decision,reasons=tuple(reasons),snapshots=n,distinct_days=days,
        median_unique_events=med_unique,median_unique_share=med_share,
        observed_unique_event_types=tuple(unique_types),
        observed_unique_frontier_segments=tuple(unique_frontier),
        observed_underserved_segments=tuple(underserved),
        median_unique_events_in_underserved_segments=med_underserved,
        parser_success_rate=success_rate,
    )


def candidate_decisions(*, db_path=None):
    history=candidate_history(db_path=db_path)
    sources=sorted({r["source"] for r in history})
    return [decide_candidate(source,history) for source in sources]
