# -*- coding: utf-8 -*-
"""Unified, conservative inference adapter for the RoleMind public-data baselines.

The two operational models intentionally exclude label-adjacent/post-submission
features. Research benchmark models are not loaded here.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from functools import lru_cache
from typing import Any

import joblib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
MODELS = ROOT / "models"
METRICS = ROOT / "outputs" / "ablation_and_validation.json"


@lru_cache(maxsize=8)
def _load_model(name: str) -> dict[str, Any]:
    return joblib.load(MODELS / name)


def _round(value: float) -> float:
    return round(float(value), 4)


def predict_student(features: dict[str, float]) -> dict[str, Any]:
    """Predict correctness before the current answer is submitted.

    Features must be available before seeing the current response:
    opportunity, prior_user_correct, prior_skill_correct.
    """
    artifact = _load_model("student_mind_pre_answer.joblib")
    row = pd.DataFrame([{key: features[key] for key in artifact["features"]}])
    probability = _round(artifact["model"].predict_proba(row)[0, 1])
    uncertainty = _round(1.0 - max(probability, 1.0 - probability))
    return {
        "role": "student",
        "scope": "current_item_pre_answer",
        "signals": {"predicted_correct": probability, "uncertainty": uncertainty},
        "evidence": artifact["intended_use"],
        "next_action": (
            "提供最小提示并让学生解释关键步骤"
            if probability < 0.55
            else "先让学生独立作答，再安排变式巩固"
        ),
    }


def predict_teacher(text: str) -> dict[str, Any]:
    artifact = _load_model("teacher_mind.joblib")
    vector = artifact["vectorizer"].transform([text])
    probabilities = artifact["classifier"].predict_proba(vector)[0]
    top = np.argsort(-probabilities)[:4]
    labels = [
        {"label": artifact["labels"][i], "probability": _round(probabilities[i])}
        for i in top
    ]
    return {
        "role": "teacher",
        "scope": "utterance",
        "signals": {"talk_moves": labels},
        "evidence": "TalkMoves teacher utterance classifier",
        "next_action": "将低置信度标签视为待复核信号，不作为教师绩效结论",
    }


def predict_sales(features: dict[str, str]) -> dict[str, Any]:
    """Pre-contact lead score using only reproducible acquisition fields."""
    artifact = _load_model("sales_mind_pre_contact.joblib")
    row = pd.DataFrame([{key: features[key] for key in artifact["features"]}])
    probability = _round(artifact["pipeline"].predict_proba(row)[0, 1])
    priority = "P0" if probability >= 0.7 else "P1" if probability >= 0.4 else "P2"
    return {
        "role": "sales",
        "scope": "pre_contact_lead",
        "signals": {"conversion_probability": probability, "priority": priority},
        "evidence": artifact["intended_use"],
        "next_action": (
            "人工核验需求与授权后跟进"
            if priority in {"P0", "P1"}
            else "低成本培育，不制造焦虑"
        ),
    }


def predict_parent(features: dict[str, Any]) -> dict[str, Any]:
    artifact = _load_model("parent_mind.joblib")
    row = pd.DataFrame([{key: features[key] for key in artifact["features"]}])
    probability = _round(artifact["pipeline"].predict_proba(row)[0, 1])
    return {
        "role": "parent",
        "scope": "family_context_proxy",
        "signals": {"high_absence_risk_proxy": probability},
        "evidence": "UCI Student Performance family-context proxy",
        "next_action": "把结果当作家庭支持访谈线索，不作为家长评价或因果归责依据",
    }


def predict_institution(features: dict[str, float | int]) -> dict[str, Any]:
    artifact = _load_model("institution_mind.joblib")
    row = pd.DataFrame([{key: features[key] for key in artifact["features"]}])
    probability = _round(artifact["model"].predict_proba(row)[0, 1])
    return {
        "role": "institution_admin",
        "scope": "course_week_proxy",
        "signals": {"weekly_attrition_risk_proxy": probability},
        "evidence": "OULAD weekly activity model",
        "next_action": "结合课程阶段、教师配置与人工事实日志复核，不能直接处罚教师或学生",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="RoleMind conservative inference")
    parser.add_argument("--role", required=True, choices=["student", "teacher", "sales", "parent", "institution"])
    parser.add_argument("--input", required=True, help="JSON object or path to a JSON object")
    args = parser.parse_args()
    source = pathlib.Path(args.input)
    payload = json.loads(source.read_text(encoding="utf-8")) if source.exists() else json.loads(args.input)
    dispatch = {
        "student": predict_student,
        "teacher": lambda x: predict_teacher(x["text"]),
        "sales": predict_sales,
        "parent": predict_parent,
        "institution": predict_institution,
    }
    print(json.dumps(dispatch[args.role](payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
