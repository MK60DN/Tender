# Tender 正式文档索引

更新时间：2026-11-01
当前仓库版本：2.0.0

## 核心文档

| 版本 | 文件 | 页数 | 内容 |
|---|---|---:|---|
| 项目白皮书 V2.0 | [PDF](../whitepaper/Tender-Whitepaper-v2.0.pdf) · [Word](../whitepaper/Tender-Whitepaper-v2.0.docx) | 48 | 预测加工、心智化、八功能态度、世界树、动态黄金比、相位与周期证据、双链路群聊 |
| 产品手册 V7.0 | [PDF](Tender-Product-Manual-v7.0.pdf) | 61 | 世界入口、相位与周期证据、双链路群聊、Agent、数据契约和验收 |
| 用户手册 V7.0 | [PDF](Tender-User-Guide-v7.0.pdf) | 26 | 世界入口、群聊授权、他者假设、共享枝、弹幕与隐私 |
| 零基础教学手册 V6.0 | [PDF](../teaching/Tender-Teaching-Manual-v6.0.pdf) | 186 | DAOQL、世界树、动态黄金比、周期检测、双链路群聊、Agent 与三种交付 |

## 研究与证据

- [动态黄金比偏置律实验 V1.0](../research/Tender-Golden-Bias-Experiment-v1.0.pdf)
- [节律相位与周期证据实验 V1.0](../research/Tender-Rhythm-Phase-Experiment-v1.0.pdf)
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
- 从 84 天事件序列估计 5—28 天周期，使用置换零分布和反相位证据；
- 周期状态包含证据不足、无稳定周期、候选周期和稳定周期，候选周期不生成日程；
- 当前相位包含吸收、整合、表达、校准、恢复或低活动；
- 单人链路维护自我模型，群聊链路处理群公开事件、授权视图和共享枝；
- 他者模型是观察者拥有的关系假设，不读取对方私密模型；
- 授权视图带用途、有效期和撤回；共享枝需全部参与者批准；
- Agent 只能生成群聊草稿，不自动发送；
- `GET /world-tree/{student_id}` 和 `GET /golden-bias/{student_id}` 已接入；
- 四臂合成实验完成：每臂 1,000 人、84 天、配对 bootstrap；
- 教学网站为 13 个中英双语模块，不包含公式；
- 全量自动测试 114 项通过。

## 实验结论边界

动态黄金比相对不调节提高行动恢复和带内时间；相对固定 50:50 用更少提示保持相近恢复；但严格带内时间和创造后校准并不全面优于简单规则。节律实验在合成数据中得到 95.3% 的周期检出率、93.3% 的容忍范围内估计、0.45 天平均绝对误差、7.0% 的非周期稳定周期误报率和 100% 的五类受控相位分类准确率。两项实验都是合成验证，不是真人教育、周期诊断或临床因果证据，也不能把黄金比或候选周期变成每日 KPI、人格评分、关系匹配分或固定日程。