window.TENDER_COURSE = {
  version: "1.0",
  audience: [
    { zh: "准备第一次使用 Tender 的学习者与家庭", en: "Learners and families preparing to use Tender for the first time" },
    { zh: "需要理解系统边界的产品、教研与工程人员", en: "Product, learning-design and engineering teams who need to understand the system boundaries" },
    { zh: "希望评估证据、隐私与 Agent 协作机制的研究者", en: "Researchers evaluating evidence, privacy and Agent collaboration" }
  ],
  outcomes: [
    { zh: "用自己的话解释预测加工、心智化与行动结果之间的关系", en: "Explain the relationship between predictive processing, mentalization and real outcomes" },
    { zh: "区分语言证据、状态假设、知识掌握度和临床诊断", en: "Distinguish language evidence, state hypotheses, mastery and clinical diagnosis" },
    { zh: "读懂知识森林、Agent 路由和 93 项测试代表什么", en: "Interpret the knowledge forest, Agent routing and the 93-test suite" },
    { zh: "完成一次从证据到最小行动的安全实操", en: "Complete a safe practice loop from evidence to a minimal action" }
  ],
  lessons: [
    {
      id: "orientation", time: "5 min", level: { zh: "基础", en: "Foundation" },
      title: { zh: "Tender 到底是什么", en: "What Tender actually is" },
      summary: { zh: "Tender 不是给用户贴标签的聊天机器人。它把授权事件、语言证据、状态假设和真实结果分层保存，用最小支持帮助人恢复下一步行动。", en: "Tender is not a chatbot that labels people. It separates authorized events, language evidence, state hypotheses and real outcomes, then offers the least support needed to restore the next action." },
      objectives: [{ zh: "说清 Tender 的四个核心层", en: "Name Tender's four core layers" }, { zh: "区分“系统说了什么”和“系统实际知道什么”", en: "Separate what the system says from what it actually knows" }],
      blocks: [
        { type: "concept", title: { zh: "四层结构", en: "Four layers" }, body: { zh: "客观事件进入 DAOQL；语言与行为证据形成候选解释；Tender 将其与历史、结果和情境融合；Agent 再给出最小支持。", en: "Objective events enter DAOQL; language and behavior produce candidate explanations; Tender fuses them with history, outcomes and context; Agents then offer minimal support." } },
        { type: "list", title: { zh: "每一层必须保留什么", en: "What every layer must retain" }, items: [{ zh: "来源：这条信息从哪里来", en: "Provenance: where the evidence came from" }, { zh: "时间：它发生在什么时候", en: "Time: when it happened" }, { zh: "不确定性：系统有多不确定", en: "Uncertainty: how unsure the system is" }, { zh: "可更正性：用户能否纠正或撤回", en: "Correctability: whether the user can correct or revoke it" }] },
        { type: "boundary", body: { zh: "Tender 不做心理或医学诊断，不把单次语言当成能力判决，也不承诺提分或治疗效果。", en: "Tender does not diagnose, does not treat one utterance as a judgment of ability, and does not promise score or treatment outcomes." } },
        { type: "quiz", question: { zh: "哪一个最接近 Tender 的定位？", en: "Which statement best matches Tender's positioning?" }, options: [{ zh: "通过一次测试判定人格", en: "Determine personality from one test" }, { zh: "持续形成可更正的状态假设并支持下一步行动", en: "Continuously form revisable state hypotheses and support the next action" }, { zh: "替代医生和心理咨询师", en: "Replace doctors and psychological counselors" }], answer: 1, why: { zh: "Tender 处理的是带不确定性的学习与心智化状态，不是固定标签。", en: "Tender models uncertain learning and mentalization states rather than fixed labels." } }
      ]
    },
    {
      id: "predictive-mentalizing", time: "7 min", level: { zh: "核心", en: "Core" },
      title: { zh: "两条回路：预测加工与心智化", en: "Two loops: predictive processing and mentalizing" },
      summary: { zh: "人与世界交往主要依靠预测加工；人与人交往还需要心智化。两者相连，但不能混同。", en: "Person–world interaction primarily uses predictive processing; person–person interaction also requires mentalizing. The loops are connected but not identical." },
      objectives: [{ zh: "区分人—世界问题与人—人问题", en: "Distinguish person–world from person–person problems" }, { zh: "理解精度和学习率在模型中的位置", en: "Understand precision and learning rate in the model" }],
      blocks: [
        { type: "concept", title: { zh: "人—世界回路", en: "Person–world loop" }, body: { zh: "人形成预测，行动改变输入，观测产生误差，模型根据误差更新。", en: "A person forms predictions, action changes inputs, observations produce error, and the model updates." } },
        { type: "concept", title: { zh: "人—人回路", en: "Person–person loop" }, body: { zh: "人还需要推断他人的信念、情绪、意图和视角，并通过表达、回应与修复校准关系模型。", en: "People also infer others' beliefs, emotions, intentions and perspectives, then calibrate the relational model through expression, response and repair." } },
        { type: "formula", title: { zh: "最小预测闭环", en: "Minimal predictive loop" }, lines: ["z_t ~ q_theta(z_t | h_t)", "O_hat_t = g_theta(z_t)", "e_t = O_t - O_hat_t", "E_t = e_t^T Pi_t e_t", "theta_t+1 = theta_t - eta * grad_theta E_t", "a_t* = argmin[a in A_t] E[E_t+1(a) | h_t, a]"] },
        { type: "boundary", body: { zh: "Pi_t 是精度权重，不是概率；theta 是模型参数，不是人格；行动集合必须包含恢复、求助和退出。", en: "Pi_t is a precision weight, not probability; theta denotes model parameters, not personality; the action set must include recovery, help-seeking and exit." } },
        { type: "quiz", question: { zh: "“老师是不是觉得我不行”首先属于哪类信号？", en: "Which signal does “Maybe the teacher thinks I'm incapable” primarily contain?" }, options: [{ zh: "人—人心智化推断", en: "A person–person mentalizing inference" }, { zh: "确定的知识掌握度", en: "Confirmed knowledge mastery" }, { zh: "硬件故障", en: "Hardware failure" }], answer: 0, why: { zh: "它在推断他人的想法，必须区分事实与推测。", en: "It infers another person's thought and must distinguish fact from inference." } }
      ]
    },
    {
      id: "language", time: "7 min", level: { zh: "证据", en: "Evidence" },
      title: { zh: "语言检测如何进入 Tender 建模", en: "How language evidence enters Tender" },
      summary: { zh: "语言层提取带来源的片段和竞争假设；它不能单独改变知识掌握度。", en: "The language layer extracts source-grounded spans and competing hypotheses. It cannot change mastery by itself." },
      objectives: [{ zh: "识别情绪、不确定性、回避、求助与心智化信号", en: "Identify emotion, uncertainty, avoidance, help-seeking and mentalizing signals" }, { zh: "说明语言模型、Tender 模型与确定性规则的分工", en: "Explain the division of labor between the language model, Tender model and deterministic rules" }],
      blocks: [
        { type: "table", title: { zh: "语言信号示例", en: "Language signals" }, headers: [{ zh: "信号", en: "Signal" }, { zh: "例子", en: "Example" }, { zh: "不能推出", en: "Cannot conclude" }], rows: [[{ zh: "显式情绪", en: "Explicit affect" }, { zh: "“我现在很焦虑”", en: "“I am very anxious”" }, { zh: "焦虑障碍", en: "An anxiety disorder" }], [{ zh: "回避", en: "Avoidance" }, { zh: "“我不想学了”", en: "“I don't want to study”" }, { zh: "懒惰或长期动机不足", en: "Laziness or chronic low motivation" }], [{ zh: "心智化", en: "Mentalizing" }, { zh: "“他们是不是看不起我”", en: "“Do they look down on me?”" }, { zh: "别人真实的想法", en: "What others actually think" }], [{ zh: "校准偏差", en: "Calibration gap" }, { zh: "“我明明会，考试又错”", en: "“I knew it, but I failed the test again”" }, { zh: "确定的知识掌握度", en: "Confirmed knowledge mastery" }]] },
        { type: "concept", title: { zh: "分工", en: "Division of labor" }, body: { zh: "语言模型负责抽取和表达；Tender 负责多源融合；确定性规则负责高风险路由、来源和禁止结论；用户与人工负责纠正和保护。", en: "The language model extracts and communicates; Tender fuses multiple sources; deterministic rules handle risk routing, provenance and forbidden conclusions; users and humans correct and protect." } },
        { type: "boundary", body: { zh: "“我觉得我会”不是掌握度证据。掌握度来自作答与任务结果。", en: "“I think I know it” is not mastery evidence. Mastery comes from answers and task outcomes." } },
        { type: "quiz", question: { zh: "系统可以仅凭文本直接改变知识掌握度吗？", en: "Can text alone directly change mastery?" }, options: [{ zh: "可以", en: "Yes" }, { zh: "不可以，必须结合作答和任务结果", en: "No—answers and task outcomes are required" }], answer: 1, why: { zh: "语言只用于理解当前表达、支持方式和验证问题。", en: "Language is used for understanding expression, support and verification, not mastery itself." } }
      ]
    },
    {
      id: "state", time: "6 min", level: { zh: "模型", en: "Model" },
      title: { zh: "Tender 如何形成状态假设", en: "How Tender forms state hypotheses" },
      summary: { zh: "状态是语言、行为、作答、结果、历史与情境的联合函数，并持续保留不确定性。", en: "State is a joint function of language, behavior, answers, outcomes, history and context—with uncertainty retained." },
      objectives: [{ zh: "理解融合式 S_t", en: "Understand the fusion equation S_t" }, { zh: "解释为什么模型输出必须可更正", en: "Explain why model outputs must remain correctable" }],
      blocks: [
        { type: "formula", title: { zh: "状态融合", en: "State fusion" }, lines: ["S_t = f(L_t, B_t, K_t, R_t, H_t, C_t)", "", "L = language evidence", "B = behavior and response", "K = knowledge answers", "R = real outcomes", "H = history and baseline", "C = context and relationships"] },
        { type: "concept", title: { zh: "四个常见状态维度", en: "Four common dimensions" }, body: { zh: "注意与工作记忆、认知负荷、元认知校准、节律与恢复。它们都是假设，不是固定人格。", en: "Attention and working memory, cognitive load, metacognitive calibration, and rhythm/recovery. All are hypotheses, not fixed personality." } },
        { type: "list", title: { zh: "每次输出至少包含", en: "Every output should include" }, items: [{ zh: "状态假设与置信度", en: "State hypothesis and confidence" }, { zh: "支持证据与替代解释", en: "Supporting evidence and alternatives" }, { zh: "一个最小行动", en: "One minimal action" }, { zh: "一个结果验证问题", en: "One outcome-check question" }, { zh: "纠正、撤回和暂停入口", en: "Correct, revoke and pause controls" }] },
        { type: "quiz", question: { zh: "状态假设最需要什么？", en: "What do state hypotheses most need?" }, options: [{ zh: "绝对确定性", en: "Absolute certainty" }, { zh: "证据、不确定性、替代解释和更新机制", en: "Evidence, uncertainty, alternatives and an update mechanism" }, { zh: "一个永久人格标签", en: "A permanent personality label" }], answer: 1, why: { zh: "Tender 的目标是可校准，而不是装作全知。", en: "Tender aims for calibration, not omniscience." } }
      ]
    },
    {
      id: "knowledge-forest", time: "5 min", level: { zh: "知识", en: "Knowledge" },
      title: { zh: "知识森林：把全部知识体系放进环境", en: "Knowledge forest: the full knowledge ecosystem" },
      summary: { zh: "知识森林由学科树、专业林、课程灌层、职业天际和生态廊道构成；缺口必须被显示。", en: "The forest combines subject trees, discipline groves, a course understory, a career horizon and ecological corridors. Gaps must remain visible." },
      objectives: [{ zh: "读懂五层知识生态", en: "Read the five knowledge layers" }, { zh: "解释为什么 26/875 的课程覆盖必须披露", en: "Explain why the 26/875 course-seed coverage must be disclosed" }],
      blocks: [
        { type: "table", title: { zh: "五层结构", en: "Five layers" }, headers: [{ zh: "层", en: "Layer" }, { zh: "规模", en: "Scale" }, { zh: "用途", en: "Use" }], rows: [[{ zh: "知识树", en: "Subject trees" }, { zh: "13 学科 / 1,075 节点", en: "13 subjects / 1,075 nodes" }, { zh: "领域—单元—概念钻取", en: "Domain–unit–concept drill-down" }], [{ zh: "专业林", en: "Discipline groves" }, { zh: "13 门类 / 875 专业", en: "13 categories / 875 majors" }, { zh: "专业路径探索", en: "Major-path exploration" }], [{ zh: "课程灌层", en: "Course understory" }, { zh: "319 课程 / 26 个专业有种子", en: "319 courses / seeds for 26 majors" }, { zh: "显示真实覆盖与缺口", en: "Show real coverage and gaps" }], [{ zh: "职业天际", en: "Career horizon" }, { zh: "1,016 职业 / 6 个 RIASEC 维度", en: "1,016 occupations / 6 RIASEC dimensions" }, { zh: "方向探索", en: "Direction exploration" }], [{ zh: "生态廊道", en: "Ecological corridors" }, { zh: "44 组学科—专业桥接", en: "44 subject–major bridges" }, { zh: "显示启发式连接", en: "Show heuristic links" }]] },
        { type: "boundary", body: { zh: "课程种子不是官方培养方案；学科—专业桥接不是官方选科要求；875 个专业也不是 875 套完整课程。", en: "Course seeds are not official curricula; subject–major bridges are not official selection requirements; 875 majors do not mean 875 complete course maps." } },
        { type: "quiz", question: { zh: "当前有多少个专业拥有课程级种子？", en: "How many majors currently have course-level seeds?" }, options: [{ zh: "26", en: "26" }, { zh: "319", en: "319" }, { zh: "875", en: "875" }], answer: 0, why: { zh: "319 是课程数量，不是已有完整课程覆盖的专业数量。", en: "319 is the course count, not the number of majors with complete course coverage." } }
      ]
    },
    {
      id: "agents", time: "6 min", level: { zh: "协作", en: "Collaboration" },
      title: { zh: "Agent 如何像团队一样协作", en: "How Agents collaborate as a team" },
      summary: { zh: "先判断问题类型，再选择固定辅助、专业顾问或工作台 Agent；专家 Agent 可以生成、购买和出售，但必须受授权和审计约束。", en: "First classify the problem, then choose fixed helpers, professional advisors or workbench Agents. Expert Agents can be generated, bought and sold—under authorization and audit." },
      objectives: [{ zh: "说明固定辅助与专家 Agent 的区别", en: "Distinguish fixed helpers from expert Agents" }, { zh: "理解 Agent 路由的第一原则", en: "Understand the first routing principle" }],
      blocks: [
        { type: "concept", title: { zh: "路由不是选最像的专家", en: "Routing is not picking the most similar expert" }, body: { zh: "系统先判断人—世界、人—人或两者嵌套，再决定是否需要学科、心理、安全或学习科学支持。", en: "The system first distinguishes person–world, person–person or nested problems, then decides whether subject, psychology, safety or learning-science support is needed." } },
        { type: "table", title: { zh: "Agent 层级", en: "Agent layers" }, headers: [{ zh: "层", en: "Layer" }, { zh: "作用", en: "Role" }], rows: [[{ zh: "固定辅助", en: "Fixed helpers" }, { zh: "心智化陪伴、情绪调节、反思、家庭桥接、安全", en: "Mentalization companion, regulation, reflection, family bridge, safety" }], [{ zh: "专业顾问", en: "Advisors" }, { zh: "健康、营养、神经认知、心理、学习科学、生涯、安全", en: "Health, nutrition, neurocognition, psychology, learning science, career, safety" }], [{ zh: "工作台编排", en: "Workbench" }, { zh: "协调、内容、评估、教练、沟通与护栏", en: "Coordination, content, assessment, coaching, communication and guardrails" }], [{ zh: "专家市场", en: "Marketplace" }, { zh: "用户生成、上架、购买和授权", en: "Generate, list, buy and authorize" }]] },
        { type: "boundary", body: { zh: "多 Agent 自动执行默认关闭；专家 Agent 不能绕过授权、预算、风险门禁和人工复核。", en: "Automatic multi-Agent execution is off by default; expert Agents cannot bypass authorization, budgets, risk gates or human review." } },
        { type: "quiz", question: { zh: "用户说“我很焦虑”时，第一步应该是什么？", en: "What is the first step when a user says “I am very anxious”?" }, options: [{ zh: "直接调用数学专家", en: "Call a math expert" }, { zh: "先判断问题类型和安全风险，再选专家", en: "Classify the problem and safety risk before choosing an expert" }, { zh: "随机选择一个 Agent", en: "Pick an Agent at random" }], answer: 1, why: { zh: "专家匹配必须服从问题类型和安全边界。", en: "Expert matching must follow problem type and safety boundaries." } }
      ]
    },
    {
      id: "safety", time: "5 min", level: { zh: "治理", en: "Governance" },
      title: { zh: "隐私、安全与证据边界", en: "Privacy, safety and evidence boundaries" },
      summary: { zh: "高风险信号进入确定性人工升级；原始对话、健康数据和未成年人身份不上链。", en: "High-risk signals enter deterministic human escalation. Raw conversations, health data and minor identities do not go on-chain." },
      objectives: [{ zh: "识别三类高风险边界", en: "Identify three high-risk boundaries" }, { zh: "理解数据最小化和可撤回原则", en: "Understand minimization and revocation" }],
      blocks: [
        { type: "list", title: { zh: "三道保护线", en: "Three protection lines" }, items: [{ zh: "即时危险：自伤、暴力、虐待或失联，优先联系可信任成人或紧急服务", en: "Immediate danger: self-harm, violence, abuse or disappearance—contact a trusted adult or emergency service" }, { zh: "证据边界：语言、点击和穿戴数据不能替代临床或教育结果", en: "Evidence boundary: language, clicks and wearables do not replace clinical or educational outcomes" }, { zh: "数据边界：最小化采集、目的限定、可撤回、可审计", en: "Data boundary: minimization, purpose limitation, revocability and audit" }] },
        { type: "boundary", body: { zh: "痛苦不是成长奖章。系统必须区分可转化困难、需要调整的负荷、需要保护的伤害和不可逆风险。", en: "Pain is not a growth badge. The system must distinguish transformable difficulty, overload, harm requiring protection and irreversible risk." } },
        { type: "quiz", question: { zh: "出现明确自伤表达时，系统最优先做什么？", en: "What has priority when explicit self-harm language appears?" }, options: [{ zh: "继续做学科匹配", en: "Continue subject matching" }, { zh: "进入人工与紧急保护流程", en: "Enter human and emergency protection flow" }, { zh: "把内容写入链上", en: "Write the content on-chain" }], answer: 1, why: { zh: "即时安全高于解释和路由。", en: "Immediate safety outranks interpretation and routing." } }
      ]
    },
    {
      id: "practice", time: "4 min", level: { zh: "实操", en: "Practice" },
      title: { zh: "完成一次从证据到行动的闭环", en: "Complete one evidence-to-action loop" },
      summary: { zh: "用普通语言写下一次真实卡点，观察系统如何提取证据、形成假设、给出最小行动，并用结果更新。", en: "Describe one real friction point in ordinary language and observe how the system extracts evidence, forms a hypothesis, offers a minimal action and updates with the outcome." },
      objectives: [{ zh: "完成输入、假设、行动、结果和复盘", en: "Complete input, hypothesis, action, outcome and reflection" }, { zh: "知道什么时候需要纠正、退出或求助", en: "Know when to correct, exit or ask for help" }],
      blocks: [
        { type: "concept", title: { zh: "示例", en: "Example" }, body: { zh: "输入：“我明明会，考试又错，老师是不是觉得我不行？” 系统可提出：校准偏差、对教师心智的推测、行动资源下降三个假设；最小行动可以是先做一道预测题并核对。", en: "Input: “I knew it, but I failed again; maybe the teacher thinks I'm incapable.” The system may propose a calibration gap, a teacher-mind inference and reduced action resources; the minimal action could be one prediction item and a check." } },
        { type: "list", title: { zh: "五步练习", en: "Five-step practice" }, items: [{ zh: "写下发生了什么，不先解释原因", en: "Write what happened before explaining why" }, { zh: "选择一个十分钟内可完成的行动", en: "Choose an action doable in ten minutes" }, { zh: "记录真实结果，不美化", en: "Record the real outcome without polishing it" }, { zh: "指出系统哪句话准确、哪句话不准确", en: "Mark which system statement was accurate or inaccurate" }, { zh: "决定保留、修改、暂停或退出", en: "Decide whether to keep, revise, pause or exit" }] },
        { type: "action", title: { zh: "现在开始", en: "Start now" }, body: { zh: "把一句话和一个最小动作写进你的学习记录。不要为了完成课程而暴露不必要的隐私。", en: "Write one sentence and one minimal action into your learning record. Do not expose unnecessary private information just to complete the course." } },
        { type: "quiz", question: { zh: "闭环什么时候才算完成？", en: "When is the loop complete?" }, options: [{ zh: "Agent 给出建议时", en: "When the Agent gives advice" }, { zh: "真实结果回流并完成复盘时", en: "When a real outcome returns and reflection is completed" }, { zh: "页面关闭时", en: "When the page closes" }], answer: 1, why: { zh: "没有结果回流，就只是建议，不是学习闭环。", en: "Without an outcome returning, it is advice—not a learning loop." } }
      ]
    }
  ]
};
