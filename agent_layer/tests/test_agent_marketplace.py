import atexit
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

import app.agent_marketplace as marketplace_module
from app.agent_catalog import agent_catalog
from app.agent_marketplace import create_expert_agent, get_agent_for_viewer, invoke_expert_agent
from app.agent_runtime import list_agents
from app.daoql import list_audit
from app.main import (
    AgentGenerateRequest,
    AgentPurchaseRequest,
    agent_entitlements,
    buy_expert_agent,
    fixed_agents,
    generate_expert_agent,
    marketplace,
)


TEST_OWNER_PREFIX = "TEST_MKT_OWNER_"
TEST_BUYER_PREFIX = "TEST_MKT_BUYER_"
TEST_DB = Path(__file__).resolve().parent.parent / "tender_agent.db"


def _cleanup_test_market_data():
    with sqlite3.connect(TEST_DB) as conn:
        agent_ids = [
            row[0]
            for row in conn.execute(
                "SELECT agent_id FROM expert_agents WHERE owner_id LIKE ? OR owner_id LIKE ?",
                (TEST_OWNER_PREFIX + "%", "HTTP_OWNER_%"),
            ).fetchall()
        ]
        if agent_ids:
            placeholders = ",".join("?" for _ in agent_ids)
            conn.execute(f"DELETE FROM agent_purchases WHERE agent_id IN ({placeholders})", agent_ids)
        conn.execute(
            "DELETE FROM expert_agents WHERE owner_id LIKE ? OR owner_id LIKE ?",
            (TEST_OWNER_PREFIX + "%", "HTTP_OWNER_%"),
        )


atexit.register(_cleanup_test_market_data)


