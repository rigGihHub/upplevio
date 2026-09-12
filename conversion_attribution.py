
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ATTRIBUTION_DB = Path("upplevio_attribution.db")

@dataclass(frozen=True)
class OutboundClick:
    click_id: str
    event_id: str
    partner_key: str
    partner_name: str
    campaign_id: Optional[str]
    destination_url: str
    created_at: str

def _connect(path: Path):
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute(
        "CREATE TABLE IF NOT EXISTS outbound_clicks("
        "click_id TEXT PRIMARY KEY,"
        "created_at TEXT NOT NULL,"
        "event_id TEXT NOT NULL,"
        "partner_key TEXT NOT NULL,"
        "partner_name TEXT NOT NULL,"
        "campaign_id TEXT,"
        "destination_url TEXT NOT NULL,"
        "context_json TEXT)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS conversions("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "recorded_at TEXT NOT NULL,"
        "click_id TEXT NOT NULL,"
        "partner_conversion_id TEXT,"
        "status TEXT NOT NULL,"
        "order_value REAL,"
        "currency TEXT,"
        "commission_value REAL,"
        "commission_currency TEXT,"
        "raw_json TEXT,"
        "UNIQUE(click_id, partner_conversion_id),"
        "FOREIGN KEY(click_id) REFERENCES outbound_clicks(click_id))"
    )
    return con

def create_outbound_click(
    *,
    event_id: str,
    partner_key: str,
    partner_name: str,
    destination_url: str,
    campaign_id: Optional[str] = None,
    context: Optional[dict] = None,
    db_path: Optional[Path] = None,
) -> OutboundClick:
    click_id = "upc_" + uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).isoformat()
    path = Path(db_path or ATTRIBUTION_DB)
    con = _connect(path)
    try:
        con.execute(
            "INSERT INTO outbound_clicks(click_id,created_at,event_id,partner_key,partner_name,campaign_id,destination_url,context_json) VALUES(?,?,?,?,?,?,?,?)",
            (
                click_id, created_at, event_id, partner_key, partner_name, campaign_id,
                destination_url, json.dumps(context or {}, ensure_ascii=False, sort_keys=True)
            ),
        )
        con.commit()
    finally:
        con.close()
    return OutboundClick(click_id, event_id, partner_key, partner_name, campaign_id, destination_url, created_at)


def create_or_get_outbound_click(
    *,
    click_id: str,
    event_id: str,
    partner_key: str,
    partner_name: str,
    destination_url: str,
    campaign_id: Optional[str] = None,
    context: Optional[dict] = None,
    db_path: Optional[Path] = None,
) -> OutboundClick:
    if not click_id.startswith("upc_"):
        raise ValueError("Invalid click_id")
    created_at = datetime.now(timezone.utc).isoformat()
    path = Path(db_path or ATTRIBUTION_DB)
    con = _connect(path)
    try:
        con.execute(
            "INSERT OR IGNORE INTO outbound_clicks(click_id,created_at,event_id,partner_key,partner_name,campaign_id,destination_url,context_json) VALUES(?,?,?,?,?,?,?,?)",
            (click_id, created_at, event_id, partner_key, partner_name, campaign_id, destination_url,
             json.dumps(context or {}, ensure_ascii=False, sort_keys=True)),
        )
        row = con.execute(
            "SELECT click_id,event_id,partner_key,partner_name,campaign_id,destination_url,created_at FROM outbound_clicks WHERE click_id=?",
            (click_id,),
        ).fetchone()
        con.commit()
    finally:
        con.close()
    return OutboundClick(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

def record_conversion(
    *,
    click_id: str,
    status: str,
    partner_conversion_id: Optional[str] = None,
    order_value: Optional[float] = None,
    currency: Optional[str] = None,
    commission_value: Optional[float] = None,
    commission_currency: Optional[str] = None,
    raw: Optional[dict] = None,
    db_path: Optional[Path] = None,
) -> bool:
    if status not in {"pending", "confirmed", "rejected", "refunded"}:
        raise ValueError("Unsupported conversion status")
    path = Path(db_path or ATTRIBUTION_DB)
    con = _connect(path)
    try:
        exists = con.execute("SELECT 1 FROM outbound_clicks WHERE click_id=?", (click_id,)).fetchone()
        if not exists:
            raise KeyError("Unknown click_id")
        try:
            con.execute(
                "INSERT INTO conversions(recorded_at,click_id,partner_conversion_id,status,order_value,currency,commission_value,commission_currency,raw_json) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    datetime.now(timezone.utc).isoformat(), click_id, partner_conversion_id, status,
                    order_value, currency, commission_value, commission_currency,
                    json.dumps(raw or {}, ensure_ascii=False, sort_keys=True),
                ),
            )
            con.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    finally:
        con.close()

def attribution_report(*, db_path: Optional[Path] = None) -> dict:
    path = Path(db_path or ATTRIBUTION_DB)
    if not path.exists():
        return {"clicks": 0, "conversions": 0, "confirmed": 0, "commission": 0.0, "partners": []}
    con = _connect(path)
    try:
        clicks = con.execute("SELECT COUNT(*) FROM outbound_clicks").fetchone()[0]
        conversions = con.execute("SELECT COUNT(*) FROM conversions").fetchone()[0]
        confirmed = con.execute("SELECT COUNT(*) FROM conversions WHERE status='confirmed'").fetchone()[0]
        commission = con.execute(
            "SELECT COALESCE(SUM(commission_value),0) FROM conversions WHERE status='confirmed'"
        ).fetchone()[0] or 0
        rows = con.execute(
            "SELECT c.partner_key, c.partner_name, "
            "COUNT(DISTINCT c.click_id) AS clicks, "
            "COUNT(v.id) AS conversions, "
            "SUM(CASE WHEN v.status='confirmed' THEN 1 ELSE 0 END) AS confirmed "
            "FROM outbound_clicks c "
            "LEFT JOIN conversions v ON v.click_id=c.click_id "
            "GROUP BY c.partner_key,c.partner_name "
            "ORDER BY clicks DESC, c.partner_name"
        ).fetchall()
    finally:
        con.close()
    return {
        "clicks": clicks,
        "conversions": conversions,
        "confirmed": confirmed,
        "commission": float(commission),
        "partners": [
            {
                "partner_key": r[0],
                "partner_name": r[1],
                "clicks": r[2],
                "conversions": r[3],
                "confirmed": r[4] or 0,
            }
            for r in rows
        ],
    }
