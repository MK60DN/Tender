# -*- coding: utf-8 -*-
"""元元检测：给研究结论本身打一个"可信度分"。

普通分析回答："效应是多少？"
元元分析回答："这个结论本身有多可信？"

为什么观测者效应必须进元元评分
------------------------------
观测者效应的本质是：测量过程回流进了被测量的系统。

    普通测量：  观察者 -> 被观察者 -> 得到一个值
    观测者效应：观察者 -> 被观察者 -> 被观察者知道自己被观察
                 -> 被观察者改变 -> 值已经不是原来的值

这正是元元层要处理的事：它不问"值是多少"，
它问"这个值被测量行为污染了多少"。

五个评分维度
------------
    观测者效应风险  0.25   知情 / 反馈 / 可见记录
    功效            0.25   N 够不够
    阴性对照        0.20   本该没效应的检验是否干净
    数据质量        0.15   覆盖天数、活动次数
    预注册依从      0.15   有没有事后改动

分级
----
    >= 0.80   可作结论
    0.50-0.80 只能作线索
    < 0.50    不可作结论
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

WEIGHTS = {
    "观测者效应风险": 0.25,
    "功效": 0.25,
    "阴性对照": 0.20,
    "数据质量": 0.15,
    "预注册依从": 0.15,
}


@dataclass
class StudyMeta:
    subjects_know_hypothesis: bool = True
    results_fed_back: bool = False
    behavior_visibly_recorded: bool = True
    n_actual: int = 0
    n_required: int = 90
    negative_control_p: float | None = None
    median_days: float = 0.0
    median_events: float = 0.0
    preregistered: bool = True
    changed_after_data: bool = False


def _score_observer(m: StudyMeta):
    notes, s = [], 1.0
    if m.subjects_know_hypothesis:
        s -= 0.45
        notes.append("学生知道研究假设 -> 可能迎合或反向表现（-0.45）")
    if m.results_fed_back:
        s -= 0.35
        notes.append("向学生反馈了结果 -> 标签效应污染后续数据（-0.35）")
    if m.behavior_visibly_recorded:
        s -= 0.20
        notes.append("行为记录对学生可见 -> 霍桑效应风险（-0.20）")
    if not notes:
        notes.append("无观测者效应风险点")
    return max(s, 0.0), notes


def _score_power(m: StudyMeta):
    r = m.n_actual / max(m.n_required, 1)
    if r >= 1.0:
        return 1.0, [f"样本 {m.n_actual}/{m.n_required}，达到目标"]
    if r >= 0.78:
        return 0.55, [f"样本 {m.n_actual}/{m.n_required}，功效不足但不至于无意义"]
    return 0.15, [f"样本 {m.n_actual}/{m.n_required}，功效严重不足"]


def _score_control(m: StudyMeta):
    if m.negative_control_p is None:
        return 0.35, ["未做阴性对照 -> 无法检测系统偏差"]
    if m.negative_control_p < 0.01:
        return 0.0, [f"阴性对照显著（p={m.negative_control_p:.3g}）-> 存在系统偏差"]
    if m.negative_control_p < 0.05:
        return 0.35, [f"阴性对照边缘显著（p={m.negative_control_p:.3g}）-> 需排查"]
    return 1.0, [f"阴性对照干净（p={m.negative_control_p:.2g}）"]


def _score_quality(m: StudyMeta):
    notes, s = [], 1.0
    if m.median_days < 28:
        s -= 0.5
        notes.append(f"中位覆盖 {m.median_days:.0f} 天 < 28 天（-0.5）")
    if m.median_events < 20:
        s -= 0.4
        notes.append(f"中位活动 {m.median_events:.0f} 次 < 20（-0.4）")
    if not notes:
        notes.append("数据质量达标")
    return max(s, 0.0), notes


def _score_prereg(m: StudyMeta):
    if m.changed_after_data:
        return 0.0, ["看过数据后改过假设或指标 -> 事后挑选，结论作废"]
    if not m.preregistered:
        return 0.35, ["未预注册 -> 无法排除事后调整"]
    return 1.0, ["已预注册且未事后改动"]


SCORERS = {
    "观测者效应风险": _score_observer,
    "功效": _score_power,
    "阴性对照": _score_control,
    "数据质量": _score_quality,
    "预注册依从": _score_prereg,
}


def meta_confidence(m: StudyMeta) -> dict[str, Any]:
    parts, notes = {}, {}
    for name, fn in SCORERS.items():
        s, n = fn(m)
        parts[name] = round(float(s), 3)
        notes[name] = n
    mc = sum(parts[k] * WEIGHTS[k] for k in WEIGHTS)

    # ---- 一票否决（护栏）----
    # 加权平均会让"单项致命缺陷"被其他项稀释。
    # 但有些缺陷是不可补偿的：事后改动 = 结论作废；系统偏差 = 结论不可信。
    veto = None
    if m.changed_after_data:
        veto = ("事后改动", "看过数据后改过假设或指标 —— 结论作废", 0.30)
    elif m.negative_control_p is not None and m.negative_control_p < 0.01:
        veto = ("系统偏差", "阴性对照显著 —— 存在系统偏差，结论不可信", 0.45)

    if veto:
        mc = min(mc, veto[2])
        grade, advice = "不可作结论", f"触发一票否决（{veto[0]}）：{veto[1]}"
    elif mc >= 0.80:
        grade, advice = "可作结论", "可以作为研究结论对外表述"
    elif mc >= 0.50:
        grade, advice = "只能作线索", "只能作为值得进一步看的线索，不能作结论"
    else:
        grade, advice = "不可作结论", "结论无效，需要重新设计或重新采集"
    return {"维度得分": parts, "权重": WEIGHTS, "MetaConfidence": round(float(mc), 3),
            "分级": grade, "建议": advice, "一票否决": (veto[0] if veto else None),
            "说明": notes, "输入": asdict(m)}


def render(res: dict, title: str = "研究元元可信度评分卡") -> str:
    L = [f"# {title}", "", f"**MetaConfidence = {res['MetaConfidence']}** ｜ 分级：**{res['分级']}**",
         "", f"> {res['建议']}", "", "## 维度得分", "",
         "| 维度 | 权重 | 得分 | 加权 |", "|---|---:|---:|---:|"]
    for k, w in res["权重"].items():
        s = res["维度得分"][k]
        L.append(f"| {k} | {w:.2f} | {s:.2f} | {s*w:.3f} |")
    L += ["", "## 说明", ""]
    for k, notes in res["说明"].items():
        for n in notes:
            L.append(f"- **{k}**：{n}")
    return "\n".join(L)
