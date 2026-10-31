"""Strict function-attitude onboarding and dynamic Big Five pulse for Tender."""
from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Mapping

from .daoql import insert_event, list_events

BASE = Path(__file__).resolve().parents[2] / "knowledge_data"
BIG_FIVE_PATH = BASE / "preassessment_big_five_items.json"
WORLD_INTERFACE_PATH = BASE / "preassessment_world_interface_items.json"
BIG_FIVE_PULSE_PATH = BASE / "preassessment_big_five_pulse_items.json"

VERSION = "world-tree-profile-1.0"
PULSE_VERSION = "big-five-pulse-1.0"

BIG_FIVE_DIMENSIONS = {
    "openness": "开放性",
    "conscientiousness": "尽责性",
    "extraversion": "外向性",
    "agreeableness": "宜人性",
    "emotional_stability": "情绪稳定性",
}

FUNCTION_META = {
    "Se": {"label": "现实观察", "attitude": "extraverted", "mode": "perception", "attitude_label": "外倾", "first_step": "先看现在具体发生了什么、有哪些材料、限制和可验证线索。", "support": "先给真实场景、例子和可执行步骤，再补充框架。"},
    "Si": {"label": "经验对照", "attitude": "introverted", "mode": "perception", "attitude_label": "内倾", "first_step": "先回忆过去是否出现过类似情况，并对照个人基线。", "support": "先连接熟悉经验和历史数据，再引入新方法。"},
    "Ne": {"label": "可能性探索", "attitude": "extraverted", "mode": "perception", "attitude_label": "外倾", "first_step": "先列出几种可能解释或路径，再选一个做现实实验。", "support": "先发散可能性，但必须设置范围、优先顺序和收尾条件。"},
    "Ni": {"label": "长期整合", "attitude": "introverted", "mode": "perception", "attitude_label": "内倾", "first_step": "先确认长期方向和整体模式，再倒推当前节点。", "support": "先给整体框架和长期意义，再拆成可验证的小步骤。"},
    "Te": {"label": "结果执行", "attitude": "extraverted", "mode": "judgment", "attitude_label": "外倾", "first_step": "先定义目标、完成标准、截止时间和可交付结果。", "support": "先给标准、时间点、优先级和结果反馈。"},
    "Ti": {"label": "结构建模", "attitude": "introverted", "mode": "judgment", "attitude_label": "内倾", "first_step": "先检查概念、条件和因果结构，再决定怎么行动。", "support": "先讲清原理和判断依据，再连接现实测试。"},
    "Fe": {"label": "关系协调", "attitude": "extraverted", "mode": "judgment", "attitude_label": "外倾", "first_step": "先看这件事涉及谁、对方需要什么、共同规则是什么。", "support": "先说明对关系和合作的影响，再形成共同行动。"},
    "Fi": {"label": "价值边界", "attitude": "introverted", "mode": "judgment", "attitude_label": "内倾", "first_step": "先确认这件事是否符合价值、真实意愿和边界。", "support": "先澄清价值、边界和个人意义，再把选择变成行动。"},
}

