from booking_intent import booking_cta

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TRACKING_DB = Path("upplevio_engagement.db")
ALLOWED_ACTIONS = {
    "impression", "activity_open", "cta_click", "booking_outbound",
    "sponsored_impression", "sponsored_click", "ad_impression", "ad_click",
    "conversion_received", "conversion_confirmed",
}

def record_action(action: str, *, event_id: Optional[str] = None, campaign_id: Optional[str] = None,
                  company: Optional[str] = None, partner: Optional[str] = None,
                  context: Optional[dict] = None, db_path: Optional[Path] = None) -> None:
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"Unknown tracking action: {action}")
    path = Path(db_path or TRACKING_DB)
    con = sqlite3.connect(path)
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS engagement_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            occurred_at TEXT NOT NULL,
            action TEXT NOT NULL,
            event_id TEXT,
            campaign_id TEXT,
            company TEXT,
            partner TEXT,
            context_json TEXT
        )""")
        con.execute(
            "INSERT INTO engagement_events(occurred_at,action,event_id,campaign_id,company,partner,context_json) VALUES(?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), action, event_id, campaign_id, company, partner,
             json.dumps(context or {}, ensure_ascii=False, sort_keys=True)),
        )
        con.commit()
    finally:
        con.close()

def company_metrics(company: str, *, db_path: Optional[Path] = None) -> dict:
    path = Path(db_path or TRACKING_DB)
    if not path.exists():
        return {"impressions": 0, "activity_visits": 0, "booking_clicks": 0, "sponsored_clicks": 0, "ctr": None}
    con = sqlite3.connect(path)
    try:
        rows = dict(con.execute(
            "SELECT action, COUNT(*) FROM engagement_events WHERE company=? GROUP BY action", (company,)
        ).fetchall())
    except sqlite3.OperationalError:
        rows = {}
    finally:
        con.close()
    impressions = rows.get("sponsored_impression", 0)
    sponsored_clicks = rows.get("sponsored_click", 0)
    return {
        "impressions": impressions,
        "activity_visits": rows.get("activity_open", 0),
        "booking_clicks": rows.get("booking_outbound", 0),
        "sponsored_clicks": sponsored_clicks,
        "ctr": (sponsored_clicks / impressions) if impressions else None,
    }

def booking_target(event):
    cta = booking_cta(event)
    return cta.url if cta and cta.track_as_booking else None

def primary_info_target(event):
    return getattr(event, "official_url", None) or getattr(event, "ticket_url", None)
