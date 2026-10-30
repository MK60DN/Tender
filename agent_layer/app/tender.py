"""Tender 心智层：把 DAOQL 事件合成为带不确定性的状态。"""
from __future__ import annotations
import math
from datetime import datetime, timezone
from .tender_models import metacognition_from_events, rhythm_from_events, baseline_from_events, metameta_from_events
from .metameta_cartographer import build_metameta_annotation_map


def _logit(p: float) -> float:
    p = min(max(float(p), 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _mean(xs, default=0.0):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else default


def compute_state(student_id: str, events: list[dict]) -> dict:
    answers = [e for e in events if e["event_type"] == "answer"]
    jols = [e for e in events if e["event_type"] == "metacognition_jol"]
    responses = [e for e in events if e["event_type"] == "response"]
    baselines = [e for e in events if e["event_type"] == "baseline"]
    groups = [e for e in events if e["event_type"] == "group_interaction"]

    mastery = _mean([1.0 if e["payload"].get("correct") else 0.0 for e in answers], 0.5)
    theta = _logit(mastery)

    jol_biases = []
    for e in jols:
        n = float(e["payload"].get("n_items", 10) or 10)
        pred = float(e["payload"].get("predicted_correct", 0) or 0) / n
        act = float(e["payload"].get("actual_correct", 0) or 0) / n
        jol_biases.append(pred - act)
    jol_bias = _mean(jol_biases, 0.0)

    hesitation = _mean([float(e["payload"].get("response_time_ms", 0) or 0) / 60000.0 for e in responses], 0.0)
    hesitation = min(max(hesitation, 0.0), 1.0)

    fit = _mean([float(e["payload"].get("arrangement_fit", 0.5) or 0.5) for e in baselines], 0.5)
    habit = _mean([float(e["payload"].get("habit_change", 0.0) or 0.0) for e in baselines], 0.0)

    clustering = _mean([float(e["payload"].get("clustering", 0.0) or 0.0) for e in groups], 0.0)
    bridge = _mean([float(e["payload"].get("bridge_ratio", 0.0) or 0.0) for e in groups], 0.0)

    return {
        "student_id": student_id,
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "n_events": len(events),
        "cognitive": {"theta": round(theta, 4), "uncertainty": round(1.0 / math.sqrt(len(answers) + 1), 4)},
        "emotion": {"valence": 0.0, "arousal": 0.0, "note": "情绪模型未接入时返回占位值"},
        "metacognition": {
            "jol_bias": round(jol_bias, 4),
            "hesitation": round(hesitation, 4),
            "auc": None,
            "profile": metacognition_from_events(events),
        },
        "knowledge": {"mastery": round(mastery, 4)},
        "baseline": {
            "arrangement_fit": round(fit, 4),
            "habit_change": round(habit, 4),
            "rhythm": rhythm_from_events(events),
            "baseline_model": baseline_from_events(events),
        },
        "group": {"clustering": round(clustering, 4), "bridge_ratio": round(bridge, 4)},
        "observer": {
            "teacher_metameta": metameta_from_events(events),
            "input_map": build_metameta_annotation_map(events),
        },
    }
