# Tender

**A research-grade system connecting self, world, other minds and collaborative outcomes**
**连接自我、世界、他人心智与共同结果的终身学习系统**

[English detail](README.en.md) · [中文完整版](README.zh-CN.md)

## Start here / 从这里开始


- **DAOQL living whitepaper / 数据活水白皮书**：[Read online](https://mk60dn.github.io/Tender/whitepaper.html) · [Markdown source](docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md) · [Edit on GitHub](https://github.com/MK60DN/Tender/edit/main/docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md) · [PDF](docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.pdf) · [Collaboration guide](docs/COLLABORATION.md)
- **One-click backend / 一键后端**：[GitHub Codespaces](https://codespaces.new/MK60DN/Tender?quickstart=1) · [Deploy to Render](https://render.com/deploy?repo=https://github.com/MK60DN/Tender) · [Deployment guide](docs/DEPLOYMENT.md)
- **Teaching website / 教学网站**： [GitHub Pages](https://mk60dn.github.io/Tender/) · [Local course / 本地课程](http://127.0.0.1:8080/guide/) · [Source / 源码](site/)
- **Whitepaper V2.2 / 白皮书 V2.2**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Whitepaper-v2.2.pdf) · [Repo PDF](docs/whitepaper/Tender-Whitepaper-v2.2.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v2.2.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v2.2.tex)
- **Product manual / 产品手册**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Product-Manual-v7.2.pdf) · [Repo PDF](docs/product/Tender-Product-Manual-v7.2.pdf) · [Word](docs/product/Tender-Product-Manual-v7.2.docx)
- **User guide / 用户手册**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-User-Guide-v7.2.pdf) · [Repo PDF](docs/product/Tender-User-Guide-v7.2.pdf) · [Word](docs/product/Tender-User-Guide-v7.2.docx)
- **Golden-bias experiment / 动态黄金比实验**： [Repo PDF](docs/research/Tender-Golden-Bias-Experiment-v1.0.pdf) · [Results](experiments/golden_bias_regulation/results.json)
- **Rhythm evidence experiment / 节律相位实验**： [Repo PDF](docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf) · [Results](experiments/rhythm_phase_detection/results.json)
- **Teaching manual / 零基础教学手册**： [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Teaching-Manual-v6.2.pdf) · [Repo PDF](docs/teaching/Tender-Teaching-Manual-v6.2.pdf)


## 如何修改白皮书 / How to edit the living whitepaper

白皮书采用 **Markdown 源文档 + GitHub Pages 发布页**：

