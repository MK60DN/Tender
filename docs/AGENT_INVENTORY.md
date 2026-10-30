# Tender Agent 对齐清单

本文件由 `scripts/build_agent_inventory.py` 从当前代码生成，是 Agent 文档的唯一对齐口径。

## 0. 执行运行时

- Agent Runtime 可用：True
- 执行层版本：managed
- 默认执行层：tender-agent-runtime
- 模型就绪：True
- DAOQL 继续负责事实、因果、授权、交易与审计，Agent Runtime 只负责执行与协作。

## 1. 运行时 YAML Agent

来源：`agents/*.yaml`；调用入口：`POST /agents/{agent_id}/invoke`。

| Agent ID | 角色 | 层级 | 可调用 |
|---|---|---|---|
| `assessment` | 题目生成、难度标定、知识追踪 | 后台/兼容运行时 | 是 |
| `content_curator` | 课标、讲义、题库入库与 RAG 切片 | 后台/兼容运行时 | 是 |
| `data_steward` | 数据质量、血缘、同意、保留与删除 | 后台/兼容运行时 | 是 |
| `fixed_cognition_emotion_regulator` | 根据认知负荷与情绪上下文调整任务粒度、节奏和恢复方式 | C端固定辅助 | 是 |
| `fixed_family_bridge` | 生成经授权的最小必要家庭支持摘要 | C端固定辅助 | 是 |
| `fixed_mentalization_companion` | 时刻解释认知与情绪状态、证据、置信度与最低必要支持 | C端固定辅助 | 是 |
| `fixed_reflection_coach` | 校准 JOL、信心、策略与真实表现，一次只提出一个反思问题 | C端固定辅助 | 是 |
| `fixed_safety_guardian` | 后台监测高风险信号并转人工支持 | C端固定辅助 | 是 |
| `group_facilitator` | 分组轮换、桥接角色、闭环预警 | 后台/兼容运行时 | 是 |
| `metacognition_coach` | JOL、信心校准、犹豫四象限干预 | 后台/兼容运行时 | 是 |
| `metameta_cartographer` | 读取 DAOQL 客观事件，派生鱼缸记忆·脑图的主观体验节点与生命树关系 | 后台/兼容运行时 | 是 |
| `parent_communication` | 家长周报与家庭配合建议 | 后台/兼容运行时 | 是 |
| `safety_guardrail` | 内容安全、年龄适配、隐私、人工升级 | 后台/兼容运行时 | 是 |
| `sales_ops` | 线索评分、onboarding、续费信号 | 后台/兼容运行时 | 是 |
| `student_tutor` | 苏格拉底式学科辅导 | 后台/兼容运行时 | 是 |
| `teacher_copilot` | 班级状态摘要、干预建议、metameta 反馈 | 后台/兼容运行时 | 是 |

## 2. C 端固定辅助 Agent

来源：`app/agent_marketplace.py:FIXED_AGENTS`，且每个都有对应的运行时 YAML。

| Agent ID | 名称 | 数据范围 | 运行时状态 |
|---|---|---|---|
| `fixed_mentalization_companion` | 心智化陪伴 | self_reflection, authorized_summary, aggregated_tender_state | 已实现并可调用 |
| `fixed_cognition_emotion_regulator` | 认知—情绪调节 | self_reflection, emotion_context, authorized_summary | 已实现并可调用 |
| `fixed_reflection_coach` | 反思教练 | self_reflection, metacognition_summary | 已实现并可调用 |
| `fixed_family_bridge` | 家庭桥接 | approved_family_summary | 已实现并可调用 |
| `fixed_safety_guardian` | 安全与保护 | minimal_safety_signals | 已实现并可调用 |

## 3. 工作台编排 Agent

来源：`app/workbench.py:AGENT_CATALOG`；它们是多 Agent 工作台内的编排角色，不是市场商品。

| Agent ID | 名称 | 职责 |
|---|---|---|
| `coordinator` | 协调者 | 拆解任务、分派、汇总、等待审批 |
| `content_curator` | 内容 Agent | 题库、讲义、重点词汇和句型抽取 |
| `assessment` | 评估 Agent | 批改、错因统计和学生状态更新 |
| `student_tutor` | 学生教练 | 最小提示、复盘和复习安排 |
| `external_communication` | 对外沟通 Agent | 按接收方角色生成待审批的沟通草稿 |
| `safety_guardrail` | 安全护栏 | 隐私、排名、越权和高风险语言检查 |

## 4. MoA 路由顾问

来源：`app/advisor_router.py:EXPERTS`；按对话与授权摘要选择 1–3 个，不共享原始数据。

| ID | 名称 | 数据范围 |
|---|---|---|
| `safety_advisor` | 安全与保护 | `minimal_safety_signals` |
| `health_advisor` | 健康 | `sleep_activity_health` |
| `nutrition_advisor` | 营养 | `meal_nutrition` |
| `neurocognitive_advisor` | 神经认知 | `cognitive_profile` |
| `psychology_advisor` | 心理支持 | `emotion_support_signals` |
| `career_advisor` | 生涯与职业 | `learning_passport_evidence` |
| `learning_science_advisor` | 学习科学 | `aggregated_tender_state` |
| `assessment` | 评估证据 | `assessment_evidence` |
| `external_communication` | 对外沟通 | `approved_external_summary` |

## 5. 市场专家 Agent

- 市场专家 Agent 不是固定名单，由用户需求生成 AgentSpec 后写入 `expert_agents` 表。
- 调用入口：`POST /agents/{agent_id}/invoke`。
- 必须由 Owner 或已购买授权用户调用。
- 已接入可插拔 Agent Runtime；没有模型时会回退到结构化 AgentSpec 输出。

## 6. 多 Agent Workforce

- 规划入口：`POST /workforce/plan`。
- 默认 `execute=false`，只生成多 Agent 执行计划。
- 只有显式设置运行时执行开关且请求 `execute=true` 才会启动。
- 生产环境还必须经过 RBAC、预算、工具白名单和风险门禁。

## 7. 当前真实边界

- 固定辅助 Agent：运行时 YAML + Agent Runtime 执行已实现。
- 专家 Agent 生成、上架与购买授权：已实现；支付为模拟状态。
- 专家 Agent 调用：Agent Runtime 已接入，失败时回退结构化输出。
- 多 Agent Workflow：已接入规划；自动执行默认关闭。
- 工作台 Agent 与 MoA 顾问是不同层，不能与固定消费者 Agent 混为一类。
