"""Bounded Tender context package for grounded agent replies."""
from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

from .daoql import list_events
from .knowledge_context import build_knowledge_context
from .mentalization import build_mentalization
from .preassessment import latest_preassessment
from .tender import compute_state

CONTEXT_VERSION = "tender-context-1.4"


def _json_safe(value):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _event_digest(events: list[dict]) -> list[dict]:
    fields = (
        "kind",
        "task_hint",
        "app_category",
        "feedback",
        "correct",
        "response_time_ms",
        "action",
        "result",
        "agent_ids", "primary_region", "regions", "memory_type", "life_tree", "annotation_version",
    )
    result = []
    for event in events[-12:]:
        payload = event.get("payload") or {}
        digest = {key: payload[key] for key in fields if key in payload}
        result.append({
            "event_type": event.get("event_type"),
            "timestamp": event.get("timestamp"),
            "summary": digest,
        })
    return result


def _preassessment_digest(profile: dict | None) -> dict:
    if not profile:
        return {"available": False, "note": "尚未完成首次预检测"}
    attention = profile.get("attention_profile") or {}
    correction = profile.get("cognitive_correction_plan") or {}
    return {
        "available": True,
        "profile_version": profile.get("profile_version"),
        "big_five": {
            key: {"label": value.get("label"), "score": value.get("score"), "band": value.get("band")}
            for key, value in (profile.get("big_five") or {}).items()
        },
        "mbti_type_hint": (profile.get("mbti_preference") or {}).get("type_hint"),
        "jungian_top": (profile.get("jungian_functions") or {}).get("top_functions", []),
        "jungian_less_preferred": (profile.get("jungian_functions") or {}).get("less_preferred", []),
        "attention_profile": {
            "capture": attention.get("capture_hypotheses", []),
            "sustain": attention.get("sustain_hypotheses", []),
            "leakage": attention.get("leakage_hypotheses", []),
            "recovery": attention.get("recovery_preferences", []),
            "scaffolds": attention.get("scaffold_suggestions", []),
            "boundary": attention.get("boundary"),
        },
        "cognitive_correction_plan": {
            "items": [
                {
                    "id": item.get("id"),
                    "pattern": item.get("pattern_hypothesis"),
                    "trigger": item.get("trigger"),
                    "practice": item.get("correction_practice"),
                    "success_evidence": item.get("success_evidence"),
                }
                for item in correction.get("items", [])[:3]
            ],
            "safe_exit": correction.get("safe_exit"),
        },
    }


def build_tender_context(student_id: str, user_message: str | None = None, task_hint: str | None = None) -> dict[str, Any]:
    events = list_events(student_id)
    if not task_hint:
        for event in reversed(events):
            hint = (event.get("payload") or {}).get("task_hint")
            if hint:
                task_hint = str(hint)
                break
    state = compute_state(student_id, events)
    mentalization = build_mentalization(student_id, state, events)
    preassessment = _preassessment_digest(latest_preassessment(student_id))
    knowledge = build_knowledge_context(user_message or "", task_hint, events)
    hypotheses = mentalization.get("hypotheses") or []
    return _json_safe({
        "context_version": CONTEXT_VERSION,
        "student_id": student_id,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "event_count": len(events),
        "preassessment": preassessment,
        "state": {
            "mastery": state.get("knowledge", {}).get("mastery"),
            "cognitive_theta": state.get("cognitive", {}).get("theta"),
            "uncertainty": state.get("cognitive", {}).get("uncertainty"),
            "jol_bias": state.get("metacognition", {}).get("jol_bias"),
            "hesitation": state.get("metacognition", {}).get("hesitation"),
            "metacognition_profile": state.get("metacognition", {}).get("profile"),
            "arrangement_fit": state.get("baseline", {}).get("arrangement_fit"),
            "baseline_model": state.get("baseline", {}).get("baseline_model"),
            "rhythm": state.get("baseline", {}).get("rhythm"),
            "group": state.get("group", {}),
            "observer": state.get("observer", {}),
            "emotion": state.get("emotion", {}),
        },
        "knowledge": knowledge,
        "mentalization": {
            "summary": mentalization.get("summary"),
            "confidence": mentalization.get("confidence"),
            "hypotheses": [
                {
                    "label": item.get("label"),
                    "score": item.get("score"),
                    "evidence": item.get("evidence", [])[:3],
                    "support_hint": item.get("support_hint"),
                }
                for item in hypotheses[:3]
            ],
            "reflection_prompt": mentalization.get("reflection_prompt"),
            "boundary": mentalization.get("boundary"),
        },
        "recent_events": _event_digest(events),
        "freshness": {
            "has_preassessment": preassessment["available"],
            "has_behavior_events": bool(events),
            "state_is_evidence_based": len(events) >= 3,
        },
        "digest": {
            "context_version": CONTEXT_VERSION,
            "event_count": len(events),
            "preassessment_available": preassessment["available"],
            "attention_available": bool(preassessment.get("attention_profile", {}).get("leakage")),
            "mentalization_summary": mentalization.get("summary"),
            "hypothesis_count": len(hypotheses),
            "knowledge_available": knowledge.get("available", False),
            "knowledge_node": ((knowledge.get("matches") or [{}])[0].get("name") if knowledge.get("available") and knowledge.get("match_method") == "topic_match" else None),
            "knowledge_subject": knowledge.get("subject_name"),
            "knowledge_ambiguous": bool(knowledge.get("subject_ambiguous")),
            "major_available": bool((knowledge.get("major") or {}).get("available")),
            "major_name": (((knowledge.get("major") or {}).get("matches") or [{}])[0].get("name") if (knowledge.get("major") or {}).get("available") else None),
            "career_intent": bool((knowledge.get("career") or {}).get("intent_detected")),
            "baseline_available": bool((state.get("baseline", {}).get("baseline_model") or {}).get("deviation_mean") is not None),
            "rhythm_available": bool((state.get("baseline", {}).get("rhythm") or {}).get("主导节律")),
            "group_clustering": state.get("group", {}).get("clustering"),
            "metameta_r": (state.get("observer", {}).get("teacher_metameta") or {}).get("metameta_r"),
            "subjective_experience_nodes": (state.get("observer", {}).get("input_map") or {}).get("total", 0),
            "subjective_experience_primary_region": (state.get("observer", {}).get("input_map") or {}).get("primary_region"),
            "metacognition_auc": (state.get("metacognition", {}).get("profile") or {}).get("元认知敏感性AUC"),
        },
        "boundary": "上下文是用于学习支持的可更正假设，不是诊断；当前用户消息和真实结果优先于历史模型。",
    })


