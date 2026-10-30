"""Agent 运行时：规则、RAG、执行适配、护栏与审计。"""
from __future__ import annotations

import hashlib
import os
import pathlib

import yaml

from .daoql import write_audit
from .guardrails import check_text, requires_human_approval
from .llm import chat
from .rag import search
from .safety_queue import create_ticket

AGENTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "agents"
RUNTIME_NAME = "tender-agent-runtime"
EXECUTION_PROVIDER = "agent-runtime"


def list_agents():
    return [yaml.safe_load(p.read_text(encoding="utf-8")) for p in sorted(AGENTS_DIR.glob("*.yaml"))]


def get_agent(agent_id: str):
    p = AGENTS_DIR / (agent_id + ".yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None


def runtime_status() -> dict:
    """Return a framework-neutral runtime status for API consumers."""
    try:
        from .agent_runtime_adapter import runtime_status as adapter_status

        raw = adapter_status()
        return {
            "runtime": RUNTIME_NAME,
            "available": bool(raw.get("runtime_available")),
            "execution_mode": EXECUTION_PROVIDER,
            "model_ready": bool(raw.get("model_ready")),
            "workforce_execution": "gated",
            "boundary": "Agent execution is pluggable; DAOQL owns facts, causality, authorization, marketplace and audit.",
        }
    except Exception:
        return {
            "runtime": RUNTIME_NAME,
            "available": False,
            "execution_mode": EXECUTION_PROVIDER,
            "model_ready": False,
            "workforce_execution": "gated",
            "boundary": "Agent execution is pluggable; DAOQL owns facts, causality, authorization, marketplace and audit.",
        }


def execute_agent(config: dict, message: str, tender_state: dict, context: dict | None = None) -> dict:
    """Execute one agent through the configured runtime without exposing adapter details."""
    try:
        from .agent_runtime_adapter import invoke_chat_agent, runtime_status as adapter_status

        status = adapter_status()
        if not status.get("runtime_available") or not status.get("model_ready"):
            raise RuntimeError("agent_runtime_unavailable")
        out = invoke_chat_agent(config, message, tender_state, context)
        text = (out.get("text") or "").strip()
        if not text:
            raise RuntimeError("agent_runtime_empty_response")
        return {
            "text": text,
            "provider": EXECUTION_PROVIDER,
            "model": out.get("model"),
            "runtime": RUNTIME_NAME,
        }
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError("agent_runtime_execution_failed") from None


def plan_workforce(task: str, agent_configs: list[dict], execute: bool = False) -> dict:
    """Framework-neutral multi-agent planning facade."""
    try:
        from .agent_runtime_adapter import workforce_plan as adapter_workforce_plan

        return adapter_workforce_plan(task, agent_configs, execute=execute)
    except ValueError:
        raise
    except Exception:
        if execute:
            raise RuntimeError("agent_runtime_execution_failed") from None
        workers = [{"agent_id": c.get("id"), "role": c.get("role")} for c in agent_configs[:5]]
        return {
            "backend": RUNTIME_NAME,
            "mode": "plan_only",
            "task": task,
            "workers": workers,
            "available": False,
            "note": "仅生成执行计划；实际执行需要显式开启，并经过权限、预算和风险门禁。",
        }


def _scoped_state_for_agent(agent_id: str, state: dict) -> dict:
    """Send only the aggregate state needed by a fixed agent to execution."""
    state = state or {}
    knowledge = state.get("knowledge", {}) or {}
    meta = state.get("metacognition", {}) or {}
    if agent_id == "fixed_family_bridge":
        return {
            "scope": "approved_family_summary",
            "knowledge": {"mastery": knowledge.get("mastery")},
            "metacognition": {
                "jol_bias": meta.get("jol_bias"),
                "hesitation": meta.get("hesitation"),
            },
            "event_count": state.get("n_events", 0),
            "state_timestamp": state.get("timestamp"),
        }
    if agent_id == "fixed_reflection_coach":
        return {
            "scope": "metacognition_summary",
            "knowledge": {"mastery": knowledge.get("mastery")},
            "metacognition": {
                "jol_bias": meta.get("jol_bias"),
                "hesitation": meta.get("hesitation"),
            },
            "state_timestamp": state.get("timestamp"),
        }
    if agent_id == "fixed_cognition_emotion_regulator":
        emotion = state.get("emotion", {}) or {}
        return {
            "scope": "emotion_context_and_aggregated_state",
            "knowledge": {"mastery": knowledge.get("mastery")},
            "metacognition": {"hesitation": meta.get("hesitation")},
            "emotion_context": {
                key: emotion.get(key)
                for key in ("valence", "arousal", "confidence", "label")
                if key in emotion
            },
            "event_count": state.get("n_events", 0),
            "state_timestamp": state.get("timestamp"),
        }
    return state




def _maybe_create_safety_ticket(student_id: str, agent_id: str, message: str, safety: dict) -> dict | None:
    if not safety.get("escalate_to_human"):
        return None
    hits = safety.get("banned_hits", [])
    pii = safety.get("pii_hits", [])
    risk_level = "emergency" if hits else "review"
    reason = "high_risk_language" if hits else "pii_detected"
    message_hash = hashlib.sha256((message or "").encode("utf-8")).hexdigest()
    return create_ticket(
        student_id=student_id,
        source_agent=agent_id,
        risk_level=risk_level,
        reason=reason,
        evidence_refs=[f"banned:{','.join(hits)}"] if hits else [f"pii:{','.join(pii)}"],
        message_hash=message_hash,
    )

def _quadrant(mastery, hesitation):
    if hesitation >= 0.5 and mastery < 0.5:
        return "high_hesitation_wrong"
    if hesitation >= 0.5:
        return "high_hesitation_right"
    if mastery < 0.5:
        return "low_hesitation_wrong"
    return "low_hesitation_right"


def _system_prompt(cfg):
    return (
        "你是 Tender 心智化教育系统的 " + cfg["role"] + "。"
        "你必须基于证据回答，不贴诊断标签，不做医疗或心理诊断。"
        "如果涉及高风险内容，建议升级人工。回答要短、具体、可执行。"
    )


def _audit_metadata(message: str, **extra) -> dict:
    raw = message or ""
    return {
        "message_chars": len(raw),
        "message_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        **extra,
    }


def _normalize_runtime_error(exc: Exception) -> str:
    value = str(exc)
    if value in {"agent_runtime_unavailable", "agent_runtime_empty_response", "agent_runtime_execution_failed"}:
        return value
    return "agent_runtime_execution_failed"


def invoke(agent_id: str, student_id: str, message: str, state: dict, context: dict | None = None):
    cfg = get_agent(agent_id)
    if not cfg:
        return {"error": "unknown_agent", "agent_id": agent_id}
    mastery = float(state.get("knowledge", {}).get("mastery", 0.5))
    bias = float(state.get("metacognition", {}).get("jol_bias", 0.0))
    hesitation = float(state.get("metacognition", {}).get("hesitation", 0.0))

    safety = check_text(message)
    safety_ticket = _maybe_create_safety_ticket(student_id, agent_id, message, safety)
    if agent_id in {"safety_guardrail", "fixed_safety_guardian"}:
        write_audit(
            agent_id,
            "invoke",
            student_id,
            _audit_metadata(message, outcome="safety_check", fallback_used=False),
        )
        return {
            "from_agent": agent_id,
            "student_id": student_id,
            "intent": "safety_check",
            "action": {**safety, "ticket_id": safety_ticket.get("ticket_id") if safety_ticket else None},
            "evidence": {"n_events": state.get("n_events", 0)},
            "policy": cfg["policy"],
            "llm": {
                "provider": EXECUTION_PROVIDER,
                "model": "policy-engine",
                "fallback_used": False,
                "fallback_reason": None,
            },
            "status": "proposed",
        }

    rag_hits = search(message or cfg["role"], top_k=4)
    rag_text = "\n".join([h["text"][:300] for h in rag_hits])

    rule = {}
    if agent_id in {"metacognition_coach", "fixed_reflection_coach"}:
        rule = {
            "quadrant": _quadrant(mastery, hesitation),
            "prompt": "你刚才在这里停了一下：你觉得自己是不确定，还是只是需要更多时间？",
        }
    elif agent_id == "fixed_mentalization_companion":
        uncertainty = float(state.get("cognitive", {}).get("uncertainty", 0.5) or 0.5)
        rule = {
            "state_summary": "当前状态仍需结合更多连续记录验证",
            "mastery": round(mastery, 3),
            "jol_bias": round(bias, 3),
            "hesitation": round(hesitation, 3),
            "uncertainty": round(uncertainty, 3),
            "support_policy": "最低必要干预；先问卡点，再决定提示、拆解或恢复",
        }
    elif agent_id == "fixed_cognition_emotion_regulator":
        emotion = state.get("emotion", {}) or {}
        load = "high" if hesitation >= 0.6 else "medium" if hesitation >= 0.35 else "low"
        rule = {
            "load_band": load,
            "emotion_context": emotion,
            "task_adjustment": "缩短单步任务并设置恢复间隙" if load != "low" else "保持当前节奏",
            "no_diagnosis": True,
        }
    elif agent_id == "fixed_family_bridge":
        rule = {
            "human_approval": True,
            "raw_conversation_shared": False,
            "summary_scope": "approved_family_summary",
            "support_focus": "家庭可以怎样支持，而不是给学习者贴标签",
        }
    elif agent_id == "student_tutor":
        rule = {"hint_level": "minimal_hint" if mastery >= 0.6 else "worked_step"}
    elif agent_id == "group_facilitator":
        rule = {
            "clique_warning": state.get("group", {}).get("clustering", 0) > 0.6,
            "bridge_suggestion": "本轮安排一个跨组桥接角色。",
        }
    elif agent_id == "data_steward":
        rule = {"n_events": state.get("n_events", 0), "has_consent": True, "retention_days": 365}

    messages = [
        {"role": "system", "content": _system_prompt(cfg)},
        {"role": "system", "content": "可用资料：\n" + rag_text},
        {"role": "user", "content": message or ("请根据状态给出建议。状态：" + str(state))},
    ]
    runtime_error = None
    llm = None
    if os.getenv("TENDER_AGENT_RUNTIME", "agent-runtime").lower() != "legacy":
        try:
            runtime_out = execute_agent(
                cfg,
                message or "请根据状态给出建议。",
                _scoped_state_for_agent(agent_id, state),
                {"rag_text": rag_text, "rule": rule},
            )
            llm = {
                "provider": EXECUTION_PROVIDER,
                "model": runtime_out.get("model"),
                "text": runtime_out.get("text", ""),
                "fallback_used": False,
                "fallback_reason": None,
            }
        except Exception as exc:
            runtime_error = _normalize_runtime_error(exc)

    if llm is None:
        fallback = chat(messages)
        llm = {
            "provider": EXECUTION_PROVIDER,
            "model": fallback.get("model"),
            "text": fallback.get("text", ""),
            "fallback_used": True,
            "fallback_reason": runtime_error or "agent_runtime_unavailable",
        }

    text = llm.get("text", "")
    action = {"text": text, "rule": rule, "rag_sources": [h["source"] for h in rag_hits]}
    approval = requires_human_approval(
        agent_id,
        "notify_parent" if agent_id in {"parent_communication", "fixed_family_bridge"} else "general",
    )
    msg = {
        "from_agent": agent_id,
        "student_id": student_id,
        "intent": cfg["role"],
        "action": action,
        "evidence": {"n_events": state.get("n_events", 0), "state_timestamp": state.get("timestamp")},
        "policy": {**cfg["policy"], "requires_human_approval": approval},
        "llm": {
            "provider": llm.get("provider"),
            "model": llm.get("model"),
            "fallback_used": llm.get("fallback_used", False),
            "fallback_reason": llm.get("fallback_reason"),
        },
        "safety": {**safety, "ticket_id": safety_ticket.get("ticket_id") if safety_ticket else None},
        "status": "proposed",
    }
    write_audit(
        agent_id,
        "invoke",
        student_id,
        _audit_metadata(
            message,
            provider=llm.get("provider"),
            fallback_used=llm.get("fallback_used", False),
            fallback_reason=llm.get("fallback_reason"),
            outcome="completed",
        ),
    )
    return msg
