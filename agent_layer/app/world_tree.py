"""World-tree projection over DAOQL events and derived experience nodes."""
from __future__ import annotations

from collections import Counter

from .daoql import list_events
from .golden_bias import build_golden_bias
from .metameta_cartographer import build_metameta_annotation_map
from .preassessment import big_five_change_state, latest_preassessment

TREE_VERSION = "world-tree-1.0"

BRANCH_MAP = {
    "input_branch": {"label": "输入枝", "regions": ["visual_cortex", "auditory_cortex", "language_encoding"]},
    "memory_branch": {"label": "记忆枝", "regions": ["working_memory", "hippocampus_index", "long_term_memory"]},
    "regulation_branch": {"label": "调节枝", "regions": ["limbic_emotion", "metabolic_governance"]},
    "integration_branch": {"label": "整合与反思枝", "regions": ["central_retrieval", "introspection_feedback"]},
    "expression_branch": {"label": "表达枝", "regions": ["language_expression"]},
}

LOCAL_AXIS = {
    "visual_cortex": "清晰 / 模糊",
    "auditory_cortex": "注意 / 忽略",
    "language_encoding": "字面 / 推断",
    "working_memory": "保持 / 更新或超载",
    "hippocampus_index": "熟悉 / 新颖",
    "long_term_memory": "提取 / 编码",
    "limbic_emotion": "安全 / 威胁",
    "metabolic_governance": "可投入 / 需恢复",
    "central_retrieval": "可达 / 阻塞",
    "introspection_feedback": "确定 / 不确定",
    "language_expression": "表达 / 保留",
}

FLOWER_EVENTS = {"response", "reflection", "ambient_dialogue_reply", "teacher_task_completed", "teaching_task_completed"}
OUTCOME_EVENTS = {"answer", "baseline", "metacognition_jol", "ambient_feedback", "assessment_result"}

GOLDEN_RATIO_LENS = {
    "status": "design_hypothesis_not_scientific_law",
    "balances": [
        "客观输入与主观整合",
        "内部生长与外部开花",
        "探索与巩固",
        "稳定基线与新经验",
        "共享枝与私人边界",
        "支持介入与用户自主",
    ],
    "notice": "黄金比只作为视觉、节律与交互比例的设计假设；不用于人格评分、能力预测或关系匹配结论。",
}


def _counter(events: list[dict], key: str) -> dict:
    return dict(Counter(str((event.get("payload") or {}).get(key) or "unknown") for event in events))


def build_world_tree(student_id: str) -> dict:
    events = list_events(student_id)
    experience_map = build_metameta_annotation_map(events)
    profile = latest_preassessment(student_id)
    pulse = big_five_change_state(student_id)
    golden_bias = build_golden_bias(student_id)
    region_counts = experience_map.get("region_counts", {})
    region_by_id = {item["id"]: item for item in experience_map.get("legend", [])}
    branches = []
    for branch_id, branch in BRANCH_MAP.items():
        nodes = []
        for region_id in branch["regions"]:
            region = region_by_id.get(region_id, {"id": region_id, "name": region_id, "color": "#8A8F95"})
            count = int(region_counts.get(region_id, 0))
            nodes.append({
                "node_id": region_id,
                "label": region.get("name", region_id),
                "color": region.get("color"),
                "observation_count": count,
                "local_state_axis": LOCAL_AXIS.get(region_id, "未定义 / 未定义"),
                "local_state_status": "insufficient_evidence" if count == 0 else "exploratory",
                "evidence_scope": "derived_subjective_experience",
            })
        branches.append({"branch_id": branch_id, "label": branch["label"], "nodes": nodes})
    world_entry = ((profile or {}).get("world_interface") or {}).get("world_entry") or {}
    gateway = ((profile or {}).get("world_interface") or {}).get("gateway") or {}
    flowers = [event for event in events if event.get("event_type") in FLOWER_EVENTS]
    outcomes = [event for event in events if event.get("event_type") in OUTCOME_EVENTS]
    event_type_counts = dict(Counter(str(event.get("event_type") or "unknown") for event in events))
    return {
        "tree_version": TREE_VERSION,
        "student_id": student_id,
        "roots": {
            "label": "DAOQL 客观事件根系",
            "event_count": len(events),
            "event_types": event_type_counts,
            "sources": _counter(events, "source"),
            "boundary": "DAOQL 保存客观事件、来源和审计，不保存主观体验本身。",
        },
        "trunk": {
            "label": "Agent Bridge 与有限接触面",
            "world_entry": world_entry,
            "gateway": gateway,
            "big_five_pulse_available": pulse.get("available", False),
            "relationship_support": pulse.get("relationship_support", []),
            "boundary": "世界入口与心理资源是支持假设，不是能力、诊断或固定人格。",
        },
        "canopy": {
            "label": "生命树树冠",
            "branches": branches,
            "experience_nodes": experience_map.get("total", 0),
            "active": experience_map.get("active", 0),
            "archived": experience_map.get("archived", 0),
            "primary_region": experience_map.get("primary_region"),
            "primary_region_name": experience_map.get("primary_region_name"),
        },
        "flowers": {
            "label": "开花事件",
            "count": len(flowers),
            "recent": [
                {"event_type": event.get("event_type"), "timestamp": event.get("timestamp")}
                for event in flowers[-8:]
            ],
        },
        "outcomes": {
            "label": "结果回流",
            "count": len(outcomes),
            "recent": [
                {"event_type": event.get("event_type"), "timestamp": event.get("timestamp")}
                for event in outcomes[-8:]
            ],
        },
        "shared_branches": {
            "status": "authorization_required",
            "implementation": "group_chat.shared_branch_store",
            "rule": "只连接全部参与者明确授权的共同事实、目标、任务、承诺和结果；不得共享完整私人生命树。",
            "allowed_categories": ["shared_fact", "shared_goal", "shared_task", "shared_commitment", "shared_outcome"],
        },
        "golden_ratio_lens": {**GOLDEN_RATIO_LENS, "dynamic_regulator": golden_bias},
        "boundary": "世界树是从客观事件派生的可更正体验视图，不是脑区诊断、量子脑证据或关系匹配评分。",
    }