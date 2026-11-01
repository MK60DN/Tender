"""Group-chat backend with private/group/shared data boundaries."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import pathlib
import sqlite3
import uuid
from typing import Any, Iterable

from .daoql import write_audit

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"
GROUP_ROLES = {"owner", "facilitator", "member", "observer"}
GROUP_STATUSES = {"active", "paused", "closed", "archived"}
EVENT_VISIBILITIES = {"group_public", "system"}
SHARED_BRANCH_CATEGORIES = {"fact", "goal", "task", "commitment", "boundary", "outcome", "summary"}
ALLOWED_VIEW_SCOPES = {"role_task", "availability", "communication_preference", "commitment", "time_limited_state_summary"}
FORBIDDEN_VIEW_SCOPES = {"raw_text", "raw_dialogue", "private_events", "full_life_tree", "diagnosis", "personality"}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _id(prefix: str) -> str:
    return prefix + "_" + uuid.uuid4().hex[:12]


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def _json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


def init_db() -> None:
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS group_sessions (
            group_id TEXT PRIMARY KEY, platform TEXT NOT NULL, purpose TEXT NOT NULL,
            tenant_id TEXT, status TEXT NOT NULL, created_by TEXT NOT NULL,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS group_memberships (
            group_id TEXT NOT NULL, actor_id TEXT NOT NULL, role TEXT NOT NULL,
            consent_scopes_json TEXT NOT NULL, status TEXT NOT NULL, joined_at TEXT NOT NULL,
            revoked_at TEXT, PRIMARY KEY(group_id, actor_id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS group_events (
            event_id TEXT PRIMARY KEY, group_id TEXT NOT NULL, actor_id TEXT NOT NULL,
            event_type TEXT NOT NULL, visibility TEXT NOT NULL, payload_json TEXT NOT NULL,
            source TEXT NOT NULL, consent_ref TEXT, created_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS peer_view_grants (
            grant_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, viewer_id TEXT NOT NULL,
            group_id TEXT NOT NULL, purpose TEXT NOT NULL, scopes_json TEXT NOT NULL,
            evidence_refs_json TEXT NOT NULL, status TEXT NOT NULL, valid_from TEXT NOT NULL,
            valid_until TEXT NOT NULL, revoked_at TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS peer_models (
            model_id TEXT PRIMARY KEY, observer_id TEXT NOT NULL, subject_id TEXT NOT NULL,
            group_id TEXT NOT NULL, scope_snapshot_json TEXT NOT NULL, evidence_refs_json TEXT NOT NULL,
            model_json TEXT NOT NULL, confidence REAL NOT NULL, status TEXT NOT NULL,
            expires_at TEXT, updated_at TEXT NOT NULL, UNIQUE(observer_id, subject_id, group_id)
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS shared_branches (
            branch_id TEXT PRIMARY KEY, group_id TEXT NOT NULL, category TEXT NOT NULL,
            content_json TEXT NOT NULL, participants_json TEXT NOT NULL, evidence_refs_json TEXT NOT NULL,
            approvals_json TEXT NOT NULL, proposed_by TEXT NOT NULL, visibility TEXT NOT NULL DEFAULT 'bilateral',
            status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS group_model_snapshots (
            snapshot_id TEXT PRIMARY KEY, group_id TEXT NOT NULL, model_json TEXT NOT NULL,
            evidence_refs_json TEXT NOT NULL, confidence REAL NOT NULL, created_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS group_outcomes (
            outcome_id TEXT PRIMARY KEY, group_id TEXT NOT NULL, decision TEXT NOT NULL,
            commitments_json TEXT NOT NULL, unresolved_json TEXT NOT NULL,
            evidence_refs_json TEXT NOT NULL, recorded_by TEXT NOT NULL, created_at TEXT NOT NULL
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_group_members_actor ON group_memberships(actor_id, status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_group_events_group ON group_events(group_id, created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_peer_grants_pair ON peer_view_grants(owner_id, viewer_id, group_id, status)")
        branch_cols = {row[1] for row in c.execute("PRAGMA table_info(shared_branches)").fetchall()}
        if "visibility" not in branch_cols:
            c.execute("ALTER TABLE shared_branches ADD COLUMN visibility TEXT NOT NULL DEFAULT 'bilateral'")
        c.execute("CREATE INDEX IF NOT EXISTS idx_shared_branches_group ON shared_branches(group_id, status, updated_at)")


def _member_row(group_id: str, actor_id: str):
    with _conn() as c:
        return c.execute("SELECT * FROM group_memberships WHERE group_id=? AND actor_id=? AND status='active'", (group_id, actor_id)).fetchone()


def _require_member(group_id: str, actor_id: str) -> dict:
    init_db()
    row = _member_row(group_id, actor_id)
    if not row:
        raise PermissionError("group_membership_required")
    return dict(row)


def _active_grants(owner_id: str, viewer_id: str, group_id: str) -> list[dict]:
    init_db()
    now_dt = datetime.now(timezone.utc)
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM peer_view_grants WHERE owner_id=? AND viewer_id=? AND group_id=? AND status='active' ORDER BY valid_until ASC",
            (owner_id, viewer_id, group_id),
        ).fetchall()
    out = []
    for row in rows:
        try:
            valid_until = datetime.fromisoformat(row["valid_until"]).astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
        if valid_until < now_dt:
            continue
        item = dict(row)
        item["scopes"] = json.loads(item.pop("scopes_json") or "[]")
        item["evidence_refs"] = json.loads(item.pop("evidence_refs_json") or "[]")
        out.append(item)
    return out


def create_group_session(platform: str, purpose: str, created_by: str, tenant_id: str | None = None) -> dict:
    init_db()
    if not platform.strip() or not purpose.strip() or not created_by.strip():
        raise ValueError("platform, purpose and created_by are required")
    group_id = _id("group")
    now = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO group_sessions(group_id,platform,purpose,tenant_id,status,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            (group_id, platform.strip(), purpose.strip(), tenant_id, "active", created_by, now, now),
        )
        c.execute(
            "INSERT INTO group_memberships(group_id,actor_id,role,consent_scopes_json,status,joined_at,revoked_at) VALUES(?,?,?,?,?,?,NULL)",
            (group_id, created_by, "owner", _json(["session.manage", "group_public.read"]), "active", now),
        )
    write_audit(created_by, "group.session.create", group_id, {"platform": platform, "purpose": purpose})
    return get_group_session(group_id, created_by)


def join_group_session(group_id: str, actor_id: str, role: str = "member", consent_scopes: Iterable[str] | None = None) -> dict:
    init_db()
    role = role if role in {"member", "observer"} else "member"
    scopes = sorted({str(scope) for scope in (consent_scopes or ["group_public.read"]) if scope})
    if "group_public.read" not in scopes:
        scopes.append("group_public.read")
    now = _now()
    with _conn() as c:
        session = c.execute("SELECT * FROM group_sessions WHERE group_id=?", (group_id,)).fetchone()
        if not session:
            raise KeyError("group_session_not_found")
        if session["status"] != "active":
            raise ValueError("group_session_not_active")
        c.execute(
            "INSERT INTO group_memberships(group_id,actor_id,role,consent_scopes_json,status,joined_at,revoked_at) VALUES(?,?,?,?,?,?,NULL) "
            "ON CONFLICT(group_id,actor_id) DO UPDATE SET role=excluded.role, consent_scopes_json=excluded.consent_scopes_json, status='active', revoked_at=NULL",
            (group_id, actor_id, role, _json(scopes), "active", now),
        )
        c.execute("UPDATE group_sessions SET updated_at=? WHERE group_id=?", (now, group_id))
    write_audit(actor_id, "group.session.join", group_id, {"role": role, "scopes": scopes})
    return {"group_id": group_id, "actor_id": actor_id, "role": role, "consent_scopes": scopes, "status": "active"}


def get_group_session(group_id: str, actor_id: str) -> dict:
    _require_member(group_id, actor_id)
    with _conn() as c:
        session = c.execute("SELECT * FROM group_sessions WHERE group_id=?", (group_id,)).fetchone()
        members = c.execute("SELECT actor_id,role,consent_scopes_json,status,joined_at,revoked_at FROM group_memberships WHERE group_id=? ORDER BY joined_at", (group_id,)).fetchall()
    if not session:
        raise KeyError("group_session_not_found")
    result = dict(session)
    result["members"] = []
    your_scopes: list[str] = []
    for row in members:
        member = dict(row)
        scopes = json.loads(member.pop("consent_scopes_json") or "[]")
        if member["actor_id"] == actor_id:
            your_scopes = scopes
            member["consent_scopes"] = scopes
        else:
            member["consent_scopes_visible"] = False
        result["members"].append(member)
    result["your_consent_scopes"] = your_scopes
    result["member_count"] = sum(1 for member in result["members"] if member["status"] == "active")
    result["boundary"] = "Group membership does not grant access to any member's private Tender model."
    return result


def list_group_sessions(actor_id: str) -> list[dict]:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT s.*, m.role, m.consent_scopes_json FROM group_sessions s JOIN group_memberships m ON m.group_id=s.group_id WHERE m.actor_id=? AND m.status='active' ORDER BY s.updated_at DESC",
            (actor_id,),
        ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["consent_scopes"] = json.loads(item.pop("consent_scopes_json") or "[]")
        out.append(item)
    return out


def ingest_group_event(group_id: str, actor_id: str, event_type: str, content: str = "", visibility: str = "group_public", consent_ref: str | None = None, payload: dict | None = None) -> dict:
    _require_member(group_id, actor_id)
    visibility = visibility if visibility in EVENT_VISIBILITIES else "group_public"
    event_id = _id("gevent")
    body = dict(payload or {})
    body["content"] = str(content or "")[:4000]
    with _conn() as c:
        c.execute(
            "INSERT INTO group_events(event_id,group_id,actor_id,event_type,visibility,payload_json,source,consent_ref,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (event_id, group_id, actor_id, event_type.strip() or "message", visibility, _json(body), "group_chat", consent_ref, _now()),
        )
    write_audit(actor_id, "group.event.ingest", group_id, {"event_id": event_id, "event_type": event_type, "visibility": visibility})
    return {"event_id": event_id, "group_id": group_id, "actor_id": actor_id, "event_type": event_type, "visibility": visibility, "status": "recorded"}


def list_group_events(group_id: str, actor_id: str, limit: int = 100) -> list[dict]:
    _require_member(group_id, actor_id)
    with _conn() as c:
        rows = c.execute("SELECT * FROM group_events WHERE group_id=? AND visibility IN ('group_public','system') ORDER BY created_at DESC LIMIT ?", (group_id, max(1, min(int(limit), 500)))).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json") or "{}")
        out.append(item)
    return out


def create_peer_view_grant(owner_id: str, viewer_id: str, group_id: str, purpose: str, scopes: Iterable[str], evidence_refs: Iterable[str] | None = None, valid_hours: int = 24) -> dict:
    if owner_id == viewer_id:
        raise ValueError("peer_view_requires_two_members")
    _require_member(group_id, owner_id)
    _require_member(group_id, viewer_id)
    selected = sorted({str(scope) for scope in scopes if scope})
    forbidden = sorted(set(selected) & FORBIDDEN_VIEW_SCOPES)
    if forbidden:
        raise ValueError("forbidden_peer_view_scopes:" + ",".join(forbidden))
    unknown = sorted(set(selected) - ALLOWED_VIEW_SCOPES)
    if unknown or not selected:
        raise ValueError("invalid_peer_view_scopes:" + ",".join(unknown or ["none"]))
    now_dt = datetime.now(timezone.utc)
    valid_from = now_dt.isoformat()
    valid_until = (now_dt + timedelta(hours=max(1, min(int(valid_hours), 24 * 30)))).isoformat()
    grant_id = _id("pvgrant")
    with _conn() as c:
        c.execute(
            "INSERT INTO peer_view_grants(grant_id,owner_id,viewer_id,group_id,purpose,scopes_json,evidence_refs_json,status,valid_from,valid_until,revoked_at) VALUES(?,?,?,?,?,?,?,?,?,?,NULL)",
            (grant_id, owner_id, viewer_id, group_id, purpose.strip() or "collaboration", _json(selected), _json(list(evidence_refs or [])), "active", valid_from, valid_until),
        )
    write_audit(owner_id, "peer.view.grant", grant_id, {"viewer_id": viewer_id, "group_id": group_id, "scopes": selected, "valid_until": valid_until})
    return {"grant_id": grant_id, "owner_id": owner_id, "viewer_id": viewer_id, "group_id": group_id, "scopes": selected, "status": "active", "valid_until": valid_until}


def list_peer_view_grants(owner_id: str, group_id: str | None = None) -> list[dict]:
    init_db()
    sql = "SELECT * FROM peer_view_grants WHERE owner_id=?"
    args: list[Any] = [owner_id]
    if group_id:
        sql += " AND group_id=?"
        args.append(group_id)
    sql += " ORDER BY valid_until DESC"
    with _conn() as c:
        rows = c.execute(sql, args).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["scopes"] = json.loads(item.pop("scopes_json") or "[]")
        item["evidence_refs"] = json.loads(item.pop("evidence_refs_json") or "[]")
        out.append(item)
    return out


def revoke_peer_view_grant(grant_id: str, owner_id: str) -> dict:
    init_db()
    now = _now()
    with _conn() as c:
        row = c.execute("SELECT * FROM peer_view_grants WHERE grant_id=?", (grant_id,)).fetchone()
        if not row:
            raise KeyError("peer_view_grant_not_found")
        if row["owner_id"] != owner_id:
            raise PermissionError("peer_view_owner_required")
        c.execute("UPDATE peer_view_grants SET status='revoked', revoked_at=? WHERE grant_id=?", (now, grant_id))
        c.execute(
            "UPDATE peer_models SET status='expired', updated_at=? WHERE observer_id=? AND subject_id=? AND group_id=?",
            (now, row["viewer_id"], row["owner_id"], row["group_id"]),
        )
    write_audit(owner_id, "peer.view.revoke", grant_id, {"viewer_id": row["viewer_id"], "group_id": row["group_id"]})
    return {"grant_id": grant_id, "status": "revoked", "revoked_at": now, "derived_peer_models_expired": True}


def build_peer_model(observer_id: str, subject_id: str, group_id: str) -> dict:
    if observer_id == subject_id:
        raise ValueError("use_self_model_for_self")
    _require_member(group_id, observer_id)
    _require_member(group_id, subject_id)
    grants = _active_grants(subject_id, observer_id, group_id)
    with _conn() as c:
        rows = c.execute(
            "SELECT event_id,event_type,created_at FROM group_events WHERE group_id=? AND actor_id=? AND visibility='group_public' ORDER BY created_at DESC LIMIT 50",
            (group_id, subject_id),
        ).fetchall()
    event_refs = [row["event_id"] for row in rows]
    event_types: dict[str, int] = {}
    for row in rows:
        event_types[row["event_type"]] = event_types.get(row["event_type"], 0) + 1
    authorized_scopes = sorted({scope for grant in grants for scope in grant["scopes"]})
    grant_refs = [grant["grant_id"] for grant in grants]
    evidence_refs = event_refs[:20] + grant_refs
    if not evidence_refs:
        status = "insufficient_evidence"
        confidence = 0.0
        hypotheses = ["没有足够的群公开互动或授权摘要，不能形成他者模型。"]
    else:
        confidence = min(0.85, 0.2 + 0.03 * len(rows) + (0.25 if grants else 0.0))
        status = "corroborated" if grants and len(rows) >= 3 else "provisional"
        hypotheses = ["只可讨论公开互动模式与授权范围内的协作信息。"]
        hypotheses.append("可参考对方明确授权的作用域，但不能外推为完整人格、情绪或诊断。" if grants else "未获得对方私密授权；任何关系判断都必须保留证据不足。")
    model = {
        "observer_id": observer_id,
        "subject_id": subject_id,
        "group_id": group_id,
        "model_type": "observer_owned_relationship_hypothesis",
        "subject_self_model_accessed": False,
        "authorization": {
            "status": "active" if grants else "none",
            "authorized_scopes": authorized_scopes,
            "grant_refs": grant_refs,
            "notice": "Shared views are scoped summaries, never the subject's private Tender state.",
        },
        "observable_evidence": {"public_event_count": len(rows), "public_event_types": event_types, "evidence_refs": event_refs[:20]},
        "hypotheses": hypotheses,
        "correction_required": True,
        "boundary": "This model belongs to the observer. It is not the subject's self-model and cannot infer private mental states.",
    }
    now = _now()
    expires_at = min((grant["valid_until"] for grant in grants), default=None)
    model_id = _id("pmodel")
    with _conn() as c:
        existing = c.execute("SELECT model_id FROM peer_models WHERE observer_id=? AND subject_id=? AND group_id=?", (observer_id, subject_id, group_id)).fetchone()
        if existing:
            model_id = existing["model_id"]
            c.execute(
                "UPDATE peer_models SET scope_snapshot_json=?, evidence_refs_json=?, model_json=?, confidence=?, status=?, expires_at=?, updated_at=? WHERE model_id=?",
                (_json(authorized_scopes), _json(evidence_refs), _json(model), confidence, status, expires_at, now, model_id),
            )
        else:
            c.execute(
                "INSERT INTO peer_models(model_id,observer_id,subject_id,group_id,scope_snapshot_json,evidence_refs_json,model_json,confidence,status,expires_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (model_id, observer_id, subject_id, group_id, _json(authorized_scopes), _json(evidence_refs), _json(model), confidence, status, expires_at, now),
            )
    write_audit(observer_id, "peer.model.build", model_id, {"subject_id": subject_id, "group_id": group_id, "confidence": confidence, "grant_count": len(grants)})
    return {"model_id": model_id, "confidence": round(confidence, 3), "status": status, **model, "expires_at": expires_at, "updated_at": now}


def create_shared_branch(group_id: str, actor_id: str, category: str, content: dict, participant_ids: Iterable[str], evidence_refs: Iterable[str] | None = None, visibility: str | None = None) -> dict:
    _require_member(group_id, actor_id)
    if category not in SHARED_BRANCH_CATEGORIES:
        raise ValueError("invalid_shared_branch_category")
    participants = sorted(set(str(item) for item in participant_ids if item))
    if actor_id not in participants:
        participants.append(actor_id)
    for participant in participants:
        _require_member(group_id, participant)
    session = get_group_session(group_id, actor_id)
    active_members = sorted(member["actor_id"] for member in session["members"] if member["status"] == "active")
    visibility = visibility or ("group" if set(participants) >= set(active_members) else "bilateral")
    if visibility not in {"bilateral", "group"}:
        raise ValueError("invalid_shared_branch_visibility")
    if visibility == "group" and set(participants) < set(active_members):
        raise ValueError("group_branch_requires_all_active_participants")
    now = _now()
    branch_id = _id("branch")
    approvals = [actor_id]
    status = "active" if set(approvals) >= set(participants) else "proposed"
    with _conn() as c:
        c.execute(
            "INSERT INTO shared_branches(branch_id,group_id,category,content_json,participants_json,evidence_refs_json,approvals_json,proposed_by,visibility,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (branch_id, group_id, category, _json(content), _json(participants), _json(list(evidence_refs or [])), _json(approvals), actor_id, visibility, status, now, now),
        )
    write_audit(actor_id, "shared_branch.create", branch_id, {"group_id": group_id, "category": category, "participants": participants, "visibility": visibility, "status": status})
    return {"branch_id": branch_id, "group_id": group_id, "category": category, "content": content, "participants": participants, "visibility": visibility, "approvals": approvals, "status": status}


def approve_shared_branch(branch_id: str, actor_id: str) -> dict:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM shared_branches WHERE branch_id=?", (branch_id,)).fetchone()
        if not row:
            raise KeyError("shared_branch_not_found")
        group_id = row["group_id"]
        participants = json.loads(row["participants_json"] or "[]")
        approvals = json.loads(row["approvals_json"] or "[]")
        if actor_id not in participants:
            raise PermissionError("shared_branch_participant_required")
        _require_member(group_id, actor_id)
        if actor_id not in approvals:
            approvals.append(actor_id)
        status = "active" if set(approvals) >= set(participants) else "proposed"
        c.execute("UPDATE shared_branches SET approvals_json=?, status=?, updated_at=? WHERE branch_id=?", (_json(approvals), status, _now(), branch_id))
    write_audit(actor_id, "shared_branch.approve", branch_id, {"group_id": group_id, "status": status})
    return {"branch_id": branch_id, "participants": participants, "approvals": approvals, "status": status}


def list_shared_branches(group_id: str, actor_id: str, status: str | None = None) -> list[dict]:
    _require_member(group_id, actor_id)
    sql = "SELECT * FROM shared_branches WHERE group_id=?"
    args: list[Any] = [group_id]
    if status:
        sql += " AND status=?"
        args.append(status)
    sql += " ORDER BY updated_at DESC"
    with _conn() as c:
        rows = c.execute(sql, args).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        participants = json.loads(item.pop("participants_json") or "[]")
        if actor_id not in participants:
            continue
        item["content"] = json.loads(item.pop("content_json") or "{}")
        item["participants"] = participants
        item["evidence_refs"] = json.loads(item.pop("evidence_refs_json") or "[]")
        item["approvals"] = json.loads(item.pop("approvals_json") or "[]")
        out.append(item)
    return out


def build_group_model(group_id: str, actor_id: str) -> dict:
    session = get_group_session(group_id, actor_id)
    active_members = [member for member in session["members"] if member["status"] == "active"]
    with _conn() as c:
        event_rows = c.execute(
            "SELECT event_id,event_type,actor_id FROM group_events WHERE group_id=? AND visibility='group_public' ORDER BY created_at DESC LIMIT 500",
            (group_id,),
        ).fetchall()
        branch_rows = c.execute("SELECT * FROM shared_branches WHERE group_id=? AND status='active' AND visibility='group' ORDER BY updated_at DESC", (group_id,)).fetchall()
    event_type_counts: dict[str, int] = {}
    actor_counts: dict[str, int] = {}
    for row in event_rows:
        event_type_counts[row["event_type"]] = event_type_counts.get(row["event_type"], 0) + 1
        actor_counts[row["actor_id"]] = actor_counts.get(row["actor_id"], 0) + 1
    branches = []
    for row in branch_rows:
        branches.append({"branch_id": row["branch_id"], "category": row["category"], "visibility": row["visibility"], "content": json.loads(row["content_json"] or "{}"), "evidence_refs": json.loads(row["evidence_refs_json"] or "[]")})
    commitment_branches = [b for b in branches if b["category"] in {"task", "commitment", "goal"}]
    outcome_branches = [b for b in branches if b["category"] == "outcome"]
    open_questions = event_type_counts.get("question", 0) + event_type_counts.get("open_question", 0)
    if actor_counts:
        low = min(actor_counts.values())
        high = max(actor_counts.values())
        participation_balance = round(low / high, 3) if high else 1.0
    else:
        participation_balance = None
    model = {
        "group_id": group_id,
        "group_scope_only": True,
        "private_member_models_accessed": False,
        "active_members": len(active_members),
        "public_event_count": len(event_rows),
        "event_type_counts": event_type_counts,
        "participation_balance": participation_balance,
        "open_questions": open_questions,
        "shared_branches": branches,
        "commitment_count": len(commitment_branches),
        "decision_count": len(outcome_branches),
        "decision_state": "decided" if outcome_branches else "open_questions" if open_questions else "coordinating",
        "notice": "Participation balance is an aggregate process signal, not a ranking of members.",
        "boundary": "The group model may only read group-public events and active shared branches. It cannot read any member's private Tender state.",
    }
    snapshot_id = _id("gsnap")
    now = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO group_model_snapshots(snapshot_id,group_id,model_json,evidence_refs_json,confidence,created_at) VALUES(?,?,?,?,?,?)",
            (snapshot_id, group_id, _json(model), _json([row["event_id"] for row in event_rows[:50]] + [b["branch_id"] for b in branches]), 0.6 if event_rows or branches else 0.0, now),
        )
    write_audit(actor_id, "group.model.build", group_id, {"snapshot_id": snapshot_id, "public_event_count": len(event_rows), "shared_branch_count": len(branches)})
    return {"snapshot_id": snapshot_id, "created_at": now, **model}


def create_group_draft(group_id: str, actor_id: str, intent: str = "clarify") -> dict:
    _require_member(group_id, actor_id)
    model = build_group_model(group_id, actor_id)
    intent = intent.strip().lower()
    templates = {
        "clarify": "我想先确认一下：我们现在要解决的问题是什么，下一步由谁负责？",
        "commit": "我可以先承担一个最小步骤，并在这里确认具体交付和时间。",
        "repair": "我想确认刚才的分歧：我观察到的是……，我可能理解错了，愿意先听你的版本。",
        "summarize": f"当前群里还有 {model['open_questions']} 个开放问题，先确认负责人和下一步。",
    }
    draft = templates.get(intent, templates["clarify"])
    write_audit(actor_id, "group.draft.create", group_id, {"intent": intent})
    return {"group_id": group_id, "actor_id": actor_id, "draft": draft, "status": "draft_only", "auto_send": False, "requires_user_confirmation": True, "based_on_group_scope_only": True}


def record_group_outcome(group_id: str, actor_id: str, decision: str, commitments: Iterable[dict] | None = None, unresolved: Iterable[str] | None = None, evidence_refs: Iterable[str] | None = None) -> dict:
    session = get_group_session(group_id, actor_id)
    outcome_id = _id("goutcome")
    participant_ids = [member["actor_id"] for member in session["members"] if member["status"] == "active"]
    branch = create_shared_branch(
        group_id,
        actor_id,
        "outcome",
        {"outcome_id": outcome_id, "decision": decision.strip(), "commitments": list(commitments or []), "unresolved": list(unresolved or [])},
        participant_ids,
        evidence_refs,
        visibility="group",
    )
    with _conn() as c:
        c.execute(
            "INSERT INTO group_outcomes(outcome_id,group_id,decision,commitments_json,unresolved_json,evidence_refs_json,recorded_by,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (outcome_id, group_id, decision.strip(), _json(list(commitments or [])), _json(list(unresolved or [])), _json(list(evidence_refs or [])), actor_id, _now()),
        )
    write_audit(actor_id, "group.outcome.record", outcome_id, {"group_id": group_id, "shared_branch_id": branch["branch_id"], "branch_status": branch["status"]})
    return {"outcome_id": outcome_id, "group_id": group_id, "status": "pending_shared_approval", "shared_branch": branch}


def list_group_outcomes(group_id: str, actor_id: str) -> list[dict]:
    _require_member(group_id, actor_id)
    with _conn() as c:
        rows = c.execute("SELECT * FROM group_outcomes WHERE group_id=? ORDER BY created_at DESC", (group_id,)).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["commitments"] = json.loads(item.pop("commitments_json") or "[]")
        item["unresolved"] = json.loads(item.pop("unresolved_json") or "[]")
        item["evidence_refs"] = json.loads(item.pop("evidence_refs_json") or "[]")
        out.append(item)
    return out
