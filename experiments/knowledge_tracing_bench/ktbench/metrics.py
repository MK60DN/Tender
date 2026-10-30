# -*- coding: utf-8 -*-
"""评测指标：AUC 与 RMSE（知识追踪的标准评测口径）。"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score


def auc(y_true, y_pred) -> float:
    y_true = np.asarray(y_true)
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_pred))


def rmse(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def log_loss(y_true, y_pred) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.clip(np.asarray(y_pred, dtype=float), 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def platt_calibrate(p_train, y_train, p_test):
    """一维 Platt 校准：在 logit(p) 上拟合逻辑回归，修正概率刻度。"""
    from sklearn.linear_model import LogisticRegression
    z = np.log(np.clip(p_train, 1e-6, 1 - 1e-6) / (1 - np.clip(p_train, 1e-6, 1 - 1e-6)))
    m = LogisticRegression()
    m.fit(z.reshape(-1, 1), y_train)
    zt = np.log(np.clip(p_test, 1e-6, 1 - 1e-6) / (1 - np.clip(p_test, 1e-6, 1 - 1e-6)))
    return m.predict_proba(zt.reshape(-1, 1))[:, 1]
