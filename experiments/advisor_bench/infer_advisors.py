# -*- coding: utf-8 -*-
"""Conservative inference adapter for health, nutrition and cognitive-affective advisors."""
from __future__ import annotations
import argparse, json, pathlib
from functools import lru_cache
from typing import Any
import joblib, numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parent
MODELS = ROOT / "models"
@lru_cache(maxsize=8)
def load_model(name: str) -> dict[str, Any]: return joblib.load(MODELS / name)
def health_advisor(features: dict[str, float]) -> dict:
    a=load_model("health_advisor.joblib"); row=pd.DataFrame([{k:features.get(k,np.nan) for k in a["features"]}]); p=float(a["model"].predict_proba(row)[0,1])
    return {"advisor":"health_advisor","signal":"elevated_bp_screening_proxy","probability":round(p,4),"triage":"high" if p>=.65 else "medium" if p>=.35 else "low","next_action":"建议在授权范围内复测并咨询校医/医生" if p>=.65 else "继续记录睡眠、活动与饮食趋势","boundary":"筛查代理，不是诊断，不替代血压测量或医疗建议"}
def nutrition_advisor(features: dict[str, float]) -> dict:
    a=load_model("nutrition_advisor.joblib"); row=pd.DataFrame([{k:features.get(k,np.nan) for k in a["features"]}]); score=float(a["pipeline"].predict(row)[0]); tier="high" if score>=60 else "medium" if score>=30 else "low"
    return {"advisor":"nutrition_advisor","signal":"nutrition_pattern_risk_score","score_0_100":round(score,2),"tier":tier,"next_action":"检查纤维、钠、钾和添加糖来源，优先做一项可执行替换" if score>=30 else "保持当前饮食结构并继续记录","boundary":"营养模式评分，不是疾病诊断或医学营养治疗"}

def career_advisor(profile: dict[str, float], top_k: int = 5) -> dict:
    a=load_model("career_advisor.joblib")
    vec=np.zeros((1,len(a["feature_names"])))
    for j,name in enumerate(a["feature_names"]):
        raw=name.split(":",1)[1]
        if name in profile: vec[0,j]=float(profile[name])
        elif raw in profile: vec[0,j]=float(profile[raw])
    q=a["normalizer"].transform(a["scaler"].transform(vec))
    sims=np.asarray(a["matrix"]@q.T).ravel(); order=np.argsort(-sims)[:top_k]
    return {"advisor":"career_advisor","matches":[{"code":a["occupation_codes"][i],"title":a["occupation_titles"][i],"similarity":round(float(sims[i]),4),"cluster":int(a["clusters"][i])} for i in order],"boundary":"O*NET content-based exploration, not job prediction or employment promise"}

def safety_advisor(text: str) -> dict:
    a=load_model("safety_advisor.joblib")
    abuse=float(a["abuse_model"].predict_proba([text])[0,1]); scam=float(a["scam_model"].predict_proba([text])[0,1])
    lowered=text.lower()
    emergency_terms=["自杀","不想活","自残","结束生命","kill myself","suicide","self-harm"]
    violence_terms=["杀了他","打死","shoot","kill him","kill her"]
    unsafe_contact=["脱衣服","发裸照","send nudes","不要告诉家长","meet me alone"]
    emergency=[x for x in emergency_terms+violence_terms+unsafe_contact if x in lowered]
    level="emergency" if emergency else "review" if abuse>=a["abuse_threshold"] or scam>=a["scam_threshold"] else "watch" if max(abuse,scam)>=.4 else "low"
    return {"advisor":"safety_advisor","signals":{"abuse_probability":round(abuse,4),"scam_probability":round(scam,4),"rule_hits":emergency},"level":level,"next_action":"立即保护当事人并联系监护人和学校安全负责人；紧急危险联系 110/120" if level=="emergency" else "人工复核上下文，不要仅凭模型结论处理" if level=="review" else "记录并继续观察","boundary":"low-level text signal plus rules; no investigation, diagnosis or autonomous emergency handling"}

