# -*- coding: utf-8 -*-
"""Train advisor models from NHANES and UCLA CNP/NKI OpenNeuro data."""
from __future__ import annotations
import json, pathlib, warnings
warnings.filterwarnings("ignore")
import joblib, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.ensemble import HistGradientBoostingClassifier, GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score, log_loss, roc_auc_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(r"D:\Tender")
DATA = ROOT / "external_data" / "open_downloads"
BENCH = ROOT / "experiments" / "advisor_bench"
OUT = BENCH / "outputs"
MODELS = BENCH / "models"
OUT.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)

def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def metric_binary(y, p):
    pred = (np.asarray(p) >= 0.5).astype(int)
    return {"auc": round(float(roc_auc_score(y, p)),4), "ap": round(float(average_precision_score(y,p)),4),
            "brier": round(float(brier_score_loss(y,p)),4), "logloss": round(float(log_loss(y,p)),4),
            "f1": round(float(f1_score(y,pred,zero_division=0)),4), "n": int(len(y)),
            "positive_rate": round(float(np.mean(y)),4)}

def load_nhanes():
    r = DATA / "nhanes_2017_2018"
    names = ["DEMO_J.xpt","BMX_J.xpt","BPX_J.xpt","SLQ_J.xpt","PAQ_J.xpt","DR1TOT_J.xpt","DR2TOT_J.xpt"]
    f = {n: pd.read_sas(r/n, format="xport", encoding="utf-8") for n in names}
    demo=f["DEMO_J.xpt"][["SEQN","RIAGENDR","RIDAGEYR","RIDRETH1","INDFMPIR"]]
    bmx=f["BMX_J.xpt"][["SEQN","BMXBMI","BMXWAIST"]]
    bpx=f["BPX_J.xpt"]
    sleep=f["SLQ_J.xpt"][["SEQN","SLD012"]].rename(columns={"SLD012":"sleep_hours"})
    df=demo.merge(bmx,on="SEQN",how="left").merge(bpx,on="SEQN",how="left").merge(sleep,on="SEQN",how="left").merge(f["PAQ_J.xpt"],on="SEQN",how="left")
    sys=df[[f"BPXSY{i}" for i in range(1,5)]].apply(pd.to_numeric,errors="coerce")
    dia=df[[f"BPXDI{i}" for i in range(1,5)]].apply(pd.to_numeric,errors="coerce").replace(0,np.nan)
    df["systolic_mean"]=sys.where(sys>0).mean(axis=1); df["diastolic_mean"]=dia.where(dia>0).mean(axis=1)
    df["elevated_bp"]=((df.systolic_mean>=130)|(df.diastolic_mean>=80)).astype(float)
    df.loc[df.systolic_mean.isna()|df.diastolic_mean.isna(),"elevated_bp"]=np.nan
    def mins(days,minutes):
        d=pd.to_numeric(df[days],errors="coerce"); m=pd.to_numeric(df[minutes],errors="coerce")
        return d.where((d>=1)&(d<=7),0).fillna(0)*m.where((m>=0)&(m<=300),0).fillna(0)
    df["mvpa_week"]=(mins("PAQ610","PAD615")*2+mins("PAQ625","PAD630")+mins("PAQ640","PAD645")+mins("PAQ655","PAD660")*2+mins("PAQ670","PAD675")).clip(0,3000)
    nut_map={"KCAL":"DR1TKCAL","PROT":"DR1TPROT","CARB":"DR1TCARB","SUGR":"DR1TSUGR","FIBE":"DR1TFIBE","TTFAT":"DR1TTFAT","SFAT":"DR1TSFAT","CHOL":"DR1TCHOL","SODI":"DR1TSODI","POTA":"DR1TPOTA","CALC":"DR1TCALC","IRON":"DR1TIRON","VC":"DR1TVC"}
    d1=f["DR1TOT_J.xpt"][["SEQN"]+list(nut_map.values())].rename(columns={v:k for k,v in nut_map.items()}).set_index("SEQN")
    nut_map2={k:v.replace("DR1","DR2") for k,v in nut_map.items()}
    d2=f["DR2TOT_J.xpt"][["SEQN"]+list(nut_map2.values())].rename(columns={v:k for k,v in nut_map2.items()}).set_index("SEQN")
    diet=pd.concat([d1,d2]).groupby(level=0).mean().reset_index(); diet.columns=["SEQN"]+[f"diet_{c.lower()}" for c in diet.columns[1:]]
    return df.merge(diet,on="SEQN",how="left")

