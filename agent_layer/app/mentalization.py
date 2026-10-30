# -*- coding: utf-8 -*-
"""C-end mentalization layer.

Converts observable learning events and Tender state into evidence-backed,
non-clinical hypotheses about what a learner may need right now.
"""
from __future__ import annotations
from datetime import datetime, timezone
from math import exp
from .language_signals import analyze_language


EMOTION_TERMS = {
    "开心": (0.75, 0.55), "兴奋": (0.70, 0.80), "轻松": (0.55, 0.25),
    "平静": (0.35, 0.20), "有动力": (0.65, 0.55), "满意": (0.60, 0.30),
    "焦虑": (-0.55, 0.80), "紧张": (-0.45, 0.75), "害怕": (-0.60, 0.80),
    "挫败": (-0.65, 0.65), "烦躁": (-0.55, 0.75), "压力": (-0.50, 0.70),
    "难过": (-0.70, 0.35), "低落": (-0.65, 0.25), "疲惫": (-0.45, 0.18),
    "困": (-0.35, 0.15), "无聊": (-0.40, 0.20), "走神": (-0.25, 0.35),
    "不想学": (-0.60, 0.35), "崩溃": (-0.80, 0.90), "孤独": (-0.60, 0.25),
}


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _payload_text(payload: dict) -> str:
    for key in ("text", "message", "content", "reflection", "answer", "note"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def infer_emotion(events: list[dict]) -> dict:
    """Infer a weak valence-arousal estimate from explicit labels or text.

    This is a context signal, not an emotion diagnosis.
    """
    vals, ars, evidence = [], [], []
    for event in events:
        payload = event.get("payload", {}) or {}
        if payload.get("valence") is not None and payload.get("arousal") is not None:
            try:
                vals.append(_clip(float(payload["valence"]), -1.0, 1.0))
                ars.append(_clip(float(payload["arousal"]), 0.0, 1.0))
                evidence.append(event.get("event_id", ""))
                continue
            except (TypeError, ValueError):
                pass
        text = _payload_text(payload)
        if not text:
            continue
        matched = False
        v_sum, a_sum = 0.0, 0.0
        for term, (v, a) in EMOTION_TERMS.items():
            if term in text:
                v_sum += v
                a_sum += a
                matched = True
        if matched:
            vals.append(_clip(v_sum / max(1, sum(1 for term in EMOTION_TERMS if term in text)), -1, 1))
            ars.append(_clip(a_sum / max(1, sum(1 for term in EMOTION_TERMS if term in text)), 0, 1))
            evidence.append(event.get("event_id", ""))

    if not vals:
        return {
            "valence": 0.0,
            "arousal": 0.0,
            "label": "未观测",
            "confidence": 0.0,
            "evidence_count": 0,
            "evidence_refs": [],
            "note": "情绪上下文不足，不进行推断。",
        }

    valence = sum(vals) / len(vals)
    arousal = sum(ars) / len(ars)
    if valence >= 0.20 and arousal >= 0.50:
        label = "积极唤醒"
    elif valence >= 0.20:
        label = "平稳积极"
    elif arousal >= 0.55:
        label = "紧张或高负荷"
    elif arousal <= 0.25 and valence < 0.0:
        label = "低能量"
    else:
        label = "中性或混合"
    confidence = round(min(0.88, 0.30 + 0.10 * len(vals)), 3)
    return {
        "valence": round(valence, 3),
        "arousal": round(arousal, 3),
        "label": label,
        "confidence": confidence,
        "evidence_count": len(vals),
        "evidence_refs": [x for x in evidence if x][-8:],
        "note": "由可观察文本或显式自述得到，只作为学习支持上下文。",
    }


def _confidence(base: float, n_events: int, deviation: float) -> float:
    return round(min(0.90, base + 0.015 * min(n_events, 20) + 0.10 * _clip(deviation, 0, 1)), 3)


def build_mentalization(student_id: str, state: dict, events: list[dict]) -> dict:
    knowledge = state.get("knowledge", {}) or {}
    meta = state.get("metacognition", {}) or {}
    baseline = state.get("baseline", {}) or {}
    emotion = infer_emotion(events)
    recent_text = "\n".join(
        _payload_text(event.get("payload", {}) or {})
        for event in events[-8:]
        if _payload_text(event.get("payload", {}) or {})
    )
    language_signals = analyze_language(recent_text, context={"event_count": len(events), "source": "mentalization"})

    mastery = float(knowledge.get("mastery", 0.5) or 0.5)
    bias = float(meta.get("jol_bias", 0.0) or 0.0)
    hesitation = float(meta.get("hesitation", 0.0) or 0.0)
    fit = float(baseline.get("arrangement_fit", 0.5) or 0.5)
    n_events = len(events)

    hypotheses = []
    if mastery < 0.60:
        hypotheses.append({
            "id": "knowledge_connection",
            "label": "知识连接可能尚未稳定",
            "score": _confidence(0.48, n_events, 0.60 - mastery),
            "evidence": [f"近期掌握度约 {mastery:.2f}", f"共记录 {n_events} 条学习事件"],
            "support_hint": "先确认卡在哪个连接，再给最小提示和复述机会。",
        })
    if abs(bias) >= 0.15:
        hypotheses.append({
            "id": "metacognitive_calibration",
            "label": "元认知校准可能存在偏差",
            "score": _confidence(0.50, n_events, abs(bias)),
            "evidence": [f"预测与实际表现偏差约 {bias:+.2f}"],
            "support_hint": "先预测，再作答，之后只比较预测与实际。",
        })
    if hesitation >= 0.55:
        hypotheses.append({
            "id": "hesitation_or_load",
            "label": "犹豫或认知负荷可能正在升高",
            "score": _confidence(0.48, n_events, hesitation - 0.55),
            "evidence": [f"近期响应犹豫指标约 {hesitation:.2f}"],
            "support_hint": "先问卡点，再决定提示、拆解还是短暂停顿。",
        })
    if emotion["label"] in {"紧张或高负荷", "低能量"}:
        hypotheses.append({
            "id": "emotion_cognition_fit",
            "label": "情绪状态可能正在占用学习资源",
            "score": _confidence(0.42, int(emotion["evidence_count"]) + n_events, emotion["arousal"]),
            "evidence": [f"情绪上下文：{emotion['label']}", "该判断只用于调整支持方式"],
            "support_hint": "降低单步任务强度，先恢复可控感，再继续。",
        })
    if fit < 0.50:
        hypotheses.append({
            "id": "arrangement_fit",
            "label": "当前安排与个人节律可能不完全匹配",
            "score": _confidence(0.44, n_events, 0.50 - fit),
            "evidence": [f"安排匹配度约 {fit:.2f}"],
            "support_hint": "尝试缩短连续学习段，并把任务放到更合适的时段。",
        })

    existing_ids = {item["id"] for item in hypotheses}
    for language_hypothesis in language_signals.get("hypotheses", []):
        if language_hypothesis["id"] in {"insufficient_language_evidence"}:
            continue
        mapped_id = {"safety_check_required": "safety_check_required",
                     "other_mind_inference_active": "mentalizing_language_signal",
                     "action_resource_threat": "language_action_resource",
                     "calibration_or_knowledge_gap": "language_calibration_gap",
                     "task_help_request": "language_task_help"}.get(language_hypothesis["id"], language_hypothesis["id"])
        if mapped_id in existing_ids:
            continue
        evidence = [span["text"] for span in language_hypothesis.get("evidence_spans", [])]
        hypotheses.append({
            "id": mapped_id,
            "label": language_hypothesis["label"],
            "score": language_hypothesis["confidence"],
            "evidence": evidence or ["语言证据不足，仅保留为观察假设"],
            "support_hint": language_hypothesis["next_probe"],
            "source": "language_signal_model",
            "alternative_explanations": language_hypothesis.get("alternative_explanations", []),
        })
        existing_ids.add(mapped_id)

    if not hypotheses:
        hypotheses.append({
            "id": "stable_state",
            "label": "当前状态相对稳定",
            "score": _confidence(0.50, n_events, 0.0),
            "evidence": ["近期没有出现明显的知识、校准、负荷或节律异常"],
            "support_hint": "保持节奏，并做一次迁移或自我解释。",
        })

    hypotheses.sort(key=lambda item: item["score"], reverse=True)
    top = hypotheses[0]
    support_options = [{
        "id": item["id"],
        "label": item["support_hint"],
        "type": "protection" if item["id"] == "safety_check_required" else ("reflection" if item["id"] in {"metacognitive_calibration", "hesitation_or_load", "mentalizing_language_signal"} else "adjustment"),
        "evidence_refs": item["evidence"],
    } for item in hypotheses[:3]]

    question_map = {
        "knowledge_connection": "刚才最卡的是理解题意、找到方法，还是无法确认自己做对了没有？",
        "metacognitive_calibration": "作答前你预估自己对多少？现在回看，差距来自哪一步？",
        "hesitation_or_load": "你在哪一刻停顿最久？当时脑中缺的是信息、方法，还是安全感？",
        "emotion_cognition_fit": "如果先把任务缩小到现在能做的一步，你更想先处理哪一部分？",
        "arrangement_fit": "今天哪个时段你最容易进入状态？连续学习多久后开始下降？",
        "stable_state": "这次你用的是什么方法？下一次希望保留哪一步？",
        "mentalizing_language_signal": "对方实际说了什么，哪些是你从语气或表情里推测的？",
        "language_action_resource": "现在有没有一个十分钟内能完成、又不会增加压力的最小动作？",
        "language_calibration_gap": "作答前你有多确定？真实结果和你的预期差在哪里？",
        "language_task_help": "你现在最需要的是提示、讲解、练习，还是先整理问题？",
        "safety_check_required": "你现在是否处于即时危险中，身边是否有可以立即联系的人？",
    }

    recent_refs = [event.get("event_id") for event in events[-8:] if event.get("event_id")]
    return {
        "student_id": student_id,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "summary": top["label"],
        "confidence": top["score"],
        "hypotheses": hypotheses,
        "emotion_context": emotion,
        "language_signals": language_signals,
        "state_snapshot": {
            "mastery": round(mastery, 3),
            "jol_bias": round(bias, 3),
            "hesitation": round(hesitation, 3),
            "arrangement_fit": round(fit, 3),
            "event_count": n_events,
        },
        "support_options": support_options,
        "reflection_prompt": question_map.get(top["id"], "此刻最值得被理解的是什么？"),
        "evidence_refs": recent_refs,
        "boundary": "这是用于学习支持的状态假设，不是心理或医学诊断；语言只提供弱证据，不能单独决定知识掌握、人格或临床结论。用户可以纠正、撤回或要求导出。",
    }
