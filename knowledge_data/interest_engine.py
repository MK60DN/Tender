from pathlib import Path
import sqlite3, json, math, datetime, argparse

DATA=Path(r'D:\Tender\knowledge_data')
LEARNER=DATA/'db_learner_evidence.sqlite'
UNI=DATA/'db_university.sqlite'
K12=DATA/'db_k12.sqlite'
CAREER=DATA/'db_career.sqlite'
UNIVERSITY_COURSES=DATA/'db_university_courses.sqlite'
RIASEC=['R','I','A','S','E','C']

def connect():
    con=sqlite3.connect(LEARNER); con.row_factory=sqlite3.Row
    con.execute('ATTACH DATABASE ? AS uni',(str(UNI),))
    con.execute('ATTACH DATABASE ? AS k12',(str(K12),))
    con.execute('ATTACH DATABASE ? AS career',(str(CAREER),))
    con.execute('ATTACH DATABASE ? AS uc',(str(UNIVERSITY_COURSES),))
    con.executescript('''
    CREATE VIEW IF NOT EXISTS v_student_subject_interest AS SELECT student_id,subject_id,SUM(strength*confidence)/NULLIF(SUM(confidence),0) AS interest_score,SUM(confidence) AS evidence_weight,COUNT(*) AS evidence_count FROM student_interest_evidence WHERE subject_id IS NOT NULL GROUP BY student_id,subject_id;
    CREATE VIEW IF NOT EXISTS v_student_riasec AS SELECT student_id,riasec_code,SUM(strength*confidence)/NULLIF(SUM(confidence),0) AS interest_score,SUM(confidence) AS evidence_weight,COUNT(*) AS evidence_count FROM student_interest_evidence WHERE riasec_code IS NOT NULL GROUP BY student_id,riasec_code;
    ''')
    return con

def clip(v): return max(0.0,min(1.0,float(v)))

def add_interest(student_id, subject_id=None, riasec_code=None, strength=.5, confidence=.5, source_type='self_report', evidence_text='', major_code=None, provenance=None):
    con=connect(); con.execute('INSERT INTO student_interest_evidence(student_id,observed_at,source_type,subject_id,major_code,riasec_code,strength,confidence,evidence_text,provenance_json) VALUES(?,?,?,?,?,?,?,?,?,?)',(student_id,datetime.datetime.now().isoformat(timespec='seconds'),source_type,subject_id,major_code,riasec_code,clip(strength),clip(confidence),evidence_text,json.dumps(provenance or {},ensure_ascii=False))); con.commit(); con.close()

def add_score(student_id, subject_id, score, max_score, assessment_type='observation', knowledge_node_id=None, source_ref='', confidence=.7):
    con=connect(); con.execute('INSERT INTO student_score_evidence(student_id,observed_at,subject_id,knowledge_node_id,score,max_score,assessment_type,source_ref,confidence,provenance_json) VALUES(?,?,?,?,?,?,?,?,?,?)',(student_id,datetime.datetime.now().isoformat(timespec='seconds'),subject_id,knowledge_node_id,float(score),float(max_score),assessment_type,source_ref,clip(confidence),'{}')); con.commit(); con.close()

def set_goal(student_id, major_code, target_score=None, target_date=None):
    con=connect(); con.execute('INSERT INTO student_goals(student_id,goal_type,target_major_code,target_score,target_date,status,created_at) VALUES(?,?,?,?,?,?,?)',(student_id,'major',major_code,target_score,target_date,'active',datetime.datetime.now().isoformat(timespec='seconds'))); con.commit(); con.close()

def vectors(con, student_id):
    r={row['riasec_code']:clip(row['interest_score']) for row in con.execute('SELECT riasec_code,interest_score FROM v_student_riasec WHERE student_id=?',(student_id,))}
    s={row['subject_id']:clip(row['interest_score']) for row in con.execute('SELECT subject_id,interest_score FROM v_student_subject_interest WHERE student_id=?',(student_id,))}
    total=con.execute('SELECT COUNT(*) FROM student_interest_evidence WHERE student_id=?',(student_id,)).fetchone()[0]
    return r,s,total