WORLD_ENTRY = {
    "objective_first": {"label": "更自然地先进入客观世界", "description": "你通常更容易从可观察的事实、现实任务和外部反馈开始，再逐渐形成内部理解。", "first_step": "先建立现实坐标：当前任务、时间、资源、人物和可验证结果。", "guardrail": "进入现实行动后，要补一次内部整合，避免只忙不做、只有结果没有意义。"},
    "subjective_first": {"label": "更自然地先整理主观世界", "description": "你通常更容易先形成内部模型、长期方向或价值判断，再与外部现实接触。", "first_step": "先画清当前理解、假设、价值和不确定点，再设计一个现实探针。", "guardrail": "内部模型必须经过一个真实行动或外部反馈验证，避免只建模不接触现实。"},
    "bridge_first": {"label": "更适合从一件真实卡点进入", "description": "你没有明显固定的入口，从当前最具体的卡点进入更容易同时看到现实和内在假设。", "first_step": "选一件最近推进不下去的真实事情，分别记录客观事实和主观解释。", "guardrail": "避免一开始做抽象人格分析；先处理一个现实问题，再让模型逐步显现。"},
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def preassessment_items() -> dict:
    return {
        "version": VERSION,
        "estimated_minutes": "7-9",
        "consent_notice": "这是自我反思与支持假设工具，不是诊断。系统只保存标准化分数，不默认保存逐题原文；所有结果都可以更正或重测。",
        "big_five": _load(BIG_FIVE_PATH),
        "world_interface": _load(WORLD_INTERFACE_PATH),
    }


def big_five_pulse_items() -> dict:
    return _load(BIG_FIVE_PULSE_PATH)


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


def _score_big_five_from_items(items: list[dict], responses: Mapping[str, int]) -> dict:
    missing = [item["id"] for item in items if item["id"] not in responses]
    if missing:
        raise ValueError("incomplete_big_five:" + ",".join(missing))
    grouped: dict[str, list[float]] = {}
    for item in items:
        raw = float(responses[item["id"]])
        grouped.setdefault(item["dimension"], []).append(_normalize(raw, bool(item.get("reverse"))))
    scores = {dim: sum(values) / len(values) for dim, values in grouped.items()}
    sensitivity = scores.pop("emotional_sensitivity")
    scores["emotional_stability"] = 1 - sensitivity
    return {key: {"label": BIG_FIVE_DIMENSIONS[key], "score": round(value, 4), "band": _band(value)} for key, value in scores.items()}


def _score_big_five(responses: Mapping[str, int]) -> dict:
    return _score_big_five_from_items(_load(BIG_FIVE_PATH)["items"], responses)


def _score_world_interface(responses: Mapping[str, int]) -> dict:
    items = _load(WORLD_INTERFACE_PATH)["items"]
    missing = [item["id"] for item in items if item["id"] not in responses]
    if missing:
        raise ValueError("incomplete_world_interface:" + ",".join(missing))
    grouped: dict[str, list[float]] = {}
    for item in items:
        raw = float(responses[item["id"]])
        grouped.setdefault(item["function"], []).append(_normalize(raw, False))
    functions = {}
    for code, values in grouped.items():
        score = sum(values) / len(values)
        spread = statistics.pstdev(values) if len(values) > 1 else 0.0
        consistency = max(0.0, min(1.0, 1.0 - spread * 2.0))
        meta = FUNCTION_META[code]
        functions[code] = {
            "label": meta["label"], "attitude": meta["attitude"], "attitude_label": meta["attitude_label"],
            "mode": meta["mode"], "score": round(score, 4), "consistency": round(consistency, 4),
            "confidence": "moderate" if consistency >= 0.65 else "low" if consistency >= 0.35 else "very_low",
            "first_step": meta["first_step"], "support": meta["support"],
        }
    extraverted = [value["score"] for value in functions.values() if value["attitude"] == "extraverted"]
    introverted = [value["score"] for value in functions.values() if value["attitude"] == "introverted"]
    extra_avg = sum(extraverted) / len(extraverted)
    intro_avg = sum(introverted) / len(introverted)
    difference = extra_avg - intro_avg
    entry_code = "objective_first" if difference > 0.08 else "subjective_first" if difference < -0.08 else "bridge_first"
    entry = dict(WORLD_ENTRY[entry_code])
    entry["code"] = entry_code
    ordered = sorted(functions.items(), key=lambda pair: pair[1]["score"], reverse=True)
    top = [code for code, _ in ordered[:3]]
    less = [code for code, _ in ordered[-2:]]
    return {
        "version": "eight-function-attitudes-1.0",
        "functions": functions,
        "matrix": {"extraverted": {"sensation": "Se", "intuition": "Ne", "thinking": "Te", "feeling": "Fe"}, "introverted": {"sensation": "Si", "intuition": "Ni", "thinking": "Ti", "feeling": "Fi"}},
        "extraverted_average": round(extra_avg, 4), "introverted_average": round(intro_avg, 4),
        "attitude_balance": {"difference": round(difference, 4), "preferred_attitude": "extraverted" if difference > 0.08 else "introverted" if difference < -0.08 else "balanced"},
        "gateway": {"function": ordered[0][0], "label": ordered[0][1]["label"], "first_step": ordered[0][1]["first_step"]},
        "top_functions": top, "less_used": less, "world_entry": entry,
        "confidence": "structured_self_report",
        "notice": "八功能态度用于描述当前更自然的世界入口和支持方式，不是固定类型、能力排名或临床诊断。",
    }
def _big_five_hypotheses(big_five: dict) -> tuple[list[str], list[str], list[str]]:
    strengths, frictions, supports = [], [], []
    rules = {
        "conscientiousness": {"higher": ("计划、拆解和持续完成", "计划被打断时可能过度自责或追求完美", "提供可调整的计划，而不是增加更多清单"), "lower": ("灵活应变、保留探索空间", "任务启动、收尾和重复执行可能更耗力", "使用外部提醒、最小步骤和明确收尾")},
        "openness": {"higher": ("探索、联想和新方法尝试", "选项过多时容易发散或偏离目标", "同时给探索空间和清晰的边界"), "lower": ("稳定、经验和可复用流程", "陌生方法或频繁变化可能增加摩擦", "先给具体例子，再逐步引入新方法")},
        "extraversion": {"higher": ("主动表达、求助和互动", "外部刺激过多时可能难以安静收束", "用短对话和互动式复盘"), "lower": ("独立思考、深度专注和观察", "主动求助或临场表达可能更耗能", "默认文字优先，提前给问题和准备时间")},
        "agreeableness": {"higher": ("合作、共情和关系维护", "可能为了照顾他人而压抑自己的需要", "在关键处提供温和但直接的边界提示"), "lower": ("直接、边界和批判性判断", "冲突情境中可能显得过直或难以协作", "用具体影响和共同目标表达分歧")},
        "emotional_stability": {"higher": ("压力恢复、稳定执行", "可能忽略早期疲劳和风险信号", "保留定期状态检查，而不是只看产出"), "lower": ("敏感、风险觉察和共情", "批评、不确定和高压可能占用较多认知资源", "先降低威胁感，再拆出可控下一步")},
    }
    for dimension, value in big_five.items():
        band = value["band"]
        if band in ("higher", "lower"):
            strength, friction, support = rules[dimension][band]
            strengths.append(f"{value['label']}偏高：{strength}")
            frictions.append(f"{value['label']}{'偏高' if band == 'higher' else '偏低'}时：{friction}")
            supports.append(support)
    return strengths[:4], frictions[:4], supports[:4]


def _world_interface_hypotheses(world: dict) -> tuple[list[str], list[str], list[str]]:
    strengths, frictions, supports = [], [], []
    top = world["top_functions"]
    less = world["less_used"]
    for code in top:
        value = world["functions"][code]
        strengths.append(f"更容易从「{value['label']}」开始：{value['first_step']}")
        supports.append(value["support"])
    if world["world_entry"]["code"] == "objective_first":
        supports.append("先给现实坐标和行动反馈，再补内部整合。")
    elif world["world_entry"]["code"] == "subjective_first":
        supports.append("先给整体框架和价值澄清，再要求一个现实探针。")
    else:
        supports.append("先从一个真实卡点同时记录事实与解释。")
    if less:
        labels = "、".join(world["functions"][code]["label"] for code in less)
        frictions.append(f"「{labels}」不是默认入口，压力高时可能需要外部脚手架。")
    return strengths[:4], frictions[:2], supports[:5]


def _attention_profile(big_five: dict, world: dict) -> dict:
    capture, sustain, leakage, recovery, scaffolds = [], [], [], [], []
    top = set(world["top_functions"])
    if "Se" in top:
        capture.append("现场变化、真实材料和即时反馈更容易激活注意")
        sustain.append("短任务、动手操作和可见进展有助于持续投入")
        leakage.append("环境变化过多时可能不断被新刺激带走")
    if "Si" in top:
        capture.append("熟悉线索、固定流程和历史对比更容易稳定注意")
        recovery.append("固定作息、熟悉环境和重复仪式有助于恢复")
        leakage.append("环境或规则突然变化时可能消耗额外注意")
    if "Ne" in top:
        capture.append("新颖性、可能性和跨领域联系更容易吸引注意")
        sustain.append("适度变化和探索空间有助于保持投入")
        leakage.append("选项过多时可能不断切换方向")
    if "Ni" in top:
        capture.append("长期方向和整体洞察更容易吸引深入思考")
        scaffolds.append("先确认长期目标，再把当前任务连接到目标")
        leakage.append("过度追求完整解释时可能迟迟不开始现实测试")
    if "Te" in top:
        capture.append("明确目标、完成标准和进度反馈更容易激活注意")
        sustain.append("计划、检查点和可见产出有助于持续完成")
        leakage.append("过度追求效率时可能忽略疲劳和关系信号")
    if "Ti" in top:
        capture.append("概念一致性和推理闭环更容易吸引持续思考")
        scaffolds.append("先写清判断标准，再开始处理信息")
        leakage.append("反复校验概念可能造成分析瘫痪")
    if "Fe" in top:
        capture.append("互动、共同目标和关系反馈更容易激活注意")
        recovery.append("真实交流和有边界的合作有助于恢复")
        leakage.append("过度照顾他人需求可能切碎自己的任务注意")
    if "Fi" in top:
        capture.append("与个人价值和真实感受一致的任务更容易投入")
        recovery.append("价值澄清、自我对话和边界确认有助于恢复")
        leakage.append("内在价值冲突可能造成沉默、回避或迟迟不选")
    if big_five["conscientiousness"]["band"] == "lower":
        sustain.append("短时冲刺、外部提醒和清晰收尾比长清单更有效")
        leakage.append("任务边界模糊时更容易启动困难或留下开放循环")
    if big_five["emotional_stability"]["band"] == "lower":
        capture.append("威胁、不确定和评价线索更容易抢占注意")
        leakage.append("担心结果或反复检查会占用工作记忆")
        scaffolds.append("先降低威胁感，再把任务缩小到一个可控步骤")
    if big_five["extraversion"]["band"] == "lower":
        leakage.append("高频社交或临场表达可能额外消耗注意")
        recovery.append("独处和异步准备有助于恢复")
    elif big_five["extraversion"]["band"] == "higher":
        capture.append("互动和即时反馈更容易激活注意")
    if big_five["agreeableness"]["band"] == "higher":
        leakage.append("过度照顾他人需求可能造成频繁中断或难以拒绝")
    if world["world_entry"]["code"] == "objective_first":
        scaffolds.append("每次现实行动后补一句：这件事让我对内外部世界有什么新理解？")
    elif world["world_entry"]["code"] == "subjective_first":
        scaffolds.append("每次内部建模后必须接一个十分钟内能完成的外部验证。")
    scaffolds.extend(["一次只保留一个主任务和一个下一步", "为任务设置明确的停止与收尾条件"])
    return {
        "capture_hypotheses": list(dict.fromkeys(capture))[:5],
        "sustain_hypotheses": list(dict.fromkeys(sustain))[:5],
        "leakage_hypotheses": list(dict.fromkeys(leakage))[:5],
        "recovery_preferences": list(dict.fromkeys(recovery))[:5],
        "scaffold_suggestions": list(dict.fromkeys(scaffolds))[:6],
        "world_entry": world["world_entry"],
        "confidence": "exploratory_self_report",
        "boundary": "注意力画像来自八功能态度和近期心理资源自评，不是注意力测评、神经测量或 ADHD 诊断。",
    }
def _cognitive_correction_plan(big_five: dict, world: dict, attention: dict) -> dict:
    items = []
    top = set(world["top_functions"])

    def add(item_id, pattern, trigger, practice, evidence, boundary):
        items.append({
            "id": item_id, "pattern_hypothesis": pattern, "trigger": trigger,
            "correction_practice": practice, "success_evidence": evidence,
            "fade_rule": "连续两次成功后减少提示，并把策略交还给用户", "boundary": boundary,
        })

    if "Ne" in top and "Te" not in top:
        add("idea_sprawl", "想法扩展快，但容易出现多个开放分支", "新点子多、截止时间模糊、需要收束", "先保留一个主任务；新想法放停车区；定义今天必须交付的一个结果", "主任务完成一个可交付版本，停车区仍可回看", "这是策略练习，不用于诊断注意力缺陷")
    if "Ni" in top and "Se" not in top:
        add("inner_loop", "容易先形成完整内部解释，现实测试不足", "长期问题、信息不完整、害怕做错", "写下一个可证伪假设，并设计十分钟现实探针", "获得一次外部反馈并更新原假设", "深思是资源；接触现实才形成学习")
    if "Se" in top and "Ni" not in top:
        add("present_bias", "容易被当下任务和即时反馈带走", "连续行动、缺少复盘、刺激很多", "每次行动结束时写一句结果与下一步", "连续三次行动后能说出模式和调整", "行动力不是缺陷；复盘让行动形成积累")
    if "Ti" in top:
        add("analysis_paralysis", "反复校验概念一致性，行动测试迟迟不开始", "标准不清、信息不完整、害怕犯错", "先写出当前最佳解释和可证伪行动", "完成一次可验证行动并根据结果修改模型", "严谨思考是资源；和现实测试结合才形成学习")
    if "Fe" in top:
        add("relational_overload", "优先维持关系，自己的任务边界容易被切碎", "临时求助、冲突、担心让别人失望", "先确认当前任务和可承诺时间，再回应关系需求", "保留一段完整任务时间并清楚表达边界", "边界不等于冷漠；不以人格评分评判关系")
    if "Fi" in top and "Te" not in top:
        add("value_isolation", "需要价值一致才行动，但可能缺少外部完成标准", "价值冲突、选择过多、害怕违背自己", "把价值转成一个可观察作品或选择标准", "完成一个不违背价值且可被他人检验的小结果", "内在价值需要现实表达才能进入关系")
    if "Te" in top and "Fi" not in top:
        add("outcome_only", "容易只看结果和效率，忽略价值与关系成本", "截止期紧、团队压力高、连续执行", "在行动前补一句：谁会受影响、我愿意承担什么", "在结果达成时仍能说明边界和关系影响", "效率是资源；承担与关系也需要被纳入结果")
    if "Si" in top and "Ne" not in top:
        add("familiar_lock", "熟悉经验稳定，但可能低估新环境变化", "规则变化、陌生任务、旧方法失效", "保留熟悉锚点，同时做一个低成本新尝试", "比较旧方法与新方法的一次真实结果", "稳定不是保守；比较可以降低变化风险")
    if big_five["emotional_stability"]["band"] == "lower":
        add("threat_load", "评价、不确定和冲突更容易占用工作记忆", "公开评价、结果未知、关系冲突", "先降低威胁感，再把任务缩小到一个可控步骤", "能在压力情境中完成一个最小步骤并恢复", "不是心理诊断；持续困扰时寻求专业支持")
    if big_five["conscientiousness"]["band"] == "lower":
        add("task_start", "任务启动、收尾和重复执行可能更耗力", "任务过长、边界模糊、没有外部提醒", "使用外部提醒、最小步骤和明确收尾", "连续两次完成约定的小步骤", "需要结构不是缺陷；外部脚手架可以逐步淡出")
    distinct, seen = [], set()
    for item in items:
        if item["id"] not in seen:
            seen.add(item["id"])
            distinct.append(item)
    return {
        "confidence": "exploratory_self_report",
        "principle": "短处被定义为特定条件下的高注意成本，而不是人的缺陷；矫正方式是替换策略并用结果验证。",
        "items": distinct[:5],
        "safe_exit": "如果问题持续造成显著痛苦、功能受损或安全风险，应停止自助练习并寻求专业支持。",
    }


def _agent_hypotheses(big_five: dict, world: dict, attention: dict) -> list[dict]:
    recommendations = []
    top = set(world["top_functions"])
    if top & {"Te", "Ne", "Si"}:
        recommendations.append({"agent_id": "learning_strategist", "reason": "把世界入口转成可执行任务与收束条件"})
    if "Ti" in top:
        recommendations.append({"agent_id": "subject_expert", "reason": "概念、条件和因果结构校验"})
    if "Fe" in top:
        recommendations.append({"agent_id": "external_communication", "reason": "关系协调与对外沟通"})
    if top & {"Fi", "Ni"}:
        recommendations.append({"agent_id": "career_advisor", "reason": "长期方向与价值澄清"})
    if top & {"Se", "Si"}:
        recommendations.append({"agent_id": "metacognition_coach", "reason": "把经验与行动结果转成复盘"})
    if big_five["conscientiousness"]["band"] == "lower":
        recommendations.append({"agent_id": "learning_strategist", "reason": "任务启动与收尾支持"})
    if big_five["emotional_stability"]["band"] == "lower":
        recommendations.append({"agent_id": "psychologist", "reason": "降低威胁感与恢复支持"})
    if attention.get("leakage_hypotheses"):
        recommendations.append({"agent_id": "neuro_cognition", "reason": "校准注意成本与环境支持"})
    seen, result = set(), []
    for item in recommendations:
        if item["agent_id"] not in seen:
            seen.add(item["agent_id"])
            result.append(item)
    return result[:3]


def score_preassessment(responses: Mapping[str, int]) -> dict:
    big_five = _score_big_five(responses)
    world = _score_world_interface(responses)
    attention = _attention_profile(big_five, world)
    correction = _cognitive_correction_plan(big_five, world, attention)
    strengths, frictions, supports = _big_five_hypotheses(big_five)
    world_strengths, world_frictions, world_supports = _world_interface_hypotheses(world)
    return {
        "profile_version": VERSION,
        "big_five": big_five,
        "world_interface": world,
        "attention_profile": attention,
        "cognitive_correction_plan": correction,
        "strength_hypotheses": list(dict.fromkeys(strengths + world_strengths))[:5],
        "friction_hypotheses": list(dict.fromkeys(frictions + world_frictions))[:5],
        "support_preferences": list(dict.fromkeys(supports + world_supports))[:7],
        "agent_routing_hypotheses": _agent_hypotheses(big_five, world, attention),
        "observation_policy": {
            "world_entry": world["world_entry"],
            "gateway": world["gateway"],
            "rule": "先按用户当前问题与风险分诊，再用世界入口调整提问和任务组织；不得用功能态度决定能力或命运。",
        },
        "confidence": "first_run_self_report",
        "user_review_required": True,
        "diagnosis": False,
        "notice": "这些是待用户确认的支持假设，不是人格标签、能力判决或临床诊断。",
    }


def submit_preassessment(student_id: str, responses: Mapping[str, int], *, consent: bool) -> dict:
    if consent is not True:
        raise ValueError("explicit_consent_required")
    profile = score_preassessment(responses)
    event_id = insert_event({
        "event_type": "preassessment_profile", "student_id": student_id,
        "source": "structured_world_interface_and_big_five",
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

def score_big_five_pulse(responses: Mapping[str, int]) -> dict:
    scores = _score_big_five_from_items(_load(BIG_FIVE_PULSE_PATH)["items"], responses)
    return {
        "pulse_version": PULSE_VERSION,
        "big_five": scores,
        "confidence": "brief_state_pulse",
        "notice": "脉搏反映近期状态与恢复，不替代完整人格基线，也不用于诊断。",
    }


def submit_big_five_pulse(student_id: str, responses: Mapping[str, int], *, consent: bool, context: dict | None = None) -> dict:
    if consent is not True:
        raise ValueError("explicit_consent_required")
    profile = score_big_five_pulse(responses)
    safe_context = {
        key: context.get(key)
        for key in ("relationship", "role", "task", "period", "note")
        if context and context.get(key) is not None
    }
    event_id = insert_event({
        "event_type": "big_five_pulse", "student_id": student_id, "source": "big_five_pulse",
        "payload": {"profile": profile, "context": safe_context},
        "provenance": {"consent": True, "raw_responses_stored": False},
    })
    return {"event_id": event_id, "profile": profile, "context": safe_context}


def latest_big_five_pulse(student_id: str) -> dict | None:
    events = [e for e in list_events(student_id) if e["event_type"] == "big_five_pulse"]
    if not events:
        return None
    latest = events[-1]
    return {**latest["payload"].get("profile", {}), "context": latest["payload"].get("context", {}), "event_id": latest["event_id"], "created_at": latest["timestamp"]}


def big_five_change_state(student_id: str) -> dict:
    baseline = latest_preassessment(student_id)
    if not baseline or not baseline.get("big_five"):
        return {"available": False, "note": "尚未建立大五基线"}
    pulse_events = [e for e in list_events(student_id) if e["event_type"] == "big_five_pulse"][-6:]
    if not pulse_events:
        return {"available": False, "note": "尚未记录大五状态脉搏", "baseline_at": baseline.get("created_at")}
    series = [event["payload"]["profile"]["big_five"] for event in pulse_events]
    current = series[-1]
    dimensions = {}
    supports = []
    for key, baseline_value in baseline["big_five"].items():
        base = float(baseline_value["score"])
        now = float(current[key]["score"])
        delta = round(now - base, 4)
        values = [float(item[key]["score"]) for item in series]
        volatility = round(statistics.pstdev(values), 4) if len(values) > 1 else 0.0
        direction = "higher_than_baseline" if delta > 0.08 else "lower_than_baseline" if delta < -0.08 else "near_baseline"
        dimensions[key] = {"baseline": round(base, 4), "current": round(now, 4), "delta": delta, "direction": direction, "volatility": volatility}
    if dimensions["extraversion"]["delta"] < -0.1:
        supports.append("社交电量可能低于基线：优先异步、缩短互动并保留恢复时间。")
    if dimensions["agreeableness"]["delta"] < -0.1:
        supports.append("合作敏感度可能变化：先确认边界与冲突来源，不把它解释为人变坏。")
    if dimensions["conscientiousness"]["delta"] < -0.1:
        supports.append("近期履约成本可能升高：缩小承诺、写清检查点并减少并行任务。")
    if dimensions["emotional_stability"]["delta"] < -0.1:
        supports.append("近期对评价和冲突更敏感：降低威胁线索，先给可控下一步。")
    if dimensions["openness"]["delta"] < -0.1:
        supports.append("近期更依赖熟悉方法：先连接稳定经验，再引入变化。")
    if not supports:
        supports.append("当前大五脉搏接近个人基线；继续观察跨情境变化，不急于重新定性。")
    return {
        "available": True,
        "baseline_at": baseline.get("created_at"),
        "latest_pulse_at": pulse_events[-1].get("timestamp"),
        "pulses_used": len(series),
        "dimensions": dimensions,
        "relationship_support": supports,
        "boundary": "变化反映近期状态和情境，不等于人格永久改变；只用于沟通、负荷和关系支持。",
    }