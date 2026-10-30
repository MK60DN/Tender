# -*- coding: utf-8 -*-
"""发现型学习循环的最小持久化实现。

一个循环依次经历 planned、acted、completed 三个状态。每次状态变更都会
写入 DAOQL 事件，并通过因果边连接前一步；成功写入后追加哈希链审计。
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from .daoql import insert_edge, insert_event, write_audit

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"

STATUS_PLANNED = "planned"
STATUS_ACTED = "acted"
STATUS_COMPLETED = "completed"
VALID_STATUSES = {STATUS_PLANNED, STATUS_ACTED, STATUS_COMPLETED}


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _normalize_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not options:
        raise ValueError("at least one option is required")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for option in options:
        if not isinstance(option, dict):
            raise ValueError("each option must be an object")
        option_id = _required_text(option.get("id"), "option.id")
        label = _required_text(option.get("label"), "option.label")
        if option_id in seen:
            raise ValueError("option.id must be unique")
        seen.add(option_id)
        item = dict(option)
        item["id"] = option_id
        item["label"] = label
        normalized.append(item)
    return normalized


def _decode(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item["options"] = json.loads(item.pop("options_json") or "[]")
    item["state"] = json.loads(item.pop("state_json") or "{}")
    return item


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_loops (
                loop_id TEXT PRIMARY KEY,
                learner_id TEXT NOT NULL,
                goal TEXT NOT NULL,
                options_json TEXT NOT NULL,
                selected_option_id TEXT NOT NULL,
                choice_reason TEXT NOT NULL,
                action TEXT,
                expected_outcome TEXT,
                actual_result TEXT,
                responsibility_owner TEXT,
                reflection TEXT,
                state_json TEXT NOT NULL,
                status TEXT NOT NULL,
                create_event_id TEXT NOT NULL,
                action_event_id TEXT,
                result_event_id TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_decision_loops_learner "
            "ON decision_loops(learner_id, created_at DESC)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_decision_loops_status "
            "ON decision_loops(learner_id, status, updated_at DESC)"
        )


def get_loop(loop_id: str) -> dict[str, Any]:
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM decision_loops WHERE loop_id=?", (loop_id,)
        ).fetchone()
    if row is None:
        raise KeyError("decision loop not found")
    return _decode(row)


def list_loops(learner_id: str, limit: int = 50) -> list[dict[str, Any]]:
    init_db()
    safe_limit = max(1, min(int(limit), 200))
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM decision_loops WHERE learner_id=? "
            "ORDER BY created_at DESC LIMIT ?",
            (learner_id, safe_limit),
        ).fetchall()
    return [_decode(row) for row in rows]


def create_loop(
    *,
    learner_id: str,
    goal: str,
    options: list[dict[str, Any]],
    selected_option_id: str,
    choice_reason: str,
    state: dict[str, Any] | None,
    actor_id: str,
) -> dict[str, Any]:
    learner_id = _required_text(learner_id, "learner_id")
    actor_id = _required_text(actor_id, "actor_id")
    goal = _required_text(goal, "goal")
    choice_reason = _required_text(choice_reason, "choice_reason")
    selected_option_id = _required_text(selected_option_id, "selected_option_id")
    clean_options = _normalize_options(options)
    if selected_option_id not in {item["id"] for item in clean_options}:
        raise ValueError("selected_option_id must reference an option")

    init_db()
    loop_id = "loop_" + uuid.uuid4().hex[:12]
    now = _now()
    clean_state = dict(state or {})
    event_id = insert_event(
        {
            "event_type": "decision_loop.created",
            "student_id": learner_id,
            "payload": {
                "loop_id": loop_id,
                "goal": goal,
                "options": clean_options,
                "selected_option_id": selected_option_id,
                "choice_reason": choice_reason,
                "state": clean_state,
                "status": STATUS_PLANNED,
            },
            "source": "tender.decision_loop",
            "provenance": {"schema": "decision_loop.v1", "actor_id": actor_id},
        }
    )
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO decision_loops(
                loop_id,learner_id,goal,options_json,selected_option_id,choice_reason,
                action,expected_outcome,actual_result,responsibility_owner,reflection,
                state_json,status,create_event_id,action_event_id,result_event_id,
                created_by,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                loop_id,
                learner_id,
                goal,
                json.dumps(clean_options, ensure_ascii=False),
                selected_option_id,
                choice_reason,
                None,
                None,
                None,
                None,
                None,
                json.dumps(clean_state, ensure_ascii=False),
                STATUS_PLANNED,
                event_id,
                None,
                None,
                actor_id,
                now,
                now,
            ),
        )
    write_audit(
        actor_id,
        "decision_loop.create",
        loop_id,
        {
            "learner_id": learner_id,
            "event_id": event_id,
            "status": STATUS_PLANNED,
            "option_count": len(clean_options),
            "state_keys": sorted(clean_state),
        },
    )
    return get_loop(loop_id)


def record_action(
    loop_id: str,
    *,
    action: str,
    expected_outcome: str,
    state: dict[str, Any] | None,
    actor_id: str,
) -> dict[str, Any]:
    actor_id = _required_text(actor_id, "actor_id")
    action = _required_text(action, "action")
    expected_outcome = _required_text(expected_outcome, "expected_outcome")
    current = get_loop(loop_id)
    if current["status"] != STATUS_PLANNED:
        raise ValueError("decision loop must be planned before recording an action")

    clean_state = dict(state or {})
    now = _now()
    event_id = insert_event(
        {
            "event_type": "decision_loop.action_recorded",
            "student_id": current["learner_id"],
            "payload": {
                "loop_id": loop_id,
                "action": action,
                "expected_outcome": expected_outcome,
                "state": clean_state,
                "status": STATUS_ACTED,
            },
            "source": "tender.decision_loop",
            "provenance": {
                "schema": "decision_loop.v1",
                "actor_id": actor_id,
                "previous_event_id": current["create_event_id"],
            },
        }
    )
    insert_edge(
        current["create_event_id"],
        event_id,
        relation="followed_by_action",
        confidence=1.0,
        evidence={"loop_id": loop_id, "selection": current["selected_option_id"]},
    )
    with _conn() as conn:
        updated = conn.execute(
            """
            UPDATE decision_loops
            SET action=?, expected_outcome=?, state_json=?, status=?,
                action_event_id=?, updated_at=?
            WHERE loop_id=? AND status=?
            """,
            (
                action,
                expected_outcome,
                json.dumps(clean_state, ensure_ascii=False),
                STATUS_ACTED,
                event_id,
                now,
                loop_id,
                STATUS_PLANNED,
            ),
        ).rowcount
    if updated != 1:
        raise RuntimeError("decision loop state changed concurrently")
    write_audit(
        actor_id,
        "decision_loop.action",
        loop_id,
        {
            "learner_id": current["learner_id"],
            "event_id": event_id,
            "previous_event_id": current["create_event_id"],
            "status": STATUS_ACTED,
            "state_keys": sorted(clean_state),
        },
    )
    return get_loop(loop_id)


def record_result(
    loop_id: str,
    *,
    actual_result: str,
    responsibility_owner: str,
    reflection: str,
    state: dict[str, Any] | None,
    actor_id: str,
) -> dict[str, Any]:
    actor_id = _required_text(actor_id, "actor_id")
    actual_result = _required_text(actual_result, "actual_result")
    responsibility_owner = _required_text(
        responsibility_owner, "responsibility_owner"
    )
    current = get_loop(loop_id)
    if current["status"] != STATUS_ACTED:
        raise ValueError("decision loop must be acted before recording a result")

    clean_state = dict(state or {})
    now = _now()
    event_id = insert_event(
        {
            "event_type": "decision_loop.result_recorded",
            "student_id": current["learner_id"],
            "payload": {
                "loop_id": loop_id,
                "actual_result": actual_result,
                "responsibility_owner": responsibility_owner,
                "reflection": reflection,
                "state": clean_state,
                "status": STATUS_COMPLETED,
            },
            "source": "tender.decision_loop",
            "provenance": {
                "schema": "decision_loop.v1",
                "actor_id": actor_id,
                "previous_event_id": current["action_event_id"],
            },
        }
    )
    insert_edge(
        current["action_event_id"],
        event_id,
        relation="produced_result",
        confidence=1.0,
        evidence={"loop_id": loop_id, "responsibility_owner": responsibility_owner},
    )
    with _conn() as conn:
        updated = conn.execute(
            """
            UPDATE decision_loops
            SET actual_result=?, responsibility_owner=?, reflection=?,
                state_json=?, status=?, result_event_id=?, updated_at=?
            WHERE loop_id=? AND status=?
            """,
            (
                actual_result,
                responsibility_owner,
                reflection,
                json.dumps(clean_state, ensure_ascii=False),
                STATUS_COMPLETED,
                event_id,
                now,
                loop_id,
                STATUS_ACTED,
            ),
        ).rowcount
    if updated != 1:
        raise RuntimeError("decision loop state changed concurrently")
    write_audit(
        actor_id,
        "decision_loop.result",
        loop_id,
        {
            "learner_id": current["learner_id"],
            "event_id": event_id,
            "previous_event_id": current["action_event_id"],
            "status": STATUS_COMPLETED,
            "responsibility_owner": responsibility_owner,
            "reflection_present": bool(reflection.strip()),
            "state_keys": sorted(clean_state),
        },
    )
    return get_loop(loop_id)