def _profile_for_cluster(profiles: list[dict], cluster: int) -> dict: return next(p for p in profiles if int(p["cluster"])==int(cluster))
def neurocognitive_advisor(features: dict[str, float]) -> dict:
    a=load_model("neurocognitive_advisor.joblib"); cols=[]; vals=[]
    for domain,fs in a["domain_features"].items():
        for name,direction in fs.items(): cols.append(name); vals.append(features.get(name,np.nan))
    Z=a["scaler"].transform(a["imputer"].transform(pd.DataFrame([vals],columns=cols))); domain_scores={}; offset=0
    for domain,fs in a["domain_features"].items():
        n=len(fs); chunk=Z[0,offset:offset+n].copy()
        for j,(_,direction) in enumerate(fs.items()):
            if direction<0: chunk[j]*=-1
        domain_scores[domain]=round(float(chunk.mean()),4); offset+=n
    cluster=int(a["kmeans"].predict(pd.DataFrame([[domain_scores[d] for d in a["domain_features"]]],columns=list(a["domain_features"])))[0]); profile=_profile_for_cluster(a["profiles"],cluster)
    return {"advisor":"neurocognitive_advisor","domain_scores":domain_scores,"profile":profile["label"],"cluster":cluster,"next_action":"调整任务负荷和提示层级，必要时转介学校心理/神经心理专业人员" if profile["label"]!="lower_support_need" else "维持当前节奏，观察跨周期稳定性","boundary":"研究型认知画像，不是神经心理诊断，不用于分班或处分"}
def psychology_advisor(features: dict[str, float]) -> dict:
    a=load_model("psychology_advisor.joblib"); vals=[features.get(f,np.nan) for f in a["features"]]; Xs=a["scaler"].transform(a["imputer"].transform(pd.DataFrame([vals],columns=a["features"]))); cluster=int(a["kmeans"].predict(Xs)[0]); profile=_profile_for_cluster(a["profiles"],cluster)
    return {"advisor":"psychology_advisor","profile":profile["label"],"cluster":cluster,"next_action":"安排可信任成人进行支持性访谈；如有自伤、极端绝望或安全问题，立即转介专业人员" if profile["label"]=="high_support_signal" else "保持观察并提供低压力求助入口","boundary":"问卷相关支持信号，不是临床诊断，不输出抑郁/焦虑确诊"}
def _tier_value(label: str) -> float: return {"lower_support_need":.1,"low_support_signal":.1,"monitor":.5,"higher_support_need":.8,"high_support_signal":.9}.get(label,.5)
def learning_science_advisor(tender: dict, advisor_signals: dict) -> dict:
    cfg=load_model("learning_science_advisor.joblib"); w=cfg["weights"]; knowledge=float(tender.get("mastery",.5)); uncertainty=float(tender.get("uncertainty",.5)); jol=abs(float(tender.get("jol_bias",0))); hesitation=float(tender.get("hesitation",0)); neuro=_tier_value(advisor_signals.get("neurocognitive",{}).get("profile","monitor")); psych=_tier_value(advisor_signals.get("psychology",{}).get("profile","monitor")); health=float(advisor_signals.get("health",{}).get("probability",.3)); nutrition=float(advisor_signals.get("nutrition",{}).get("score_0_100",30))/100
    index=(w["knowledge_gap"]*(1-knowledge)+w["uncertainty"]*uncertainty+w["metacognitive_bias"]*min(jol,1)+w["hesitation"]*hesitation+w["neuro_support"]*neuro+w["psych_support"]*psych+w["health_risk"]*health+w["nutrition_risk"]*nutrition); mode="regular" if index<.35 else "scaffold" if index<.6 else "coordinated_support" if index<.8 else "human_referral"
    return {"advisor":"learning_science_advisor","support_index":round(float(index),4),"recommended_support_mode":mode,"quantum_cognition":{"theta":"融合/模糊状态变量","phi":"认知相位与周期","trajectory":"Bloch 球状态演化表示","boundary":"建模语法，不主张真实物理量子效应"},"emotion_interpretation":"情绪必须与情境、行为和时间一起解释，不输出单一情绪人格标签","evidence":{"tender":tender,"advisor_signals":advisor_signals},"boundary":"整合解释，不替代教师、心理老师或医生"}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--advisor",required=True,choices=["health","nutrition","neurocognitive","psychology","career","safety","learning"]); ap.add_argument("--input",required=True); a=ap.parse_args(); p=pathlib.Path(a.input); payload=json.loads(p.read_text(encoding="utf-8")) if p.exists() else json.loads(a.input)
    if a.advisor=="health": out=health_advisor(payload)
    elif a.advisor=="nutrition": out=nutrition_advisor(payload)
    elif a.advisor=="neurocognitive": out=neurocognitive_advisor(payload)
    elif a.advisor=="psychology": out=psychology_advisor(payload)
    elif a.advisor=="career": out=career_advisor(payload)
    elif a.advisor=="safety": out=safety_advisor(payload.get("text",""))
    else: out=learning_science_advisor(payload.get("tender",{}),payload.get("advisors",{}))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
