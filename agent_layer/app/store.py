"""DAOQL 最小事件存储：SQLite 版。"""
from __future__ import annotations
import json, sqlite3, pathlib, uuid
from datetime import datetime, timezone

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            student_id TEXT NOT NULL,
            session_id TEXT,
            timestamp TEXT NOT NULL,
            payload TEXT NOT NULL,
            source TEXT NOT NULL,
            provenance TEXT
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_student ON events(student_id, timestamp)")


def insert_event(event: dict) -> str:
    init_db()
    eid = event.get("event_id") or "evt_" + uuid.uuid4().hex[:12]
    ts = event.get("timestamp") or datetime.now(timezone.utc).astimezone().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO events(event_id,event_type,student_id,session_id,timestamp,payload,source,provenance) VALUES(?,?,?,?,?,?,?,?)",
            (
                eid,
                event["event_type"],
                event["student_id"],
                event.get("session_id"),
                ts,
                json.dumps(event.get("payload", {}), ensure_ascii=False),
                event.get("source", "unknown"),
                json.dumps(event.get("provenance", {}), ensure_ascii=False),
            ),
        )
    return eid


def list_events(student_id: str):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM events WHERE student_id=? ORDER BY timestamp",
            (student_id,),
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"] or "{}")
        d["provenance"] = json.loads(d["provenance"] or "{}")
        out.append(d)
    return out


def all_events():
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM events ORDER BY timestamp").fetchall()
    return [dict(r) for r in rows]


def count_events():
    init_db()
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
