from pathlib import Path
import sqlite3, json, hashlib, datetime

BASE = Path(r'D:\Tender')
OUT = BASE / 'knowledge_data' / 'subject_databases'
OUT.mkdir(parents=True, exist_ok=True)
NOW = datetime.datetime.now().isoformat(timespec='seconds')

STANDARD_URLS = {
    'hs': 'https://www.moe.gov.cn/srcsite/A26/s8001/202006/t20200603_462199.html',
    'cs': 'https://www.moe.gov.cn/srcsite/A26/s8001/202204/t20220420_619921.html',
}

# Each unit is (unit_name, module, concepts, prior_units, question_modes)
# Concepts are short curriculum knowledge points, not copied passages.
SUBJECTS = {
'math': {
 'name':'数学', 'stem':'hs_03_math',
 'competencies':['数学抽象','逻辑推理','数学建模','直观想象','数学运算','数据分析'],
 'domains':[
  ('预备知识','必修',[
   ('集合',['集合的含义与表示','元素与集合的关系','集合间的基本关系','集合的基本运算','有限集与无限集'],[],['概念辨析','集合运算','参数讨论']),
   ('常用逻辑用语',['命题与量词','充分条件与必要条件','全称量词与存在量词','命题的否定'],[],['条件判断','命题改写','逻辑推理']),
   ('相等关系与不等关系',['等式性质','不等式性质','比较大小','基本不等式'],[],['性质判断','最值问题','证明']),
   ('一元二次方程与不等式',['一元二次方程','判别式','根与系数关系','一元二次不等式','不等式恒成立'],[],['解不等式','根的分布','参数问题']),
  ]),
  ('函数','必修',[
   ('函数概念与性质',['函数概念','定义域与值域','函数的表示','单调性','奇偶性','周期性','最值','函数图象'],[],['图象识别','性质判断','抽象函数']),
   ('幂函数、指数函数与对数函数',['幂函数','指数与指数函数','对数与对数函数','函数增长比较','指数方程与对数方程'],[],['比较大小','复合函数','方程求解']),
   ('三角函数',['角与弧度制','三角函数定义','同角三角函数关系','诱导公式','三角恒等变换','正弦型函数图象','解三角形'],[],['求值化简','图象变换','解三角形']),
   ('函数应用',['函数模型','零点与二分法','实际情境建模','模型检验'],[],['零点判断','建模','参数估计']),
  ]),
  ('几何与代数','必修',[
   ('平面向量及其应用',['向量的概念','向量线性运算','数量积','向量坐标表示','向量在几何中的应用'],[],['坐标运算','几何证明','最值']),
   ('复数',['复数的概念','复数几何意义','复数四则运算','共轭复数','复数方程'],[],['化简','几何意义','方程']),
   ('立体几何初步',['空间几何体','表面积与体积','点线面位置关系','平行关系','垂直关系','空间角与距离'],[],['位置关系判断','证明','体积计算']),
  ]),
  ('概率与统计','必修',[
   ('概率',['样本空间','随机事件','古典概型','概率基本性质','互斥与独立'],[],['古典概型','事件关系','概率计算']),
   ('统计',['抽样方法','频率分布','集中趋势与离散程度','图表读取','用样本估计总体'],[],['图表分析','统计量计算','抽样判断']),
  ]),
  ('数学建模与探究','必修',[
   ('数学建模活动',['问题提出','模型假设','数学表达','模型求解','结果检验','论文表达'],[],['开放探究','建模报告','跨学科应用']),
  ]),
  ('函数深化','选择性必修',[
   ('数列',['数列概念','等差数列','等比数列','数列求和','递推数列'],[],['通项公式','求和','递推分析']),
   ('导数及其应用',['导数概念','基本求导公式','导数与单调性','极值与最值','导数与不等式'],[],['切线','单调性','最值证明']),
  ]),
  ('几何与代数深化','选择性必修',[
   ('直线与圆',['直线方程','两直线位置关系','圆的方程','直线与圆的位置关系'],[],['方程选择','距离','位置关系']),
   ('圆锥曲线',['椭圆','双曲线','抛物线','直线与圆锥曲线','曲线与方程'],[],['标准方程','离心率','定点定值']),
   ('空间向量与立体几何',['空间直角坐标系','空间向量运算','空间向量求角','空间向量求距离'],[],['坐标法','角度计算','证明']),
  ]),
  ('概率与统计深化','选择性必修',[
   ('计数原理',['分类加法','分步乘法','排列','组合','二项式定理'],[],['计数','系数','分组分配']),
   ('随机变量及其分布',['离散型随机变量','分布列','期望与方差','二项分布','正态分布'],[],['分布列','期望方差','实际决策']),
   ('统计案例',['成对数据','相关关系','回归直线','独立性检验'],[],['相关性','回归','列联表']),
  ]),
 ]},
'chinese': {
 'name':'语文', 'stem':'hs_02_chinese',
 'competencies':['语言建构与运用','思维发展与提升','审美鉴赏与创造','文化传承与理解'],
 'domains':[
  ('语言基础','必修',[
   ('语音与汉字',['普通话读音','多音字','形近字','汉字结构','规范书写'],[],['字音辨析','字形辨析','书写']),
   ('词语与成语',['词义辨析','近义词','成语使用','熟语','语境义'],[],['选词填空','成语判断','语境解释']),
   ('语法与修辞',['词性','短语结构','句子成分','病句修改','常见修辞','句式变换'],[],['病句','修辞赏析','句式效果']),
  ]),
  ('现代文阅读','必修',[
   ('信息类文本',['论点与论据','论证结构','论证方法','信息筛选','观点评价','材料比较'],[],['信息提取','论证分析','多材料比较']),
   ('文学类文本',['人物形象','情节结构','环境描写','叙事视角','语言风格','主题意蕴'],[],['人物分析','作用题','主旨探究']),
   ('实用类文本',['说明对象','说明方法','新闻事实','报告结构','图表信息'],[],['概括','方法判断','信息整合']),
  ]),
  ('古诗文阅读','必修',[
   ('文言实词与虚词',['通假字','古今异义','词类活用','一词多义','常见虚词','特殊句式'],[],['实词解释','虚词辨析','句式翻译']),
   ('文言文阅读',['断句','内容概括','人物评价','翻译','文化常识'],[],['断句','翻译','内容分析']),
   ('古代诗歌',['意象','意境','表达技巧','语言风格','情感主旨','比较阅读'],[],['意象分析','手法鉴赏','情感比较']),
  ]),
  ('写作','必修',[
   ('审题立意',['材料类型','任务指令','核心概念','立意范围','思辨关系'],[],['材料作文','命题作文','任务驱动']),
   ('结构谋篇',['中心论点','分论点','论证结构','开头结尾','段落衔接'],[],['提纲','结构评价','逻辑衔接']),
   ('论据与表达',['事实论据','道理论据','例证分析','语言润色','修改升格'],[],['论据选择','论证展开','升格']),
  ]),
  ('整本书阅读与综合实践','必修',[
   ('整本书阅读',['阅读计划','情节梳理','人物关系','主题探究','阅读笔记','成果表达'],[],['专题探究','读书报告','展示']),
   ('综合性学习',['问题确定','资料搜集','访谈调查','成果整合','口头表达'],[],['项目式学习','调查报告','展示答辩']),
  ]),
 ]},
'english': {
 'name':'英语', 'stem':'hs_04_english',
 'competencies':['语言能力','文化意识','思维品质','学习能力'],
 'domains':[
  ('语言知识','必修',[
   ('语音与词汇',['音标与重音','连读弱读','构词法','核心词汇','词块搭配','熟词生义'],[],['语音识别','词汇辨析','构词判断']),
   ('语法基础',['词类','句子成分','时态','语态','非谓语动词','情态动词'],[],['语法填空','单句改错','句子翻译']),
   ('从句与复杂句',['定语从句','状语从句','名词性从句','主谓一致','倒装','强调'],[],['从句判断','长难句分析','句式改写']),
  ]),
  ('语篇理解','必修',[
   ('阅读理解',['主旨大意','细节定位','词义猜测','推理判断','作者态度','篇章结构'],[],['阅读理解','七选五','信息匹配']),
   ('完形填空',['语境线索','语义衔接','逻辑关系','词汇复现','情感态度'],[],['完形填空','语篇填空']),
   ('语篇分析',['主题语境','段落功能','衔接手段','信息组织','文体特征'],[],['结构分析','语篇标记','摘要']),
  ]),
  ('表达与交流','必修',[
   ('听力与口语',['场景预测','关键信息','语音辨识','观点回应','交际策略'],[],['听力选择','情境问答','口头表达']),
   ('应用文写作',['书信','通知','申请','建议信','活动介绍','格式规范'],[],['提纲','应用文','改写']),
   ('读后续写',['情节衔接','人物一致','动作描写','心理描写','语言润色','主题升华'],[],['续写','情节设计','语言升格']),
  ]),
  ('文化与学习策略','必修',[
   ('跨文化理解',['文化比较','价值表达','社会习俗','国际理解','中国故事'],[],['文化判断','观点表达','项目展示']),
   ('学习策略',['目标管理','词汇复习','错题分析','语料积累','自我评价'],[],['计划制定','反思','自主监测']),
  ]),
 ]},
'physics': {
 'name':'物理', 'stem':'hs_08_physics',
 'competencies':['物理观念','科学思维','科学探究','科学态度与责任'],
 'domains':[
  ('力学','必修',[
   ('运动的描述',['质点与参考系','位移与路程','速度与加速度','运动图象','匀变速直线运动'],[],['图象分析','运动学计算','实验']),
   ('相互作用',['重力','弹力','摩擦力','力的合成与分解','共点力平衡'],[],['受力分析','平衡计算','动态平衡']),
   ('牛顿运动定律',['牛顿第一定律','牛顿第二定律','牛顿第三定律','超重与失重','连接体问题'],[],['受力与运动','临界问题','实验']),
   ('曲线运动与万有引力',['运动的合成与分解','平抛运动','圆周运动','万有引力定律','天体运动'],[],['轨迹分析','向心力','天体质量']),
   ('机械能',['功与功率','动能定理','重力势能','机械能守恒','功能关系'],[],['能量守恒','过程分析','实验']),
   ('动量',['冲量','动量定理','动量守恒','碰撞','反冲'],[],['动量守恒','碰撞计算','模型']),
  ]),
  ('电磁学','必修',[
   ('静电场',['电荷','库仑定律','电场强度','电势与电势能','电容器','带电粒子运动'],[],['场强叠加','电势判断','粒子运动']),
   ('恒定电流',['电流','欧姆定律','电阻定律','电功与电功率','闭合电路欧姆定律','电学实验'],[],['电路计算','故障分析','实验设计']),
   ('磁场',['磁场与磁感线','安培力','洛伦兹力','带电粒子在磁场中运动'],[],['方向判断','轨迹分析','综合计算']),
   ('电磁感应',['磁通量','楞次定律','法拉第电磁感应定律','自感与互感','电磁感应中的能量'],[],['感应方向','感应电动势','图像问题']),
   ('交变电流',['交流电产生','有效值','变压器','远距离输电'],[],['有效值','变压器','输电']),
  ]),
  ('热学','选择性必修',[
   ('分子动理论与气体',['分子热运动','分子力','气体实验定律','理想气体状态方程','气体压强微观解释'],[],['气体状态变化','图像','微观解释']),
   ('热力学定律',['内能','热力学第一定律','热力学第二定律','能量守恒'],[],['功热关系','熵增判断','计算']),
  ]),
  ('振动、波与光学','选择性必修',[
   ('机械振动与机械波',['简谐运动','单摆','受迫振动','波的形成','波的描述','波的干涉与衍射'],[],['振动图像','波动图像','波的多解']),
   ('光学',['光的折射','全反射','光的干涉','光的衍射','光的偏振','光电效应'],[],['光路','干涉条纹','光电效应']),
  ]),
  ('近代物理与实验','选择性必修',[
   ('原子与原子核',['原子结构','能级','原子核组成','放射性衰变','核反应','质能方程'],[],['能级跃迁','衰变','核能计算']),
   ('物理实验',['测量与误差','实验设计','数据处理','图象拟合','误差分析'],[],['力学实验','电学实验','创新实验']),
  ]),
 ]},
'chemistry': {
 'name':'化学', 'stem':'hs_09_chemistry',
 'competencies':['宏观辨识与微观探析','变化观念与平衡思想','证据推理与模型认知','科学探究与创新意识','科学态度与社会责任'],
 'domains':[
  ('物质结构','必修',[
   ('原子结构与元素周期律',['原子结构','核外电子排布','元素周期表','元素周期律','元素性质递变'],[],['结构推断','周期律比较','元素推断']),
   ('化学键与物质结构',['离子键','共价键','金属键','分子间作用力','氢键','晶体类型'],[],['键型判断','结构解释','性质比较']),
   ('物质的量与化学计量',['物质的量','摩尔质量','气体摩尔体积','物质的量浓度','化学计量计算'],[],['浓度计算','方程式计算','误差分析']),
  ]),
  ('化学反应原理','选择性必修',[
   ('氧化还原与离子反应',['氧化还原反应','氧化剂与还原剂','离子反应','离子方程式','电子守恒'],[],['配平','离子共存','方程式书写']),
   ('化学反应速率与平衡',['反应速率','影响因素','化学平衡','平衡常数','平衡移动','工业条件选择'],[],['速率图像','平衡计算','条件优化']),
   ('水溶液中的平衡',['弱电解质电离','水的离子积','盐类水解','沉淀溶解平衡','酸碱中和滴定'],[],['pH计算','离子浓度比较','滴定曲线']),
   ('电化学',['原电池','电解池','电极反应','电化学腐蚀','新型电池'],[],['电极判断','电池书写','定量计算']),
   ('反应热',['焓变','热化学方程式','盖斯定律','反应热计算'],[],['焓变判断','盖斯定律','能量图']),
  ]),
  ('元素化合物','必修',[
   ('金属元素',['钠及其化合物','铁及其化合物','铝及其化合物','金属冶炼','金属材料'],[],['性质推断','转化关系','实验探究']),
   ('非金属元素',['氯及其化合物','硫及其化合物','氮及其化合物','硅及其化合物','无机非金属材料'],[],['性质推断','转化关系','环境问题']),
  ]),
  ('有机化学','选择性必修',[
   ('烃与卤代烃',['烷烃','烯烃','炔烃','芳香烃','卤代烃'],[],['结构性质','同分异构','反应类型']),
   ('烃的衍生物',['醇','酚','醛','羧酸','酯','油脂'],[],['官能团','转化关系','合成路线']),
   ('生物大分子与高分子',['糖类','蛋白质','核酸','合成高分子','功能高分子'],[],['结构判断','性质应用','材料']),
   ('有机合成与推断',['官能团转化','保护基','合成路线','逆合成分析','同分异构体'],[],['推断','路线设计','异构计数']),
  ]),
  ('实验与STSE','必修',[
   ('化学实验基础',['仪器使用','基本操作','物质分离提纯','检验与鉴别','实验安全'],[],['操作判断','实验方案','安全评价']),
   ('实验探究与化工流程',['变量控制','实验设计','证据链','流程图分析','产率与纯度'],[],['流程题','探究题','定量实验']),
   ('化学与社会',['能源','材料','环境','健康','可持续发展'],[],['情境判断','证据评价','方案设计']),
  ]),
 ]},
'biology': {
 'name':'生物学', 'stem':'hs_10_biology',
 'competencies':['生命观念','科学思维','科学探究','社会责任'],
 'domains':[
  ('分子与细胞','必修',[
   ('细胞的分子组成',['水与无机盐','糖类','脂质','蛋白质','核酸','生物大分子功能'],[],['结构功能','实验鉴定','概念判断']),
   ('细胞结构',['细胞膜','细胞器','细胞核','细胞骨架','原核与真核细胞'],[],['结构辨析','功能联系','显微观察']),
   ('细胞代谢',['酶','ATP','细胞呼吸','光合作用','影响因素','物质与能量'],[],['过程分析','曲线','实验探究']),
   ('细胞生命历程',['细胞增殖','有丝分裂','细胞分化','细胞衰老','细胞凋亡','癌变'],[],['分裂图像','概念判断','机制解释']),
  ]),
  ('遗传与进化','必修',[
   ('遗传规律',['分离定律','自由组合定律','性状与基因','伴性遗传','遗传系谱'],[],['系谱分析','概率计算','实验设计']),
   ('分子遗传',['DNA结构','DNA复制','转录','翻译','中心法则','基因表达调控'],[],['过程判断','碱基计算','信息流分析']),
   ('变异与育种',['基因突变','基因重组','染色体变异','育种方法','生物多样性'],[],['变异类型','育种方案','比较']),
   ('进化',['自然选择','种群基因频率','物种形成','共同进化','进化证据'],[],['频率计算','机制解释','证据推理']),
  ]),
  ('稳态与调节','选择性必修',[
   ('神经调节',['神经元','反射','兴奋传导','突触传递','中枢调节'],[],['传导方向','实验分析','机制解释']),
   ('体液调节',['激素','血糖调节','体温调节','水盐调节','激素分级调节'],[],['调节路径','曲线','实验']),
   ('免疫调节',['免疫系统','非特异性免疫','特异性免疫','免疫失调','疫苗'],[],['过程判断','免疫应用','实验']),
   ('植物调节',['生长素','其他植物激素','向性运动','植物生长调节剂'],[],['作用特点','实验设计','应用']),
  ]),
  ('生态与生物技术','选择性必修',[
   ('种群与群落',['种群特征','种群增长','群落结构','演替','种间关系'],[],['增长曲线','群落分析','调查']),
   ('生态系统',['能量流动','物质循环','信息传递','生态平衡','生态修复'],[],['能量计算','系统分析','方案设计']),
   ('生物技术与工程',['发酵工程','细胞工程','基因工程','胚胎工程','生物安全'],[],['流程分析','技术应用','伦理判断']),
  ]),
  ('实验与探究','必修',[
   ('生物实验',['显微观察','对照实验','变量控制','数据处理','实验评价'],[],['实验设计','结果分析','评价']),
  ]),
 ]},
'politics': {
 'name':'思想政治', 'stem':'hs_05_politics',
 'competencies':['政治认同','科学精神','法治意识','公共参与'],
 'domains':[
  ('中国特色社会主义','必修',[
   ('社会发展规律',['生产力与生产关系','经济基础与上层建筑','社会形态更替','人类社会发展规律'],[],['概念判断','材料分析','逻辑推理']),
   ('中国特色社会主义',['社会主义初级阶段','中国特色社会主义道路','制度优势','中国式现代化','习近平新时代中国特色社会主义思想'],[],['理论阐述','材料分析','观点评价']),
  ]),
  ('经济与社会','必修',[
   ('基本经济制度',['公有制为主体','多种所有制共同发展','按劳分配为主体','社会主义市场经济体制'],[],['制度判断','材料分析','比较']),
   ('微观经济运行',['价格机制','消费','生产与经营','就业','收入分配','社会保障'],[],['曲线题','案例分析','方案设计']),
   ('宏观经济',['宏观调控','财政政策','货币政策','高质量发展','新发展格局'],[],['政策判断','传导路径','综合分析']),
  ]),
  ('政治与法治','必修',[
   ('国家与民主',['国家性质','人民代表大会制度','全过程人民民主','政党制度','民族区域自治','基层群众自治'],[],['制度分析','案例判断','论述']),
   ('全面依法治国',['法治国家','法治政府','法治社会','科学立法','严格执法','公正司法','全民守法'],[],['法治案例','程序判断','论述']),
  ]),
  ('哲学与文化','必修',[
   ('辩证唯物论',['物质与意识','规律客观性','主观能动性','一切从实际出发'],[],['原理阐述','材料对应','辨析']),
   ('唯物辩证法',['联系观','发展观','矛盾观','量变质变','否定之否定'],[],['关系分析','矛盾分析','材料论证']),
   ('认识论与历史唯物主义',['实践与认识','真理','社会存在与社会意识','人民群众','价值判断与价值选择'],[],['认识过程','价值分析','论述']),
   ('文化',['文化功能','文化传承','文化创新','文化交流互鉴','中华优秀传统文化','文化自信'],[],['文化分析','案例评价','方案设计']),
  ]),
  ('当代国际政治与经济','选择性必修',[
   ('国际社会',['主权国家','国际组织','国家利益','国际关系','全球治理','人类命运共同体'],[],['主体分析','利益判断','国际案例']),
  ]),
 ]},
'history': {
 'name':'历史', 'stem':'hs_06_history',
 'competencies':['唯物史观','时空观念','史料实证','历史解释','家国情怀'],
 'domains':[
  ('中国古代史','必修',[
   ('先秦与秦汉',['中华文明起源','夏商周','春秋战国','秦统一','汉朝治理','丝绸之路'],[],['时空定位','制度比较','史料分析']),
   ('魏晋至隋唐',['民族交融','区域开发','隋唐制度','经济发展','文化交流'],[],['阶段特征','制度演变','史料实证']),
   ('宋元明清',['中央集权','商品经济','民族关系','对外交流','思想文化','社会转型'],[],['比较','因果分析','史料评价']),
  ]),
  ('中国近现代史','必修',[
   ('晚清变局',['鸦片战争','太平天国','洋务运动','甲午战争','戊戌变法','义和团与辛丑条约'],[],['背景影响','史料辨析','比较']),
   ('辛亥革命与民国',['清末新政','辛亥革命','中华民国建立','五四运动','国民革命'],[],['事件评价','因果链','时空定位']),
   ('中国共产党与新民主主义革命',['中国共产党诞生','土地革命','抗日战争','解放战争','新中国成立'],[],['史料分析','战略判断','历史解释']),
   ('社会主义建设与改革开放',['社会主义改造','社会主义建设探索','改革开放','社会主义市场经济','新时代成就'],[],['阶段特征','政策影响','综合论述']),
  ]),
  ('世界史','必修',[
   ('古代与中古世界',['古代文明','希腊罗马','中古欧洲','亚非文明','文明交流'],[],['文明比较','地图定位','史料解读']),
   ('近代世界',['文艺复兴','新航路开辟','宗教改革','启蒙运动','资产阶级革命','工业革命'],[],['因果分析','制度比较','全球联系']),
   ('现代世界',['世界大战','俄国革命','民族解放','冷战','全球化','国际秩序'],[],['时间线','利益分析','历史评价']),
  ]),
  ('史学方法与专题','选择性必修',[
   ('史料与史学',['史料分类','史料价值','证据链','历史解释','历史写作'],[],['史料辨析','论证','小论文']),
   ('政治与制度',['国家制度','社会治理','法律与教化','官员选拔','基层治理'],[],['制度演变','比较','影响']),
   ('经济与社会',['农业','商业','工业','货币金融','城市化','社会保障'],[],['经济变迁','数据史料','因果']),
   ('文化交流',['人口迁徙','商贸往来','战争与和平','文化传播','文明互鉴'],[],['地图','传播路径','影响']),
  ]),
 ]},
'geography': {
 'name':'地理', 'stem':'hs_07_geography',
 'competencies':['人地协调观','综合思维','区域认知','地理实践力'],
 'domains':[
  ('地理基础','必修',[
   ('地球与地图',['经纬网','地图三要素','等高线','地理信息技术','空间定位'],[],['读图','坐标定位','图层叠加']),
   ('地球运动',['地球自转','地球公转','昼夜变化','太阳高度','季节与日期'],[],['时间计算','光照图','晒图分析']),
  ]),
  ('自然地理','必修',[
   ('大气',['大气受热过程','热力环流','气压带风带','天气系统','气候类型'],[],['过程分析','气候判断','天气预报']),
   ('水',['水循环','洋流','陆地水体','水资源'],[],['路径分析','影响判断','图表']),
   ('地貌',['内力作用','外力作用','板块运动','河流地貌','喀斯特地貌','风成地貌'],[],['地貌判读','成因分析','剖面图']),
   ('土壤与植被',['土壤形成','土壤剖面','植被类型','自然带'],[],['图文判读','成因分析','区域比较']),
   ('自然灾害',['灾害类型','成灾机制','防灾减灾','风险评估'],[],['灾害链','措施评价','地图']),
  ]),
  ('人文地理','必修',[
   ('人口',['人口分布','人口迁移','人口容量','人口结构'],[],['图表','因素分析','影响评价']),
   ('城市与乡村',['聚落形态','城市功能分区','城镇化','城乡融合'],[],['空间结构','区位分析','规划']),
   ('产业区位',['农业区位','工业区位','服务业区位','交通区位','产业集聚'],[],['区位评价','布局选择','案例']),
   ('区域发展',['区域特征','区域差异','产业转移','资源开发','可持续发展'],[],['区域比较','问题诊断','方案设计']),
  ]),
  ('区域与资源环境','选择性必修',[
   ('区域联系',['区域合作','流域协同','城市群','一带一路','全球化'],[],['联系图','案例分析','影响评价']),
   ('资源环境与安全',['资源安全','生态安全','环境治理','碳中和','国土空间'],[],['安全评价','措施','图表']),
   ('地理实践',['野外观察','社会调查','地理实验','数据可视化'],[],['调查报告','方案设计','展示']),
  ]),
 ]},
'it': {
 'name':'信息技术', 'stem':'hs_11_it',
 'competencies':['信息意识','计算思维','数字化学习与创新','信息社会责任'],
 'domains':[
  ('数据与信息','必修',[
   ('数据表示',['二进制','字符编码','图像数字化','音频数字化','数据压缩'],[],['编码转换','容量计算','格式判断']),
   ('数据处理',['数据采集','数据清洗','表格分析','数据可视化','数据解释'],[],['数据处理','图表分析','结论表达']),
  ]),
  ('算法与编程','必修',[
   ('算法基础',['问题分解','流程图','顺序结构','选择结构','循环结构','算法评价'],[],['流程图','代码追踪','复杂度']),
   ('程序设计',['变量','数据类型','表达式','函数','列表','调试','测试'],[],['程序阅读','填空','项目']),
  ]),
  ('网络与系统','必修',[
   ('网络基础',['网络协议','IP地址','域名','网络服务','无线网络'],[],['网络诊断','配置','安全分析']),
   ('信息系统',['系统组成','数据库','接口','传感器','系统集成'],[],['系统设计','数据分析','故障排查']),
  ]),
  ('人工智能与安全','选择性必修',[
   ('人工智能',['机器学习','训练与测试','分类','计算机视觉','自然语言处理','模型评价'],[],['模型选择','结果解释','伦理判断']),
   ('信息安全',['身份认证','加密','恶意代码','隐私保护','风险处置'],[],['风险识别','防护方案','案例分析']),
  ]),
 ]},
'general_technology': {
 'name':'通用技术', 'stem':'hs_12_general_technology',
 'competencies':['技术意识','工程思维','创新设计','图样表达','物化能力'],
 'domains':[
  ('技术与设计','必修',[
   ('设计过程',['需求分析','方案构思','方案比较','模型制作','测试优化','成果表达'],[],['设计任务','方案评价','迭代']),
   ('技术图样',['三视图','尺寸标注','剖视图','轴测图','CAD表达'],[],['识图','绘图','尺寸判断']),
  ]),
  ('结构与流程','必修',[
   ('结构',['结构类型','受力分析','稳定性','强度','结构优化'],[],['受力判断','改进设计','试验']),
   ('流程',['环节','时序','流程设计','流程优化'],[],['流程读图','优化','成本评价']),
  ]),
  ('系统与控制','必修',[
   ('系统',['系统要素','系统结构','反馈','系统分析','系统优化'],[],['要素分析','反馈判断','方案设计']),
   ('控制',['开环控制','闭环控制','传感器','控制器','执行器','控制方案'],[],['控制类型','框图','调试']),
  ]),
  ('电子与工程','选择性必修',[
   ('电子技术',['电路基础','逻辑门','传感器电路','单片机入门'],[],['电路分析','逻辑判断','项目']),
   ('工程实践',['材料选择','加工工艺','连接方式','安全规范','项目管理'],[],['制作','测试','报告']),
  ]),
 ]},
'arts': {
 'name':'艺术', 'stem':'hs_13_arts',
 'competencies':['艺术感知','审美判断','创意表达','文化理解'],
 'domains':[
  ('艺术鉴赏','必修',[
   ('视觉艺术',['线条','色彩','构图','空间','材质','风格'],[],['作品分析','比较','策展']),
   ('音乐艺术',['节奏','旋律','和声','曲式','音色','风格'],[],['听辨','结构分析','赏析']),
   ('综合艺术',['戏剧','影视','舞蹈','跨媒介','艺术与科技'],[],['作品解读','创意表达','评论']),
  ]),
  ('艺术实践','选择性必修',[
   ('创作',['主题构思','素材收集','草图','排练或制作','修改','展示'],[],['作品集','过程记录','展示']),
   ('评论与策展',['描述','分析','解释','评价','展览叙事'],[],['艺术评论','策展方案','口头表达']),
  ]),
 ]},
'pe_health': {
 'name':'体育与健康', 'stem':'hs_16_pe_health',
 'competencies':['运动能力','健康行为','体育品德'],
 'domains':[
  ('体能','必修',[
   ('基础体能',['心肺耐力','力量','速度','柔韧','协调','平衡'],[],['体能测试','计划','自我监测']),
   ('运动技能',['田径','球类','体操','水上或冰雪','民族民间体育'],[],['技能评价','比赛','动作分析']),
  ]),
  ('健康管理','必修',[
   ('健康知识',['营养','睡眠','运动损伤','心理健康','急救','传染病预防'],[],['知识判断','情境应对','健康计划']),
   ('运动计划',['目标设定','负荷安排','恢复','风险评估','效果评价'],[],['计划设计','执行记录','调整']),
  ]),
 ]},
}

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE sources(source_id TEXT PRIMARY KEY,name TEXT,url_or_path TEXT,license TEXT,retrieved_at TEXT,usage_note TEXT);
CREATE TABLE subjects(subject_id TEXT PRIMARY KEY,name TEXT,stage TEXT,standard_stem TEXT,competency_json TEXT,source_id TEXT);
CREATE TABLE domains(domain_id TEXT PRIMARY KEY,subject_id TEXT,name TEXT,module_scope TEXT,sort_order INTEGER,source_id TEXT);
CREATE TABLE knowledge_nodes(
 node_id TEXT PRIMARY KEY, subject_id TEXT, domain_id TEXT, parent_id TEXT,
 code TEXT, name TEXT, node_type TEXT, module_scope TEXT, description TEXT,
 official_ref TEXT, source_id TEXT, evidence_type TEXT, confidence REAL,
 difficulty INTEGER, estimated_minutes INTEGER, sort_order INTEGER
);
CREATE TABLE knowledge_edges(
 source_node TEXT, target_node TEXT, relation TEXT, strength REAL,
 evidence_type TEXT, source_id TEXT, note TEXT,
 PRIMARY KEY(source_node,target_node,relation)
);
CREATE TABLE competencies(competency_id TEXT PRIMARY KEY,subject_id TEXT,name TEXT,description TEXT);
CREATE TABLE node_competencies(node_id TEXT,competency_id TEXT,weight REAL,PRIMARY KEY(node_id,competency_id));
CREATE TABLE question_modes(question_mode_id TEXT PRIMARY KEY,subject_id TEXT,name TEXT,description TEXT);
CREATE TABLE unit_question_modes(node_id TEXT,question_mode_id TEXT,importance REAL,PRIMARY KEY(node_id,question_mode_id));
CREATE TABLE assessment_blueprint(node_id TEXT,assessment_type TEXT,item_format TEXT,evidence_required TEXT,PRIMARY KEY(node_id,assessment_type,item_format));
CREATE TABLE learner_mastery_snapshot(
 student_id TEXT, node_id TEXT, mastery REAL, confidence REAL, observed_at TEXT,
 source_ref TEXT, provenance_json TEXT
);
CREATE VIEW v_subject_tree AS
SELECT d.name domain_name,u.node_id unit_id,u.name unit_name,c.node_id concept_id,c.name concept_name,
       c.module_scope,c.difficulty,c.estimated_minutes
