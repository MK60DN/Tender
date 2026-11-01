# Tender C 端 API

基础地址：`http://127.0.0.1:8080`

## 身份认证

开发态签名会话：

```text
POST /auth/demo-session
GET  /auth/me

POST /guardian/requests
GET  /guardian/requests
POST /guardian/requests/{learner_id}/{guardian_id}/verify
POST /guardian/requests/{learner_id}/{guardian_id}/revoke

GET  /audit
GET  /audit/verify

GET  /safety/tickets
GET  /safety/tickets/{ticket_id}
POST /safety/tickets/{ticket_id}/update
```

登录请求：

```json
{"actor_id":"S01","role":"learner","learner_id":"S01"}
```

响应：

```json
{"token":"...","token_type":"Bearer","expires_in":3600}
```

除公开目录、市场浏览和健康检查外，敏感接口必须携带：

```text
Authorization: Bearer <token>
```

监护关系必须经过管理员核验后才允许家庭访问；撤回后立即失去访问。

审计日志使用哈希链，`GET /audit/verify` 可由管理员验证完整性。

会话支持退出登录和强制全端下线。

高风险事件生成安全工单，管理员可分配、升级和关闭。

生产环境应关闭 `TENDER_DEMO_MODE`，替换为 OIDC/真实会话。

## 健康检查

```text
GET /health
```

## 角色面

```text
GET /roles?surface=consumer
```

默认只返回：

- `learner`
- `parent`

专业顾问不作为用户手工切换的账号。它们由 MoA 按对话调用：

```text
GET /roles?surface=advisor_runtime
```

历史兼容：

```text
GET /roles?surface=all
```

## 学习首页

```text
GET /learner/home/{learner_id}
```

返回：

- 学习者身份与 Tender ID；
- 学习护照；
- 当前心智化状态卡；
- 最低必要支持；
- 按需专业支持网络；
- AI 伙伴建议；
- 家庭授权边界；
- 数据可携带度。

## 心智化状态卡

```text
GET /learner/mentalization/{learner_id}
```

示例响应：

```json
{
  "summary": "元认知校准可能存在偏差",
  "confidence": 0.835,
  "hypotheses": [
    {
      "id": "metacognitive_calibration",
      "label": "元认知校准可能存在偏差",
      "evidence": ["预测与实际表现偏差约 +0.20"]
    }
  ],
  "emotion_context": {
    "label": "紧张或高负荷",
    "confidence": 0.5,
    "note": "只作为学习支持上下文"
  },
  "reflection_prompt": "作答前你预估自己对多少？现在回看，差距来自哪一步？",
  "boundary": "这是用于学习支持的状态假设，不是心理或医学诊断"
}
```

## 心智化快照

```text
POST /learner/mentalization/snapshot/{learner_id}
```

把当前认知与情绪状态、置信度、证据、反思问题写入 DAOQL，用于长期因果。

## 心智化时间线

```text
GET /learner/mentalization/timeline/{learner_id}
```

返回：

- 认知与情绪时间点；
- 状态变化；
- 支持—反思—结果链；
- 可审计证据引用。

## 写入反思

```text
POST /learner/reflection/{learner_id}
```

请求：

```json
{
  "prompt": "此刻最值得被理解的是什么？",
  "answer": "我卡在不知道如何开始，也有点焦虑。",
  "consent_scopes": ["self_reflection", "learning_support"]
}
```

响应：

- `status=recorded`
- DAOQL `event_id`
- 更新后的心智化状态卡

## 导出学习护照

```text
GET /learner/export/{learner_id}
```

返回可下载 JSON。导出内容属于学习者本人。

## Agent 总目录

```text
GET /agents/catalog
```

由当前代码生成，返回：

- 15 个运行时 YAML Agent；
- 5 个 C 端固定辅助 Agent；
- 6 个工作台编排 Agent；
- 9 个 MoA 路由顾问；
- 当前市场专家 Agent 实例。

## Agent Runtime 运行时

```text
GET  /agent-runtime/status
POST /workforce/plan
```

`/agent-runtime/status` 返回 Agent Runtime 版本、模型与回退状态。

`/workforce/plan` 默认只生成执行计划：

```json
{
  "task": "分析当前心智化状态并给出安全支持",
  "agent_ids": [
    "fixed_mentalization_companion",
    "fixed_reflection_coach",
    "fixed_safety_guardian"
  ],
  "execute": false
}
```

