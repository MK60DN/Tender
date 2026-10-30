"""Longitudinal multi-stage, multi-role simulation V4 for Tender."""
from __future__ import annotations

import json
import sys
import time
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, r"D:\Tender\agent_layer")
sys.path.insert(0, r"D:\Tender\experiments\simulated_user_agents")
from app.daoql import event_graph, insert_edge, insert_event
from app.preassessment import submit_preassessment
from app.tender_context import build_tender_context
import run_simulated_users as sim
import run_simulated_users_v2 as sim2

BASE = "http://127.0.0.1:8080"
OUT = Path(r"D:\Tender\产品管理文档")
RUN_ID = "long4-" + uuid.uuid4().hex[:6]
REPORT_VERSION = "4.0"
BASE_TIME = datetime(2026, 8, 1, tzinfo=timezone.utc)
ROUND_DAYS = [0, 7, 14, 21, 35, 49, 63, 84]

ADULT_PERSONA = {
    "id": "adult_self_study_work_family",
    "label": "成人自学者 · 工作家庭与自考复习",
    "tag": "中等开放、较高尽责、偏 F/J、Si/Te/Fe 较突出",
    "overrides": {
        "c1": 4, "c2": 4, "c3": 2, "c4": 4, "o1": 4, "o2": 3, "o3": 2, "o4": 4,
        "e1": 3, "e2": 3, "e3": 3, "e4": 3, "a1": 4, "a2": 4, "a3": 3, "a4": 4,
        "n1": 4, "n2": 4, "n3": 2, "n4": 2,
        "ei1": 3, "ei2": 3, "sn1": 3, "sn2": 4, "tf1": 3, "tf2": 4, "jp1": 4, "jp2": 4,
        "ne1": 3, "ni1": 3, "se1": 3, "si1": 4, "te1": 4, "ti1": 3, "fe1": 4, "fi1": 4,
    },
    "baseline": [
        {"event_type": "ambient_card_shown", "payload": {"kind": "fatigue", "task_hint": "自考复习"}},
        {"event_type": "answer", "payload": {"correct": False, "subject": "学习方法"}},
        {"event_type": "response", "payload": {"response_time_ms": 60000}},
        {"event_type": "metacognition_jol", "payload": {"predicted_correct": 8, "actual_correct": 4, "n_items": 10}},
    ],
    "rounds": [],
}

PERSONAS = [
    sim2.EXTRA_PERSONAS[0], sim2.EXTRA_PERSONAS[1], sim.PERSONAS[0], sim.PERSONAS[1],
    sim2.EXTRA_PERSONAS[2], sim.PERSONAS[2], sim2.EXTRA_PERSONAS[3], ADULT_PERSONA,
]