def train_health(df):
    df=df[(df.RIDAGEYR>=20)&(df.RIDAGEYR<=80)].dropna(subset=["elevated_bp"]).copy()
    feats=["RIDAGEYR","RIAGENDR","BMXBMI","BMXWAIST","sleep_hours","mvpa_week","diet_kcal","diet_fibe","diet_sodi","diet_pota","diet_sugr","diet_sfat"]
    X=df[feats].apply(pd.to_numeric,errors="coerce"); y=df.elevated_bp.astype(int)
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    model=HistGradientBoostingClassifier(max_iter=200,learning_rate=.06,max_leaf_nodes=31,random_state=42).fit(Xtr,ytr)
    prob=model.predict_proba(Xte)[:,1]
    joblib.dump({"model":model,"features":feats,"target":"mean systolic >=130 or diastolic >=80","intended_use":"screening_support_only_not_diagnosis"},MODELS/"health_advisor.joblib")
    return metric_binary(yte,prob),{"predicted_elevated_bp_proxy":round(float(prob[0]),4)}

def train_nutrition(df):
    df=df[(df.RIDAGEYR>=12)&(df.diet_kcal>500)].dropna(subset=["diet_kcal","diet_fibe","diet_sodi","diet_pota","diet_sugr"]).copy()
    df["fiber_per_1000kcal"]=df.diet_fibe/(df.diet_kcal/1000); df["sugar_kcal_pct"]=df.diet_sugr*4/df.diet_kcal
    flags=pd.DataFrame({"low_fiber":df.fiber_per_1000kcal<14,"high_sodium":df.diet_sodi>2300,"low_potassium":df.diet_pota<2600,"high_sugar":df.sugar_kcal_pct>.10},index=df.index).astype(int)
    # Transparent 0-100 guideline score. The supervised model approximates this score; it is not a disease predictor.
    df["nutrition_risk_score"]=(flags.low_fiber*30+flags.high_sodium*25+flags.low_potassium*20+flags.high_sugar*25).astype(float)
    feats=["RIDAGEYR","RIAGENDR","BMXBMI","sleep_hours","mvpa_week","diet_kcal","diet_prot","diet_carb","diet_sugr","diet_fibe","diet_ttfat","diet_sfat","diet_sodi","diet_pota","diet_calc","diet_iron","diet_vc"]
    X=df[feats].apply(pd.to_numeric,errors="coerce"); y=df.nutrition_risk_score
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42)
    model=Pipeline([("impute",SimpleImputer(strategy="median")),("reg",GradientBoostingRegressor(n_estimators=220,learning_rate=.04,max_depth=3,random_state=42))]).fit(Xtr,ytr)
    pred=model.predict(Xte)
    metrics={"mae":round(float(mean_absolute_error(yte,pred)),4),"rmse":round(float(np.sqrt(mean_squared_error(yte,pred))),4),"r2":round(float(r2_score(yte,pred)),4),"n":int(len(yte)),"mean_true_score":round(float(yte.mean()),3),"tier_counts":{ "low_0_29":int((y<30).sum()),"medium_30_59":int(((y>=30)&(y<60)).sum()),"high_60_100":int((y>=60).sum()) },"flag_definition":"0-100 score from low fiber, high sodium, low potassium, high sugar"}
    joblib.dump({"pipeline":model,"features":feats,"flags":list(flags.columns),"target":"transparent_nutrition_risk_score_0_100","intended_use":"nutrition_pattern_triage_not_medical_advice"},MODELS/"nutrition_advisor.joblib")
    return metrics,{"predicted_nutrition_risk_score":round(float(pred[0]),3),"true_nutrition_risk_score":round(float(yte.iloc[0]),3)}