只有设置 `ENABLE_AGENT_WORKFLOW=1` 且 `execute=true` 才会真正启动 多 Agent Workflow。

## 固定辅助 Agent

```text
GET /agents/fixed
```

返回始终可用的心智化陪伴、认知—情绪调节、反思教练、家庭桥接与安全保护 Agent。

## 专家 Agent 市场调用

固定 Agent 与市场专家都通过：

```text
POST /agents/{agent_id}/invoke
```

市场专家必须由 Owner 或已购买授权用户调用。

## 专家 Agent 市场

```text
GET  /agents/marketplace?query=&category=
POST /agents/generate
GET  /agents/{agent_id}/spec
POST /agents/{agent_id}/purchase
GET  /agents/entitlements/{buyer_id}
```

生成请求：

```json
{
  "owner_id": "S01",
  "need": "帮助我在焦虑时拆分任务并做元认知复盘",
  "name": "认知情绪调节专家",
  "category": "emotion_cognition",
  "price_cents": 1990,
  "visibility": "marketplace"
}
```

规则：

- 生成受控 AgentSpec，不直接生成无限权限 Agent；
- 默认只访问授权摘要；
- 高风险类别需要认证与人工审阅；
- 购买获得使用授权，不转移模型权重或原始数据；
- 卖家分成 80%，平台分成 20%（当前为模拟支付）。

## Multi-Agent Workbench / 实验模型增强

```text
GET  /workbench/agents
GET  /workbench/experimental/status
GET  /workbench/threads
POST /workbench/threads
GET  /workbench/threads/{thread_id}
POST /workbench/threads/{thread_id}/orchestrate
POST /workbench/approvals/{approval_id}/decide
```

实验增强仅在 orchestration 请求包含 `context_overrides.use_experimental_api=true` 时启用。六个协作 Agent 并行调用配置好的实验模型 API，并将模型生成的补充判断写入各自的 `output.experimental_api`。

边界：

- 只发送脱敏任务类型、任务长度、受众角色和聚合状态摘要；
- 不发送姓名、学校、班级、原始对话、健康信息、完整学习树或会话 ID；
- 确定性 Workbench 输出仍是主契约，模型输出只作补充；
- API 不可用、只返回推理内容或超时时，自动保留确定性安全结果；
- 对外沟通仍只能是草稿，必须由真人审批。

## DAOQL

```text
POST /daoql/events
GET  /daoql/events/{learner_id}
GET  /daoql/causal_path?source=...&target=...
GET  /daoql/graph/{learner_id}
GET  /audit?limit=20
```

## Tender 状态

```text
GET /tender/state/{learner_id}
```

返回：

- 知识结构；
- 元认知与 JOL 偏差；
- 犹豫；
- 节律与安排匹配；
- 情绪上下文占位或估计；
- 群体结构与观察者状态。

## 专业顾问路由

```text
POST /advisors/route
```

请求：

```json
{
  "student_id": "S01",
  "role": "learner",
  "message": "我最近压力很大，也总是走神，不知道该怎么安排学习。",
  "consent_scopes": ["aggregated_tender_state"]
}
```

规则：

- 每次最多选择 3 个相关顾问；
- 安全检查后台常驻；
- 顾问之间只交换授权摘要；
- 不共享原始对话；
- 只生成一条统一回复，不让多个 Agent 同时对话。

## 授权摘要协作

```text
POST /advisors/share
```

必须显式具备 `share:{from_advisor}:{to_advisor}` 授权，且只共享摘要与证据引用。

## 边界

- 当前 RBAC 仍是界面预览，生产环境必须补服务端鉴权；
- 不输出临床诊断；
- 未成年人必须接入监护人授权；
- 高风险事件必须人工升级；
- 所有 Agent 动作必须进入审计。


## 机构租户隔离

租户会话只能通过独立租户库中的 membership 建立：

```text
POST /tenant/demo-session
```

请求：

```json
{"tenant_id":"yanwen","actor_id":"yanwen-admin"}
```

查询：

```text
GET /tenant/context
GET /tenant/stats
GET /tenant/students?campus_id=&class_id=&query=&limit=
GET /tenant/students/{student_id}
GET /tenant/leads?campus_id=&limit=
GET /tenant/files?classification=&campus_id=&limit=
GET /tenant/search?q=&limit=
GET /tenant/projections/stats?year=2026
GET /tenant/projections/students?year=2026&stage=&review_status=&campus_id=&limit=
```

