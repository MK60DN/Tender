# Tender 正式文档索引

更新时间：2026-10-31
当前仓库版本：1.7.0

## 核心文档

| 版本 | 文件 | 页数 | 内容 |
|---|---|---:|---|
| 项目白皮书 V1.7 | [PDF](../whitepaper/Tender-Whitepaper-v1.7.pdf) · [Word](../whitepaper/Tender-Whitepaper-v1.7.docx) | 43 | 预测加工、心智化、严格八功能态度、世界树、共享枝与黄金比边界 |
| 产品手册 V6.21 | [PDF](Tender-Product-Manual-v6.21.pdf) | 57 | 世界入口、大五脉搏、世界树 API、Agent 支持、角色、数据契约和验收 |
| 用户手册 V6.9 | [PDF](Tender-User-Guide-v6.9.pdf) | 24 | 第一次启用、世界入口评估、大五脉搏、弹幕、隐私与安全 |
| 零基础教学手册 V5.4 | [PDF](../teaching/Tender-Teaching-Manual-v5.4.pdf) | 184 | 从零理解 DAOQL、世界树、八功能态度、大五脉搏、Agent 与三种交付 |

## 研究与边界

- [研究主张与限制](../RESEARCH_CLAIMS.md)
- [神经学习证据与数据源 V1.0](../research/Tender-Neuro-Learning-Evidence-v1.0.pdf)
- 首次预检测与世界入口：见产品手册 V6.21 第 13.7 节
- [全功能验证 V1.0](../research/Tender-Full-Feature-Validation-v1.0.pdf)
- [长期多阶段多角色测试 V4.0](../research/Tender-Longitudinal-Multi-Role-v4.0.pdf)
- [博弈论与机制设计 V1.2](../strategy/Tender-Game-Theory-Mechanism-Design-v1.2.pdf)
- [隐私与安全](../PRIVACY_AND_SAFETY.md)
- [数据许可证](../DATA_LICENSES.md)

## 当前实现事实

- 统一 24 题八功能态度测评，每种功能 3 题并记录一致性；
- 用户界面不显示 MBTI 字母或荣格功能代码；
- 世界入口分为客观优先、主观优先和桥接优先；
- 大五包含 20 题基线、10 题脉搏和基线变化支持；
- `GET /world-tree/{student_id}` 提供根系、树干、五类树枝、11 个体验节点、开花、结果与共享枝边界；
- 教学网站为 10 个中英双语模块，不包含公式；
- 全量自动测试 95 项通过；
- 黄金比仅作为设计假设，不用于人格评分、关系匹配或效果承诺。

## 版本规则

- 活动目录只保留当前正式版本。
- 历史版本只保留在 Git 标签和 `CHANGELOG.md` 中。
- 同一文件路径始终由当前版本替换，不并列堆放旧版本。