# Tender 学科知识数据库总览

更新时间：2026-10-25

## 1. 这套数据库解决什么问题

它解决三个连续问题：

1. **孩子可能喜欢什么**：用课程知识、真实行为、RIASEC 兴趣和项目证据，避免只凭一句“我喜欢某个专业”就下结论。
2. **目标专业需要什么**：从 875 个本科专业、93 个专业类、13 个门类，追到课程和高中先修知识。
3. **现在差在哪里、先练什么**：把某一门学科拆到单元和概念，优先找出低掌握度、且对目标专业重要的知识节点，再用最小练习验证。

它不是“替学生填志愿”的答案库。正式志愿和选科仍必须核对各省考试院、高校招生章程和当年选科要求。

## 2. 数据库分层

```text
official sources
  ├─ 普通高中课程标准（2017年版2020年修订）
  ├─ 义务教育课程标准（2022年版）
  ├─ 本科专业目录（2026年）
  ├─ 研究生教育学科专业目录（2022年）
  └─ O*NET 30.1（CC BY 4.0）
        ↓
subject databases
  ├─ 13 个高中学科库，按“领域 → 单元 → 概念”组织
  ├─ 13 个本科门类库，按“门类 → 专业类 → 专业”组织
  └─ 代表专业课程种子库
        ↓
crosswalks
  ├─ 高中学科 ↔ 本科专业
  ├─ 本科专业 ↔ 核心课程
  └─ 专业 ↔ 职业兴趣（RIASEC）
        ↓
learner evidence
  ├─ 兴趣行为证据
  ├─ 分数与知识点掌握证据
  ├─ 目标专业
  └─ 推荐与复盘记录
```

## 3. 核心目录

```text
D:\Tender\knowledge_data\
  db_catalog.sqlite                 # 所有数据库、来源、边界说明的目录
  db_manifest.json                  # 数据库清单与文件指纹
  db_k12.sqlite                     # 13 个高中学科合并后的查询库
  db_university.sqlite              # 875 个本科专业及专业类、研究生目录
  db_university_courses.sqlite      # 26 个代表专业、319 门课程名及推荐顺序
  db_career.sqlite                  # 1016 个职业与 RIASEC 兴趣
  db_learner_evidence.sqlite        # 学习者证据；默认不含真实学生数据
  db_asset_inventory.sqlite         # D:\言文 的 6409 个文件清单
  subject_databases\
    db_chinese.sqlite
    db_math.sqlite
    db_english.sqlite
    db_physics.sqlite
    db_chemistry.sqlite
    db_biology.sqlite
    db_politics.sqlite
    db_history.sqlite
    db_geography.sqlite
    db_it.sqlite
    db_general_technology.sqlite
    db_arts.sqlite
    db_pe_health.sqlite
    db_subject_index.sqlite
    university\
      db_ug_01_philosophy.sqlite
      db_ug_02_economics.sqlite
      db_ug_03_law.sqlite
      db_ug_04_education.sqlite
      db_ug_05_literature.sqlite
      db_ug_06_history.sqlite
      db_ug_07_science.sqlite
      db_ug_08_engineering.sqlite
      db_ug_09_agriculture.sqlite
      db_ug_10_medicine.sqlite
      db_ug_12_management.sqlite
      db_ug_13_arts.sqlite
      db_ug_14_interdisciplinary.sqlite
      db_university_index.sqlite
```

## 4. 高中学科库的结构

每个学科库都包含：

- `subjects`：学科名称、阶段、课程标准来源。
- `domains`：课程领域，例如数学的“函数”“几何与代数”“概率与统计”。
- `knowledge_nodes`：领域、单元、概念三级节点。
- `knowledge_edges`：包含、推荐学习顺序、先修建议。
- `competencies`：学科核心素养。
- `question_modes`：该知识常见的考查或表现方式。
- `unit_question_modes`：单元与任务类型的连接。
- `assessment_blueprint`：建议如何取得证据，不是自动判分规则。
- `learner_mastery_snapshot`：学生掌握度快照接口，内容默认为空。

当前合并库规模：

- 13 个高中学科；
- 1,075 个知识节点；
- 1,787 条知识关系；
- 447 种任务/题型描述；
- 3,775 条知识点—核心素养连接。

## 5. 本科专业库的结构

每个门类库都包含：

- `discipline_categories`：学科门类。
- `major_classes`：专业类。
- `majors`：本科专业及官方专业代码。
- `graduate_disciplines`：对应研究生一级学科或专业学位类别。
- `major_subject_requirements`：门类层面的高中学科重要性启发式画像。
- `major_courses`：代表专业课程名与推荐顺序。
- `course_edges`：课程之间的推荐顺序。
- `major_highschool_bridges`：更具体的高中学科相关性。
- `major_competencies`：专业能力标签。
- `program_coverage`：哪些专业已经有课程种子，哪些还缺。

当前规模：

- 875 个本科专业；
- 93 个专业类；
- 13 个学科门类；
- 181 个研究生一级学科/专业学位类别；
- 26 个代表专业已有课程级种子；
- 319 门课程名；
- 293 条课程顺序关系；
- 90 条高中学科—专业桥接；
- 78 条专业能力标签。

“26 个代表专业”是课程层首发覆盖，不是全部 875 个专业都已经有完整培养方案。后续应逐校导入真实培养方案，而不是用相似专业名称强行补齐。

## 6. 数据来源与许可证边界

### 已进入主库