def format_tender_context(context: dict[str, Any] | None) -> str:
    if not context:
        return "Tender 尚未提供状态上下文。请说明信息不足，不要假装了解用户状态。"
    pre = context.get("preassessment") or {}
    state = context.get("state") or {}
    mental = context.get("mentalization") or {}
    knowledge = context.get("knowledge") or {}
    lines = [
        "【Tender 状态上下文｜可更正假设】",
        f"上下文版本：{context.get('context_version')}；事件数：{context.get('event_count')}",
        "规则：当前用户消息和真实结果优先于历史模型；有冲突时说明不确定；不要向用户暴露字段名、模型或内部流程。",
    ]
    if pre.get("available"):
        attention = pre.get("attention_profile") or {}
        lines.append(f"人格先验：MBTI偏好代码={pre.get('mbti_type_hint')}；八维更常用={pre.get('jungian_top')}")
        lines.append(f"注意捕获={attention.get('capture')}")
        lines.append(f"注意维持={attention.get('sustain')}")
        lines.append(f"注意泄漏={attention.get('leakage')}")
        lines.append(f"恢复偏好={attention.get('recovery')}")
        correction = pre.get("cognitive_correction_plan") or {}
        if correction.get("items"):
            lines.append("认知矫正练习：" + "；".join(
                f"{item.get('pattern')} -> {item.get('practice')}（有效证据：{item.get('success_evidence')}）"
                for item in correction["items"]
            ))
    else:
        lines.append("预检测：尚未完成；不要假设用户人格或注意成本。")
    if knowledge.get("available"):
        matches = knowledge.get("matches") or []
        if knowledge.get("subject_ambiguous"):
            lines.append("知识体系：存在学科歧义，候选学科=" + "、".join(knowledge.get("subject_names") or []) + "；先确认学科再使用具体节点。")
        elif matches and knowledge.get("match_method") == "subject_fallback":
            candidates = "、".join(item.get("name", "") for item in matches)
            lines.append(f"学科知识：学科={knowledge.get('subject_name')}；具体知识点待确认；候选单元={candidates}")
        elif matches:
            lines.append(f"学科知识：学科={knowledge.get('subject_name')}；命中方式={knowledge.get('match_method')}")
        for match in (matches[:2] if knowledge.get("match_method") == "topic_match" else []):
            path_names = " > ".join(item.get("name", "") for item in match.get("path", []))
            prerequisites = "、".join(item.get("name", "") for item in match.get("prerequisites", [])) or "无直接先修记录"
            next_nodes = "、".join(item.get("name", "") for item in match.get("next_nodes", [])) or "无推荐后续"
            modes = "、".join(item.get("name", "") for item in match.get("question_modes", [])) or "未记录"
            mastery = match.get("learner_mastery") or {}
            lines.append(
                f"知识节点：{match.get('name')}；路径={path_names}；先修={prerequisites}；后续={next_nodes}；"
                f"常见任务={modes}；节点掌握度={mastery.get('value')}（观测{mastery.get('observations')}）"
            )
        major = knowledge.get("major") or {}
        for match in (major.get("matches") or [])[:2]:
            courses = "、".join(item.get("course_name", "") for item in match.get("courses", [])[:6]) or "课程种子未覆盖"
            competencies = "、".join(match.get("competencies", [])[:5]) or "未记录"
            lines.append(f"专业路径：{match.get('code')} {match.get('name')}；课程种子={courses}；能力标签={competencies}")
        career = knowledge.get("career") or {}
        if career.get("intent_detected"):
            occupation_titles = "、".join(item.get("title", "") for item in career.get("matches", [])) or "暂无匹配的具体职业"
            dimensions = "、".join(item.get("name_zh", "") for item in career.get("riasec_dimensions", []))
            lines.append(f"职业探索：具体职业={occupation_titles}；RIASEC兴趣维度={dimensions}")
    else:
        lines.append("知识体系：未命中具体学科、专业或职业节点；不要假设用户正在学什么。")
    lines.append(
        "近期状态：掌握度={mastery}；元认知偏差={jol}；犹豫={hesitation}；安排匹配={fit}；情绪上下文={emotion}".format(
            mastery=state.get("mastery"),
            jol=state.get("jol_bias"),
            hesitation=state.get("hesitation"),
            fit=state.get("arrangement_fit"),
            emotion=(state.get("emotion") or {}).get("label"),
        )
    )
    metacognition_profile = state.get("metacognition_profile") or {}
    if metacognition_profile.get("元认知敏感性AUC") is not None:
        lines.append(
            f"元认知校准：敏感性AUC={metacognition_profile.get('元认知敏感性AUC')}；"
            f"偏差={metacognition_profile.get('元认知偏差')}；d'={metacognition_profile.get('d_prime')}"
        )
    rhythm = state.get("rhythm") or {}
    baseline_model = state.get("baseline_model") or {}
    group = state.get("group") or {}
    observer = state.get("observer") or {}
    if rhythm.get("主导节律") or baseline_model.get("deviation_mean") is not None:
        lines.append(
            f"节律与个人基线：主导节律={rhythm.get('主导节律')}；R24={rhythm.get('日内强度R24')}；"
            f"R168={rhythm.get('周内强度R168')}；节律平衡B={rhythm.get('节律平衡B')}；"
            f"基线偏离均值={baseline_model.get('deviation_mean')}；最大偏离={baseline_model.get('deviation_max')}"
        )
    if group:
        lines.append(f"群体结构：聚类={group.get('clustering')}；桥接比例={group.get('bridge_ratio')}")
    metameta = observer.get("teacher_metameta") or {}
    if metameta.get("metameta_r") is not None:
        lines.append(f"教师元元校准：metameta_r={metameta.get('metameta_r')}；样本={metameta.get('n')}")
    input_map = observer.get("input_map") or {}
    if input_map.get("total"):
        recent_regions = []
        for item in (input_map.get("recent") or [])[:3]:
            region = item.get("region") or item.get("primary_region") or {}
            tree = item.get("life_tree") or {}
            if region.get("name"):
                recent_regions.append(f"{region.get('name')}→{tree.get('label', '未映射')}")
        lines.append(
            f"生命树主观体验图谱：体验节点={input_map.get('total')}；分解次数={input_map.get('decomposition_count')}；活跃={input_map.get('active')}；"
            f"归档={input_map.get('archived')}；主要区域={input_map.get('primary_region_name')}；"
            f"最近标签={'、'.join(recent_regions) or '无'}"
        )
    hypotheses = mental.get("hypotheses") or []
    if hypotheses:
        lines.append("当前主要假设：" + "；".join(
            f"{item.get('label')}（{item.get('score')}，证据：{item.get('evidence')}，支持：{item.get('support_hint')}）"
            for item in hypotheses[:2]
        ))
    else:
        lines.append("当前主要假设：证据不足")
    recent = context.get("recent_events") or []
    if recent:
        lines.append("最近事件：" + "；".join(
            f"{item.get('event_type')}={item.get('summary')}" for item in recent[-5:]
        ))
    lines.append("回答要求：当用户询问自己的状态或怎么办时，先给1–2个最可能的状态假设与依据，再给一个最小行动；如果证据不足要直说。")
    return "\n".join(lines)
