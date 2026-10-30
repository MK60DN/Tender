from pathlib import Path
import sqlite3, json
base=Path(r'D:\Tender\knowledge_data')
paths=[base/'db_k12.sqlite',base/'db_university.sqlite',base/'db_university_courses.sqlite',base/'db_career.sqlite',base/'db_learner_evidence.sqlite']+sorted((base/'subject_databases').glob('db_*.sqlite'))+sorted((base/'subject_databases'/'university').glob('*.sqlite'))
issues=[]; rows=[]
for p in paths:
    con=sqlite3.connect(p)
    integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
    fk=con.execute('PRAGMA foreign_key_check').fetchall()
    tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    counts={t:con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    if integrity!='ok': issues.append((str(p),'integrity',integrity))
    if fk: issues.append((str(p),'foreign_keys',len(fk)))
    rows.append({'db':str(p),'bytes':p.stat().st_size,'integrity':integrity,'foreign_key_errors':len(fk),'tables':counts})
    con.close()
k=sqlite3.connect(base/'db_k12.sqlite')
dup=k.execute('SELECT node_id,COUNT(*) c FROM knowledge_nodes GROUP BY node_id HAVING c>1').fetchall()
missing_edges=k.execute('SELECT COUNT(*) FROM knowledge_edges e LEFT JOIN knowledge_nodes s ON s.node_id=e.source_node LEFT JOIN knowledge_nodes t ON t.node_id=e.target_node WHERE s.node_id IS NULL OR t.node_id IS NULL').fetchone()[0]
if dup: issues.append(('db_k12','duplicate_nodes',len(dup)))
if missing_edges: issues.append(('db_k12','orphan_edges',missing_edges))
k.close()
u=sqlite3.connect(base/'db_university_courses.sqlite')
course_missing=u.execute('SELECT COUNT(*) FROM major_courses c LEFT JOIN majors m ON m.code=c.major_code WHERE m.code IS NULL').fetchone()[0]
if course_missing: issues.append(('db_university_courses','courses_without_major',course_missing))
u.close()
report={'databases':len(paths),'issues':issues,'items':rows}
(base/'database_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'databases':len(paths),'issues':issues},ensure_ascii=False,indent=2))
