# -*- coding: utf-8 -*-
"""Signed development sessions for Tender.

This is a small HMAC session layer, not a replacement for production OIDC.
It prevents trivial identity spoofing through client-supplied actor headers.
"""
from __future__ import annotations
import base64, hashlib, hmac, json, os, pathlib, secrets, sqlite3, time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
SECRET_FILE = ROOT / ".tender_session_secret"
DB = ROOT / "tender_agent.db"


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _secret() -> bytes:
    env = os.getenv("TENDER_SESSION_SECRET")
    if env:
        return env.encode("utf-8")
    if SECRET_FILE.exists():
        return SECRET_FILE.read_bytes()
    value = secrets.token_bytes(32)
    SECRET_FILE.write_bytes(value)
    try:
        os.chmod(SECRET_FILE, 0o600)
    except OSError:
        pass
    return value


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS auth_sessions (
            jti TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            role TEXT NOT NULL,
            learner_id TEXT,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            revoked_at INTEGER,
            replaced_by TEXT
        )
        """)
        cols = {r[1] for r in c.execute("PRAGMA table_info(auth_sessions)").fetchall()}
        if "tenant_id" not in cols:
            c.execute("ALTER TABLE auth_sessions ADD COLUMN tenant_id TEXT")
        c.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_actor ON auth_sessions(actor_id, revoked_at, expires_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_auth_sessions_tenant ON auth_sessions(tenant_id, actor_id)")


def create_session(actor_id: str, role: str, learner_id: str | None = None, ttl_seconds: int = 3600, tenant_id: str | None = None) -> dict:
    init_db()
    now = int(time.time())
    jti = "sess_" + secrets.token_urlsafe(18)
    payload = {
        "sub": actor_id,
        "role": role,
        "learner_id": learner_id,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + max(60, min(int(ttl_seconds), 86400)),
        "jti": jti,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body = _b64e(raw)
    signature = _b64e(hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest())
    with _conn() as c:
        c.execute("INSERT INTO auth_sessions(jti,actor_id,role,learner_id,tenant_id,created_at,expires_at) VALUES(?,?,?,?,?,?,?)",
                  (jti, actor_id, role, learner_id, tenant_id, now, payload["exp"]))
    return {"token": body + "." + signature, "token_type": "Bearer", "expires_in": payload["exp"] - now, "payload": payload}


def verify_session(token: str) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    body, signature = token.rsplit(".", 1)
    expected = _b64e(hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload = json.loads(_b64d(body).decode("utf-8"))
    except Exception:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM auth_sessions WHERE jti=?", (payload.get("jti"),)).fetchone()
    if not row or row["revoked_at"] is not None or int(row["expires_at"]) < int(time.time()):
        return None
    return payload


def revoke_session(jti: str, replaced_by: str | None = None) -> bool:
    init_db()
    with _conn() as c:
        cur = c.execute("UPDATE auth_sessions SET revoked_at=?, replaced_by=? WHERE jti=? AND revoked_at IS NULL",
                        (int(time.time()), replaced_by, jti))
    return cur.rowcount > 0


def revoke_actor_sessions(actor_id: str) -> int:
    init_db()
    with _conn() as c:
        cur = c.execute("UPDATE auth_sessions SET revoked_at=? WHERE actor_id=? AND revoked_at IS NULL",
                        (int(time.time()), actor_id))
    return cur.rowcount


def list_sessions(actor_id: str, include_revoked: bool = False) -> list[dict]:
    init_db()
    sql = "SELECT jti,actor_id,role,learner_id,tenant_id,created_at,expires_at,revoked_at,replaced_by FROM auth_sessions WHERE actor_id=?"
    if not include_revoked:
        sql += " AND revoked_at IS NULL AND expires_at>=?"
    args = (actor_id, int(time.time())) if not include_revoked else (actor_id,)
    with _conn() as c:
        return [dict(r) for r in c.execute(sql, args).fetchall()]
