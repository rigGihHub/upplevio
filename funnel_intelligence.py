
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from engagement import TRACKING_DB
from conversion_attribution import ATTRIBUTION_DB

def _ratio(num, den):
    return (num / den) if den else None

def _read_engagement(db_path):
    path=Path(db_path)
    if not path.exists():
        return []
    con=sqlite3.connect(path)
    try:
        rows=con.execute(
            "SELECT action,event_id,partner,context_json FROM engagement_events "
            "WHERE action IN ('impression','activity_open')"
        ).fetchall()
    except sqlite3.OperationalError:
        rows=[]
    finally:
        con.close()
    out=[]
    for action,event_id,partner,raw in rows:
        try:
            ctx=json.loads(raw or "{}")
        except Exception:
            ctx={}
        out.append({"action":action,"event_id":event_id,"partner":partner,"context":ctx})
    return out

def _read_clicks(db_path):
    path=Path(db_path)
    if not path.exists():
        return []
    con=sqlite3.connect(path)
    try:
        rows=con.execute(
            "SELECT event_id,partner_key,partner_name,context_json FROM outbound_clicks"
        ).fetchall()
    except sqlite3.OperationalError:
        rows=[]
    finally:
        con.close()
    out=[]
    for event_id,key,name,raw in rows:
        try:
            ctx=json.loads(raw or "{}")
        except Exception:
            ctx={}
        out.append({"event_id":event_id,"partner_key":key,"partner_name":name,"context":ctx})
    return out

def _event_meta(events):
    result={}
    for e in events or []:
        result[str(e.id)]={
            "source": ", ".join(getattr(e,"source_names",[]) or []) or "Okänd källa",
            "event_type": getattr(e,"event_type",None) or "Okänd typ",
            "partner": getattr(e,"booking_partner",None) or "Okänd partner",
        }
    return result

def funnel_report(events=None, *, engagement_db=None, attribution_db=None):
    meta=_event_meta(events)
    engagement=_read_engagement(engagement_db or TRACKING_DB)
    clicks=_read_clicks(attribution_db or ATTRIBUTION_DB)

    by_source=defaultdict(lambda:{"impressions":0,"opens":0,"booking_clicks":0})
    by_type=defaultdict(lambda:{"impressions":0,"opens":0,"booking_clicks":0})
    by_partner=defaultdict(lambda:{"impressions":0,"opens":0,"booking_clicks":0})

    def dims(event_id, ctx, partner=None):
        m=meta.get(str(event_id),{})
        source=ctx.get("source") or m.get("source") or "Okänd källa"
        event_type=ctx.get("event_type") or m.get("event_type") or "Okänd typ"
        partner_name=partner or ctx.get("partner") or m.get("partner") or "Okänd partner"
        return source,event_type,partner_name

    for row in engagement:
        source,event_type,partner=dims(row["event_id"],row["context"],row.get("partner"))
        field="impressions" if row["action"]=="impression" else "opens"
        by_source[source][field]+=1
        by_type[event_type][field]+=1
        by_partner[partner][field]+=1

    for row in clicks:
        source,event_type,partner=dims(row["event_id"],row["context"],row["partner_name"])
        by_source[source]["booking_clicks"]+=1
        by_type[event_type]["booking_clicks"]+=1
        by_partner[partner]["booking_clicks"]+=1

    def finalize(grouped, name_key):
        rows=[]
        for name,data in grouped.items():
            rows.append({
                name_key:name,
                **data,
                "open_rate":_ratio(data["opens"],data["impressions"]),
                "booking_click_rate":_ratio(data["booking_clicks"],data["impressions"]),
                "click_from_open_rate":_ratio(data["booking_clicks"],data["opens"]),
            })
        rows.sort(key=lambda r:(-(r["booking_clicks"]),-(r["opens"]),r[name_key].casefold()))
        return rows

    totals={
        "impressions":sum(1 for r in engagement if r["action"]=="impression"),
        "opens":sum(1 for r in engagement if r["action"]=="activity_open"),
        "booking_clicks":len(clicks),
    }
    totals["open_rate"]=_ratio(totals["opens"],totals["impressions"])
    totals["booking_click_rate"]=_ratio(totals["booking_clicks"],totals["impressions"])
    totals["click_from_open_rate"]=_ratio(totals["booking_clicks"],totals["opens"])
    return {
        "totals":totals,
        "by_source":finalize(by_source,"source"),
        "by_event_type":finalize(by_type,"event_type"),
        "by_partner":finalize(by_partner,"partner"),
    }

def session_impression_key(event_id, filter_signature):
    return f"{filter_signature}:{event_id}"
