# -*- coding: utf-8 -*-
"""BKT（贝叶斯知识追踪）：标准可解释基线，EM 估计参数。

向量化实现：对一个技能的全部学生序列做 padding 后批处理。
padding 位置的发射概率设为 1（等价于"没有观测"），统计量用 mask 排除。

模型（每个技能一组四参数）：
    P(L0) 先验掌握概率
    P(T)  学习转移概率
    P(G)  猜测概率（未掌握答对）
    P(S)  失误概率（已掌握答错）
转移矩阵 A = [[1-P(T), P(T)], [0, 1]]（一旦掌握不再遗忘）
"""
from __future__ import annotations

import numpy as np

EPS = 1e-10
MAX_LEN = 300


def _pad(sequences, max_len: int = MAX_LEN):
    seqs = [np.asarray(s, dtype=np.int8)[:max_len] for s in sequences if len(s) > 0]
    if not seqs:
        return None, None
    n = len(seqs)
    tmax = max(len(s) for s in seqs)
    obs = np.zeros((n, tmax), dtype=np.int8)
    mask = np.zeros((n, tmax), dtype=bool)
    for i, s in enumerate(seqs):
        obs[i, : len(s)] = s
        mask[i, : len(s)] = True
    return obs, mask


def _emit(obs, mask, pg, ps):
    e0 = np.where(obs == 1, pg, 1.0 - pg)
    e1 = np.where(obs == 1, 1.0 - ps, ps)
    # 填充位不提供信息
    e0 = np.where(mask, e0, 1.0)
    e1 = np.where(mask, e1, 1.0)
    return e0, e1


def _estep(obs, mask, p0, pt, pg, ps):
    n, tmax = obs.shape
    e0, e1 = _emit(obs, mask, pg, ps)

    alpha = np.zeros((tmax, n, 2))
    alpha[0, :, 0] = (1.0 - p0) * e0[:, 0]
    alpha[0, :, 1] = p0 * e1[:, 0]
    c = alpha[0].sum(axis=1, keepdims=True)
    ll = np.log(np.maximum(c[:, 0], EPS)).sum()
    alpha[0] /= np.maximum(c, EPS)

    for t in range(1, tmax):
        a0 = alpha[t - 1, :, 0]
        a1 = alpha[t - 1, :, 1]
        n0 = a0 * (1.0 - pt) * e0[:, t]
        n1 = (a0 * pt + a1) * e1[:, t]
        alpha[t, :, 0] = n0
        alpha[t, :, 1] = n1
        c = (n0 + n1)
        ll += np.log(np.maximum(c, EPS)).sum()
        alpha[t, :, 0] = n0 / np.maximum(c, EPS)
        alpha[t, :, 1] = n1 / np.maximum(c, EPS)

    beta = np.zeros((tmax, n, 2))
    beta[tmax - 1] = 1.0
    for t in range(tmax - 2, -1, -1):
        b0 = beta[t + 1, :, 0]
        b1 = beta[t + 1, :, 1]
        beta[t, :, 0] = (1.0 - pt) * e0[:, t + 1] * b0 + pt * e1[:, t + 1] * b1
        beta[t, :, 1] = e1[:, t + 1] * b1

    gamma = alpha * beta
    s = gamma.sum(axis=2, keepdims=True)
    gamma = gamma / np.maximum(s, EPS)

    # 转移期望（只需要 0->0 与 0->1）
    a0 = alpha[:-1, :, 0]
    b0 = beta[1:, :, 0]
    b1 = beta[1:, :, 1]
    x00 = a0 * (1.0 - pt) * e0[:, 1:].T * b0
    x01 = a0 * pt * e1[:, 1:].T * b1
    trans_mask = mask[:, 1:].T
    x00 = np.where(trans_mask, x00, 0.0)
    x01 = np.where(trans_mask, x01, 0.0)
    return gamma, mask, x00.sum(), x01.sum(), ll


def fit_skill(sequences, n_restarts: int = 2, max_iter: int = 30, tol: float = 1e-5, seed: int = 0):
    obs, mask = _pad(sequences)
    if obs is None:
        return None
    rng = np.random.default_rng(seed)
    best_ll, best_params = -np.inf, None
    for _ in range(n_restarts):
        p0 = float(rng.uniform(0.10, 0.60))
        pt = float(rng.uniform(0.05, 0.40))
        pg = float(rng.uniform(0.05, 0.35))
        ps = float(rng.uniform(0.02, 0.25))
        prev_ll = -np.inf
        for _it in range(max_iter):
            gamma, m, n_unlearn, n_learn, ll = _estep(obs, mask, p0, pt, pg, ps)
            correct = (obs == 1) & mask
            wrong = (obs == 0) & mask
            n_l1 = gamma[:, :, 1].T
            n_l0 = gamma[:, :, 0].T
            n_l1_correct = n_l1[correct].sum()
            n_l1_wrong = n_l1[wrong].sum()
            n_l0_correct = n_l0[correct].sum()
            n_l0_wrong = n_l0[wrong].sum()
            n_l0_first = gamma[0, :, 1].sum()

            tot1 = n_l1_correct + n_l1_wrong
            tot0 = n_l0_correct + n_l0_wrong
            new_ps = n_l1_wrong / tot1 if tot1 > EPS else ps
            new_pg = n_l0_correct / tot0 if tot0 > EPS else pg
            denom = n_learn + n_unlearn
            new_pt = n_learn / denom if denom > EPS else pt
            new_p0 = n_l0_first / obs.shape[0]
            p0, pt, pg, ps = (float(np.clip(v, 1e-4, 1.0 - 1e-4))
                              for v in (new_p0, new_pt, new_pg, new_ps))
            improved = ll - prev_ll
            prev_ll = ll
            if improved < tol * max(1.0, abs(ll)):
                break
        if prev_ll > best_ll:
            best_ll, best_params = prev_ll, (p0, pt, pg, ps)
    return best_params


def predict_sequence(obs: np.ndarray, params) -> np.ndarray:
    """返回每一步"观测之前的预测概率"（用于评测）。"""
    p0, pt, pg, ps = params
    out = np.empty(len(obs))
    p_l = p0
    for t, o in enumerate(obs):
        p = p_l * (1.0 - ps) + (1.0 - p_l) * pg
        out[t] = float(np.clip(p, 1e-6, 1 - 1e-6))
        if o == 1:
            post = (p_l * (1.0 - ps)) / max(p, EPS)
        else:
            post = (p_l * ps) / max(1.0 - p, EPS)
        p_l = post + (1.0 - post) * pt
    return out
