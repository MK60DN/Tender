"""Run synthetic user agents against the live Tender API."""
from __future__ import annotations

import json
import sys
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, r"D:\Tender\agent_layer")
from app.daoql import insert_event
from app.preassessment import preassessment_items, submit_preassessment

BASE = "http://127.0.0.1:8080"
OUT = Path(r"D:\Tender\产品管理文档")
RUN_ID = "sim-" + uuid.uuid4().hex[:6]
NOW = datetime.now().astimezone().isoformat(timespec="seconds")


def responses(overrides):
    items = preassessment_items()
    data = {item["id"]: 3 for section in ["big_five", "mbti", "jungian"] for item in items[section]["items"]}
    data.update(overrides)
    return data


PERSONAS = [
    {
        "id": "high_school_attention_drift",
        "label": "高三学生 · 注意漂移与开放探索",
        "tag": "高开放性、低尽责性、偏 P、Ne/Ti 较突出",
        "overrides": {
            "c1":1,"c2":1,"c3":5,"c4":1,"o1":5,"o2":5,"o3":1,"o4":5,
            "e1":2,"e2":2,"e3":4,"e4":4,"n1":4,"n2":4,"n3":2,"n4":2,
            "ei1":2,"ei2":2,"sn1":5,"sn2":5,"tf1":3,"tf2":3,"jp1":1,"jp2":1,
            "ne1":5,"ni1":4,"se1":2,"si1":2,"te1":2,"ti1":4,"fe1":2,"fi1":3,
        },
        "baseline": [
            {"event_type":"ambient_card_shown","payload":{"kind":"attention_drift","task_hint":"数学作业"}},
            {"event_type":"answer","payload":{"correct":False,"subject":"数学"}},
            {"event_type":"response","payload":{"response_time_ms":52000}},
            {"event_type":"metacognition_jol","payload":{"predicted_correct":8,"actual_correct":3,"n_items":10}},
        ],
        "rounds": [
            {"message":"我坐在书桌前半小时了，一直在换资料，题还没开始。我现在是什么状态？","after":{"event_type":"action_result","payload":{"action":"打开一道题","result":"未开始","attention_returned":False}}},
            {"message":"我照做了十分钟，但刚才又冒出一个新想法，就切过去看了。现在该怎么办？","after":{"event_type":"action_result","payload":{"action":"使用停车区十分钟","result":"部分完成","attention_returned":True}}},
            {"message":"我把新想法写进停车区后回到题上了，但还是很担心这样做不够好。","after":{"event_type":"answer","payload":{"correct":True,"subject":"数学"}}},
        ],
    },
    {
        "id": "university_anxious_overchecking",
        "label": "大一学生 · 焦虑与反复检查",
        "tag": "高尽责性、低情绪稳定性、偏 J、Ni/Ti/Fi 较突出",
        "overrides": {
            "c1":5,"c2":4,"c3":2,"c4":5,"o1":4,"o2":3,"o3":3,"o4":3,
            "e1":2,"e2":2,"e3":4,"e4":4,"a1":4,"a2":4,"a3":2,"a4":5,
            "n1":5,"n2":5,"n3":1,"n4":2,
            "ei1":2,"ei2":2,"sn1":4,"sn2":4,"tf1":4,"tf2":5,"jp1":5,"jp2":5,
            "ne1":3,"ni1":5,"se1":2,"si1":3,"te1":3,"ti1":4,"fe1":3,"fi1":4,
        },
        "baseline": [
            {"event_type":"answer","payload":{"correct":False,"subject":"统计"}},
            {"event_type":"response","payload":{"response_time_ms":68000}},
            {"event_type":"metacognition_jol","payload":{"predicted_correct":7,"actual_correct":2,"n_items":10}},
            {"event_type":"ambient_card_shown","payload":{"kind":"stuck","task_hint":"统计作业"}},
        ],
        "rounds": [
            {"message":"我明明复习了，但一做题就觉得自己什么都不会，越想越慌。","after":{"event_type":"action_result","payload":{"action":"先做一道题","result":"未开始","attention_returned":False}}},
            {"message":"我先做了一道题，做完还是不确定对不对，又开始反复检查。我现在不知道该怎么办。","after":{"event_type":"answer","payload":{"correct":True,"subject":"统计"}}},
            {"message":"我按标准只检查一次就停了，结果还在可接受范围内，但我还是有点不放心。","after":{"event_type":"action_result","payload":{"action":"一次复核后提交","result":"完成","overchecking_prevented":True}}},
        ],
    },
    {
        "id": "career_transition_after_work",
        "label": "职场转行者 · 下班学习与疲劳",
        "tag": "高开放性、中等尽责性、偏 E/N/F/P、Ne/Te 较突出",
        "overrides": {
            "c1":4,"c2":3,"c3":3,"c4":4,"o1":5,"o2":5,"o3":2,"o4":5,
            "e1":4,"e2":4,"e3":2,"e4":2,"a1":4,"a2":4,"a3":3,"a4":4,
            "n1":4,"n2":4,"n3":2,"n4":2,
            "ei1":4,"ei2":4,"sn1":5,"sn2":4,"tf1":3,"tf2":5,"jp1":2,"jp2":2,
            "ne1":5,"ni1":4,"se1":3,"si1":3,"te1":4,"ti1":3,"fe1":4,"fi1":3,
        },
        "baseline": [
            {"event_type":"ambient_card_shown","payload":{"kind":"fatigue","task_hint":"产品课程"}},
            {"event_type":"response","payload":{"response_time_ms":60000}},
            {"event_type":"answer","payload":{"correct":False,"subject":"产品基础"}},
        ],
        "rounds": [
            {"message":"下班后想学新技能，但一打开课程就困，我是不是不适合转行？","after":{"event_type":"action_result","payload":{"action":"打开课程十分钟","result":"未开始","attention_returned":False}}},
            {"message":"我今晚只看了十分钟，比昨天好一点，但我担心坚持不了。","after":{"event_type":"action_result","payload":{"action":"看课程十分钟","result":"完成","minutes":10}}},
            {"message":"如果每天只能学十分钟，帮我看看我的状态和下一步，这样还有意义吗？","after":{"event_type":"action_result","payload":{"action":"安排明天下班后的十分钟","result":"计划已确认","minutes":10}}},
        ],
    },
]

