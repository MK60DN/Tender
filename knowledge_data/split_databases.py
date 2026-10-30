from pathlib import Path
import sqlite3, hashlib, json
DATA=Path(r'D:\Tender\knowledge_data'); SRC=DATA/'tender_knowledge.sqlite'
specs={
 'db_university.sqlite':{
   'tables':['sources','discipline_categories','major_classes','majors','graduate_disciplines','admission_subject_requirements','major_subject_requirements'],
   'queries':{
     'knowledge_nodes':"SELECT * FROM knowledge_nodes WHERE education_level IN ('undergraduate','graduate')",
     'knowledge_edges':"SELECT e.* FROM knowledge_edges e JOIN knowledge_nodes s ON s.node_id=e.source_node JOIN knowledge_nodes t ON t.node_id=e.target_node WHERE s.education_level IN ('undergraduate','graduate') AND t.education_level IN ('undergraduate','graduate')"
   }
 },
 'db_k12.sqlite':{
   'tables':['sources','k12_subjects'],
   'queries':{
     'knowledge_nodes':"SELECT * FROM knowledge_nodes WHERE education_level='k12'",
     'knowledge_edges':"SELECT e.* FROM knowledge_edges e JOIN knowledge_nodes s ON s.node_id=e.source_node JOIN knowledge_nodes t ON t.node_id=e.target_node WHERE s.education_level='k12' AND t.education_level='k12'"
   }
 },
 'db_career.sqlite':{'tables':['sources','interest_dimensions','occupations','occupation_interests','riasec_keywords','major_interest_profiles'],'queries':{}},
 'db_learner_evidence.sqlite':{'tables':['sources','interest_dimensions','student_interest_evidence','student_score_evidence','student_goals','recommendation_runs'],'queries':{}},
 'db_asset_inventory.sqlite':{'tables':['sources','asset_inventory'],'queries':{}}
}
src=sqlite3.connect(SRC); src.row_factory=sqlite3.Row
manifest={'source':str(SRC),'databases':{}}
for filename,spec in specs.items():
    dest_path=DATA/filename
    if dest_path.exists(): dest_path.unlink()
    dst=sqlite3.connect(dest_path); dst.execute('PRAGMA journal_mode=OFF')
    for table in spec['tables']:
        schema=src.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
        if schema: dst.execute(schema[0])
        rows=src.execute(f'SELECT * FROM {table}').fetchall()
        if rows:
            cols=[d[0] for d in src.execute(f'SELECT * FROM {table} LIMIT 1').description]
            dst.executemany(f"INSERT INTO {table} VALUES({','.join(['?']*len(cols))})",[tuple(r) for r in rows])
    for name,q in spec.get('queries',{}).items():
        rows=src.execute(q).fetchall()
        if not rows: continue
        cols=[d[0] for d in src.execute(q).description]
        dst.execute(f"CREATE TABLE {name} ({','.join(c+' TEXT' for c in cols)})")
        dst.executemany(f"INSERT INTO {name} VALUES({','.join(['?']*len(cols))})",[tuple(r) for r in rows])
    dst.commit(); dst.execute('VACUUM'); dst.close()
    con=sqlite3.connect(dest_path); tables={r[0]:con.execute(f'SELECT COUNT(*) FROM "{r[0]}"').fetchone()[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}; con.close()
    manifest['databases'][filename]={'bytes':dest_path.stat().st_size,'sha256':hashlib.sha256(dest_path.read_bytes()).hexdigest(),'tables':tables}
(DATA/'db_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
