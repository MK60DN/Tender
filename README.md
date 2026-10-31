# Tender

**A research-grade lifelong learning and mentalization system**  
**研究型终身学习与心智化支持系统**

[English detail](README.en.md) · [中文完整版](README.zh-CN.md)

## Start here / 从这里开始

- **Teaching website / 教学网站**： [GitHub Pages](https://mk60dn.github.io/Tender/) · [Local course / 本地课程](http://127.0.0.1:8080/guide/) · [Source / 源码](site/)
- **Whitepaper V1.9 / 白皮书 V1.9**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Whitepaper-v1.9.pdf) · [Repo PDF](docs/whitepaper/Tender-Whitepaper-v1.9.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v1.9.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v1.9.tex)
- **Product manual / 产品手册**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Product-Manual-v6.23.pdf) · [Repo PDF](docs/product/Tender-Product-Manual-v6.23.pdf)
- **User guide / 用户手册**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-User-Guide-v6.11.pdf) · [Repo PDF](docs/product/Tender-User-Guide-v6.11.pdf)
- **Golden-bias experiment / 动态黄金比实验**： [Repo PDF](docs/research/Tender-Golden-Bias-Experiment-v1.0.pdf) · [Results](experiments/golden_bias_regulation/results.json)
- **Rhythm evidence experiment / 节律相位实验**： [Repo PDF](docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf) · [Results](experiments/rhythm_phase_detection/results.json)
- **Teaching manual / 零基础教学手册**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Teaching-Manual-v5.6.pdf) · [Repo PDF](docs/teaching/Tender-Teaching-Manual-v5.6.pdf)