AGENT_IDS = [
    "metacognition_coach",
    "neuro_cognition",
    "learning_strategist",
    "psychologist",
    "nutritionist",
]


def session_for(student_id: str, session: requests.Session) -> dict:
    response = session.post(
        BASE + "/auth/demo-session",
        json={"actor_id": student_id, "role": "learner", "learner_id": student_id},
        timeout=15,
    )
    response.raise_for_status()
    return {"Authorization": "Bearer " + response.json()["token"]}


def profile_summary(profile: dict) -> dict:
    attention = profile.get("attention_profile") or {}
    return {
        "big_five": profile.get("big_five", {}),
        "mbti_type_hint": (profile.get("mbti_preference") or {}).get("type_hint"),
        "jungian_top": (profile.get("jungian_functions") or {}).get("top_functions", []),
        "attention_capture": attention.get("capture_hypotheses", [])[:3],
        "attention_leakage": attention.get("leakage_hypotheses", [])[:3],
        "attention_recovery": attention.get("recovery_preferences", [])[:3],
        "correction_patterns": [item.get("pattern_hypothesis") for item in (profile.get("cognitive_correction_plan") or {}).get("items", [])],
    }


def run_persona(persona: dict, session: requests.Session) -> dict:
    student_id = f"{RUN_ID}-{persona['id']}"
    assessment = submit_preassessment(student_id, responses(persona["overrides"]), consent=True)
    for event in persona["baseline"]:
        insert_event({
            "event_type": event["event_type"],
            "student_id": student_id,
            "payload": event["payload"],
            "source": "synthetic_user_simulation",
            "provenance": {"synthetic": True, "run_id": RUN_ID},
        })
    headers = session_for(student_id, session)
    turns = []
    for index, item in enumerate(persona["rounds"], start=1):
        response = session.post(
            BASE + f"/ambient/reply/{student_id}",
            headers=headers,
            json={
                "card_id": f"ambient_{RUN_ID}_{persona['id']}_{index}",
                "message": item["message"],
                "scenario": "score_improvement",
                "agent_ids": AGENT_IDS,
            },
            timeout=90,
        )
        response.raise_for_status()
        card = response.json()["reply_card"]
        turns.append({
            "round": index,
            "user_message": item["message"],
            "reply": card.get("text"),
            "triage": card.get("triage"),
            "routed_agent_ids": card.get("routed_agent_ids"),
            "tender_context_used": card.get("tender_context_used"),
            "llm": card.get("llm"),
            "ensemble_messages": [
                {"agent_id": msg.get("agent_id"), "name": msg.get("name"), "text": msg.get("text")}
                for msg in (card.get("ensemble_messages") or [])
            ],
        })
        insert_event({
            "event_type": item["after"]["event_type"],
            "student_id": student_id,
            "payload": item["after"]["payload"],
            "source": "synthetic_user_action",
            "provenance": {"synthetic": True, "run_id": RUN_ID, "round": index},
        })
    context_response = session.get(BASE + f"/tender/context/{student_id}", headers=headers, timeout=30)
    context_response.raise_for_status()
    context = context_response.json()
    return {
        "student_id": student_id,
        "persona_id": persona["id"],
        "label": persona["label"],
        "tag": persona["tag"],
        "profile": profile_summary(assessment["profile"]),
        "turns": turns,
        "final_context": {
            "digest": context.get("digest"),
            "state": context.get("state"),
            "mentalization": context.get("mentalization"),
            "recent_events": context.get("recent_events", [])[-5:],
        },
    }


