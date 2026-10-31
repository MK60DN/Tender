# Tender Advisor Bench 公开数据建模报告

日期：2026-10-20  
目录：`D:\Tender\experiments\advisor_bench`

## 1. 结论

本轮把宿管角色拆分为五类专业顾问模型：

| 顾问 | 数据 | 任务 | 当前结果 |
|---|---|---|---|
| 健康顾问 | NHANES 2017–2018 | 高血压筛查代理 | AUC 0.7235；属于弱到中等基线 |
| 营养顾问 | NHANES 2017–2018 + Nutrition5k | 0–100 营养模式评分 | MAE 3.34，RMSE 5.92，R² 0.8844 |
| 神经认知顾问 | UCLA CNP / OpenNeuro ds000030 | 认知画像聚类 | 272 人，3 个画像 |
| 心理学顾问 | ds000030 问卷量表 | 支持信号聚类 | 272 人，3 个支持等级 |
| 学习科学顾问 | Tender + 上述模型 | 透明融合与解释 | 无监督量子认知标签，不做伪训练 |

所有模型只用于筛查、解释、教学支持和转介提示，不用于疾病诊断、分班、处分或替代专业人员。

## 2. 数据来源

### 2.1 NHANES 2017–2018

- 来源：CDC / NCHS NHANES。
- 文件：DEMO、BMX、BPX、SLQ、PAQ、DR1TOT、DR2TOT。
- 用途：
  - 健康：年龄、性别、BMI、腰围、睡眠、活动、膳食概括预测平均血压升高代理；
  - 营养：由纤维密度、钠、钾、添加糖构建 0–100 营养模式评分。
- 局限：美国横断面调查、24 小时膳食自报、非中国 K12 现场、不能推断因果。

### 2.2 UCLA CNP / OpenNeuro ds000030

- 来源：OpenNeuro ds000030，CC0。
- 样本：272 名成人，年龄 21–50；包含 CONTROL、ADHD、BIPOLAR、SCHZ 研究分组。
- 使用：WAIS、WMS、DKEFS、Stroop、StopSignal、TaskSwitch、CPT，以及 Hopkins/ASRS 问卷。
- 重要边界：
  - 诊断标签没有用于聚类；
  - 神经认知模型不是临床诊断；
  - 心理学模型是问卷相关支持信号，不是抑郁/焦虑分类器；
  - 成人研究样本不能直接外推到未成年人。

### 2.3 Nutrition5k

- 来源：Google Research，CC BY 4.0。
- 本轮下载：5,006 道菜的 dish metadata 和 train/test 划分。
- 未下载：181.4GB 图像与视频。
- 用途：餐盘级热量、质量、脂肪、碳水、蛋白质分布参考；后续可接图像营养估算。
- 局限：美国食堂场景，不代表中国饮食。

## 3. 健康顾问模型

目标：平均收缩压 ≥130 mmHg 或平均舒张压 ≥80 mmHg 的筛查代理。  
预测特征不包含血压本身：年龄、性别、BMI、腰围、睡眠、每周活动、膳食热量、纤维、钠、钾、糖和饱和脂肪。

| 指标 | 数值 |
|---|---:|
| AUC | 0.7235 |
| AP | 0.6529 |
| Brier | 0.2136 |
| LogLoss | 0.6169 |
| F1 | 0.6366 |
| 测试样本 | 1,250 |

模型文件：`models/health_advisor.joblib`。

## 4. 营养顾问模型

将以下四项转换成透明的 0–100 营养模式评分：

- 纤维密度 <14g/1000kcal：30 分；
- 钠 >2300mg：25 分；
- 钾 <2600mg：20 分；
- 添加糖供能比 >10%：25 分。

模型是一个“评分校准器”，不是疾病预测器。

| 指标 | 数值 |
|---|---:|
| MAE | 3.3369 |
| RMSE | 5.9192 |
| R² | 0.8844 |
| 测试样本 | 1,437 |
| 高分段人数 | 4,902 / 5,747 |

高分段比例较高，说明指南缺口在样本中普遍存在，不能解释为“85% 的人有病”。

模型文件：`models/nutrition_advisor.joblib`。

## 5. 神经认知顾问模型

域构造：

- 记忆：WAIS、WMS、DKEFS 相关分数；
- 执行：DKEFS、Stroop、StopSignal、TaskSwitch；
- 注意：CPT 漏报、误报和反应时变异。

标准化后做 KMeans（3 类）：