def recommend(student_id, limit=12):
    con=connect(); sr,ss,total=vectors(con,student_id)
    if total==0:
        return {'student_id':student_id,'cold_start':True,'message':'没有兴趣证据，先记录自选行为、持续投入、主动提问或项目产出。','recommendations':[]}
    majors={r['code']:dict(r) for r in con.execute('SELECT m.code,m.name,c.name category,cl.name class_name FROM uni.majors m JOIN uni.discipline_categories c ON c.code=m.category_code JOIN uni.major_classes cl ON cl.code=m.class_code')}
    profiles={}
    for r in con.execute('SELECT major_code,riasec_code,weight FROM career.major_interest_profiles'):
        profiles.setdefault(r['major_code'],{})[r['riasec_code']]=float(r['weight'])
    reqs={}
    for r in con.execute('SELECT major_code,subject_id,weight FROM uc.major_highschool_bridges'):
        reqs.setdefault(r['major_code'],[]).append((r['subject_id'],float(r['weight'])))
    for r in con.execute('SELECT major_code,subject_id,weight FROM uni.major_subject_requirements'):
        reqs.setdefault(r['major_code'],[]).append((r['subject_id'],float(r['weight'])))
    out=[]
    for code,m in majors.items():
        pv=profiles.get(code,{})
        dot=sum(sr.get(k,0)*v for k,v in pv.items())
        norm_s=math.sqrt(sum(v*v for v in sr.values())) or 1
        norm_p=math.sqrt(sum(v*v for v in pv.values())) or 1
        rmatch=dot/(norm_s*norm_p) if sr and pv else 0
        rq=reqs.get(code,[])
        smatch=sum(ss.get(s,0)*w for s,w in rq)/sum(w for _,w in rq) if rq else 0
        conf=min(1,total/10)
        fit=.55*rmatch+.35*smatch+.10*conf
        out.append({**m,'fit':round(fit,4),'riasec_match':round(rmatch,4),'subject_interest_match':round(smatch,4),'evidence_count':total,'cold_start':False})
    out.sort(key=lambda x:x['fit'],reverse=True)
    result={'student_id':student_id,'cold_start':False,'recommendations':out[:limit],'method':'55% RIASEC similarity + 35% subject affinity + 10% evidence confidence','boundary':'heuristic_seed; needs validation with behavior, projects and longitudinal outcomes'}
    con.execute('INSERT INTO recommendation_runs(student_id,created_at,model_version,input_summary_json,output_json) VALUES(?,?,?,?,?)',(student_id,datetime.datetime.now().isoformat(timespec='seconds'),'interest-engine-v0.1',json.dumps({'riasec':sr,'subject_interest':ss,'evidence_count':total},ensure_ascii=False),json.dumps(result,ensure_ascii=False)))
    con.commit(); con.close(); return result

