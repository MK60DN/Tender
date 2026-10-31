"""Dynamic golden-bias regulation and evidence-gated rhythm guidance."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import math
import random
from statistics import mean
from typing import Any

from .daoql import list_events

MINOR_FLOOR = 0.382
MAJOR_CEILING = 0.618
DEFAULT_WINDOW_DAYS = 28
SHORT_WINDOW_DAYS = 7
MIN_EVIDENCE = 6

PERIOD_ANALYSIS_DAYS = 84
PERIOD_MIN_ANALYSIS_DAYS = 42
PERIOD_MIN_ACTIVE_DAYS = 28
PERIOD_MIN_EVENTS = 36
PERIOD_SEARCH_MIN_DAYS = 5
PERIOD_SEARCH_MAX_DAYS = 28
PERIOD_MIN_CYCLES = 3.0
PERIOD_PERMUTATIONS = 80
PERIOD_STABLE_AUTOCORR = 0.32
PERIOD_STABLE_CONFIDENCE = 0.62
PERIOD_CANDIDATE_AUTOCORR = 0.20
PERIOD_CANDIDATE_CONFIDENCE = 0.45
PERIOD_SIGNIFICANCE = 0.05
PERIOD_CANDIDATE_SIGNIFICANCE = 0.08

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
RECOVERY_EVENTS = {"rest", "break", "recovery", "pause", "session_end"}

PHASE_SEQUENCE = [
    {"code": "absorb", "label": "吸收与编码"},
    {"code": "integrate", "label": "整合与巩固"},
    {"code": "express", "label": "表达与分叉"},
    {"code": "calibrate", "label": "现实校准"},
    {"code": "recover", "label": "恢复或低活动"},
]


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


def _daily_balance_series(events: list[dict], end: datetime) -> tuple[list[float], int, int]:
    start_date = end.date() - timedelta(days=PERIOD_ANALYSIS_DAYS - 1)
    learning = [0.0] * PERIOD_ANALYSIS_DAYS
    creation = [0.0] * PERIOD_ANALYSIS_DAYS
    active = [False] * PERIOD_ANALYSIS_DAYS
    event_count = 0
    for event in events:
        timestamp = _parse_time(event.get("timestamp"))
        if not timestamp or timestamp > end or timestamp.date() < start_date:
            continue
        event_type = str(event.get("event_type") or "")
        if event_type not in LEARNING_EVENTS and event_type not in CREATION_EVENTS:
            continue
        index = (timestamp.date() - start_date).days
        if index < 0 or index >= PERIOD_ANALYSIS_DAYS:
            continue
        weight = _weight(event)
        if event_type in LEARNING_EVENTS:
            learning[index] += weight
        else:
            creation[index] += weight
        active[index] = True
        event_count += 1
    series = []
    for l_value, c_value in zip(learning, creation):
        total = l_value + c_value
        series.append(0.0 if total <= 0 else (c_value - l_value) / total)
    return series, sum(1 for value in active if value), event_count


def _smooth(series: list[float], radius: int = 1) -> list[float]:
    result = []
    for index in range(len(series)):
        start = max(0, index - radius)
        stop = min(len(series), index + radius + 1)
        result.append(sum(series[start:stop]) / (stop - start))
    return result


def _autocorrelation(series: list[float], lag: int) -> float:
    if lag <= 0 or lag >= len(series):
        return 0.0
    left = series[:-lag]
    right = series[lag:]
    denominator = math.sqrt(sum(value * value for value in left) * sum(value * value for value in right))
    if denominator <= 1e-12:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / denominator


def _best_period_candidate(series: list[float]) -> tuple[int, float, list[int]]:
    max_lag = min(PERIOD_SEARCH_MAX_DAYS, len(series) // 2)
    lags = list(range(PERIOD_SEARCH_MIN_DAYS, max_lag + 1))
    correlations = {lag: _autocorrelation(series, lag) for lag in lags}
    local_peaks = []
    for lag in lags:
        current = correlations[lag]
        previous = correlations.get(lag - 1, current)
        following = correlations.get(lag + 1, current)
        if current >= previous and current >= following:
            local_peaks.append((lag, current))
    if not local_peaks:
        best_lag = max(lags, key=lambda lag: correlations[lag])
        best_corr = correlations[best_lag]
    else:
        local_peaks.sort(key=lambda item: item[1], reverse=True)
        best_lag, best_corr = local_peaks[0]
        for lag, corr in local_peaks[1:]:
            if lag < best_lag and best_lag % lag == 0 and best_lag // lag >= 2 and corr >= best_corr - 0.12:
                best_lag, best_corr = lag, corr
                break
    return best_lag, best_corr, lags


def _refine_period(series: list[float], lag: int) -> float:
    if lag <= 1 or lag >= len(series) - 1:
        return float(lag)
    left = _autocorrelation(series, lag - 1)
    center = _autocorrelation(series, lag)
    right = _autocorrelation(series, lag + 1)
    denominator = left - 2 * center + right
    if abs(denominator) <= 1e-9:
        return float(lag)
    offset = 0.5 * (left - right) / denominator
    return max(lag - 0.5, min(lag + 0.5, lag + offset))


def _confidence_label(score: float) -> str:
    if score >= 0.72:
        return "high"
    if score >= 0.55:
        return "moderate"
    return "low"


def _detect_periodicity(events: list[dict], end: datetime, student_id: str) -> dict:
    series, active_days, event_count = _daily_balance_series(events, end)
    base = {
        "analysis_days": PERIOD_ANALYSIS_DAYS,
        "active_days": active_days,
        "event_count": event_count,
        "search_range_days": [PERIOD_SEARCH_MIN_DAYS, PERIOD_SEARCH_MAX_DAYS],
        "operating_windows_are_not_period": True,
        "notice": "周期只作为可更正估计；7/28 天是观察与控制窗口，不是用户真实周期。",
    }
    if active_days < PERIOD_MIN_ACTIVE_DAYS or event_count < PERIOD_MIN_EVENTS or PERIOD_ANALYSIS_DAYS < PERIOD_MIN_ANALYSIS_DAYS:
        return {
            **base,
            "status": "insufficient_evidence",
            "period_days": None,
            "confidence": "low",
            "reason": "活动天数和事件量不足，不判断周期。",
        }
    smoothed = _smooth(series)
    centered = [value - mean(smoothed) for value in smoothed]
    best_lag, best_corr, lags = _best_period_candidate(centered)
    period_days = _refine_period(centered, best_lag)
    seed_text = f"{student_id}|{end.date().isoformat()}|rhythm-period-v2"
    seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    null_peaks = []
    for _ in range(PERIOD_PERMUTATIONS):
        shuffled = centered[:]
        rng.shuffle(shuffled)
        null_peaks.append(max(_autocorrelation(shuffled, lag) for lag in lags))
    null_peaks.sort()
    null_95 = null_peaks[min(len(null_peaks) - 1, int(0.95 * len(null_peaks)))]
    exceed = sum(value >= best_corr for value in null_peaks)
    p_value = (1 + exceed) / (PERIOD_PERMUTATIONS + 1)
    cycles = PERIOD_ANALYSIS_DAYS / max(period_days, 1.0)
    coverage = min(1.0, active_days / 56.0)
    cycle_score = min(1.0, cycles / 4.0)
    confidence_score = (
        0.50 * max(0.0, min(1.0, best_corr))
        + 0.30 * max(0.0, 1.0 - p_value)
        + 0.10 * coverage
        + 0.10 * cycle_score
    )
    antiphase_lag = max(1, round(period_days / 2))
    antiphase_corr = _autocorrelation(centered, antiphase_lag)
    if (
        best_corr >= PERIOD_STABLE_AUTOCORR
        and p_value <= PERIOD_SIGNIFICANCE
        and confidence_score >= PERIOD_STABLE_CONFIDENCE
        and cycles >= PERIOD_MIN_CYCLES
        and antiphase_corr <= -0.20
    ):
        status = "stable_period"
    elif (
        best_corr >= PERIOD_CANDIDATE_AUTOCORR
        and p_value <= PERIOD_CANDIDATE_SIGNIFICANCE
        and confidence_score >= PERIOD_CANDIDATE_CONFIDENCE
        and antiphase_corr <= -0.05
    ):
        status = "candidate_period"
    else:
        status = "no_stable_period"
    return {
        **base,
        "status": status,
        "period_days": round(period_days, 1) if status != "no_stable_period" else None,
        "confidence": _confidence_label(confidence_score),
        "confidence_score": round(confidence_score, 3),
        "peak_autocorrelation": round(best_corr, 3),
        "antiphase_autocorrelation": round(antiphase_corr, 3),
        "permutation_p_value": round(p_value, 4),
        "null_95th_percentile": round(null_95, 3),
        "cycles_observed": round(cycles, 2),
        "method": "daily learning-creation balance; autocorrelation with permutation null",
        "reason": "只有在重复相位结构与随机波动基线分离时才报告周期。",
    }


def detect_periodicity(events: list[dict], *, end: datetime, student_id: str) -> dict:
    """Public, side-effect-free periodicity evidence for experiments and audits."""
    return _detect_periodicity(events, end, student_id)


def _current_rhythm_phase(
    events: list[dict],
    end: datetime,
    learning_share: float,
    creation_share: float,
    calibration: float | None,
) -> dict:
    recent_start = end - timedelta(days=7)
    recent_learning, recent_creation, _ = _shares(events, recent_start, end)
    recent_calibration, _ = _post_creation_calibration(events, recent_start, end)
    recent_events = []
    last_event_at = None
    recovery_seen = False
    for event in events:
        timestamp = _parse_time(event.get("timestamp"))
        if not timestamp or timestamp > end:
            continue
        if last_event_at is None or timestamp > last_event_at:
            last_event_at = timestamp
        if timestamp >= recent_start:
            recent_events.append(event)
        if timestamp >= end - timedelta(days=3) and str(event.get("event_type") or "") in RECOVERY_EVENTS:
            recovery_seen = True
    if recovery_seen:
        return {
            "code": "recover",
            "label": "恢复或低活动",
            "certainty": "moderate",
            "reason": "近期出现主动休息或恢复事件。",
            "next_action": "先恢复，暂不追加高负荷任务。",
        }
    if last_event_at is not None:
        inactivity_days = max(0, (end.date() - last_event_at.date()).days)
        if 2 <= inactivity_days <= 14:
            return {
                "code": "recover",
                "label": "恢复或低活动",
                "certainty": "low",
                "reason": "近期活动减少；恢复、失去兴趣与其他阻塞目前无法区分。",
                "next_action": "先确认这是主动恢复还是行动阻塞，再决定是否介入。",
            }
        if inactivity_days > 14:
            return {
                "code": "dormant",
                "label": "长期低活动",
                "certainty": "low",
                "reason": "连续多日缺少可观察活动，不代表已经恢复或放弃。",
                "next_action": "用一次低负担询问确认是否暂停、离开或需要帮助。",
            }
    creation_count = sum(1 for event in recent_events if str(event.get("event_type") or "") in CREATION_EVENTS)
    calibration_count = sum(1 for event in recent_events if str(event.get("event_type") or "") in CALIBRATION_EVENTS)
    if creation_count and (recent_calibration is None or recent_calibration < MINOR_FLOOR):
        return {
            "code": "calibrate",
            "label": "现实校准",
            "certainty": "moderate",
            "reason": "近期有输出，但尚缺足够反馈、复测或结果校验。",
            "next_action": "先收集一次真实反馈，再继续扩展。",
        }
    if recent_creation > MAJOR_CEILING:
        return {
            "code": "express",
            "label": "表达与分叉",
            "certainty": "moderate",
            "reason": "近期创造投入明显高于学习与校准投入。",
            "next_action": "检查输出的现实价值，并保留一个可验证的下一步。",
        }
    if recent_learning > MAJOR_CEILING:
        return {
            "code": "absorb",
            "label": "吸收与编码",
            "certainty": "moderate",
            "reason": "近期学习与校准投入明显高于创造输出。",
            "next_action": "完成一个最小可验证输出，让理解进入现实。",
        }
    if creation_count and calibration_count:
        return {
            "code": "integrate",
            "label": "整合与巩固",
            "certainty": "moderate",
            "reason": "近期学习、输出和校准都有可观察证据。",
            "next_action": "保持当前节律，并记录最有效的学习与创造组合。",
        }
    return {
        "code": "integrate",
        "label": "整合与巩固",
        "certainty": "low",
        "reason": "当前证据不足以区分更具体的相位。",
        "next_action": "继续记录一次学习、输出和真实反馈。",
    }


def _next_probe(status: str, calibration: float | None, rhythm_phase: dict) -> dict:
    phase_code = rhythm_phase.get("code")
    if phase_code in {"recover", "dormant"}:
        return {
            "type": "recovery_probe",
            "label": "先确认是否需要恢复",
            "action": rhythm_phase.get("next_action") or "先确认休息、阻塞或离开，再决定是否介入。",
        }
    if phase_code == "calibrate":
        return {
            "type": "calibration_probe",
            "label": "先收集一次真实反馈",
            "action": "对一个输出做复述、测试或结果校验，再继续扩展。",
        }
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
    periodicity = _detect_periodicity(events, end, student_id)
    evidence_count = long_count
    if evidence_count < MIN_EVIDENCE:
        rhythm_phase = _current_rhythm_phase(events, end, long_learning, long_creation, calibration)
        return {
            "version": "dynamic-golden-bias-2.0",
            "available": False,
            "status": "insufficient_evidence",
            "window_days": window_days,
            "evidence_count": evidence_count,
            "minimum_evidence": MIN_EVIDENCE,
            "band": {"minor_floor": MINOR_FLOOR, "major_ceiling": MAJOR_CEILING},
            "rhythm_phase": rhythm_phase,
            "rhythm": {
                "operating_windows": {"short_days": SHORT_WINDOW_DAYS, "long_days": window_days, "role": "observation_and_control_only"},
                "detected_periodicity": periodicity,
                "current_phase": rhythm_phase,
                "phase_sequence": PHASE_SEQUENCE,
            },
            "notice": "证据不足，不判断学习与创造比例或稳定周期。继续记录学习、输出和真实反馈后再评估。",
        }
    long_status, long_major, long_minor = _band_status(long_learning, long_creation)
    short_status, _, _ = _band_status(short_learning, short_creation) if short_count >= MIN_EVIDENCE else ("insufficient_evidence", 0.0, 0.0)
    phase = "learning_dominant" if long_status == "learning_overweight" else "creation_dominant" if long_status == "creation_overweight" else "balanced"
    confidence = "higher" if evidence_count >= 20 else "moderate"
    rhythm_phase = _current_rhythm_phase(events, end, long_learning, long_creation, calibration)
    next_probe = _next_probe(long_status, calibration, rhythm_phase)
    quality = {
        "novelty_labeled": novelty_labeled,
        "creation_events": creation_count,
        "novelty_coverage": round(novelty_labeled / creation_count, 3) if creation_count else 0.0,
        "calibration_creation_events": calibration_creations,
    }
    return {
        "version": "dynamic-golden-bias-2.0",
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
        "rhythm_phase": rhythm_phase,
        "rhythm": {
            "operating_windows": {"short_days": SHORT_WINDOW_DAYS, "long_days": window_days, "role": "observation_and_control_only"},
            "detected_periodicity": periodicity,
            "current_phase": rhythm_phase,
            "phase_sequence": PHASE_SEQUENCE,
        },
        "hysteresis_state": _hysteresis_state(short_status, long_status),
        "novelty_ratio": None if novelty is None else round(novelty, 4),
        "post_creation_calibration": None if calibration is None else round(calibration, 4),
        "data_quality": quality,
        "confidence": confidence,
        "next_probe": next_probe,
        "notice": "黄金比是弹性偏置带；稳定周期只有在与随机波动基线分离后才报告。两者都不是每日 KPI、人格评分或效果承诺。",
    }
