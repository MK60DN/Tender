# RoleMind Bench

用公开教育数据训练 Tender 的角色心智基线。

## 已训练模型

- StudentMind：ASSISTments 2009，答题正确概率和知识状态
- TeacherMind：TalkMoves，教师课堂话语/提问/解释/管理行为
- SalesMind：X Education Lead Scoring，教育线索转化概率
- ParentMind：UCI Student Performance 家庭支持代理，高缺勤风险 + 家庭支持画像
- InstitutionMind：OULAD 周级学习参与，课程流失风险代理

## 数据缺口

- HeadTeacherMind：当前只有 OULAD 课程周风险代理，没有班主任个人行为的公开标签
- DormMind：没有直接公开数据；需要自建应查、实到、请假、跑校、晚归、异常和交接事件

## 运行

```powershell
$py='D:\Tender\Tender-Demo\backend\.venv\Scripts\python.exe'
& $py D:\Tender\experiments\role_mind_bench\run_role_mind_models.py
```

## 目录

- `run_role_mind_models.py`：训练主程序
- `models/`：joblib 模型
- `outputs/role_mind_metrics.json`：指标
- `outputs/role_mind_examples.json`：角色状态示例
- `outputs/fig_*.png`：图表
- `REPORT.md`：完整实验报告

## 说明

这些是公开数据上的行为代理模型，不是对现实某位教师、家长、宿管或销售的人格判断。  
正式产品必须用真实、授权、脱敏的自有事件做校准和评测。
