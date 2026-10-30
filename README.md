# Tender

> 温柔地了解您的心智。基于授权后的行为、回复和真实结果，了解注意、负荷、动机与行动阻力。

[![CI](https://github.com/MK60DN/Tender/actions/workflows/ci.yml/badge.svg)](https://github.com/MK60DN/Tender/actions/workflows/ci.yml)

Tender 是一个研究型、可运行的终身学习与心智化支持系统。它把客观事件、语言证据、行为结果和可更正的状态假设分层保存，使用固定辅助 Agent 与可生成的专家 Agent 提供支持。

项目当前版本对应《Tender 项目白皮书 V1.5》。

## 它是什么

- **心智化学习系统**：记录注意、认知负荷、动机、情绪上下文和行动恢复。
- **可追溯的事件系统**：DAOQL 保存事实、来源、因果关系、授权和审计。
- **语言证据层**：从话语中提取可观察片段，生成带来源、置信度和替代解释的候选假设。
- **多 Agent 系统**：固定辅助 Agent、专业顾问、工作台编排与专家 Agent 市场。
- **知识森林**：连接 13 个高中学科、1,075 个知识节点、875 个本科专业、319 门课程和 1,016 个职业方向。
- **可检验的研究系统**：公开报告证据等级、失败结果、测量边界和待验证假设。

## 它不是什么

- 不是心理或医学诊断工具；
- 不是“读心”系统；
- 不会仅凭一句话推断知识掌握度、人格或临床状态；
- 不把合成实验当作真人因果证据；
- 不承诺提分、录取、就业或治疗效果；
- 不允许原始对话、健康数据和未成年人身份进入链上。

## 核心架构

```text
世界事件 / 行为 / 对话 / 作答 / 真实结果
                  │
                  ▼
        DAOQL 客观事件与因果层
         来源 · 时间 · 授权 · 审计
                  │
                  ▼
   Bloch 有限接触面 / 语言证据 / metameta
                  │
                  ▼
        Tender 状态假设与生命树
   注意 · 负荷 · 元认知 · 情绪 · 关系
                  │
                  ▼
   固定辅助 Agent + 专业顾问 + 专家 Agent
                  │
                  ▼
       最小行动 → 真实结果 → 模型更新
```

## 当前已实现

| 模块 | 内容 |
|---|---|
| Web 应用 | FastAPI + 原生 HTML/CSS/JS |
| 语言证据 | 证据片段、竞争假设、替代解释、高风险路由 |
| 知识体系 | 13 学科、1,075 节点、875 专业、319 课程、1,016 职业 |
| 知识森林 | 全量知识生态可视化与钻取 |
| 状态建模 | 基线、节律、JOL、元认知、安排匹配、行动结果 |
| Agent | 固定辅助、顾问路由、工作台、Agent 市场 MVP |
| 治理 | 签名会话、对象授权、审计哈希链、安全工单 |
| 研究 | 认知构念、纵向多角色测试、公开基准与证据边界 |
| 测试 | 93 项自动测试 |

## 快速开始

要求 Python 3.11 或 3.12。

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
cd agent_layer
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

打开：

- 主应用：<http://127.0.0.1:8080/ui/>
- 语言证据层：<http://127.0.0.1:8080/ui/language.html>
- 知识森林：<http://127.0.0.1:8080/ui/knowledge.html>
- API 文档：<http://127.0.0.1:8080/docs>

默认使用 `LLM_PROVIDER=mock`，无需 API Key。接入真实模型时复制 `.env.example` 为 `.env` 并填写自己的兼容接口配置。

## 测试

```bash
python agent_layer/tests/run_all.py
```

本地基线：`passed 93 tests`。

## 核心接口

```text
GET  /health
GET  /knowledge/forest
POST /language/analyze
GET  /language/schema
GET  /tender/context/{student_id}?message=...
GET  /cognition/constructs
GET  /agents/catalog
GET  /agent-runtime/status
POST /workforce/plan
GET  /docs
```

## 仓库结构

```text
agent_layer/                  可运行应用、Agent、UI、测试
knowledge_data/               学科、专业、课程、职业 SQLite 数据库
experiments/                  可复现实验代码与精简结果
docs/whitepaper/              白皮书 V1.5：TeX、PDF、Word
docs/product/                 产品手册、用户手册、版本文件
docs/research/                神经学习、预检测、验证报告
docs/strategy/                博弈论与机制设计
.github/                      CI、Issue 与 PR 模板
```

## 数据与证据边界

详细数据来源与许可证见 [docs/DATA_LICENSES.md](docs/DATA_LICENSES.md)。

- 高中知识结构依据公开课程标准整理，不等于教材逐字目录；
- 875 个专业中，目前只有 26 个有课程级种子；
- 高中—专业桥接是启发式证据，不是官方选科要求；
- O*NET 内容遵循 CC BY 4.0；
- 仓库不包含真实学生、家庭或租户数据库；
- 合成用户和纵向测试不等于真人教育效果。

## 安全与隐私

- 运行数据库、租户数据库、会话密钥、`.env` 和缓存不会进入版本库；
- 高风险语言信号进入人工保护流程；
- 生产环境需要 OIDC/RBAC、密钥管理和真实合规评估；
- 安全问题请使用 GitHub Security Advisory，详见 [SECURITY.md](SECURITY.md)。

## 文档

- [项目白皮书 V1.5](docs/whitepaper/Tender-Whitepaper-v1.5.pdf)
- [中心主旨](docs/product/Tender-Central-Thesis.md)
- [产品手册](docs/product/Tender-Product-Manual-v6.19.pdf)
- [用户手册](docs/product/Tender-User-Guide-v6.7.pdf)
- [研究边界](docs/RESEARCH_CLAIMS.md)

## License

本项目采用 **PolyForm Noncommercial License 1.0.0**：允许个人、教育、研究和其他非商业用途，禁止商业化使用。

这是源码可见的非商业许可证，不是 OSI 批准的开源许可证。商业授权必须另行取得版权所有者书面许可。第三方数据和依赖继续遵循各自许可证，详见 [NOTICE](NOTICE) 与 [docs/DATA_LICENSES.md](docs/DATA_LICENSES.md)。
