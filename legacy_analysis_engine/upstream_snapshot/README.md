# Tender

**A research-grade lifelong learning and mentalization system**  
**研究型终身学习与心智化支持系统**

[English README](README.en.md) · [中文 README](README.zh-CN.md)

## Start here / 从这里开始

> 本机正在运行 Tender 时，以下 Local 链接可以直接打开。完整源码和 PDF 同步到 GitHub 后，Repo 链接同样有效。

| Resource | Open now / 立即可用 | Repository / 仓库路径 |
|---|---|---|
| **Teaching website / 教学网站** | [Local course](http://127.0.0.1:8080/guide/) · [GitHub Pages](https://mk60dn.github.io/Tender/) | [site](site/) |
| **Whitepaper V1.5 / 白皮书 V1.5** | [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Whitepaper-v1.5.pdf) | [PDF](docs/whitepaper/Tender-Whitepaper-v1.5.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v1.5.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v1.5.tex) |
| **Product manual / 产品手册 V6.19** | [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Product-Manual-v6.19.pdf) | [PDF](docs/product/Tender-Product-Manual-v6.19.pdf) |
| **User guide / 用户手册 V6.7** | [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-User-Guide-v6.7.pdf) | [PDF](docs/product/Tender-User-Guide-v6.7.pdf) |
| **Teaching manual / 零基础教学手册 V5.2** | [Local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Teaching-Manual-v5.2.pdf) | [PDF](docs/teaching/Tender-Teaching-Manual-v5.2.pdf) |

The teaching site is an eight-module bilingual course organized around the whitepaper architecture: world and black-box APIs → DAOQL → limited observation → Agent Bridge → life-tree canopy → flowering, outcomes and the knowledge forest. It intentionally contains no mathematical formulas.

教学网站包含 8 个中英文模块，按“世界与黑盒 API → DAOQL → 有限接触面 → Agent Bridge → 生命树树冠 → 开花、结果与知识森林”的白皮书架构建成，不包含任何数学公式。

## What Tender is / 它是什么

Tender forms revisable hypotheses about attention, cognitive load, motivation and action friction from authorized behavior, language and real outcomes. Objective events, language evidence, subjective experience and optional Agent support remain separate layers.

Tender 在授权后从行为、语言和真实结果中形成关于注意、认知负荷、动机与行动阻力的可更正假设，并严格区分客观事件、语言证据、主观体验与可选 Agent 支持。

## Boundaries / 边界

Tender is not diagnosis, mind reading, or a guarantee of scores, admission or employment. Language evidence cannot determine mastery, personality or clinical state. Synthetic and benchmark results are not real-world causal evidence.

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

Then open:

- App / 主应用：<http://127.0.0.1:8080/ui/>
- Teaching course / 教学课程：<http://127.0.0.1:8080/guide/>
- Language evidence / 语言证据层：<http://127.0.0.1:8080/ui/language.html>
- Knowledge forest / 知识森林：<http://127.0.0.1:8080/ui/knowledge.html>

## License / 许可证

**PolyForm Noncommercial License 1.0.0**

Permitted for personal, educational, research and other noncommercial purposes. Commercial use is prohibited without separate written permission. This is source-available, not an OSI-approved open-source license.

允许个人、教育、研究和其他非商业用途；未经另行书面许可，禁止商业化使用。
