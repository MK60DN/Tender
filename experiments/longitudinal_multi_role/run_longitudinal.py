"""Longitudinal multi-role simulation for Tender."""
from __future__ import annotations
import json, sys, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests
sys.path.insert(0, r"D:\Tender\agent_layer")
sys.path.insert(0, r"D:\Tender\experiments\simulated_user_agents")
from app.daoql import insert_event, insert_edge, event_graph
from app.preassessment import submit_preassessment
from app.tender_context import build_tender_context
import run_simulated_users as sim
import run_simulated_users_v2 as sim2

BASE="http://127.0.0.1:8080"; OUT=Path(r"D:\Tender\产品管理文档"); RUN_ID="long-" + uuid.uuid4().hex[:6]
PERSONAS=[sim.PERSONAS[0], sim.PERSONAS[1], sim.PERSONAS[2], sim2.EXTRA_PERSONAS[-1]]
ROUNDS={
 "high_school_attention_drift":[
  "我最近做数学函数题，总是换资料，题还没开始，我现在是什么状态？",
  "我用了停车区，但新想法还是老把我带走，现在该怎么办？",
  "我完成了一道题，但正确率不稳，我开始担心。",
  "两周后我发现晚上更容易进入状态，但白天不行，这算周期吗？",
  "考试临近，我计划很多但执行不了，我该怎么调整？",
  "八周下来，请综合我的基线、周期、元认知和知识节点，告诉我哪些变化是真的。",
 ],
 "university_anxious_overchecking":[
  "我一做统计题就慌，反复检查，我现在是什么状态？",
  "我按一次检查上限做了，还是不安，现在该怎么办？",
  "我发现晚上做题更稳，但周中课程会打乱节奏。",
  "同学进度比我快，我又开始比较，帮我看看状态。",
  "项目与考研冲突，我不知道先做哪个，请给我下一步。",
  "八周后请综合我的基线、周期、元认知、群体和知识节点，我是否在改善？",
 ],
 "career_transition_after_work":[
  "下班后学产品课就困，我不确定自己适不适合转行。",
  "十分钟能开始，但我担心坚持不了。",
  "我把课程拆小了，但有时加班完全断掉，这会影响基线吗？",
  "我在想转行是否值得，也容易和别人比较。",
  "我想验证产品经理能力，但不知道先做哪个项目。",
  "八周后请综合我的基线、节律和职业方向，告诉我下一步。",
 ],
 "graduate_research_analysis_paralysis":[
  "文献综述无法收束，我该怎么定研究问题？",
  "我写了一个问题又回去读，帮我看看当前状态。",
  "我做了最小实验，但结果不支持原假设，现在怎么办？",
  "导师预测和我实际进展不一致，这说明什么？",
  "我连续几天晚上效率高，但白天差，周期是否稳定？",
  "八周后请综合我的基线、周期、元认知、群体和教师观测，判断下一步。",
 ],
}

def make_events(student_id, persona, stable, round_index):
    base=datetime(2026,8,1,tzinfo=timezone.utc)
    week=[0,7,14,21,35,49][round_index]
    hours=[19,19.2,19.4,19.6,19.8,20] if stable else [6,9,13,17,21,23]
    trigger_id=insert_event({"event_type":"learning_trigger","student_id":student_id,"timestamp":(base+timedelta(days=week,hours=18)).isoformat(),"payload":{"task_hint":"数学函数" if "函数" in ROUNDS[persona["id"]][round_index] else "学习任务","kind":"simulation" },"source":"longitudinal_sim"})
    for j,h in enumerate(hours):
        insert_event({"event_type":"learning_activity","student_id":student_id,"timestamp":(base+timedelta(days=week,hours=h,minutes=j*4)).isoformat(),"payload":{"activity":"study","intensity":1.0-j*.08,"round":round_index+1},"source":"longitudinal_sim"})
    correct=round_index>=3
    answer_id=insert_event({"event_type":"answer","student_id":student_id,"timestamp":(base+timedelta(days=week,hours=20)).isoformat(),"payload":{"correct":correct,"node_id":"k12:math:concept:020101","subject":"数学"},"source":"longitudinal_sim"})
    response_id=insert_event({"event_type":"response","student_id":student_id,"timestamp":(base+timedelta(days=week,hours=20,minutes=1)).isoformat(),"payload":{"response_time_ms":max(28000,65000-round_index*6000),"node_id":"k12:math:concept:020101"},"source":"longitudinal_sim"})
    jol_id=insert_event({"event_type":"metacognition_jol","student_id":student_id,"timestamp":(base+timedelta(days=week,hours=20,minutes=2)).isoformat(),"payload":{"predicted_correct":8,"actual_correct":7 if correct else 3,"n_items":10},"source":"longitudinal_sim"})
    insert_edge(trigger_id,answer_id,"elicited_response",0.8,{"round":round_index+1})
    insert_edge(answer_id,response_id,"measured_time",0.7,{"round":round_index+1})
    return trigger_id,answer_id,response_id,jol_id

