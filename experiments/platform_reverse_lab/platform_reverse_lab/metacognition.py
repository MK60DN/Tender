# -*- coding: utf-8 -*-
"""元认知校准：从"标记的重点"与"实际对错"算元认知质量。

学术基础（DOI 已核实）
----------------------
Fleming & Lau (2014), How to measure metacognition, Front. Hum. Neurosci.
    DOI 10.3389/fnhum.2014.00443   被引 1388
    核心主张：元认知必须拆成两个独立的量——
        · 元认知**敏感性**：能不能区分自己"会"与"不会"
        · 元认知**偏差**：总体偏自信还是偏保守
    两者可以独立变化。

Barrett, Dienes & Seth (2013), Measures of metacognition on signal-detection
theoretic models, Psychological Methods.  DOI 10.1037/a0033268   被引 177
    给出 meta-d' 的形式化定义。

Double (2025), Survey measures of metacognitive monitoring are often false,
Behavior Research Methods.  DOI 10.3758/s13428-025-02621-6
    用自评问卷测元认知常常是假的 —— 支持本项目用行为数据而非问卷。

本项目怎么落地
--------------
讲义上已有两类天然数据：
    · 学生标记的**重点词/重点句**（前面打根号）
    · 测试的**实际对错**

前者是**元认知判断**（"我不会这个"），后者是**一阶结果**。

    2x2 列联表
                      实际答错     实际答对
        标记为重点      命中 H       虚报 FA
        未标记          漏报         正确拒绝

与项目 L2 的连接
----------------
第 14 课测谎模块做的是"自报颜色 vs HRV 生理"的一致性检查；
本节做的是"自报重点 vs 实际对错"的一致性检查。
**同一个元元逻辑，用在不同信号对上。**
"""
from __future__ import annotations

import math

import numpy as np

Z_EPS = 1e-6


def _z(p: float) -> float:
    p = min(max(p, Z_EPS), 1 - Z_EPS)
    from scipy.stats import norm
    return float(norm.ppf(p))


def calibration_table(marked, error):
    """构造 2x2 列联表。

    marked : 布尔数组，True = 学生标记为重点
    error  : 布尔数组，True = 实际答错
    """
    m = np.asarray(marked, dtype=bool)
    e = np.asarray(error, dtype=bool)
    if len(m) != len(e):
        raise ValueError("marked 与 error 长度不一致")
    return {"命中": int(np.sum(m & e)), "虚报": int(np.sum(m & ~e)),
            "漏报": int(np.sum(~m & e)), "正确拒绝": int(np.sum(~m & ~e)),
            "n": int(len(m))}


def metacognitive_sensitivity(marked, error) -> float:
    """元认知敏感性 AUC = P(错题被标记的概率 > 对题被标记的概率)。

    标准 AUC 定义：
        AUC = [ #(pos > neg) + 0.5·#(pos == neg) ] / (n_pos · n_neg)

    0.5 = 标记与对错无关（元认知无效）
    1.0 = 标记完美对应错题
    """
    m = np.asarray(marked, dtype=float)
    e = np.asarray(error, dtype=bool)
    n1, n0 = int(e.sum()), int((~e).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    pos, neg = m[e], m[~e]
    gt = int((pos[:, None] > neg[None, :]).sum())
    eq = int((pos[:, None] == neg[None, :]).sum())
    return (gt + 0.5 * eq) / (n1 * n0)


def metacognitive_bias(marked, error) -> float:
    """元认知偏差 = 标记率 - 错误率。

    > 0：标记得比实际错的多 -> 过度谨慎（宁可多标）
    < 0：标记得比实际错的少 -> 过度自信（漏标）
    """
    m = np.asarray(marked, dtype=bool)
    e = np.asarray(error, dtype=bool)
    if len(m) == 0:
        return float("nan")
    return float(m.mean() - e.mean())


def d_prime(marked, error) -> float:
    """信号检测论 d' = z(H) - z(FA)，采用加 0.5 校正避免边界。"""
    t = calibration_table(marked, error)
    n1 = t["命中"] + t["漏报"]
    n0 = t["虚报"] + t["正确拒绝"]
    if n1 == 0 or n0 == 0:
        return float("nan")
    H = (t["命中"] + 0.5) / (n1 + 1.0)
    FA = (t["虚报"] + 0.5) / (n0 + 1.0)
    return float(_z(H) - _z(FA))


def metacognitive_profile(marked, error, min_n: int = 8):
    """一次算出全部元认知指标。"""
    t = calibration_table(marked, error)
    if t["n"] < min_n:
        return None
    auc = metacognitive_sensitivity(marked, error)
    if not np.isfinite(auc):
        return None
    bias = metacognitive_bias(marked, error)
    return {"元认知敏感性AUC": round(auc, 4),
            "元认知偏差": round(bias, 4),
            "偏差绝对值": round(abs(bias), 4),
            "d_prime": round(d_prime(marked, error), 4),
            **t}


def confidence_discount(auc: float, lo: float = 0.5, hi: float = 0.9) -> float:
    """把元认知敏感性转成"自评可信度"折扣，供 L2 元元层使用。

    AUC <= 0.5（无区分能力） -> 0.30（几乎不信自评）
    AUC >= 0.9（高度敏感）   -> 1.00（完全信自评）
    中间线性插值。

    用途：作为 θ 合成里"自评分量"的权重折扣。
    """
    if not np.isfinite(auc):
        return 0.50
    x = (auc - lo) / max(hi - lo, 1e-9)
    return float(min(max(0.30 + 0.70 * x, 0.30), 1.00))


def calibrate_confidence(mc_meta: float, auc: float) -> float:
    """把元认知折扣乘进 L2 的 MetaConfidence。

        MC_adjusted = MC_meta × discount(AUC)
    """
    return float(mc_meta * confidence_discount(auc))
