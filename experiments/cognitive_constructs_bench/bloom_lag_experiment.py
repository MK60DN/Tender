# -*- coding: utf-8 -*-
"""Bloom experiment on public ASSISTments 2009 sequences.

Question: after controlling for prior performance, does lag between repeated
opportunities for the same skill predict success on the next opportunity?

This is an observational lag-based proxy, not a laboratory measure of delay.
"""
from __future__ import annotations
import json, pathlib, sys
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import StandardScaler

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"
KT = pathlib.Path(r"D:\Tender\experiments\knowledge_tracing_bench")
sys.path.insert(0, str(KT))
from ktbench.data import load_assistments, filter_skills


def ece(y_true, p, bins=10):
    y_true = np.asarray(y_true); p = np.asarray(p)
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if m.any():
            total += m.mean() * abs(y_true[m].mean() - p[m].mean())
    return float(total)


def safe_number(value, default=0.0):
    try:
        if pd.isna(value):
            return float(default)
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return float(default)


def build_rows(df):
    rows = []
    needed = ["user_id", "order_id", "skill_name", "correct"]
    df = df.dropna(subset=needed).sort_values(["user_id", "order_id"]).reset_index(drop=True)
    for uid, g in df.groupby("user_id", sort=False):
        state = {}
        for pos, row in enumerate(g.itertuples(index=False)):
            sk = str(row.skill_name)
            hist = state.get(sk)
            if hist:
                lag = pos - hist["last_pos"] - 1
                rows.append({
                    "user_id": uid,
                    "skill_name": sk,
                    "correct": int(row.correct),
                    "prior_rate": hist["success"] / hist["count"],
                    "prior_count": hist["count"],
                    "prev_correct": hist["last_correct"],
                    "lag_events": max(0, lag),
                    "log_lag": np.log1p(max(0, lag)),
                    "hint_count": safe_number(getattr(row, "hint_count", 0)),
                    "attempt_count": max(1.0, safe_number(getattr(row, "attempt_count", 1), 1)),
                    "log_response": np.log1p(safe_number(getattr(row, "ms_first_response", 0))),
                    "opportunity": max(1.0, safe_number(getattr(row, "opportunity", hist["count"] + 1), hist["count"] + 1)),
                })
                hist["count"] += 1
                hist["success"] += int(row.correct)
                hist["last_pos"] = pos
                hist["last_correct"] = int(row.correct)
            else:
                state[sk] = {"count": 1, "success": int(row.correct), "last_pos": pos, "last_correct": int(row.correct)}
    out = pd.DataFrame(rows)
    return out.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)


def feature_frame(df, skill_mean):
    base = pd.DataFrame({
        "prior_rate": df["prior_rate"].to_numpy(),
        "prior_count_log": np.log1p(df["prior_count"].to_numpy()),
        "prev_correct": df["prev_correct"].to_numpy(),
        "hint_log": np.log1p(df["hint_count"].to_numpy()),
        "attempt_log": np.log1p(df["attempt_count"].to_numpy()),
        "response_log": df["log_response"].to_numpy(),
        "skill_mean": df["skill_name"].map(skill_mean).fillna(df["correct"].mean()).to_numpy(),
        "opportunity_log": np.log1p(df["opportunity"].to_numpy()),
    })
    return base


