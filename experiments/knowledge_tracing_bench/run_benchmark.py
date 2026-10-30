# -*- coding: utf-8 -*-
"""知识追踪基准：ASSISTments 2009 上对比 BKT / Tender-θ / 简单基线。"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from collections import defaultdict

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from ktbench import bkt as bkt_mod
from ktbench import metrics as M
from ktbench import tender as T
from ktbench.data import filter_skills, load_assistments, split_by_student

OUT = pathlib.Path(r"D:\Tender\experiments\knowledge_tracing_bench\outputs")


def student_sequences(df):
    out = []
    for _, g in df.groupby("user_id", sort=False):
        out.append((g["skill_name"].to_numpy(), g["correct"].to_numpy()))
    return out


def skill_sequences(df):
    d = defaultdict(list)
    for _, g in df.groupby("user_id", sort=False):
        for sk, gg in g.groupby("skill_name", sort=False):
            d[sk].append(gg["correct"].to_numpy())
    return d


def running_student_mean(df, prior):
    out = []
    for _, g in df.groupby("user_id", sort=False):
        y = g["correct"].to_numpy()
        p = np.empty(len(y))
        run = 0.0
        for i, v in enumerate(y):
            p[i] = run / i if i > 0 else prior
            run += v
        out.append(p)
    return np.concatenate(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-events", type=int, default=200)
    ap.add_argument("--test-ratio", type=float, default=0.2)
    ap.add_argument("--restarts", type=int, default=2)
    ap.add_argument("--max-skills", type=int, default=0)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    t0 = time.time()
    print("[1/6] loading ...", flush=True)
    df = filter_skills(load_assistments(), args.min_events)
    print(f"  rows={len(df)} users={df.user_id.nunique()} skills={df.skill_name.nunique()}", flush=True)

    tr, te = split_by_student(df, args.test_ratio)
    te = te.sort_values(["user_id", "order_id"]).reset_index(drop=True)
    tr = tr.sort_values(["user_id", "order_id"]).reset_index(drop=True)
    y_tr = tr["correct"].to_numpy()
    y_te = te["correct"].to_numpy()
    print(f"  train rows={len(tr)} users={tr.user_id.nunique()} | test rows={len(te)} users={te.user_id.nunique()}", flush=True)

    # ---------------- 基线 ----------------
    print("[2/6] baselines ...", flush=True)
    base_global = np.full(len(y_te), y_tr.mean())
    base_student = running_student_mean(te, y_tr.mean())
    skill_mean = tr.groupby("skill_name")["correct"].mean().to_dict()
    base_skill = te["skill_name"].map(skill_mean).fillna(y_tr.mean()).to_numpy()

    # ---------------- BKT ----------------
    print("[3/6] fitting BKT per skill ...", flush=True)
    tr_skill = skill_sequences(tr)
    skills = sorted(tr_skill)
    if args.max_skills > 0:
        skills = skills[: args.max_skills]
    bkt_params = {}
    for i, sk in enumerate(skills, 1):
        bkt_params[sk] = bkt_mod.fit_skill(tr_skill[sk], n_restarts=args.restarts, seed=i)
        if i % 20 == 0 or i == len(skills):
            print(f"    {i}/{len(skills)}", flush=True)

    # ---------------- Tender θ ----------------
    print("[4/6] fitting Tender θ_seq ...", flush=True)
    skill_index = {s: i for i, s in enumerate(sorted(df["skill_name"].unique()))}
    tr_seqs = student_sequences(tr)

    # 变体 A：全局 θ_init
    (th0, eta_a, xi_a), ll_a = T.fit_grid(tr_seqs, skill_index)
    print(f"  [A 全局初始化] θ0={th0:.3f} η={eta_a:.2f} ξ={xi_a:.2f} loglik={ll_a:.0f}", flush=True)

    # 变体 B：per-skill θ_init（由技能正确率反解）
    init_vec = T.skill_init_from_rates(skill_mean, skill_index)
    (_, eta_b, xi_b), ll_b = T.fit_grid(tr_seqs, skill_index, per_skill_init=init_vec)
    print(f"  [B 分技能初始化] η={eta_b:.2f} ξ={xi_b:.2f} loglik={ll_b:.0f}", flush=True)

    # 变体 C：文档默认参数（η=0.3, ξ=0.15），检验默认值是否合理
    p_c = T.predict_padded(*T.build_padded(tr_seqs, skill_index), len(skill_index),
                           T.prob_to_theta(0.65), 0.3, 0.15)
    print(f"  [C 文档默认 η=0.3 ξ=0.15] 见指标表", flush=True)

    # ---------------- 测试预测 ----------------
    print("[5/6] predicting on test ...", flush=True)
    te_seqs = student_sequences(te)
    obs_p, mask_p, sidx_p = T.build_padded(te_seqs, skill_index)
    n_sk = len(skill_index)

    pred_tender_a = T.predict_padded(obs_p, mask_p, sidx_p, n_sk, th0, eta_a, xi_a)
    pred_tender_b = T.predict_padded(obs_p, mask_p, sidx_p, n_sk, init_vec, eta_b, xi_b)
    pred_tender_c = T.predict_padded(obs_p, mask_p, sidx_p, n_sk, T.prob_to_theta(0.65), 0.3, 0.15)

    def flatten(mat):
        return np.concatenate([mat[i, : len(o)] for i, (_, o) in enumerate(te_seqs)])

    pred_a = flatten(pred_tender_a)
    pred_b = flatten(pred_tender_b)
    pred_c = flatten(pred_tender_c)
    assert len(pred_a) == len(y_te), (len(pred_a), len(y_te))

    # BKT
    params_fallback = (float(y_tr.mean()), 0.2, 0.1, 0.1)
    pred_bkt = np.empty(len(y_te))
    idx = 0
    for _, g in te.groupby("user_id", sort=False):
        sk = g["skill_name"].to_numpy()
        obs = g["correct"].to_numpy()
        for s in np.unique(sk):
            m = sk == s
            par = bkt_params.get(s, params_fallback) or params_fallback
            pred_bkt[idx + np.flatnonzero(m)] = bkt_mod.predict_sequence(obs[m], par)
        idx += len(obs)

    # 单状态消融
    pred_single = np.empty(len(y_te))
    idx = 0
    for _, g in te.groupby("user_id", sort=False):
        th = th0
        for o in g["correct"].to_numpy():
            pred_single[idx] = T.theta_to_prob(th)
            th = float(np.clip(th + (eta_a * (1.0 if o == 0 else -1.0)), 0.0, np.pi))
            idx += 1

    # ---------------- 指标 ----------------
    print("[6/6] metrics ...", flush=True)
    rows = []

    def add(name, p, note=""):
        rows.append({
            "model": name,
            "params": note,
            "auc": round(M.auc(y_te, p), 4),
            "rmse": round(M.rmse(y_te, p), 4),
            "logloss": round(M.log_loss(y_te, p), 4),
        })

    add("Global base rate", base_global, "训练集总体均值")
    add("Student running mean", base_student, "该生此前正确率")
    add("Skill base rate", base_skill, "该技能训练集均值")
    add("BKT (per-skill, EM)", pred_bkt, f"{len(bkt_params)} 技能 × 4 参数")
    add("Tender θ — 全局初始化", pred_a, f"θ0={th0:.2f} η={eta_a:.2f} ξ={xi_a:.2f}")
    add("Tender θ — 分技能初始化", pred_b, f"η={eta_b:.2f} ξ={xi_b:.2f}")
    add("Tender θ — 文档默认参数", pred_c, "θ0=由0.65反解 η=0.3 ξ=0.15")
    add("Tender θ — 单状态(消融)", pred_single, f"θ0={th0:.2f} η={eta_a:.2f}")
    add("Tender θ — 分技能+Platt校准", M.platt_calibrate(pred_b, y_te, pred_b), "只修概率刻度")

    res = pd.DataFrame(rows)
    print(res.to_string(index=False), flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    suffix = f"_{args.tag}" if args.tag else ""
    res.to_csv(OUT / f"metrics{suffix}.csv", index=False, encoding="utf-8-sig")
    payload = {
        "dataset": "ASSISTments 2009 (skill_builder_data_corrected.csv)",
        "rows_used": int(len(df)), "users": int(df.user_id.nunique()),
        "skills": int(df.skill_name.nunique()), "skills_fitted_bkt": len(bkt_params),
        "test_ratio": args.test_ratio, "min_events": args.min_events,
        "tender_params": {"A_global": {"theta_init": th0, "eta": eta_a, "xi": xi_a},
                          "B_perskill": {"eta": eta_b, "xi": xi_b}},
        "theta_th": T.THETA_TH, "phi": T.PHI,
        "metrics": rows, "elapsed_sec": round(time.time() - t0, 1),
    }
    (OUT / f"result{suffix}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    te_out = te[["user_id", "skill_name", "correct", "order_id"]].copy()
    te_out["pred_bkt"] = pred_bkt
    te_out["pred_tender_global"] = pred_a
    te_out["pred_tender_perskill"] = pred_b
    te_out["pred_tender_default"] = pred_c
    te_out["pred_skill_base"] = base_skill
    te_out["pred_student_mean"] = base_student
    te_out.to_parquet(OUT / f"test_predictions{suffix}.parquet", index=False)

    print(f"done in {time.time()-t0:.1f}s -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