ROUNDS = {
    "primary_writing_frustration": [
        "我一看到作文题就发呆，妈妈一催我更不想写，我现在是什么状态？",
        "我先写了三句话，但不知道该怎样接着写。",
        "我写完一段了，可还是很担心会被说不好。",
        "今天换了一个小故事做素材，我反而写得快了一点。",
        "妈妈又催我时，我怎么提醒自己先写一小步？",
        "老师说我开头有进步，但我还是怕考试时写不出来。",
        "十二周后回头看，我哪些时候最容易卡住，下一步怎么保持？",
        "请综合我的基线、周期、元认知和知识节点，告诉我真正稳定的变化。",
    ],
    "middle_geometry_avoidance": [
        "同学都会做这道几何题，我一不会就不想上课，我现在是什么状态？",
        "我先画了图，但还是看不出辅助线，能给我一个最小提示吗？",
        "我做出一小步了，但还是担心考试时想不起来。",
        "这次错在条件没标全，我该怎么复盘才不变成抄答案？",
        "我想安排一周复习，但总被同伴进度影响，下一步怎么定？",
        "临考前我又开始躲几何题，这种回避和焦虑哪个更明显？",
        "换一道新几何题，我能先画图再找条件了，这算迁移吗？",
        "请综合我的基线、周期、元认知和知识节点，说明我是否在改善。",
    ],
    "high_school_attention_drift": [
        "我最近做数学函数题，总是换资料，题还没开始，我现在是什么状态？",
        "我用了停车区，但新想法还是老把我带走，现在该怎么办？",
        "我完成了一道题，但正确率不稳，我开始担心。",
        "两周后我发现晚上更容易进入状态，但白天不行，这算周期吗？",
        "考试临近，我计划很多但执行不了，我该怎么调整？",
        "一次模拟考没考好，我又想换整套学习方法，这像旧模式复现吗？",
        "这周我没有换资料，先把一道错题做到能讲出来，这说明什么？",
        "十二周后请综合我的基线、周期、元认知、群体和知识节点，告诉我哪些变化是真的。",
    ],
    "university_anxious_overchecking": [
        "我一做统计题就慌，反复检查，我现在是什么状态？",
        "我按一次检查上限做了，还是不安，现在该怎么办？",
        "我发现晚上做题更稳，但周中课程会打乱节奏。",
        "同学进度比我快，我又开始比较，帮我看看状态。",
        "项目与考研冲突，我不知道先做哪个，请给我下一步。",
        "这两周我按周计划走，断了一天就忍不住补量，基线会被毁掉吗？",
        "我在新的统计题里只检查一次也能完成，这和以前有什么不同？",
        "十二周后请综合我的基线、周期、元认知、群体和知识节点，我是否在改善？",
    ],
    "university_exam_project_conflict": [
        "我每天都列计划但完不成，看到别人进度就慌，我现在该怎么办？",
        "我今天只复习了两小时，觉得远远不够，现在不知道该怎么办。",
        "课程项目和考研冲突时，帮我判断状态和优先级，我应该先做哪一个？",
        "我按优先级做了，但还是会临时改计划，这是元认知偏差吗？",
        "我想用实习验证职业方向，又怕影响考研，怎么排一周节奏？",
        "连续几天晚上效率高，但白天低，我的周期是否已经稳定？",
        "这周我没有追求做完，只完成了三个最小块，为什么反而更稳？",
        "十二周后请综合我的基线、周期、元认知、群体和职业方向，判断下一步。",
    ],
    "career_transition_after_work": [
        "下班后学产品课就困，我不确定自己适不适合转行。",
        "十分钟能开始，但我担心坚持不了。",
        "我把课程拆小了，但有时加班完全断掉，这会影响基线吗？",
        "我在想转行是否值得，也容易和别人比较。",
        "我想验证产品经理能力，但不知道先做哪个项目。",
        "连续两周的晚间节律比较稳，但周末会乱，这种安排要改吗？",
        "我做了一个小项目并拿给同行反馈，这比继续看课更能验证方向吗？",
        "十二周后请综合我的基线、节律、元认知、群体和职业方向，告诉我下一步。",
    ],
    "graduate_research_analysis_paralysis": [
        "文献综述无法收束，我该怎么定研究问题？",
        "我写了一个问题又回去读，帮我看看当前状态。",
        "我做了最小实验，但结果不支持原假设，现在怎么办？",
        "导师预测和我实际进展不一致，这说明什么？",
        "我连续几天晚上效率高，但白天差，周期是否稳定？",
        "我又想扩大文献范围，怎么区分开放探索和逃避收束？",
        "这次我只补了三篇关键文献，就把问题写成可检验假设，这算进展吗？",
        "十二周后请综合我的基线、周期、元认知、群体和教师观测，判断下一步。",
    ],
    "adult_self_study_work_family": [
        "我下班后还要照顾家里，自考复习总是开始不了，我现在是什么状态？",
        "我把资料放进通勤包里，地铁上听了十分钟，但记不住，怎么办？",
        "周末想做完整复习，结果一拖再拖，我是不是没有自控力？",
        "家人觉得我学习没用，我一边生气一边更不想打开书。",
        "工作临时加班，原计划全乱了，我该怎样保住最小连续？",
        "我发现自己早上比晚上更能记住，但只有二十分钟，这算节律吗？",
        "这周我在通勤、午休和睡前各做了十分钟，反而比周末突击更稳。",
        "十二周后请综合我的基线、节律、元认知和长期目标，告诉我下一步。",
    ],
}

TASK_HINTS = {
    "primary_writing_frustration": ["语文作文", "语文作文", "语文阅读", "语文写作", "语文作文", "语文阅读", "语文写作", "语文学习方法"],
    "middle_geometry_avoidance": ["数学几何", "数学几何", "数学几何", "数学错题", "数学复习", "数学几何", "数学几何", "数学学习方法"],
    "high_school_attention_drift": ["数学函数", "数学函数", "数学错题", "数学学习节律", "数学复习", "数学函数", "数学错题", "数学学习方法"],
    "university_anxious_overchecking": ["统计", "统计", "统计学习节律", "统计复习", "学习计划", "统计", "统计", "统计学习方法"],
    "university_exam_project_conflict": ["考研数学", "考研复习", "课程项目", "学习计划", "职业方向", "学习节律", "考研复习", "职业与学习方法"],
    "career_transition_after_work": ["产品课程", "产品课程", "职业转行", "职业比较", "产品项目", "学习节律", "产品项目", "职业方向"],
    "graduate_research_analysis_paralysis": ["文献综述", "研究方法", "研究方法", "教师观测", "研究节律", "文献综述", "研究方法", "研究学习方法"],
    "adult_self_study_work_family": ["自考复习", "自考复习", "自考计划", "家庭沟通", "学习计划", "学习节律", "自考复习", "终身学习"],
}

