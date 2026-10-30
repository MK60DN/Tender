# -*- coding: utf-8 -*-
"""Identity, object-level authorization and guardian consent baseline.

This is a development identity envelope that closes anonymous access and binds
market actions to an actor. Production must replace it with authenticated
sessions/OIDC and server-side guardian relationships.
"""
from __future__ import annotations
import contextvars, json, sqlite3, pathlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS guardian_consents (
            consent_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL,
            guardian_id TEXT NOT NULL,
            status TEXT NOT NULL,
            scopes_json TEXT NOT NULL,
            granted_at TEXT,
            revoked_at TEXT,
            updated_at TEXT NOT NULL,
            UNIQUE(learner_id, guardian_id)
        )
        """)
        cols = {r[1] for r in c.execute("PRAGMA table_info(guardian_consents)").fetchall()}
        for name, ddl in {
            "verification_status": "ALTER TABLE guardian_consents ADD COLUMN verification_status TEXT DEFAULT 'pending'",
            "evidence": "ALTER TABLE guardian_consents ADD COLUMN evidence TEXT",
            "verified_by": "ALTER TABLE guardian_consents ADD COLUMN verified_by TEXT",
            "verified_at": "ALTER TABLE guardian_consents ADD COLUMN verified_at TEXT",
        }.items():
            if name not in cols:
                c.execute(ddl)
        c.execute("CREATE INDEX IF NOT EXISTS idx_guardian_consent_learner ON guardian_consents(learner_id,status)")


CURRENT_PRINCIPAL: contextvars.ContextVar[Principal | None] = contextvars.ContextVar("tender_principal", default=None)


@dataclass(frozen=True)
class Principal:
    actor_id: str
    role: str
    learner_id: str | None = None
    tenant_id: str | None = None


def principal_from_headers(actor: str | None, role: str | None, learner_id: str | None, tenant_id: str | None = None) -> Principal | None:
    actor = (actor or "").strip()
    role = (role or "learner").strip().lower()
    if not actor:
        return None
    if role not in {"learner", "parent", "admin", "auditor", "advisor"}:
        role = "learner"
    return Principal(actor_id=actor, role=role, learner_id=(learner_id or "").strip() or None, tenant_id=(tenant_id or "").strip() or None)


def grant_consent(learner_id: str, guardian_id: str, scopes: Iterable[str], verified_by: str = "system_demo", evidence: str = "demo_seed") -> dict:
    init_db()
    scopes = sorted({str(s) for s in scopes if s})
    if not learner_id or not guardian_id or not scopes:
        raise ValueError("learner_id, guardian_id and scopes are required")
    now = _now()
    consent_id = "consent_" + learner_id + "_" + guardian_id
    with _conn() as c:
        c.execute("""
        INSERT INTO guardian_consents(consent_id,learner_id,guardian_id,status,scopes_json,granted_at,revoked_at,updated_at,verification_status,evidence,verified_by,verified_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(learner_id,guardian_id) DO UPDATE SET
          status='active', scopes_json=excluded.scopes_json, granted_at=excluded.granted_at,
          revoked_at=NULL, updated_at=excluded.updated_at, verification_status='verified',
          evidence=excluded.evidence, verified_by=excluded.verified_by, verified_at=excluded.verified_at
        """, (consent_id, learner_id, guardian_id, "active", json.dumps(scopes, ensure_ascii=False), now, None, now, "verified", evidence, verified_by, now))
    return {"learner_id": learner_id, "guardian_id": guardian_id, "status": "active", "scopes": scopes, "granted_at": now}


def request_guardian_relation(learner_id: str, guardian_id: str, evidence: str = "") -> dict:
    init_db()
    if not learner_id or not guardian_id:
        raise ValueError("learner_id and guardian_id are required")
    now = _now()
    consent_id = "consent_" + learner_id + "_" + guardian_id
    with _conn() as c:
        c.execute("""
        INSERT INTO guardian_consents(consent_id,learner_id,guardian_id,status,scopes_json,granted_at,revoked_at,updated_at,verification_status,evidence,verified_by,verified_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(learner_id,guardian_id) DO UPDATE SET
          status='pending_verification', verification_status='pending', evidence=excluded.evidence,
          revoked_at=NULL, updated_at=excluded.updated_at
        """, (consent_id, learner_id, guardian_id, "pending_verification", "[]", None, None, now, "pending", evidence, None, None))
    return {"learner_id": learner_id, "guardian_id": guardian_id, "status": "pending_verification", "verification_status": "pending"}


def verify_guardian_relation(learner_id: str, guardian_id: str, admin_id: str, scopes: Iterable[str] | None = None) -> dict:
    init_db()
    scopes = sorted({str(s) for s in (scopes or ["learning_support", "family_summary"]) if s})
    now = _now()
    with _conn() as c:
        row = c.execute("SELECT * FROM guardian_consents WHERE learner_id=? AND guardian_id=?", (learner_id, guardian_id)).fetchone()
        if not row:
            raise KeyError("guardian request not found")
        c.execute("""UPDATE guardian_consents SET status='active', verification_status='verified', scopes_json=?,
                     granted_at=?, verified_by=?, verified_at=?, updated_at=? WHERE learner_id=? AND guardian_id=?""",
                  (json.dumps(scopes, ensure_ascii=False), now, admin_id, now, now, learner_id, guardian_id))
    return {"learner_id": learner_id, "guardian_id": guardian_id, "status": "active", "verification_status": "verified", "verified_by": admin_id, "scopes": scopes}


def list_guardian_requests() -> list[dict]:
    init_db()
    with _conn() as c:
        rows = c.execute("SELECT * FROM guardian_consents ORDER BY updated_at DESC").fetchall()
    out = []
    for row in rows:
        d = dict(row); d["scopes"] = json.loads(d.pop("scopes_json") or "[]"); out.append(d)
    return out


def revoke_consent(learner_id: str, guardian_id: str) -> dict:
    init_db()
    now = _now()
    with _conn() as c:
        row = c.execute("SELECT * FROM guardian_consents WHERE learner_id=? AND guardian_id=?", (learner_id, guardian_id)).fetchone()
        if not row:
            raise KeyError("consent not found")
        c.execute("UPDATE guardian_consents SET status='revoked', verification_status='revoked', revoked_at=?, updated_at=? WHERE learner_id=? AND guardian_id=?",
                  (now, now, learner_id, guardian_id))
    return {"learner_id": learner_id, "guardian_id": guardian_id, "status": "revoked", "revoked_at": now}


def get_consent(learner_id: str, guardian_id: str | None = None) -> dict | None:
    init_db()
    with _conn() as c:
        if guardian_id:
            row = c.execute("SELECT * FROM guardian_consents WHERE learner_id=? AND guardian_id=?", (learner_id, guardian_id)).fetchone()
        else:
            row = c.execute("SELECT * FROM guardian_consents WHERE learner_id=? ORDER BY updated_at DESC LIMIT 1", (learner_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["scopes"] = json.loads(d.pop("scopes_json") or "[]")
    return d


def seed_demo_consents(learner_ids: Iterable[str]) -> None:
    init_db()
    for learner_id in learner_ids:
        existing = get_consent(learner_id, "P-" + learner_id)
        if not existing or existing.get("status") != "active" or existing.get("verification_status") not in {"verified", "demo_verified"}:
            grant_consent(learner_id, "P-" + learner_id, ["learning_support", "family_summary", "readiness"])


def authorize_learner(principal: Principal | None, learner_id: str) -> tuple[bool, str]:
    if principal is None:
        return False, "identity_required"
    if principal.role in {"admin", "auditor"}:
        return True, "admin"
    if principal.role == "learner":
        return (principal.actor_id == learner_id, "self" if principal.actor_id == learner_id else "cross_learner_denied")
    if principal.role == "parent":
        consent = get_consent(learner_id, principal.actor_id)
        if consent and consent.get("status") == "active" and consent.get("verification_status") in {"verified", "demo_verified"}:
            return True, "guardian_consent"
        return False, "guardian_consent_required"
    if principal.role == "advisor":
        return (principal.learner_id == learner_id, "assigned_advisor" if principal.learner_id == learner_id else "advisor_assignment_required")
    return False, "role_not_allowed"


def set_current_principal(principal: Principal | None):
    return CURRENT_PRINCIPAL.set(principal)


def reset_current_principal(token) -> None:
    CURRENT_PRINCIPAL.reset(token)


def get_current_principal() -> Principal | None:
    return CURRENT_PRINCIPAL.get()
