import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "data" / "upplevio.db"

def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                event_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query TEXT DEFAULT '',
                event_type TEXT DEFAULT '',
                category TEXT DEFAULT '',
                origin_city TEXT DEFAULT '',
                radius_km INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_seen (
                event_id TEXT PRIMARY KEY,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL
            )
        """)
        conn.commit()

def favorite_ids():
    init_db()
    with connect() as conn:
        return {row[0] for row in conn.execute("SELECT event_id FROM favorites")}

def toggle_favorite(event_id: str):
    init_db()
    with connect() as conn:
        exists = conn.execute("SELECT 1 FROM favorites WHERE event_id=?", (event_id,)).fetchone()
        if exists:
            conn.execute("DELETE FROM favorites WHERE event_id=?", (event_id,))
            active = False
        else:
            conn.execute(
                "INSERT INTO favorites(event_id, created_at) VALUES (?, ?)",
                (event_id, datetime.now(timezone.utc).isoformat()),
            )
            active = True
        conn.commit()
        return active

def get_meta(key: str):
    init_db()
    with connect() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

def set_meta(key: str, value: str):
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()

def list_watches():
    init_db()
    with connect() as conn:
        rows=conn.execute("SELECT id,name,query,event_type,category,origin_city,radius_km,created_at FROM watches ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

def add_watch(name,query="",event_type="",category="",origin_city="",radius_km=None):
    init_db()
    with connect() as conn:
        conn.execute(
            "INSERT INTO watches(name,query,event_type,category,origin_city,radius_km,created_at) VALUES(?,?,?,?,?,?,?)",
            (name,query,event_type,category,origin_city,radius_km,datetime.now(timezone.utc).isoformat())
        )
        conn.commit()

def delete_watch(watch_id):
    init_db()
    with connect() as conn:
        conn.execute("DELETE FROM watches WHERE id=?",(watch_id,))
        conn.commit()


def record_event_sightings(event_ids):
    """Persist when canonical event IDs were first/last seen by Upplevio.

    This is global ingestion metadata, not user-specific visit history.
    """
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    clean_ids = [str(x) for x in dict.fromkeys(event_ids) if x]
    if not clean_ids:
        return
    with connect() as conn:
        for event_id in clean_ids:
            conn.execute(
                """
                INSERT INTO event_seen(event_id, first_seen_at, last_seen_at)
                VALUES(?,?,?)
                ON CONFLICT(event_id) DO UPDATE SET last_seen_at=excluded.last_seen_at
                """,
                (event_id, now, now),
            )
        conn.commit()

def event_first_seen_map():
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT event_id, first_seen_at FROM event_seen").fetchall()
    return {row["event_id"]: row["first_seen_at"] for row in rows}