[![CI](https://github.com/MK60DN/Tender/actions/workflows/ci.yml/badge.svg)](https://github.com/MK60DN/Tender/actions/workflows/ci.yml)

> **EN** — Tender learns, with explicit authorization, from behavior, language and real outcomes to form revisable hypotheses about attention, cognitive load, motivation and friction. It separates objective events, language evidence, subjective experience and optional Agent support.
>
> **中文** — Tender 在明确授权下，从行为、语言和真实结果中形成关于注意、认知负荷、动机与行动阻力的可更正假设。系统严格区分客观事件、语言证据、主观体验和可选 Agent 支持。

## Why Tender / 为什么需要 Tender

| English | 中文 |
|---|---|
| One score is too late and too narrow to explain why learning breaks down. | 单一分数出现得太晚，也无法解释学习为什么卡住。 |
| Tender treats exams as periodic checks and treats behavior, language and outcomes as continuous evidence. | Tender 把考试视为定期检查，把行为、语言与结果视为连续证据。 |
| The goal is not to grade a person, but to support the next viable action and preserve long-term evidence. | 目标不是给人打分，而是支持下一个可执行动作，并保存长期成长证据。 |

## What it is / 它是什么

- **Mentalization layer / 心智化层**：turn authorized evidence into competing, reversible state hypotheses. / 把授权证据转化为竞争性、可撤回的状态假设。
- **Language evidence layer / 语言证据层**：extract emotion, uncertainty, avoidance, help-seeking and mentalizing signals with source spans. / 从话语中提取情绪、不确定性、回避、求助与心智化信号，并保留来源片段。
- **World tree / 世界树**：DAOQL roots → Agent Bridge trunk → five experience branches → local state axes → flowering and outcomes; shared branches require explicit consent. / DAOQL 根系 → Agent Bridge 树干 → 五类体验树枝 → 局部状态轴 → 开花与结果；共享枝必须获得明确授权。
- **Evidence-gated rhythm / 节律证据**：7/28-day windows control observation; a detected period must survive permutation and antiphase checks before it is reported. / 7/28 天窗口只负责观察与控制；检测到的周期必须通过置换与反相位检验后才能报告。
- **Knowledge forest / 知识森林**：13 subjects, 1,075 K12 nodes, 875 majors, 319 course seeds and 1,016 occupations. / 连接 13 个学科、1,075 个知识节点、875 个专业、319 门课程与 1,016 个职业。
- **DAOQL event layer / DAOQL 事件层**：facts, provenance, causality, authorization and audit. / 保存事实、来源、因果、授权与审计。
- **Agent system / Agent 系统**：fixed helpers, professional advisors, orchestration and an expert-Agent marketplace MVP. / 固定辅助、专业顾问、编排与专家 Agent 市场 MVP。
- **Research transparency / 研究透明**：public benchmarks, negative results, uncertainty and claim boundaries. / 公开基准、失败结果、不确定性与主张边界。

## What it is not / 它不是什么

- Not a diagnostic or mind-reading system. / 不是诊断工具，也不是“读心”系统。
- Language evidence does not determine mastery, personality or clinical state. / 语言证据不能单独决定掌握度、人格或临床状态。
- Synthetic and benchmark results are not proof of real-world educational effect. / 合成与基准结果不等于真实教育效果。
- No claim of guaranteed score improvement, admission or employment. / 不承诺提分、录取或就业结果。
- No raw conversations, health data or minor identities on-chain. / 原始对话、健康数据与未成年人身份不上链。

## Architecture / 架构

```text
World events · behavior · dialogue · answers · outcomes
世界事件 · 行为 · 对话 · 作答 · 结果
                         │
                         ▼
DAOQL: provenance · causality · authorization · audit
DAOQL：来源 · 因果 · 授权 · 审计
                         │
                         ▼
Bloch observation surface · language evidence · metameta
Bloch 有限接触面 · 语言证据 · metameta
                         │
                         ▼
Tender state hypotheses · life tree
Tender 状态假设 · 生命树
                         │
                         ▼
Fixed helpers + advisors + expert Agents
固定辅助 + 专业顾问 + 专家 Agent
                         │
                         ▼
Minimal action → real outcome → model update
最小行动 → 真实结果 → 模型更新
```

## Implemented / 已实现

| Area / 模块 | Status / 状态 |
|---|---|
| Language evidence / 语言证据 | source spans, competing hypotheses, alternative explanations, risk routing / 来源片段、竞争假设、替代解释、风险路由 |
| Knowledge ecosystem / 知识生态 | full database-backed forest and drill-down / 全量数据库森林与钻取 |
| State modeling / 状态建模 | baseline, rhythm, JOL, metacognition, fit, outcomes / 基线、节律、JOL、元认知、匹配、结果 |
| Agent runtime / Agent 运行时 | fixed helpers, advisors, workbench, marketplace MVP / 固定辅助、顾问、工作台、市场 MVP |
| Governance / 治理 | signed sessions, object authorization, audit hash chain, safety tickets / 签名会话、对象授权、审计哈希链、安全工单 |
| Tests / 测试 | 105 automated tests / 105 项自动测试 |

## Teaching site / 教学网站

双语教学网站位于 `site/`，包含 12 个模块、82 分钟、学习进度、语言切换与知识检查。FastAPI 在 `/guide/` 提供页面，GitHub Pages 由 `.github/workflows/pages.yml` 部署。

## Quick start / 快速开始

Requirements: Python 3.11–3.12.

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

Open / 打开：

- App / 主应用：<http://127.0.0.1:8080/ui/>
- Language evidence / 语言证据层：<http://127.0.0.1:8080/ui/language.html>
- Knowledge forest / 知识森林：<http://127.0.0.1:8080/ui/knowledge.html>
- API docs / API 文档：<http://127.0.0.1:8080/docs>

`LLM_PROVIDER=mock` runs without an external model. Copy `.env.example` to `.env` only when connecting a model provider. / 默认 mock 模式无需外部模型；接入真实模型时再复制 `.env.example`。

## Tests / 测试

```bash
python agent_layer/tests/run_all.py
```

Expected baseline / 当前基线：`passed 105 tests`.

## Core APIs / 核心接口

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
```

## Repository map / 仓库结构

```text
agent_layer/       runnable app, Agents, UI and tests / 可运行应用、Agent、UI、测试
knowledge_data/    subject, major, course and career databases / 学科、专业、课程、职业数据库
experiments/       selected reproducible research code / 精简可复现研究代码
docs/whitepaper/   Whitepaper V1.9: TeX, PDF, Word / 白皮书 V1.9
docs/product/      product and user manuals / 产品与用户手册
docs/research/     evidence and validation reports / 证据与验证报告
site/               bilingual teaching website / 双语教学网站
```

## Data and safety / 数据与安全

- 26 of 875 majors currently have course-level seeds. / 875 个专业中目前仅 26 个有课程级种子。
- High-risk language signals enter a deterministic human-escalation path. / 高风险语言信号进入确定性人工升级路径。
- Runtime databases, tenant data, `.env` and session secrets are not committed. / 运行数据库、租户数据、`.env` 与会话密钥不会提交。
- See [data licenses](docs/DATA_LICENSES.md), [privacy and safety](docs/PRIVACY_AND_SAFETY.md) and [research claims](docs/RESEARCH_CLAIMS.md). / 详见数据许可证、隐私安全与研究边界。

## Documentation / 文档

- [Whitepaper V1.9 / 白皮书 V1.9](docs/whitepaper/Tender-Whitepaper-v1.9.pdf)
- [Product manual / 产品手册](docs/product/Tender-Product-Manual-v6.23.pdf)
- [User guide / 用户手册](docs/product/Tender-User-Guide-v6.11.pdf)
- [Central thesis / 中心主旨](docs/product/Tender-Central-Thesis.md)

## License / 许可证

**PolyForm Noncommercial License 1.0.0**

Personal, educational, research and other noncommercial use is permitted.
Commercial use is prohibited without separate written permission.

允许个人、教育、研究和其他非商业用途。未经另行书面许可，禁止商业化使用。

This is source-available, not an OSI-approved open-source license. See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md). / 这是源码可见许可证，不是 OSI 批准的开源许可证。



