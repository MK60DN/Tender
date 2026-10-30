# -*- coding: utf-8 -*-
"""Tender θ_seq 模型：严格按《05-L1-QSCM》与《12-完整闭环总览》的公式实现。

公式（全部出自教学文档，非自创）：

1) 序列分量递推（文档 05 §5.4）：
       θ_seq_t = θ_{t-1} + η·Δt·趋势 + ξ·场景切换惩罚
   默认值：η = 0.3，ξ = 0.15

2) 冲击响应饱和（文档 12）：
       α = (0.5·s) / (0.618 + |s|)

3) 临界纬线（文档 05）：
       θ_th = arccos(1/φ)，φ = 1.618

4) Bloch 态到可观测概率：
       |ψ⟩ = cos(θ/2)|D⟩ + e^{iφ}sin(θ/2)|F⟩
       P(区分态) = cos²(θ/2)   → 用作"答对概率"

教育场景取舍（必须声明）：
  校内模式不采集颜色/文本/HRV，四源退化为单源 θ_seq。
  本实验只评测 θ_seq。
"""
from __future__ import annotations

import numpy as np

PHI = 1.618
THETA_TH = float(np.arccos(1.0 / PHI))   # ≈ 0.9046 rad ≈ 51.8°
ETA_DEFAULT = 0.3
XI_DEFAULT = 0.15
SAT_DENOM = 0.618
EPS = 1e-10


def shock(s: float) -> float:
    """冲击响应饱和：α = (0.5·s)/(0.618+|s|)。"""
    return (0.5 * s) / (SAT_DENOM + abs(s))


def theta_to_prob(theta):
    """Bloch 映射：P(区分态) = cos²(θ/2)。"""
    return np.clip(np.cos(np.asarray(theta) / 2.0) ** 2, 1e-6, 1 - 1e-6)


def prob_to_theta(p) -> float:
    """Bloch 映射的逆：由正确率反解 θ（用于 per-skill 初始化）。"""
    p = float(np.clip(p, 1e-4, 1 - 1e-4))
    return float(2.0 * np.arccos(np.sqrt(p)))


def run_sequence(obs, skills, theta_init, eta=ETA_DEFAULT, xi=XI_DEFAULT):
    """标量版（可读性参考）：单条学生序列的 θ_seq 递推。"""
    T = len(obs)
    preds = np.empty(T)
    theta = {}
    last = None
    for t in range(T):
        k = skills[t]
        th = theta.get(k, theta_init)
        preds[t] = theta_to_prob(th)
        trend = 1.0 if obs[t] == 0 else -1.0
        switch = xi if (last is not None and k != last) else 0.0
        theta[k] = float(np.clip(th + eta * trend + switch, 0.0, np.pi))
        last = k
    return preds


# ---------------------------------------------------------------- 向量化

def build_padded(seqs, skill_index: dict, max_len: int | None = None):
    """seqs: list[(skills_arr, obs_arr)] → (obs, mask, sidx) 定长矩阵。"""
    items = []
    for s, o in seqs:
        if len(o) == 0:
            continue
        if max_len is not None:
            s, o = s[:max_len], o[:max_len]
        items.append((s, o))
    n = len(items)
    tmax = max(len(o) for _, o in items)
    obs = np.zeros((n, tmax), dtype=np.int8)
    mask = np.zeros((n, tmax), dtype=bool)
    sidx = np.full((n, tmax), -1, dtype=np.int32)
    for i, (s, o) in enumerate(items):
        L = len(o)
        obs[i, :L] = o
        mask[i, :L] = True
        sidx[i, :L] = [skill_index[x] for x in s]
    return obs, mask, sidx


def predict_padded(obs, mask, sidx, n_skills, theta_init, eta, xi):
    """向量化预测。

    theta_init 可以是标量，也可以是长度 n_skills 的数组（per-skill 初始 θ）。
    """
    n, tmax = obs.shape
    if np.isscalar(theta_init):
        state = np.full((n, n_skills), float(theta_init), dtype=np.float64)
    else:
        state = np.tile(np.asarray(theta_init, dtype=np.float64)[None, :], (n, 1))
    preds = np.zeros((n, tmax), dtype=np.float64)
    rows = np.arange(n)
    prev = np.full(n, -1, dtype=np.int32)
    eta_f, xi_f = float(eta), float(xi)
    for t in range(tmax):
        valid = mask[:, t]
        if not valid.any():
            continue
        sk = sidx[:, t]
        th = state[rows, sk]
        preds[:, t] = theta_to_prob(th)
        trend = np.where(obs[:, t] == 0, 1.0, -1.0)
        switch = np.where((t > 0) & (sk != prev), xi_f, 0.0)
        state[rows, sk] = np.clip(th + eta_f * trend + switch, 0.0, np.pi)
        prev = sk
    return preds


def fit_grid(seqs, skill_index: dict, theta_init_grid=None, eta_grid=None, xi_grid=None,
             per_skill_init: np.ndarray | None = None):
    """向量化网格搜索。

    per_skill_init 为 None 时搜索全局 θ_init；否则固定 per-skill 初始 θ，只搜 η 与 ξ。
    返回 ((theta_init, eta, xi), loglik)。theta_init 在 per-skill 模式下返回数组。
    """
    from itertools import product
    eta_grid = np.array([0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.45]) if eta_grid is None else eta_grid
    xi_grid = np.array([0.0, 0.10, 0.25, 0.40]) if xi_grid is None else xi_grid
    obs, mask, sidx = build_padded(seqs, skill_index)
    n_skills = len(skill_index)
    y = obs == 1

    if per_skill_init is None:
        theta_init_grid = np.linspace(0.3, 2.8, 13) if theta_init_grid is None else theta_init_grid
        best = (-np.inf, None)
        for th0, eta, xi in product(theta_init_grid, eta_grid, xi_grid):
            p = predict_padded(obs, mask, sidx, n_skills, float(th0), float(eta), float(xi))
            ll = float(np.where(y, np.log(p), np.log(1.0 - p))[mask].sum())
            if ll > best[0]:
                best = (ll, (float(th0), float(eta), float(xi)))
        return best[1], best[0]

    best = (-np.inf, None)
    for eta, xi in product(eta_grid, xi_grid):
        p = predict_padded(obs, mask, sidx, n_skills, np.asarray(per_skill_init, dtype=float), float(eta), float(xi))
        ll = float(np.where(y, np.log(p), np.log(1.0 - p))[mask].sum())
        if ll > best[0]:
            best = (ll, (np.asarray(per_skill_init, dtype=float), float(eta), float(xi)))
    return best[1], best[0]


def skill_init_from_rates(skill_rates: dict, skill_index: dict) -> np.ndarray:
    """由技能训练集正确率反解每个技能的初始 θ（per-skill 初始化）。"""
    out = np.full(len(skill_index), prob_to_theta(0.65), dtype=np.float64)
    for s, i in skill_index.items():
        if s in skill_rates:
            out[i] = prob_to_theta(skill_rates[s])
    return out
