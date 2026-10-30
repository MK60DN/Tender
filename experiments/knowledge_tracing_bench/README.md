# knowledge_tracing_bench

**知识追踪基准实验**：用公开数据评测 Tender 的 θ_seq 表示，与标准方法对照。

完全独立目录，可整体删除，不影响 Tender/DaoQL 主链路。

## 为什么做这个

项目里已经下载了大量公开教育数据（EdNet / ASSISTments / OULAD / Eedi / ...），
但之前只做了描述性统计（规模、正确率、标签分布），**从未训练过知识追踪模型**。
本实验补上这一步：给出第一个可复现、有对照组的 Tender 教育建模评测。

## 数据

- 来源：`D:\Tender\external_data\open_downloads\assistments2009.csv`
- 原始：346,860 行 / 4,217 学生 / 101 技能
- 清洗后：273,364 行 / 4,128 学生 / 81 技能
- 划分：**按学生** 8:2（避免同学生跨集造成成绩虚高）

## 文件

```
ktbench/data.py       加载与清洗 ASSISTments，按学生划分
ktbench/bkt.py        BKT（EM，向量化实现）
ktbench/tender.py     Tender θ_seq（严格照 05-L1-QSCM / 12-完整闭环 的公式）
ktbench/metrics.py    AUC / RMSE / LogLoss / Platt 校准
run_benchmark.py      基准主程序
analyze.py            分析、图表、控制组
REPORT.md             实验报告（结论在这里）
outputs/              全部产物
```

## 运行

```powershell
$py = 'D:\Tender\Tender-Demo\backend\.venv\Scripts\python.exe'
$env:PYTHONPATH = 'D:\Tender\experiments\knowledge_tracing_bench'

& $py run_benchmark.py        # 约 5 分钟
& $py analyze.py              # 出图表（约 30 秒）
```

## 核心结论（详见 REPORT.md）

| 模型 | AUC | LogLoss |
|---|---:|---:|
| BKT（标准基线） | 0.6794 | 0.5910 |
| Tender θ_seq（全局初始化） | 0.6853 | 0.6164 |
| Tender θ_seq（文档默认 η=0.3） | 0.6895 | 1.1155 |
| Logistic（控制组） | 0.7058 | 0.5752 |

三条主要发现：

1. **文档默认 η=0.3 比数据支持值大约 15 倍**；按概率校准最优点在 η≈0.02。
   η 越大 AUC 略升但 LogLoss 急剧恶化——文档调的是排序，产品需要的是校准。
2. **场景切换惩罚 ξ=0.15 未获数据支持**，网格搜索最优落在边界 0。
3. **按知识点分状态是必要的**（去掉后 AUC 掉 0.03-0.04，LogLoss 翻倍）。

## 边界

- 只评测了 **θ_seq 单源**；完整 Tender 的四源（颜色/文本/序列/HRV）未参与。
- 数据是**美国中学生数学题**，不是中文语法填空。
- 未与 DKT/SAKT 等深度知识追踪对比，因此**不能宣称达到前沿水平**。
- 单次划分，差异在 ±0.01 以内不应过度解读。