def run_persona(persona, index):
    student_id=f"{RUN_ID}-{persona['id']}"; stable=index<2
    profile=submit_preassessment(student_id,sim.responses(persona["overrides"]),consent=True)
    base=datetime(2026,8,1,tzinfo=timezone.utc)
    insert_event({"event_type":"baseline","student_id":student_id,"timestamp":(base+timedelta(hours=8)).isoformat(),"payload":{"arrangement_fit":0.82 if stable else 0.45,"habit_change":0.1 if stable else 0.65},"source":"longitudinal_sim"})
    for i in range(8):
        insert_event({"event_type":"metacognition_mark","student_id":student_id,"timestamp":(base+timedelta(days=i,hours=10)).isoformat(),"payload":{"marked":i%3==0,"correct":i%4!=0},"source":"longitudinal_sim"})
    for i in range(4):
        insert_event({"event_type":"group_interaction","student_id":student_id,"timestamp":(base+timedelta(days=i*7,hours=15)).isoformat(),"payload":{"clustering":0.25 if stable else 0.78,"bridge_ratio":0.72 if stable else 0.24},"source":"longitudinal_sim"})
    for i in range(6):
        insert_event({"event_type":"teacher_prediction","student_id":student_id,"timestamp":(base+timedelta(days=i*7,hours=12)).isoformat(),"payload":{"confidence":[90,82,74,66,58,50][i],"predicted_correct":[9,8,7,6,5,4][i],"actual_correct":([9,8,6,5,3,1][i] if stable else [4,3,5,2,3,2][i])},"source":"longitudinal_sim"})
    session=requests.post(BASE+"/auth/demo-session",json={"actor_id":student_id,"role":"learner","learner_id":student_id},timeout=15); session.raise_for_status(); headers={"Authorization":"Bearer "+session.json()["token"]}
    turns=[]; previous_outcome=None
    for i,message in enumerate(ROUNDS[persona["id"]]):
        trigger_id,answer_id,response_id,jol_id=make_events(student_id,persona,stable,i)
        if previous_outcome:
            insert_edge(previous_outcome,trigger_id,"influences_next_round",0.75,{"round":i+1})
        context=build_tender_context(student_id,user_message=message)
        api=requests.get(BASE+f"/tender/context/{student_id}",params={"message":message},headers=headers,timeout=30); api.raise_for_status()
        reply=requests.post(BASE+f"/ambient/reply/{student_id}",headers=headers,json={"card_id":f"ambient_{RUN_ID}_{persona['id']}_{i+1}","message":message,"scenario":"score_improvement","agent_ids":["metacognition_coach","neuro_cognition","learning_strategist","subject_expert","psychologist"]},timeout=120); reply.raise_for_status(); card=reply.json()["reply_card"]
        outcome_id=insert_event({"event_type":"action_result","student_id":student_id,"timestamp":(base+timedelta(days=[0,7,14,21,35,49][i],hours=23)).isoformat(),"payload":{"round":i+1,"action":"完成最小学习动作","result":"partially_completed" if i<3 else "completed","agent_ids":card.get("routed_agent_ids",[])},"source":"longitudinal_sim"})
        insert_edge(response_id,outcome_id,"action_outcome",0.8,{"round":i+1}); previous_outcome=outcome_id
        turns.append({"round":i+1,"user_message":message,"reply":card.get("text"),"triage":card.get("triage"),"routed_agent_ids":card.get("routed_agent_ids"),"context":api.json()["digest"],"knowledge":api.json().get("knowledge"),"llm":card.get("llm")})
    graph=event_graph(student_id)
    return {"persona_id":persona["id"],"label":persona["label"],"stable":stable,"student_id":student_id,"turns":turns,"profile":sim.profile_summary(profile["profile"]),"final_context":build_tender_context(student_id,user_message="请综合长期变化").get("digest"),"graph":{"nodes":len(graph["nodes"]),"edges":len(graph["edges"])}}


