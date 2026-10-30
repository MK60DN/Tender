"""学生、教师、家长、机构报告。"""
from __future__ import annotations
from .guardrails import filter_parent_report


def student_report(state: dict) -> dict:
    mastery = state.get("knowledge", {}).get("mastery", 0.5)
    bias = state.get("metacognition", {}).get("jol_bias", 0.0)
    hesitation = state.get("metacognition", {}).get("hesitation", 0.0)
    fit = state.get("baseline", {}).get("arrangement_fit", 0.5)
    actions = []
    if mastery < 0.6: actions.append("优先补知识缺口：最小提示 → 变式 → 复述")
    if bias > 0.1: actions.append("做 JOL 校准：测试前预测，批改后对比")
    if hesitation > 0.5: actions.append("识别犹豫：先问卡点，再给提示")
    if fit < 0.5: actions.append("检查排课与节律匹配度")
    return {"student_id": state.get("student_id"), "mastery": mastery,
            "jol_bias": bias, "hesitation": hesitation, "arrangement_fit": fit,
            "next_actions": actions or ["保持当前节奏，做迁移题"]}


def teacher_report(states: list[dict]) -> dict:
    states = sorted(states, key=lambda s: s.get("knowledge", {}).get("mastery", 1.0))
    top = [{"student_id": s.get("student_id"),
            "mastery": s.get("knowledge", {}).get("mastery"),
            "jol_bias": s.get("metacognition", {}).get("jol_bias"),
            "hesitation": s.get("metacognition", {}).get("hesitation")} for s in states[:3]]
    n = len(states)
    avg = sum(s.get("knowledge", {}).get("mastery", 0.5) for s in states) / n if n else 0.0
    return {"n_students": n, "class_mastery_mean": round(avg, 4),
            "top_intervention": top,
            "suggestion": "先处理低掌握 + 高犹豫的学生；再用 JOL 校准处理高偏差学生。"}


def parent_report(state: dict, week: str = "") -> dict:
    mastery = state.get("knowledge", {}).get("mastery", 0.5)
    progress = "本周整体稳定" if mastery >= 0.6 else "本周在基础知识点上需要更多练习"
    action = "每天用 10 分钟做一次‘先预测、再作答、后复盘’的小练习。"
    return filter_parent_report({"student_id": state.get("student_id"), "week": week,
                                 "progress_summary": progress, "one_home_action": action})


def org_report(states: list[dict]) -> dict:
    n = len(states)
    avg = sum(s.get("knowledge", {}).get("mastery", 0.5) for s in states) / n if n else 0.0
    risk = sum(1 for s in states if s.get("knowledge", {}).get("mastery", 0.5) < 0.5)
    return {"n_students": n, "avg_mastery": round(avg, 4), "at_risk": risk,
            "note": "机构报告只使用聚合数据，不含 PII。"}
