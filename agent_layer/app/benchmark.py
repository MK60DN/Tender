# -*- coding: utf-8 -*-
"""Audited public benchmark for Tender θ on ASSISTments 2009.

The benchmark is intentionally presented as a complete comparison table rather
than a single favorable AUC point estimate.
"""
from __future__ import annotations

from copy import deepcopy

DATASET = {
    "name": "ASSISTments 2009",
    "raw_records": 346860,
    "cleaned_records": 273364,
    "students": 4128,
    "skills": 81,
    "split": "按学生 8:2",
    "train_records": 218945,
    "test_records": 54419,
}

MODELS = [
    {"id": "bkt", "name": "BKT 标准基线", "auc": 0.6794, "log_loss": 0.5910, "note": "概率校准较好"},
    {"id": "tender_global", "name": "Tender θ_seq 全局初始化", "auc": 0.6853, "log_loss": 0.6164, "note": "排序接近 BKT，校准较弱"},
    {"id": "tender_default", "name": "Tender θ_seq 文档默认 η=0.3", "auc": 0.6895, "log_loss": 1.1155, "note": "不推荐作为产品默认值"},
    {"id": "logistic", "name": "Logistic 控制组", "auc": 0.7058, "log_loss": 0.5752, "note": "当前实验中 AUC 与 LogLoss 均更强"},
]

_TENDER_DEFAULT = next(item for item in MODELS if item["id"] == "tender_default")

_BENCHMARK = {
    "benchmark_id": "tender_theta_assistments2009_full_v2",
    "dataset": DATASET,
    "dataset_record_count": "340000+",
    "dataset_record_count_min": 340000,
    "models": MODELS,
    "headline_model_id": "logistic",
    "headline_model_name": "Logistic 控制组",
    "tender_default_recommended": False,
    "comparison_status": "tender_not_superior",
    "claim_status": "mixed_results_not_a_win",
    "headline_warning": (
        "0.6895 是 Tender 文档默认 η=0.3 配置下的 AUC 点估计；同一配置 LogLoss 为 1.1155，"
        "明显差于 BKT 的 0.5910；Logistic 控制组 AUC 0.7058、LogLoss 0.5752，整体更强。"
    ),
    "recommended_tender_configuration": {
        "eta": 0.02,
        "xi": 0,
        "calibration_required": True,
        "note": "η≈0.02 是按概率校准选择的候选值，仍需重复划分和外部验证。",
    },
    "pending_validation": [
        "confidence_interval",
        "repeated_splits",
        "significance_test",
        "calibration_ece_brier",
        "auprc",
        "dkt_sakt_comparison",
        "cross_period_intervention_effect",
    ],
    "disclaimer": (
        "当前结果是单次按学生划分的公开数据基准。Tender θ_seq 可用但未表现出对 BKT 或 Logistic 的全面优势；"
        "不能写成‘显著优于’、‘已证明教学有效’或‘已取代考试’。"
    ),
    "boundary": "该结果是模型基准，不是对任何学习者的诊断或能力裁决。",
}


def tender_theta_benchmark() -> dict:
    """Return an isolated copy so callers cannot mutate the audited benchmark."""
    return deepcopy(_BENCHMARK)
