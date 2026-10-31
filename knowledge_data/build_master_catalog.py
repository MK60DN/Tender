from pathlib import Path
import sqlite3, json, hashlib, datetime
BASE=Path(r'D:\Tender\knowledge_data'); NOW=datetime.datetime.now().isoformat(timespec='seconds')
DB=sqlite3.connect(BASE/'db_catalog.sqlite')
DB.executescript('''
DROP TABLE IF EXISTS databases; DROP TABLE IF EXISTS sources; DROP TABLE IF EXISTS dataset_notes;
CREATE TABLE databases(db_id TEXT PRIMARY KEY,path TEXT UNIQUE,name TEXT,role TEXT,scope TEXT,records_json TEXT,bytes INTEGER,sha256 TEXT,integrity TEXT);
CREATE TABLE sources(source_id TEXT PRIMARY KEY,name TEXT,url TEXT,license TEXT,usage_note TEXT);
CREATE TABLE dataset_notes(topic TEXT,note TEXT);
''')
paths=[]
for p in [BASE/'db_k12.sqlite',BASE/'db_university.sqlite',BASE/'db_university_courses.sqlite',BASE/'db_career.sqlite',BASE/'db_learner_evidence.sqlite',BASE/'db_asset_inventory.sqlite',BASE/'db_catalog.sqlite']:
    if p.exists(): paths.append(p)
paths += sorted((BASE/'subject_databases').glob('db_*.sqlite'))
paths += sorted((BASE/'subject_databases'/'university').glob('*.sqlite'))
seen=set(); rows=[]
for p in paths:
    rp=p.resolve()
    if str(rp) in seen: continue
    seen.add(str(rp))
    con=sqlite3.connect(rp)
    integrity=con.execute('PRAGMA integrity_check').fetchone()[0]
    tables=[r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'search_%'")]
    counts={t:con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    role='unknown'; scope=''
    if 'metadata' in tables:
        md={r[0]:r[1] for r in con.execute('SELECT key,value FROM metadata')}
        role=md.get('role',md.get('database_role',role))
        scope=md.get('category_name') or md.get('subject_id') or md.get('coverage','')
    if p.name=='db_k12.sqlite': role,scope='k12_union','高中多学科合并索引'
    if p.name=='db_university.sqlite': role,scope='university_directory','本科专业目录与专业类'
    if p.name=='db_university_courses.sqlite': role,scope='university_course_union','本科专业—课程种子总表'
    if p.name=='db_career.sqlite': role,scope='career_interest','职业与RIASEC兴趣'
    if p.name=='db_learner_evidence.sqlite': role,scope='learner_evidence','学习者证据库（默认不含真实数据）'
    if p.name=='db_asset_inventory.sqlite': role,scope='asset_inventory','D:\\言文 文件清单'
    if p.name=='db_catalog.sqlite': role,scope='catalog','数据库与来源目录'
    rel=str(rp.relative_to(BASE.parent))
    data={'path':rel,'role':role,'scope':scope,'records':counts,'bytes':rp.stat().st_size,'integrity':integrity}
    rows.append(data)
    con.close()
for r in rows:
    db_id=hashlib.sha1(r['path'].encode()).hexdigest()[:12]
    DB.execute('INSERT INTO databases VALUES(?,?,?,?,?,?,?,?,?)',(db_id,r['path'],Path(r['path']).name,r['role'],r['scope'],json.dumps(r['records'],ensure_ascii=False),r['bytes'],hashlib.sha256((BASE.parent/r['path']).read_bytes()).hexdigest(),r['integrity']))
sources=[
 ('src_ug_2026','普通高等学校本科专业目录（2026年）','https://www.moe.gov.cn/','教育部公开文件','专业代码、专业类、门类、学位备注；再分发前法务复核'),
 ('src_ug_quality_2018','普通高等学校本科专业类教学质量国家标准（2018）','https://www.moe.gov.cn/jyb_xwfb/xw_fbh/moe_2069/xwfbh_2018n/xwfbh_20180130/mtbd/201801/t20180131_326071.html','教育部公开标准','课程种子为结构化摘要，不逐字复制；高校培养方案须复核'),
 ('src_hs_standard','普通高中课程方案和语文等学科课程标准（2017年版2020年修订）','https://www.moe.gov.cn/srcsite/A26/s8001/202006/t20200603_462199.html','教育部公开课程标准','知识点树为课程标准的专家结构化索引，非原文替代'),
 ('src_cs_standard','义务教育课程方案和课程标准（2022年版）','https://www.moe.gov.cn/srcsite/A26/s8001/202204/t20220420_619921.html','教育部公开课程标准','原始PDF已保存；当前产品树主要采用高中课标结构'),
 ('src_onet_301','O*NET 30.1 Database','https://www.onetcenter.org/database.html','CC BY 4.0','职业、RIASEC兴趣与关键词；需保留署名'),
 ('src_gr_2022','研究生教育学科专业目录（2022年）','https://www.moe.gov.cn/','教育部公开文件','一级学科和专业学位类别'),
]
DB.executemany('INSERT INTO sources VALUES(?,?,?,?,?)',sources)
notes=[
 ('boundary','学科库用于兴趣探索、薄弱点发现和促进学习；不用于高利害志愿填报的最终判断。'),
 ('learner_data','db_learner_evidence.sqlite 默认不写真实学生数据；写入前需取得监护人与学生授权。'),
 ('admission_requirements','admission_subject_requirements 仍为空，必须接入各省考试院和高校官方选科要求后才能用于志愿建议。'),
 ('course_seeds','课程层覆盖26个代表专业、319门课程名；其余专业保留官方目录字段，后续按高校培养方案逐步补全。'),
 ('k12_scope','当前知识树1075个节点，覆盖高中13个学科；义务教育阶段与教材版本差异仍需继续补齐。'),
 ('licensing','未明确许可的第三方知识图谱（如K12-KGraph、MOOCubeX）没有并入商业主库。'),
]
DB.executemany('INSERT INTO dataset_notes VALUES(?,?)',notes)
DB.commit(); DB.close()
(BASE/'db_manifest.json').write_text(json.dumps({'created_at':NOW,'catalog':str(BASE/'db_catalog.sqlite'),'databases':rows},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'databases':len(rows),'catalog':str(BASE/'db_catalog.sqlite')},ensure_ascii=False,indent=2))
