# -*- coding: utf-8 -*-
"""Fit O*NET career recommender and public safety signal models."""
from __future__ import annotations
import json, pathlib, zipfile, warnings
warnings.filterwarnings("ignore")
import joblib, numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, log_loss, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, Normalizer
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
ROOT=pathlib.Path(r"D:\Tender"); DATA=ROOT/"external_data"/"open_downloads"; BENCH=ROOT/"experiments"/"advisor_bench"; OUT=BENCH/"outputs"; MODELS=BENCH/"models"
OUT.mkdir(parents=True,exist_ok=True); MODELS.mkdir(parents=True,exist_ok=True)
def save_json(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def fit_career():
    r=DATA/"onet"/"db_30_1"/"db_30_1_text"
    occ=pd.read_csv(r/"Occupation Data.txt",sep="\t",encoding="latin-1")
    domains={"skill":("Skills.txt",["IM"]),"ability":("Abilities.txt",["IM"]),"activity":("Work Activities.txt",["IM"]),"interest":("Interests.txt",["OI"]),"style":("Work Styles.txt",["DR"])}
    matrices=[]
    for prefix,(fn,scales) in domains.items():
        d=pd.read_csv(r/fn,sep="\t",encoding="latin-1"); d=d[d["Scale ID"].isin(scales)].copy(); d["feature"]=prefix+":"+d["Element Name"].astype(str)
        p=d.pivot_table(index="O*NET-SOC Code",columns="feature",values="Data Value",aggfunc="mean"); p.columns=[str(c) for c in p.columns]; matrices.append(p.astype(float))
    X=pd.concat(matrices,axis=1).fillna(0); X=X.loc[:,~X.columns.duplicated()]
    scaler=StandardScaler(with_mean=False); normalizer=Normalizer(norm="l2"); Xs=normalizer.fit_transform(scaler.fit_transform(X.values))
    svd=TruncatedSVD(n_components=30,random_state=42); Z=svd.fit_transform(Xs); kmeans=KMeans(n_clusters=12,random_state=42,n_init=20).fit(Z)
    occ_idx=occ.set_index("O*NET-SOC Code"); titles=[occ_idx.loc[code,"Title"] if code in occ_idx.index else code for code in X.index]
    sil=float(silhouette_score(Z,kmeans.labels_,sample_size=min(500,len(Z)),random_state=42))
    demo={"Investigative":5,"Social":4,"Conventional":3,"Reading Comprehension":5,"Critical Thinking":5,"Active Learning":4,"Writing":4,"Complex Problem Solving":4,"Oral Comprehension":4,"Deductive Reasoning":4}
    vec=np.zeros((1,X.shape[1]))
    for j,col in enumerate(X.columns):
        raw=col.split(":",1)[1]
        if raw in demo: vec[0,j]=demo[raw]
    q=normalizer.transform(scaler.transform(vec)); sims=np.asarray(Xs@q.T).ravel(); order=np.argsort(-sims)[:8]
    recommendations=[{"code":X.index[i],"title":titles[i],"score":round(float(sims[i]),4),"cluster":int(kmeans.labels_[i])} for i in order]
    artifact={"scaler":scaler,"normalizer":normalizer,"matrix":Xs,"occupation_codes":X.index.tolist(),"occupation_titles":titles,"feature_names":X.columns.tolist(),"svd":svd,"kmeans":kmeans,"clusters":kmeans.labels_.tolist(),"intended_use":"content_based_career_exploration_not_job_prediction"}
    joblib.dump(artifact,MODELS/"career_advisor.joblib")
    summary={"occupations":int(X.shape[0]),"features":int(X.shape[1]),"clusters":12,"explained_variance_30":round(float(svd.explained_variance_ratio_.sum()),4),"silhouette":round(sil,4),"example_recommendations":recommendations,"note":"O*NET content-based similarity; no employment outcome labels"}
    save_json("career_profiles.json",summary); return summary

def _binary_metrics(y,p):
    pred=(np.asarray(p)>=.5).astype(int)
    return {"auc":round(float(roc_auc_score(y,p)),4),"ap":round(float(average_precision_score(y,p)),4),"f1":round(float(f1_score(y,pred,zero_division=0)),4),"logloss":round(float(log_loss(y,p)),4),"n":int(len(y)),"positive_rate":round(float(np.mean(y)),4)}

def fit_safety():
    from datasets import load_dataset
    cyber=load_dataset("SSEF-HG-AC/cyberbullying-instagram-tiktok",split="train").to_pandas()
    cyber=cyber.dropna(subset=["text","label"]).copy(); cyber["label"]=cyber["label"].astype(int)
    cyber.to_csv(DATA/"safety"/"cyberbullying_ssef.csv",index=False,encoding="utf-8-sig")
    sms_path=DATA/"safety"/"sms_spam"/"SMSSpamCollection"
    sms=pd.read_csv(sms_path,sep="\t",names=["label","text"],encoding="latin-1")
    sms["target"]=(sms.label=="spam").astype(int)
    # Cyberbullying / abusive-content channel
    Xtr,Xte,ytr,yte=train_test_split(cyber.text,cyber.label,test_size=.25,random_state=42,stratify=cyber.label)
    abuse=Pipeline([("tfidf",TfidfVectorizer(max_features=5000,ngram_range=(1,2),min_df=1,sublinear_tf=True)),("clf",LogisticRegression(max_iter=3000,class_weight="balanced",C=.8))]).fit(Xtr,ytr)
    p_abuse=abuse.predict_proba(Xte)[:,1]; abuse_metrics=_binary_metrics(yte,p_abuse)
    # Scam / phishing channel
    Xtr2,Xte2,ytr2,yte2=train_test_split(sms.text,sms.target,test_size=.25,random_state=42,stratify=sms.target)
    scam=Pipeline([("tfidf",TfidfVectorizer(max_features=5000,ngram_range=(1,2),min_df=2,sublinear_tf=True)),("clf",LogisticRegression(max_iter=3000,class_weight="balanced",C=1.0))]).fit(Xtr2,ytr2)
    p_scam=scam.predict_proba(Xte2)[:,1]; scam_metrics=_binary_metrics(yte2,p_scam)
    artifact={"abuse_model":abuse,"scam_model":scam,"abuse_threshold":.6,"scam_threshold":.65,"intended_use":"safety_signal_only_human_escalation_required","not_trained":["self_harm","real_world_violence","child_abuse_diagnosis"]}
    joblib.dump(artifact,MODELS/"safety_advisor.joblib")
    report={"cyberbullying":abuse_metrics,"scam_spam":scam_metrics,"boundary":"low-level text signals only; self-harm, violence, abuse and emergencies remain rule + human escalation","examples":{"abusive_text":"You are so stupid, nobody wants you here.","scam_text":"Congratulations! You won a prize. Send your bank details now to claim."}}
    save_json("safety_metrics.json",report); return report

def main():
    print("[1/2] career"); career=fit_career()
    print("[2/2] safety"); safety=fit_safety()
    report={"generated_at":pd.Timestamp.now(tz="Asia/Shanghai").isoformat(),"career_advisor":career,"safety_advisor":safety,"boundaries":{"career":"content-based exploration, not job prediction","safety":"text signal + human escalation, not investigation or diagnosis"}}
    save_json("career_safety_metrics.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
