# -*- coding: utf-8 -*-
"""Mixture-of-Advisors router with scoped, summary-only cross-end collaboration."""
from __future__ import annotations
import re, uuid
from datetime import datetime, timezone
from .daoql import insert_event, write_audit

EXPERTS = [
 {"id":"safety_advisor","name":"安全与保护","icon":"!","scope":"minimal_safety_signals","roles":["learner","parent","teacher","head_teacher","institution","health_advisor","psychology_advisor","learning_science_advisor"],"keywords":{"霸凌":9,"欺凌":9,"威胁":8,"诈骗":8,"被骗":8,"转账":6,"裸照":12,"不当接触":12,"自伤":14,"自杀":14,"不想活":14,"失联":8,"bully":8,"scam":8,"suicide":14}},
 {"id":"health_advisor","name":"健康","icon":"♡","scope":"sleep_activity_health","roles":["learner","parent","teacher","health_advisor","learning_science_advisor"],"keywords":{"睡":5,"失眠":7,"熬夜":6,"疲劳":5,"头疼":5,"生病":7,"运动":4,"健康":5,"心率":4}},
 {"id":"nutrition_advisor","name":"营养","icon":"◒","scope":"meal_nutrition","roles":["learner","parent","nutrition_advisor","learning_science_advisor"],"keywords":{"吃":4,"饭":5,"早餐":5,"营养":7,"体重":5,"糖":5,"钠":5,"钾":5,"蔬菜":5,"水果":5,"喝水":5}},
 {"id":"neurocognitive_advisor","name":"神经认知","icon":"◉","scope":"cognitive_profile","roles":["learner","parent","teacher","head_teacher","neurocognitive_advisor","psychology_advisor","learning_science_advisor"],"keywords":{"注意":7,"专注":6,"走神":6,"记不住":6,"记忆":6,"执行":5,"多动":5,"认知负荷":7,"overwhelmed":5,"cognitive":5}},
 {"id":"psychology_advisor","name":"心理支持","icon":"◌","scope":"emotion_support_signals","roles":["learner","parent","teacher","head_teacher","psychology_advisor","health_advisor","learning_science_advisor"],"keywords":{"焦虑":7,"压力":6,"难过":5,"情绪":6,"害怕":6,"不想学":6,"没动力":5,"孤独":6,"崩溃":8,"stress":5,"anxiety":6}},
 {"id":"career_advisor","name":"生涯与职业","icon":"↗","scope":"learning_passport_evidence","roles":["learner","parent","teacher","career_advisor","learning_science_advisor"],"keywords":{"职业":7,"工作":6,"就业":7,"专业":6,"转行":8,"实习":6,"面试":5,"简历":6,"考研":4,"留学":4,"career":7,"job":5}},
 {"id":"learning_science_advisor","name":"学习科学","icon":"◇","scope":"aggregated_tender_state","roles":["learner","parent","teacher","head_teacher","learning_science_advisor","career_advisor","health_advisor","nutrition_advisor","neurocognitive_advisor","psychology_advisor"],"keywords":{"学习":5,"复习":5,"计划":4,"考试":4,"掌握":5,"错题":5,"效率":6,"元认知":8,"节律":6,"learn":4,"study":4}},
 {"id":"assessment","name":"评估证据","icon":"▤","scope":"assessment_evidence","roles":["learner","parent","teacher","head_teacher","assessment","learning_science_advisor"],"keywords":{"测试":5,"成绩":6,"正确率":6,"错了":5,"错因":6,"评估":5,"分数":5,"掌握度":5}},
 {"id":"external_communication","name":"对外沟通","icon":"↔","scope":"approved_external_summary","roles":["learner","parent","teacher","head_teacher","external_communication"],"keywords":{"家长":6,"导师":6,"老板":6,"客户":6,"邮件":5,"周报":5,"沟通":5,"汇报":5,"面试官":6}}
]

def _meta(tender: dict | None) -> dict:
    tender=tender or {}; meta=tender.get("metacognition",{}) or {}; knowledge=tender.get("knowledge",{}) or {}
    return {"mastery":float(knowledge.get("mastery",0.5) or 0.5),"jol_bias":float(meta.get("jol_bias",0) or 0),"hesitation":float(meta.get("hesitation",0) or 0),"uncertainty":float(knowledge.get("uncertainty",0) or 0)}

