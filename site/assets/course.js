window.TENDER_COURSE = {
  version: "2.1-world-tree",
  audience: [
    { zh: "第一次使用 Tender 的学习者与家庭", en: "Learners and families using Tender for the first time" },
    { zh: "需要理解产品逻辑的教师、产品与研究团队", en: "Educators, product teams and researchers who need the product logic" },
    { zh: "希望评估证据、隐私与 Agent 协作边界的人", en: "People evaluating evidence, privacy and Agent collaboration boundaries" }
  ],
  outcomes: [
    { zh: "用生命树解释学习、开花、结果与森林", en: "Explain learning, flowering, outcomes and the forest through the life-tree model" },
    { zh: "区分客观世界、有限观测、主观体验与 Agent 支持", en: "Distinguish the objective world, limited observation, subjective experience and Agent support" },
    { zh: "看懂语言证据如何进入 Tender，但不越权决定掌握度", en: "Understand how language evidence enters Tender without determining mastery" },
    { zh: "说明知识森林、固定辅助 Agent 与专家 Agent 的协作边界", en: "Explain the collaboration boundaries of the knowledge forest, fixed helpers and expert Agents" }
  ],
  lessons: [
    {
      id: "life-tree", time: "6 min", level: { zh: "总览", en: "Overview" },
      title: { zh: "生命树与有限世界", en: "The life tree and the limited world" },
      summary: { zh: "生命树是 Tender 的组织语法：世界、观测、体验、行动与结果不是同一层。", en: "The life tree is Tender's organizing grammar: world, observation, experience, action and outcomes are different layers." },
      objectives: [{ zh: "说清生命树的六个部分", en: "Name the six parts of the life tree" }, { zh: "理解为什么生命树不是生物器官断言", en: "Understand why the life tree is not a biological claim" }],
      blocks: [
        { type: "table", title: { zh: "生命树结构", en: "Life-tree structure" }, headers: [{ zh: "部分", en: "Part" }, { zh: "含义", en: "Meaning" }], rows: [
          [{ zh: "种子", en: "Seed" }, { zh: "尚未展开的可能性", en: "Possibilities not yet expressed" }],
          [{ zh: "根系", en: "Roots" }, { zh: "安全、关系、身体与真实反馈", en: "Safety, relationships, body and real feedback" }],
          [{ zh: "生长", en: "Growth" }, { zh: "学习带来的结构、能力与自我模型变化", en: "Changes in structure, capability and self-model through learning" }],
          [{ zh: "开花", en: "Flowering" }, { zh: "表达、提问、教学、协作、试验、发表与应用", en: "Expression, questioning, teaching, collaboration, experimentation, publication and application" }],
          [{ zh: "结果", en: "Outcome" }, { zh: "作品、反馈、关系、机会、失败、边界与新问题", en: "Works, feedback, relationships, opportunities, failure, boundaries and new questions" }],
          [{ zh: "森林", en: "Forest" }, { zh: "全部知识体系与不同学习者共同构成的生态", en: "The ecosystem formed by all knowledge systems and diverse learners" }]
        ] },
        { type: "boundary", body: { zh: "生命树是叙事与建模语法，不是对真实大脑的生理断言，也不是固定人格测试。", en: "The life tree is narrative and modeling grammar, not a biological claim or a fixed personality test." } },
        { type: "quiz", question: { zh: "开花在 Tender 中主要指什么？", en: "What does flowering primarily mean in Tender?" }, options: [{ zh: "考试得高分", en: "Getting a high exam score" }, { zh: "把内部理解转化为向世界表达、提问、教学、协作或应用", en: "Turning internal understanding into expression, questioning, teaching, collaboration or application" }, { zh: "完成一次人格测评", en: "Completing a personality test" }], answer: 1, why: { zh: "开花是内部理解进入外部世界的过程，不是单一分数。", en: "Flowering is the movement from internal understanding into the world, not a single score." } }
      ]
    },
    {
      id: "dual-loops", time: "6 min", level: { zh: "核心理论", en: "Core theory" },
      title: { zh: "两条回路：预测加工与心智化", en: "Two loops: predictive processing and mentalizing" },
      summary: { zh: "人与世界交往主要靠预测加工；人与人交往还需要心智化。两者相连，但不能混同。", en: "Person–world interaction primarily uses predictive processing; person–person interaction also requires mentalizing. They connect without becoming the same thing." },
      objectives: [{ zh: "区分人—世界与人—人问题", en: "Distinguish person–world and person–person problems" }, { zh: "理解行动不只是做题", en: "Understand that action is not limited to exercises" }],
      blocks: [
        { type: "concept", title: { zh: "人—世界回路", en: "Person–world loop" }, body: { zh: "人会预期接下来发生什么，通过行动获得真实反馈，再调整理解或改变行动。", en: "A person anticipates what will happen, acts, receives real feedback, then revises understanding or changes the action." } },
        { type: "concept", title: { zh: "人—人回路", en: "Person–person loop" }, body: { zh: "人还会推断对方的信念、情绪、意图和视角，并通过表达、回应和修复校准关系。", en: "A person also infers another's beliefs, emotions, intentions and perspective, then calibrates the relationship through expression, response and repair." } },
        { type: "list", title: { zh: "行动可以是什么", en: "What action can be" }, items: [{ zh: "打开材料或写一句话", en: "Open a resource or write one sentence" }, { zh: "复述概念或请求提示", en: "Explain a concept or request a hint" }, { zh: "停下来恢复或向教师求助", en: "Pause to recover or ask a teacher for help" }, { zh: "明确退出或暂不行动", en: "Explicitly exit or choose not to act yet" }] },
        { type: "boundary", body: { zh: "关系问题不能交给学科专家处理；Agent 必须先判断问题属于人—世界、人—人还是两者嵌套。", en: "Relational problems must not be routed to a subject expert; Agents must first distinguish person–world, person–person or nested problems." } }
      ]
    },
    {
      id: "world-layer", time: "6 min", level: { zh: "客观层", en: "Objective layer" },
      title: { zh: "世界如何进入系统：DAOQL、有限接触面与 Agent Bridge", en: "How the world enters: DAOQL, limited observation and Agent Bridge" },
      summary: { zh: "Tender 不能直接读取完整世界。世界事件先进入客观层，再经过有限观测与翻译，才形成可更正的主观体验。", en: "Tender cannot read the whole world. World events enter the objective layer, pass through limited observation and translation, and only then become correctable subjective experience." },
      objectives: [{ zh: "理解四层数据边界", en: "Understand the four data boundaries" }, { zh: "说清为什么会话不能直接当事实", en: "Explain why a conversation cannot be treated directly as fact" }],
      blocks: [
        { type: "table", title: { zh: "从世界到体验", en: "From world to experience" }, headers: [{ zh: "层", en: "Layer" }, { zh: "作用", en: "Role" }, { zh: "不能混淆", en: "Do not confuse" }], rows: [
          [{ zh: "世界与黑盒 API", en: "World and black-box APIs" }, { zh: "平台、设备、人物、行动与结果", en: "Platforms, devices, people, actions and outcomes" }, { zh: "系统看不见完整世界", en: "The system cannot see the whole world" }],
          [{ zh: "DAOQL 客观层", en: "DAOQL objective layer" }, { zh: "保存事件、来源、时间、因果、授权与审计", en: "Stores events, provenance, time, causality, authorization and audit" }, { zh: "不是心理档案", en: "Not a psychological dossier" }],
          [{ zh: "有限接触面", en: "Limited observation surface" }, { zh: "人类或设备实际能接触、测量和压缩的证据", en: "Evidence people or devices can actually access, measure and compress" }, { zh: "不是世界本身", en: "Not the world itself" }],
          [{ zh: "Agent Bridge", en: "Agent Bridge" }, { zh: "把客观事件翻译为主观体验节点和可更正假设", en: "Translates objective events into subjective nodes and revisable hypotheses" }, { zh: "不能覆盖原始事件", en: "Must not overwrite source events" }]
        ] },
        { type: "concept", title: { zh: "为什么分层", en: "Why layers" }, body: { zh: "如果系统把用户说的话直接当事实，它会把情绪、猜测、语境和真实结果混在一起。分层让每个判断都能回到来源、时间和证据。", en: "If the system treats what a user says as fact, it mixes emotion, inference, context and outcomes. Layering lets every judgment return to provenance, time and evidence." } },
        { type: "boundary", body: { zh: "DAOQL 记录的是世界性质的事件；生命树记录的是事件如何被体验。两者不能互相替代。", en: "DAOQL records world-like events; the life tree records how events are experienced. Neither replaces the other." } }
      ]
    },
    {
      id: "canopy", time: "6 min", level: { zh: "主观层", en: "Subjective layer" },
      title: { zh: "生命树树冠：体验如何被分区", en: "Life-tree canopy: how experience is organized" },
      summary: { zh: "树冠不是脑区诊断，而是把注意、记忆、语言、内省、情绪和身体状态组织成可探索的体验分区。", en: "The canopy is not a brain-region diagnosis. It organizes attention, memory, language, reflection, emotion and body state into explorable experience regions." },
      objectives: [{ zh: "认识树冠的主要分区", en: "Recognize the main canopy regions" }, { zh: "理解主观体验节点必须保留来源", en: "Understand that subjective nodes must retain provenance" }],
      blocks: [
        { type: "list", title: { zh: "代表性体验分区", en: "Representative experience regions" }, items: [{ zh: "中央检索与工作记忆：当前在处理什么", en: "Central retrieval and working memory: what is being processed now" }, { zh: "长期记忆与语言：知识如何被保存和表达", en: "Long-term memory and language: how knowledge is stored and expressed" }, { zh: "内省与反馈：人如何观察自己的判断", en: "Reflection and feedback: how a person observes their own judgment" }, { zh: "情绪与生活回路：关系、感受与安全感", en: "Emotion and life loops: relationships, feelings and safety" }, { zh: "代谢与治理：睡眠、疲劳、营养与恢复", en: "Metabolism and governance: sleep, fatigue, nutrition and recovery" }] },
        { type: "concept", title: { zh: "metameta 的作用", en: "The role of metameta" }, body: { zh: "metameta 把客观事件拆成带来源的体验节点，同时保留置信度、不确定性和替代解释。节点可以被更正、重算和撤回，但原始事件不变。", en: "metameta decomposes objective events into subjective nodes with provenance, confidence, uncertainty and alternatives. Nodes can be corrected, recomputed or revoked while source events remain unchanged." } },
        { type: "boundary", body: { zh: "树冠标签是产品隐喻和组织语法，不是临床脑区定位，也不能用来诊断疾病或固定人格。", en: "Canopy labels are a product metaphor and organizing grammar, not clinical localization or a diagnosis of disease or fixed personality." } }
      ]
    },
    {
      id: "flowering-results", time: "6 min", level: { zh: "行动层", en: "Action layer" },
      title: { zh: "生长、开花与结果", en: "Growth, flowering and outcomes" },
      summary: { zh: "学习是生长；开花是把理解带进外部世界；结果是不同外界交互产生的分化后果。", en: "Learning is growth; flowering brings understanding into the external world; outcomes are the differentiated consequences of different interactions." },
      objectives: [{ zh: "区分生长、开花与结果", en: "Distinguish growth, flowering and outcomes" }, { zh: "理解痛苦为何不是成长奖章", en: "Understand why pain is not a growth badge" }],
      blocks: [
        { type: "table", title: { zh: "六种开花方式", en: "Six flowering modes" }, headers: [{ zh: "方式", en: "Mode" }, { zh: "可能结果", en: "Possible outcome" }], rows: [
          [{ zh: "自我复述", en: "Self-explanation" }, { zh: "结构化、暴露空白", en: "Structure and exposed gaps" }],
          [{ zh: "同伴讲解", en: "Peer teaching" }, { zh: "保持、迁移、被追问", en: "Retention, transfer and follow-up questions" }],
          [{ zh: "专家提问", en: "Expert questioning" }, { zh: "概念修复、更高精度反馈", en: "Concept repair and higher-precision feedback" }],
          [{ zh: "协作创作", en: "Collaborative creation" }, { zh: "作品、关系、分工与冲突", en: "Works, relationships, coordination and conflict" }],
          [{ zh: "公开发表", en: "Public sharing" }, { zh: "反馈、机会、评价压力", en: "Feedback, opportunity and evaluative pressure" }],
          [{ zh: "真实任务", en: "Real task" }, { zh: "效用、责任、失败与新问题", en: "Utility, responsibility, failure and new questions" }]
        ] },
        { type: "concept", title: { zh: "结果会回流", en: "Outcomes return" }, body: { zh: "结果不是终点。新的反馈、作品、机会、失败和问题会回到系统，改变下一次生长和行动。", en: "Outcomes are not endpoints. New feedback, works, opportunities, failures and questions return to change the next round of growth and action." } },
        { type: "boundary", body: { zh: "痛苦可能是高权重反馈，可能来自边界、错配、责任或伤害。系统必须区分可转化困难与需要保护、退出和求助的伤害。", en: "Pain can be high-weight feedback from boundaries, mismatch, responsibility or harm. The system must distinguish transformable difficulty from harm requiring protection, exit and help." } }
      ]
    },
    {
      id: "language-state", time: "8 min", level: { zh: "证据层", en: "Evidence layer" },
      title: { zh: "语言证据与 Tender 状态", en: "Language evidence and Tender state" },
      summary: { zh: "语言只提供带来源的弱证据。Tender 要把语言与答题、行为、时间、结果、历史和情境一起校准。", en: "Language provides weak, source-grounded evidence. Tender calibrates it together with answers, behavior, time, outcomes, history and context." },
      objectives: [{ zh: "识别语言证据与候选假设", en: "Identify language evidence and candidate hypotheses" }, { zh: "理解语言不能单独改变掌握度", en: "Understand that language cannot change mastery by itself" }],
      blocks: [
        { type: "table", title: { zh: "语言信号与边界", en: "Language signals and boundaries" }, headers: [{ zh: "信号", en: "Signal" }, { zh: "可形成的假设", en: "Allowed hypothesis" }, { zh: "不能推出", en: "Cannot conclude" }], rows: [
          [{ zh: "“我很焦虑”", en: "“I am very anxious”" }, { zh: "情绪负荷可能升高", en: "Emotional load may be elevated" }, { zh: "焦虑障碍", en: "An anxiety disorder" }],
          [{ zh: "“我不想学了”", en: "“I don't want to study”" }, { zh: "行动资源可能下降", en: "Action resources may be reduced" }, { zh: "懒惰或长期动机不足", en: "Laziness or chronic low motivation" }],
          [{ zh: "“老师是不是觉得我不行”", en: "“Does the teacher think I'm incapable?”" }, { zh: "正在推断他人心智", en: "The user is inferring another mind" }, { zh: "别人真实的想法", en: "What others actually think" }],
          [{ zh: "“我明明会，考试又错”", en: "“I knew it, but failed again”" }, { zh: "可能存在校准偏差", en: "A calibration gap may exist" }, { zh: "确定的知识掌握度", en: "Confirmed mastery" }]
        ] },
        { type: "concept", title: { zh: "三个组件", en: "Three components" }, body: { zh: "语言模型负责抽取和表达；Tender 负责多源证据融合；确定性规则负责高风险路由、来源校验和禁止结论。用户和人工保留纠正与保护权。", en: "The language model extracts and communicates; Tender fuses evidence; deterministic rules handle risk routing, provenance and forbidden conclusions. Users and humans retain correction and protection rights." } },
        { type: "boundary", body: { zh: "掌握度来自作答和任务结果，不来自“我觉得我会”。语言只用于理解当前表达、选择最小支持和提出下一次验证问题。", en: "Mastery comes from answers and task outcomes, not from “I think I know it.” Language is used to understand expression, choose minimal support and propose the next verification." } }
      ]
    },
    {
      id: "forest", time: "5 min", level: { zh: "森林", en: "Forest" },
      title: { zh: "知识森林：知识体系如何进入环境", en: "Knowledge forest: how knowledge systems become an environment" },
      summary: { zh: "森林由学科树、专业林、课程灌层、职业天际和生态廊道共同构成。", en: "The forest combines subject trees, discipline groves, a course understory, a career horizon and ecological corridors." },
      objectives: [{ zh: "读懂五层知识生态", en: "Read the five knowledge layers" }, { zh: "说出当前课程覆盖缺口", en: "State the current course-seed gap" }],
      blocks: [
        { type: "table", title: { zh: "森林五层", en: "Five forest layers" }, headers: [{ zh: "层", en: "Layer" }, { zh: "规模", en: "Scale" }, { zh: "作用", en: "Role" }], rows: [
          [{ zh: "知识树层", en: "Subject-tree layer" }, { zh: "13 学科、1,075 节点、1,787 关系", en: "13 subjects, 1,075 nodes, 1,787 relationships" }, { zh: "领域—单元—概念钻取", en: "Domain–unit–concept drill-down" }],
          [{ zh: "专业林层", en: "Major-grove layer" }, { zh: "13 门类、93 专业类、875 专业", en: "13 categories, 93 classes, 875 majors" }, { zh: "专业路径探索", en: "Major-path exploration" }],
          [{ zh: "课程灌层", en: "Course understory" }, { zh: "319 课程；26 个专业有课程种子", en: "319 courses; seeds for 26 majors" }, { zh: "显示真实覆盖和缺口", en: "Show actual coverage and gaps" }],
          [{ zh: "职业天际层", en: "Career horizon" }, { zh: "1,016 职业；6 个 RIASEC 维度", en: "1,016 occupations; 6 RIASEC dimensions" }, { zh: "方向探索", en: "Direction exploration" }],
          [{ zh: "生态廊道", en: "Ecological corridors" }, { zh: "44 组学科—专业桥接", en: "44 subject–major bridges" }, { zh: "显示启发式连接", en: "Show heuristic links" }]
        ] },
        { type: "boundary", body: { zh: "课程种子不是官方培养方案，桥接不是官方选科要求，875 个专业也不等于 875 套完整课程。", en: "Course seeds are not official curricula, bridges are not official selection requirements, and 875 majors are not 875 complete course maps." } }
      ]
    },
    {
      id: "agents-governance", time: "5 min", level: { zh: "支持层", en: "Support layer" },
      title: { zh: "Agent、治理与路线图", en: "Agents, governance and roadmap" },
      summary: { zh: "Agent 是生命树周围的支撑者，不是系统的主人。多 Agent 协作必须受授权、预算、安全和审计约束。", en: "Agents support the life tree; they do not own it. Multi-Agent collaboration must remain under authorization, budget, safety and audit constraints." },
      objectives: [{ zh: "区分固定辅助与专家 Agent", en: "Distinguish fixed helpers from expert Agents" }, { zh: "说明三阶段治理", en: "Explain the three governance phases" }],
      blocks: [
        { type: "table", title: { zh: "Agent 分层", en: "Agent layers" }, headers: [{ zh: "层", en: "Layer" }, { zh: "职责", en: "Responsibility" }], rows: [
          [{ zh: "固定辅助 Agent", en: "Fixed helper Agents" }, { zh: "心智化陪伴、情绪调节、反思、家庭桥接、安全", en: "Mentalization companion, regulation, reflection, family bridge and safety" }],
          [{ zh: "专业顾问 Agent", en: "Professional advisors" }, { zh: "健康、营养、神经认知、心理、学习科学、生涯与安全", en: "Health, nutrition, neurocognition, psychology, learning science, career and safety" }],
          [{ zh: "天使 Agent", en: "Angel Agents" }, { zh: "围绕树冠提供专业视角，不替用户决定方向", en: "Provide expertise around the canopy without deciding the user's direction" }],
          [{ zh: "专家 Agent 市场", en: "Expert-Agent marketplace" }, { zh: "生成、上架、购买和出售专业能力，但必须授权和审计", en: "Generate, list, buy and sell expertise under authorization and audit" }]
        ] },
        { type: "list", title: { zh: "三阶段治理", en: "Three governance phases" }, items: [{ zh: "当前：链下专家议会", en: "Current: off-chain expert council" }, { zh: "联盟阶段：许可 BFT 与外部验证", en: "Federation: permissioned BFT and external validation" }, { zh: "全民自治：少数保护、申诉与紧急权力日落", en: "Public autonomy: minority protection, appeal and sunset of emergency powers" }] },
        { type: "boundary", body: { zh: "原始对话、健康信号与未成年人身份不上链。多 Agent 自动执行默认关闭，高风险问题转人工。", en: "Raw conversations, health signals and minor identities do not go on-chain. Automatic multi-Agent execution is off by default, and high-risk problems escalate to humans." } }
      ]
    },
    {
      id: "world-tree-interface", time: "10 min", level: { zh: "世界树", en: "World tree" },
      title: { zh: "世界树、八功能入口与共享枝", en: "World tree, eight-function entry and shared branches" },
      summary: { zh: "Tender 不给用户贴 MBTI 标签。系统统一评估八种功能态度，在后台判断用户更容易先进入客观世界还是主观世界，再用动态大五理解近期人际资源。", en: "Tender does not label users with MBTI. A common assessment estimates eight function-attitudes, decides internally whether objective or subjective entry is more natural, and uses a dynamic Big Five pulse to understand recent interpersonal resources." },
      objectives: [{ zh: "区分客观入口、主观入口和桥接入口", en: "Distinguish objective, subjective and bridge entry" }, { zh: "理解世界树、共享枝与私人边界", en: "Understand the world tree, shared branches and private boundaries" }],
      blocks: [
        { type: "concept", title: { zh: "两种态度 × 四种功能", en: "Two attitudes by four functions" }, body: { zh: "八种入口来自两种态度与四种功能的交叉：外倾感觉、外倾直觉、外倾思维、外倾情感，以及对应的内倾形式。它们描述当前更自然的进入方式，不是固定类型或能力排名。", en: "The eight entry modes cross two attitudes with four functions: extraverted and introverted versions of sensation, intuition, thinking and feeling. They describe current entry preferences, not fixed types or ability rankings." } },
        { type: "table", title: { zh: "内部矩阵", en: "Internal matrix" }, headers: [{ zh: "态度", en: "Attitude" }, { zh: "感觉", en: "Sensation" }, { zh: "直觉", en: "Intuition" }, { zh: "思维", en: "Thinking" }, { zh: "情感", en: "Feeling" }], rows: [
          [{ zh: "外倾：更直接面向客观世界", en: "Extraverted: more directly toward the objective world" }, { zh: "现实观察", en: "Reality observation" }, { zh: "可能性探索", en: "Possibility exploration" }, { zh: "结果执行", en: "Outcome execution" }, { zh: "关系协调", en: "Relational coordination" }],
          [{ zh: "内倾：更直接整理主观世界", en: "Introverted: more directly organizes the subjective world" }, { zh: "经验对照", en: "Experience comparison" }, { zh: "长期整合", en: "Long-range integration" }, { zh: "结构建模", en: "Structural modeling" }, { zh: "价值边界", en: "Value boundaries" }]
        ] },
        { type: "list", title: { zh: "用户实际看到什么", en: "What the user actually sees" }, items: [{ zh: "更自然地先进入客观世界、主观世界，或从真实卡点进入", en: "A more natural objective, subjective or real-problem entry" }, { zh: "第一个现实动作和需要防止的偏差", en: "A first real action and the bias to guard against" }, { zh: "按当前问题调整后的支持方式", en: "Support adjusted to the current problem" }, { zh: "不显示 MBTI 字母、功能代码或固定人格标签", en: "No MBTI letters, function codes or fixed personality labels" }] },
        { type: "concept", title: { zh: "大五脉搏服务人与人", en: "The Big Five pulse serves person-to-person interaction" }, body: { zh: "大五不是第二个世界入口。它记录近期开放、尽责、外向、宜人和情绪稳定的变化、波动与恢复，用于沟通频率、冲突、承诺、协作和社交电量。变化不等于人格永久改变。", en: "The Big Five is not a second world-entry model. It tracks recent change, variability and recovery in openness, conscientiousness, extraversion, agreeableness and emotional stability for communication pacing, conflict, commitments, collaboration and social energy. Change is not permanent personality change." } },
        { type: "table", title: { zh: "两棵世界树如何合作", en: "How two world trees cooperate" }, headers: [{ zh: "层", en: "Layer" }, { zh: "可以比较什么", en: "What can be compared" }, { zh: "边界", en: "Boundary" }], rows: [
          [{ zh: "客观世界", en: "Objective world" }, { zh: "共同事实、目标、任务、时间与结果", en: "Shared facts, goals, tasks, time and outcomes" }, { zh: "不读取对方完整数据库", en: "Do not read the other person's full database" }],
          [{ zh: "主观世界", en: "Subjective world" }, { zh: "哪些是事实、哪些是解释、哪些仍未知", en: "What is fact, interpretation or still unknown" }, { zh: "不把推测当对方意图", en: "Do not treat inference as the other's intention" }],
          [{ zh: "共享枝", en: "Shared branch" }, { zh: "共同承诺、沟通规则与共同结果", en: "Shared commitments, communication rules and outcomes" }, { zh: "私人生命树不默认共享", en: "Private life trees are not shared by default" }]
        ] },
        { type: "boundary", body: { zh: "黄金比是设计假设，不是科学定律。它可以组织外部输入与内部整合、探索与巩固、共享与私密、支持与自主的视觉和交互比例，但不能做人格评分、关系匹配或效果承诺。", en: "The golden ratio is a design hypothesis, not a scientific law. It may guide visual and interaction proportions among external input and internal integration, exploration and consolidation, shared and private, support and autonomy. It must not become a personality score, relationship match or efficacy claim." } }
      ]
    },    {
      id: "delivery-model", time: "6 min", level: { zh: "交付", en: "Delivery" },
      title: { zh: "一套核心，三种交付", en: "One core, three delivery surfaces" },
      summary: { zh: "Tender 不是 B 端和 C 端各做一套产品。它用同一套客观事件、语言证据、Tender 状态、知识森林、Agent 和治理核心，分别支持 B 端完整系统、B 端嵌入模块与 C 端生活界面。", en: "Tender does not build two separate products for B2B and C-end. One core of objective events, language evidence, Tender state, knowledge forest, Agents and governance supports a full B2B suite, an embedded B2B module and a C-end life interface." },
      objectives: [{ zh: "区分三种交付方式", en: "Distinguish the three delivery modes" }, { zh: "理解共享核心与数据边界", en: "Understand the shared core and data boundaries" }],
      blocks: [
        { type: "table", title: { zh: "三种交付界面", en: "Three delivery surfaces" }, headers: [{ zh: "方式", en: "Mode" }, { zh: "谁提供界面", en: "Who provides the interface" }, { zh: "核心价值", en: "Core value" }], rows: [
          [{ zh: "B 端完整系统", en: "Full B2B suite" }, { zh: "Tender 提供完整教育系统", en: "Tender provides the full education system" }, { zh: "招生、排课、考勤、教学、班主任、校长、财务与学情" , en: "Enrollment, scheduling, attendance, teaching, head teacher, principal, finance and learning analytics" }],
          [{ zh: "B 端嵌入模块", en: "Embedded B2B module" }, { zh: "保留合作方原有教育系统界面，Tender 嵌入能力", en: "The partner keeps its education-system interface and embeds Tender capabilities" }, { zh: "通过 API、SDK、事件契约、单点登录与权限接入语言证据、状态、Agent 和知识森林", en: "Use APIs, SDKs, event contracts, SSO and permissions to add language evidence, state, Agents and the knowledge forest" }],
          [{ zh: "C 端自有界面", en: "C-end owned interface" }, { zh: "Tender 提供自己的移动端、网页与桌面环境层", en: "Tender provides its own mobile, web and desktop ambient interface" }, { zh: "融入用户生活：弹幕、对话条、学习护照、长期时间线与个人 Agent", en: "Integrates into daily life through ambient prompts, a conversation bar, learning passport, long-term timeline and personal Agents" }]
        ] },
        { type: "concept", title: { zh: "共享核心", en: "Shared core" }, body: { zh: "DAOQL、语言证据、Tender 状态、生命树、知识森林、Agent 运行时、授权与审计是同一套核心。B 端和 C 端改变的是界面、客户、权限和数据范围，而不是底层模型。", en: "DAOQL, language evidence, Tender state, the life tree, knowledge forest, Agent runtime, authorization and audit are one shared core. B2B and C-end change the interface, customer, permissions and data scope, not the underlying model." } },
        { type: "list", title: { zh: "数据边界", en: "Data boundaries" }, items: [{ zh: "机构租户数据与个人数据分账", en: "Institutional tenant data and personal data remain separately accounted" }, { zh: "只有经用户授权，机构学习记录才进入个人学习护照", en: "Institutional learning records enter the personal passport only with user authorization" }, { zh: "嵌入式模块不得复制合作方全部数据库", en: "Embedded modules must not copy the partner's entire database" }, { zh: "C 端界面归属于用户，可导出、暂停和删除", en: "The C-end interface belongs to the user and supports export, pause and deletion" }] },
        { type: "boundary", body: { zh: "B 端购买系统不等于拥有学生全部心智数据。C 端免费或付费也不意味着机构可以读取个人记录。购买关系、监护关系和授权关系必须分别计算。", en: "A B2B purchase does not grant ownership of all learner mental data. A C-end subscription does not give institutions access to personal records. Commercial, guardian and consent relationships must be evaluated separately." } }
      ]
    }
  ]
};
