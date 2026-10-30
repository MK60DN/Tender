# -*- coding: utf-8 -*-
"""Train first-pass RoleMind models from public education datasets."""
from __future__ import annotations
import json, pathlib, warnings
warnings.filterwarnings('ignore')
import joblib
import numpy as np
import pandas as pd
from datasets import load_dataset
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, log_loss, brier_score_loss
from sklearn.cluster import KMeans
from lightgbm import LGBMClassifier

ROOT = pathlib.Path(r'D:\Tender')
OUT = ROOT / 'experiments' / 'role_mind_bench' / 'outputs'
MODELS = ROOT / 'experiments' / 'role_mind_bench' / 'models'
OUT.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)
REPORT = {}

def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def safe_auc(y, p):
    try:
        if len(set(y)) < 2: return None
        return round(float(roc_auc_score(y, p)), 4)
    except Exception: return None

def safe_ap(y, p):
    try:
        if len(set(y)) < 2: return None
        return round(float(average_precision_score(y, p)), 4)
    except Exception: return None

def train_student():
    p = ROOT / 'external_data' / 'open_downloads' / 'assistments2009.csv'
    df = pd.read_csv(p, low_memory=False, encoding="latin-1")
    skill_counts = df.groupby('skill_name').size()
    keep = set(skill_counts[skill_counts >= 200].index)
    df = df[df['skill_name'].isin(keep)].copy()
    df = df.sort_values(['user_id','order_id']).reset_index(drop=True)
    # Sequential features only: no future information.
    df['prior_user_correct'] = df.groupby('user_id')['correct'].transform(lambda s: s.shift().expanding().mean())
    df['prior_skill_correct'] = df.groupby(['user_id','skill_name'])['correct'].transform(lambda s: s.shift().expanding().mean())
    df['prior_user_correct'] = df['prior_user_correct'].fillna(df['correct'].mean())
    df['prior_skill_correct'] = df['prior_skill_correct'].fillna(df['prior_user_correct'])
    feats = ['attempt_count','hint_count','hint_total','ms_first_response','opportunity','prior_user_correct','prior_skill_correct']
    X = df[feats].apply(pd.to_numeric, errors='coerce').fillna(0)
    y = df['correct'].astype(int)
    users = df['user_id'].drop_duplicates().to_numpy()
    tr_users, te_users = train_test_split(users, test_size=0.2, random_state=42)
    tr = df['user_id'].isin(tr_users).to_numpy(); te = ~tr
    model = HistGradientBoostingClassifier(max_iter=120, learning_rate=0.08, max_leaf_nodes=31, random_state=42)
    model.fit(X[tr], y[tr])
    prob = model.predict_proba(X[te])[:,1]
    metrics = {
        'dataset':'ASSISTments 2009', 'rows':int(len(df)), 'users':int(df.user_id.nunique()), 'skills':int(df.skill_name.nunique()),
        'features':feats, 'auc':safe_auc(y[te], prob), 'ap':safe_ap(y[te], prob),
        'logloss':round(float(log_loss(y[te], prob)),4), 'brier':round(float(brier_score_loss(y[te], prob)),4),
        'train_users':int(len(tr_users)), 'test_users':int(len(te_users)),
    }
    joblib.dump({'model':model,'features':feats}, MODELS/'student_mind.joblib')
    sample = df.loc[te, ['user_id','skill_name','correct']].copy(); sample['prediction']=prob
    sample.head(2000).to_csv(OUT/'student_predictions_sample.csv',index=False,encoding='utf-8-sig')
    REPORT['student'] = metrics

