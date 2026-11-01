window.TENDER_COURSE = {
  version: "3.1-three-loops",
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
      id: "three-loops", time: "8 min", level: { zh: "价值回路", en: "Value loops" },
      title: { zh: "自我、世界、关系与群体", en: "Self, world, relationships and groups" },
      summary: { zh: "Tender 从理解自己开始，把理解转化为世界中的行动，再把人与人的理解转化为可授权、可协商、可撤回的协作。", en: "Tender starts with self-understanding, turns it into action in the world, and turns understanding between people into authorized, negotiable and revocable collaboration." },
      objectives: [{ zh: "用四条回路解释 Tender 的价值", en: "Explain Tender's value through four loops" }, { zh: "把观察、推断和需要分开", en: "Separate observation, inference and need" }],
      blocks: [
        { type: "table", title: { zh: "四条价值回路", en: "Four value loops" }, headers: [{ zh: "回路", en: "Loop" }, { zh: "核心问题", en: "Core question" }], rows: [
          [{ zh: "自我", en: "Self" }, { zh: "我现在的注意、负荷、动机、情绪和行动阻力是什么？", en: "What is happening in my attention, load, motivation, emotion and action friction?" }],
          [{ zh: "世界", en: "World" }, { zh: "下一步做什么？真实结果是否支持原来的判断？", en: "What is the next action, and does the real outcome support my judgment?" }],
          [{ zh: "关系", en: "Relationship" }, { zh: "我观察到了什么？我推断了什么？我真正的需要是什么？", en: "What did I observe, what did I infer, and what do I need?" }],
          [{ zh: "群体", en: "Group" }, { zh: "开放问题、承诺和决定是否清楚？", en: "Are open questions, commitments and decisions clear?" }]
        ] },
        { type: "concept", title: { zh: "关系中的一句改写", en: "One relational rewrite" }, body: { zh: "把“他就是不在乎我”改写成：“我观察到他没有回复；我的解释是他不在乎；我的需要是确认；我准备问一个具体问题。”", en: "Change “He does not care about me” into “I observed no reply; my interpretation is that he does not care; my need is clarification; I will ask a specific question.”" } },
        { type: "list", title: { zh: "每层各自要看的结果", en: "Outcomes by layer" }, items: [{ zh: "自我：能否更正、是否减轻负担", en: "Self: correction and support burden" }, { zh: "世界：行动恢复、预测误差、迁移", en: "World: action recovery, prediction error and transfer" }, { zh: "关系：误归因、澄清和修复", en: "Relationship: misattribution, clarification and repair" }, { zh: "群体：承诺闭合、决策完成、开放问题", en: "Group: commitments, decisions and open questions" }] },
        { type: "boundary", body: { zh: "Tender 不声称知道他人的真实心智。他者模型是观察者的假设；共享枝需要参与者确认；Agent 支持选择，方向和后果仍由人承担。", en: "Tender does not claim access to another person's true mind. A peer model is the observer's hypothesis; shared branches require participant confirmation; Agents support choices while people retain direction and consequence." } },
        { type: "quiz", question: { zh: "“他没有回复，所以不在乎我”缺少哪一步？", en: "What step is missing from “He did not reply, so he does not care”?" }, options: [{ zh: "把推断当成事实", en: "Treating an inference as fact" }, { zh: "区分观察、推断和需要，并请求确认", en: "Separating observation, inference and need, then asking for clarification" }, { zh: "直接让群模型判断对方人格", en: "Asking the group model to judge his personality" }], answer: 1, why: { zh: "没有回复是观察，不在乎是推断，确认信息才是关系回路中的下一步。", en: "No reply is an observation, not caring is an inference, and clarification is the next relational step." } }
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
      id: "dynamic-golden-bias", time: "10 min", level: { zh: "节律调节", en: "Rhythm regulation" },
      title: { zh: "动态黄金比偏置律", en: "Dynamic golden-bias regulation" },
      summary: { zh: "黄金比不是每日 KPI，而是一条带滞回的弹性带：学习与创造中较小的一极长期不低于约 38.2%，较大的一极长期不高于约 61.8%。", en: "The golden ratio is not a daily KPI. It is a hysteresis-aware elastic band: the smaller pole should not remain below about 38.2%, and the larger pole should not remain above about 61.8%." },
      objectives: [{ zh: "区分投入比、新异比与创造后校准比", en: "Distinguish input ratio, novelty ratio and post-creation calibration" }, { zh: "理解实验结果中的收益与权衡", en: "Understand the benefits and tradeoffs in the experiment" }],
      blocks: [
        { type: "concept", title: { zh: "学习与创造分别做什么", en: "What learning and creation do" }, body: { zh: "学习偏测量、输入、更新、修剪和客观校准；创造偏制备、分叉、表达和选择新的测量基。两者不是被动与主动的二分，任何一极长期缺席都会让世界树失衡。", en: "Learning leans toward measurement, input, updating, pruning and objective calibration. Creation leans toward preparation, branching, expression and choosing new measurement bases. Neither is simply passive or active, and a long absence of either pole destabilizes the world tree." } },
        { type: "table", title: { zh: "三类指标", en: "Three regulators" }, headers: [{ zh: "指标", en: "Metric" }, { zh: "看什么", en: "What it observes" }, { zh: "防止什么", en: "What it prevents" }], rows: [
          [{ zh: "投入比", en: "Input ratio" }, { zh: "学习与创造的滚动时间/事件权重", en: "Rolling time and event weight across learning and creation" }, { zh: "长期只吸收或只输出", en: "Prolonged absorption or output without the other pole" }],
          [{ zh: "新异比", en: "Novelty ratio" }, { zh: "输出中真正产生新分支的比例", en: "The share of output that creates a genuinely new branch" }, { zh: "重复、空转或无根发散", en: "Repetition, stagnation or rootless divergence" }],
          [{ zh: "创造后校准比", en: "Post-creation calibration" }, { zh: "输出后 72 小时内是否获得反馈、复测或结果校验", en: "Whether feedback, retest or outcome validation follows within 72 hours" }, { zh: "脱离现实的自繁殖", en: "Self-reproduction detached from reality" }]
        ] },
        { type: "list", title: { zh: "7 天与 28 天", en: "Seven days and twenty-eight days" }, items: [{ zh: "7 天窗口用于温和提示短期偏移", en: "The seven-day window supports gentle short-term prompts" }, { zh: "28 天窗口用于判断学习期或创造期", en: "The twenty-eight-day window estimates a learning or creation phase" }, { zh: "证据不足时不判断比例", en: "When evidence is insufficient, no ratio conclusion is produced" }, { zh: "连续偏离才提示，回到带内后解除", en: "Prompts require sustained deviation and clear when the band is regained" }] },
        { type: "table", title: { zh: "合成实验结果", en: "Synthetic experiment" }, headers: [{ zh: "规则", en: "Rule" }, { zh: "行动恢复", en: "Recovery" }, { zh: "带内时间", en: "In-band" }, { zh: "提示负担", en: "Burden" }], rows: [
          [{ zh: "不调节", en: "No regulation" }, { zh: "0.884", en: "0.884" }, { zh: "0.474", en: "0.474" }, { zh: "0", en: "0" }],
          [{ zh: "固定 50:50", en: "Fixed 50:50" }, { zh: "0.945", en: "0.945" }, { zh: "0.775", en: "0.775" }, { zh: "63.7", en: "63.7" }],
          [{ zh: "固定阈值", en: "Fixed band" }, { zh: "0.927", en: "0.927" }, { zh: "0.476", en: "0.476" }, { zh: "6.3", en: "6.3" }],
          [{ zh: "动态黄金比", en: "Dynamic golden" }, { zh: "0.947", en: "0.947" }, { zh: "0.572", en: "0.572" }, { zh: "33.1", en: "33.1" }]
        ] },
        { type: "concept", title: { zh: "结果怎么看", en: "How to read the result" }, body: { zh: "动态规则相对不调节提高恢复与带内时间；相对固定 50:50 用更少提示保持相近恢复；但严格带内时间低于固定 50:50，创造后校准也不优于固定阈值。这是负担、平衡和校准之间的权衡，不是全面胜出。", en: "The dynamic rule improves recovery and in-band time versus no regulation. It preserves recovery with fewer prompts than fixed 50:50. It is less strictly in-band than fixed 50:50 and does not outperform the fixed band on calibration. This is a tradeoff among burden, balance and calibration, not universal superiority." } },
        { type: "boundary", body: { zh: "实验是每臂 1,000 名合成学习者、84 天的机制仿真，不是真人教育或临床因果证据。黄金比不能变成人格评分、关系匹配、绩效排名或每日考核。", en: "The experiment is an 84-day mechanism simulation with 1,000 synthetic learners per arm. It is not human educational or clinical causal evidence. The golden ratio must not become a personality score, relationship match, performance rank or daily KPI." } }
      ]
    },    {
      id: "rhythm-evidence", time: "8 min", level: { zh: "节律证据", en: "Rhythm evidence" },
      title: { zh: "相位与周期：不把波动写成定律", en: "Phase and period: do not turn fluctuation into law" },
      summary: { zh: "7/28 天窗口只是观察尺度。真实周期必须从事件序列估计，与随机波动比较，并在证据不足时明确弃判。", en: "Seven- and 28-day windows are observation scales, not the learner's true period. Periodicity must be estimated from events, compared with random fluctuation, and explicitly withheld when evidence is insufficient." },
      objectives: [{ zh: "区分观察窗口、用户周期与相位", en: "Distinguish observation windows, learner periods and phases" }, { zh: "理解候选周期为什么不能直接变成日程", en: "Understand why a candidate period must not become a schedule" }],
      blocks: [
        { type: "table", title: { zh: "五类当前相位", en: "Five current phases" }, headers: [{ zh: "相位", en: "Phase" }, { zh: "可观察依据", en: "Observable basis" }, { zh: "支持方式", en: "Support" }], rows: [
          [{ zh: "吸收与编码", en: "Absorb" }, { zh: "学习与校准明显多于表达", en: "Learning and calibration exceed expression" }, { zh: "完成一个最小可验证输出", en: "Create one minimal verifiable output" }],
          [{ zh: "整合与巩固", en: "Integrate" }, { zh: "学习、输出和校准都有证据", en: "Learning, output and calibration all have evidence" }, { zh: "保持节律并记录有效组合", en: "Maintain the rhythm and record what works" }],
          [{ zh: "表达与分叉", en: "Express" }, { zh: "近期创造投入明显更高", en: "Recent creation investment is higher" }, { zh: "检查现实价值与可验证下一步", en: "Check real value and the next verifiable step" }],
          [{ zh: "现实校准", en: "Calibrate" }, { zh: "有输出但缺少反馈、复测或结果", en: "Output exists without enough feedback, testing or outcomes" }, { zh: "先收集一次真实反馈", en: "Collect one real piece of feedback first" }],
          [{ zh: "恢复或低活动", en: "Recover or low activity" }, { zh: "近期活动减少或出现恢复事件", en: "Recent activity decreased or a recovery event appeared" }, { zh: "先确认恢复、阻塞或离开，不追加负荷", en: "Clarify recovery, blockage or exit before adding load" }]
        ] },
        { type: "concept", title: { zh: "周期证据闸门", en: "Period evidence gate" }, body: { zh: "系统使用 84 天每日学习—创造序列，在 5—28 天范围内估计候选周期，并用置换零分布、自相关强度和反相位关系判断它是否区别于平滑随机波动。状态分为证据不足、无稳定周期、候选周期和稳定周期。", en: "Tender uses an 84-day daily learning-creation series, searches 5–28 days, and compares autocorrelation and antiphase structure against a permutation null. States are insufficient evidence, no stable period, candidate period and stable period." } },
        { type: "table", title: { zh: "合成验证结果", en: "Synthetic validation" }, headers: [{ zh: "指标", en: "Metric" }, { zh: "结果", en: "Result" }], rows: [
          [{ zh: "周期检出率", en: "Periodic detection" }, { zh: "95.3%", en: "95.3%" }],
          [{ zh: "周期估计在容忍范围内", en: "Within tolerance" }, { zh: "93.3%", en: "93.3%" }],
          [{ zh: "平均绝对周期误差", en: "Mean absolute error" }, { zh: "0.45 天", en: "0.45 days" }],
          [{ zh: "非周期稳定周期误报率", en: "Aperiodic stable false positive" }, { zh: "7.0%", en: "7.0%" }],
          [{ zh: "五类受控相位分类", en: "Five controlled phases" }, { zh: "100%", en: "100%" }]
        ] },
        { type: "boundary", body: { zh: "这是合成检测器验证，不是真人周期诊断。候选周期不能变成固定日程；恢复与低活动不能推断休息、放弃或临床状态。", en: "This is synthetic detector validation, not a human rhythm diagnosis. A candidate period must not become a fixed schedule; recovery and low activity cannot determine rest, disengagement or clinical state." } },
        { type: "quiz", question: { zh: "看到“候选周期”时，产品应该怎么做？", en: "What should the product do with a candidate period?" }, options: [{ zh: "立即生成固定日程", en: "Immediately create a fixed schedule" }, { zh: "保持试探性，继续收集证据并允许用户关闭", en: "Keep it provisional, collect more evidence and let the user turn it off" }, { zh: "把它写成人格类型", en: "Turn it into a personality type" }], answer: 1, why: { zh: "候选周期不是稳定结论，更不能成为新的绩效或人格标签。", en: "A candidate period is not a stable conclusion and must not become a performance or personality label." } }
      ]
    },
    {
      id: "dual-chain-group", time: "10 min", level: { zh: "双链路", en: "Dual chain" },
      title: { zh: "群聊中的双链路与授权视图", en: "Dual-chain group chat and authorized views" },
      summary: { zh: "单人链路维护完整自我模型；群聊链路只处理群公开事实、授权视图和共享枝。他者模型属于观察者，不是对方的真实心智。", en: "The single-user chain maintains a complete self-model. The group chain handles only public facts, authorized views and shared branches. A peer model belongs to the observer and is not the subject's true mind." },
      objectives: [{ zh: "区分自我模型、他者假设、授权视图和群组模型", en: "Distinguish self-models, peer hypotheses, authorized views and group models" }, { zh: "理解 Agent 为什么不能自动在群里发言", en: "Understand why an Agent must not auto-send to a group" }],
      blocks: [
        { type: "table", title: { zh: "四类模型", en: "Four model types" }, headers: [{ zh: "对象", en: "Object" }, { zh: "归属", en: "Owner" }, { zh: "边界", en: "Boundary" }], rows: [
          [{ zh: "自我模型", en: "Self-model" }, { zh: "本人", en: "The person" }, { zh: "完整私密状态，不自动进入群聊", en: "Complete private state, never auto-shared" }],
          [{ zh: "他者假设", en: "Peer hypothesis" }, { zh: "观察者", en: "Observer" }, { zh: "公开互动 + 对方授权摘要，始终片面", en: "Public interactions plus authorized summaries; always partial" }],
          [{ zh: "授权视图", en: "Authorized view" }, { zh: "被观察者", en: "Subject" }, { zh: "用途、有效期和撤回权", en: "Purpose, expiry and revocation" }],
          [{ zh: "共享枝", en: "Shared branch" }, { zh: "参与者共同", en: "Participants jointly" }, { zh: "事实、目标、任务、承诺和结果", en: "Facts, goals, tasks, commitments and outcomes" }]
        ] },
        { type: "concept", title: { zh: "Scope Router", en: "Scope Router" }, body: { zh: "群公开消息、我的私密行为、他人授权摘要和系统事件先分开，再进入不同模型。群体模型只读群公开事件和已批准共享枝，不读取任何成员的私人 Tender。", en: "Public messages, my private behavior, authorized summaries and system events are separated before modeling. The group model reads only public events and approved shared branches, never a member's private Tender." } },
        { type: "table", title: { zh: "授权层级", en: "Authorization levels" }, headers: [{ zh: "层级", en: "Level" }, { zh: "分享内容", en: "Shared content" }], rows: [
          [{ zh: "不授权", en: "No grant" }, { zh: "只有群公开互动", en: "Public group interactions only" }],
          [{ zh: "协作级", en: "Coordination" }, { zh: "角色、任务、可用时间、截止承诺", en: "Role, task, availability and deadlines" }],
          [{ zh: "沟通级", en: "Communication" }, { zh: "沟通偏好、支持方式和反馈习惯", en: "Communication and support preferences" }],
          [{ zh: "短期状态级", en: "Time-limited state" }, { zh: "有时效的状态摘要，到期失效", en: "A time-limited state summary that expires" }],
          [{ zh: "共享枝级", en: "Shared branch" }, { zh: "共同目标、承诺和结果", en: "Shared goals, commitments and outcomes" }]
        ] },
        { type: "list", title: { zh: "必须固定为 0 的指标", en: "Metrics that must remain zero" }, items: [{ zh: "私密数据越权读取数", en: "Unauthorized private-data reads" }, { zh: "Agent 自动向群发送数", en: "Automatic Agent sends to the group" }, { zh: "未批准共享枝进入群体模型数", en: "Unapproved branches entering the group model" }] },
        { type: "boundary", body: { zh: "当前群聊后台已通过 9 项隔离测试，全量 114 项测试通过。它验证工程边界，不证明真人群体协作因果效果。BFT 与 Shapley 仍只是后续治理工具。", en: "The group backend passes 9 isolation tests and the full 114-test suite. This validates engineering boundaries, not human group-causality claims. BFT and Shapley remain future governance tools." } },
        { type: "quiz", question: { zh: "B 不授权时，A 的 Tender 可以做什么？", en: "When B grants nothing, what may A's Tender do?" }, options: [{ zh: "读取 B 的完整私密模型", en: "Read B's complete private model" }, { zh: "基于公开互动形成低置信关系假设，并标明证据不足", en: "Form a low-confidence relationship hypothesis from public interactions and label the evidence gap" }, { zh: "自动替 A 向群里发送结论", en: "Automatically send conclusions to the group" }], answer: 1, why: { zh: "他者模型不能读取对方私密 Tender；无授权时只能保留片面的关系假设。", en: "A peer model cannot read the subject's private Tender; without a grant it remains a partial relationship hypothesis." } }
      ]
    },
    {
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
