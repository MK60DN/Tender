from pathlib import Path
import sqlite3, json, hashlib, datetime
BASE=Path(r'D:\Tender'); DATA=BASE/'knowledge_data'; OUT=DATA/'subject_databases'/'university'
OUT.mkdir(parents=True,exist_ok=True); UNI=DATA/'db_university.sqlite'; NOW=datetime.datetime.now().isoformat(timespec='seconds')

# Course lists are compact expert-curated seeds. They record course names and suggested order,
# not institution-specific syllabi. Exact programs must be verified against each university.
COURSE_SEEDS={
'080901':['高等数学','线性代数','概率论与数理统计','离散数学','程序设计基础','数据结构','计算机组成原理','操作系统','计算机网络','数据库系统','软件工程','算法设计与分析','人工智能导论','毕业设计'],
'080902':['高等数学','离散数学','程序设计基础','面向对象程序设计','数据结构','数据库系统','操作系统','软件工程导论','软件需求工程','软件设计与体系结构','软件测试','项目管理','毕业设计'],
'080717T':['高等数学','线性代数','概率论与数理统计','最优化方法','程序设计基础','数据结构','机器学习','深度学习','模式识别','自然语言处理','计算机视觉','人工智能伦理','毕业设计'],
'080910T':['高等数学','线性代数','概率论与数理统计','程序设计基础','数据结构','数据库原理','数据采集与清洗','数据挖掘','大数据技术','数据可视化','机器学习','因果推断','毕业设计'],
'080701':['高等数学','大学物理','电路分析','模拟电子技术','数字电子技术','信号与系统','数字信号处理','通信原理','微机原理与接口','嵌入式系统','电磁场与电磁波','毕业设计'],
'080801':['高等数学','线性代数','大学物理','电路分析','模拟电子技术','数字电子技术','自动控制原理','现代控制理论','传感器与检测技术','电机与拖动','过程控制','毕业设计'],
'100201K':['人体解剖学','组织学与胚胎学','生理学','生物化学','医学细胞生物学','医学遗传学','医学免疫学','病理学','药理学','诊断学','内科学','外科学','妇产科学','儿科学','预防医学','临床实习'],
'100701':['无机化学','有机化学','分析化学','物理化学','生物化学','药理学','药剂学','药物化学','药物分析','生药学','药事管理学','药物代谢动力学','毕业实习'],
'020101':['高等数学','线性代数','概率论与数理统计','微观经济学','宏观经济学','计量经济学','政治经济学','财政学','货币金融学','产业经济学','发展经济学','毕业论文'],
'020301K':['高等数学','线性代数','概率论与数理统计','微观经济学','宏观经济学','货币金融学','公司金融','投资学','金融工程','风险管理','会计学','金融监管与合规','毕业设计'],
'030101K':['法理学','宪法学','民法总论','刑法总论','行政法学','民事诉讼法','刑事诉讼法','商法','经济法','国际法','法律职业伦理','模拟法庭'],
'050101':['现代汉语','古代汉语','语言学概论','中国古代文学','中国现当代文学','外国文学','文学概论','中国文学批评史','写作','民间文学','比较文学','毕业论文'],
'050301':['新闻学概论','传播学概论','新闻采访','新闻写作','新闻编辑','新闻评论','媒介伦理与法规','传播研究方法','数字媒体技术','数据新闻','新闻摄影','毕业实习'],
'070101':['数学分析','高等代数','解析几何','常微分方程','概率论','数理统计','复变函数','抽象代数','实变函数','泛函分析','数值分析','毕业论文'],
'070201':['高等数学','线性代数','力学','热学','电磁学','光学','原子物理学','量子力学','数学物理方法','电动力学','统计物理','固体物理','普通物理实验'],
'070301':['高等数学','大学物理','无机化学','有机化学','分析化学','物理化学','结构化学','仪器分析','高分子化学','化学生物学','化工基础','化学综合实验'],
'071001':['植物学','动物学','生物化学','细胞生物学','遗传学','分子生物学','微生物学','生态学','生理学','生物信息学','生物统计学','综合实验'],
'071101':['普通心理学','实验心理学','心理统计学','心理测量学','发展心理学','社会心理学','认知心理学','生理心理学','异常心理学','咨询心理学','研究设计与论文'],
'082801':['建筑设计基础','建筑制图','建筑构造','建筑结构','中外建筑史','城市设计','建筑物理','建筑设备','场地设计','建筑法规','毕业设计'],
'080205':['设计素描','设计构成','工业设计史','人机工程学','设计思维','产品结构设计','材料与工艺','交互设计','模型制作','设计管理','毕业设计'],
'120203K':['管理学','经济学','基础会计','中级财务会计','高级财务会计','成本管理会计','审计学','财务管理','税法','会计信息系统','财务报表分析','毕业实习'],
'120201K':['管理学原理','微观经济学','宏观经济学','组织行为学','市场营销','财务管理','运营管理','人力资源管理','战略管理','创业管理','商业数据分析','毕业设计'],
'040101':['教育学原理','普通心理学','教育心理学','课程与教学论','教育研究方法','教育测量与评价','教育社会学','教育技术学','班级管理','教师职业道德','教育实习'],
'040106':['学前教育学','儿童发展心理学','学前卫生学','幼儿园课程','幼儿游戏与指导','幼儿园教育活动设计','学前儿童语言教育','学前儿童科学教育','家庭与社区教育','儿童行为观察','教育实习'],
'080201':['高等数学','大学物理','理论力学','材料力学','机械原理','机械设计','工程材料','机械制造技术','液压与气动','控制工程基础','数控技术','毕业设计'],
'080601':['高等数学','大学物理','电路','模拟电子技术','数字电子技术','电机学','电力电子技术','自动控制原理','电力系统分析','继电保护','发电厂电气部分','毕业设计'],
}
BRIDGES={
'080901':[('k12:math',.9),('k12:physics',.6),('k12:it',.8),('k12:english',.5)],
'080902':[('k12:math',.8),('k12:it',.9),('k12:english',.6)],
'080717T':[('k12:math',.95),('k12:it',.9),('k12:physics',.5),('k12:english',.5)],
'080910T':[('k12:math',.95),('k12:it',.9),('k12:english',.5)],
'080701':[('k12:math',.9),('k12:physics',.95),('k12:it',.6)],
'080801':[('k12:math',.85),('k12:physics',.95),('k12:it',.65)],
'100201K':[('k12:biology',.98),('k12:chemistry',.9),('k12:physics',.55),('k12:english',.5)],
'100701':[('k12:chemistry',.98),('k12:biology',.8),('k12:math',.45)],
'020101':[('k12:math',.95),('k12:politics',.7),('k12:english',.7)],
'020301K':[('k12:math',.95),('k12:politics',.6),('k12:english',.65)],
'030101K':[('k12:chinese',.9),('k12:politics',.9),('k12:history',.7)],
'050101':[('k12:chinese',.98),('k12:history',.7),('k12:english',.45)],
'050301':[('k12:chinese',.95),('k12:politics',.7),('k12:english',.75),('k12:history',.5)],
'070101':[('k12:math',.98),('k12:physics',.55),('k12:english',.5)],
'070201':[('k12:math',.95),('k12:physics',.98),('k12:chemistry',.45)],
'070301':[('k12:chemistry',.98),('k12:physics',.65),('k12:math',.55)],
'071001':[('k12:biology',.98),('k12:chemistry',.75),('k12:math',.55)],
'071101':[('k12:biology',.8),('k12:math',.85),('k12:chinese',.65),('k12:english',.6)],
'082801':[('k12:math',.75),('k12:physics',.8),('k12:arts',.8),('k12:geography',.45)],
'080205':[('k12:arts',.9),('k12:physics',.55),('k12:math',.55),('k12:general_technology',.75)],
'120203K':[('k12:math',.8),('k12:politics',.7),('k12:english',.5)],
'120201K':[('k12:math',.7),('k12:politics',.6),('k12:chinese',.55),('k12:english',.55)],
'040101':[('k12:chinese',.6),('k12:math',.5),('k12:biology',.45),('k12:politics',.6),('k12:english',.5)],
'040106':[('k12:chinese',.55),('k12:biology',.55),('k12:politics',.45),('k12:arts',.55),('k12:pe_health',.45)],
'080201':[('k12:math',.85),('k12:physics',.95),('k12:general_technology',.8)],
'080601':[('k12:math',.85),('k12:physics',.98),('k12:it',.5)],
}

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE sources(source_id TEXT PRIMARY KEY,name TEXT,url_or_path TEXT,license TEXT,retrieved_at TEXT,usage_note TEXT);
CREATE TABLE discipline_categories(code TEXT PRIMARY KEY,name TEXT,level TEXT);
CREATE TABLE major_classes(code TEXT PRIMARY KEY,name TEXT,category_code TEXT,source_id TEXT);
CREATE TABLE majors(code TEXT PRIMARY KEY,name TEXT,category_code TEXT,class_code TEXT,degree_note TEXT,source_id TEXT);
CREATE TABLE graduate_disciplines(code TEXT PRIMARY KEY,name TEXT,category_name TEXT,is_professional_degree INTEGER,source_id TEXT);
CREATE TABLE major_subject_requirements(major_code TEXT,subject_id TEXT,weight REAL,evidence_type TEXT,confidence REAL,note TEXT,PRIMARY KEY(major_code,subject_id));
CREATE TABLE admission_subject_requirements(id INTEGER PRIMARY KEY,university TEXT,province TEXT,year INTEGER,major_code TEXT,subject_requirement TEXT,source_url TEXT,verified INTEGER DEFAULT 0);
CREATE TABLE major_courses(course_id TEXT PRIMARY KEY,major_code TEXT,course_name TEXT,course_type TEXT,knowledge_domain TEXT,sequence_no INTEGER,source_id TEXT,evidence_type TEXT,confidence REAL);
CREATE TABLE course_edges(source_course TEXT,target_course TEXT,relation TEXT,strength REAL,evidence_type TEXT,note TEXT,PRIMARY KEY(source_course,target_course,relation));
CREATE TABLE major_competencies(major_code TEXT,competency TEXT,weight REAL,evidence_type TEXT,PRIMARY KEY(major_code,competency));
CREATE TABLE major_highschool_bridges(major_code TEXT,subject_id TEXT,weight REAL,evidence_type TEXT,confidence REAL,note TEXT,PRIMARY KEY(major_code,subject_id));
CREATE TABLE program_coverage(major_code TEXT PRIMARY KEY,coverage_status TEXT,course_count INTEGER,evidence_note TEXT);
CREATE TABLE course_knowledge_links(course_id TEXT,subject_id TEXT,node_id TEXT,relation TEXT,strength REAL,PRIMARY KEY(course_id,subject_id,node_id,relation));
CREATE VIEW v_major_course_sequence AS SELECT m.code major_code,m.name major_name,c.sequence_no,c.course_name,c.course_type,c.knowledge_domain FROM majors m JOIN major_courses c ON c.major_code=m.code ORDER BY m.code,c.sequence_no;
'''


CATEGORY_SLUG={'01':'philosophy','02':'economics','03':'law','04':'education','05':'literature','06':'history','07':'science','08':'engineering','09':'agriculture','10':'medicine','12':'management','13':'arts','14':'interdisciplinary'}

CATEGORY_COMPETENCIES={
'01':['概念分析','论证评估','文本解释'], '02':['经济建模','统计分析','决策判断'],
'03':['规范解释','证据推理','论证写作'], '04':['学习支持','沟通协作','研究评价'],
'05':['文本细读','表达创作','文化理解'], '06':['史料实证','时空定位','历史解释'],
'07':['抽象建模','实验探究','数据分析'], '08':['工程建模','系统设计','实现验证'],
'09':['生命与生态认知','生产管理','实验实践'], '10':['临床或健康推理','实验操作','伦理责任'],
'12':['组织协调','数据决策','运营管理'], '13':['审美判断','创意表达','作品分析'],
'14':['跨学科整合','建模计算','创新实践']}

def sha(text): return hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]
def course_type(name,index,total):
    if name.endswith(('实习','实验','设计','论文')): return '综合实践'
    if index<=4: return '学科基础'
    if index>=total-1: return '专业方向'
    return '专业核心'
def domain_for(name):
    keys=[('数学','数学与自然科学'),('物理','数学与自然科学'),('化学','化学与生命科学'),('生物','化学与生命科学'),('统计','数学与自然科学'),('程序','计算与系统'),('数据','计算与系统'),('计算机','计算与系统'),('算法','计算与系统'),('网络','计算与系统'),('电路','电子与工程'),('电子','电子与工程'),('控制','电子与工程'),('机械','工程与制造'),('建筑','空间与工程'),('设计','设计与表达'),('经济','经济与管理'),('金融','经济与管理'),('会计','经济与管理'),('管理','经济与管理'),('心理','心理与行为'),('教育','教育与学习'),('文学','人文与语言'),('汉语','人文与语言'),('新闻','传播与表达'),('法','法律与制度'),('药','医学与健康'),('诊断','医学与健康'),('临床','医学与健康'),('解剖','医学与健康'),('生理','医学与健康'),('病理','医学与健康')]
    for k,v in keys:
        if k in name: return v
    return '专业综合'

def base_schema(con,role,code='',name=''):
    con.executescript(SCHEMA)
    con.execute('INSERT INTO metadata VALUES(?,?)',('role',role))
    con.execute('INSERT INTO metadata VALUES(?,?)',('created_at',NOW))
    if code: con.execute('INSERT INTO metadata VALUES(?,?)',('category_code',code))
    if name: con.execute('INSERT INTO metadata VALUES(?,?)',('category_name',name))
    con.execute('INSERT INTO sources VALUES(?,?,?,?,?,?)',('src_ug_2026','普通高等学校本科专业目录（2026年）','https://www.moe.gov.cn/','教育部公开文件',NOW,'官方专业代码、专业类和门类事实'))
    con.execute('INSERT INTO sources VALUES(?,?,?,?,?,?)',('src_ug_quality_2018','普通高等学校本科专业类教学质量国家标准（2018）','https://www.moe.gov.cn/jyb_xwfb/xw_fbh/moe_2069/xwfbh_2018n/xwfbh_20180130/mtbd/201801/t20180131_326071.html','教育部公开标准',NOW,'课程名称与知识领域为结构化种子，不逐字复制原文'))

def add_courses(con,major_code,courses):
    ids=[]
    total=len(courses)
    for i,name in enumerate(courses,1):
        cid=f'{major_code}:course:{i:03d}:{sha(name)}'; ids.append(cid)
        con.execute('INSERT INTO major_courses VALUES(?,?,?,?,?,?,?,?,?)',(cid,major_code,name,course_type(name,i,total),domain_for(name),i,'src_ug_quality_2018','curated_seed',0.78))
    for a,b in zip(ids,ids[1:]):
        con.execute('INSERT INTO course_edges VALUES(?,?,?,?,?,?)',(a,b,'recommended_sequence',0.55,'expert_curated','推荐学习顺序，不表示硬性先修'))
    con.execute('INSERT INTO program_coverage VALUES(?,?,?,?)',(major_code,'course_seed_available',total,'课程名为结构化种子；高校实际课程名称、学分和先修关系须以培养方案复核'))
    comps=CATEGORY_COMPETENCIES.get(major_code[:2],['持续学习'])
    for comp in comps:
        con.execute('INSERT INTO major_competencies VALUES(?,?,?,?)',(major_code,comp,round(1.0/len(comps),3),'expert_curated'))
    for subject_id,weight in BRIDGES.get(major_code,[]):
        con.execute('INSERT INTO major_highschool_bridges VALUES(?,?,?,?,?,?)',(major_code,subject_id,weight,'expert_curated',0.68,'高中学科相关性提示，不是官方选科要求'))

src=sqlite3.connect(UNI); src.row_factory=sqlite3.Row
cats={r['code']:dict(r) for r in src.execute('SELECT * FROM discipline_categories')}
classes={r['code']:dict(r) for r in src.execute('SELECT * FROM major_classes')}
majors={r['code']:dict(r) for r in src.execute('SELECT * FROM majors')}
grad=[dict(r) for r in src.execute('SELECT * FROM graduate_disciplines')]
reqs=[dict(r) for r in src.execute('SELECT * FROM major_subject_requirements')]
admissions=[dict(r) for r in src.execute('SELECT * FROM admission_subject_requirements')]
src.close()

UNION=DATA/'db_university_courses.sqlite'
if UNION.exists(): UNION.unlink()
u=sqlite3.connect(UNION); base_schema(u,'university_course_union')
for code,c in cats.items(): u.execute('INSERT INTO discipline_categories VALUES(?,?,?)',(code,c['name'],c['level']))
for code,c in classes.items(): u.execute('INSERT INTO major_classes VALUES(?,?,?,?)',(code,c['name'],c['category_code'],'src_ug_2026'))
for code,m in majors.items(): u.execute('INSERT INTO majors VALUES(?,?,?,?,?,?)',(code,m['name'],m['category_code'],m['class_code'],m.get('degree_note'),'src_ug_2026'))
for g in grad: u.execute('INSERT INTO graduate_disciplines VALUES(?,?,?,?,?)',(g['code'],g['name'],g['category_name'],g['is_professional_degree'],g['source_id']))
for r in reqs: u.execute('INSERT INTO major_subject_requirements VALUES(?,?,?,?,?,?)',(r['major_code'],r['subject_id'],r['weight'],r['evidence_type'],r['confidence'],r['note']))
for r in admissions: u.execute('INSERT INTO admission_subject_requirements VALUES(?,?,?,?,?,?,?,?)',(r['id'],r['university'],r['province'],r['year'],r['major_code'],r['subject_requirement'],r['source_url'],r['verified']))
for major_code,courses in COURSE_SEEDS.items():
    if major_code in majors: add_courses(u,major_code,courses)
u.commit()

results=[]
for cat_code,cat in sorted(cats.items()):
    filename=f'db_ug_{cat_code.zfill(2)}_{CATEGORY_SLUG.get(cat_code,sha(cat["name"]))}.sqlite'; path=OUT/filename
    if path.exists(): path.unlink()
    con=sqlite3.connect(path); base_schema(con,'university_discipline_database',cat_code,cat['name'])
    con.execute('INSERT INTO discipline_categories VALUES(?,?,?)',(cat_code,cat['name'],cat['level']))
    cat_classes=[c for c in classes.values() if c['category_code']==cat_code]
    cat_majors=[m for m in majors.values() if m['category_code']==cat_code]
    for c in cat_classes: con.execute('INSERT INTO major_classes VALUES(?,?,?,?)',(c['code'],c['name'],c['category_code'],'src_ug_2026'))
    for m in cat_majors: con.execute('INSERT INTO majors VALUES(?,?,?,?,?,?)',(m['code'],m['name'],m['category_code'],m['class_code'],m.get('degree_note'),'src_ug_2026'))
    for g in grad:
        if g['category_name']==cat['name']: con.execute('INSERT INTO graduate_disciplines VALUES(?,?,?,?,?)',(g['code'],g['name'],g['category_name'],g['is_professional_degree'],g['source_id']))
    for r in reqs:
        if majors.get(r['major_code'],{}).get('category_code')==cat_code:
            con.execute('INSERT INTO major_subject_requirements VALUES(?,?,?,?,?,?)',(r['major_code'],r['subject_id'],r['weight'],r['evidence_type'],r['confidence'],r['note']))
    for major_code,courses in COURSE_SEEDS.items():
        if majors.get(major_code,{}).get('category_code')==cat_code: add_courses(con,major_code,courses)
    con.commit()
    counts={t:con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['major_classes','majors','graduate_disciplines','major_courses','course_edges','major_highschool_bridges']}
    con.close()
    results.append({'category_code':cat_code,'name':cat['name'],'db':str(path),'counts':counts})

union_counts={t:u.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['majors','major_courses','course_edges','major_highschool_bridges','major_competencies']}
u.commit(); u.close()

INDEX=OUT/'db_university_index.sqlite'
if INDEX.exists(): INDEX.unlink()
idx=sqlite3.connect(INDEX)
idx.executescript('''
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE category_catalog(category_code TEXT PRIMARY KEY,name TEXT,db_file TEXT,majors INTEGER,major_classes INTEGER,major_courses INTEGER);
CREATE TABLE course_catalog(course_id TEXT PRIMARY KEY,major_code TEXT,major_name TEXT,course_name TEXT,course_type TEXT,knowledge_domain TEXT,source_id TEXT,evidence_type TEXT,confidence REAL);
''')
idx.execute('INSERT INTO metadata VALUES(?,?)',('role','university_subject_index')); idx.execute('INSERT INTO metadata VALUES(?,?)',('created_at',NOW))
for r in results:
    idx.execute('INSERT INTO category_catalog VALUES(?,?,?,?,?,?)',(r['category_code'],r['name'],Path(r['db']).name,r['counts']['majors'],r['counts']['major_classes'],r['counts']['major_courses']))
u=sqlite3.connect(UNION); u.row_factory=sqlite3.Row
for r in u.execute('SELECT c.course_id,c.major_code,m.name major_name,c.course_name,c.course_type,c.knowledge_domain,c.source_id,c.evidence_type,c.confidence FROM major_courses c JOIN majors m ON m.code=c.major_code'):
    idx.execute('INSERT INTO course_catalog VALUES(?,?,?,?,?,?,?,?,?)',tuple(r))
u.close(); idx.commit(); idx.close()
manifest={'created_at':NOW,'index':str(INDEX),'union':str(UNION),'union_counts':union_counts,'categories':results,'notes':['All 875 majors retain official directory metadata.','Course-level profiles cover a representative seed of 27 majors and require university-program verification.','High-school bridges are relevance hints, not official admission requirements.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'categories':len(results),'seed_majors':len(COURSE_SEEDS),'counts':union_counts},ensure_ascii=False,indent=2))
