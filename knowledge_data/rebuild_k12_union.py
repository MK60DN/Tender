from pathlib import Path
import sqlite3, json, datetime
BASE=Path(r'D:\Tender'); SUB=DATA=BASE/'knowledge_data'/'subject_databases'; DB=BASE/'knowledge_data'/'db_k12.sqlite'
if DB.exists(): DB.unlink()
con=sqlite3.connect(DB)
con.executescript('''
PRAGMA foreign_keys=ON;
CREATE TABLE sources(source_id TEXT PRIMARY KEY,name TEXT NOT NULL,url_or_path TEXT,license TEXT,retrieved_at TEXT,usage_note TEXT);
CREATE TABLE k12_subjects(subject_id TEXT PRIMARY KEY,name TEXT,stage TEXT,source_id TEXT);
CREATE TABLE knowledge_nodes(node_id TEXT PRIMARY KEY,education_level TEXT,subject_id TEXT,parent_id TEXT,code TEXT,name TEXT,node_type TEXT,description TEXT,source_id TEXT,confidence REAL DEFAULT 0.5,domain_id TEXT,module_scope TEXT,official_ref TEXT,evidence_type TEXT,difficulty INTEGER,estimated_minutes INTEGER,sort_order INTEGER);
CREATE TABLE knowledge_edges(source_node TEXT NOT NULL,target_node TEXT NOT NULL,relation TEXT NOT NULL,confidence REAL DEFAULT 0.5,source_id TEXT,note TEXT,PRIMARY KEY(source_node,target_node,relation));
CREATE TABLE question_modes(question_mode_id TEXT PRIMARY KEY,subject_id TEXT,name TEXT,description TEXT);
CREATE TABLE node_competencies(node_id TEXT,competency_id TEXT,weight REAL,PRIMARY KEY(node_id,competency_id));
CREATE TABLE unit_question_modes(node_id TEXT,question_mode_id TEXT,importance REAL,PRIMARY KEY(node_id,question_mode_id));
CREATE TABLE assessment_blueprint(node_id TEXT,assessment_type TEXT,item_format TEXT,evidence_required TEXT,PRIMARY KEY(node_id,assessment_type,item_format));
''')
for path in sorted(SUB.glob('db_*.sqlite')):
    if path.name=='db_subject_index.sqlite': continue
    s=sqlite3.connect(path); s.row_factory=sqlite3.Row
    for r in s.execute('SELECT * FROM sources'):
        con.execute('INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)',tuple(r))
    for r in s.execute('SELECT * FROM subjects'):
        con.execute('INSERT OR REPLACE INTO k12_subjects(subject_id,name,stage,source_id) VALUES(?,?,?,?)',(r['subject_id'],r['name'],r['stage'],r['source_id']))
    for r in s.execute('SELECT * FROM knowledge_nodes'):
        con.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(r['node_id'],'k12',r['subject_id'],r['parent_id'],r['code'],r['name'],r['node_type'],r['description'],r['source_id'],r['confidence'],r['domain_id'],r['module_scope'],r['official_ref'],r['evidence_type'],r['difficulty'],r['estimated_minutes'],r['sort_order']))
    for r in s.execute('SELECT * FROM knowledge_edges'):
        con.execute('INSERT OR REPLACE INTO knowledge_edges VALUES(?,?,?,?,?,?)',(r['source_node'],r['target_node'],r['relation'],r['strength'],r['source_id'],r['note']))
    for r in s.execute('SELECT * FROM question_modes'):
        con.execute('INSERT OR REPLACE INTO question_modes VALUES(?,?,?,?)',tuple(r))
    for r in s.execute('SELECT * FROM node_competencies'):
        con.execute('INSERT OR REPLACE INTO node_competencies VALUES(?,?,?)',tuple(r))
    for r in s.execute('SELECT * FROM unit_question_modes'):
        con.execute('INSERT OR REPLACE INTO unit_question_modes VALUES(?,?,?)',tuple(r))
    for r in s.execute('SELECT * FROM assessment_blueprint'):
        con.execute('INSERT OR REPLACE INTO assessment_blueprint VALUES(?,?,?,?)',tuple(r))
    s.close()
try:
    con.executescript("CREATE VIRTUAL TABLE search_knowledge USING fts5(node_id,name,node_type,subject_id,module_scope); INSERT INTO search_knowledge SELECT node_id,name,node_type,subject_id,module_scope FROM knowledge_nodes;")
except sqlite3.OperationalError as e:
    print('fts warning',e)
con.commit()
counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['k12_subjects','knowledge_nodes','knowledge_edges','question_modes','unit_question_modes','node_competencies']}
con.close()
print(json.dumps(counts,ensure_ascii=False,indent=2))