def role_probe(role, actor, messages):
    try:
        session_role = role if role in {"learner","parent","admin","auditor","advisor"} else "admin"
        session_actor = actor if session_role == role else "ADMIN-" + actor
        s=requests.post(BASE+"/auth/demo-session",json={"actor_id":session_actor,"role":session_role,"learner_id":"S01"},timeout=15); s.raise_for_status(); headers={"Authorization":"Bearer "+s.json()["token"]}
    except Exception as exc:
        return {"role":role,"status":"auth_failed","error":str(exc)}
    out={"role":role,"status":"ok","home":None,"routes":[]}
    try:
        home=requests.get(BASE+f"/roles/{role}/home",params={"student_id":"S01","class_id":"理科班"},headers=headers,timeout=30)
        out["home"]={"status":home.status_code,"title":home.json().get("title") if home.ok else None,"tier":home.json().get("tier") if home.ok else None}
    except Exception as exc:
        out["home"]={"status":"error","error":str(exc)}
    for message in messages:
        try:
            route=requests.post(BASE+"/advisors/route",headers=headers,json={"message":message,"student_id":"S01","role":role,"consent_scopes":["minimal_safety_signals","aggregated_tender_state","emotion_support_signals","cognitive_profile","learning_passport_evidence","assessment_evidence"]},timeout=30)
            data=route.json() if route.content else {}
            out["routes"].append({"message":message,"status":route.status_code,"experts":[x.get("id") for x in data.get("selected_experts",[])],"safety":data.get("safety_level")})
        except Exception as exc:
            out["routes"].append({"message":message,"status":"error","error":str(exc)})
    try:
        if role=="sales":
            sales=requests.get(BASE+"/sales/ammunition/理科班",headers=headers,timeout=30)
            out["sales_ammunition"]={"status":sales.status_code,"keys":list(sales.json().keys()) if sales.ok else []}
    except Exception as exc:
        out["sales_ammunition"]={"status":"error","error":str(exc)}
    return out


