# Tender

**研究型终身学习与心智化支持系统**

[双语首页](README.md) · [English](README.en.md)

## 从这里开始

- [教学网站](https://mk60dn.github.io/Tender/) · [本地课程](http://127.0.0.1:8080/guide/) · [站点源码](site/)
- [白皮书 PDF](docs/whitepaper/Tender-Whitepaper-v1.5.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v1.5.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v1.5.tex)
- [产品手册](docs/product/Tender-Product-Manual-v6.19.pdf) · [用户手册](docs/product/Tender-User-Guide-v6.7.pdf)


[![CI](https://github.com/MK60DN/Tender/actions/workflows/ci.yml/badge.svg)](https://github.com/MK60DN/Tender/actions/workflows/ci.yml)

> 温柔地了解您的心智。Tender 在明确授权下，从行为、语言和真实结果中形成关于注意、认知负荷、动机与行动阻力的可更正假设。

## 为什么需要 Tender

- 单一分数出现得太晚，也无法解释学习为什么卡住。
- Tender 把考试视为定期检查，把行为、语言与结果视为连续证据。
- 目标不是给人打分，而是支持下一个可执行动作，并保存长期成长证据。

## 核心模块

- **心智化层**：形成竞争性、可撤回的状态假设。
- **语言证据层**：保留来源片段，识别情绪、不确定性、回避、求助和心智化信号。
- **知识森林**：连接 13 个高中学科、1,075 个知识节点、875 个本科专业、319 门课程和 1,016 个职业。
- **DAOQL 事件层**：保存事实、来源、因果、授权与审计。
- **Agent 系统**：固定辅助、专业顾问、工作台编排与专家 Agent 市场 MVP。

## 边界

Tender 不是心理或医学诊断工具，也不是“读心”系统。语言证据不能单独决定知识掌握度、人格或临床状态。合成实验与公开基准结果不等于真实教育效果。

## 教学网站

双语课程位于 `site/`。FastAPI 在 `/guide/` 提供页面，GitHub Pages 由 `.github/workflows/pages.yml` 部署。

## 快速开始

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

打开：<http://127.0.0.1:8080/ui/>

## 测试

```bash
python agent_layer/tests/run_all.py
```

当前基线：`passed 93 tests`。

## 文档

- [项目白皮书 V1.5](docs/whitepaper/Tender-Whitepaper-v1.5.pdf)
- [产品手册](docs/product/Tender-Product-Manual-v6.19.pdf)
- [用户手册](docs/product/Tender-User-Guide-v6.7.pdf)
- [研究边界](docs/RESEARCH_CLAIMS.md)

## 许可证

PolyForm Noncommercial License 1.0.0。允许个人、教育、研究和其他非商业用途；未经另行书面许可，禁止商业化使用。本许可证不是 OSI 批准的开源许可证。