- 教育部《普通高等学校本科专业目录（2026年）》：专业代码、专业类和门类事实。
- 教育部《研究生教育学科专业目录（2022年）》：研究生学科和专业学位类别。
- 教育部普通高中课程标准（2017年版2020年修订）：学科知识树的课程结构依据。
- 教育部义务教育课程标准（2022年版）：原始文件已保存，义务教育树仍待继续扩展。
- O*NET 30.1：职业、RIASEC 兴趣和关键词，CC BY 4.0，需保留署名。
- 用户自有资料：只用于标题、流程和内部索引，不直接作为可再分发的商业知识内容。

### 未并入商业主库

- `mmlong818/k12-knowledge-points`：未发现明确许可证。
- `haolpku/K12-KGraph`：CC BY-NC-SA 4.0，禁止商业使用。
- `THU-KEG/EDUKG`：未发现明确许可证。
- `THU-KEG/MOOCCubeX`：GPL-3.0，不适合直接并入闭源商业主库。

## 7. 怎么查

### 查看高中某学科的知识树

```sql
SELECT domain_name, unit_name, concept_name, module_scope
FROM v_subject_tree
WHERE concept_name IS NOT NULL
LIMIT 50;
```

### 查看某专业有哪些课程种子

```sql
SELECT sequence_no, course_name, course_type, knowledge_domain
FROM v_major_course_sequence
WHERE major_code = '080901'
ORDER BY sequence_no;
```

### 查看某专业更依赖哪些高中学科

```sql
SELECT subject_id, weight, evidence_type, note
FROM major_highschool_bridges
WHERE major_code = '080901'
ORDER BY weight DESC;
```

### 查看某学生与目标专业的差距

```powershell
& 'C:\Users\Dell\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  'D:\Tender\knowledge_data\interest_engine.py' gap `
  --student STUDENT_ID --major 080901
```

## 8. 知识森林的数据映射

产品中的“森林”不是装饰图，也不是只展示专业名称。它由现有数据库直接生成：

| 森林层 | 数据库来源 | 当前规模 | 视觉表达 |
|---|---|---:|---|
| 知识树层 | `db_k12.sqlite`、`subject_databases/` | 13 学科、1,075 节点、1,787 关系 | 每片叶对应一个知识节点，点击进入完整领域—单元—概念树 |
| 专业林层 | `db_university.sqlite` | 13 门类、93 专业类、875 专业、181 研究生学科 | 每个专业点对应一个本科专业，点击按门类检索 |
| 课程灌层 | `db_university_courses.sqlite` | 319 课程、293 课程关系、26 个有课程种子的专业 | 底部灌层光点；26/875 覆盖率明确显示 |
| 职业天际层 | `db_career.sqlite` | 1,016 职业、6 个 RIASEC 维度 | 天际光点，不把职业当作确定答案 |
| 生态廊道 | `major_subject_requirements` | 44 组高中学科—专业桥接 | 连线粗细对应平均权重，仅表示启发式证据 |

接口：`GET /knowledge/forest`  
页面：`GET /ui/knowledge.html`

森林中的视觉元素与研究构念“森林”不是同一层含义。前者是知识生态的数据视图；后者仍由认知多样性、心智化、贡献熵、重组历史与同质化等变量测量。不能因为页面有 875 个专业点，就推断某个学习者已有相应能力。

## 9. 最重要的边界

1. **兴趣不是一次点击**：高置信兴趣证据至少应包含主动选择、持续投入、遇难后回来、主动提问或作品产出。
2. **专业课程不是官方选科要求**：课程种子是探索路径，不能替代高校招生要求。
3. **高中知识树不是教材逐字目录**：它是对官方课程标准的专家结构化索引，仍需教研人员校准版本与地区差异。
4. **没有写入任何真实学生数据**：当前学习者证据库为空。写入真实数据前，需要授权、脱敏和访问控制。
5. **不宣称替代考试**：它减少高频重复考试，保留最少必要真实验证。

## 10. 下一步最值得补的三件事

1. **接入官方选科要求**：按年份、省份、高校、专业保存原文、来源 URL、核验状态。
2. **逐校导入培养方案**：先把 26 个代表专业扩到 100 个高频专业，记录课程学分、先修关系和实践环节。
3. **建立知识节点级题库接口**：让每个节点都能绑定真实作答、错因、反馈和复测结果，而不是只停留在目录层。

## 11. Agent 运行时知识上下文

Agent 不再只读取对话和知识树名称。每次用户请求会通过：

```text
agent_layer/app/knowledge_context.py
  build_knowledge_context()
```

自动完成：

1. 从用户当前消息与最近 `task_hint` 识别学科；
2. 在 1,075 个知识节点中匹配概念、单元或学科；
3. 找回从学科到领域、单元、概念的路径；
4. 读取先修关系、推荐后续和常见任务；
5. 读取节点对应核心素养；
6. 根据 DAOQL 中带 `node_id` 的作答记录计算节点级掌握度；
7. 将有界知识上下文注入 Tender Agent Prompt。

新增可查询接口：

```text
GET /tender/context/{student_id}?message=这道函数题不会
```

返回中的 `knowledge` 字段包括：

```text
subject_name
match_method
matches
  node_id
  name
  path
  prerequisites
  next_nodes
  question_modes
  competencies
  learner_mastery
```

边界：

- 没有匹配到具体节点时，不虚构知识点；
- 只有学科但无具体概念时，退回到单元级建议；
- 知识节点用于组织下一步学习，不替代正式课程方案、选科要求和考试政策；
- 节点掌握度只有在作答事件包含 `node_id` 或 `knowledge_node_id` 时才计算。
