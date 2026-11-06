# Tender Research & Modeling

> **最新更新 / Latest update · 2026-11-06**
>
> [Tender 建模零基础课（12 篇）](https://github.com/MK60DN/Tender/blob/main/docs/teaching/modeling-zero-basics/README.md) 已按自然讲解口吻重写，并只保留正文与站点，发布流程已移除。
> 教学站点源码：[Tender-Product site/modeling-teaching](https://github.com/MK60DN/Tender-Product/tree/main/site/modeling-teaching)。

**Whitepapers, research experiments, knowledge databases and reference models.**
**白皮书、研究实验、知识数据库与参考模型。**

> The runnable product, UI, Agent runtime, desktop overlay, teaching website, manuals and deployment configuration now live in [MK60DN/Tender-Product](https://github.com/MK60DN/Tender-Product).
>
> 可运行产品、UI、Agent 运行时、桌面弹层、教学网站、手册与部署配置已迁至 [Tender-Product](https://github.com/MK60DN/Tender-Product)。

## Start here / 从这里开始

- **DAOQL living whitepaper / 数据活水白皮书**：[Read online](https://mk60dn.github.io/Tender-Whitepaper/whitepaper.html) · [GitHub source](https://github.com/MK60DN/Tender/blob/main/docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.1.md) · [Markdown](docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.1.md) · [PDF](docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.1.pdf)
- **Tender Whitepaper V2.2 / Tender 白皮书 V2.2**：[PDF](docs/whitepaper/Tender-Whitepaper-v2.2.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v2.2.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v2.2.tex)
- **Research reports / 研究报告**：[Golden-bias](docs/research/Tender-Golden-Bias-Experiment-v1.0.pdf) · [Rhythm and phase](docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf) · [Neuro-learning evidence](docs/research/Tender-Neuro-Learning-Evidence-v1.0.pdf) · [Preassessment](docs/research/Tender-Preassessment-v1.1.pdf)
- **Reference models / 参考模型**：[modeling/](modeling/) · [modeling/app/](modeling/app/)
- **Knowledge databases / 知识数据库**：[knowledge_data/](knowledge_data/)
- **Reproducible experiments / 可复现实验**：[experiments/](experiments/)

## Research scope / 研究范围

- predictive processing, mentalization and world-tree modeling;
- Tender state, preassessment and cognitive constructs;
- dynamic golden-bias regulation and rhythm evidence;
- knowledge forest, subject databases, majors, courses and careers;
- language evidence and uncertainty boundaries;
- mechanism design, benchmarks and decision loops;
- reproducible simulations and claim-boundary reports.

## Modeling package / 建模包

Create a Python environment and expose the reference package:

    pip install -r requirements-research.txt
    # Windows PowerShell
    $env:PYTHONPATH="modeling;experiments"
    # macOS / Linux
    export PYTHONPATH="modeling:experiments"

Then modules are available as:

    from app.tender import TenderEngine
    from app.tender_models import TenderState
    from app.golden_bias import DynamicGoldenBiasRegulator

The reference package is extracted from Tender commit e917545. It is not a deployable application; the runnable implementation is in Tender-Product.

## Repository map / 仓库结构

    docs/whitepaper/       whitepapers and evidence boundaries / 白皮书
    docs/research/         research reports / 研究报告
    experiments/           reproducible simulations and benchmarks / 实验
    knowledge_data/        subject, major, course, career databases / 知识数据库
    modeling/              reference model code and schemas / 参考模型
    docs/COLLABORATION.md  whitepaper collaboration / 白皮书协作

## Validation / 校验

    python scripts/verify_research.py
    python scripts/check_modeling_imports.py

This checks the presence and integrity of the whitepaper set, research reports, key experiment outputs, knowledge-database counts and reference model package.

## Data and claim boundaries / 数据与主张边界

- Synthetic and benchmark results are not proof of real-world educational effect.
- Language evidence does not determine mastery, personality or clinical state.
- High-risk signals require deterministic human escalation.
- No raw learner, family, health or identity data belongs in this repository.
- No claim of guaranteed score improvement, admission or employment.

See [data licenses](docs/DATA_LICENSES.md) and [research claims](docs/RESEARCH_CLAIMS.md).

## Repository split / 仓库拆分

- Research and modeling: this repository.
- Product implementation: https://github.com/MK60DN/Tender-Product
- Pre-split rollback tag: pre-product-split-2026-11-04

## License / 许可证

**PolyForm Noncommercial License 1.0.0**

Personal, educational, research and other noncommercial use is permitted. Commercial use is prohibited without separate written permission.