def run_cv(rows, seed):
    y = rows["correct"].to_numpy()
    groups = rows["user_id"].to_numpy()
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    fold_rows = []
    oof = np.full(len(rows), np.nan)
    for fold, (tr, te) in enumerate(sgkf.split(rows, y, groups), 1):
        train = rows.iloc[tr]
        test = rows.iloc[te]
        skill_mean = train.groupby("skill_name")["correct"].mean().to_dict()
        Xtr = feature_frame(train, skill_mean)
        Xte = feature_frame(test, skill_mean)
        # Leakage-safe lag quartiles learned within the training fold.
        q = np.quantile(train["log_lag"], [0.25, 0.5, 0.75])
        for name, X in (("base", Xtr), ("space", Xte)):
            pass
        def add_space(X, source):
            out = X.copy()
            lag = source["log_lag"].to_numpy()
            out["lag_log"] = lag
            out["lag_q2"] = ((lag > q[0]) & (lag <= q[1])).astype(float)
            out["lag_q3"] = ((lag > q[1]) & (lag <= q[2])).astype(float)
            out["lag_q4"] = (lag > q[2]).astype(float)
            return out
        Xtr_b, Xte_b = Xtr, Xte
        Xtr_s, Xte_s = add_space(Xtr, train), add_space(Xte, test)
        for name, a, b in (("base", Xtr_b, Xte_b), ("space", Xtr_s, Xte_s)):
            scaler = StandardScaler().fit(a)
            model = LogisticRegression(max_iter=800, solver="lbfgs")
            model.fit(scaler.transform(a), train["correct"].to_numpy())
            pred = model.predict_proba(scaler.transform(b))[:, 1]
            fold_rows.append({"seed": seed, "fold": fold, "model": name,
                              "auc": roc_auc_score(test["correct"], pred),
                              "logloss": log_loss(test["correct"], pred),
                              "brier": brier_score_loss(test["correct"], pred),
                              "ece": ece(test["correct"], pred)})
            if name == "space":
                oof[te] = pred
    return pd.DataFrame(fold_rows), oof


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = filter_skills(load_assistments(), 200)
    rows = build_rows(raw)
    rows.to_csv(OUT / "lag_rows.csv", index=False, encoding="utf-8-sig")
    all_folds = []
    oofs = []
    for seed in range(5):
        folds, oof = run_cv(rows, seed)
        all_folds.append(folds)
        oofs.append(oof)
    folds = pd.concat(all_folds, ignore_index=True)
    folds.to_csv(OUT / "cv_metrics.csv", index=False, encoding="utf-8-sig")
    oof = np.nanmean(np.vstack(oofs), axis=0)
    # Cross-fitted quartile dose-response.
    rows["lag_band"] = pd.qcut(
        rows["log_lag"].rank(method="first"),
        4,
        labels=["Q1 shortest", "Q2", "Q3", "Q4 longest"],
    )
    dose = rows.assign(pred=oof).groupby("lag_band", observed=True).agg(
        n=("correct", "size"), observed_correct=("correct", "mean"), mean_prediction=("pred", "mean")
    ).reset_index()
    dose.to_csv(OUT / "lag_dose_response.csv", index=False, encoding="utf-8-sig")
    summary = {"dataset": "ASSISTments 2009", "rows_after_first_opportunity": int(len(rows)),
               "students": int(rows.user_id.nunique()), "skills": int(rows.skill_name.nunique()),
               "feature_note": "lag_events is the number of intervening student events before the next same-skill opportunity; it is not elapsed time.",
               "metrics": {}}
    for model in ("base", "space"):
        g = folds[folds.model == model]
        summary["metrics"][model] = {k: {"mean": float(g[k].mean()), "sd": float(g[k].std(ddof=1))} for k in ("auc", "logloss", "brier", "ece")}
    pairs = folds.pivot_table(index=["seed", "fold"], columns="model", values=["auc", "logloss", "brier", "ece"])
    summary["difference_space_minus_base"] = {
        metric: {"mean": float((pairs[(metric, "space")] - pairs[(metric, "base")]).mean()),
                 "sd": float((pairs[(metric, "space")] - pairs[(metric, "base")]).std(ddof=1))}
        for metric in ("auc", "logloss", "brier", "ece")
    }
    dose_records = dose.copy()
    dose_records["lag_band"] = dose_records["lag_band"].astype(str)
    summary["dose_response"] = dose_records.to_dict(orient="records")
    summary["interpretation_guardrail"] = "Observational association only; selection and unmeasured ability can explain part of the association."
    (OUT / "result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