NODE_IDS = {
    "primary_writing_frustration": "k12:chinese:domain:01",
    "middle_geometry_avoidance": "k12:math:unit:0303",
    "high_school_attention_drift": "k12:math:concept:020101",
    "university_anxious_overchecking": "k12:math:unit:0402",
    "university_exam_project_conflict": "k12:math:domain:02",
    "career_transition_after_work": "general:career:product",
    "graduate_research_analysis_paralysis": "general:research:method",
    "adult_self_study_work_family": "general:lifelong:learning",
}

ROLE_PROBES = [
    ("parent", "P-V4", ["孩子最近总说不想学，我怎么沟通才不加重压力？", "孩子晚上效率高、白天低，我该怎么安排家庭支持？"]),
    ("teacher", "T-V4", ["班里几个学生注意力下降，怎样分层支持？", "这道函数题的基础差异很大，如何设计最小任务？"]),
    ("head_teacher", "HT-V4", ["班级里哪些学生需要优先回访和家校沟通？", "怎样区分群体注意漂移和个别学生情绪问题？"]),
    ("sales", "SALES-V4", ["家长担心孩子坚持不了，我该用什么教学证据回应？", "哪些长期改善证据适合用于续费沟通，哪些不能用？"]),
    ("institution", "ORG-V4", ["下周排课怎样避开教师冲突并兼顾班级进度？", "班主任绩效里哪些指标来自可追溯交付证据？"]),
    ("health_advisor", "HEALTH-V4", ["学生连续熬夜、早餐很少，学习支持上先做什么？", "运动与睡眠信号怎样进入恢复建议但不做诊断？"]),
    ("psychology_advisor", "PSY-V4", ["学生说一考试就慌，支持边界和转介条件是什么？", "怎样帮助家长区分情绪支持与学习施压？"]),
    ("learning_science_advisor", "SCIENCE-V4", ["请综合基线、周期、元认知和教师metameta解释这名学生。", "怎样区分开放探索和逃避收束，而不把行为标签化？"]),
]

def make_events(student_id, persona_id, stable, round_index):
    days = ROUND_DAYS[round_index]
    hours = [19.0, 19.2, 19.4, 19.6, 19.8, 20.0] if stable else [6, 9, 13, 17, 21, 23]
    task_hint = TASK_HINTS[persona_id][round_index]
    provenance = {"synthetic": True, "run_id": RUN_ID, "round": round_index + 1}
    trigger_id = insert_event({
        "event_type": "learning_trigger", "student_id": student_id,
        "timestamp": (BASE_TIME + timedelta(days=days, hours=18)).isoformat(),
        "payload": {"task_hint": task_hint, "kind": "simulation", "round": round_index + 1},
        "source": "longitudinal_sim_v4", "provenance": provenance,
    })
    for j, hour in enumerate(hours):
        insert_event({
            "event_type": "learning_activity", "student_id": student_id,
            "timestamp": (BASE_TIME + timedelta(days=days, hours=hour, minutes=j * 4)).isoformat(),
            "payload": {"activity": "study", "intensity": round(1.0 - j * 0.08, 3), "round": round_index + 1},
            "source": "longitudinal_sim_v4", "provenance": provenance,
        })
    correct = round_index >= 2 if stable else [False, False, True, False, True, True, True, True][round_index]
    answer_id = insert_event({
        "event_type": "answer", "student_id": student_id,
        "timestamp": (BASE_TIME + timedelta(days=days, hours=20)).isoformat(),
        "payload": {"correct": correct, "node_id": NODE_IDS[persona_id], "subject": task_hint, "round": round_index + 1},
        "source": "longitudinal_sim_v4", "provenance": provenance,
    })
    response_id = insert_event({
        "event_type": "response", "student_id": student_id,
        "timestamp": (BASE_TIME + timedelta(days=days, hours=20, minutes=1)).isoformat(),
        "payload": {"response_time_ms": max(26000, 68000 - round_index * 5200 + (0 if stable else 5000)), "node_id": NODE_IDS[persona_id], "round": round_index + 1},
        "source": "longitudinal_sim_v4", "provenance": provenance,
    })
    predicted = 8 if stable else 9
    actual = 8 if correct else (4 if stable else 3)
    jol_id = insert_event({
        "event_type": "metacognition_jol", "student_id": student_id,
        "timestamp": (BASE_TIME + timedelta(days=days, hours=20, minutes=2)).isoformat(),
        "payload": {"predicted_correct": predicted, "actual_correct": actual, "n_items": 10, "round": round_index + 1},
        "source": "longitudinal_sim_v4", "provenance": provenance,
    })
    insert_edge(trigger_id, answer_id, "elicited_response", 0.84, {"round": round_index + 1})
    insert_edge(answer_id, response_id, "measured_time", 0.72, {"round": round_index + 1})
    return trigger_id, answer_id, response_id, jol_id