def gap(student_id, major_code):
    con=connect(); major=con.execute('SELECT m.code,m.name,c.name category,cl.name class_name FROM uni.majors m JOIN uni.discipline_categories c ON c.code=m.category_code JOIN uni.major_classes cl ON cl.code=m.class_code WHERE m.code=?',(major_code,)).fetchone()
    if not major: raise ValueError('major_not_found')
    reqs=con.execute('SELECT subject_id,weight,evidence_type,confidence,note FROM uc.major_highschool_bridges WHERE major_code=? ORDER BY weight DESC',(major_code,)).fetchall()
    if not reqs:
        reqs=con.execute('SELECT subject_id,weight,evidence_type,confidence,note FROM uni.major_subject_requirements WHERE major_code=? ORDER BY weight DESC',(major_code,)).fetchall()
    mastery={r['subject_id']:r['avg_mastery'] for r in con.execute('SELECT subject_id,AVG(CASE WHEN max_score>0 THEN score/max_score END) avg_mastery FROM student_score_evidence WHERE student_id=? GROUP BY subject_id',(student_id,))}
    target=con.execute('SELECT target_major_code,target_score FROM student_goals WHERE student_id=? AND status="active" ORDER BY goal_id DESC LIMIT 1',(student_id,)).fetchone()
    items=[]
    for r in reqs:
        sid=r['subject_id']; name=con.execute('SELECT name FROM k12.k12_subjects WHERE subject_id=?',(sid,)).fetchone(); nm=name['name'] if name else sid
        m=mastery.get(sid)
        unknown=m is None
        current=0.5 if unknown else clip(m)
        gap_score=float(r['weight'])*(1-current)
        candidates=[]
        for nr in con.execute('''SELECT n.node_id,n.name,n.parent_id,n.difficulty,n.module_scope,
                  AVG(CASE WHEN e.max_score>0 THEN e.score/e.max_score END) AS node_mastery,
                  COUNT(e.evidence_id) AS evidence_count
                FROM k12.knowledge_nodes n
                LEFT JOIN student_score_evidence e ON e.student_id=? AND e.knowledge_node_id=n.node_id
                WHERE n.subject_id=? AND n.node_type='concept'
                GROUP BY n.node_id
                ORDER BY CASE WHEN COUNT(e.evidence_id)>0 THEN 0 ELSE 1 END,
                         COALESCE(AVG(CASE WHEN e.max_score>0 THEN e.score/e.max_score END),0.5) ASC,
                         n.difficulty ASC,n.sort_order ASC LIMIT 5''',(student_id,sid)):
            modes=[mr['name'] for mr in con.execute('''SELECT q.name FROM k12.unit_question_modes uqm
                    JOIN k12.question_modes q ON q.question_mode_id=uqm.question_mode_id
                    WHERE uqm.node_id=? ORDER BY uqm.importance DESC,q.name LIMIT 3''',(nr['parent_id'],))]
            candidates.append({'node_id':nr['node_id'],'name':nr['name'],'unit_id':nr['parent_id'],
                               'module_scope':nr['module_scope'],'mastery':None if nr['node_mastery'] is None else round(clip(nr['node_mastery']),4),
                               'evidence_count':nr['evidence_count'],'question_modes':modes})
        items.append({'subject_id':sid,'subject_name':nm,'requirement_weight':float(r['weight']),'current_mastery':None if unknown else round(current,4),'estimated_gap':round(gap_score,4),'unknown_mastery':unknown,'evidence_type':r['evidence_type'],'next_topic':candidates[0]['name'] if candidates else '','recommended_knowledge_nodes':candidates})
    items.sort(key=lambda x:x['estimated_gap'],reverse=True)
    course_path=[dict(r) for r in con.execute('SELECT sequence_no,course_name,course_type,knowledge_domain FROM uc.major_courses WHERE major_code=? ORDER BY sequence_no',(major_code,))]
    con.close(); return {'student_id':student_id,'target_major':dict(major),'goal':dict(target) if target else None,'subject_gaps':items,'target_score':target['target_score'] if target else None,'course_path':course_path,'boundary':'subject requirements are heuristic seeds unless marked official; no high-stakes selection decision should rely on them alone'}

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    ai=sub.add_parser('add-interest'); ai.add_argument('--student',required=True); ai.add_argument('--source',default='self_report'); ai.add_argument('--subject'); ai.add_argument('--riasec',choices=RIASEC); ai.add_argument('--strength',type=float,default=.5); ai.add_argument('--confidence',type=float,default=.5); ai.add_argument('--text',default=''); ai.add_argument('--major')
    asc=sub.add_parser('add-score'); asc.add_argument('--student',required=True); asc.add_argument('--subject',required=True); asc.add_argument('--score',type=float,required=True); asc.add_argument('--max-score',type=float,default=100); asc.add_argument('--type',default='observation'); asc.add_argument('--node'); asc.add_argument('--ref',default=''); asc.add_argument('--confidence',type=float,default=.7)
    sg=sub.add_parser('set-goal'); sg.add_argument('--student',required=True); sg.add_argument('--major',required=True); sg.add_argument('--target-score',type=float); sg.add_argument('--target-date')
    r=sub.add_parser('recommend'); r.add_argument('--student',required=True); r.add_argument('--limit',type=int,default=12)
    g=sub.add_parser('gap'); g.add_argument('--student',required=True); g.add_argument('--major',required=True)
    a=ap.parse_args()
    if a.cmd=='add-interest': add_interest(a.student,a.subject,a.riasec,a.strength,a.confidence,a.source,a.text,a.major); print('added')
    elif a.cmd=='add-score': add_score(a.student,a.subject,a.score,a.max_score,a.type,a.node,a.ref,a.confidence); print('added')
    elif a.cmd=='set-goal': set_goal(a.student,a.major,a.target_score,a.target_date); print('added')
    elif a.cmd=='recommend': print(json.dumps(recommend(a.student,a.limit),ensure_ascii=False,indent=2))
    elif a.cmd=='gap': print(json.dumps(gap(a.student,a.major),ensure_ascii=False,indent=2))

if __name__=='__main__': main()