| 画像 | 人数 | 记忆 | 执行 | 注意 |
|---|---:|---:|---:|---:|
| higher_support_need | 101 | -0.712 | -0.270 | 0.029 |
| monitor | 49 | 0.144 | -0.152 | -0.675 |
| lower_support_need | 122 | 0.532 | 0.285 | 0.247 |

诊断标签未参与聚类。模型文件：`models/neurocognitive_advisor.joblib`。

## 6. 心理学顾问模型

输入：Hopkins 抑郁、焦虑、躯体化、强迫、人际敏感、总体严重度，以及 ASRS 分数。  
输出：低支持信号、观察、高支持信号三类，不输出临床诊断。

| 支持信号 | 人数 |
|---|---:|
| low_support_signal | 146 |
| monitor | 79 |
| high_support_signal | 47 |

模型文件：`models/psychology_advisor.joblib`。

## 7. 学习科学顾问

没有公开的“量子认知标签数据集”，因此不训练一个伪监督模型。该顾问使用透明融合：

```text
support_index = knowledge_gap + uncertainty + metacognitive_bias
              + hesitation + neuro_support + psych_support
              + health_risk + nutrition_risk
```

权重的当前版本：

| 输入 | 权重 |
|---|---:|
| 知识缺口 | 0.25 |
| 不确定性 | 0.15 |
| 元认知偏差 | 0.10 |
| 犹豫 | 0.15 |
| 神经认知支持 | 0.15 |
| 心理支持 | 0.10 |
| 健康风险 | 0.05 |
| 营养风险 | 0.05 |

Bloch 球中的 θ、φ 和轨迹仅作为状态建模语言。该模型不主张真实物理量子效应。

模型配置：`models/learning_science_advisor.joblib`。

## 8. 文件与复现

训练：

```powershell
$py='D:\Tender\Tender-Demo\backend\.venv\Scripts\python.exe'
& $py D:\Tender\experiments\advisor_bench\run_advisor_models.py
```

推理：

```powershell
& $py D:\Tender\experiments\advisor_bench\infer_advisors.py --advisor health --input '{"RIDAGEYR":16,"RIAGENDR":1,"BMXBMI":22,"sleep_hours":7,"mvpa_week":300}'
```

输出：

- `outputs/advisor_metrics.json`
- `outputs/data_manifest.json`
- `outputs/neurocognitive_profiles.json`
- `outputs/psychology_profiles.json`
- `outputs/nutrition5k_summary.json`
- `outputs/fig_neurocognitive_profiles.png`
- `outputs/fig_psychology_profiles.png`

## 9. 下一阶段

1. 接入中国 K12 的授权健康、膳食和睡眠记录；
2. 用 PHQ/GAD 等经过许可和验证的青少年量表重做心理学基线；
3. 与校医、营养师、心理老师共同设定阈值和转介流程；
4. 用营养5k图像做餐盘识别与营养回归；
5. 对真实用户做公平性、校准、漂移和误报评估；
6. 不把模型结果用于录取、分班、处罚或自动收费。


## 10. 生涯与安全顾问模型

### 10.1 生涯与职业顾问

数据：O*NET 30.1，923 个职业、155 个能力/技能/兴趣/活动特征。

方法：标准化、L2 归一化、余弦相似度和 12 类职业聚类。

结果：

- 30 维 SVD 解释方差 0.9213；
- 聚类 silhouette 0.1764；
- 结果仅用于职业探索，不是就业预测。

模型：`models/career_advisor.joblib`。

### 10.2 安全与保护顾问

数据：

- UCI SMS Spam Collection：5,574 条短信；
- SSEF cyberbullying Instagram/TikTok：538 条文本。

结果：

- 诈骗/垃圾短信：AUC 0.9919，AP 0.9773；
- 霸凌/攻击性文本：AUC 0.7500，AP 0.6779；
- 训练集和测试集较小，不能作为生产级安全模型。

安全顾问还有硬规则：自伤、现实暴力威胁、不当接触和失联必须立即人工升级；这部分没有训练分类器。

模型：`models/safety_advisor.joblib`。

### 10.3 数据许可

- O*NET：使用前需审核 O*NET 条款和署名要求；
- UCI SMS Spam：使用前需遵循 UCI 引用要求；
- SSEF cyberbullying：HF 元数据只标注 CC，商用前必须核实具体版本；
- 安全模型不是案件调查、诊断或自动处置系统。
