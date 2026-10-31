# -*- coding: utf-8 -*-
"""Generate AGENT_CATALOG.json and AGENT_INVENTORY.md from live code."""
from __future__ import annotations
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agent_catalog import agent_catalog
from app.agent_runtime import list_agents
from app.workbench import AGENT_CATALOG
from app.advisor_router import EXPERTS
from app.agent_marketplace import FIXED_AGENTS


def build(out_dir: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog = agent_catalog()
    json_path = out_dir / "AGENT_CATALOG.json"
    json_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fixed_ids = {a["agent_id"] for a in FIXED_AGENTS}
    runtime = catalog["execution_runtime"]
    lines = [
        "# Tender Agent 对齐清单",
        "",
        "本文件由 `scripts/build_agent_inventory.py` 从当前代码生成，是 Agent 文档的唯一对齐口径。",
        "",
        "## 0. 执行运行时",
        "",
        f"- Agent Runtime 可用：{runtime.get('available')}",
        f"- 执行层版本：{runtime.get('version', 'managed')}",
        f"- 默认执行层：{runtime.get('framework')}",
        f"- 模型就绪：{runtime.get('model_ready')}",
        "- DAOQL 继续负责事实、因果、授权、交易与审计，Agent Runtime 只负责执行与协作。",
        "",
        "## 1. 运行时 YAML Agent",
        "",
        "来源：`agents/*.yaml`；调用入口：`POST /agents/{agent_id}/invoke`。",
        "",
        "| Agent ID | 角色 | 层级 | 可调用 |",
        "|---|---|---|---|",
    ]
    for a in list_agents():
        surface = "C端固定辅助" if a["id"] in fixed_ids else "后台/兼容运行时"
        lines.append(f"| `{a['id']}` | {a.get('role', '')} | {surface} | 是 |")
    lines += [
        "",
        "## 2. C 端固定辅助 Agent",
        "",
        "来源：`app/agent_marketplace.py:FIXED_AGENTS`，且每个都有对应的运行时 YAML。",
        "",
        "| Agent ID | 名称 | 数据范围 | 运行时状态 |",
        "|---|---|---|---|",
    ]
    for a in FIXED_AGENTS:
        lines.append(f"| `{a['agent_id']}` | {a['name']} | {', '.join(a['data_scopes'])} | 已实现并可调用 |")
    lines += [
        "",
        "## 3. 工作台编排 Agent",
        "",
        "来源：`app/workbench.py:AGENT_CATALOG`；它们是多 Agent 工作台内的编排角色，不是市场商品。",
        "",
        "| Agent ID | 名称 | 职责 |",
        "|---|---|---|",
    ]
    for a in AGENT_CATALOG:
        lines.append(f"| `{a['id']}` | {a['name']} | {a['scope']} |")
    lines += [
        "",
        "## 4. MoA 路由顾问",
        "",
        "来源：`app/advisor_router.py:EXPERTS`；按对话与授权摘要选择 1–3 个，不共享原始数据。",
        "",
        "| ID | 名称 | 数据范围 |",
        "|---|---|---|",
    ]
    for a in EXPERTS:
        lines.append(f"| `{a['id']}` | {a['name']} | `{a['scope']}` |")
    lines += [
        "",
        "## 5. 市场专家 Agent",
        "",
        "- 市场专家 Agent 不是固定名单，由用户需求生成 AgentSpec 后写入 `expert_agents` 表。",
        "- 调用入口：`POST /agents/{agent_id}/invoke`。",
        "- 必须由 Owner 或已购买授权用户调用。",
        "- 已接入可插拔 Agent Runtime；没有模型时会回退到结构化 AgentSpec 输出。",
        "",
        "## 6. 多 Agent Workforce",
        "",
        "- 规划入口：`POST /workforce/plan`。",
        "- 默认 `execute=false`，只生成多 Agent 执行计划。",
        "- 只有显式设置运行时执行开关且请求 `execute=true` 才会启动。",
        "- 生产环境还必须经过 RBAC、预算、工具白名单和风险门禁。",
        "",
        "## 7. 当前真实边界",
        "",
        "- 固定辅助 Agent：运行时 YAML + Agent Runtime 执行已实现。",
        "- 专家 Agent 生成、上架与购买授权：已实现；支付为模拟状态。",
        "- 专家 Agent 调用：Agent Runtime 已接入，失败时回退结构化输出。",
        "- 多 Agent Workflow：已接入规划；自动执行默认关闭。",
        "- 工作台 Agent 与 MoA 顾问是不同层，不能与固定消费者 Agent 混为一类。",
    ]
    md_path = out_dir / "AGENT_INVENTORY.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    print(*build(target), sep="\n")
