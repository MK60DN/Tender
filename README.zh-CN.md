# Tender

**连接自我、世界、他人心智与共同结果的终身学习系统**

[双语首页](README.md) · [English](README.en.md)

## 从这里开始

- **One-click backend / 一键后端**：[GitHub Codespaces](https://codespaces.new/MK60DN/Tender?quickstart=1) · [Deploy to Render](https://render.com/deploy?repo=https://github.com/MK60DN/Tender) · [Deployment guide](docs/DEPLOYMENT.md)
- [教学网站](https://mk60dn.github.io/Tender/) · [本地课程](http://127.0.0.1:8080/guide/) · [站点源码](site/)
- [白皮书本地 PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Whitepaper-v2.2.pdf) · [仓库 PDF](docs/whitepaper/Tender-Whitepaper-v2.2.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v2.2.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v2.2.tex)
- [产品手册本地 PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Product-Manual-v7.2.pdf) · [Word](docs/product/Tender-Product-Manual-v7.2.docx) · [用户手册本地 PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-User-Guide-v7.2.pdf) · [Word](docs/product/Tender-User-Guide-v7.2.docx) · [零基础教学手册本地 PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Teaching-Manual-v6.2.pdf)


[![CI](https://github.com/MK60DN/Tender/actions/workflows/ci.yml/badge.svg)](https://github.com/MK60DN/Tender/actions/workflows/ci.yml)

> 温柔地了解您的心智，也帮助您更好地进入世界、理解他人、参与协作。Tender 把自我理解转化为真实行动，把关系中的理解转化为可授权、可协商、可撤回的共享。

## 为什么需要 Tender

- 单一分数出现得太晚，也无法解释学习为什么卡住。
- Tender 把考试视为定期检查，把行为、语言与结果视为连续证据。
- 目标不是给人打分，而是支持下一个可执行动作，并保存长期成长证据。

## 核心模块

- **三层价值回路**：自我理解、世界行动、关系协商与群体结果。
- **心智化层**：形成竞争性、可撤回的状态假设。
- **语言证据层**：保留来源片段，识别情绪、不确定性、回避、求助和心智化信号。
- **世界树**：DAOQL 根系、Agent Bridge 树干、五类体验树枝、局部状态轴、开花与结果；共享枝必须获得明确授权。
- **知识森林**：连接 13 个高中学科、1,075 个知识节点、875 个本科专业、319 门课程和 1,016 个职业。
- **DAOQL 事件层**：保存事实、来源、因果、授权与审计。
- **三种界面模式**：单人专注、多人协作群聊与环境辅助，通过常驻三段切换器直接切换。
- **Agent 系统**：固定辅助、专业顾问、工作台编排、多 Agent 作战大屏、脱敏实验模型 API 链路与专家 Agent 市场 MVP。

## 群聊双链路

每个成员保留自己的完整私密模型；他者模型属于观察者，只使用群公开互动与对方授权摘要；共享枝需要全部参与者批准，Agent 不自动在群里发言。

## 多媒体与界面上下文

Tender 可以处理用户选择的图片、音频与视频：本地 OCR、Whisper 转写、视频关键帧分析、本地语音生成，均提供独立插件。桌面弹幕还支持逐次授权读取当前可见窗口。来源、许可证与隐私边界见 [多媒体插件](docs/MEDIA_PLUGINS.md) 与 [界面上下文 MCP](docs/SCREEN_CONTEXT_MCP.md)。
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

打开登录：<http://127.0.0.1:8080/ui/login.html>。完成“登录 → 世界坐标 → 心智测评”后：单人 <http://127.0.0.1:8080/ui/single.html>、多人 <http://127.0.0.1:8080/ui/multi.html>、环境辅助 <http://127.0.0.1:8080/ui/ambient.html>。每个登录后页面右上角都有账号菜单，可退出账号、删除当前学习者数据或关闭 Tender 服务。

## 测试

```bash
python agent_layer/tests/run_all.py
```

当前基线：`passed 136 tests`；完整 `pytest` 当前为 139 通过、1 个可选重媒体测试跳过。

## 文档

- [项目白皮书 V2.2](docs/whitepaper/Tender-Whitepaper-v2.2.pdf)
- [节律相位与周期证据实验 V1.0](docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf)
- [产品手册](docs/product/Tender-Product-Manual-v7.2.pdf)
- [用户手册](docs/product/Tender-User-Guide-v7.2.pdf)
- [研究边界](docs/RESEARCH_CLAIMS.md)

## 许可证

PolyForm Noncommercial License 1.0.0。允许个人、教育、研究和其他非商业用途；未经另行书面许可，禁止商业化使用。本许可证不是 OSI 批准的开源许可证。