FROM domains d JOIN knowledge_nodes u ON u.domain_id=d.domain_id AND u.node_type='unit'
LEFT JOIN knowledge_nodes c ON c.parent_id=u.node_id AND c.node_type='concept';
'''

def slug(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]

def build_subject(key, spec):
    db_path = OUT / f'db_{key}.sqlite'
    if db_path.exists(): db_path.unlink()
    con = sqlite3.connect(db_path); cur = con.cursor(); cur.executescript(SCHEMA)
    source_id = f'src_{spec["stem"]}'
    source_name = f'教育部普通高中课程标准（{spec["name"]}）'
    source_path = str(BASE/'external_data'/'curriculum_standards'/'normalized'/f'{spec["stem"]}.pdf')
    cur.execute('INSERT INTO sources VALUES(?,?,?,?,?,?)',(source_id,source_name,STANDARD_URLS['hs'],'教育部公开课程标准；数据库仅做结构化和事实性索引，不替代原文',NOW,'curated_from_official_standard'))
    subject_id = f'k12:{key}'
    cur.execute('INSERT INTO subjects VALUES(?,?,?,?,?,?)',(subject_id,spec['name'],'高中',spec['stem'],json.dumps(spec['competencies'],ensure_ascii=False),source_id))
    cur.execute('INSERT INTO metadata VALUES(?,?)',('database_role','subject_knowledge_graph'))
    cur.execute('INSERT INTO metadata VALUES(?,?)',('coverage','high_school_curriculum_seed'))
    cur.execute('INSERT INTO metadata VALUES(?,?)',('commercial_readiness','requires_legal_and_editorial_review'))
    cur.execute('INSERT INTO metadata VALUES(?,?)',('created_at',NOW))
    cur.execute('INSERT INTO metadata VALUES(?,?)',('subject_id',subject_id))
    # subject root
    root_id = subject_id
    cur.execute('INSERT INTO knowledge_nodes(node_id,subject_id,domain_id,parent_id,code,name,node_type,module_scope,description,official_ref,source_id,evidence_type,confidence,difficulty,estimated_minutes,sort_order) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(root_id,subject_id,'',None,key,spec['name'],'subject','','高中学科根节点',spec['stem'],source_id,'curated_from_official_standard',1.0,0,0,0))
    for ci, cname in enumerate(spec['competencies'],1):
        cid=f'{subject_id}:competency:{ci:02d}'
        cur.execute('INSERT INTO competencies VALUES(?,?,?,?)',(cid,subject_id,cname,f'{spec["name"]}课程标准核心素养'))
    mode_ids = {}
    for di,(domain_name,module_scope,units) in enumerate(spec['domains'],1):
        did=f'{subject_id}:domain:{di:02d}'
        cur.execute('INSERT INTO domains VALUES(?,?,?,?,?,?)',(did,subject_id,domain_name,module_scope,di,source_id))
        cur.execute('INSERT INTO knowledge_nodes(node_id,subject_id,domain_id,parent_id,code,name,node_type,module_scope,description,official_ref,source_id,evidence_type,confidence,difficulty,estimated_minutes,sort_order) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(did,subject_id,did,root_id,f'{key}.{di:02d}',domain_name,'domain',module_scope,'',f'{spec["stem"]} 课程内容：{domain_name}',source_id,'curated_from_official_standard',0.85,0,0,di))
        cur.execute('INSERT INTO knowledge_edges VALUES(?,?,?,?,?,?,?)',(root_id,did,'contains',1.0,'curated_from_official_standard',source_id,''))
        unit_ids = []
        for ui, unit in enumerate(units, 1):
            if len(unit) == 5:
                unit_name, unit_module, concepts, prior_units, modes = unit
            elif len(unit) == 4:
                unit_name, concepts, prior_units, modes = unit
                unit_module = module_scope
            elif len(unit) == 3:
                unit_name, concepts, modes = unit
                unit_module, prior_units = module_scope, []
            else:
                raise ValueError(f'bad unit definition: {unit!r}')
            uid=f'{subject_id}:unit:{di:02d}{ui:02d}'
            unit_ids.append((uid,unit_name))
            cur.execute('INSERT INTO knowledge_nodes(node_id,subject_id,domain_id,parent_id,code,name,node_type,module_scope,description,official_ref,source_id,evidence_type,confidence,difficulty,estimated_minutes,sort_order) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid,subject_id,did,did,f'{key}.{di:02d}.{ui:02d}',unit_name,'unit',unit_module,'',f'{spec["stem"]} {domain_name} / {unit_name}',source_id,'curated_from_official_standard',0.88,2,45,ui))
            cur.execute('INSERT INTO knowledge_edges VALUES(?,?,?,?,?,?,?)',(did,uid,'contains',1.0,'curated_from_official_standard',source_id,''))
            for mi,mode in enumerate(modes,1):
                mid=f'{subject_id}:question_mode:{slug(mode)}'
                mode_ids[mid]=(mode,spec['name'])
                cur.execute('INSERT OR IGNORE INTO question_modes VALUES(?,?,?,?)',(mid,subject_id,mode,f'{spec["name"]}常见任务：{mode}'))
                cur.execute('INSERT INTO unit_question_modes VALUES(?,?,?)',(uid,mid,round(1.0/max(1,len(modes)),4)))
                cur.execute('INSERT OR IGNORE INTO assessment_blueprint VALUES(?,?,?,?)',(uid,'formative',mode,'真实作答、过程记录或口头解释'))
            prev_concept = None
            for pi,concept in enumerate(concepts,1):
                nid=f'{subject_id}:concept:{di:02d}{ui:02d}{pi:02d}'
                diff = 1 if pi <= max(1,len(concepts)//3) else (2 if pi <= 2*max(1,len(concepts)//3) else 3)
                cur.execute('INSERT INTO knowledge_nodes(node_id,subject_id,domain_id,parent_id,code,name,node_type,module_scope,description,official_ref,source_id,evidence_type,confidence,difficulty,estimated_minutes,sort_order) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(nid,subject_id,did,uid,f'{key}.{di:02d}.{ui:02d}.{pi:02d}',concept,'concept',unit_module,'',f'{spec["stem"]} {domain_name} / {unit_name} / {concept}',source_id,'curated_from_official_standard',0.82,diff,15,pi))
                cur.execute('INSERT INTO knowledge_edges VALUES(?,?,?,?,?,?,?)',(uid,nid,'contains',1.0,'curated_from_official_standard',source_id,''))
                if prev_concept:
                    cur.execute('INSERT INTO knowledge_edges VALUES(?,?,?,?,?,?,?)',(prev_concept,nid,'recommended_before',0.65,'expert_curated',source_id,'同一单元内的概念学习顺序建议，不是硬性先修'))
                prev_concept=nid
                # spread competencies round-robin while preserving all links
                for ci,cname in enumerate(spec['competencies'],1):
                    cid=f'{subject_id}:competency:{ci:02d}'
                    cur.execute('INSERT OR IGNORE INTO node_competencies VALUES(?,?,?)',(nid,cid,round(0.5 + 0.1*((pi+ci)%3),2)))
            for prior in prior_units:
                for puid,puname in unit_ids:
                    if puname == prior:
                        cur.execute('INSERT OR IGNORE INTO knowledge_edges VALUES(?,?,?,?,?,?,?)',(puid,uid,'prerequisite',0.8,'expert_curated',source_id,'跨单元先修建议'))
        # domain sequence
        if di > 1:
            prev_did=f'{subject_id}:domain:{di-1:02d}'
            cur.execute('INSERT OR IGNORE INTO knowledge_edges VALUES(?,?,?,?,?,?,?)',(prev_did,did,'recommended_sequence',0.5,'expert_curated',source_id,'建议学习顺序，不表示硬先修'))
    con.commit()
    counts = {t:cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['domains','knowledge_nodes','knowledge_edges','question_modes','node_competencies']}
    con.close()
    return {'subject_id':subject_id,'name':spec['name'],'db':str(db_path),'counts':counts,'source_standard':str(source_path)}

def build_index(results):
    db_path=OUT/'db_subject_index.sqlite'
    if db_path.exists(): db_path.unlink()
    con=sqlite3.connect(db_path); cur=con.cursor()
    cur.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE subject_catalog(subject_id TEXT PRIMARY KEY,name TEXT,db_file TEXT,node_count INTEGER,unit_count INTEGER,source_standard TEXT,coverage TEXT);
    CREATE TABLE node_registry(node_id TEXT PRIMARY KEY,subject_id TEXT,db_file TEXT,node_type TEXT,name TEXT,parent_id TEXT,module_scope TEXT,official_ref TEXT,source_id TEXT);
    CREATE TABLE standard_documents(doc_id TEXT PRIMARY KEY,title TEXT,path TEXT,pages INTEGER,chars INTEGER,extraction_status TEXT,official_url TEXT);
    CREATE TABLE standard_document_aliases(doc_id TEXT,alias TEXT);
    ''')
    cur.execute('INSERT INTO metadata VALUES(?,?)',('role','cross_subject_index'))
    cur.execute('INSERT INTO metadata VALUES(?,?)',('created_at',NOW))
    for stem,title,pages,chars,status in [
        ('hs_03_math','普通高中数学课程标准（2017年版2020年修订）',188,124884,'text_extracted'),
        ('hs_02_chinese','普通高中语文课程标准（2017年版2020年修订）',66,46081,'text_extracted'),
        ('hs_04_english','普通高中英语课程标准（2017年版2020年修订）',220,161667,'text_extracted'),
        ('hs_08_physics','普通高中物理课程标准（2017年版2020年修订）',98,57898,'text_extracted'),
        ('hs_09_chemistry','普通高中化学课程标准（2017年版2020年修订）',113,67657,'text_extracted'),
        ('hs_10_biology','普通高中生物学课程标准（2017年版2020年修订）',74,62663,'text_extracted'),
        ('hs_05_politics','普通高中思想政治课程标准（2017年版2020年修订）',71,46738,'text_extracted'),
        ('hs_06_history','普通高中历史课程标准（2017年版2020年修订）',91,57283,'text_extracted'),
        ('hs_07_geography','普通高中地理课程标准（2017年版2020年修订）',67,40625,'text_extracted'),
        ('hs_11_it','普通高中信息技术课程标准（2017年版2020年修订）',83,0,'text_available'),
        ('hs_12_general_technology','普通高中通用技术课程标准（2017年版2020年修订）',108,0,'text_available'),
        ('hs_13_arts','普通高中艺术课程标准（2017年版2020年修订）',82,0,'text_available'),
        ('hs_16_pe_health','普通高中体育与健康课程标准（2017年版2020年修订）',122,0,'text_available'),
    ]:
        cur.execute('INSERT INTO standard_documents VALUES(?,?,?,?,?,?,?)',(stem,title,str(BASE/'external_data'/'curriculum_standards'/'normalized'/f'{stem}.pdf'),pages,chars,status,STANDARD_URLS['hs']))
    for result in results:
        subj=result['subject_id']; key=subj.split(':',1)[1]; db=Path(result['db']); s=sqlite3.connect(db); s.row_factory=sqlite3.Row
        cur.execute('INSERT INTO subject_catalog VALUES(?,?,?,?,?,?,?)',(subj,result['name'],db.name,result['counts']['knowledge_nodes'],sum(1 for _ in s.execute("SELECT 1 FROM knowledge_nodes WHERE node_type='unit'")),result['source_standard'],'official_structure_curated'))
        for r in s.execute('SELECT node_id,subject_id,node_type,name,parent_id,module_scope,official_ref,source_id FROM knowledge_nodes'):
            cur.execute('INSERT INTO node_registry VALUES(?,?,?,?,?,?,?,?,?)',(r['node_id'],r['subject_id'],db.name,r['node_type'],r['name'],r['parent_id'],r['module_scope'],r['official_ref'],r['source_id']))
        s.close()
    con.commit(); con.close()
    return db_path

results=[]
for key,spec in SUBJECTS.items():
    results.append(build_subject(key,spec))
index=build_index(results)
manifest={'created_at':NOW,'index':str(index),'subjects':results,'notes':['Official curriculum structure is indexed; wording is expert-curated and not a verbatim reproduction.','Knowledge trees are a product seed and require subject-matter/editorial review before high-stakes use.','Learner scores remain in db_learner_evidence.sqlite and link by node_id.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'subjects':len(results),'nodes':sum(r['counts']['knowledge_nodes'] for r in results),'index':str(index)},ensure_ascii=False,indent=2))
