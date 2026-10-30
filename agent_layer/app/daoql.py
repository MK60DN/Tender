"""DAOQL 因果层：事件、因果关系、证据、审计。"""
from __future__ import annotations
import hashlib, json, sqlite3, uuid, pathlib
from datetime import datetime, timezone
from collections import deque

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
        c.execute("""
        CREATE TABLE IF NOT EXISTS causal_edges (
            edge_id TEXT PRIMARY KEY,
            source_event_id TEXT NOT NULL,
            target_event_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            evidence TEXT,
            created_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            payload TEXT,
            created_at TEXT NOT NULL
        )
        """)
        cols = {r[1] for r in c.execute("PRAGMA table_info(audit_log)").fetchall()}
        if "prev_hash" not in cols:
            c.execute("ALTER TABLE audit_log ADD COLUMN prev_hash TEXT")
        if "record_hash" not in cols:
            c.execute("ALTER TABLE audit_log ADD COLUMN record_hash TEXT")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_student ON events(student_id, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON causal_edges(source_event_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON causal_edges(target_event_id)")


def _now():
    return datetime.now(timezone.utc).astimezone().isoformat()


def insert_event(event: dict) -> str:
    init_db()
    eid = event.get("event_id") or "evt_" + uuid.uuid4().hex[:12]
    ts = event.get("timestamp") or _now()
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO events(event_id,event_type,student_id,session_id,timestamp,payload,source,provenance) VALUES(?,?,?,?,?,?,?,?)",
            (eid, event["event_type"], event["student_id"], event.get("session_id"), ts,
             json.dumps(event.get("payload", {}), ensure_ascii=False),
             event.get("source", "unknown"),
             json.dumps(event.get("provenance", {}), ensure_ascii=False)),
        )
    try:
        from .metameta_cartographer import maybe_decompose_event
        maybe_decompose_event(eid, event)
    except Exception:
        pass
    return eid


def insert_edge(source_event_id: str, target_event_id: str, relation: str = "causes",
                confidence: float = 0.5, evidence: dict | None = None) -> str:
    init_db()
    eid = "edge_" + uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute(
            "INSERT INTO causal_edges(edge_id,source_event_id,target_event_id,relation,confidence,evidence,created_at) VALUES(?,?,?,?,?,?,?)",
            (eid, source_event_id, target_event_id, relation, float(confidence),
             json.dumps(evidence or {}, ensure_ascii=False), _now()),
        )
    return eid


def list_events(student_id: str):
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM events WHERE student_id=? ORDER BY timestamp", (student_id,)).fetchall()
    return [_decode_event(r) for r in rows]


def all_events():
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM events ORDER BY timestamp").fetchall()
    return [_decode_event(r) for r in rows]


def _decode_event(r):
    d = dict(r)
    d["payload"] = json.loads(d["payload"] or "{}")
    d["provenance"] = json.loads(d["provenance"] or "{}")
    return d


def list_edges():
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM causal_edges ORDER BY created_at").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["evidence"] = json.loads(d["evidence"] or "{}")
        out.append(d)
    return out


def causal_path(source_event_id: str, target_event_id: str, max_depth: int = 6):
    edges = list_edges()
    graph = {}
    for e in edges:
        graph.setdefault(e["source_event_id"], []).append(e)
    q = deque([(source_event_id, [source_event_id], [])])
    seen = {source_event_id}
    while q:
        node, path, epath = q.popleft()
        if len(epath) >= max_depth:
            continue
        for e in graph.get(node, []):
            nxt = e["target_event_id"]
            if nxt in seen:
                continue
            if nxt == target_event_id:
                return {"found": True, "path": path + [nxt], "edges": epath + [e]}
            seen.add(nxt)
            q.append((nxt, path + [nxt], epath + [e]))
    return {"found": False, "path": [], "edges": []}


def event_graph(student_id: str | None = None):
    import networkx as nx
    init_db()
    G = nx.DiGraph()
    events = all_events()
    if student_id:
        events = [e for e in events if e["student_id"] == student_id]
    ids = {e["event_id"] for e in events}
    for e in events:
        G.add_node(e["event_id"], event_type=e["event_type"], student_id=e["student_id"], timestamp=e["timestamp"])
    for e in list_edges():
        if e["source_event_id"] in ids and e["target_event_id"] in ids:
            G.add_edge(e["source_event_id"], e["target_event_id"], relation=e["relation"], confidence=e["confidence"])
    return {
        "nodes": [{"id": n, **G.nodes[n]} for n in G.nodes()],
        "edges": [{"source": u, "target": v, **G.edges[u, v]} for u, v in G.edges()],
    }


def _audit_material(prev_hash: str, actor: str, action: str, target: str, payload_json: str, created_at: str) -> str:
    return "\n".join([prev_hash or "", actor or "", action or "", target or "", payload_json, created_at])


def write_audit(actor: str, action: str, target: str = "", payload: dict | None = None) -> str:
    init_db()
    aid = "audit_" + uuid.uuid4().hex[:12]
    created_at = _now()
    payload_json = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
    c = _conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        last = c.execute("SELECT record_hash FROM audit_log ORDER BY rowid DESC LIMIT 1").fetchone()
        prev_hash = (last[0] if last and last[0] else "")
        record_hash = hashlib.sha256(_audit_material(prev_hash, actor, action, target, payload_json, created_at).encode("utf-8")).hexdigest()
        c.execute("INSERT INTO audit_log(audit_id,actor,action,target,payload,created_at,prev_hash,record_hash) VALUES(?,?,?,?,?,?,?,?)",
                  (aid, actor, action, target, payload_json, created_at, prev_hash, record_hash))
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
    return aid


def verify_audit_chain(limit: int = 10000) -> dict:
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM audit_log ORDER BY rowid ASC LIMIT ?", (int(limit),)).fetchall()
    prev_hash = ""
    checked = 0
    legacy = 0
    for r in rows:
        d = dict(r)
        record_hash = d.get("record_hash")
        if not record_hash:
            legacy += 1
            continue
        expected_prev = d.get("prev_hash") or ""
        if expected_prev != prev_hash:
            return {"valid": False, "checked": checked, "legacy_records": legacy,
                    "failure": "prev_hash_mismatch", "audit_id": d.get("audit_id")}
        expected = hashlib.sha256(_audit_material(
            prev_hash, d.get("actor", ""), d.get("action", ""), d.get("target", ""),
            d.get("payload", "{}"), d.get("created_at", "")
        ).encode("utf-8")).hexdigest()
        if expected != record_hash:
            return {"valid": False, "checked": checked, "legacy_records": legacy,
                    "failure": "record_hash_mismatch", "audit_id": d.get("audit_id")}
        prev_hash = record_hash
        checked += 1
    return {"valid": True, "checked": checked, "legacy_records": legacy, "head": prev_hash}


def list_audit(limit: int = 100):
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (int(limit),)).fetchall()
    out = []
    for r in rows:
        d = dict(r); d["payload"] = json.loads(d["payload"] or "{}"); out.append(d)
    return out


def count_events():
    init_db()
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM events").fetchone()[0]


def rebuild_audit_chain() -> dict:
    """One-time migration for databases created before hash-chain support."""
    init_db()
    prev_hash = ""
    updated = 0
    c = _conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        rows = c.execute("SELECT rowid,actor,action,target,payload,created_at FROM audit_log ORDER BY rowid ASC").fetchall()
        for r in rows:
            actor, action, target, payload_json, created_at = r[1], r[2], r[3] or "", r[4] or "{}", r[5]
            record_hash = hashlib.sha256(_audit_material(prev_hash, actor, action, target, payload_json, created_at).encode("utf-8")).hexdigest()
            c.execute("UPDATE audit_log SET prev_hash=?, record_hash=? WHERE rowid=?", (prev_hash, record_hash, r[0]))
            prev_hash = record_hash
            updated += 1
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
    return {"updated": updated, "head": prev_hash}