def seed_longitudinal_profile(student_id, persona, stable):
    submit_preassessment(student_id, sim.responses(persona["overrides"]), consent=True)
    provenance = {"synthetic": True, "run_id": RUN_ID}
    insert_event({
        "event_type": "baseline", "student_id": student_id,
        "timestamp": (BASE_TIME + timedelta(hours=8)).isoformat(),
        "payload": {"arrangement_fit": 0.84 if stable else 0.43, "habit_change": 0.12 if stable else 0.68},
        "source": "longitudinal_sim_v4", "provenance": provenance,
    })
    for i in range(10):
        insert_event({
            "event_type": "metacognition_mark", "student_id": student_id,
            "timestamp": (BASE_TIME + timedelta(days=i, hours=10)).isoformat(),
            "payload": {"marked": i % 3 == 0, "correct": i % 4 != 0},
            "source": "longitudinal_sim_v4", "provenance": provenance,
        })
    for i in range(6):
        insert_event({
            "event_type": "group_interaction", "student_id": student_id,
            "timestamp": (BASE_TIME + timedelta(days=i * 14, hours=15)).isoformat(),
            "payload": {"clustering": 0.22 if stable else 0.82, "bridge_ratio": 0.78 if stable else 0.18},
            "source": "longitudinal_sim_v4", "provenance": provenance,
        })
    for i in range(8):
        insert_event({
            "event_type": "teacher_prediction", "student_id": student_id,
            "timestamp": (BASE_TIME + timedelta(days=i * 10, hours=12)).isoformat(),
            "payload": {
                "confidence": ([48, 55, 62, 68, 75, 82, 88, 92][i] if stable else [90, 84, 78, 72, 66, 60, 54, 48][i]),
                "predicted_correct": ([4, 5, 6, 7, 8, 9, 9, 10][i] if stable else [9, 8, 8, 7, 6, 6, 5, 4][i]),
                "actual_correct": ([3, 4, 5, 7, 8, 9, 9, 10][i] if stable else [4, 3, 5, 2, 4, 3, 4, 3][i]),
            },
            "source": "longitudinal_sim_v4", "provenance": provenance,
        })


def compact_context(context):
    state = context.get("state") or {}
    meta = state.get("metacognition_profile") or {}
    baseline = state.get("baseline_model") or {}
    rhythm = state.get("rhythm") or {}
    group = state.get("group") or {}
    observer = state.get("observer") or {}
    digest = context.get("digest") or {}
    return {
        "context_version": context.get("context_version"), "event_count": context.get("event_count"),
        "knowledge_available": digest.get("knowledge_available"), "knowledge_node": digest.get("knowledge_node"),
        "baseline_available": digest.get("baseline_available"), "rhythm_available": digest.get("rhythm_available"),
        "group_clustering": digest.get("group_clustering"), "metameta_r": digest.get("metameta_r"),
        "metacognition_auc": digest.get("metacognition_auc"),
        "baseline_deviation_mean": baseline.get("deviation_mean"), "baseline_deviation_max": baseline.get("deviation_max"),
        "rhythm_label": rhythm.get("主导节律"), "R24": rhythm.get("日内强度R24"), "R168": rhythm.get("周内强度R168"),
        "rhythm_balance_B": rhythm.get("节律平衡B"), "group_bridge_ratio": group.get("bridge_ratio"),
        "metameta_n": (observer.get("teacher_metameta") or {}).get("n"),
        "metacognition_bias": meta.get("元认知偏差"), "d_prime": meta.get("d_prime"),
    }

def post_reply(student_id, headers, persona_id, round_index, message):
    payload = {
        "card_id": f"ambient_{RUN_ID}_{persona_id}_{round_index + 1}", "message": message,
        "scenario": "score_improvement",
        "agent_ids": ["metacognition_coach", "neuro_cognition", "learning_strategist", "subject_expert", "psychologist"],
    }
    last_error = None
    for attempt in range(3):
        try:
            reply = requests.post(BASE + f"/ambient/reply/{student_id}", headers=headers, json=payload, timeout=180)
            reply.raise_for_status()
            return reply.json()["reply_card"], None
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1.5 * (attempt + 1))
    return {}, last_error


