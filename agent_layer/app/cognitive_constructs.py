"""Tender cognitive constructs: bloom, result and forest.

This module operationalizes the academic supplement as transparent, testable
scoring functions. The default coefficients are engineering priors, not
validated scientific constants. Every result carries its evidence, threshold
and limitations so it can be recalibrated later.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import exp
from typing import Any, Mapping


MODEL_VERSION = "cognitive-constructs-1.0"
DEFAULT_THRESHOLDS = {"bloom": 0.65, "result": 0.35, "forest": 0.60}

BLOOM_WEIGHTS = {
    "intercept": -2.6,
    "retention": 1.8,
    "transfer": 1.5,
    "schema": 1.2,
    "load": -0.8,
}
RESULT_WEIGHTS = {
    "intercept": -3.0,
    "novelty_gain": 2.0,
    "synthesis": 1.5,
    "utility": 1.5,
    "tms": 1.0,
    "conflict": -1.2,
}
FOREST_WEIGHTS = {
    "intercept": -2.5,
    "diversity": 1.6,
    "tms": 1.8,
    "contribution_entropy": 1.0,
    "recombination_history": 0.8,
    "homogenization": -1.4,
}

CAVEATS = [
    "默认系数是产品先验，不是已经校准的科学常数。",
    "分数是局部证据综合，不是诊断、智力或人格判断。",
    "阈值必须按任务、年龄、语言和测量方式重新校准。",
    "相关关系不能自动解释为因果关系。",
]


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return 1.0 / (1.0 + z)
    z = exp(value)
    return z / (1.0 + z)


def _number(evidence: Mapping[str, Any], key: str, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    if key not in evidence:
        raise ValueError(f"missing_field:{key}")
    try:
        value = float(evidence[key])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_number:{key}") from exc
    if value < minimum or value > maximum:
        raise ValueError(f"out_of_range:{key}")
    return value


def assess_bloom(evidence: Mapping[str, Any], threshold: float | None = None) -> dict[str, Any]:
    """Estimate whether knowledge is consolidating into stable cognition."""
    retention_24h = _number(evidence, "retention_24h")
    retention_7d = _number(evidence, "retention_7d")
    retention_30d = _number(evidence, "retention_30d")
    transfer = _number(evidence, "transfer_score")
    schema = _number(evidence, "schema_coherence")
    load = _number(evidence, "cognitive_load")
    retention = 0.2 * retention_24h + 0.5 * retention_7d + 0.3 * retention_30d
    z = (
        BLOOM_WEIGHTS["intercept"]
        + BLOOM_WEIGHTS["retention"] * retention
        + BLOOM_WEIGHTS["transfer"] * transfer
        + BLOOM_WEIGHTS["schema"] * schema
        + BLOOM_WEIGHTS["load"] * load
    )
    score = _sigmoid(z)
    cutoff = float(threshold if threshold is not None else DEFAULT_THRESHOLDS["bloom"])
    conditions = {
        "retention_7d_at_least_0_6": retention_7d >= 0.60,
        "transfer_at_least_0_5": transfer >= 0.50,
        "score_at_least_threshold": score >= cutoff,
    }
    passed = all(conditions.values())
    return {
        "construct": "bloom",
        "model_version": MODEL_VERSION,
        "score": round(score, 6),
        "threshold": cutoff,
        "status": "supported" if passed else "insufficient_evidence",
        "components": {
            "retention_index": round(retention, 6),
            "retention_24h": retention_24h,
            "retention_7d": retention_7d,
            "retention_30d": retention_30d,
            "transfer_score": transfer,
            "schema_coherence": schema,
            "cognitive_load": load,
        },
        "conditions": conditions,
        "weights": dict(BLOOM_WEIGHTS),
        "evidence_grade": "strong_for_spacing_and_retrieval; moderate_for_transfer",
        "caveats": list(CAVEATS),
    }


def assess_result(evidence: Mapping[str, Any], threshold: float | None = None) -> dict[str, Any]:
    """Estimate whether a group produced a genuinely recombinant result."""
    individual = evidence.get("individual_novelty")
    if not isinstance(individual, (list, tuple)) or len(individual) < 2:
        raise ValueError("individual_novelty_requires_two_members")
    individual_values = [_clip01(float(item)) for item in individual]
    group_novelty = _number(evidence, "group_novelty")
    synthesis = _number(evidence, "synthesis")
    utility = _number(evidence, "utility")
    tms = _number(evidence, "tms")
    conflict = _number(evidence, "relationship_conflict")
    novelty_gain = group_novelty - max(individual_values)
    positive_gain = max(0.0, novelty_gain)
    z = (
        RESULT_WEIGHTS["intercept"]
        + RESULT_WEIGHTS["novelty_gain"] * positive_gain
        + RESULT_WEIGHTS["synthesis"] * synthesis
        + RESULT_WEIGHTS["utility"] * utility
        + RESULT_WEIGHTS["tms"] * tms
        + RESULT_WEIGHTS["conflict"] * conflict
    )
    score = _sigmoid(z)
    cutoff = float(threshold if threshold is not None else DEFAULT_THRESHOLDS["result"])
    conditions = {
        "novelty_gain_positive": novelty_gain > 0,
        "utility_at_least_0_6": utility >= 0.60,
        "synthesis_at_least_0_5": synthesis >= 0.50,
        "score_at_least_threshold": score >= cutoff,
    }
    passed = all(conditions.values())
    return {
        "construct": "result",
        "model_version": MODEL_VERSION,
        "score": round(score, 6),
        "threshold": cutoff,
        "status": "supported" if passed else "insufficient_evidence",
        "components": {
            "individual_novelty_max": round(max(individual_values), 6),
            "group_novelty": group_novelty,
            "novelty_gain": round(novelty_gain, 6),
            "synthesis": synthesis,
            "utility": utility,
            "tms": tms,
            "relationship_conflict": conflict,
        },
        "conditions": conditions,
        "weights": dict(RESULT_WEIGHTS),
        "evidence_grade": "mixed_requires_coordination_and_baseline",
        "caveats": list(CAVEATS),
    }


def assess_forest(evidence: Mapping[str, Any], threshold: float | None = None) -> dict[str, Any]:
    """Estimate whether diverse cognition can be sustained and recombined."""
    diversity = _number(evidence, "cognitive_diversity")
    tms = _number(evidence, "tms")
    entropy = _number(evidence, "contribution_entropy")
    history = _number(evidence, "recombination_history")
    homogenization = _number(evidence, "homogenization")
    z = (
        FOREST_WEIGHTS["intercept"]
        + FOREST_WEIGHTS["diversity"] * diversity
        + FOREST_WEIGHTS["tms"] * tms
        + FOREST_WEIGHTS["contribution_entropy"] * entropy
        + FOREST_WEIGHTS["recombination_history"] * history
        + FOREST_WEIGHTS["homogenization"] * homogenization
    )
    score = _sigmoid(z)
    cutoff = float(threshold if threshold is not None else DEFAULT_THRESHOLDS["forest"])
    conditions = {
        "diversity_at_least_0_5": diversity >= 0.50,
        "tms_at_least_0_5": tms >= 0.50,
        "homogenization_below_0_5": homogenization < 0.50,
        "score_at_least_threshold": score >= cutoff,
    }
    passed = all(conditions.values())
    return {
        "construct": "forest",
        "model_version": MODEL_VERSION,
        "score": round(score, 6),
        "threshold": cutoff,
        "status": "supported" if passed else "insufficient_evidence",
        "components": {
            "cognitive_diversity": diversity,
            "tms": tms,
            "contribution_entropy": entropy,
            "recombination_history": history,
            "homogenization": homogenization,
        },
        "conditions": conditions,
        "weights": dict(FOREST_WEIGHTS),
        "evidence_grade": "mixed_diversity_requires_coordination",
        "caveats": list(CAVEATS),
    }


ASSESSORS = {"bloom": assess_bloom, "result": assess_result, "forest": assess_forest}


def assess_construct(construct: str, evidence: Mapping[str, Any], threshold: float | None = None) -> dict[str, Any]:
    try:
        assessor = ASSESSORS[construct]
    except KeyError as exc:
        raise ValueError("unknown_construct") from exc
    return assessor(evidence, threshold=threshold)


def construct_catalog() -> dict[str, Any]:
    return {
        "model_version": MODEL_VERSION,
        "status": "research_operationalization_not_validated_unified_theory",
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "constructs": [
            {
                "id": "bloom",
                "name": "开花",
                "definition": "工作记忆中的临时表征，经延迟提取、迁移和结构整合，逐渐形成稳定认知结构。",
                "requires": ["retention_24h", "retention_7d", "retention_30d", "transfer_score", "schema_coherence", "cognitive_load"],
                "evidence_grade": "spacing_retrieval_strong; transfer_moderate",
            },
            {
                "id": "result",
                "name": "结果",
                "definition": "不同认知结构发生连接、碰撞和重组，产生超过个体基线的新颖且有用产出。",
                "requires": ["individual_novelty", "group_novelty", "synthesis", "utility", "tms", "relationship_conflict"],
                "evidence_grade": "mixed_context_dependent",
            },
            {
                "id": "forest",
                "name": "森林",
                "definition": "个人层面，是不同认知结构长期共存、准确调用并持续重组；共享层面，是全部知识体系与不同学习者共同构成的生态。当前分数只测量前一层的可观察证据。",
                "requires": ["cognitive_diversity", "tms", "contribution_entropy", "recombination_history", "homogenization"],
                "evidence_grade": "mixed_diversity_requires_coordination",
            },
        ],
        "caveats": list(CAVEATS),
    }