def train_teacher():
    p = ROOT / 'external_data' / 'open_downloads' / 'talkmoves_annotated.parquet'
    df = pd.read_parquet(p)
    label_candidates = [
      'has_a_question','has_a_directive_or_instruction','has_explanation_or_reasoning',
      'checks_for_understanding_or_agreement','evaluates_a_student_response',
      'manages_classroom_behavior_or_attention','has_praise_or_encouragement',
      'has_answer_to_a_math_problem','uses_collaborative_or_inclusive_language','shows_uncertainty']
    cols = ['assertion_sentence_'+x for x in label_candidates]
    cols = [c for c in cols if c in df.columns]
    labels = [c.replace('assertion_sentence_','') for c in cols]
    files = df['file_name'].drop_duplicates().tolist()
    tr_files, te_files = train_test_split(files, test_size=0.2, random_state=42)
    tr = df['file_name'].isin(tr_files); te = ~tr
    vec = TfidfVectorizer(max_features=7000, ngram_range=(1,2), min_df=2, sublinear_tf=True)
    Xtr = vec.fit_transform(df.loc[tr,'text'].fillna(''))
    Xte = vec.transform(df.loc[te,'text'].fillna(''))
    Ytr = df.loc[tr,cols].fillna(0).astype(int).to_numpy()
    Yte = df.loc[te,cols].fillna(0).astype(int).to_numpy()
    clf = OneVsRestClassifier(LogisticRegression(C=1.5, max_iter=1000, class_weight='balanced', solver='liblinear'))
    clf.fit(Xtr,Ytr)
    prob = clf.predict_proba(Xte)
    pred = (prob >= 0.5).astype(int)
    per_label = {}
    for i,l in enumerate(labels):
        per_label[l] = {'auc':safe_auc(Yte[:,i],prob[:,i]), 'ap':safe_ap(Yte[:,i],prob[:,i]),
                        'f1':round(float(f1_score(Yte[:,i],pred[:,i],zero_division=0)),4), 'positives':int(Yte[:,i].sum())}
    profiles = {}
    for fn, g in df.loc[te].groupby('file_name'):
        Xg = vec.transform(g['text'].fillna(''))
        pg = clf.predict_proba(Xg)
        profiles[fn] = {labels[i]: round(float(pg[:,i].mean()),4) for i in range(len(labels))}
    metrics = {'dataset':'TalkMoves annotated teacher utterances','rows':int(len(df)),'files':int(df.file_name.nunique()),
               'labels':labels,'micro_f1':round(float(f1_score(Yte,pred,average='micro',zero_division=0)),4),
               'macro_f1':round(float(f1_score(Yte,pred,average='macro',zero_division=0)),4),
               'per_label':per_label}
    joblib.dump({'vectorizer':vec,'classifier':clf,'labels':labels}, MODELS/'teacher_mind.joblib')
    save_json('teacher_profiles.json', profiles)
    REPORT['teacher'] = metrics

def train_sales():
    tr = load_dataset('shawhin/lead-scoring-x', split='train').to_pandas()
    va = load_dataset('shawhin/lead-scoring-x', split='valid').to_pandas()
    te = load_dataset('shawhin/lead-scoring-x', split='test').to_pandas()
    train_df = pd.concat([tr,va],ignore_index=True)
    cats = ['Lead Origin','Lead Source','Last Activity','Tags','What is your current occupation']
    pre = ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),cats)], remainder='drop')
    model = Pipeline([('pre',pre),('clf',LogisticRegression(max_iter=2000,class_weight='balanced',C=1.0))])
    model.fit(train_df[cats], train_df['Converted'].astype(int))
    prob = model.predict_proba(te[cats])[:,1]
    pred = (prob >= 0.5).astype(int)
    order = np.argsort(-prob)
    top10 = order[:max(1,len(order)//10)]
    metrics = {'dataset':'X Education Lead Scoring','train_rows':int(len(train_df)),'test_rows':int(len(te)),
               'auc':safe_auc(te['Converted'],prob),'ap':safe_ap(te['Converted'],prob),
               'f1':round(float(f1_score(te['Converted'],pred,zero_division=0)),4),
               'top10_capture':round(float(te.iloc[top10]['Converted'].sum()/max(1,te['Converted'].sum())),4),
               'base_rate':round(float(te['Converted'].mean()),4)}
    joblib.dump({'pipeline':model,'features':cats}, MODELS/'sales_mind.joblib')
    score = te[['Prospect ID']+cats+['Converted']].copy(); score['conversion_probability']=prob
    score['priority'] = np.where(prob>=0.7,'P0',np.where(prob>=0.4,'P1','P2'))
    score['next_action'] = np.where(prob>=0.7,'24小时内人工跟进',np.where(prob>=0.4,'48小时内补充证据','进入低成本培育'))
    score.sort_values('conversion_probability',ascending=False).head(200).to_csv(OUT/'sales_mind_scores.csv',index=False,encoding='utf-8-sig')
    REPORT['sales'] = metrics

def train_parent():
    base = ROOT/'external_data'/'open_downloads'/'student_performance_uci'
    dfs=[]
    for fn,subject in [('student-mat.csv','math'),('student-por.csv','portuguese')]:
        d=pd.read_csv(base/fn,sep=';'); d['subject']=subject; dfs.append(d)
    df=pd.concat(dfs,ignore_index=True)
    # Parent/family context only; exclude grades and absences from predictors.
    feats=['Medu','Fedu','Pstatus','famsup','paid','schoolsup','studytime','famrel','internet','address','subject']
    X=df[feats].copy(); y=(df['absences']>=10).astype(int)
    cat=['Pstatus','famsup','paid','schoolsup','internet','address','subject']; num=[c for c in feats if c not in cat]
    pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),cat),('num',StandardScaler(),num)])
    model=Pipeline([('pre',pre),('clf',LogisticRegression(max_iter=1000,class_weight='balanced'))])
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.25,random_state=42,stratify=y)
    model.fit(Xtr,ytr); prob=model.predict_proba(Xte)[:,1]
    metrics={'dataset':'UCI Student Performance (family-context proxy)','rows':int(len(df)),'positive_rate':round(float(y.mean()),4),
             'auc':safe_auc(yte,prob),'ap':safe_ap(yte,prob),'note':'代理模型：家庭支持变量预测高缺勤风险，不是家长人格模型'}
    joblib.dump({'pipeline':model,'features':feats}, MODELS/'parent_mind.joblib')
    # Context profiles from the same family features.
    full_pre=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),cat),('num',StandardScaler(),num)])
    Z=full_pre.fit_transform(X)
    km=KMeans(n_clusters=3,random_state=42,n_init=10).fit(Z)
    prof=df[feats].copy(); prof['cluster']=km.labels_
    summaries=[]
    for c,g in prof.groupby('cluster'):
        summaries.append({'cluster':int(c),'n':int(len(g)),'Medu':round(float(g['Medu'].mean()),2),'Fedu':round(float(g['Fedu'].mean()),2),
                          'famsup_rate':round(float((g['famsup']=='yes').mean()),3),'paid_rate':round(float((g['paid']=='yes').mean()),3),
                          'schoolsup_rate':round(float((g['schoolsup']=='yes').mean()),3),'study_time':round(float(g['studytime'].mean()),2)})
    save_json('parent_profiles.json',summaries); REPORT['parent']=metrics

