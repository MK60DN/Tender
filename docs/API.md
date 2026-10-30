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
