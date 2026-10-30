# -*- coding: utf-8 -*-
"""Time-gap analysis on EdNet 5000 sequences.

Question: when a learner answers the same question again, does elapsed time
since the previous attempt predict the next correctness after controlling for
prior performance?

This is still observational. It tests association, not a causal spacing effect.
"""
from __future__ import annotations
import csv, json, math, pathlib
from collections import defaultdict
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"
SEQ = pathlib.Path(r"D:\Tender\external_data\open_downloads\ednet5000_extracted\raw_data\ednet_sequence")
QUESTIONS = pathlib.Path(r"D:\Tender\external_data\open_downloads\ednet5000_extracted\raw_data\ednet_content\questions.csv")


def ece(y_true, p, bins=10):
    y_true=np.asarray(y_true); p=np.asarray(p); total=0.0
    for lo, hi in zip(np.linspace(0,1,bins+1)[:-1], np.linspace(0,1,bins+1)[1:]):
        m=(p>=lo)&(p<hi if hi<1 else p<=hi)
        if m.any(): total += m.mean()*abs(y_true[m].mean()-p[m].mean())
    return float(total)


def load_answers():
    ans={}
    with QUESTIONS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ans[row["question_id"]] = str(row["correct_answer"]).strip().lower()
    return ans


def build_rows(limit=0):
    answers=load_answers(); rows=[]; files=sorted(SEQ.glob("u*.csv"))
    if limit: files=files[:limit]
    for idx, path in enumerate(files, 1):
        events_by_item=defaultdict(list)
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                item=row.get("item_id","")
                if row.get("action_type")!="respond" or item not in answers:
                    continue
                try: ts=int(float(row.get("timestamp") or 0))
                except ValueError: continue
                user_answer=str(row.get("user_answer") or "").strip().lower()
                if not user_answer: continue
                events_by_item[item].append((ts, int(user_answer==answers[item]), row.get("source",""), row.get("platform","")))
        for item, events in events_by_item.items():
            events.sort(); success=0
            for n,(ts,correct,source,platform) in enumerate(events):
                if n>0:
                    prev_ts, prev_correct, _, _ = events[n-1]
                    gap_h=max(0.0,(ts-prev_ts)/3600000.0)
                    rows.append({"user_id":path.stem,"item_id":item,"correct":correct,"prior_rate":success/n,"prior_count":n,"prev_correct":prev_correct,"gap_hours":gap_h,"log_gap":math.log1p(min(gap_h,24*365)),"source":source or "unknown","platform":platform or "unknown"})
                success += correct
        if idx % 500 == 0:
            print(f"processed {idx}/{len(files)} files, rows={len(rows)}", flush=True)
    out=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan).dropna().reset_index(drop=True)
    return out


def features(df, source_means, platform_means, global_rate):
    return pd.DataFrame({"prior_rate":df.prior_rate.to_numpy(),"prior_count_log":np.log1p(df.prior_count.to_numpy()),"prev_correct":df.prev_correct.to_numpy(),"source_mean":df.source.map(source_means).fillna(global_rate).to_numpy(),"platform_mean":df.platform.map(platform_means).fillna(global_rate).to_numpy()})


def add_gap(x, df, cuts):
    y=x.copy(); g=df.log_gap.to_numpy(); y["log_gap"]=g
    y["gap_q2"]=((g>cuts[0])&(g<=cuts[1])).astype(float)
    y["gap_q3"]=((g>cuts[1])&(g<=cuts[2])).astype(float)
    y["gap_q4"]=(g>cuts[2]).astype(float)
    return y


def run_cv(rows, seed):
    y=rows.correct.to_numpy(); groups=rows.user_id.to_numpy(); oof=np.full(len(rows),np.nan); metric_rows=[]
    splitter=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=seed)
    for fold,(tr,te) in enumerate(splitter.split(rows,y,groups),1):
        train=rows.iloc[tr]; test=rows.iloc[te]; rate=train.correct.mean(); sm=train.groupby("source").correct.mean().to_dict(); pm=train.groupby("platform").correct.mean().to_dict()
        xb_tr=features(train,sm,pm,rate); xb_te=features(test,sm,pm,rate); cuts=np.quantile(train.log_gap,[.25,.5,.75])
        xs_tr=add_gap(xb_tr,train,cuts); xs_te=add_gap(xb_te,test,cuts)
        for name,a,b in (("base",xb_tr,xb_te),("time_gap",xs_tr,xs_te)):
            scaler=StandardScaler().fit(a); model=LogisticRegression(max_iter=800).fit(scaler.transform(a),train.correct.to_numpy()); p=model.predict_proba(scaler.transform(b))[:,1]
            metric_rows.append({"seed":seed,"fold":fold,"model":name,"auc":roc_auc_score(test.correct,p),"logloss":log_loss(test.correct,p),"brier":brier_score_loss(test.correct,p),"ece":ece(test.correct,p)})
            if name=="time_gap": oof[te]=p
    return pd.DataFrame(metric_rows),oof


def main():
    rows=build_rows(); rows.to_csv(OUT/"ednet_time_gap_rows.csv",index=False,encoding="utf-8-sig")
    metrics=[]; oofs=[]
    for seed in range(5):
        m,o=run_cv(rows,seed); metrics.append(m); oofs.append(o)
    metrics=pd.concat(metrics,ignore_index=True); metrics.to_csv(OUT/"ednet_time_gap_metrics.csv",index=False,encoding="utf-8-sig")
    oof=np.nanmean(np.vstack(oofs),axis=0)
    rows["gap_band"]=pd.qcut(rows.log_gap.rank(method="first"),4,labels=["Q1 shortest","Q2","Q3","Q4 longest"])
    dose=rows.assign(pred=oof).groupby("gap_band",observed=True).agg(n=("correct","size"),observed_correct=("correct","mean"),mean_prediction=("pred","mean")).reset_index(); dose["gap_band"]=dose.gap_band.astype(str)
    summary={"dataset":"EdNet 5000 (respond events with repeated items)","rows_after_first_item_attempt":int(len(rows)),"students":int(rows.user_id.nunique()),"items":int(rows.item_id.nunique()),"metrics":{}}
    for model in ("base","time_gap"):
        g=metrics[metrics.model==model]; summary["metrics"][model]={k:{"mean":float(g[k].mean()),"sd":float(g[k].std(ddof=1))} for k in ("auc","logloss","brier","ece")}
    pairs=metrics.pivot_table(index=["seed","fold"],columns="model",values=["auc","logloss","brier","ece"])
    summary["difference_time_gap_minus_base"]={metric:{"mean":float((pairs[(metric,"time_gap")]-pairs[(metric,"base")]).mean()),"sd":float((pairs[(metric,"time_gap")]-pairs[(metric,"base")]).std(ddof=1))} for metric in ("auc","logloss","brier","ece")}
    summary["gap_dose_response"]=dose.to_dict(orient="records"); summary["interpretation_guardrail"]="Observational association; item repetition, selection and learner strategy are not randomized."
    (OUT/"ednet_time_gap_result.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
