"""Extended real-world-style synthetic user simulation for Tender."""
from __future__ import annotations

import json
import sys
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, r"D:\Tender\experiments\simulated_user_agents")
import run_simulated_users as sim

sim.RUN_ID = "sim2-" + uuid.uuid4().hex[:6]
sim.NOW = datetime.now().astimezone().isoformat(timespec="seconds")

EXTRA_PERSONAS = [
    {
        "id": "primary_writing_frustration",
        "label": "小学五年级 · 作文启动与成人催促",
        "tag": "中等开放性、偏 P、情绪较敏感，需要成人共同调节",
        "overrides": {
            "c1":2,"c2":2,"c3":4,"c4":2,"o1":4,"o2":4,"o3":2,"o4":4,
            "e1":3,"e2":3,"e3":3,"e4":3,"a1":4,"a2":4,"a3":3,"a4":4,
            "n1":4,"n2":4,"n3":2,"n4":2,
            "ei1":3,"ei2":2,"sn1":4,"sn2":3,"tf1":3,"tf2":5,"jp1":2,"jp2":2,
            "ne1":4,"ni1":3,"se1":3,"si1":3,"te1":2,"ti1":3,"fe1":4,"fi1":4,
        },
        "baseline": [
            {"event_type":"ambient_card_shown","payload":{"kind":"stuck","task_hint":"语文作文"}},
            {"event_type":"response","payload":{"response_time_ms":50000}},
            {"event_type":"answer","payload":{"correct":False,"subject":"语文"}},
        ],
        "rounds": [
            {"message":"我一看到作文题就发呆，妈妈一催我更不想写，我现在该怎么办？","after":{"event_type":"action_result","payload":{"action":"只写一个开头句","result":"未开始"}}},
            {"message":"我先写了三句话，但不知道怎么接着写。","after":{"event_type":"action_result","payload":{"action":"写三句话","result":"完成","sentences":3}}},
            {"message":"我写完一段了，可还是很担心会被说不好。","after":{"event_type":"action_result","payload":{"action":"完成一段并读一遍","result":"完成","paragraphs":1}}},
        ],
    },
    {
        "id": "middle_geometry_avoidance",
        "label": "初二学生 · 几何卡点与同伴比较",
        "tag": "外向性偏低、情绪敏感、偏 P、Ti/Se/Si 较突出",
        "overrides": {
            "c1":3,"c2":3,"c3":3,"c4":3,"o1":3,"o2":3,"o3":3,"o4":4,
            "e1":2,"e2":2,"e3":4,"e4":4,"a1":4,"a2":4,"a3":3,"a4":4,
            "n1":4,"n2":4,"n3":2,"n4":2,
            "ei1":2,"ei2":2,"sn1":4,"sn2":4,"tf1":4,"tf2":3,"jp1":2,"jp2":2,
            "ne1":3,"ni1":3,"se1":4,"si1":4,"te1":3,"ti1":5,"fe1":3,"fi1":3,
        },
        "baseline": [
            {"event_type":"ambient_card_shown","payload":{"kind":"stuck","task_hint":"数学几何"}},
            {"event_type":"answer","payload":{"correct":False,"subject":"数学","node_id":"k12:math:unit:0201"}},
            {"event_type":"response","payload":{"response_time_ms":55000}},
        ],
        "rounds": [
            {"message":"同学都会做这道几何题，我一不会就不想上课，我现在是什么状态？","after":{"event_type":"action_result","payload":{"action":"画图并标已知","result":"未开始"}}},
            {"message":"我先画了图，但还是看不出辅助线，能给我一个最小提示吗？","after":{"event_type":"action_result","payload":{"action":"画图并标已知","result":"完成"}}},
            {"message":"我做出一小步了，但还是担心考试时想不起来。","after":{"event_type":"answer","payload":{"correct":True,"subject":"数学"}}},
        ],
    },
    {
        "id": "university_exam_project_conflict",
        "label": "大三学生 · 课程项目与考研冲突",
        "tag": "高尽责、情绪敏感、偏 J、Ni/Te/Ti 较突出",
        "overrides": {
            "c1":5,"c2":4,"c3":2,"c4":5,"o1":4,"o2":4,"o3":3,"o4":4,
            "e1":2,"e2":2,"e3":4,"e4":4,"a1":4,"a2":4,"a3":2,"a4":4,
            "n1":5,"n2":5,"n3":1,"n4":2,
            "ei1":2,"ei2":2,"sn1":5,"sn2":5,"tf1":4,"tf2":3,"jp1":5,"jp2":5,
            "ne1":3,"ni1":5,"se1":2,"si1":3,"te1":5,"ti1":4,"fe1":3,"fi1":3,
        },
        "baseline": [
            {"event_type":"ambient_card_shown","payload":{"kind":"stuck","task_hint":"考研数学复习"}},
            {"event_type":"answer","payload":{"correct":False,"subject":"数学"}},
            {"event_type":"metacognition_jol","payload":{"predicted_correct":8,"actual_correct":4,"n_items":10}},
            {"event_type":"response","payload":{"response_time_ms":65000}},
        ],
        "rounds": [
            {"message":"我每天都列计划但完不成，看到别人进度就慌，我现在该怎么办？","after":{"event_type":"action_result","payload":{"action":"完成一个最小复习块","result":"未开始"}}},
            {"message":"我今天只复习了两小时，觉得远远不够，现在不知道该怎么办。","after":{"event_type":"action_result","payload":{"action":"复习一个知识块","result":"完成","minutes":25}}},
            {"message":"课程项目和考研冲突时，帮我判断状态和优先级，我应该先做哪一个？","after":{"event_type":"action_result","payload":{"action":"明确今晚优先事项","result":"完成"}}},
        ],
    },
    {
        "id": "graduate_research_analysis_paralysis",
        "label": "研二学生 · 文献综述与分析瘫痪",
        "tag": "高开放性、高尽责、情绪敏感、偏 Ni/Ti/Fi",
        "overrides": {
            "c1":4,"c2":4,"c3":2,"c4":4,"o1":5,"o2":5,"o3":2,"o4":5,
            "e1":2,"e2":2,"e3":4,"e4":4,"a1":3,"a2":3,"a3":3,"a4":3,
            "n1":4,"n2":4,"n3":2,"n4":2,
            "ei1":2,"ei2":2,"sn1":5,"sn2":5,"tf1":4,"tf2":4,"jp1":4,"jp2":3,
            "ne1":4,"ni1":5,"se1":2,"si1":3,"te1":3,"ti1":5,"fe1":3,"fi1":4,
        },
        "baseline": [
            {"event_type":"ambient_card_shown","payload":{"kind":"stuck","task_hint":"文献综述"}},
            {"event_type":"response","payload":{"response_time_ms":72000}},
            {"event_type":"answer","payload":{"correct":False,"subject":"研究方法"}},
        ],
        "rounds": [
            {"message":"我卡在文献综述，不知道该收束到什么问题，现在该怎么办？","after":{"event_type":"action_result","payload":{"action":"写出一个候选研究问题","result":"未开始"}}},
            {"message":"我写了一个研究问题，但总觉得不够新，又回去继续读，帮我看看当前状态。","after":{"event_type":"action_result","payload":{"action":"保留候选问题并停止扩读","result":"部分完成"}}},
            {"message":"我想先做一个小实验验证方向，这样是不是更有效？","after":{"event_type":"action_result","payload":{"action":"设计最小验证实验","result":"完成"}}},
        ],
    },
]