def train_neurocognitive():
    r = DATA / "openneuro_ds000030"
    parts = pd.read_csv(r / "participants.tsv", sep="\t")[["participant_id","diagnosis","age","gender"]]
    files = {"wais":"phenotype_wais.tsv","wms":"phenotype_wms.tsv","dkefs":"phenotype_dkefs.tsv",
             "stroop":"phenotype_stroop.tsv","stopsignal":"phenotype_stopsignal.tsv",
             "taskswitch":"phenotype_taskswitch.tsv","cpt":"phenotype_cpt.tsv"}
    merged=parts.copy()
    for prefix,fn in files.items():
        d=pd.read_csv(r/fn,sep="\t")
        d=d.rename(columns={c:f"{prefix}_{c}" for c in d.columns if c!="participant_id"})
        merged=merged.merge(d,on="participant_id",how="left")
    domain_features={
      "memory":{"wais_mr_totalraw":1,"wais_voc_totalraw":1,"wais_lns_totalraw":1,"wms_vr1ir_totalraw":1,"wms_vr2dr_total3":1,"wms_ds_ldsf":1,"wms_ds_totalraw":1,"dkefs_s_total":1},
      "executive":{"dkefs_c":1,"dkefs_a_three":1,"dkefs_f_total":1,"stroop_scwt_accinc":1,"stroop_scwt_ii_std_rt":-1,"stroop_scwt_conflict_rt_effect":-1,"stopsignal_sst_ses_ssd50":1,"stopsignal_sst_ses_stdev_rt":-1,"stopsignal_sst_ses_ssrt":-1,"taskswitch_ts_accuracy":1,"taskswitch_ts_costlong":-1,"taskswitch_ts_costshort":-1},
      "attention":{"cpt_cpt_fa":-1,"cpt_cpt_miss":-1,"cpt_cpt_sd_h":-1}}
    all_features=[(c,d) for fs in domain_features.values() for c,d in fs.items()]
    for c,_ in all_features:
        if c not in merged: raise KeyError(f"missing NKI feature: {c}")
        merged[c]=pd.to_numeric(merged[c],errors="coerce")
    imputer=SimpleImputer(strategy="median"); scaler=StandardScaler()
    Z=scaler.fit_transform(imputer.fit_transform(merged[[c for c,_ in all_features]]))
    domains=pd.DataFrame(index=merged.index); offset=0
    for domain,fs in domain_features.items():
        n=len(fs); chunk=Z[:,offset:offset+n].copy()
        for j,(_,direction) in enumerate(fs.items()):
            if direction<0: chunk[:,j]*=-1
        domains[domain]=chunk.mean(axis=1); offset+=n
    kmeans=KMeans(n_clusters=3,random_state=42,n_init=30); clusters=kmeans.fit_predict(domains)
    domains["cluster"]=clusters; domains["participant_id"]=merged.participant_id.values
    profiles=[]
    for cluster,g in domains.groupby("cluster"):
        profiles.append({"cluster":int(cluster),"n":int(len(g)),**{d:round(float(g[d].mean()),4) for d in domain_features},"overall":round(float(g[list(domain_features)].mean(axis=1).mean()),4)})
    ordered=sorted(profiles,key=lambda x:x["overall"])
    for profile,label in zip(ordered,["higher_support_need","monitor","lower_support_need"]): profile["label"]=label
    joblib.dump({"imputer":imputer,"scaler":scaler,"kmeans":kmeans,"domain_features":domain_features,"profiles":profiles,"intended_use":"cognitive_profile_not_diagnosis"},MODELS/"neurocognitive_advisor.joblib")
    domains.to_csv(OUT/"neurocognitive_domain_scores.csv",index=False,encoding="utf-8-sig"); save_json("neurocognitive_profiles.json",profiles)
    fig,ax=plt.subplots(figsize=(7.5,4.2))
    for p in profiles: ax.plot(list(domain_features),[p[d] for d in domain_features],marker="o",label=f"{p['label']} (n={p['n']})")
    ax.axhline(0,color="#777",linewidth=1); ax.set_ylabel("Standardized domain score"); ax.set_title("Neurocognitive support profiles (NKI/OpenNeuro)"); ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(OUT/"fig_neurocognitive_profiles.png",dpi=180); plt.close(fig)
    return {"rows":int(len(merged)),"diagnosis_counts":merged.diagnosis.value_counts().to_dict(),"domain_features":domain_features,"cluster_profiles":profiles,"note":"Unsupervised research profile; diagnosis labels were not used in clustering."}

