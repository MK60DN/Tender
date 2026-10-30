# Tender

**A research-grade lifelong learning and mentalization system**  
**研究型终身学习与心智化支持系统**

[English README](README.en.md) · [中文 README](README.zh-CN.md)

[![Teaching Site](https://img.shields.io/badge/Course-Tender%20Academy-176b50)](https://mk60dn.github.io/Tender/)
[![License](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-d4a557)](LICENSE)

> **EN** — Tender learns, with explicit authorization, from behavior, language and real outcomes to form revisable hypotheses about attention, cognitive load, motivation and friction. It separates objective events, language evidence, subjective experience and optional Agent support.
>
> **中文** — Tender 在明确授权下，从行为、语言和真实结果中形成关于注意、认知负荷、动机与行动阻力的可更正假设。系统严格区分客观事件、语言证据、主观体验和可选 Agent 支持。

## Start here / 从这里开始

| Resource | Entry |
|---|---|
| **Teaching website / 教学网站** | [GitHub Pages](https://mk60dn.github.io/Tender/) · [Source](https://github.com/MK60DN/Tender/tree/main/site) · [Local course](http://127.0.0.1:8080/guide/) |
| **Whitepaper V1.5 / 白皮书 V1.5** | [PDF](docs/whitepaper/Tender-Whitepaper-v1.5.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v1.5.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v1.5.tex) |
| **Product manual / 产品手册** | [PDF](docs/product/Tender-Product-Manual-v6.19.pdf) |
| **User guide / 用户手册** | [PDF](docs/product/Tender-User-Guide-v6.7.pdf) |

The teaching site is a self-contained bilingual course with eight modules, progress storage and knowledge checks. It intentionally contains no mathematical formulas. GitHub Pages must use **GitHub Actions** as its source once; `.github/workflows/pages.yml` handles later deployments automatically.

教学网站是一个完整的双语课程，包含 8 个模块、学习进度和知识检查，不包含任何数学公式。首次使用时需要在仓库 `Settings → Pages` 中选择 **GitHub Actions** 作为来源，之后会自动部署。

## Why Tender / 为什么需要 Tender

- A single score arrives late and explains too little. / 单一分数出现得太晚，也无法解释学习为什么卡住。
- Tender treats exams as periodic checks and behavior, language and outcomes as continuous evidence. / Tender 把考试视为定期检查，把行为、语言与结果视为连续证据。
- The goal is not to grade a person, but to support the next viable action and preserve long-term evidence. / 目标不是给人打分，而是支持下一个可执行动作，并保存长期成长证据。

## Core layers / 核心层

- **Mentalization / 心智化**：competing, reversible hypotheses about attention, load, motivation and relationships. / 对注意、负荷、动机与关系形成竞争性、可撤回的假设。
- **Language evidence / 语言证据**：source-grounded signals such as emotion, uncertainty, avoidance, help-seeking and mentalizing. / 保留来源的情绪、不确定性、回避、求助与心智化信号。
- **DAOQL / 客观事件层**：facts, provenance, causality, authorization and audit. / 保存事实、来源、因果、授权与审计。
- **Knowledge forest / 知识森林**：13 subjects, 1,075 nodes, 875 majors, 319 course seeds and 1,016 occupations. / 13 个学科、1,075 个节点、875 个专业、319 门课程与 1,016 个职业。
- **Agent collaboration / Agent 协作**：fixed helpers, advisors, workbench orchestration and an expert-Agent marketplace MVP. / 固定辅助、专业顾问、工作台编排与专家 Agent 市场 MVP。

## Boundaries / 边界

Tender is not diagnosis, mind reading, or a guarantee of score, admission or employment outcomes. Language evidence does not determine mastery, personality or clinical state. Synthetic and benchmark results are not real-world causal evidence.

Tender 不是诊断，不是读心，也不承诺提分、录取或就业。语言证据不能单独决定掌握度、人格或临床状态。合成与基准结果不等于真实因果证据。

## Quick start / 快速开始

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate   # macOS / Linux

pip install -r requirements-dev.txt
cd agent_layer
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

- App / 主应用：<http://127.0.0.1:8080/ui/>
- Teaching course / 教学课程：<http://127.0.0.1:8080/guide/>
- Language evidence / 语言证据层：<http://127.0.0.1:8080/ui/language.html>
- Knowledge forest / 知识森林：<http://127.0.0.1:8080/ui/knowledge.html>

## Repository map / 仓库结构

```text
agent_layer/       runnable app, Agents, UI and tests
knowledge_data/    subject, major, course and career databases
experiments/       selected research code and compact results
site/              bilingual teaching website
docs/whitepaper/   Whitepaper V1.5
docs/product/      product and user manuals
docs/research/     evidence and validation reports
```

## License / 许可证

**PolyForm Noncommercial License 1.0.0**

Personal, educational, research and other noncommercial use is permitted. Commercial use is prohibited without separate written permission. This is source-available, not an OSI-approved open-source license.

允许个人、教育、研究和其他非商业用途。未经另行书面许可，禁止商业化使用。详见 [LICENSE](LICENSE) 与 [COMMERCIAL_LICENSE.md](COMMERCIAL_LICENSE.md)。