def run_persona(persona, index):
    student_id = f"{RUN_ID}-{persona['id']}"
    stable = index in {0, 1, 4, 5}
    seed_longitudinal_profile(student_id, persona, stable)
    session = requests.post(
        BASE + "/auth/demo-session",
        json={"actor_id": student_id, "role": "learner", "learner_id": student_id}, timeout=15,
    )
    session.raise_for_status()
    headers = {"Authorization": "Bearer " + session.json()["token"]}
    turns, previous_outcome = [], None
    for i, message in enumerate(ROUNDS[persona["id"]]):
        trigger_id, answer_id, response_id, jol_id = make_events(student_id, persona["id"], stable, i)
        if previous_outcome:
            insert_edge(previous_outcome, trigger_id, "influences_next_round", 0.78, {"round": i + 1})
        context_response = requests.get(
            BASE + f"/tender/context/{student_id}", params={"message": message}, headers=headers, timeout=45,
        )
        context_response.raise_for_status()
        context = context_response.json()
        card, error = post_reply(student_id, headers, persona["id"], i, message)
        outcome = ["not_started", "partial", "partial", "blocked", "completed", "completed", "completed", "transferred"][i]
        outcome_id = insert_event({
            "event_type": "action_result", "student_id": student_id,
            "timestamp": (BASE_TIME + timedelta(days=ROUND_DAYS[i], hours=23)).isoformat(),
            "payload": {"round": i + 1, "action": "完成当前最小学习动作", "result": outcome, "agent_ids": card.get("routed_agent_ids", [])},
            "source": "longitudinal_sim_v4",
            "provenance": {"synthetic": True, "run_id": RUN_ID, "round": i + 1},
        })
        insert_edge(response_id, outcome_id, "action_outcome", 0.82, {"round": i + 1})
        insert_edge(jol_id, outcome_id, "self_evaluation_affects_action", 0.66, {"round": i + 1})
        previous_outcome = outcome_id
        turns.append({
            "round": i + 1, "days_from_start": ROUND_DAYS[i], "task_hint": TASK_HINTS[persona["id"]][i],
            "user_message": message, "reply": card.get("text"), "reply_error": error,
            "triage": card.get("triage"), "routed_agent_ids": card.get("routed_agent_ids"),
            "llm": card.get("llm"), "action_result": outcome, "context": compact_context(context),
        })
        time.sleep(0.15)
    graph = event_graph(student_id)
    final_context = build_tender_context(student_id, user_message="请综合长期变化")
    latest_profile = submit_preassessment(student_id, sim.responses(persona["overrides"]), consent=True)["profile"]
    return {
        "persona_id": persona["id"], "label": persona["label"], "tag": persona["tag"],
        "stable": stable, "student_id": student_id, "turns": turns,
        "profile": sim.profile_summary(latest_profile), "final_context": compact_context(final_context),
        "graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])},
    }


def role_probe(role, actor, messages):
    try:
        session_role = role if role in {"learner", "parent", "admin", "auditor", "advisor"} else "admin"
        session_actor = actor if session_role == role else "ADMIN-" + actor
        response = requests.post(
            BASE + "/auth/demo-session",
            json={"actor_id": session_actor, "role": session_role, "learner_id": "S01"}, timeout=15,
        )
        response.raise_for_status()
        headers = {"Authorization": "Bearer " + response.json()["token"]}
    except Exception as exc:
        return {"role": role, "status": "auth_failed", "error": str(exc), "routes": []}
    result = {"role": role, "status": "ok", "home": None, "routes": []}
    try:
        home = requests.get(BASE + f"/roles/{role}/home", params={"student_id": "S01", "class_id": "理科班"}, headers=headers, timeout=45)
        data = home.json() if home.content else {}
        advisor = ((data.get("data") or {}).get("advisor") or {})
        result["home"] = {
            "status": home.status_code, "name": (data.get("role") or {}).get("name"),
            "tier": advisor.get("tier"), "data_keys": list((data.get("data") or {}).keys()) if home.ok else [],
        }
    except Exception as exc:
        result["home"] = {"status": "error", "error": str(exc)}
    for message in messages:
        try:
            route = requests.post(
                BASE + "/advisors/route", headers=headers,
                json={"message": message, "student_id": "S01", "role": role,
                      "consent_scopes": ["minimal_safety_signals", "aggregated_tender_state", "emotion_support_signals",
                                         "cognitive_profile", "learning_passport_evidence", "assessment_evidence"]},
                timeout=45,
            )
            data = route.json() if route.content else {}
            result["routes"].append({
                "message": message, "status": route.status_code,
                "experts": [item.get("id") for item in data.get("selected_experts", [])],
                "safety": data.get("safety_level"),
            })
        except Exception as exc:
            result["routes"].append({"message": message, "status": "error", "error": str(exc)})
    if role == "sales":
        try:
            sales = requests.get(BASE + "/sales/ammunition/理科班", headers=headers, timeout=30)
            result["sales_ammunition"] = {"status": sales.status_code, "keys": list(sales.json().keys()) if sales.ok else []}
        except Exception as exc:
            result["sales_ammunition"] = {"status": "error", "error": str(exc)}
    return result