def train_institution():
    p=ROOT/'external_data'/'open_downloads'/'oulad_engineered.parquet'
    df=pd.read_parquet(p).dropna(subset=['target_attrition']).copy()
    ids=df['id_student'].drop_duplicates().to_numpy(); tr_ids,te_ids=train_test_split(ids,test_size=0.2,random_state=42)
    tr=df['id_student'].isin(tr_ids); te=~tr
    feats=['week','weekly_clicks','activity_count','cumulative_clicks','click_diff','code_module','code_presentation']
    X=df[feats].copy()
    for c in ['code_module','code_presentation']: X[c]=X[c].astype('category').cat.codes
    y=df['target_attrition'].astype(int)
    model=LGBMClassifier(n_estimators=300,learning_rate=0.05,num_leaves=31,subsample=0.8,colsample_bytree=0.8,random_state=42,n_jobs=4,verbose=-1)
    model.fit(X[tr],y[tr]); prob=model.predict_proba(X[te])[:,1]
    metrics={'dataset':'OULAD engineered weekly activity','rows':int(len(df)),'students':int(df.id_student.nunique()),'features':feats,
             'auc':safe_auc(y[te],prob),'ap':safe_ap(y[te],prob),'positive_rate':round(float(y.mean()),4),
             'note':'机构侧代理：课程周级参与度预测学生流失风险'}
    joblib.dump({'model':model,'features':feats}, MODELS/'institution_mind.joblib')
    tmp=df.loc[te,['code_module','code_presentation','week']].copy(); tmp['risk']=prob
    agg=tmp.groupby(['code_module','code_presentation','week'],as_index=False)['risk'].mean()
    agg.to_csv(OUT/'institution_weekly_risk.csv',index=False,encoding='utf-8-sig')
    REPORT['institution']=metrics

def main():
    print('[1/5] student'); train_student()
    print('[2/5] teacher'); train_teacher()
    print('[3/5] sales'); train_sales()
    print('[4/5] parent'); train_parent()
    print('[5/5] institution'); train_institution()
    REPORT['dorm_proxy']={'status':'no_direct_dataset','note':'需自建应查/实到/请假/跑校/晚归/异常/交接事件；SSOCS/Campus Safety只能做风险先验。'}
    REPORT['head_teacher_proxy']={'status':'proxy_only','note':'用OULAD课程周风险与clickstream聚合做班级健康代理，不能等同于班主任个人心智。'}
    REPORT['role_mind_schema']={'fields':['role','scope','workload','clarity','uncertainty','boundary_risk','collaboration','evidence','next_action']}
    save_json('role_mind_metrics.json',REPORT)
    print(json.dumps(REPORT,ensure_ascii=False,indent=2))

if __name__=='__main__': main()