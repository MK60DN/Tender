# -*- coding: utf-8 -*-
"""CAMEL-AI adapter for Tender agent execution and workforce orchestration.

CAMEL executes agents. DAOQL remains the source of truth for facts, causality,
authorization, trade records and audit.
"""
from __future__ import annotations
import os
from functools import lru_cache

from .llm import config as llm_config

try:
    import camel
    from camel.agents import ChatAgent
    from camel.models import ModelFactory
    from camel.societies.workforce import Workforce
    from camel.tasks import Task
    RUNTIME_AVAILABLE = True
except Exception as exc:  # pragma: no cover - exercised only when dependency is absent
    RUNTIME_AVAILABLE = False
    camel = None
    ChatAgent = None
    ModelFactory = None
    Workforce = None
    Task = None
    RUNTIME_IMPORT_ERROR = repr(exc)
else:
    RUNTIME_IMPORT_ERROR = ""


def runtime_status() -> dict:
    c = llm_config()
    enabled = os.getenv("TENDER_AGENT_RUNTIME", "camel").lower() != "legacy"
    model_ready = bool(c.get("api_key")) and c.get("provider") != "mock"
    return {
        "runtime_available": RUNTIME_AVAILABLE,
        "runtime_version": getattr(camel, "__version__", None) if RUNTIME_AVAILABLE else None,
        "runtime_default": "agent-runtime" if enabled and RUNTIME_AVAILABLE else "unavailable",
        "model_ready": model_ready,
        "provider": c.get("provider"),
        "model": c.get("model"),
        "import_error": RUNTIME_IMPORT_ERROR,
        "boundary": "Agent execution is isolated from DAOQL facts, causality, authorization, marketplace and audit.",
    }


@lru_cache(maxsize=1)
def _camel_model():
    if not RUNTIME_AVAILABLE:
        raise RuntimeError("agent runtime unavailable")
    c = llm_config()
    if not c.get("api_key") or c.get("provider") == "mock":
        raise RuntimeError("agent model unavailable")
    return ModelFactory.create(
        model_platform="openai-compatible-model",
        model_type=c["model"],
        api_key=c["api_key"],
        url=c["base_url"],
        model_config_dict={
            "temperature": c.get("temperature", 0.3),
            "max_tokens": c.get("max_tokens", 1200),
        },
        timeout=180,
    )


def _system_message(config: dict) -> str:
    policy = config.get("policy", {}) or {}
    return (
        f"你是 Tender 的 {config.get('id', 'agent')}。\n"
        f"角色：{config.get('role', '学习支持')}\n"
        f"可用工具：{config.get('tools', [])}\n"
        f"输入：{config.get('input', [])}\n"
        f"输出：{config.get('output', [])}\n"
        f"策略：{policy}\n"
        "必须基于证据回答；不输出心理或医学诊断；不贴固定人格标签；"
        "不访问未授权的原始对话或跨用户数据；高风险内容必须建议人工升级。"
    )


def compile_agent(config: dict):
    """Compile a Tender YAML AgentSpec into the configured runtime agent."""
    if not RUNTIME_AVAILABLE:
        raise RuntimeError("agent runtime unavailable")
    max_turns = (config.get("policy", {}) or {}).get("max_turns", 3)
    return ChatAgent(
        system_message=_system_message(config),
        model=_camel_model(),
        max_iteration=max(1, min(int(max_turns or 3), 6)),
        output_language="zh",
        agent_id=config.get("id", "tender_agent"),
    )


def invoke_chat_agent(config: dict, message: str, tender_state: dict, context: dict | None = None) -> dict:
    """Execute one compiled Tender agent through the configured runtime."""
    agent = compile_agent(config)
    payload = {
        "message": message or "请基于当前状态给出一个最低必要支持。",
        "tender_state": tender_state,
        "authorized_context": context or {},
    }
    response = agent.step(str(payload))
    content = ""
    if getattr(response, "msgs", None):
        content = response.msgs[0].content or ""
    if not content:
        content = str(response)
    return {
        "text": content,
        "provider": "agent-runtime",
        "model": llm_config().get("model"),
        "agent_id": config.get("id"),
    }


def workforce_plan(task: str, agent_configs: list[dict], execute: bool = False) -> dict:
    """Create a multi-agent execution plan and optionally execute it.

    Execution is opt-in because a workforce can call multiple models and tools.
    """
    if not (task or "").strip():
        raise ValueError("task is required")
    if not agent_configs:
        raise ValueError("at least one agent is required")
    if len(agent_configs) > 5:
        raise ValueError("at most five agents are allowed")
    configs = list(agent_configs)
    ids = [c.get("id") for c in configs]
    if any(not agent_id for agent_id in ids):
        raise ValueError("every agent requires an id")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate agents are not allowed")
    workers = [{"agent_id": c.get("id"), "role": c.get("role")} for c in configs]
    if not execute:
        return {
            "backend": "tender-agent-runtime",
            "mode": "plan_only",
            "task": task,
            "workers": workers,
            "available": RUNTIME_AVAILABLE,
            "note": "仅生成执行计划；实际执行需要显式开启，并经过权限、预算和风险门禁。",
        }
    if not RUNTIME_AVAILABLE:
        raise RuntimeError("agent runtime unavailable")
    enabled = os.getenv("ENABLE_TENDER_WORKFORCE", "0") == "1"
    if not enabled:
        return {
            "backend": "tender-agent-runtime",
            "mode": "blocked",
            "task": task,
            "workers": workers,
            "reason": "multi_agent_execution_disabled",
            "note": "多 Agent 自动执行默认关闭，避免不可控成本和工具调用。",
        }
    model = _camel_model()
    coordinator = ChatAgent(
        system_message="你是 Tender 的协调者。拆分任务、分派给受控专家、汇总成一条可审计结果，不伪造证据。",
        model=model,
        max_iteration=3,
        output_language="zh",
    )
    workforce = Workforce(f"Tender task: {task[:80]}", coordinator_agent=coordinator, default_model=model)
    for config in configs:
        worker = compile_agent(config)
        workforce.add_single_agent_worker(config.get("role", config.get("id", "worker")), worker)
    result = workforce.process_task(Task(content=task))
    return {
        "backend": "tender-agent-runtime",
        "mode": "executed",
        "task": task,
        "workers": workers,
        "result": result.get_result() if hasattr(result, "get_result") else str(result),
        "state": str(result.state) if getattr(result, "state", None) is not None else None,
    }