隔离规则：

- 每个机构使用独立 SQLite 文件；
- 客户端不能通过 header 切换租户；数据库由签名会话中的 `tenant_id` 决定；
- 校区管理员只能读所属校区，班主任只能读指定班级，顾问/家长/学习者只能读指定学生；
- 敏感联系人、财务、合同、HR、账号文件默认不对教师角色开放；
- 2026 推算学生与原始学生分表保存，返回 `synthetic=true`，不得当作已确认事实。

## 世界树与世界入口

```text
GET  /preassessment/items
POST /preassessment/submit/{learner_id}
GET  /preassessment/profile/{learner_id}
GET  /preassessment/pulse/items
POST /preassessment/pulse/{learner_id}
GET  /preassessment/pulse/{learner_id}
GET  /world-tree/{student_id}
GET  /golden-bias/{student_id}
```

`/preassessment/*` 保存标准化八功能态度、大五基线与大五脉搏，不保存逐题原文。`/world-tree/{student_id}` 返回 DAOQL 客观根系、Agent Bridge 树干、五类树枝、11 个体验节点、开花、结果与共享枝边界。共享枝默认不生成，需双方明确授权。
## 动态黄金比偏置

`GET /golden-bias/{student_id}` 返回 7 天和 28 天窗口下的学习/创造投入、较小极与较大极占比、带内状态、滞回状态、新异比、创造后 72 小时校准比、置信度和下一步探针。当前版本还返回 `rhythm.detected_periodicity`、`rhythm.current_phase` 与 `rhythm.phase_sequence`：真实周期从 84 天事件序列估计，状态为 `insufficient_evidence`、`no_stable_period`、`candidate_period` 或 `stable_period`；7/28 天窗口不被解释为用户周期。证据不足时既不输出比例结论，也不输出稳定周期。该接口只用于节律支持，不用于人格、能力、关系匹配、绩效或临床评分。

# 群聊双链路 API

群聊链路不读取成员的私密 Tender。每个成员保留自己的完整模型；群聊只处理群公开事件、授权视图、他者假设、共享枝和群体模型。群成员只能看到自己的授权范围，不能查看他人的授权字段。

## 群会话

```text
GET    /group-sessions
POST   /group-sessions
POST   /group-sessions/{group_id}/join
GET    /group-sessions/{group_id}
POST   /group-sessions/{group_id}/events
GET    /group-sessions/{group_id}/events
GET    /group-sessions/{group_id}/model
POST   /group-sessions/{group_id}/drafts
POST   /group-sessions/{group_id}/outcomes
GET    /group-sessions/{group_id}/outcomes
```

## 他者授权与关系假设

```text
POST   /peer-view-grants
GET    /peer-view-grants
DELETE /peer-view-grants/{grant_id}
GET    /peer-models/{observer_id}/{subject_id}?group_id=...
```

- 只有授权视图的所有者可以创建或撤回授权。
- 只有观察者本人可以读取自己发起的他者模型。
- 他者模型只能读取群公开互动和授权摘要，不能读取对方的私密 Tender。
- 撤回授权后，由该授权产生的派生模型会失效。

## 共享枝

```text
POST /group-sessions/{group_id}/shared-branches
GET  /group-sessions/{group_id}/shared-branches
POST /shared-branches/{branch_id}/approve
```

共享枝只允许事实、目标、任务、承诺、边界、结果和摘要，并区分 `bilateral` 与 `group`。双人枝不会自动进入 Group Model；只有群组可见且全部参与者批准的共享枝才进入群体模型。Agent 生成的群聊内容仅为草稿，`auto_send=false`。

## Local MCP interfaces

界面上下文和多媒体能力不是公开 HTTP 接口，而是通过仓库根目录 `.mcp.json` 启动的本地 stdio MCP 服务提供。

### tender-screen-context

```text
grant_screen_context
screen_context_status
read_screen_context
capture_screen_context
revoke_screen_context
```

### tender-media-tools

```text
list_media_plugins
analyze_image
transcribe_audio
analyze_video
speak_text
list_voices
```

MCP 服务要求显式用户授权。原始窗口文字、截图和媒体内容不写入 DAOQL；弹幕规划只使用粗粒度派生信号。
