# -*- coding: utf-8 -*-
"""作息节律的周期图分析（点过程版，对标 HRV 的频域分析）。

为什么不用普通 PSD
------------------
HRV 的 RR 间期接近**连续信号**，适合功率谱密度（Lomb-Scargle 周期图）。
但作息是**点过程**：有活动才有记录，一天可能只有一次。

对一个"每天一次"的脉冲序列做 PSD，会在 12h、8h、6h… 产生大量谐波，
功率被摊到各个频带里，反而看不清主节律。
（自检验证：纯 24h 正弦的日内占比是 1.000，但"每天一次脉冲"只有 0.367。）

点过程的标准工具：Rayleigh / Schuster 周期图
--------------------------------------------
对候选周期 P，把每个事件时刻换成相位：

    φ_i = (t_i mod P) / P        ∈ [0, 1)

如果事件确实以 P 为周期聚集，φ 就会集中在某个值附近。
用**合向量长度**衡量集中程度：

    C(P) = Σ cos(2πφ_i) / n
    S(P) = Σ sin(2πφ_i) / n
    R(P) = √(C² + S²)             —— 取值 [0,1]，越大越周期

显著性：零假设（相位均匀）下， 2nR² ~ χ²(2)。
这等价于 Rayleigh 检验。

三个指标
--------
    日内强度  R_24  = R(P=24h)     —— 每天固定时段的规律程度
    周内强度  R_168 = R(P=168h)    —— 每周固定日子的规律程度
    节律平衡  B     = R_168 / R_24 —— 课表驱动 vs 自主节律

B 高 → 作息主要跟着课表走；B 低 → 主要跟着自己的日节律走。
"""
from __future__ import annotations

import math

import numpy as np

DAY = 24.0
WEEK = 168.0


def rayleigh_R(times, period: float) -> tuple[float, float]:
    """Rayleigh 检验：返回 (R, p值)。

    R = 合向量长度，取值 [0,1]；零假设为相位均匀。
    """
    t = np.asarray(times, dtype=float)
    n = len(t)
    if n < 5:
        return np.nan, np.nan
    phase = np.mod(t, period) / period * 2.0 * np.pi
    C = float(np.mean(np.cos(phase)))
    S = float(np.mean(np.sin(phase)))
    R = float(math.hypot(C, S))
    Z = n * R * R
    # 零分布：2Z ~ chi2(2)，即 Z ~ Exp(1)
    p = float(math.exp(-Z))
    return R, p


def rayleigh_periodogram(times, periods=None, n_periods: int = 240,
                         p_min: float = 6.0, p_max: float = 2000.0):
    """在周期轴上扫描 R(P)，返回 (periods, R, p)。"""
    if periods is None:
        periods = np.logspace(math.log10(p_min), math.log10(p_max), n_periods)
    R, P = [], []
    for pr in periods:
        r, p = rayleigh_R(times, float(pr))
        R.append(r)
        P.append(p)
    return np.asarray(periods), np.asarray(R), np.asarray(P)


def rhythm_metrics(times, day: float = DAY, week: float = WEEK):
    """三个核心指标：日内强度、周内强度、节律平衡。"""
    r_d, p_d = rayleigh_R(times, day)
    r_w, p_w = rayleigh_R(times, week)
    if not np.isfinite(r_d) or not np.isfinite(r_w):
        return None
    return {
        "日内强度R24": r_d, "日内p": p_d,
        "周内强度R168": r_w, "周内p": p_w,
        "节律平衡B": (r_w / r_d) if r_d > 1e-9 else np.nan,
        "主导节律": ("周内" if r_w > r_d else "日内"),
    }


def phase_profile(times, period: float, n_bins: int = 24):
    """相位的分布直方图（用来看聚集在哪个时段）。"""
    t = np.asarray(times, dtype=float)
    ph = np.mod(t, period) / period
    h, edges = np.histogram(ph, bins=n_bins, range=(0, 1))
    centers = (edges[:-1] + edges[1:]) / 2.0 * period
    return centers, h