def _consent_set(consent_scopes):
    return set(consent_scopes or [])

def route(message: str, role: str = "learner", tender: dict | None = None, consent_scopes: list[str] | None = None) -> dict:
    text=(message or "").lower(); tm=_meta(tender); consent=_consent_set(consent_scopes); scores={}; reasons={}
    for e in EXPERTS:
        if role not in e["roles"] and role != "coordinator": scores[e["id"]]=0; continue
        score=0.0; hits=[]
        for kw,weight in e["keywords"].items():
            if kw.lower() in text: score+=float(weight); hits.append(kw)
        if hits: reasons[e["id"]]=hits
        scores[e["id"]]=score
    if abs(tm["jol_bias"])>.25:
        scores["learning_science_advisor"]=scores.get("learning_science_advisor",0)+3; reasons.setdefault("learning_science_advisor",[]).append("元认知偏差")
    if tm["hesitation"]>.6:
        scores["neurocognitive_advisor"]=scores.get("neurocognitive_advisor",0)+3; scores["psychology_advisor"]=scores.get("psychology_advisor",0)+2
        reasons.setdefault("neurocognitive_advisor",[]).append("高犹豫"); reasons.setdefault("psychology_advisor",[]).append("高犹豫")
    if tm["mastery"]<.55:
        scores["assessment"]=scores.get("assessment",0)+2; scores["learning_science_advisor"]=scores.get("learning_science_advisor",0)+2
        reasons.setdefault("assessment",[]).append("掌握度偏低")
    if not any(v>0 for v in scores.values()): scores["learning_science_advisor"]=2; reasons["learning_science_advisor"]=["默认学习支持"]
    safety_score=scores.get("safety_advisor",0); visible=[k for k,v in scores.items() if v>0 and k!="safety_advisor"]
    visible=sorted(visible,key=lambda k:scores[k],reverse=True)[:3]
    if safety_score>=8: visible=["safety_advisor"]+visible[:2]
    selected=[]; total=sum(max(scores.get(k,0),.01) for k in visible) or 1
    for k in visible:
        e=next(x for x in EXPERTS if x["id"]==k)
        selected.append({"id":k,"name":e["name"],"icon":e["icon"],"weight":round(max(scores.get(k,0),.01)/total,3),"reason":reasons.get(k,[]),
                         "scope":e["scope"],"scope_status":"available" if e["scope"] in consent or e["scope"] in {"minimal_safety_signals","aggregated_tender_state"} else "needs_consent"})
    return {"route_id":"route_"+uuid.uuid4().hex[:10],"created_at":datetime.now(timezone.utc).astimezone().isoformat(),"role":role,"selected_experts":selected,
            "safety_level":"emergency" if any(x in text for x in ["自杀","不想活","自残","裸照","杀了他"]) else "review" if safety_score>=8 else "normal",
            "monitoring_experts":["safety_advisor"],"policy":"one_unified_reply_not_multiple_agents_talking","raw_data_shared":False}

def share_signal(student_id: str, from_advisor: str, to_advisor: str, purpose: str, summary: str,
                 evidence_refs: list[str], consent_scopes: list[str]) -> dict:
    """Exchange a scoped summary, never raw conversation or raw records."""
    required=f"share:{from_advisor}:{to_advisor}"
    if required not in set(consent_scopes or []):
        raise PermissionError("cross-advisor sharing consent is missing")
    if not summary or len(summary)>2000:
        raise ValueError("summary must be non-empty and <=2000 chars")
    safe={"purpose":purpose,"summary":summary,"evidence_refs":evidence_refs[:20],"raw_data_shared":False}
    eid=insert_event({"event_type":"advisor_collaboration","student_id":student_id,"payload":{"from_advisor":from_advisor,"to_advisor":to_advisor,"scope_request":required,**safe},"source":"advisor_moe_router"})
    write_audit(from_advisor,"advisor.signal.share",eid,{"to":to_advisor,"consent_scope":required})
    return {"collaboration_id":eid,"status":"shared","from_advisor":from_advisor,"to_advisor":to_advisor,"scope":required,"raw_data_shared":False}