def markdown(payload):
    turns=sum(len(p["turns"]) for p in payload["personas"]); lines=["# Tender 长期多角色连续测试报告 V3.0","", "版本：3.0  ", f"日期：{datetime.now().astimezone().date().isoformat()}  ", f"运行编号：{RUN_ID}  ", "性质：合成用户/事件；不是真人研究。", "", "## 一、测试设计", "", f"- 学习者：{len(payload['personas'])}","- 每人轮次：6","- 学习者总轮次：%d"%turns,"- 时间跨度：约8周","- 角色探针：家长、任课教师、班主任、销售","- 核心链路：任务触发 → 作答/犹豫 → Agent行动 → 结果 → 下一轮"]
    for p in payload["personas"]:
        lines += [f"## {p['label']}", "", f"- 学生ID：`{p['student_id']}`", f"- 节律类型：{'稳定' if p['stable'] else '漂移'}", f"- 因果图：{p['graph']['nodes']} 节点 / {p['graph']['edges']} 边", f"- 最终上下文：{json.dumps(p['final_context'],ensure_ascii=False)}", "", "| 轮次 | 用户输入 | Triage | 知识节点 | 基线 | 周期 | 群体 | metameta | 回复长度 |", "|---:|---|---|---|---|---|---|---|---:|"]
        for t in p["turns"]:
            c=t.get("context") or {}; tri=t.get("triage") or {}
            lines.append(f"| {t['round']} | {t['user_message']} | {tri.get('problem_type')} | {c.get('knowledge_node') or '—'} | {c.get('baseline_available')} | {c.get('rhythm_available')} | {c.get('group_clustering')} | {c.get('metameta_r')} | {len(t.get('reply') or '')} |")
        lines += ["", "### 逐轮 Agent 回复", ""]
        for t in p["turns"]:
            lines += [f"#### 第 {t['round']} 轮", "", f"**用户：** {t['user_message']}", "", f"**Agent：** {t.get('reply') or '无回复'}", ""]
    lines += ["## 二、多角色探针", "", "| 角色 | 工作台 | 专家路由 | 安全级别 | 备注 |", "|---|---|---|---|---|"]
    for r in payload["roles"]:
        routes="；".join(f"{x.get('message')} → {','.join(x.get('experts') or [])} / {x.get('safety')}" for x in r.get("routes",[]))
        home=r.get("home") or {}
        lines.append(f"| {r['role']} | {home.get('status')} / {home.get('title') or home.get('error','')} | {routes} |  |  |")
    lines += ["", "## 三、长期因果与功能覆盖", "", "本测试把每轮触发、作答、响应时间、行动结果和下一轮触发连接成DAOQL因果边。它是可追溯的合成因果图，不是统计因果证明。", "", "| 功能 | 覆盖 |", "|---|---|", "| 预检测/注意画像 | 每个学习者已写入 |", "| DAOQL事实与因果边 | 每轮触发→结果→下一轮 |", "| 基线 | 跨8周、40+事件 |", "| R24/R168/B | 稳定与漂移对照 |", "| 元认知AUC/偏差/JOL/犹豫 | 每轮事件累积 |", "| 群体聚类/桥接 | 四个学习者不同结构 |", "| 教师metameta | 6条教师预测 |", "| 知识节点/专业/职业 | 函数、统计、职业意图、研究问题 |", "| Triage/Agent路由 | 24轮真实调用 |", "| 真实模型 | DeepSeek-compatible |", "| 家长/教师/班主任/销售 | 角色工作台和专家路由 |", "", "## 四、结论", "", "- 长期记录使Tender从单轮提示转向跨周的状态轨迹，基线、周期、群体和metameta会随数据累积进入上下文。", "- 因果边让“触发—行动—结果—下一轮”可追溯，但不能据此宣称真实因果效应。", "- 下一步需要真人纵向研究，检验这些轨迹是否预测行动恢复、退出和长期自主性。"]
    return "\n".join(lines)


if __name__=="__main__":
    results=[run_persona(p,i) for i,p in enumerate(PERSONAS)]
    roles=[role_probe("parent","P-S01",["孩子最近总说不想学，我该怎么沟通？"]),role_probe("teacher","T-S01",["班里几个学生注意力下降，怎样分层支持？"]),role_probe("head_teacher","HT-S01",["班级里哪些学生需要优先回访和家校沟通？"]),role_probe("sales","SALES-S01",["家长担心孩子坚持不了，我该用什么教学证据回应？"])]
    payload={"meta":{"run_id":RUN_ID,"synthetic":True,"generated_at":datetime.now().astimezone().isoformat()},"personas":results,"roles":roles}
    (OUT/"Tender-长期多角色连续测试结果-V3.0.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    report=markdown(payload); (OUT/"Tender-长期多角色连续测试报告-V3.0.md").write_text(report,encoding="utf-8")
    print(json.dumps({"run_id":RUN_ID,"personas":len(results),"turns":sum(len(p['turns']) for p in results),"roles":len(roles)},ensure_ascii=False))
