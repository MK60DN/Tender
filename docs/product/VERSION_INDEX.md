# Tender 正式文档索引

更新时间：2026-11-01
当前仓库版本：1.8.0

## 核心文档

| 版本 | 文件 | 页数 | 内容 |
|---|---|---:|---|
| 项目白皮书 V1.8 | [PDF](../whitepaper/Tender-Whitepaper-v1.8.pdf) · [Word](../whitepaper/Tender-Whitepaper-v1.8.docx) | 45 | 预测加工、心智化、八功能态度、世界树、动态黄金比偏置律 |
| 产品手册 V6.22 | [PDF](Tender-Product-Manual-v6.22.pdf) | 58 | 世界入口、大五脉搏、动态偏置带、Agent、数据契约和验收 |
| 用户手册 V6.10 | [PDF](Tender-User-Guide-v6.10.pdf) | 25 | 世界入口、大五脉搏、学习/创造节律、弹幕与隐私 |
| 零基础教学手册 V5.5 | [PDF](../teaching/Tender-Teaching-Manual-v5.5.pdf) | 185 | DAOQL、世界树、动态黄金比、Agent 与三种交付 |

## 研究与证据

- [动态黄金比偏置律实验 V1.0](../research/Tender-Golden-Bias-Experiment-v1.0.pdf)
- [研究主张与限制](../RESEARCH_CLAIMS.md)
- [神经学习证据与数据源 V1.0](../research/Tender-Neuro-Learning-Evidence-v1.0.pdf)
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
- 动态黄金比使用 7/28 天窗口、38.2/61.8 弹性带、证据门槛和滞回；
- 同时观察投入比、新异比和创造后 72 小时校准比；
- `GET /world-tree/{student_id}` 和 `GET /golden-bias/{student_id}` 已接入；
- 四臂合成实验完成：每臂 1,000 人、84 天、配对 bootstrap；
- 教学网站为 11 个中英双语模块，不包含公式；
- 全量自动测试 100 项通过。

## 实验结论边界

动态黄金比相对不调节提高行动恢复和带内时间；相对固定 50:50 用更少提示保持相近恢复；但严格带内时间和创造后校准并不全面优于简单规则。该实验是合成机制测试，不是真人教育或临床因果证据，也不能把黄金比变成每日 KPI、人格评分或关系匹配分。