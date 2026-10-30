"""First-run Big Five, MBTI-preference and Jungian-function preassessment."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .daoql import insert_event, list_events

BASE = Path(__file__).resolve().parents[2] / "knowledge_data"
BIG_FIVE_PATH = BASE / "preassessment_big_five_items.json"
MBTI_PATH = BASE / "preassessment_mbti_items.json"
JUNGIAN_PATH = BASE / "preassessment_jungian_items.json"
VERSION = "preassessment-0.1"

BIG_FIVE_DIMENSIONS = {
    "openness": "开放性",
    "conscientiousness": "尽责性",
    "extraversion": "外向性",
    "agreeableness": "宜人性",
    "emotional_stability": "情绪稳定性",
}

JUNGIAN_LABELS = {
    "Ne": "外倾直觉",
    "Ni": "内倾直觉",
    "Se": "外倾感觉",
    "Si": "内倾感觉",
    "Te": "外倾思维",
    "Ti": "内倾思维",
    "Fe": "外倾情感",
    "Fi": "内倾情感",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def preassessment_items() -> dict:
    big = _load(BIG_FIVE_PATH)
    mbti = _load(MBTI_PATH)
    jungian = _load(JUNGIAN_PATH)
    return {
        "version": VERSION,
        "estimated_minutes": "5-7",
        "consent_notice": "这是自我反思工具，不是诊断。你可以跳过可选部分，结果只保存标准化分数，不默认保存逐题原文。",
        "big_five": big,
        "mbti": mbti,
        "jungian": jungian,
    }


def _normalize(raw: float, reverse: bool) -> float:
    if raw < 1 or raw > 5:
        raise ValueError("responses_must_be_between_1_and_5")
    value = 6 - raw if reverse else raw
    return (value - 1) / 4


def _band(score: float) -> str:
    if score < 0.4:
        return "lower"
    if score > 0.6:
        return "higher"
    return "balanced"


def _score_big_five(responses: Mapping[str, int]) -> dict:
    items = _load(BIG_FIVE_PATH)["items"]
    missing = [item["id"] for item in items if item["id"] not in responses]
    if missing:
        raise ValueError("incomplete_big_five:" + ",".join(missing))
    grouped: dict[str, list[float]] = {}
    for item in items:
        raw = float(responses[item["id"]])
        grouped.setdefault(item["dimension"], []).append(_normalize(raw, item["reverse"]))
    scores = {dim: sum(values) / len(values) for dim, values in grouped.items()}
    sensitivity = scores.pop("emotional_sensitivity")
    scores["emotional_stability"] = 1 - sensitivity
    return {
        key: {
            "label": BIG_FIVE_DIMENSIONS[key],
            "score": round(value, 4),
            "band": _band(value),
        }
        for key, value in scores.items()
    }


def _score_mbti(responses: Mapping[str, int]) -> dict | None:
    items = _load(MBTI_PATH)["items"]
    if not any(item["id"] in responses for item in items):
        return None
    missing = [item["id"] for item in items if item["id"] not in responses]
    if missing:
        raise ValueError("incomplete_mbti:" + ",".join(missing))
    axes: dict[str, list[float]] = {}
    for item in items:
        raw = float(responses[item["id"]])
        if raw < 1 or raw > 5:
            raise ValueError("responses_must_be_between_1_and_5")
        axes.setdefault(item["axis"], []).append((raw - 1) / 4)
    definitions = {
        "energy": ("I", "E"),
        "information": ("S", "N"),
        "decision": ("T", "F"),
        "lifestyle": ("P", "J"),
    }
    result = {}
    for axis, values in axes.items():
        score = sum(values) / len(values)
        low, high = definitions[axis]
        pole = high if score > 0.55 else low if score < 0.45 else "X"
        result[axis] = {
            "low_pole": low,
            "high_pole": high,
            "high_pole_score": round(score, 4),
            "preference": pole,
            "confidence": round(abs(score - 0.5) * 2, 4),
        }
    code = "".join(result[axis]["preference"] for axis in ["energy", "information", "decision", "lifestyle"])
    result["type_hint"] = code
    result["notice"] = "类型代码仅表示沟通偏好；X 表示接近中间，不输出命运或能力结论。"
    return result


def _score_jungian(responses: Mapping[str, int]) -> dict | None:
    items = _load(JUNGIAN_PATH)["items"]
    if not any(item["id"] in responses for item in items):
        return None
    missing = [item["id"] for item in items if item["id"] not in responses]
    if missing:
        raise ValueError("incomplete_jungian:" + ",".join(missing))
    scores = {}
    for item in items:
        scores[item["function"]] = {
            "label": JUNGIAN_LABELS[item["function"]],
            "score": round(_normalize(float(responses[item["id"]]), False), 4),
        }
    ordered = sorted(scores.items(), key=lambda pair: pair[1]["score"], reverse=True)
    return {
        "functions": scores,
        "top_functions": [key for key, value in ordered[:3] if value["score"] >= 0.6],
        "less_preferred": [key for key, value in ordered[-2:] if value["score"] <= 0.4],
        "confidence": "exploratory_low",
        "notice": "八维为单项探索性筛查；结果不是神经测量、能力排名或临床诊断。",
    }


def _big_five_hypotheses(big_five: dict) -> tuple[list[str], list[str], list[str]]:
    strengths, frictions, supports = [], [], []
    rules = {
        "conscientiousness": {
            "higher": ("计划、拆解和持续完成", "计划被打断时可能过度自责或追求完美", "提供可调整的计划，而不是增加更多清单"),
            "lower": ("灵活应变、保留探索空间", "任务启动、收尾和重复执行可能更耗力", "使用外部提醒、最小步骤和明确收尾"),
        },
        "openness": {
            "higher": ("探索、联想和新方法尝试", "选项过多时容易发散或偏离目标", "同时给探索空间和清晰的边界"),
            "lower": ("稳定、经验和可复用流程", "陌生方法或频繁变化可能增加摩擦", "先给具体例子，再逐步引入新方法"),
        },
        "extraversion": {
            "higher": ("主动表达、求助和互动", "外部刺激过多时可能难以安静收束", "用短对话和互动式复盘"),
            "lower": ("独立思考、深度专注和观察", "主动求助或临场表达可能更耗能", "默认文字优先，提前给问题和准备时间"),
        },
        "agreeableness": {
            "higher": ("合作、共情和关系维护", "可能为了照顾他人而压抑自己的需要", "在关键处提供温和但直接的边界提示"),
            "lower": ("直接、边界和批判性判断", "冲突情境中可能显得过直或难以协作", "用具体影响和共同目标表达分歧"),
        },
        "emotional_stability": {
            "higher": ("压力恢复、稳定执行", "可能忽略早期疲劳和风险信号", "保留定期状态检查，而不是只看产出"),
            "lower": ("敏感、风险觉察和共情", "批评、不确定和高压可能占用较多认知资源", "先降低威胁感，再拆出可控下一步"),
        },
    }
    for dimension, value in big_five.items():
        band = value["band"]
        if band in ("higher", "lower"):
            strength, friction, support = rules[dimension][band]
            strengths.append(f"{value['label']}偏高：{strength}")
            frictions.append(f"{value['label']}{'偏高' if band == 'higher' else '偏低'}时：{friction}")
            supports.append(support)
    return strengths[:4], frictions[:4], supports[:4]


def _mbti_supports(mbti: dict | None) -> list[str]:
    if not mbti:
        return []
    mapping = {
        "I": "先文字或异步沟通，再进入实时讨论",
        "E": "用短对话和即时反馈帮助整理思路",
        "S": "先给具体例子、步骤和可验证结果",
        "N": "先给整体框架与关联，再限制探索范围",
        "T": "先给判断标准、逻辑和取舍",
        "F": "先回应感受、价值和对人的影响",
        "J": "给清单、时间点和完成条件",
        "P": "给可选路径和调整空间",
    }
    return [mapping[pole] for axis in ["energy", "information", "decision", "lifestyle"] if (pole := mbti[axis]["preference"]) != "X"]


def _attention_profile(big_five: dict, mbti: dict | None, jungian: dict | None) -> dict:
    capture, sustain, leakage, recovery, scaffolds = [], [], [], [], []
    top = set(jungian["top_functions"]) if jungian else set()

    if big_five["openness"]["band"] == "higher" or "Ne" in top:
        capture.append("新颖性、可能性和跨领域联系更容易吸引注意")
        sustain.append("适度变化和探索空间有助于保持投入")
        leakage.append("选项过多时可能不断切换方向")
    if big_five["conscientiousness"]["band"] == "higher" or "Te" in top:
        capture.append("明确目标、完成标准和进度反馈更容易激活注意")
        sustain.append("计划、检查点和可见产出有助于持续完成")
    if big_five["conscientiousness"]["band"] == "lower":
        sustain.append("短时冲刺、外部提醒和清晰收尾比长清单更有效")
        leakage.append("任务边界模糊时更容易启动困难或留下开放循环")
    if big_five["extraversion"]["band"] == "higher" or "Fe" in top:
        capture.append("互动、口头表达和即时反馈更容易激活注意")
        sustain.append("短对话或可选的同伴反馈可能提供启动动力")
        leakage.append("安静、孤立且低刺激的任务可能让人分心寻找互动")
    if big_five["extraversion"]["band"] == "lower":
        sustain.append("安静、无打断的连续时间更有利于深度投入")
        leakage.append("高频社交或临场表达可能额外消耗注意资源")
    if big_five["agreeableness"]["band"] == "higher":
        leakage.append("过度照顾他人需求可能造成频繁中断或难以拒绝")
    if big_five["emotional_stability"]["band"] == "lower":
        capture.append("威胁、不确定和评价线索更容易抢占注意")
        leakage.append("担心结果或反复检查会占用工作记忆")
        scaffolds.append("先降低威胁感，再把任务缩小到一个可控步骤")
    if "Se" in top:
        capture.append("即时环境变化和动手任务更容易抓住注意")
        recovery.append("走动、换环境或短时感官切换有助于恢复")
    if "Si" in top:
        capture.append("熟悉流程、固定线索和过去经验更容易稳定注意")
        recovery.append("固定作息、熟悉环境和重复仪式有助于恢复")
    if "Ti" in top:
        capture.append("概念一致性和推理闭环更容易吸引持续思考")
        scaffolds.append("先写清判断标准，再开始处理信息")
    if "Fi" in top:
        capture.append("与个人价值和真实感受一致的任务更容易投入")
        recovery.append("通过价值澄清和自我对话恢复方向感")
    if "Ni" in top:
        capture.append("长期方向和整体洞察更容易吸引深入思考")
        scaffolds.append("先确认长期目标，再把当前任务连接到目标")
    if mbti:
        energy = mbti["energy"]["preference"]
        information = mbti["information"]["preference"]
        decision = mbti["decision"]["preference"]
        lifestyle = mbti["lifestyle"]["preference"]
        if energy == "I":
            recovery.append("独处和异步准备有助于恢复注意")
        elif energy == "E":
            recovery.append("交流和外部反馈有助于恢复注意")
        if information == "S":
            scaffolds.append("先给具体例子和可验证步骤，再扩展框架")
        elif information == "N":
            scaffolds.append("先给整体框架，再限制当前探索范围")
        if decision == "T":
            scaffolds.append("先呈现判断标准和取舍")
        elif decision == "F":
            scaffolds.append("先说明对人和价值的影响")
        if lifestyle == "J":
            recovery.append("关闭开放循环和完成一个阶段有助于恢复")
        elif lifestyle == "P":
            recovery.append("保留调整空间比强制固定流程更可持续")
    scaffolds.extend([
        "一次只保留一个主任务和一个下一步",
        "把进度外置成可见标记，减少工作记忆负担",
        "设置明确停止条件，避免完美主义或无限探索",
    ])
    return {
        "capture_hypotheses": list(dict.fromkeys(capture))[:5],
        "sustain_hypotheses": list(dict.fromkeys(sustain))[:5],
        "leakage_hypotheses": list(dict.fromkeys(leakage))[:5],
        "recovery_preferences": list(dict.fromkeys(recovery))[:5],
        "scaffold_suggestions": list(dict.fromkeys(scaffolds))[:6],
        "confidence": "exploratory_self_report",
        "boundary": "注意力画像来自人格自评推导，不是注意力测评、神经测量或 ADHD 诊断。",
    }


def _cognitive_correction_plan(
    big_five: dict,
    mbti: dict | None,
    jungian: dict | None,
    attention: dict,
) -> dict:
    items = []

    def add(item_id, pattern, trigger, practice, evidence, boundary):
        items.append({
            "id": item_id,
            "pattern_hypothesis": pattern,
            "trigger": trigger,
            "correction_practice": practice,
            "success_evidence": evidence,
            "fade_rule": "连续两次成功后减少提示，并把策略交还给用户",
            "boundary": boundary,
        })

    if (
        big_five["openness"]["band"] == "higher"
        and big_five["conscientiousness"]["band"] == "lower"
    ):
        add(
            "novelty_switching",
            "注意力容易被新想法带走，主任务留下开放循环",
            "选项多、任务长、没有明确收尾",
            "保留一个主任务；新想法写入停车区；完成一个 15 分钟步骤后再决定是否切换",
            "主任务恢复或完成一个可交付步骤",
            "这是策略练习，不用于诊断注意力缺陷",
        )
    if big_five["agreeableness"]["band"] == "higher":
        add(
            "over_accommodation",
            "优先照顾他人需求，自己的注意被外部请求切碎",
            "临时求助、冲突或担心让别人失望",
            "使用固定边界句；先确认当前任务和可承诺时间，再回应请求",
            "能够保留一段完整任务时间并清楚表达边界",
            "温和的边界不等于自私；不以人格评分评判关系",
        )
    if big_five["emotional_stability"]["band"] == "lower":
        add(
            "threat_monitoring",
            "评价、不确定或失败线索反复占用注意",
            "结果未知、被批评、任务标准模糊",
            "写下担心的具体结果、可验证证据和一个最小行动；行动后再更新判断",
            "焦虑没有完全消失，但用户能开始并完成下一步",
            "这是学习与自我调节练习；持续痛苦或功能受损时应寻求专业支持",
        )
    if (
        big_five["conscientiousness"]["band"] == "higher"
        and big_five["emotional_stability"]["band"] == "lower"
    ):
        add(
            "overchecking",
            "反复检查或追求完美，导致收尾延迟",
            "高评价压力、不可逆决定、缺少完成标准",
            "开始前定义“足够好”的完成标准；设置一次复核上限和停止时间",
            "在标准时间内提交或关闭任务循环",
            "高标准是资源；当检查不再提高结果时，需要外部停止规则",
        )
    if big_five["extraversion"]["band"] == "higher":
        add(
            "understimulation",
            "低刺激、孤立任务中注意容易寻找外部变化",
            "长时间独处、安静环境、缺少即时反馈",
            "把任务切成短段，安排可选的休息交流；先完成一段再加入互动",
            "能在低刺激任务中完成一个短段并主动安排恢复",
            "需要互动不是自控力差；关键是安排而非压抑",
        )
    if big_five["extraversion"]["band"] == "lower":
        add(
            "social_demand_fatigue",
            "高频社交或临场表达额外占用注意",
            "陌生群体、即时发言、长时间会议",
            "提前拿到问题并准备要点；优先文字或异步沟通；设置退出恢复时间",
            "能够在表达需求的同时保留恢复时间",
            "偏好独处不是缺陷；只在造成持续困扰时调整",
        )
    if mbti and mbti["lifestyle"]["preference"] == "P":
        add(
            "open_loops",
            "保留过多开放选项，任务缺少明确闭合",
            "截止时间模糊、任务可以不断修改",
            "先选择一个可交付版本，设置截止时间和一个明确的关闭条件",
            "按约定时间关闭版本并记录下一步",
            "灵活探索是资源；用外部闭合保护它",
        )
    if jungian and "Ti" in jungian["top_functions"]:
        add(
            "analysis_paralysis",
            "反复校验概念一致性，行动测试迟迟不开始",
            "标准不清、信息不完整、害怕犯错",
            "先写出当前最佳解释和可证伪行动；用小实验替代继续分析",
            "完成一次可验证行动并根据结果修改模型",
            "严谨思考是资源；和现实测试结合才形成学习",
        )
    return {
        "confidence": "exploratory_self_report",
        "principle": "短处被定义为特定条件下的高注意成本，而不是人的缺陷；矫正方式是替换策略并用结果验证。",
        "items": items[:4],
        "safe_exit": "如果问题持续造成显著痛苦、功能受损或安全风险，应停止自助练习并寻求专业支持。",
    }


def _agent_hypotheses(big_five: dict, jungian: dict | None, attention: dict | None = None) -> list[dict]:
    recommendations = []
    if big_five["conscientiousness"]["band"] == "lower":
        recommendations.append({"agent_id": "learning_strategist", "reason": "任务拆解与启动支持"})
        recommendations.append({"agent_id": "metacognition_coach", "reason": "复盘启动和收尾模式"})
    if big_five["emotional_stability"]["band"] == "lower":
        recommendations.append({"agent_id": "psychologist", "reason": "降低威胁感与恢复支持"})
    if big_five["openness"]["band"] == "higher":
        recommendations.append({"agent_id": "career_advisor", "reason": "把探索连接到长期方向"})
    if jungian and "Ti" in jungian["top_functions"]:
        recommendations.append({"agent_id": "subject_expert", "reason": "概念结构与原理校验"})
    if attention and attention.get("leakage_hypotheses"):
        recommendations.append({"agent_id": "neuro_cognition", "reason": "校准注意力成本与环境支持"})
    seen, result = set(), []
    for item in recommendations:
        if item["agent_id"] not in seen:
            seen.add(item["agent_id"])
            result.append(item)
    return result[:3]


def score_preassessment(responses: Mapping[str, int]) -> dict:
    big_five = _score_big_five(responses)
    mbti = _score_mbti(responses)
    jungian = _score_jungian(responses)
    attention = _attention_profile(big_five, mbti, jungian)
    correction = _cognitive_correction_plan(big_five, mbti, jungian, attention)
    strengths, frictions, supports = _big_five_hypotheses(big_five)
    supports.extend(_mbti_supports(mbti))
    if jungian and jungian["top_functions"]:
        supports.append("优先用 " + "、".join(jungian["top_functions"]) + " 所代表的偏好模式组织任务，同时给较弱模式外部脚手架")
    return {
        "profile_version": VERSION,
        "big_five": big_five,
        "mbti_preference": mbti,
        "jungian_functions": jungian,
        "attention_profile": attention,
        "cognitive_correction_plan": correction,
        "strength_hypotheses": strengths,
        "friction_hypotheses": frictions,
        "support_preferences": list(dict.fromkeys(supports))[:6],
        "agent_routing_hypotheses": _agent_hypotheses(big_five, jungian, attention),
        "confidence": "first_run_self_report",
        "user_review_required": True,
        "diagnosis": False,
        "notice": "这些是待用户确认的支持假设，不是问题标签清单、能力判决或临床诊断。",
    }


def submit_preassessment(student_id: str, responses: Mapping[str, int], *, consent: bool) -> dict:
    if consent is not True:
        raise ValueError("explicit_consent_required")
    profile = score_preassessment(responses)
    event_id = insert_event({
        "event_type": "preassessment_profile",
        "student_id": student_id,
        "source": "self_report_preassessment",
        "payload": {"profile": profile, "instrument_version": VERSION},
        "provenance": {"consent": True, "raw_responses_stored": False},
    })
    return {"event_id": event_id, "profile": profile}


def latest_preassessment(student_id: str) -> dict | None:
    events = [e for e in list_events(student_id) if e["event_type"] == "preassessment_profile"]
    if not events:
        return None
    latest = events[-1]
    return {**latest["payload"].get("profile", {}), "event_id": latest["event_id"], "created_at": latest["timestamp"]}