def main_v2():
    sim.PERSONAS = list(sim.PERSONAS) + EXTRA_PERSONAS
    sim.OUT = Path(r"D:\Tender\产品管理文档")
    health = requests.get(sim.BASE + "/health", timeout=10)
    health.raise_for_status()
    all_personas = []
    triage_counts = Counter()
    llm_used = 0
    context_turns = 0
    knowledge_turns = 0
    preassessment_turns = 0
    reply_chars = 0
    with requests.Session() as session:
        for persona in sim.PERSONAS:
            result = sim.run_persona(persona, session)
            all_personas.append(result)
            for turn in result["turns"]:
                triage_counts[(turn.get("triage") or {}).get("problem_type", "unknown")] += 1
                llm_used += int(bool((turn.get("llm") or {}).get("used")))
                used = turn.get("tender_context_used") or {}
                context_turns += int(bool(used))
                knowledge_turns += int(bool(used.get("knowledge_available")))
                preassessment_turns += int(bool(used.get("preassessment_available")))
                reply_chars += len(turn.get("reply") or "")
    turns = sum(len(persona["turns"]) for persona in all_personas)
    fallback_count = sum(len((turn.get("llm") or {}).get("fallback_agents") or []) for persona in all_personas for turn in persona["turns"])
    prefix_count = sum(1 for persona in all_personas for turn in persona["turns"] if (turn.get("reply") or "").startswith("["))
    summary = {
        "personas": len(all_personas),
        "turns": turns,
        "llm_used_turns": llm_used,
        "context_turns": context_turns,
        "knowledge_turns": knowledge_turns,
        "preassessment_turns": preassessment_turns,
        "avg_reply_chars": round(reply_chars / turns, 1) if turns else 0,
        "fallback_agent_count": fallback_count,
        "agent_prefix_turns": prefix_count,
        "triage_counts": dict(triage_counts),
    }
    payload = {
        "meta": {"run_id": sim.RUN_ID, "generated_at": sim.NOW, "synthetic": True, "report_version": "2.0"},
        "summary": summary,
        "personas": all_personas,
    }
    (sim.OUT / "Tender-模拟用户Agent测试结果-V2.0.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (sim.OUT / "Tender-模拟用户Agent连续测试报告-V2.0.md").write_text(sim.markdown_report(payload), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main_v2()
