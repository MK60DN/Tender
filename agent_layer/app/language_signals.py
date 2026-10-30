# -*- coding: utf-8 -*-
"""Deterministic language-signal extraction for Tender.

This module detects observable linguistic evidence. It does not diagnose the
speaker and does not update knowledge mastery from wording alone.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

MODEL_VERSION = "tender-language-signals-1.0"

RULES = {
    "explicit_affect": {
        "label": "显式情绪表达",
        "terms": ["焦虑", "紧张", "害怕", "难受", "烦躁", "崩溃", "压力", "孤独", "委屈", "生气", "疲惫", "累", "低落"],
        "confidence": 0.72,
    },
    "uncertainty": {
        "label": "不确定性或低把握",
        "terms": ["不知道", "不确定", "没把握", "说不好", "也许", "可能", "大概", "好像", "不确定是不是"],
        "confidence": 0.58,
    },
    "avoidance": {
        "label": "回避或行动阻力",
        "terms": ["不想学", "不想做", "算了", "拖延", "逃避", "做不下去", "坚持不了", "不想面对"],
        "confidence": 0.64,
    },
    "self_efficacy_threat": {
        "label": "自我效能受威胁",
        "terms": ["我不行", "我做不到", "我总是错", "我又错了", "我很笨", "我学不会", "我怎么都不会", "我不适合"],
        "confidence": 0.66,
    },
    "mentalizing": {
        "label": "对他人心智状态的推断",
        "terms": ["他觉得", "她觉得", "老师觉得", "老师认为", "妈妈觉得", "爸爸觉得", "他们觉得", "他们看不起", "别人怎么看我", "我担心他们认为", "他是不是讨厌我", "是不是觉得", "会不会觉得", "怎么看我", "觉得我不行", "认为我不行"],
        "confidence": 0.58,
    },
    "calibration": {
        "label": "预期与实际可能存在偏差",
        "terms": ["我以为", "我明明会", "考试就错", "平时会", "应该会", "结果又错", "没想到会错", "看着会但不会做"],
        "confidence": 0.62,
    },
    "help_seeking": {
        "label": "主动求助",
        "terms": ["帮我", "教我", "怎么办", "该怎么做", "陪我", "能不能帮我", "我想问"],
        "confidence": 0.75,
    },
    "task_focus": {
        "label": "具体任务或知识请求",
        "terms": ["这题", "这道题", "怎么解", "为什么", "解释一下", "复习", "背诵", "计划", "练习", "知识点"],
        "confidence": 0.60,
    },
    "causal_attribution": {
        "label": "因果归因表达",
        "terms": ["因为", "所以", "都是", "怪我", "都是因为", "导致"],
        "confidence": 0.42,
    },
}

RISK_PATTERNS = [
    "不想活", "自杀", "自残", "伤害自己", "结束生命", "活着没意思", "想死", "不如死了",
]


def _spans(text: str, terms: list[str]) -> list[dict[str, Any]]:
    out = []
    occupied: list[tuple[int, int]] = []
    for term in sorted(terms, key=len, reverse=True):
        for m in re.finditer(re.escape(term), text):
            start, end = m.start(), m.end()
            if any(start < b and end > a for a, b in occupied):
                continue
            occupied.append((start, end))
            out.append({"text": text[start:end], "start": start, "end": end})
    return sorted(out, key=lambda item: item["start"])


def detect_script(text: str) -> dict[str, Any]:
    han = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))
    digits = sum(1 for ch in text if ch.isdigit())
    total = max(1, han + latin + digits)
    if han and latin >= max(3, han // 3):
        label = "mixed_zh_en"
    elif han >= latin:
        label = "zh"
    elif latin:
        label = "en"
    else:
        label = "unknown"
    return {
        "label": label,
        "han_ratio": round(han / total, 4),
        "latin_ratio": round(latin / total, 4),
    }


def _hypothesis(
    hypothesis_id: str,
    label: str,
    confidence: float,
    evidence_types: list[str],
    evidence_spans: list[dict[str, Any]],
    alternative: str,
    next_probe: str,
    response_mode: str,
) -> dict[str, Any]:
    return {
        "id": hypothesis_id,
        "label": label,
        "status": "hypothesis_requires_cross_evidence",
        "confidence": round(min(0.92, max(0.0, confidence)), 3),
        "evidence_types": evidence_types,
        "evidence_spans": evidence_spans,
        "alternative_explanations": [alternative],
        "next_probe": next_probe,
        "recommended_response_mode": response_mode,
    }


def analyze_language(text: str, response_time_ms: float | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Extract language evidence and produce non-clinical candidate hypotheses."""
    clean = (text or "").strip()
    context = context or {}
    if not clean:
        return {
            "model_version": MODEL_VERSION,
            "status": "insufficient_input",
            "language": {"label": "unknown", "han_ratio": 0.0, "latin_ratio": 0.0},
            "features": [],
            "feature_vector": {},
            "hypotheses": [],
            "boundary": "没有语言输入时不做状态推断。",
        }

    features = []
    feature_vector: dict[str, float] = {}
    for feature_type, rule in RULES.items():
        spans = _spans(clean, rule["terms"])
        if spans:
            features.append({
                "type": feature_type,
                "label": rule["label"],
                "confidence": rule["confidence"],
                "spans": spans,
                "method": "dictionary_span_match",
            })
            feature_vector[feature_type] = min(1.0, 0.55 + 0.15 * len(spans))

    risk_spans = _spans(clean, RISK_PATTERNS)
    if risk_spans:
        features.append({
            "type": "safety_risk",
            "label": "潜在即时安全风险词",
            "confidence": 0.82,
            "spans": risk_spans,
            "method": "safety_phrase_match",
        })
        feature_vector["safety_risk"] = 1.0

    if response_time_ms is not None:
        try:
            latency = max(0.0, float(response_time_ms))
            feature_vector["response_delay"] = round(min(1.0, latency / 120000.0), 4)
        except (TypeError, ValueError):
            pass

    types = {item["type"] for item in features}
    hypotheses = []
    if "safety_risk" in types:
        risk_feature = next(item for item in features if item["type"] == "safety_risk")
        hypotheses.append(_hypothesis(
            "safety_check_required",
            "出现需要立即核实的潜在安全风险词",
            0.86,
            ["safety_risk"],
            risk_feature["spans"],
            "也可能是引用、转述或否定语境，仍需按高风险流程核实。",
            "直接确认当前是否存在即时危险，并进入人工与紧急支持流程。",
            "protect",
        ))
    if "mentalizing" in types:
        h = next(item for item in features if item["type"] == "mentalizing")
        hypotheses.append(_hypothesis(
            "other_mind_inference_active",
            "用户正在推断他人的想法或评价",
            0.61,
            ["mentalizing"],
            h["spans"],
            "也可能是在陈述已经发生的事实或转述原话。",
            "区分“对方实际说了什么”和“你推测对方怎么想”。",
            "clarify",
        ))
    if "self_efficacy_threat" in types or "avoidance" in types:
        ev = [x for x in features if x["type"] in {"self_efficacy_threat", "avoidance", "explicit_affect"}]
        hypotheses.append(_hypothesis(
            "action_resource_threat",
            "行动资源或自我效能可能正在下降",
            0.64 + 0.05 * max(0, len(ev) - 1),
            [x["type"] for x in ev],
            [span for x in ev for span in x["spans"]],
            "也可能只是对某个具体任务暂时失去兴趣，不代表长期动机或能力。",
            "让用户选一个十分钟内可完成的最小动作，并观察能否恢复。",
            "support",
        ))
    if "uncertainty" in types or "calibration" in types:
        ev = [x for x in features if x["type"] in {"uncertainty", "calibration", "task_focus"}]
        hypotheses.append(_hypothesis(
            "calibration_or_knowledge_gap",
            "可能是元认知校准或具体知识连接不稳",
            0.56 + 0.05 * max(0, len(ev) - 1),
            [x["type"] for x in ev],
            [span for x in ev for span in x["spans"]],
            "也可能只是信息不足，不能仅凭措辞判断知识掌握。",
            "先做一道低风险预测题，再与真实结果对照。",
            "check",
        ))
    if "help_seeking" in types or "task_focus" in types:
        ev = [x for x in features if x["type"] in {"help_seeking", "task_focus"}]
        hypotheses.append(_hypothesis(
            "task_help_request",
            "存在明确任务或求助请求",
            0.76,
            [x["type"] for x in ev],
            [span for x in ev for span in x["spans"]],
            "问题表面是任务，也可能同时包含情绪或关系卡点。",
            "先确认目标、当前步骤和希望获得的帮助类型。",
            "task",
        ))

    if not hypotheses:
        hypotheses.append(_hypothesis(
            "insufficient_language_evidence",
            "语言证据不足以形成状态假设",
            0.35,
            sorted(types),
            [],
            "陈述本身可能只是事实描述。",
            "继续观察真实任务、行为结果和用户自述。",
            "observe",
        ))

    hypotheses.sort(key=lambda item: item["confidence"], reverse=True)
    return {
        "model_version": MODEL_VERSION,
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "language": detect_script(clean),
        "features": features,
        "feature_vector": feature_vector,
        "hypotheses": hypotheses,
        "context_keys_used": sorted(context.keys()),
        "model_use": {
            "language_role": "提取可观察信号、生成候选解释",
            "tender_state_role": "与答题、行为、时间、结果和历史共同更新状态假设",
            "mastery_rule": "语言表达本身不改变知识掌握度；只有作答和任务结果可进入掌握度证据",
            "llm_rule": "语言模型可做结构化抽取和自然表达，但不得把候选解释写成事实、诊断或固定人格",
        },
        "boundary": "语言信号是弱证据，不是读心、诊断或能力判决。高风险词触发保护流程；所有推断均应保留来源片段、置信度、替代解释和用户纠正。",
    }
