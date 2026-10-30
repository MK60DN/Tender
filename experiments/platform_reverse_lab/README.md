# Platform Reverse Lab

这是一个**完全独立**的实验目录，不属于 Tender/DaoQL 主链路，可直接删除或归档回退。

## 目标

把 Tender 的群体心智化状态用于抖音、视频号、小红书、知乎的推荐策略实验。

- 观众群体对齐、多样性、互惠、网络密度、共同基础、视角错位；
- 平台可观测行为信号：完播、停留、点赞、评论、分享、收藏、关注、搜索匹配、负反馈；
- 输出内容优化动作、预期相对得分、内容日历和招生漏斗投影。

## 边界

不是读取平台私有算法，不是刷量、控制账号、绕过风控或制造虚假互动。

这里的"逆向"定义为：

> 用公开可观测的互动信号，建立一个可校准的排序先验，帮助内容创作者做更符合平台机制的内容优化。

全部平台权重初始标记为 `prior_only`。只有接入用户自己的真实发布数据后，才能进入标定。

## 已接入的两份文档

| 文档 | 用途 | 处理方式 |
|---|---|---|
| 万象学院《校门口IP口播文案总汇》 | 真实内容库（58 条选题） | PDF 文本层直接提取 + 规则标注 |
| 万象学院《教培线上招生白皮书》 | 平台口径、数据基准、招生漏斗 | 图片版 PDF，本地 OCR（RapidOCR）67 页 |

两份文档都是**第三方教培招生资料**，其中的平台权重、CES 公式、数据基准均未经平台确认，在本实验里只作为"待验证先验"。

### 从白皮书提取的关键口径（均标记 `document_claimed_unverified`）

- 抖音倾向权重：收藏率 35% > 复访率 25% > 铁粉互动 20% > 5秒完播 15% > 点赞 5%
- 小红书 CES 公式：点赞×1 + 收藏×1 + 评论×4 + 转发×4 + 关注×8
- 短视频基准：5秒完播 30% 基础 / 40% 较好 / 50% 优秀 / 60% 热门
- 直播基准：商品点击率最低 3%、商品转化率最低 5%、`GMV = PV × GPM ÷ 1000`
- 内容配比建议：70% 干货清单 + 20% 校长IP口播 + 10% 课堂实拍

### 明确排除的操作

白皮书里包含以下操作，**不进入本实验的任何流程**：买特定号段手机卡规避风控、连续 7 天刷同品类视频养号、组织 50 人点赞完播、直播间水军配合逼单、道德绑架式成交话术、绝对化效果承诺、数字人批量同质化量产。

## 目录

```text
configs/platform_profiles.json             实验口径平台先验权重
configs/platform_profiles_document.json    白皮书口径平台权重（仅抖音/小红书有依据）
configs/document_priors.json               白皮书里的平台声明与数据基准
configs/enrollment_funnel.json             招生漏斗系数与依据
configs/whitepaper_extract.json            白皮书逐块"采用/排除"分级
configs/content_library.json               58 条真实文案的结构化内容库

platform_reverse_lab/models.py             群体状态、内容方案、评分结果
platform_reverse_lab/simulator.py          推荐排序和增长模拟
platform_reverse_lab/strategy.py           内容优化动作枚举
platform_reverse_lab/reporting.py          基础报告和图表
platform_reverse_lab/content_library.py    真实文案 -> ContentPlan 的规则映射
platform_reverse_lab/library_reporting.py  内容库排序、日历、热力图
platform_reverse_lab/dual_prior.py         实验口径 vs 文档口径 排序对比
platform_reverse_lab/prior_compare.py      两套权重的量化差异
platform_reverse_lab/funnel.py             招生漏斗投影
platform_reverse_lab/integration.py        整合报告

tools/build_content_library.py             从原始文案文本重建内容库
data/                                      两份文档的原始／OCR 文本
run_demo.py                                基础演示入口
run_content_library.py                     内容库排期入口
run_integration.py                         整合报告入口
outputs/                                   全部产物
```

## 运行

```powershell
$env:PYTHONPATH='D:\Tender\experiments\platform_reverse_lab'
$py = 'D:\Tender\Tender-Demo\backend\.venv\Scripts\python.exe'
$base = 'D:\Tender\experiments\platform_reverse_lab'

# 1) 基础平台策略演示
& $py "$base\run_demo.py" all '高中英语语法填空'

# 2) 重建内容库（源文件在 data\wanxiang_scripts_source.txt）
& $py "$base\tools\build_content_library.py"

# 3) 内容库排序 + 30 天日历 + 图表
& $py "$base\run_content_library.py"

# 4) 实验口径 vs 文档口径 排序对比
& $py -m platform_reverse_lab.dual_prior

# 5) 整合报告（含招生漏斗）
& $py "$base\run_integration.py"
```

## 输出

```text
outputs/demo_report.md                          基础策略报告
outputs/content_library/content_library_report.md  内容库平台适配报告
outputs/content_library/content_calendar.md        30 天排期
outputs/content_library/dual_prior_comparison.md   双口径对比
outputs/integration/INTEGRATION_REPORT.md          整合报告（主交付物）
```

## 重要的诚实声明

1. 平台权重、漏斗系数全部是**先验**，没有接入真实账号数据，不能当作预测。
2. 白皮书口径与实验口径的差异越大，越说明该处必须用真实数据标定（见 `dual_prior_comparison.md`）。
3. 内容库的字段是**规则自动标注**（`rule_tagged_unverified`），未逐条人工复核。
4. `aesthetic_score` 无法从文本测量，固定为 0.50。

## 回退

删除或归档 `D:\Tender\experiments\platform_reverse_lab` 即可，不影响现有 Tender/DaoQL。