def train_psychology():
    r=DATA/"openneuro_ds000030"
    h=pd.read_csv(r/"phenotype_hopkins.tsv",sep="\t"); a=pd.read_csv(r/"phenotype_asrs.tsv",sep="\t")
    df=h.merge(a[["participant_id","asrs_score","asrs_flag"]],on="participant_id",how="left")
    feats=["hopkins_depression","hopkins_anxiety","hopkins_somatization","hopkins_obscomp","hopkins_intsensitivity","hopkins_globalseverity","asrs_score"]
    X=df[feats].apply(pd.to_numeric,errors="coerce"); imputer=SimpleImputer(strategy="median"); scaler=StandardScaler()
    Xs=scaler.fit_transform(imputer.fit_transform(X)); kmeans=KMeans(n_clusters=3,random_state=42,n_init=30); clusters=kmeans.fit_predict(Xs); df["cluster"]=clusters
    profiles=[]
    for cluster,g in df.groupby("cluster"):
        profiles.append({"cluster":int(cluster),"n":int(len(g)),**{f:round(float(g[f].mean()),3) for f in feats},"overall":round(float(Xs[df.index.isin(g.index)].mean()),4)})
    ordered=sorted(profiles,key=lambda x:x["overall"])
    for profile,label in zip(ordered,["low_support_signal","monitor","high_support_signal"]): profile["label"]=label
    joblib.dump({"imputer":imputer,"scaler":scaler,"kmeans":kmeans,"features":feats,"profiles":profiles,"intended_use":"support_triage_only_not_diagnosis"},MODELS/"psychology_advisor.joblib")
    save_json("psychology_profiles.json",profiles)
    fig,ax=plt.subplots(figsize=(8,4.2)); x=np.arange(len(feats)); width=.25
    for i,p in enumerate(profiles): ax.bar(x+(i-1)*width,[p[f]/max(1,df[f].mean()) for f in feats],width,label=f"{p['label']} (n={p['n']})")
    ax.set_xticks(x); ax.set_xticklabels([f.replace("hopkins_","") for f in feats],rotation=30,ha="right"); ax.set_ylabel("Relative score"); ax.set_title("Psychology support profiles"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT/"fig_psychology_profiles.png",dpi=180); plt.close(fig)
    return {"rows":int(len(df)),"features":feats,"cluster_profiles":profiles,"note":"Questionnaire-derived support signal; not a diagnostic classifier."}

def nutrition5k_summary():
    import csv
    r=DATA/"nutrition5k"; rows=[]
    names=["dish_id","total_calories","total_mass","total_fat","total_carb","total_protein"]
    for fn in ["dish_metadata_cafe1.csv","dish_metadata_cafe2.csv"]:
        with open(r/fn,encoding="utf-8-sig",newline="") as f:
            for row in csv.reader(f):
                if len(row)<6: continue
                rows.append({"source_file":fn,**{name:row[i] for i,name in enumerate(names)}})
    df=pd.DataFrame(rows)
    for c in names[1:]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.dropna(subset=["total_calories","total_mass"])
    cols=names[1:]
    summary={"dishes":int(len(df)),"cafeterias":2,"license":"CC BY 4.0","nutrition_distributions":{c:{"mean":round(float(df[c].mean()),3),"median":round(float(df[c].median()),3)} for c in cols}}
    save_json("nutrition5k_summary.json",summary); return summary


def learning_science_config(health,nutrition,neuro,psych):
    config={"model_id":"learning_science_advisor","version":"1.0.0","weights":{"knowledge_gap":.25,"uncertainty":.15,"metacognitive_bias":.10,"hesitation":.15,"neuro_support":.15,"psych_support":.10,"health_risk":.05,"nutrition_risk":.05},"quantum_cognition":{"theta":"fusion/ambiguity state variable","phi":"cognitive phase / cycle variable","trajectory":"Bloch-sphere representation of state evolution","boundary":"modeling language, not evidence of physical quantum effects"},"inputs":{"health":health,"nutrition":nutrition,"neurocognitive":neuro,"psychology":psych},"output":["support_index","recommended_support_mode","uncertainty","referral_suggestion"],"status":"transparent_fusion_no_supervised_quantum_label_dataset"}
    joblib.dump(config,MODELS/"learning_science_advisor.joblib"); save_json("learning_science_advisor_config.json",config); return config

def main():
    print("[1/5] load NHANES")
    df=load_nhanes()
    print("[2/5] health advisor")
    health_metrics,health_example=train_health(df)
    print("[3/5] nutrition advisor")
    nutrition_metrics,nutrition_example=train_nutrition(df)
    print("[4/5] neurocognitive + psychology")
    neuro=train_neurocognitive(); psych=train_psychology()
    print("[5/5] Nutrition5k + learning science fusion")
    n5k=nutrition5k_summary(); fusion=learning_science_config(health_metrics,nutrition_metrics,neuro,psych)
    report={"generated_at":pd.Timestamp.now(tz="Asia/Shanghai").isoformat(),"health_advisor":{"metrics":health_metrics,"example":health_example},"nutrition_advisor":{"metrics":nutrition_metrics,"example":nutrition_example},"neurocognitive_advisor":neuro,"psychology_advisor":psych,"nutrition5k":n5k,"learning_science_advisor":fusion,"boundaries":{"health":"screening proxy, not diagnosis or treatment","nutrition":"nutrition-pattern triage, not medical nutrition therapy","neurocognitive":"unsupervised profile, not neuropsychological diagnosis","psychology":"support triage, not clinical diagnosis","learning_science":"transparent fusion; quantum cognition is a modeling grammar"}}
    save_json("advisor_metrics.json",report)
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
