# cognitive_constructs_bench

对 Tender 的“开花、结果、森林”构念做公开数据检验与方法学验证。

## 数据

- EdNet 5000：真实毫秒时间戳；重复题目作答后续尝试；
- ASSISTments 2009：没有真实时间戳，只用于事件间隔代理的对照；
- 合成案例：检查群体评分函数的边界行为。

## 运行

```powershell
$py = 'D:\Tender\Tender-Demo\backend\.venv\Scripts\python.exe'
$env:PYTHONPATH = 'D:\Tender\experiments\knowledge_tracing_bench'

& $py bloom_lag_experiment.py
& $py ednet_time_gap_experiment.py
& $py group_construct_simulation.py
```

`ednet_time_gap_experiment.py` 需要读取约 510MB 的 EdNet 序列文件，运行时间约数分钟。

## 主要结果

| 实验 | 结论 |
|---|---|
| EdNet 真实时间间隔 | AUC 0.6648 → 0.6839；LogLoss 0.6472 → 0.6345；有预测信息，但非因果 |
| ASSISTments 事件间隔代理 | AUC 仅 +0.00033；代理变量不能替代真实时间 |
| 群体结果模拟 | AUROC 0.993；敏感度 67.1%；特异度 99.4% |
| 森林模拟 | AUROC 0.999；敏感度 68.4%；特异度 100% |

完整结果和限制见 `REPORT.md`。