def markdown(payload):
    personas = payload["personas"]
    turns = [turn for persona in personas for turn in persona["turns"]]
    summary = payload["summary"]
    lines = [
        "# Tender 长期多阶段多角色连续测试报告 V4.0", "",
        "版本：4.0", f"日期：{datetime.now().astimezone().date().isoformat()}  ",
        f"运行编号：`{RUN_ID}`  ",
        "性质：合成用户、合成事件与合成行动结果；不是真人受试者研究，也不是统计因果证明。", "",
        "## 一、这次测试回答什么", "",
        "本轮不只验证单次问答是否可用，而是验证 Tender 能否在较长时间里把“触发、作答、迟疑、Agent 支持、行动结果、下一轮触发”连成可追溯的状态轨迹。", "",
        "| 维度 | 本版规模 |", "|---|---:|",
        f"| 学习者画像 | {len(personas)} |", f"| 连续轮次 | {len(turns)}（每人 8 轮） |",
        "| 时间跨度 | 12 周 |", f"| 角色探针 | {len(payload['roles'])} 类，每类 2 个场景 |",
        f"| 行动结果节点 | {len(turns)} |", f"| 有效 Agent 回复 | {summary['reply_ok_turns']} / {len(turns)} |", "",
        "覆盖的生活阶段包括小学、初中、高中、大学、考研/项目冲突、职场转行、研究生科研、成人自考。覆盖的功能包括预检测、注意画像、知识节点、DAOQL 事件与边、元认知、JOL、基线、R24/R168/节律平衡、群体聚类/桥接、教师 metameta、Triage 与多 Agent 回复。", "",
        "### 因果链如何记录", "", "每个学习者的每一轮都写入以下合成链路：", "",
        "```text", "学习触发 → 作答 → 响应时间 → JOL/元认知标记 → Agent 回复 → 行动结果 → 下一轮触发", "```", "",
        "DAOQL 中分别记录 `elicited_response`、`measured_time`、`self_evaluation_affects_action`、`action_outcome` 和 `influences_next_round`。这些边表示测试数据中的可追溯依赖关系，不表示估计出的真实因果效应。", "",
        "## 二、总体结果", "", "| 指标 | 结果 |", "|---|---:|",
        f"| 合成对话轮次 | {summary['turns']} |",
        f"| 至少一个 Agent 使用真实模型的轮次 | {summary['llm_used_turns']} / {summary['turns']} |",
        f"| 全部轮次携带 Tender 上下文 | {summary['context_turns']} / {summary['turns']} |",
        f"| 知识体系命中轮次 | {summary['knowledge_turns']} / {summary['turns']} |",
        f"| 预检测可用轮次 | {summary['preassessment_turns']} / {summary['turns']} |",
        f"| 最终基线可用 | {summary['final_baseline_available']} / {len(personas)} |",
        f"| 最终节律可用 | {summary['final_rhythm_available']} / {len(personas)} |",
        f"| 最终 metameta 可用 | {summary['final_metameta_available']} / {len(personas)} |",
        f"| 平均回复字数 | {summary['avg_reply_chars']} |",
        f"| 模板回退 Agent 次数 | {summary['fallback_agent_count']} |",
        f"| 回复以内部标签开头的轮次 | {summary['prefix_turns']} |", "",
        f"Triage 分布：`{json.dumps(summary['triage_counts'], ensure_ascii=False)}`", "",
        "### 稳定轨迹与漂移轨迹", "",
        "这里把 8 个合成学习者分为稳定轨迹与漂移轨迹两组，只用于检查系统能否产生不同状态形状，不用于证明模型具有分类能力。", "",
        "| 组别 | 人数 | 最终基线偏离均值 | 最终基线最大偏离 | R24 | R168 | 节律平衡 B | 聚类 | 桥接 | metameta_r |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, stable in [("稳定轨迹", True), ("漂移轨迹", False)]:
        group = [persona for persona in personas if persona["stable"] is stable]
        final = [persona["final_context"] for persona in group]
        def avg(key):
            vals = [float(item[key]) for item in final if item.get(key) is not None]
            return round(sum(vals) / len(vals), 4) if vals else None
        lines.append(
            f"| {label} | {len(group)} | {avg('baseline_deviation_mean')} | {avg('baseline_deviation_max')} | "
            f"{avg('R24')} | {avg('R168')} | {avg('rhythm_balance_B')} | {avg('group_clustering')} | "
            f"{avg('group_bridge_ratio')} | {avg('metameta_r')} |"
        )
    lines.extend([
        "", "稳定组被设计为时间更集中、节律更一致、行动结果逐步改善；漂移组被设计为时间分散、行动结果反复。该对照说明的是模拟数据能驱动不同轨迹，不是真人之间的效果差异。", "",
        "## 三、每个学习者的长期轨迹", "",
        "| 学习者 | 阶段/场景 | 轨迹 | 因果图 | 首轮基线 | 末轮基线 | 末轮周期 | 末轮 metameta | 知识节点 |",
        "|---|---|---|---:|---|---|---|---|---|",
    ])
    for persona in personas:
        first = persona["turns"][0]["context"]
        final = persona["final_context"]
        lines.append(
            f"| {persona['label']} | {persona['tag']} | {'稳定' if persona['stable'] else '漂移'} | "
            f"{persona['graph']['nodes']} / {persona['graph']['edges']} | {first.get('baseline_available')} | "
            f"{final.get('baseline_available')} | {final.get('rhythm_label') or '—'} | {final.get('metameta_r')} | "
            f"{final.get('knowledge_node') or '未命中具体节点'} |"
        )
    lines.extend([
        "", "### 功能随时间出现的方式", "",
        "| 学习者 | 第1轮知识 | 第1轮基线 | 第1轮周期 | 第1轮 metameta | 末轮基线 | 末轮周期 | 末轮群体 | 末轮 metameta |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    for persona in personas:
        first = persona["turns"][0]["context"]
        final = persona["final_context"]
        lines.append(
            f"| {persona['label']} | {first.get('knowledge_node') or '—'} | {first.get('baseline_available')} | "
            f"{first.get('rhythm_available')} | {first.get('metameta_r')} | {final.get('baseline_available')} | "
            f"{final.get('rhythm_available')} | {final.get('group_clustering')} | {final.get('metameta_r')} |"
        )
    lines.extend([
        "", "这张表用于验证“证据随时间累积后进入上下文”。它不表示第 1 轮不可用就一定是缺陷：有些模块本来就需要更多事件才能形成可用估计。", "",
        "## 四、逐轮测试记录与 Agent 回复", "",
    ])
    for persona in personas:
        final = persona["final_context"]
        lines.extend([
            f"### {persona['label']}", "",
            f"- 学生 ID：`{persona['student_id']}`", f"- 合成人格：{persona['tag']}",
            f"- 节律类型：{'稳定轨迹' if persona['stable'] else '漂移轨迹'}",
            f"- DAOQL 图：{persona['graph']['nodes']} 个节点 / {persona['graph']['edges']} 条边",
            f"- 末轮基线偏离：均值 {final.get('baseline_deviation_mean')}，最大 {final.get('baseline_deviation_max')}",
            f"- 末轮节律：{final.get('rhythm_label')}；R24={final.get('R24')}；R168={final.get('R168')}；B={final.get('rhythm_balance_B')}",
            f"- 末轮元认知：AUC={final.get('metacognition_auc')}；偏差={final.get('metacognition_bias')}；d′={final.get('d_prime')}",
            f"- 末轮群体：聚类={final.get('group_clustering')}；桥接={final.get('group_bridge_ratio')}",
            f"- 末轮教师 metameta：r={final.get('metameta_r')}；样本={final.get('metameta_n')}", "",
            "| 轮次 | 周 | 用户输入 | Triage | 知识节点 | 行动结果 | 回复长度 |",
            "|---:|---:|---|---|---|---|---:|",
        ])
        for turn in persona["turns"]:
            context = turn["context"]
            lines.append(
                f"| {turn['round']} | {round(turn['days_from_start'] / 7, 1)} | {turn['user_message']} | "
                f"{(turn.get('triage') or {}).get('problem_type')} | {context.get('knowledge_node') or '—'} | "
                f"{turn['action_result']} | {len(turn.get('reply') or '')} |"
            )
        lines.extend(["", "#### 每轮对话", ""])
        for turn in persona["turns"]:
            lines.extend([
                f"##### 第 {turn['round']} 轮 · 第 {round(turn['days_from_start'] / 7, 1)} 周", "",
                f"**用户：** {turn['user_message']}", "",
                f"**Agent：** {turn.get('reply') or '无有效回复'}", "",
            ])
    lines.extend([
        "## 五、多角色探针", "",
        "| 角色 | 工作台 | 场景 | 专家路由 | 安全级别 |", "|---|---|---|---|---|",
    ])
    for role in payload["roles"]:
        home = role.get("home") or {}
        for route in role.get("routes", []):
            experts = "、".join(route.get("experts") or []) or "未返回专家"
            lines.append(
                f"| {role['role']} | {home.get('status')} / {home.get('name') or '—'} | {route.get('message')} | {experts} | {route.get('safety')} |"
            )
    lines.extend([
        "", "说明：角色探针使用管理员演示会话代理调用目标角色，属于接口与权限代理测试；生产环境仍需真实身份、RBAC、对象授权与审计。", "",
        "## 六、因果与功能覆盖结论", "",
        "| 验证点 | 本版覆盖方式 | 能说明什么 | 不能说明什么 |", "|---|---|---|---|",
        "| 长期因果关系 | 每人 8 轮、12 周、行动结果回写下一轮 | 测试事件链可以持续累积并被 Agent 读取 | 不能说明真实干预导致改善 |",
        "| 基线 | 安排匹配、行为偏离与多轮作答 | 模型可以把长期轨迹压缩进上下文 | 不能当作临床或人格诊断 |",
        "| 周期/R24/R168/B | 稳定与漂移两种合成活动时间 | 不同节律形状会进入模型 | 不能证明真实作息因果效应 |",
        "| 元认知与 JOL | 预测正确数、实际结果、校准指标 | 系统能展示过度自信与犹豫轨迹 | 不能证明 JOL 能替代考试 |",
        "| 群体结构 | 聚类与桥接比例 | 群体信号能作为弱上下文出现 | 不能据此给学生贴标签 |",
        "| 教师 metameta | 8 条合成教师预测 | 能检验多来源观测的建模入口 | 不能证明教师判断准确 |",
        "| 知识节点 | 不同阶段任务提示与知识数据库匹配 | 能触发阶段化知识上下文 | 研究型与职业课程覆盖仍不完整 |",
        "| 多角色协作 | 家长、教师、班主任、销售、机构、健康、心理、学习科学 | 工作台与专家路由可被调用 | 不等于生产权限和多角色真实协作已验证 |", "",
        "## 七、发现的问题与下一轮修正", "",
        f"- 有效回复：{summary['reply_ok_turns']} / {summary['turns']}；失败轮次为 {summary['reply_failed_turns']}。",
        f"- 发生模板回退的 Agent 次数：{summary['fallback_agent_count']}。",
        f"- 回复以内部标签开头的轮次：{summary['prefix_turns']}。这类输出不应暴露给用户。",
        f"- 知识节点命中：{summary['knowledge_turns']} / {summary['turns']}。未命中的场景需要补充研究型、职业型与成人学习知识树。",
        "- metameta 只有 8 条合成教师预测，样本量很小，只能验证字段和回路存在，不能验证教师预测能力。",
        "- 当前合成时间主要写入学习事件；“长期”要看事件时间与因果边，不能把测试运行时长当成 12 周真人使用。",
        "- 本报告中的对话是合成用户对当前系统的调用结果。合成用户会不断重试并写入行为结果，真实用户不一定会这样反馈。", "",
        "## 八、研究边界与下一步", "",
        "下一步应做三类真人研究：第一，预注册的纵向观察，检验基线、周期与元认知信号是否预测后续行动恢复；第二，交替处理实验，比较不同 Agent 支持方式对最小行动完成率的影响；第三，公平性与误判审查，尤其是未成年人、焦虑用户和低资源学习者。", "",
        "在这些研究完成前，Tender 可以提供可更正的状态假设、行动建议和学习证据，但不能宣称能够诊断、替代考试或保证提分。",
    ])
    return "\n".join(lines)

def build_summary(personas, roles):
    turns = [turn for persona in personas for turn in persona["turns"]]
    final = [persona["final_context"] for persona in personas]
    triage_counts = Counter((turn.get("triage") or {}).get("problem_type", "unknown") for turn in turns)
    fallback = sum(len((turn.get("llm") or {}).get("fallback_agents") or []) for turn in turns)
    reply_ok = sum(bool(turn.get("reply")) and not turn.get("reply_error") for turn in turns)
    return {
        "personas": len(personas), "turns": len(turns), "weeks": 12, "roles": len(roles),
        "role_scenarios": sum(len(role.get("routes") or []) for role in roles),
        "llm_used_turns": sum(bool((turn.get("llm") or {}).get("used")) for turn in turns),
        "context_turns": sum(bool(turn.get("context")) for turn in turns),
        "knowledge_turns": sum(bool((turn.get("context") or {}).get("knowledge_available")) for turn in turns),
        "preassessment_turns": sum((turn.get("context") or {}).get("context_version") is not None for turn in turns),
        "final_baseline_available": sum(bool(item.get("baseline_available")) for item in final),
        "final_rhythm_available": sum(bool(item.get("rhythm_available")) for item in final),
        "final_metameta_available": sum(item.get("metameta_r") is not None for item in final),
        "reply_ok_turns": reply_ok, "reply_failed_turns": len(turns) - reply_ok,
        "avg_reply_chars": round(sum(len(turn.get("reply") or "") for turn in turns) / len(turns), 1),
        "fallback_agent_count": fallback,
        "prefix_turns": sum(1 for turn in turns if (turn.get("reply") or "").startswith("[")),
        "triage_counts": dict(triage_counts),
    }


if __name__ == "__main__":
    health = requests.get(BASE + "/health", timeout=15)
    health.raise_for_status()
    results = [run_persona(persona, index) for index, persona in enumerate(PERSONAS)]
    roles = [role_probe(role, actor, messages) for role, actor, messages in ROLE_PROBES]
    payload = {
        "meta": {"run_id": RUN_ID, "synthetic": True, "report_version": REPORT_VERSION,
                 "generated_at": datetime.now().astimezone().isoformat()},
        "summary": build_summary(results, roles), "personas": results, "roles": roles,
    }
    json_path = OUT / "Tender-长期多阶段多角色连续测试结果-V4.0.json"
    md_path = OUT / "Tender-长期多阶段多角色连续测试报告-V4.0.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(markdown(payload), encoding="utf-8")
    print(json.dumps({"run_id": RUN_ID, "json": str(json_path), "markdown": str(md_path), **payload["summary"]}, ensure_ascii=False))
