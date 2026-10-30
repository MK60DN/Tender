# -*- coding: utf-8 -*-
"""Canonical, code-derived Agent catalog used by API and documentation."""
from __future__ import annotations

from .advisor_router import EXPERTS
from .agent_marketplace import FIXED_AGENTS, list_marketplace
from .agent_runtime import list_agents, runtime_status
from .workbench import AGENT_CATALOG

FIXED_IDS = {a["agent_id"] for a in FIXED_AGENTS}


def agent_catalog() -> dict:
    runtime_items = list_agents()
    runtime_ids = [item.get("id") for item in runtime_items if item.get("id")]
    runtime_id_set = set(runtime_ids)
    duplicate_runtime_ids = sorted({agent_id for agent_id in runtime_ids if runtime_ids.count(agent_id) > 1})

    runtime = []
    for item in runtime_items:
        runtime.append({
            "id": item.get("id"),
            "role": item.get("role"),
            "tools": item.get("tools", []),
            "policy": item.get("policy", {}),
            "input": item.get("input", []),
            "output": item.get("output", []),
            "surface": "consumer_fixed" if item.get("id") in FIXED_IDS else "internal_or_compatibility",
            "invocable": item.get("id") in FIXED_IDS and item.get("id") not in duplicate_runtime_ids,
            "source": "agents/*.yaml",
        })

    fixed = []
    missing_fixed_ids = []
    for item in FIXED_AGENTS:
        implemented = item["agent_id"] in runtime_id_set
        if not implemented:
            missing_fixed_ids.append(item["agent_id"])
        fixed.append({
            **item,
            "runtime_agent_id": item["agent_id"],
            "runtime_status": "implemented" if implemented else "missing_runtime_spec",
            "invocable": implemented,
            "invoke_endpoint": f"/agents/{item['agent_id']}/invoke",
        })

    workbench = [
        {**item, "surface": "workbench_orchestration", "source": "app/workbench.py:AGENT_CATALOG"}
        for item in AGENT_CATALOG
    ]
    advisors = [{
        "id": item["id"],
        "name": item["name"],
        "scope": item["scope"],
        "surface": "moa_advisor",
        "source": "app/advisor_router.py:EXPERTS",
    } for item in EXPERTS]
    market = [{
        "agent_id": item["agent_id"],
        "name": item["name"],
        "category": item["category"],
        "owner_id": item["owner_id"],
        "price": item["price"],
        "status": item["status"],
        "surface": "expert_marketplace",
        "invocable": item["status"] == "published",
        "access": "purchase_required",
        "source": "app/agent_marketplace.py:expert_agents",
    } for item in list_marketplace()["expert_agents"]]

    status = runtime_status()
    return {
        "product": "Tender",
        "catalog_version": "6.2",
        "execution_runtime": {
            "framework": "tender-agent-runtime",
            "pluggable": True,
            "available": bool(status.get("available")),
            "model_ready": bool(status.get("model_ready")),
            "workforce_execution": "gated",
        },
        "counts": {
            "runtime_yaml_agents": len(runtime),
            "fixed_consumer_agents": len(fixed),
            "workbench_agents": len(workbench),
            "moa_advisors": len(advisors),
            "marketplace_expert_agents": len(market),
        },
        "integrity": {
            "duplicate_runtime_ids": duplicate_runtime_ids,
            "missing_fixed_runtime_specs": missing_fixed_ids,
            "ok": not duplicate_runtime_ids and not missing_fixed_ids,
        },
        "runtime_yaml_agents": runtime,
        "fixed_consumer_agents": fixed,
        "workbench_orchestration_agents": workbench,
        "moa_advisors": advisors,
        "marketplace_expert_agents": market,
        "note": "这是由当前代码生成的 Agent 总目录。运行时 YAML、工作台编排、MoA 顾问和市场专家是四个不同层次，不能混称为同一类 Agent。",
    }
