"""MetaMeta input cartographer for Tender.

Maps each detected input into the Fishbowl Memory cognitive-map regions,
then stores the labels as a traceable DAOQL annotation event. The map is a
cognitive metaphor and a retrieval index, not a clinical brain diagnosis.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from .daoql import insert_edge, insert_event, list_events, write_audit

ANNOTATION_VERSION = "fishbowl-experience-1.0"
AGENT_ID = "metameta_cartographer"
SUMMARY_EVENT_TYPE = "subjective_experience_summary"
NODE_EVENT_TYPE = "subjective_experience_node"
EPISTEMIC_STATUS = "subjective_experience"

REGIONS = [
    {"id":"central_retrieval","name":"大脑中枢·检索","color":"#F4F1E8","side":"center","keywords":("怎么办","如何","下一步","选择","决定","找","检索","开始","任务","先做")},
    {"id":"hippocampus_index","name":"海马体·索引","color":"#5BCB8A","side":"right","keywords":("回忆","想不起来","记得","上次","曾经","检索","索引","找到","以前","那次")},
    {"id":"long_term_memory","name":"长期记忆库","color":"#D8A84E","side":"right","keywords":("事实","定义","公式","定理","概念","原理","知识点","昨天","周末","事件","课文","笔记","材料","资料")},
    {"id":"working_memory","name":"工作记忆","color":"#D57BD8","side":"right","keywords":("同时","记不住","忘了","刚才","步骤","容量","反复检查","一边","信息太多","转不过来")},
    {"id":"visual_cortex","name":"视觉皮层","color":"#5A9CF8","side":"right","keywords":("看到","看见","画面","图","视频","屏幕","颜色","图表","读题","视觉","表情")},
    {"id":"auditory_cortex","name":"听觉皮层","color":"#8E79E8","side":"right","keywords":("听到","声音","音频","语音","听力","老师说","同学说","讨论","交流","对话","讲课","播客")},
    {"id":"language_encoding","name":"语言编码","color":"#7B79F2","side":"right","keywords":("读","阅读","理解这句话","题目说","文本","语言","词","含义","编码","论文","文献","题目","内容","句子")},
    {"id":"language_expression","name":"语言中枢·表达","color":"#D8B35A","side":"left","keywords":("怎么说","表达","写出","说出来","沟通","汇报","讲清楚","解释","写作","发言")},
    {"id":"introspection_feedback","name":"内省·反馈","color":"#EF8BB6","side":"left","keywords":("我觉得","我是不是","为什么我","元认知","预测","反思","复盘","不确定","不知道","猜","状态","担心","自我评价","信心")},
    {"id":"limbic_emotion","name":"边缘系统·情绪","color":"#9DDA86","side":"left","keywords":("焦虑","害怕","难过","兴奋","生气","压力","心情","情绪","喜欢","讨厌","崩溃","不安","紧张","慌","怕")},
    {"id":"metabolic_governance","name":"代谢·治理","color":"#6650A8","side":"left","keywords":("困","累","疲劳","睡","饿","吃","头痛","心率","运动","生病","营养","熬夜","能量")},
]
REGION_BY_ID = {r["id"]: r for r in REGIONS}

REGION_FLOW = (
    ("visual_cortex", "working_memory", "perceived_into"),
    ("auditory_cortex", "working_memory", "perceived_into"),
    ("language_encoding", "working_memory", "encoded_into"),
    ("working_memory", "hippocampus_index", "indexed_by"),
    ("hippocampus_index", "long_term_memory", "consolidates_into"),
    ("limbic_emotion", "working_memory", "colors"),
    ("metabolic_governance", "central_retrieval", "energizes"),
    ("central_retrieval", "introspection_feedback", "monitored_by"),
    ("introspection_feedback", "language_expression", "expressed_as"),
)

EVENT_PRIORS = {
    "metacognition_jol": {"introspection_feedback": 1.2},
    "reflection": {"introspection_feedback": 1.2},
    "teacher_prediction": {"introspection_feedback": 0.9},
    "answer": {"long_term_memory": 0.8},
    "response": {"working_memory": 0.7},
    "ambient_feedback": {"introspection_feedback": 0.8},
    "mentalization_snapshot": {"introspection_feedback": 0.6},
    "preassessment_profile": {"introspection_feedback": 0.4},
}

EPISODE_MARKERS = ("昨天","今天","上次","那次","周末","曾经","记得","当时","刚才")
FACT_MARKERS = ("定义","公式","定理","概念","原理","事实","知识点","课文","笔记")

LIFE_TREE_BY_REGION = {
    "central_retrieval": {"stage":"trunk","label":"树干","meaning":"把输入接回当前选择与行动"},
    "hippocampus_index": {"stage":"roots","label":"根系","meaning":"把经验连接到可检索的过去"},
    "long_term_memory": {"stage":"trunk","label":"树干","meaning":"把事实与事件沉淀为长期连续性"},
    "working_memory": {"stage":"branches","label":"枝叶","meaning":"正在展开的有限工作空间"},
    "visual_cortex": {"stage":"branches","label":"枝叶","meaning":"视觉信息的进入路径"},
    "auditory_cortex": {"stage":"branches","label":"枝叶","meaning":"听觉信息的进入路径"},
    "language_encoding": {"stage":"branches","label":"枝叶","meaning":"把外部语言转为可理解的内部结构"},
    "language_expression": {"stage":"fruit","label":"结果","meaning":"把内部理解转化为可说、可写、可交付的表达"},
    "introspection_feedback": {"stage":"flower","label":"开花","meaning":"开始看见自己的认知过程与判断依据"},
    "limbic_emotion": {"stage":"roots","label":"根系","meaning":"情绪为记忆和选择提供底色"},
    "metabolic_governance": {"stage":"roots","label":"根系","meaning":"睡眠、营养与能量支撑高级认知"},
}


def region_catalog() -> list[dict]:
    return [{"id":r["id"],"name":r["name"],"color":r["color"],"side":r["side"]} for r in REGIONS]


def extract_text(payload: dict | None) -> str:
    payload = payload or {}
    for key in ("message","user_message","text","content","reflection","answer","note","transcript","ocr_text","audio_transcript"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

def _memory_type(text: str, region_ids: list[str]) -> dict:
    if "introspection_feedback" in region_ids:
        kind, label = "reflection", "自我预测与反思"
    elif "metabolic_governance" in region_ids:
        kind, label = "physiological_state", "生理与能量状态"
    elif "limbic_emotion" in region_ids:
        kind, label = "affective_state", "情绪与价值底色"
    elif "visual_cortex" in region_ids or "auditory_cortex" in region_ids:
        kind, label = "percept", "感知输入"
    elif "language_expression" in region_ids:
        kind, label = "expression", "语言表达"
    elif "working_memory" in region_ids:
        kind, label = "working_state", "当前工作状态"
    elif any(marker in text for marker in EPISODE_MARKERS):
        kind, label = "episode", "事件记忆"
    elif any(marker in text for marker in FACT_MARKERS):
        kind, label = "fact", "事实性记忆"
    elif "hippocampus_index" in region_ids or "long_term_memory" in region_ids:
        kind, label = "memory_reference", "记忆检索"
    else:
        kind, label = "indexed_input", "已索引输入"
    return {"kind": kind, "label": label}


def annotate_input(text: str, event_type: str = "user_input", payload: dict | None = None) -> dict:
    text = " ".join(str(text or "").split())
    scores: dict[str, float] = {}
    evidence: dict[str, list[str]] = {}
    for region in REGIONS:
        hits = [word for word in region["keywords"] if word in text]
        if hits:
            scores[region["id"]] = float(len(hits))
            evidence[region["id"]] = hits[:8]
    for rid, prior in EVENT_PRIORS.get(event_type, {}).items():
        scores[rid] = scores.get(rid, 0.0) + float(prior)
        evidence.setdefault(rid, []).append(f"event:{event_type}")
    if not scores:
        scores = {"central_retrieval": 0.8}
        evidence = {"central_retrieval": ["默认检索入口"]}
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:6]
    labels = []
    for rid, score in ranked:
        region = REGION_BY_ID[rid]
        confidence = round(min(0.97, 0.38 + score / (score + 4.0) * 0.5 + min(len(evidence.get(rid, [])), 3) * 0.02), 3)
        labels.append({
            "id": rid,
            "name": region["name"],
            "confidence": confidence,
            "evidence": evidence.get(rid, [])[:8],
            "color": region["color"],
            "side": region["side"],
        })
    primary = labels[0]
    life_tree = LIFE_TREE_BY_REGION.get(primary["id"], LIFE_TREE_BY_REGION["central_retrieval"])
    memory_type = _memory_type(text, [item["id"] for item in labels])
    return {
        "agent_id": AGENT_ID,
        "annotation_version": ANNOTATION_VERSION,
        "primary_region": primary,
        "regions": labels,
        "memory_type": memory_type,
        "life_tree": life_tree,
        "visual": {"node_color": primary["color"], "halo": primary["confidence"], "side": primary["side"]},
        "uncertainty": round(max(0.03, 1.0 - primary["confidence"]), 3),
        "boundary": "这是认知隐喻与检索标签，不是脑区诊断或心理测量结论。",
    }


def build_metameta_annotation_map(events: list[dict], now: datetime | None = None) -> dict:
    """Build the subjective experience map from derived nodes only.

    Raw DAOQL events remain objective facts. This map contains only
    `subjective_experience_node` records derived from those facts.
    """
    nodes = [e for e in events if e.get("event_type") == NODE_EVENT_TYPE]
    summaries = [e for e in events if e.get("event_type") == SUMMARY_EVENT_TYPE]
    region_counts: dict[str, int] = {}
    primary_counts: dict[str, int] = {}
    memory_counts: dict[str, int] = {}
    tree_counts: dict[str, int] = {}
    links = 0
    active = archived = 0
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    recent = []
    for event in nodes:
        payload = event.get("payload") or {}
        region = payload.get("region") or {}
        rid = region.get("id")
        if rid:
            region_counts[rid] = region_counts.get(rid, 0) + 1
        if payload.get("is_primary") and rid:
            primary_counts[rid] = primary_counts.get(rid, 0) + 1
        memory = payload.get("memory_type") or {}
        if memory.get("kind"):
            memory_counts[memory["kind"]] = memory_counts.get(memory["kind"], 0) + 1
        tree = payload.get("life_tree") or {}
        if tree.get("stage"):
            tree_counts[tree["stage"]] = tree_counts.get(tree["stage"], 0) + 1
        try:
            ts = datetime.fromisoformat(event.get("timestamp"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                active += 1
            else:
                archived += 1
        except Exception:
            archived += 1
        if len(recent) < 8:
            recent.append({
                "event_id": event.get("event_id"),
                "timestamp": event.get("timestamp"),
                "source_event_id": payload.get("source_event_id"),
                "region": region,
                "memory_type": memory,
                "life_tree": tree,
                "confidence": payload.get("confidence"),
                "epistemic_status": payload.get("epistemic_status"),
            })
    for summary in summaries:
        payload = summary.get("payload") or {}
        links += int(payload.get("region_link_count") or len(payload.get("region_links") or []))
    primary_region = max(primary_counts, key=primary_counts.get) if primary_counts else None
    return {
        "agent_id": AGENT_ID,
        "annotation_version": ANNOTATION_VERSION,
        "epistemic_status": EPISTEMIC_STATUS,
        "objective_source_event_count": len({(s.get("payload") or {}).get("source_event_id") for s in summaries if (s.get("payload") or {}).get("source_event_id")}),
        "decomposition_count": len(summaries),
        "total": len(nodes),
        "node_count": len(nodes),
        "link_count": links,
        "active": active,
        "archived": archived,
        "primary_region": primary_region,
        "primary_region_name": REGION_BY_ID.get(primary_region, {}).get("name") if primary_region else None,
        "region_counts": region_counts,
        "primary_region_counts": primary_counts,
        "memory_type_counts": memory_counts,
        "life_tree_counts": tree_counts,
        "recent": recent,
        "legend": region_catalog(),
        "boundary": "这是从客观事件派生出的主观体验图谱；节点表示解释路径，不是脑区诊断或客观事实。",
    }


def _existing_decomposition(student_id: str, source_event_id: str | None) -> dict | None:
    if not source_event_id:
        return None
    for event in reversed(list_events(student_id)):
        payload = event.get("payload") or {}
        if event.get("event_type") == SUMMARY_EVENT_TYPE and payload.get("source_event_id") == source_event_id:
            return event
    return None


def _region_event_payload(annotation: dict, source_event_id: str, source_event_type: str, decomposition_event_id: str, region: dict, index: int) -> dict:
    return {
        "agent_id": AGENT_ID,
        "annotation_version": ANNOTATION_VERSION,
        "epistemic_status": EPISTEMIC_STATUS,
        "derived": True,
        "source_event_id": source_event_id,
        "source_event_type": source_event_type,
        "decomposition_event_id": decomposition_event_id,
        "region": {"id": region["id"], "name": region["name"], "color": region["color"], "side": region["side"]},
        "confidence": region["confidence"],
        "uncertainty": round(1.0 - region["confidence"], 3),
        "evidence": region.get("evidence", []),
        "is_primary": index == 0,
        "memory_type": annotation["memory_type"],
        "life_tree": LIFE_TREE_BY_REGION.get(region["id"], annotation["life_tree"]),
        "boundary": "主观体验节点，由客观事件派生；可更正，不作为脑区诊断。",
    }


def decompose_and_store(student_id: str, text: str, *, source_event_id: str | None = None, source_event_type: str = "user_input", payload: dict | None = None, actor_id: str = AGENT_ID) -> dict:
    """Derive subjective life-tree nodes from one objective DAOQL event.

    The objective event is never modified. The agent writes separate derived
    events and links them back to the objective source.
    """
    text = " ".join(str(text or "").split())
    if not text and not EVENT_PRIORS.get(source_event_type):
        raise ValueError("text_required")
    existing = _existing_decomposition(student_id, source_event_id)
    if existing:
        return {
            "status": "already_decomposed",
            "event_id": existing.get("event_id"),
            "decomposition": existing.get("payload") or {},
        }
    annotation = annotate_input(text, source_event_type, payload)
    decomposition_event_id = "evt_" + uuid.uuid4().hex[:12]
    region_event_ids: dict[str, str] = {}
    node_events = []
    for index, region in enumerate(annotation["regions"]):
        node_payload = _region_event_payload(annotation, source_event_id or "", source_event_type, decomposition_event_id, region, index)
        node_id = insert_event({
            "event_type": NODE_EVENT_TYPE,
            "student_id": student_id,
            "payload": node_payload,
            "source": "metameta_cartographer",
            "provenance": {"actor_id": actor_id, "derived": True, "epistemic_status": EPISTEMIC_STATUS, "annotation_version": ANNOTATION_VERSION},
        })
        region_event_ids[region["id"]] = node_id
        node_events.append({"event_id": node_id, "region_id": region["id"], "is_primary": index == 0})
        if source_event_id:
            insert_edge(source_event_id, node_id, "experienced_as", region["confidence"], {
                "epistemic_status": EPISTEMIC_STATUS,
                "region_id": region["id"],
                "derivation": ANNOTATION_VERSION,
            })
    region_links = []
    for source_region, target_region, relation in REGION_FLOW:
        if source_region in region_event_ids and target_region in region_event_ids:
            insert_edge(region_event_ids[source_region], region_event_ids[target_region], relation, 0.65, {"subjective_experience": True})
            region_links.append({"source": region_event_ids[source_region], "target": region_event_ids[target_region], "relation": relation})
    summary_payload = {
        "agent_id": AGENT_ID,
        "annotation_version": ANNOTATION_VERSION,
        "epistemic_status": EPISTEMIC_STATUS,
        "derived": True,
        "objective_source_event_id": source_event_id,
        "source_event_id": source_event_id,
        "source_event_type": source_event_type,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_chars": len(text),
        "primary_region": annotation["primary_region"],
        "regions": annotation["regions"],
        "memory_type": annotation["memory_type"],
        "life_tree": annotation["life_tree"],
        "uncertainty": annotation["uncertainty"],
        "region_node_event_ids": region_event_ids,
        "region_nodes": node_events,
        "region_links": region_links,
        "region_link_count": len(region_links),
        "boundary": "从客观事件生成的主观体验解释；保留来源并可更正，不改变事实层。",
    }
    summary_event_id = insert_event({
        "event_id": decomposition_event_id,
        "event_type": SUMMARY_EVENT_TYPE,
        "student_id": student_id,
        "payload": summary_payload,
        "source": "metameta_cartographer",
        "provenance": {"actor_id": actor_id, "derived": True, "epistemic_status": EPISTEMIC_STATUS, "annotation_version": ANNOTATION_VERSION},
    })
    if source_event_id:
        insert_edge(source_event_id, summary_event_id, "yields_subjective_experience", annotation["primary_region"]["confidence"], {"epistemic_status": EPISTEMIC_STATUS})
    for node_id in region_event_ids.values():
        insert_edge(summary_event_id, node_id, "contains_experience_node", 0.9, {"epistemic_status": EPISTEMIC_STATUS})
    write_audit(actor_id, "metameta.decompose", student_id, {
        "event_id": summary_event_id,
        "source_event_id": source_event_id,
        "primary_region": annotation["primary_region"]["id"],
        "region_node_count": len(region_event_ids),
        "region_link_count": len(region_links),
    })
    return {
        "status": "stored",
        "event_id": summary_event_id,
        "region_node_event_ids": region_event_ids,
        "region_link_count": len(region_links),
        "decomposition": summary_payload,
    }


def annotate_and_store(*args, **kwargs):
    """Backward-compatible name for the decomposition pipeline."""
    return decompose_and_store(*args, **kwargs)


def maybe_decompose_event(event_id: str, event: dict) -> dict | None:
    """Lazy hook used after an objective DAOQL event is written."""
    event_type = event.get("event_type", "")
    if event_type in {NODE_EVENT_TYPE, SUMMARY_EVENT_TYPE, "metameta_annotation"}:
        return None
    text = extract_text(event.get("payload") or {})
    if not text and event_type not in EVENT_PRIORS:
        return None
    try:
        return decompose_and_store(
            event["student_id"],
            text,
            source_event_id=event_id,
            source_event_type=event_type,
            payload=event.get("payload") or {},
            actor_id="metameta_cartographer.auto",
        )
    except Exception:
        return None
