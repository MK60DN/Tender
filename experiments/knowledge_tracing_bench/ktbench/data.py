# -*- coding: utf-8 -*-
"""知识追踪基准实验：数据加载与划分。"""
from __future__ import annotations

import pathlib
import numpy as np
import pandas as pd

RAW = pathlib.Path(r"D:\Tender\external_data\open_downloads\assistments2009.csv")


def load_assistments(path: pathlib.Path | None = None) -> pd.DataFrame:
    """加载并清洗 ASSISTments 2009。

    清洗规则（沿用 Deep Knowledge Tracing / Piech et al. 2015 的常规做法）：
    1. 丢弃 skill_name 缺失的记录；
    2. 按 (user_id, order_id, problem_id) 去重；
    3. 按 (user_id, order_id) 排序成作答序列。
    注意：源文件不是 UTF-8，用 latin-1 读取。
    """
    df = pd.read_csv(path or RAW, low_memory=False, encoding="latin-1")
    df = df[df["skill_name"].notna()].copy()
    df = df.drop_duplicates(subset=["user_id", "order_id", "problem_id"])
    df["correct"] = df["correct"].astype(int)
    df = df.sort_values(["user_id", "order_id"]).reset_index(drop=True)
    df["skill_name"] = df["skill_name"].astype(str)
    return df


def filter_skills(df: pd.DataFrame, min_events: int = 200) -> pd.DataFrame:
    """只保留样本量足够的技能，避免 BKT 在稀有技能上过拟合。"""
    counts = df["skill_name"].value_counts()
    keep = counts[counts >= min_events].index
    return df[df["skill_name"].isin(keep)].copy()


def split_by_student(df: pd.DataFrame, test_ratio: float = 0.2, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """按学生划分训练/测试集：同一学生不会同时出现在两边。

    这是知识追踪的标准评测方式（评估对"新学生"的泛化）。
    """
    rng = np.random.default_rng(seed)
    users = df["user_id"].unique()
    rng.shuffle(users)
    n_test = int(len(users) * test_ratio)
    test_users = set(users[:n_test])
    is_test = df["user_id"].isin(test_users)
    return df[~is_test].copy(), df[is_test].copy()


def sequences(df: pd.DataFrame):
    """按学生产出 (user_id, skill_array, correct_array)。"""
    for uid, g in df.groupby("user_id", sort=False):
        yield uid, g["skill_name"].to_numpy(), g["correct"].to_numpy()
