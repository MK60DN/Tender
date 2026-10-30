# Tender Advisor Bench

公开数据驱动的健康、营养、神经认知、心理学与学习科学顾问基线。

## 训练

```powershell
$py='D:\Tender\Tender-Demo\backend\.venv\Scripts\python.exe'
& $py D:\Tender\experiments\advisor_bench\run_advisor_models.py
```

## 推理

```powershell
& $py D:\Tender\experiments\advisor_bench\infer_advisors.py --advisor health --input '{"RIDAGEYR":16,"RIAGENDR":1,"BMXBMI":22}'
```

`--advisor` 支持 `health`、`nutrition`、`neurocognitive`、`psychology`、`learning`。

## 边界

- 不是医疗或临床诊断；
- 不是人格或能力标签；
- 不使用诊断标签训练分类器；
- 量子认知是建模语法，不是真实量子效应；
- 所有结果必须经过本地校准和人工复核。