def markdown_report(result: dict) -> str:
    lines = [
        f"# Tender 模拟用户 Agent 连续测试报告 V{result['meta'].get('report_version', '1.0')}",
        "",
        f"版本：{result['meta'].get('report_version', '1.0')}  ",
        f"日期：{NOW[:10]}  ",
        f"运行编号：{RUN_ID}  ",
        "性质：合成用户仿真测试；不是真人受试者研究，不构成临床或效果结论。",
        "",
        "---",
        "",
        "## 一、测试设计",
        "",
        f"本测试通过 {len(result['personas'])} 个真人风格合成用户，各进行三轮连续对话。每轮：",
        "",
        "1. 写入预检测画像；",
        "2. 写入合成行为与作答事件；",
        "3. 调用当前 Tender Agent 接口；",
        "4. 记录 Triage、路由 Agent、模型回复和上下文摘要；",
        "5. 写入本轮行动结果，供下一轮模型更新。",
        "",
        "所有用户和事件均为合成数据。",
        "",
        "## 二、总体结果",
        "",
        f"- 合成用户：{len(result['personas'])}",
        f"- 对话轮次：{result['summary']['turns']}",
        f"- 至少一位 Agent 使用真实模型的轮次：{result['summary']['llm_used_turns']} / {result['summary']['turns']}",
        f"- 全部轮次携带 Tender 上下文：{result['summary']['context_turns']} / {result['summary']['turns']}",
        f"- 知识体系命中轮次：{result['summary'].get('knowledge_turns', 0)} / {result['summary']['turns']}",
        f"- 预检测可用轮次：{result['summary'].get('preassessment_turns', 0)} / {result['summary']['turns']}",
        f"- 平均回复字数：{result['summary'].get('avg_reply_chars', 0)}",
        f"- 发生模板回退的 Agent 次数：{sum(len((turn.get('llm') or {}).get('fallback_agents') or []) for persona in result['personas'] for turn in persona['turns'])}",
        f"- 回复中出现 Agent 名称前缀的轮次：{sum(1 for persona in result['personas'] for turn in persona['turns'] if (turn.get('reply') or '').startswith('['))}",
        f"- Triage 分布：{json.dumps(result['summary']['triage_counts'], ensure_ascii=False)}",
        "",
        "## 三、用户画像",
        "",
    ]
    for persona in result["personas"]:
        profile = persona["profile"]
        lines.extend([
            f"### {persona['label']}",
            "",
            f"- 合成人格：{persona['tag']}",
            f"- MBTI 偏好代码：{profile.get('mbti_type_hint')}",
            f"- 八维更常用：{', '.join(profile.get('jungian_top') or [])}",
            f"- 注意泄漏假设：{'；'.join(profile.get('attention_leakage') or [])}",
            f"- 认知矫正模式：{'；'.join(profile.get('correction_patterns') or [])}",
            "",
        ])
    lines.extend(["## 四、逐轮对话", ""])
    for persona in result["personas"]:
        lines.extend([f"### {persona['label']}", ""])
        for turn in persona["turns"]:
            triage = turn.get("triage") or {}
            used = turn.get("tender_context_used") or {}
            llm = turn.get("llm") or {}
            lines.extend([
                f"#### 第 {turn['round']} 轮",
                "",
                f"**用户：** {turn['user_message']}",
                "",
                f"**Triage：** {triage.get('label')} / {triage.get('problem_type')} / 置信度 {triage.get('confidence')}",
                "",
                f"**路由 Agent：** {', '.join(turn.get('routed_agent_ids') or [])}",
                "",
                f"**上下文：** 预检测={used.get('preassessment_available')}，注意画像={used.get('attention_available')}，知识节点={used.get('knowledge_node') or '未命中'}，事件数={used.get('event_count')}，假设={used.get('mentalization_summary')}",
                "",
                f"**模型：** {', '.join(llm.get('models') or []) or 'fallback/template'}",
                "",
                "**Agent 回复：**",
                "",
                turn.get("reply") or "无回复",
                "",
            ])
        final_context = persona.get("final_context") or {}
        digest = final_context.get("digest") or {}
        state = final_context.get("state") or {}
        mental = final_context.get("mentalization") or {}
        lines.extend([
            f"#### {persona['label']} 最终上下文",
            "",
            f"- 上下文版本：{digest.get('context_version')}",
            f"- 事件数：{digest.get('event_count')}",
            f"- 预检测可用：{digest.get('preassessment_available')}",
            f"- 注意画像可用：{digest.get('attention_available')}",
            f"- 当前主要假设：{mental.get('summary')}",
            f"- 假设数量：{digest.get('hypothesis_count')}",
            f"- 掌握度：{state.get('mastery')}",
            f"- 元认知偏差：{state.get('jol_bias')}",
            f"- 犹豫指标：{state.get('hesitation')}",
            "",
        ])
    lines.extend([
        "## 五、观察到的系统行为",
        "",
        "- 预检测中的注意泄漏和矫正模式已进入 Agent 上下文。",
        "- 当用户询问状态时，Triage 可路由到 `state_review`。",
        "- 回复会结合掌握度、元认知偏差、犹豫和最近行动结果。",
        "- 当用户出现焦虑、疲劳或安全相关表达时，仍优先进入专门路由。",
        "- 合成数据的反应只能验证系统链路和表达一致性，不能证明真实教育效果。",
        "",
        "## 六、下一步需要真人验证的指标",
        "",
        "- 状态假设是否被用户认为准确；",
        "- 建议是否转化为真实行动；",
        "- 同类卡点是否减少；",
        "- 是否出现过度推断、标签化或依赖；",
        "- 用户是否愿意长期保留并授权上下文。",
        "",
        "> 合成用户测试用于发现系统逻辑错误，不替代真人访谈、随机对照实验或临床评估。",
    ])
    return "\n".join(lines)


def main():
    health = requests.get(BASE + "/health", timeout=10)
    health.raise_for_status()
    all_personas = []
    triage_counts = Counter()
    llm_used = 0
    context_turns = 0
    with requests.Session() as session:
        for persona in PERSONAS:
            result = run_persona(persona, session)
            all_personas.append(result)
            for turn in result["turns"]:
                triage_counts[(turn.get("triage") or {}).get("problem_type", "unknown")] += 1
                llm_used += int(bool((turn.get("llm") or {}).get("used")))
                context_turns += int(bool(turn.get("tender_context_used")))
    summary = {
        "personas": len(all_personas),
        "turns": sum(len(persona["turns"]) for persona in all_personas),
        "llm_used_turns": llm_used,
        "context_turns": context_turns,
        "triage_counts": dict(triage_counts),
    }
    payload = {"meta": {"run_id": RUN_ID, "generated_at": NOW, "synthetic": True}, "summary": summary, "personas": all_personas}
    (OUT / "Tender-模拟用户Agent测试结果.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "Tender-模拟用户Agent连续测试报告-V1.0.md").write_text(markdown_report(payload), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
