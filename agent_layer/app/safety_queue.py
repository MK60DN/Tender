# -*- coding: utf-8 -*-
"""Human safety review queue for high-risk signals."""
from __future__ import annotations
import json, sqlite3, pathlib, uuid
from datetime import datetime, timezone
from .daoql import write_audit

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"
VALID_STATUS = {"open", "reviewing", "escalated", "closed"}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS safety_review_tickets (
            ticket_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            source_agent TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            reason TEXT NOT NULL,
            evidence_refs_json TEXT NOT NULL,
            message_hash TEXT,
            status TEXT NOT NULL,
            assignee TEXT,
            resolution TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_safety_tickets_status ON safety_review_tickets(status,created_at)")


def create_ticket(student_id: str, source_agent: str, risk_level: str, reason: str,
                  evidence_refs: list[str] | None = None, message_hash: str | None = None) -> dict:
    init_db()
    with _conn() as c:
        existing = c.execute("""SELECT * FROM safety_review_tickets
            WHERE student_id=? AND source_agent=? AND message_hash=? AND status IN ('open','reviewing','escalated')
            ORDER BY created_at DESC LIMIT 1""", (student_id, source_agent, message_hash)).fetchone()
        if existing:
            return _decode(existing)
        tid = "safety_" + uuid.uuid4().hex[:12]
        now = _now()
        c.execute("""INSERT INTO safety_review_tickets(ticket_id,student_id,source_agent,risk_level,reason,evidence_refs_json,message_hash,status,assignee,resolution,created_at,updated_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (tid, student_id, source_agent, risk_level, reason, json.dumps(evidence_refs or [], ensure_ascii=False),
                   message_hash, "open", None, None, now, now))
    ticket = get_ticket(tid)
    write_audit("safety_queue", "safety.ticket.create", tid,
                {"student_id": student_id, "source_agent": source_agent, "risk_level": risk_level})
    return ticket


def _decode(row) -> dict:
    d = dict(row)
    d["evidence_refs"] = json.loads(d.pop("evidence_refs_json") or "[]")
    return d


def get_ticket(ticket_id: str) -> dict:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM safety_review_tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
    if not row:
        raise KeyError("safety ticket not found")
    return _decode(row)


def list_tickets(status: str | None = None, limit: int = 100) -> list[dict]:
    init_db()
    sql = "SELECT * FROM safety_review_tickets"
    args = []
    if status:
        sql += " WHERE status=?"
        args.append(status)
    sql += " ORDER BY created_at DESC LIMIT ?"
    args.append(int(limit))
    with _conn() as c:
        return [_decode(r) for r in c.execute(sql, args).fetchall()]


def update_ticket(ticket_id: str, status: str, actor: str, assignee: str | None = None,
                  resolution: str | None = None) -> dict:
    init_db()
    if status not in VALID_STATUS:
        raise ValueError("invalid status")
    with _conn() as c:
        row = c.execute("SELECT * FROM safety_review_tickets WHERE ticket_id=?", (ticket_id,)).fetchone()
        if not row:
            raise KeyError("safety ticket not found")
        c.execute("""UPDATE safety_review_tickets SET status=?, assignee=COALESCE(?,assignee),
                     resolution=COALESCE(?,resolution), updated_at=? WHERE ticket_id=?""",
                  (status, assignee, resolution, _now(), ticket_id))
    result = get_ticket(ticket_id)
    write_audit(actor, "safety.ticket.update", ticket_id,
                {"status": status, "assignee": assignee, "resolution": resolution})
    return result
