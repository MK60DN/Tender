"""Tender 模型适配层：复用 experiments/platform_reverse_lab 的已有模块。"""
from __future__ import annotations
import sys, pathlib, math
from datetime import datetime

PLATFORM = pathlib.Path(__file__).resolve().parents[2] / "experiments" / "platform_reverse_lab"
if str(PLATFORM) not in sys.path:
    sys.path.insert(0, str(PLATFORM))


def _safe_import():
    out = {}
    try:
        from platform_reverse_lab.metacognition import metacognitive_profile, confidence_discount
        out["metacognitive_profile"] = metacognitive_profile
        out["confidence_discount"] = confidence_discount
    except Exception:
        pass
    try:
        from platform_reverse_lab.rhythm_periodogram import rhythm_metrics
        out["rhythm_metrics"] = rhythm_metrics
    except Exception:
        pass
    try:
        from platform_reverse_lab.rhythm_baseline import build_baseline, daily_deviation
        out["build_baseline"] = build_baseline
        out["daily_deviation"] = daily_deviation
    except Exception:
        pass
    try:
        from platform_reverse_lab.metameta import meta_confidence
        out["meta_confidence"] = meta_confidence
    except Exception:
        pass
    return out


MODELS = _safe_import()


def _hours_from_events(events):
    hours = []
    for e in events:
        ts = e.get("timestamp")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(ts)
            hours.append(dt.timestamp() / 3600.0)
        except Exception:
            continue
    return sorted(hours)


def metacognition_from_events(events):
    marked, error = [], []
    for e in events:
        if e["event_type"] == "metacognition_mark":
            marked.append(bool(e["payload"].get("marked", False)))
            error.append(not bool(e["payload"].get("correct", True)))
    if marked and MODELS.get("metacognitive_profile"):
        prof = MODELS["metacognitive_profile"](marked, error)
        if prof:
            return prof
    return {"note": "no item-level marks or profile unavailable"}


def rhythm_from_events(events):
    hours = _hours_from_events(events)
    if len(hours) >= 20 and MODELS.get("rhythm_metrics"):
        try:
            return MODELS["rhythm_metrics"](hours)
        except Exception:
            return {"note": "rhythm_metrics failed"}
    return {"note": "not enough timestamped events"}


def baseline_from_events(events):
    hours = _hours_from_events(events)
    if len(hours) >= 40 and MODELS.get("build_baseline"):
        mid = len(hours) // 2
        bl = MODELS["build_baseline"](hours[:mid])
        if bl:
            devs = []
            for h in hours[mid:]:
                try:
                    r = MODELS["daily_deviation"]([h], bl)
                    if r:
                        devs.append(r.get("综合偏离", 0.0))
                except Exception:
                    pass
            if devs:
                return {"baseline_events": bl.get("n_events"), "deviation_mean": sum(devs)/len(devs),
                        "deviation_max": max(devs)}
    return {"note": "not enough events for baseline"}


def metameta_from_events(events):
    rows = [e for e in events if e["event_type"] == "teacher_prediction"]
    if not rows:
        return {"note": "no teacher predictions"}
    conf = [float(e["payload"].get("confidence", 50) or 50) for e in rows]
    err = [abs(float(e["payload"].get("predicted_correct", 0) or 0) - float(e["payload"].get("actual_correct", 0) or 0)) for e in rows]
    if len(conf) >= 5:
        try:
            import numpy as np
            r = float(np.corrcoef(conf, [-x for x in err])[0, 1])
            return {"metameta_r": round(r, 4), "n": len(conf)}
        except Exception:
            pass
    return {"metameta_r": None, "n": len(conf)}
