"""Dynamic golden-bias regulation for learning versus creation activity."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from .daoql import list_events

MINOR_FLOOR = 0.382
MAJOR_CEILING = 0.618
DEFAULT_WINDOW_DAYS = 28
SHORT_WINDOW_DAYS = 7
MIN_EVIDENCE = 6

LEARNING_EVENTS = {
    "answer", "metacognition_jol", "baseline", "assessment_result",
    "study_session", "practice", "review", "feedback_received",
}
CREATION_EVENTS = {
    "response", "reflection", "ambient_dialogue_reply", "teacher_task_completed",
    "teaching_task_completed", "artifact_created", "published", "collaboration",
}
CALIBRATION_EVENTS = {
    "answer", "metacognition_jol", "baseline", "assessment_result",
    "ambient_feedback", "feedback_received",
}


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _weight(event: dict) -> float:
    payload = event.get("payload") or {}
    try:
        value = float(payload.get("duration_minutes", payload.get("weight", 1.0)))
    except (TypeError, ValueError):
        value = 1.0
    return max(0.25, min(value, 240.0))


def _shares(events: list[dict], start: datetime, end: datetime) -> tuple[float, float, int]:
    learning = 0.0
    creation = 0.0
    count = 0
    for event in events:
        timestamp = _parse_time(event.get("timestamp"))
        if not timestamp or timestamp < start or timestamp > end:
            continue
        event_type = str(event.get("event_type") or "")
        weight = _weight(event)
        if event_type in LEARNING_EVENTS:
            learning += weight
            count += 1
        elif event_type in CREATION_EVENTS:
            creation += weight
            count += 1
    total = learning + creation
    if total <= 0:
        return 0.0, 0.0, count
    return learning / total, creation / total, count


def _band_status(learning_share: float, creation_share: float) -> tuple[str, float, float]:
    minor = min(learning_share, creation_share)
    major = max(learning_share, creation_share)
    if learning_share > MAJOR_CEILING:
        return "learning_overweight", major, minor
    if creation_share > MAJOR_CEILING:
        return "creation_overweight", major, minor
    return "inside_band", major, minor


def _novelty_ratio(events: list[dict], start: datetime, end: datetime) -> tuple[float | None, int, int]:
    labeled = []
    creation_count = 0
    for event in events:
        timestamp = _parse_time(event.get("timestamp"))
        if not timestamp or timestamp < start or timestamp > end:
            continue
        if str(event.get("event_type") or "") not in CREATION_EVENTS:
            continue
        creation_count += 1
        payload = event.get("payload") or {}
        if "novel_branch" in payload:
            labeled.append(1.0 if payload.get("novel_branch") else 0.0)
        elif payload.get("novelty") is not None:
            try:
                labeled.append(max(0.0, min(1.0, float(payload["novelty"]))))
            except (TypeError, ValueError):
                continue
    return (mean(labeled) if labeled else None), len(labeled), creation_count


def _post_creation_calibration(events: list[dict], start: datetime, end: datetime) -> tuple[float | None, int]:
    creations = []
    calibrations = []
    for event in events:
        timestamp = _parse_time(event.get("timestamp"))
        if not timestamp or timestamp < start or timestamp > end:
            continue
        event_type = str(event.get("event_type") or "")
        if event_type in CREATION_EVENTS:
            creations.append(timestamp)
        elif event_type in CALIBRATION_EVENTS:
            calibrations.append(timestamp)
    if not creations:
        return None, 0
    calibrated = 0
    for created_at in creations:
        if any(created_at <= calibrated_at <= created_at + timedelta(hours=72) for calibrated_at in calibrations):
            calibrated += 1
    return calibrated / len(creations), len(creations)


def _hysteresis_state(short_status: str, long_status: str) -> str:
    if short_status == "inside_band" and long_status == "inside_band":
        return "normal"
    if long_status == "inside_band" and short_status != "inside_band":
        return "watch"
    if short_status == long_status and short_status != "inside_band":
        return "adjusted"
    if short_status == "inside_band" and long_status != "inside_band":
        return "recovering"
    return "mixed"


def _next_probe(status: str, calibration: float | None) -> dict:
    if status == "learning_overweight":
        return {"type": "output_probe", "label": "完成一个最小可验证输出", "action": "用十分钟讲清、写出或展示一个当前理解。"}
    if status == "creation_overweight":
        if calibration is not None and calibration < MINOR_FLOOR:
            return {"type": "calibration_probe", "label": "先收集一次真实反馈", "action": "对一个输出做复述、测试或结果校验，再继续扩展。"}
        return {"type": "reality_probe", "label": "检查输出是否仍然有根", "action": "对照真实结果，删去一个没有证据支撑的分支。"}
    return {"type": "maintenance_probe", "label": "保持当前节律", "action": "记录这一阶段哪一种学习或创造方式最有效。"}


def build_golden_bias(student_id: str, *, window_days: int = DEFAULT_WINDOW_DAYS, now: datetime | None = None) -> dict:
    events = list_events(student_id)
    end = now or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    end = end.astimezone(timezone.utc)
    long_start = end - timedelta(days=window_days)
    short_start = end - timedelta(days=SHORT_WINDOW_DAYS)
    long_learning, long_creation, long_count = _shares(events, long_start, end)
    short_learning, short_creation, short_count = _shares(events, short_start, end)
    novelty, novelty_labeled, creation_count = _novelty_ratio(events, long_start, end)
    calibration, calibration_creations = _post_creation_calibration(events, long_start, end)
    evidence_count = long_count
    if evidence_count < MIN_EVIDENCE:
        return {
            "version": "dynamic-golden-bias-1.0",
            "available": False,
            "status": "insufficient_evidence",
            "window_days": window_days,
            "evidence_count": evidence_count,
            "minimum_evidence": MIN_EVIDENCE,
            "band": {"minor_floor": MINOR_FLOOR, "major_ceiling": MAJOR_CEILING},
            "notice": "证据不足，不判断学习与创造比例。继续记录学习、输出和真实反馈后再评估。",
        }
    long_status, long_major, long_minor = _band_status(long_learning, long_creation)
    short_status, _, _ = _band_status(short_learning, short_creation) if short_count >= MIN_EVIDENCE else ("insufficient_evidence", 0.0, 0.0)
    phase = "learning_dominant" if long_status == "learning_overweight" else "creation_dominant" if long_status == "creation_overweight" else "balanced"
    confidence = "higher" if evidence_count >= 20 else "moderate"
    next_probe = _next_probe(long_status, calibration)
    quality = {
        "novelty_labeled": novelty_labeled,
        "creation_events": creation_count,
        "novelty_coverage": round(novelty_labeled / creation_count, 3) if creation_count else 0.0,
        "calibration_creation_events": calibration_creations,
    }
    return {
        "version": "dynamic-golden-bias-1.0",
        "available": True,
        "window_days": window_days,
        "short_window_days": SHORT_WINDOW_DAYS,
        "evidence_count": evidence_count,
        "learning_share": round(long_learning, 4),
        "creation_share": round(long_creation, 4),
        "larger_share": round(long_major, 4),
        "minor_share": round(long_minor, 4),
        "band": {"minor_floor": MINOR_FLOOR, "major_ceiling": MAJOR_CEILING, "status": long_status},
        "short_band_status": short_status,
        "long_band_status": long_status,
        "phase": phase,
        "hysteresis_state": _hysteresis_state(short_status, long_status),
        "novelty_ratio": None if novelty is None else round(novelty, 4),
        "post_creation_calibration": None if calibration is None else round(calibration, 4),
        "data_quality": quality,
        "confidence": confidence,
        "next_probe": next_probe,
        "notice": "黄金比是弹性偏置带：较小一极长期不低于约 38.2%，较大一极长期不高于约 61.8%。它不是每日 KPI、人格评分或效果承诺。",
    }