1. 在线阅读：[whitepaper.html](https://mk60dn.github.io/Tender/whitepaper.html)
2. 查看源文档：[Tender-DAOQL-Data-Water-Whitepaper-v1.0.md](docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md)
3. 直接编辑：[Edit on GitHub](https://github.com/MK60DN/Tender/edit/main/docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md)

### 有仓库写权限的编辑

1. 登录 GitHub，打开上面的“Edit on GitHub”。
2. 修改 Markdown，提交到新分支并创建 Pull Request。
3. 至少一位维护者审核后合并。
4. 如修改影响对外博客，维护者同步更新 site/whitepaper.html 并触发 Pages 部署。

### 没有仓库写权限

- 点击 GitHub 页面的 **Fork**，在自己的副本中编辑，然后提交 Pull Request。
- 或使用 [白皮书修改 Issue 模板](https://github.com/MK60DN/Tender/issues/new?template=whitepaper_feedback.yml) 提出事实纠错、补充来源、结构调整或合规意见。

### 给陈天桥和合伙人开放编辑权限

仓库所有者进入：

**GitHub → Settings → Collaborators and teams → Add people → 选择 Write**

建议只授予 **Write**，不要默认授予 **Admin**。如仓库属于组织，可建立 **whitepaper-editors** Team 并授予 **Write** 权限。

### 编辑底线

- 区分“已实现”“已有基础”“目标架构”“研究假设”；
- 新数字必须注明样本、测试条件、来源和局限；
- 不把贡献积分写成投资品，不承诺升值或固定收益；
- 不写入学生、患者、受益人或合作机构的可识别隐私；
- 实质修改需更新版本号、日期和 Pull Request 说明。

完整流程见 [docs/COLLABORATION.md](docs/COLLABORATION.md)。

[![CI](https://github.com/MK60DN/Tender/actions/workflows/ci.yml/badge.svg)](https://github.com/MK60DN/Tender/actions/workflows/ci.yml)

> **EN** — Tender starts by gently understanding your mind, then turns that understanding into action in the world, mentalizing in relationships, and confirmed commitments in groups. It separates objective events, language evidence, subjective experience and optional Agent support.
>
> **中文** — Tender 从温柔了解你的心智开始，把理解转化为世界中的行动、人与人之间的心智化，以及群体中可确认的承诺和结果。系统严格区分客观事件、语言证据、主观体验和可选 Agent 支持。

## Why Tender / 为什么需要 Tender

| English | 中文 |
|---|---|
| One score is too late and too narrow to explain why learning breaks down. | 单一分数出现得太晚，也无法解释学习为什么卡住。 |
| Tender treats exams as periodic checks and treats behavior, language and outcomes as continuous evidence. | Tender 把考试视为定期检查，把行为、语言与结果视为连续证据。 |
| The goal is not to grade a person, but to support the next viable action and preserve long-term evidence. | 目标不是给人打分，而是支持下一个可执行动作，并保存长期成长证据。 |

## What it is / 它是什么

- **Three value loops / 三层价值回路**：self-understanding → action in the world → relational mentalizing and group outcomes. / 自我理解 → 世界行动 → 关系心智化与群体结果。
- **Mentalization layer / 心智化层**：turn authorized evidence into competing, reversible state hypotheses. / 把授权证据转化为竞争性、可撤回的状态假设。
- **Language evidence layer / 语言证据层**：extract emotion, uncertainty, avoidance, help-seeking and mentalizing signals with source spans. / 从话语中提取情绪、不确定性、回避、求助与心智化信号，并保留来源片段。
- **World tree / 世界树**：DAOQL roots → Agent Bridge trunk → five experience branches → local state axes → flowering and outcomes; shared branches require explicit consent. / DAOQL 根系 → Agent Bridge 树干 → 五类体验树枝 → 局部状态轴 → 开花与结果；共享枝必须获得明确授权。
- **Evidence-gated rhythm / 节律证据**：7/28-day windows control observation; a detected period must survive permutation and antiphase checks before it is reported. / 7/28 天窗口只负责观察与控制；检测到的周期必须通过置换与反相位检验后才能报告。
- **Dual-chain group backend / 双链路群聊后台**：self-models remain private; peer models are observer-owned hypotheses; shared views are scoped and revocable; group models read only public events and approved shared branches. / 自我模型保持私密；他者模型是观察者的关系假设；授权视图有范围且可撤回；群体模型只读群公开事件和已批准的共享枝。
- **Knowledge forest / 知识森林**：13 subjects, 1,075 K12 nodes, 875 majors, 319 course seeds and 1,016 occupations. / 连接 13 个学科、1,075 个知识节点、875 个专业、319 门课程与 1,016 个职业。
- **DAOQL event layer / DAOQL 事件层**：facts, provenance, causality, authorization and audit. / 保存事实、来源、因果、授权与审计。
- **Three UI modes / 三种界面模式**：solo focus, multi-person group chat and ambient assistance; users switch directly from the persistent three-part control. / 单人专注、多人协作群聊与环境辅助；用户可通过常驻三段切换器直接切换。
- **Agent system / Agent 系统**：fixed helpers, professional advisors, orchestration, a multi-Agent command center, a redacted experimental-model API path and an expert-Agent marketplace MVP. / 固定辅助、专业顾问、编排、多 Agent 作战大屏、脱敏实验模型 API 链路与专家 Agent 市场 MVP。
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
| Agent runtime / Agent 运行时 | fixed helpers, advisors, workbench, Agent command center, experimental API enrichment, marketplace MVP / 固定辅助、顾问、工作台、Agent 作战大屏、实验 API 增强、市场 MVP |
| Governance / 治理 | signed sessions, object authorization, audit hash chain, safety tickets / 签名会话、对象授权、审计哈希链、安全工单 |
| Tests / 测试 | 115 automated tests / 115 项自动测试 |

## Teaching site / 教学网站

双语教学网站位于 `site/`，包含 15 个模块、108 分钟、学习进度、语言切换与知识检查。FastAPI 在 `/guide/` 提供页面，GitHub Pages 由 `.github/workflows/pages.yml` 部署。

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

- Login / 登录：<http://127.0.0.1:8080/ui/login.html>
- Solo / 单人：<http://127.0.0.1:8080/ui/single.html>
- Multi-person / 多人：<http://127.0.0.1:8080/ui/multi.html>
- Ambient / 环境辅助：<http://127.0.0.1:8080/ui/ambient.html>
- World setup / 世界坐标：<http://127.0.0.1:8080/ui/world-setup.html>
- Language evidence / 语言证据层：<http://127.0.0.1:8080/ui/language.html>
- Knowledge forest / 知识森林：<http://127.0.0.1:8080/ui/knowledge.html>
- API docs / API 文档：<http://127.0.0.1:8080/docs>

`LLM_PROVIDER=mock` runs without an external model. Copy `.env.example` to `.env` only when connecting a model provider. / 默认 mock 模式无需外部模型；接入真实模型时再复制 `.env.example`。

## Tests / 测试

```bash
python agent_layer/tests/run_all.py
```

Expected baseline / 当前基线：`passed 136 tests`；完整 `pytest` 当前为 139 通过、1 个可选重媒体测试跳过。

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
agent_layer/app/group_chat.py  dual-chain group backend / 双链路群聊后台
knowledge_data/    subject, major, course and career databases / 学科、专业、课程、职业数据库
experiments/       selected reproducible research code / 精简可复现研究代码
docs/whitepaper/   Whitepaper V2.2: TeX, PDF, Word / 白皮书 V2.2
docs/product/      product and user manuals / 产品与用户手册
docs/research/     evidence and validation reports / 证据与验证报告
site/               bilingual teaching website / 双语教学网站
```

## Screen context MCP / 界面上下文 MCP

桌面弹幕可以在用户逐次授权后读取当前可见窗口，并在本机完成脱敏与任务归因。MCP 提供授权、读取、截图和立即撤销工具；原文和截图不写入 DAOQL。详见 [Screen Context MCP](docs/SCREEN_CONTEXT_MCP.md)。 / The desktop danmaku layer can read currently visible windows after scoped, revocable consent. Text and screenshots remain local; only coarse task hints reach the planner. See [Screen Context MCP](docs/SCREEN_CONTEXT_MCP.md).
## Media plugins / 多媒体插件

桌面弹幕可读取用户选择的图片、音频和视频：本地 OCR、Whisper 语音转写、视频关键帧分析、本地语音播报与可配置视觉模型。插件目录、来源、许可证与隐私边界见 [Media Plugins](docs/MEDIA_PLUGINS.md)。 / User-selected images, audio and video can be processed with local OCR, Whisper transcription, video-frame analysis, local TTS and an optional vision model. See [Media Plugins](docs/MEDIA_PLUGINS.md) for sources, licenses and boundaries.
## Data and safety / 数据与安全

- 26 of 875 majors currently have course-level seeds. / 875 个专业中目前仅 26 个有课程级种子。
- High-risk language signals enter a deterministic human-escalation path. / 高风险语言信号进入确定性人工升级路径。
- Runtime databases, tenant data, `.env` and session secrets are not committed. / 运行数据库、租户数据、`.env` 与会话密钥不会提交。
- See [data licenses](docs/DATA_LICENSES.md), [privacy and safety](docs/PRIVACY_AND_SAFETY.md) and [research claims](docs/RESEARCH_CLAIMS.md). / 详见数据许可证、隐私安全与研究边界。

## Documentation / 文档

- [Whitepaper V2.2 / 白皮书 V2.2](docs/whitepaper/Tender-Whitepaper-v2.2.pdf)
- [Product manual / 产品手册](docs/product/Tender-Product-Manual-v7.2.pdf)
- [User guide / 用户手册](docs/product/Tender-User-Guide-v7.2.pdf)
- [Central thesis / 中心主旨](docs/product/Tender-Central-Thesis.md)

## License / 许可证

**PolyForm Noncommercial License 1.0.0**

Personal, educational, research and other noncommercial use is permitted.
Commercial use is prohibited without separate written permission.

允许个人、教育、研究和其他非商业用途。未经另行书面许可，禁止商业化使用。

This is source-available, not an OSI-approved open-source license. See [LICENSE](LICENSE) and [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md). / 这是源码可见许可证，不是 OSI 批准的开源许可证。
