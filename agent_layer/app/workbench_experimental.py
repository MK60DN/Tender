"""Experimental LLM enrichment for the Tender multi-Agent workbench.

The module sends only a redacted task and state summary to the configured
experimental model API. Deterministic workbench outputs remain the authoritative
contract; model notes are additive and can fail closed.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

from .llm import chat, config

AGENT_GUIDANCE = {
    "coordinator": "拆解任务、明确边界与交接顺序；只给一个可执行的协调判断。",
    "content_curator": "选择最小必要的学习材料与练习范围；不虚构题库内容。",
    "assessment": "解释当前掌握、犹豫和元认知信号；必须保留不确定性，不做诊断。",
    "student_tutor": "把支持压缩成一个今天能完成的最小行动；不直接替用户完成。",
    "external_communication": "说明对外草稿应保留什么、删去什么；只生成待审批内容。",
    "safety_guardrail": "检查隐私、排名、人格诊断和自动外发风险；默认只允许草稿。",
}

AGENT_IDS = tuple(AGENT_GUIDANCE)


def status() -> dict:
    cfg = config()
    configured = bool(cfg.get("api_key")) and cfg.get("provider") not in {"mock", "fallback", None}
    return {
        "configured": configured,
        "provider": cfg.get("provider"),
        "model": cfg.get("model"),
        "mode": "experimental_redacted_summary",
        "notice": "只发送脱敏任务与状态摘要；不发送姓名、原始对话、健康信息或完整学习树。",
    }


def safe_payload(thread: dict, context: dict) -> dict:
    return {
        "task_type": thread.get("task_type") or "learning_support",
        "objective_length": min(500, len(str(thread.get("objective") or ""))),
        "audience_role": thread.get("audience_role") or "parent",
        "state_summary": {
            "mastery": round(float(context.get("mastery", 0.5) or 0.5), 3),
            "jol_bias": round(float(context.get("jol_bias", 0.0) or 0.0), 3),
            "hesitation": round(float(context.get("hesitation", 0.0) or 0.0), 3),
            "event_count_bucket": min(1000, int(context.get("event_count", 0) or 0) // 10 * 10),
        },
        "policy": [
            "不展示排名",
            "任务原文不离开本地；仅发送任务长度与状态摘要",
            "不做人格或医学诊断",
            "不承诺提分、录取或就业结果",
            "对外内容只能是草稿并等待真人审批",
            "不发送姓名、原始对话和健康信息",
        ],
    }


def agent_note(agent_id: str, thread: dict, context: dict) -> dict:
    cfg = config()
    if not cfg.get("api_key") or cfg.get("provider") in {"mock", "fallback", None}:
        return {"status": "not_configured", "provider": cfg.get("provider"), "model": cfg.get("model")}
    messages = [
        {
            "role": "system",
            "content": (
                "你是 Tender 多 Agent 协作系统中的受控 Agent。"
                "只接收并使用脱敏任务与状态摘要，不猜姓名、学校、家庭、诊断或未提供的隐私。"
                "用中文输出 1—2 句、最多 100 字，给出本角色最关键的新增判断和边界。"
                "不得宣称自动发送、自动执行或保证结果。"
            ),
        },
        {"role": "system", "content": "角色要求：" + AGENT_GUIDANCE.get(agent_id, "给出可验证的支持判断。")},
        {"role": "user", "content": json.dumps(safe_payload(thread, context), ensure_ascii=False, separators=(",", ":"))},
    ]
    started = time.monotonic()
    result = chat(messages, temperature=0.2, max_tokens=480)
    latency_ms = round((time.monotonic() - started) * 1000)
    text = (result.get("text") or "").strip()
    provider = result.get("provider")
    if result.get("error") or result.get("reasoning_only") or provider in {"mock", "fallback"} or not text:
        return {
            "status": "fallback",
            "provider": provider,
            "model": result.get("model"),
            "latency_ms": latency_ms,
            "boundary": "实验 API 不可用；本轮保留确定性安全结果。",
        }
    return {
        "status": "ready",
        "provider": provider,
        "model": result.get("model"),
        "latency_ms": latency_ms,
        "text": text[:500],
        "boundary": "模型仅基于脱敏摘要生成建议；未读取原始对话或姓名。",
    }


def agent_notes(thread: dict, context: dict) -> dict[str, dict]:
    if os.getenv("TENDER_WORKBENCH_EXPERIMENTAL", "1") != "1":
        return {}
    notes: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(agent_note, agent_id, thread, context): agent_id for agent_id in AGENT_IDS}
        for future in as_completed(futures):
            agent_id = futures[future]
            try:
                notes[agent_id] = future.result()
            except Exception as exc:
                notes[agent_id] = {"status": "error", "error": type(exc).__name__}
    return notes
