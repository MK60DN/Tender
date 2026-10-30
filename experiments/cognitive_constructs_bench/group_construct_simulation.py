# -*- coding: utf-8 -*-
"""Monte Carlo sensitivity checks for group-level cognitive construct scoring.

This is a model-behavior simulation, not evidence about real teams. It checks
whether the scoring rules can separate genuine recombination from aggregation
and high-conflict diversity under their stated assumptions.
"""
from __future__ import annotations
import json, pathlib, sys
import numpy as np
from sklearn.metrics import roc_auc_score, confusion_matrix

ROOT=pathlib.Path(__file__).resolve().parent; OUT=ROOT/"outputs"
sys.path.insert(0, r"D:\Tender\agent_layer")
from app.cognitive_constructs import assess_result, assess_forest

rng=np.random.default_rng(20261022)

def result_case(label):
    individual=list(np.clip(rng.beta(2.4,2.2,3),0,1))
    if label==1:
        gain=rng.beta(2.0,3.0)
        group=float(min(1,max(individual)+gain))
        synthesis=float(rng.beta(5.0,2.0)); utility=float(rng.beta(5.0,2.0)); tms=float(rng.beta(5.0,2.0)); conflict=float(rng.beta(1.5,5.0))
    else:
        group=float(min(1,max(individual)+rng.normal(0.01,0.025)))
        synthesis=float(rng.beta(1.6,5.0)); utility=float(rng.beta(4.0,3.0)); tms=float(rng.beta(4.0,3.0)); conflict=float(rng.beta(2.0,4.0))
    return {"individual_novelty":individual,"group_novelty":group,"synthesis":np.clip(synthesis,0,1),"utility":np.clip(utility,0,1),"tms":np.clip(tms,0,1),"relationship_conflict":np.clip(conflict,0,1)}

def forest_case(label):
    if label==1:
        vals=[rng.beta(5,2),rng.beta(5,2),rng.beta(5,2),rng.beta(4,2),rng.beta(1.5,5)]
    else:
        vals=[rng.beta(2,4),rng.beta(2,4),rng.beta(2,4),rng.beta(2,3),rng.beta(4,2)]
    keys=["cognitive_diversity","tms","contribution_entropy","recombination_history","homogenization"]
    return {k:float(np.clip(v,0,1)) for k,v in zip(keys,vals)}

def run(kind, fn, n=10000):
    labels=np.r_[np.ones(n//2,dtype=int),np.zeros(n//2,dtype=int)]; rng.shuffle(labels)
    scores=[]; preds=[]
    for y in labels:
        a=fn(kind,y); scores.append(a["score"]); preds.append(1 if a["status"]=="supported" else 0)
    cm=confusion_matrix(labels,preds,labels=[0,1]); tn,fp,fn_,tp=cm.ravel()
    return {"n":int(n),"auroc":float(roc_auc_score(labels,scores)),"accuracy":float((tp+tn)/n),"sensitivity":float(tp/(tp+fn_) if tp+fn_ else 0),"specificity":float(tn/(tn+fp) if tn+fp else 0),"confusion_matrix":{"tn":int(tn),"fp":int(fp),"fn":int(fn_),"tp":int(tp)},"note":"Synthetic construct-validity check, not human-subject evidence."}

def fixed_examples():
    out=[]
    for name, evidence, assessor in [
        ("genuine_synthesis", result_case(1), assess_result),
        ("best_member_aggregation", result_case(0), assess_result),
        ("healthy_forest", forest_case(1), assess_forest),
        ("homogeneous_forest", forest_case(0), assess_forest),
    ]:
        out.append({"name":name,"evidence":evidence,"assessment":assessor(evidence)})
    return out

def main():
    OUT.mkdir(exist_ok=True)
    checks={
      "result_synergy_vs_aggregation":run("result",lambda kind,y: assess_result(result_case(y)),10000),
      "forest_healthy_vs_homogeneous":run("forest",lambda kind,y: assess_forest(forest_case(y)),10000),
      "fixed_examples": fixed_examples()
    }
    (OUT/"group_construct_simulation.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(checks,ensure_ascii=False,indent=2)[:12000])

if __name__=="__main__": main()
