from pathlib import Path
import sqlite3, csv, json, datetime, hashlib
import pandas as pd

BASE=Path(r'D:\Tender')
DATA=BASE/'knowledge_data'; DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'tender_knowledge.sqlite'
EXT=BASE/'external_data'/'open_downloads'
UG_CSV=EXT/'本科专业目录2026.csv'
GR_CSV=EXT/'研究生学科专业目录2022.csv'
ONET=EXT/'onet'/'db_30_1'/'db_30_1_text'

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources(source_id TEXT PRIMARY KEY,name TEXT NOT NULL,url_or_path TEXT,license TEXT,retrieved_at TEXT,usage_note TEXT);
CREATE TABLE IF NOT EXISTS asset_inventory(asset_id INTEGER PRIMARY KEY, path TEXT UNIQUE, scope TEXT, extension TEXT, bytes INTEGER, modified_at TEXT);
CREATE TABLE IF NOT EXISTS discipline_categories(code TEXT PRIMARY KEY,name TEXT NOT NULL,level TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS major_classes(code TEXT PRIMARY KEY,name TEXT NOT NULL,category_code TEXT NOT NULL REFERENCES discipline_categories(code));
CREATE TABLE IF NOT EXISTS majors(code TEXT PRIMARY KEY,name TEXT NOT NULL,category_code TEXT NOT NULL REFERENCES discipline_categories(code),class_code TEXT NOT NULL REFERENCES major_classes(code),degree_note TEXT,is_special INTEGER,is_state_controlled INTEGER,source_id TEXT,source_page INTEGER);
CREATE TABLE IF NOT EXISTS graduate_disciplines(code TEXT PRIMARY KEY,name TEXT NOT NULL,category_name TEXT,is_professional_degree INTEGER,source_id TEXT);
CREATE TABLE IF NOT EXISTS k12_subjects(subject_id TEXT PRIMARY KEY,name TEXT,stage TEXT,source_id TEXT);
CREATE TABLE IF NOT EXISTS knowledge_nodes(node_id TEXT PRIMARY KEY,education_level TEXT,subject_id TEXT,parent_id TEXT,code TEXT,name TEXT,node_type TEXT,description TEXT,source_id TEXT,confidence REAL DEFAULT 0.5);
CREATE TABLE IF NOT EXISTS knowledge_edges(source_node TEXT NOT NULL,target_node TEXT NOT NULL,relation TEXT NOT NULL,confidence REAL DEFAULT 0.5,source_id TEXT,PRIMARY KEY(source_node,target_node,relation));
CREATE TABLE IF NOT EXISTS interest_dimensions(code TEXT PRIMARY KEY,name_zh TEXT,name_en TEXT,description TEXT);
CREATE TABLE IF NOT EXISTS occupations(code TEXT PRIMARY KEY,title TEXT,description TEXT,source_id TEXT);
CREATE TABLE IF NOT EXISTS occupation_interests(occupation_code TEXT,riasec_code TEXT,score REAL,PRIMARY KEY(occupation_code,riasec_code));
CREATE TABLE IF NOT EXISTS riasec_keywords(riasec_code TEXT,keyword TEXT,keyword_type TEXT,PRIMARY KEY(riasec_code,keyword,keyword_type));
CREATE TABLE IF NOT EXISTS major_subject_requirements(major_code TEXT,subject_id TEXT,weight REAL,evidence_type TEXT,confidence REAL,note TEXT,PRIMARY KEY(major_code,subject_id));
CREATE TABLE IF NOT EXISTS major_interest_profiles(major_code TEXT,riasec_code TEXT,weight REAL,evidence_type TEXT,confidence REAL,note TEXT,PRIMARY KEY(major_code,riasec_code));
CREATE TABLE IF NOT EXISTS admission_subject_requirements(id INTEGER PRIMARY KEY,university TEXT,province TEXT,year INTEGER,major_code TEXT,subject_requirement TEXT,source_url TEXT,verified INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS student_interest_evidence(evidence_id INTEGER PRIMARY KEY,student_id TEXT,observed_at TEXT,source_type TEXT,subject_id TEXT,major_code TEXT,riasec_code TEXT,strength REAL,confidence REAL,evidence_text TEXT,provenance_json TEXT);
CREATE TABLE IF NOT EXISTS student_score_evidence(evidence_id INTEGER PRIMARY KEY,student_id TEXT,observed_at TEXT,subject_id TEXT,knowledge_node_id TEXT,score REAL,max_score REAL,assessment_type TEXT,source_ref TEXT,confidence REAL DEFAULT 0.7,provenance_json TEXT);
CREATE TABLE IF NOT EXISTS student_goals(goal_id INTEGER PRIMARY KEY,student_id TEXT,goal_type TEXT,target_major_code TEXT,target_score REAL,target_date TEXT,status TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS recommendation_runs(run_id INTEGER PRIMARY KEY,student_id TEXT,created_at TEXT,model_version TEXT,input_summary_json TEXT,output_json TEXT);
DROP VIEW IF EXISTS v_student_subject_interest;
CREATE VIEW v_student_subject_interest AS SELECT student_id,subject_id,SUM(strength*confidence)/NULLIF(SUM(confidence),0) AS interest_score,SUM(confidence) AS evidence_weight,COUNT(*) AS evidence_count FROM student_interest_evidence WHERE subject_id IS NOT NULL GROUP BY student_id,subject_id;
DROP VIEW IF EXISTS v_student_riasec;
CREATE VIEW v_student_riasec AS SELECT student_id,riasec_code,SUM(strength*confidence)/NULLIF(SUM(confidence),0) AS interest_score,SUM(confidence) AS evidence_weight,COUNT(*) AS evidence_count FROM student_interest_evidence WHERE riasec_code IS NOT NULL GROUP BY student_id,riasec_code;
DROP VIEW IF EXISTS v_major_subject_map;
CREATE VIEW v_major_subject_map AS SELECT m.code,m.name,m.category_code,m.class_code,r.subject_id,r.weight,r.evidence_type,r.confidence FROM majors m LEFT JOIN major_subject_requirements r ON m.code=r.major_code;
'''

def insert(cur,sql,rows):
    if rows: cur.executemany(sql,rows)

now=datetime.datetime.now().isoformat(timespec='seconds')
if DB.exists(): DB.unlink()
con=sqlite3.connect(DB); cur=con.cursor(); cur.executescript(SCHEMA)
sources=[
 ('src_ug_2026','普通高等学校本科专业目录（2026年）','https://www.moe.gov.cn/srcsite/A08/moe_1034/s3882/202604/W020260427440749576927.pdf','教育部公开文件','2026-10-25','官方专业代码与门类事实；产品再分发前需法务确认'),
 ('src_gr_2022','研究生教育学科专业目录（2022年）','https://www.moe.gov.cn/srcsite/A22/moe_833/202209/W020220914572994461110.pdf','教育部公开文件','2026-10-25','官方研究生学科目录事实'),
 ('src_onet_301','O*NET 30.1 Database',str(ONET),'CC BY 4.0','2026-10-25','职业、RIASEC兴趣与关键词；需保留署名'),
 ('src_local_k12','D:\\言文\\初中知识点汇总','D:\\言文\\初中知识点汇总','用户提供资料','2026-10-25','仅提取知识点标题用于内部图谱；商业化再分发需确认权利'),
 ('src_local_planning','D:\\言文\\学业规划','D:\\言文\\学业规划','用户提供资料','2026-10-25','仅用于理解现有规划流程；未把真实学生数据写入库'),
]
insert(cur,'INSERT OR REPLACE INTO sources VALUES(?,?,?,?,?,?)',sources)
files=[]
for p in Path(r'D:\言文').rglob('*'):
    if p.is_file():
        try: st=p.stat()
        except OSError: continue
        try: rel=p.relative_to(r'D:\言文'); scope=rel.parts[0] if rel.parts else ''
        except Exception: scope=''
        files.append((str(p),scope,p.suffix.lower(),st.st_size,datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')))
insert(cur,'INSERT OR IGNORE INTO asset_inventory(path,scope,extension,bytes,modified_at) VALUES(?,?,?,?,?)',files)
ug=pd.read_csv(UG_CSV,dtype=str).fillna('')
cats={}
for _,r in ug.iterrows(): cats[r.discipline_category]=(r.major_code[:2],r.discipline_category)
if '交叉学科' not in cats: cats['交叉学科']=('14','交叉学科')
insert(cur,'INSERT OR REPLACE INTO discipline_categories VALUES(?,?,?)',[(c,n,'undergraduate') for c,n in cats.values()])
classes={}
for _,r in ug.iterrows():
    if r.major_class: classes[r.major_class]=(r.major_code[:4],r.major_class,r.discipline_category)
    elif r.major_code[:2]=='14': classes.setdefault(r.major_code[:4],(r.major_code[:4],'交叉学科类','交叉学科'))
insert(cur,'INSERT OR REPLACE INTO major_classes VALUES(?,?,?)',[(c,n,cats[cat][0]) for c,n,cat in classes.values()])
major_rows=[]
for _,r in ug.iterrows(): major_rows.append((r.major_code,r.major_name,cats[r.discipline_category][0] if r.discipline_category in cats else '',r.major_code[:4],r.degree_note,int(r.is_special=='True'),int(r.is_state_controlled=='True'),'src_ug_2026',int(r.source_page or 0)))
insert(cur,'INSERT OR REPLACE INTO majors VALUES(?,?,?,?,?,?,?,?,?)',major_rows)
gr=pd.read_csv(GR_CSV,dtype=str).fillna('')
insert(cur,'INSERT OR REPLACE INTO graduate_disciplines VALUES(?,?,?,?,?)',[(r.discipline_code,r.discipline_name,r.discipline_category,int(r.is_professional_degree=='True'),'src_gr_2022') for _,r in gr.iterrows()])
subjects={
 'chinese':('语文',['现代文阅读','古诗文阅读','语言基础与运用','写作','名著与综合','修辞与表达']),
 'math':('数学',['数与式','方程与不等式','函数','几何与证明','图形与变换','统计与概率','解题思想','综合应用']),
 'english':('英语',['词汇与语法','单项选择','完形填空','阅读理解','写作','听力与口语','语篇分析']),
 'physics':('物理',['力学','电学','光学','热学','实验与探究']),
 'chemistry':('化学',['物质结构','元素与化合物','化学反应','化学实验','化学计算']),
 'biology':('生物',['细胞与生命活动','遗传与进化','稳态与调节','生态学','实验与探究']),
 'politics':('政治',['经济生活','政治生活','文化生活','哲学生活','法治与社会']),
 'history':('历史',['中国古代史','中国近现代史','世界史','史料分析']),
 'geography':('地理',['自然地理','人文地理','区域地理','地图与地理技能']),
 'it':('信息技术',['数据与算法','网络与安全','编程基础','数字素养']),
 'arts':('艺术',['音乐','美术','艺术鉴赏','创作实践']),
 'pe':('体育与健康',['体能','运动技能','健康管理']),
}
for key,(name,topics) in subjects.items():
    sid='k12:'+key; cur.execute('INSERT OR REPLACE INTO k12_subjects VALUES(?,?,?,?)',(sid,name,'K12','src_local_k12')); cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(sid,'k12',sid,None,key,name,'subject','', 'src_local_k12',1.0))
    for i,t in enumerate(topics,1):
        nid=f'{sid}:topic:{i:02d}'; cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(nid,'k12',sid,sid,f'{key}.{i:02d}',t,'topic','', 'src_local_k12',0.9)); cur.execute('INSERT OR REPLACE INTO knowledge_edges VALUES(?,?,?,?,?)',(sid,nid,'contains',0.9,'src_local_k12'))
for code,name in cats.values():
    nid='ug:category:'+code; cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(nid,'undergraduate',None,None,code,name,'discipline_category','', 'src_ug_2026',1.0))
for code,name,catname in classes.values():
    nid='ug:class:'+code; parent='ug:category:'+cats[catname][0]; cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(nid,'undergraduate',None,parent,code,name,'major_class','', 'src_ug_2026',1.0)); cur.execute('INSERT OR REPLACE INTO knowledge_edges VALUES(?,?,?,?,?)',(parent,nid,'contains',1.0,'src_ug_2026'))
for code,name,catcode,classcode,*_ in major_rows:
    nid='ug:major:'+code; parent='ug:class:'+classcode; cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(nid,'undergraduate',None,parent,code,name,'major','', 'src_ug_2026',1.0)); cur.execute('INSERT OR REPLACE INTO knowledge_edges VALUES(?,?,?,?,?)',(parent,nid,'contains',1.0,'src_ug_2026'))
for _,r in gr.iterrows():
    cat='grad:category:'+hashlib.md5(r.discipline_category.encode()).hexdigest()[:8]; cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(cat,'graduate',None,None,'',r.discipline_category,'discipline_category','', 'src_gr_2022',1.0))
    nid='grad:discipline:'+r.discipline_code; cur.execute('INSERT OR REPLACE INTO knowledge_nodes VALUES(?,?,?,?,?,?,?,?,?,?)',(nid,'graduate',None,cat,r.discipline_code,r.discipline_name,'discipline','', 'src_gr_2022',1.0)); cur.execute('INSERT OR REPLACE INTO knowledge_edges VALUES(?,?,?,?,?)',(cat,nid,'contains',1.0,'src_gr_2022'))
cross={'math':['ug:category:07','ug:category:08'],'physics':['ug:category:08'],'chemistry':['ug:category:08','ug:category:09','ug:category:10'],'biology':['ug:category:09','ug:category:10'],'chinese':['ug:category:01','ug:category:03','ug:category:05'],'english':['ug:category:05','ug:category:02'],'politics':['ug:category:03'],'history':['ug:category:06'],'geography':['ug:category:07']}
for subj,cats2 in cross.items():
    for target in cats2: cur.execute('INSERT OR REPLACE INTO knowledge_edges VALUES(?,?,?,?,?)',('k12:'+subj,target,'supports',0.6,'heuristic'))
riasec=[('R','现实型','Realistic','动手、工具、机械、自然与身体活动'),('I','研究型','Investigative','分析、探究、解释、实验与抽象问题'),('A','艺术型','Artistic','创作、表达、审美与原创'),('S','社会型','Social','帮助、教学、倾听与协作'),('E','企业型','Enterprising','领导、说服、经营、影响与决策'),('C','常规型','Conventional','组织、规则、数据、流程与精确性')]
insert(cur,'INSERT OR REPLACE INTO interest_dimensions VALUES(?,?,?,?)',riasec)
with (ONET/'Occupation Data.txt').open(encoding='utf-8-sig') as f: occ=[(r['O*NET-SOC Code'],r['Title'],r.get('Description',''),'src_onet_301') for r in csv.DictReader(f,delimiter='\t')]
insert(cur,'INSERT OR REPLACE INTO occupations VALUES(?,?,?,?)',occ)
ri_map={'Realistic':'R','Investigative':'I','Artistic':'A','Social':'S','Enterprising':'E','Conventional':'C'}
with (ONET/'Interests.txt').open(encoding='utf-8-sig') as f: ints=[(r['O*NET-SOC Code'],ri_map.get(r['Element Name'],r['Element Name']),float(r['Data Value'])) for r in csv.DictReader(f,delimiter='\t') if r.get('Scale ID')=='OI']
insert(cur,'INSERT OR REPLACE INTO occupation_interests VALUES(?,?,?)',ints)
with (ONET/'RIASEC Keywords.txt').open(encoding='utf-8-sig') as f: keys=[(r['Element ID'][-1].upper(),r['Keyword'],r['Keyword Type']) for r in csv.DictReader(f,delimiter='\t') if r.get('Element ID')]
insert(cur,'INSERT OR REPLACE INTO riasec_keywords VALUES(?,?,?)',keys)
cat_sub={'哲学':[('chinese',.8),('history',.7),('english',.5)],'经济学':[('math',.9),('english',.6),('politics',.5)],'法学':[('chinese',.8),('politics',.8),('history',.6),('english',.5)],'教育学':[('chinese',.7),('math',.5),('english',.6),('psychology',.8)],'文学':[('chinese',.9),('english',.7),('history',.5)],'历史学':[('history',.9),('chinese',.7),('geography',.5)],'理学':[('math',.9),('physics',.7),('chemistry',.6),('biology',.5)],'工学':[('math',.9),('physics',.9),('chemistry',.4),('it',.7)],'农学':[('biology',.8),('chemistry',.7),('math',.5)],'医学':[('biology',.9),('chemistry',.8),('physics',.5),('math',.4)],'管理学':[('math',.7),('chinese',.6),('english',.6)],'艺术学':[('arts',.9),('chinese',.5),('english',.4)],'军事学':[('math',.7),('physics',.6),('politics',.6)],'交叉学科':[('math',.7),('it',.7),('chemistry',.4),('biology',.4)]}
cat_ri={'哲学':{'I':.6,'A':.3},'经济学':{'E':.5,'C':.4,'I':.4},'法学':{'E':.4,'S':.4,'I':.3},'教育学':{'S':.7,'A':.3,'I':.2},'文学':{'A':.5,'S':.3,'I':.2},'历史学':{'I':.6,'A':.2},'理学':{'I':.7,'R':.2,'C':.2},'工学':{'R':.5,'I':.5,'C':.3},'农学':{'R':.5,'I':.4},'医学':{'I':.5,'S':.4,'R':.2},'管理学':{'E':.5,'C':.4,'S':.2},'艺术学':{'A':.8,'S':.2},'军事学':{'R':.4,'E':.4,'C':.3},'交叉学科':{'I':.5,'A':.3,'E':.2}}
req_rows=[]; prof_rows=[]
for code,name,catcode,classcode,*_ in major_rows:
    cat=next((n for c,n in cats.values() if c==catcode),'')
    for subj,w in cat_sub.get(cat,[]): req_rows.append((code,'k12:'+subj,w,'heuristic_category',0.35,'根据学科门类推断，非高校官方选科要求'))
    for r,w in cat_ri.get(cat,{}).items(): prof_rows.append((code,r,w,'heuristic_category',0.3,'根据学科门类推断，需用专业课程与职业数据校准'))
insert(cur,'INSERT OR REPLACE INTO major_subject_requirements VALUES(?,?,?,?,?,?)',req_rows)
insert(cur,'INSERT OR REPLACE INTO major_interest_profiles VALUES(?,?,?,?,?,?)',prof_rows)
try:
    cur.executescript("CREATE VIRTUAL TABLE IF NOT EXISTS search_majors USING fts5(code,name,category,class_name); DELETE FROM search_majors; INSERT INTO search_majors SELECT m.code,m.name,c.name,cl.name FROM majors m JOIN discipline_categories c ON c.code=m.category_code JOIN major_classes cl ON cl.code=m.class_code; CREATE VIRTUAL TABLE IF NOT EXISTS search_occupations USING fts5(code,title,description); DELETE FROM search_occupations; INSERT INTO search_occupations SELECT code,title,description FROM occupations; CREATE VIRTUAL TABLE IF NOT EXISTS search_knowledge USING fts5(node_id,name,node_type,education_level); DELETE FROM search_knowledge; INSERT INTO search_knowledge SELECT node_id,name,node_type,education_level FROM knowledge_nodes;")
except sqlite3.OperationalError as e: print('fts warning',e)
con.commit()
for table in ['majors','major_classes','discipline_categories','graduate_disciplines','k12_subjects','knowledge_nodes','knowledge_edges','occupations','occupation_interests','riasec_keywords','major_subject_requirements','major_interest_profiles','asset_inventory']:
    print(table,cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0])
con.close(); print('db',DB,DB.stat().st_size)