def test_expert_agent_marketplace():
    owner = TEST_OWNER_PREFIX + uuid4().hex[:8]
    buyer = TEST_BUYER_PREFIX + uuid4().hex[:8]

    fixed = fixed_agents()
    assert len(fixed["agents"]) >= 5
    assert fixed["integrity"]["ok"] is True
    assert all(item["runtime_status"] == "implemented" for item in fixed["agents"])
    assert any(a["agent_id"] == "fixed_mentalization_companion" for a in fixed["agents"])

    runtime_ids = {a["id"] for a in list_agents()}
    assert {
        "fixed_mentalization_companion",
        "fixed_cognition_emotion_regulator",
        "fixed_reflection_coach",
        "fixed_family_bridge",
        "fixed_safety_guardian",
    } <= runtime_ids

    catalog = agent_catalog()
    assert catalog["counts"]["fixed_consumer_agents"] == 5
    assert catalog["counts"]["runtime_yaml_agents"] >= 15
    assert catalog["integrity"] == {
        "duplicate_runtime_ids": [],
        "missing_fixed_runtime_specs": [],
        "ok": True,
    }
    runtime_by_id = {item["id"]: item for item in catalog["runtime_yaml_agents"]}
    assert runtime_by_id["fixed_reflection_coach"]["invocable"] is True
    assert runtime_by_id["data_steward"]["invocable"] is False
    assert "camel" not in json.dumps(catalog, ensure_ascii=False).lower()

    generated = generate_expert_agent(AgentGenerateRequest(
        owner_id=owner,
        need="帮助我在焦虑时拆分学习任务并做元认知复盘",
        name="认知情绪调节专家",
        category="emotion_cognition",
        price_cents=1990,
        visibility="marketplace",
    ))
    agent = generated["agent"]
    assert agent["status"] == "published"
    assert agent["spec"]["inputs"]["never_default"]
    listing = marketplace(query="认知情绪")
    assert any(a["agent_id"] == agent["agent_id"] for a in listing["expert_agents"])

    try:
        invoke_expert_agent(agent["agent_id"], buyer, "先给一个最小支持", {"knowledge": {"mastery": 0.4}})
        assert False, "purchase should be required before invocation"
    except PermissionError:
        pass

    bought = buy_expert_agent(agent["agent_id"], AgentPurchaseRequest(buyer_id=buyer))
    assert bought["license_status"] == "active"
    assert bought["data_scope"] == "authorized_summary_only"

    captured = {}

    def fake_execute(config, message, state, context=None):
        captured["config"] = config
        captured["state"] = state
        captured["context"] = context
        return {"text": "先确认卡点，再给一个最小支持。", "model": "unit-test", "provider": "agent-runtime"}

    original_execute = marketplace_module.execute_agent
    marketplace_module.execute_agent = fake_execute
    try:
        invoked = invoke_expert_agent(
            agent["agent_id"],
            buyer,
            "先给一个最小支持",
            {
                "knowledge": {"mastery": 0.4},
                "metacognition": {"jol_bias": 0.2, "hesitation": 0.7},
                "emotion": {
                    "valence": -0.5,
                    "arousal": 0.8,
                    "confidence": 0.7,
                    "label": "紧张或高负荷",
                    "note": "RAW_EMOTION_NOTE",
                    "evidence_refs": ["SECRET_EVENT"],
                },
                "baseline": {"arrangement_fit": 0.6},
                "raw_conversation": "SECRET_RAW_CONVERSATION",
                "n_events": 9,
                "timestamp": "2026-10-21T00:00:00+08:00",
            },
        )
    finally:
        marketplace_module.execute_agent = original_execute

    assert invoked["agent_type"] == "expert_marketplace"
    assert invoked["license"]["data_scope"] == "authorized_summary_only"
    assert invoked["action"]["next_action"]
    assert captured["state"]["scope"] == "authorized_summary_only"
    assert "raw_conversation" not in captured["state"]
    assert "evidence_refs" not in captured["state"]["emotion_context"]
    assert "note" not in captured["state"]["emotion_context"]
    serialized = json.dumps({"captured": captured, "invoked": invoked}, ensure_ascii=False)
    assert "SECRET_RAW_CONVERSATION" not in serialized
    assert "RAW_EMOTION_NOTE" not in serialized
    assert "SECRET_EVENT" not in serialized
    assert "camel" not in serialized.lower()

    audits = list_audit(200)
    assert any(a["action"] == "agent.invoke" and a["target"] == agent["agent_id"] for a in audits)
    assert any(a["action"] == "agent.invoke.denied" and a["target"] == agent["agent_id"] for a in audits)
    invoke_audit = next(a for a in audits if a["action"] == "agent.invoke" and a["target"] == agent["agent_id"])
    assert "message" not in invoke_audit["payload"]
    assert invoke_audit["payload"]["message_chars"] == len("先给一个最小支持")

    def failing_execute(config, message, state, context=None):
        raise RuntimeError("internal adapter detail must not leak")

    marketplace_module.execute_agent = failing_execute
    try:
        fallback = invoke_expert_agent(agent["agent_id"], buyer, "继续", {"knowledge": {"mastery": 0.4}})
    finally:
        marketplace_module.execute_agent = original_execute
    assert fallback["llm"]["fallback_used"] is True
    assert fallback["llm"]["fallback_reason"] == "agent_runtime_unavailable"
    assert "internal adapter detail" not in json.dumps(fallback, ensure_ascii=False)

    high_risk = create_expert_agent(
        owner_id=owner,
        need="提供安全支持",
        name="安全专家",
        category="safety",
        price_cents=100,
        visibility="marketplace",
    )
    assert high_risk["status"] == "pending_review"
    assert not any(
        item["agent_id"] == high_risk["agent_id"]
        for item in marketplace().get("expert_agents", [])
    )

    private_agent = create_expert_agent(
        owner_id=owner,
        need="私人复盘助手",
        name="私人助手",
        category="metacognition",
        visibility="private",
    )
    try:
        get_agent_for_viewer(private_agent["agent_id"])
        assert False, "private agent should not be public"
    except PermissionError:
        pass
    assert get_agent_for_viewer(private_agent["agent_id"], owner)["agent_id"] == private_agent["agent_id"]

    ent = agent_entitlements(buyer)
    assert any(p["agent_id"] == agent["agent_id"] for p in ent["purchased_agents"])
    try:
        buy_expert_agent(agent["agent_id"], AgentPurchaseRequest(buyer_id=owner))
        assert False, "owner should not purchase own agent"
    except HTTPException as exc:
        assert exc.status_code == 400
