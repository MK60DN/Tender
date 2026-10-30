# -*- coding: utf-8 -*-
"""个人节律基线与每日偏离度（对标 HRV 的个体化常模）。

为什么不做"和别人比"
--------------------
HRV 临床判断异常，看的是"你今天偏离你自己的基线多少"，
而不是"你和别人比高不高"。个体基线差异极大，
和人群比会把"正常人"判成异常。作息同理。

三个偏离分量
------------
    量偏离  今日活动量 vs 个人日均        "今天学得比平时多还是少"
    时偏离  今日时相 vs 个人时相          "今天是不是换时间了"
    型偏离  今日小时轮廓 vs 个人轮廓       "今天的节奏形状变了没有"

统计上的四个要点（前三个来自 HRV，第四个来自本项目的踩坑）
----------------------------------------------------------
1. 用稳健统计：中位数与 MAD（活动量是重尾分布，均值和标准差会被极端值污染）。
2. 基线必须事外：用前半段建基线，在后半段评估。
3. 时相用圆形统计：23 点与 1 点距离是 2 小时，不是 22 小时。
4. **口径必须一致**：拿"单日事件数"去比"多日聚合的计数"是错的，
   两者量纲不同。所以基线要做成"**日均**"口径。

第一版的错误（已被合成验证抓到）
--------------------------------
- 时相用"周内相位"（周期 168）：每天一次的活动在周内是 7 个均匀点，
  向量和约为 0 → 基线时相是随机的 → 时偏离全是噪声。
  **修正：时相用"日内小时"（周期 24）。**
- 量偏离拿单日数比 42 天聚合数 → 系统性为负。
  **修正：基线统一成"日均"口径。**
"""
from __future__ import annotations

import math

import numpy as np

MAD_SCALE = 1.4826
DAY = 24.0


def build_baseline(events, n_days: float | None = None, n_bins: int = 24):
    """用一段（应当稳定的）数据建立**日均口径**的个人作息基线。"""
    t = np.asarray(events, dtype=float)
    n = len(t)
    if n < 20:
        return None
    if n_days is None:
        n_days = max(float(np.floor(t.max() / DAY - t.min() / DAY)) + 1.0, 1.0)
    n_days = max(float(n_days), 1.0)

    hod = np.mod(t, DAY)
    width = DAY / n_bins
    idx = np.clip((hod / width).astype(int), 0, n_bins - 1)
    counts = np.bincount(idx, minlength=n_bins).astype(float)
    per_day = counts / n_days                      # 每个小时格的**日均**事件数
    total = per_day.sum()
    profile = per_day / total if total > 0 else per_day

    # 日内时相质心（周期 24）
    ang = 2.0 * np.pi * hod / DAY
    C, S = float(np.cos(ang).mean()), float(np.sin(ang).mean())
    phase = (math.atan2(S, C) % (2 * math.pi)) / (2 * math.pi) * DAY

    # 日总量：用**拟泊松**模型刻画计数（计数的标准做法）
    #   mu    = 日均事件数
    #   phi   = 过散布因子 = 方差/均值（>1 表示比泊松更波动）
    #   scale = sqrt(phi)，用于把偏差残差标准化
    day_id = np.floor(t / DAY).astype(int)
    totals = np.bincount(day_id - day_id.min()).astype(float)
    mu = float(totals.mean()) if len(totals) else float(n)
    mu = max(mu, 1e-6)
    var = float(totals.var(ddof=1)) if len(totals) > 1 else mu
    phi = max(var / mu, 1.0)                    # 过散布因子，至少为 1
    scale = math.sqrt(phi)
    med_total = float(np.median(totals)) if len(totals) else float(n)

    return {"per_day": per_day, "profile": profile, "phase": phase,
            "med_total": med_total, "mu_total": mu, "phi": phi, "scale": scale,
            "n_days": n_days, "n_events": n, "n_bins": n_bins}


def circular_distance_hours(a, b, period=DAY):
    """圆形距离（小时）：23 点和 1 点相差 2 小时。"""
    d = abs((a - b) % period)
    return min(d, period - d)


def daily_deviation(day_events, baseline):
    """计算某一天相对个人基线的三个偏离分量与综合偏离度。"""
    if baseline is None or len(day_events) == 0:
        return None
    t = np.asarray(day_events, dtype=float)
    n_bins = baseline["n_bins"]
    width = DAY / n_bins
    hod = np.mod(t, DAY)
    idx = np.clip((hod / width).astype(int), 0, n_bins - 1)
    counts = np.bincount(idx, minlength=n_bins).astype(float)
    today_profile = counts / max(counts.sum(), 1e-9)

    # 1) 量偏离：今日事件数的**拟泊松偏差残差**
    #    泊松偏差：D = 2[n·log(n/μ) − (n − μ)]
    #    标准化后：q_level = sign(n−μ)·sqrt(D) / sqrt(phi)
    n_today = float(len(t))
    mu = max(baseline["mu_total"], 1e-6)
    if n_today > 0:
        D = 2.0 * (n_today * math.log(n_today / mu) - (n_today - mu))
    else:
        D = 2.0 * mu
    D = max(D, 0.0)
    q_level = math.copysign(math.sqrt(D), n_today - mu) / baseline["scale"]

    # 2) 时偏离：今日时相 vs 基线时相（周期 24）
    ang = 2.0 * np.pi * hod / DAY
    C, S = float(np.cos(ang).mean()), float(np.sin(ang).mean())
    today_phase = (math.atan2(S, C) % (2 * math.pi)) / (2 * math.pi) * DAY
    d_phase = circular_distance_hours(today_phase, baseline["phase"], DAY)
    q_phase = d_phase / 6.0                        # 6 小时作为标度

    # 3) 型偏离：轮廓余弦距离
    a, b = today_profile, baseline["profile"]
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    cos = float(np.dot(a, b) / (na * nb)) if na > 0 and nb > 0 else 0.0
    q_shape = 1.0 - cos

    composite = math.sqrt(q_level ** 2 + q_phase ** 2 + (2.0 * q_shape) ** 2) / math.sqrt(3)

    return {
        "量偏离": q_level, "时偏离": q_phase, "型偏离": q_shape,
        "综合偏离": composite,
        "今日事件数": int(len(t)),
        "今日时相": today_phase,
        "基线时相": baseline["phase"],
    }
