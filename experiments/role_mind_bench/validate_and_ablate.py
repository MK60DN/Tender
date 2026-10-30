# -*- coding: utf-8 -*-
"""Validate saved RoleMind models and run leakage/sensitivity ablations."""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import sys
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from datasets import load_dataset
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression

ROOT = pathlib.Path(r"D:\Tender")
BENCH = ROOT / "experiments" / "role_mind_bench"
DATA = ROOT / "external_data" / "open_downloads"
OUT = BENCH / "outputs"
MODELS = BENCH / "models"
OUT.mkdir(parents=True, exist_ok=True)


def round4(value):
    return None if value is None else round(float(value), 4)


def safe_metric(fn, *args, **kwargs):
    try:
        return round4(fn(*args, **kwargs))
    except Exception:
        return None


def metrics_binary(y_true, prob, threshold=0.5):
    pred = (np.asarray(prob) >= threshold).astype(int)
    return {
        "auc": safe_metric(roc_auc_score, y_true, prob),
        "ap": safe_metric(average_precision_score, y_true, prob),
        "logloss": safe_metric(log_loss, y_true, prob),
        "brier": safe_metric(brier_score_loss, y_true, prob),
        "f1_at_0_5": safe_metric(f1_score, y_true, pred, zero_division=0),
        "n": int(len(y_true)),
        "positive_rate": round4(np.mean(y_true)),
    }


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def load_student_frame():
    path = DATA / "assistments2009.csv"
    df = pd.read_csv(path, low_memory=False, encoding="latin-1")
    skill_counts = df.groupby("skill_name").size()
    keep = set(skill_counts[skill_counts >= 200].index)
    df = df[df["skill_name"].isin(keep)].copy()
    df = df.sort_values(["user_id", "order_id"]).reset_index(drop=True)
    df["prior_user_correct"] = df.groupby("user_id")["correct"].transform(
        lambda s: s.shift().expanding().mean()
    )
    df["prior_skill_correct"] = df.groupby(["user_id", "skill_name"])["correct"].transform(
        lambda s: s.shift().expanding().mean()
    )
    df["prior_user_correct"] = df["prior_user_correct"].fillna(df["correct"].mean())
    df["prior_skill_correct"] = df["prior_skill_correct"].fillna(df["prior_user_correct"])
    return df


def student_ablations():
    df = load_student_frame()
    y = df["correct"].astype(int)
    users = df["user_id"].drop_duplicates().to_numpy()
    train_users, test_users = train_test_split(users, test_size=0.2, random_state=42)
    tr = df["user_id"].isin(train_users).to_numpy()
    te = ~tr
    variants = {
        "full_7_features": [
            "attempt_count", "hint_count", "hint_total", "ms_first_response",
            "opportunity", "prior_user_correct", "prior_skill_correct",
        ],
        "without_process_timing": ["opportunity", "prior_user_correct", "prior_skill_correct"],
        "without_prior_correctness": [
            "attempt_count", "hint_count", "hint_total", "ms_first_response", "opportunity",
        ],
        "process_timing_only": ["attempt_count", "hint_count", "hint_total", "ms_first_response"],
        "prior_correctness_only": ["prior_user_correct", "prior_skill_correct"],
    }
    results = {}
    for name, feats in variants.items():
        X = df[feats].apply(pd.to_numeric, errors="coerce").fillna(0)
        model = HistGradientBoostingClassifier(
            max_iter=120, learning_rate=0.08, max_leaf_nodes=31, random_state=42
        )
        model.fit(X[tr], y[tr])
        prob = model.predict_proba(X[te])[:, 1]
        results[name] = {"features": feats, **metrics_binary(y[te], prob)}
        if name == "without_process_timing":
            joblib.dump({
                "model": model,
                "features": feats,
                "intended_use": "pre_answer_operational",
                "excluded_features_reason": "attempt_count, hint_count, hint_total and ms_first_response are unavailable before the answer or are post-submission signals",
            }, MODELS / "student_mind_pre_answer.joblib")
        print("student", name, results[name]["auc"], results[name]["logloss"])
    return results, {"rows": int(len(df)), "train_users": int(len(train_users)), "test_users": int(len(test_users))}


def sales_ablations():
    frames = {split: load_dataset("shawhin/lead-scoring-x", split=split).to_pandas() for split in ("train", "valid", "test")}
    train_df = pd.concat([frames["train"], frames["valid"]], ignore_index=True)
    test_df = frames["test"]
    y_train = train_df["Converted"].astype(int)
    y_test = test_df["Converted"].astype(int)
    variants = {
        "full_5_fields": ["Lead Origin", "Lead Source", "Last Activity", "Tags", "What is your current occupation"],
        "without_tags": ["Lead Origin", "Lead Source", "Last Activity", "What is your current occupation"],
        "without_last_activity": ["Lead Origin", "Lead Source", "Tags", "What is your current occupation"],
        "without_tags_or_activity": ["Lead Origin", "Lead Source", "What is your current occupation"],
        "origin_and_source_only": ["Lead Origin", "Lead Source"],
    }
    results = {}
    for name, feats in variants.items():
        pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), feats)], remainder="drop")
        model = Pipeline([
            ("pre", pre),
            ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=1.0)),
        ])
        model.fit(train_df[feats], y_train)
        prob = model.predict_proba(test_df[feats])[:, 1]
        base = metrics_binary(y_test, prob)
        order = np.argsort(-prob)
        top10 = order[: max(1, len(order) // 10)]
        base["top10_capture"] = round4(y_test.iloc[top10].sum() / max(1, y_test.sum()))
        results[name] = {"features": feats, **base}
        if name == "without_tags_or_activity":
            joblib.dump({
                "pipeline": model,
                "features": feats,
                "intended_use": "pre_contact_operational",
                "excluded_features_reason": "Tags and Last Activity are strongly label-adjacent and caused large AUC inflation",
            }, MODELS / "sales_mind_pre_contact.joblib")
        print("sales", name, results[name]["auc"], results[name]["logloss"])
    return results, {"train_rows": int(len(train_df)), "test_rows": int(len(test_df))}


def parent_sensitivity():
    base = DATA / "student_performance_uci"
    frames = []
    for fn, subject in [("student-mat.csv", "math"), ("student-por.csv", "portuguese")]:
        d = pd.read_csv(base / fn, sep=";")
        d["subject"] = subject
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    feats = ["Medu", "Fedu", "Pstatus", "famsup", "paid", "schoolsup", "studytime", "famrel", "internet", "address", "subject"]
    cat = ["Pstatus", "famsup", "paid", "schoolsup", "internet", "address", "subject"]
    y = (df["absences"] >= 10).astype(int)

    def fit_eval(train_idx, test_idx, variant_feats):
        cats = [c for c in cat if c in variant_feats]
        pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), cats)], remainder="passthrough")
        model = Pipeline([
            ("pre", pre),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ])
        model.fit(df.loc[train_idx, variant_feats], y.loc[train_idx])
        prob = model.predict_proba(df.loc[test_idx, variant_feats])[:, 1]
        return metrics_binary(y.loc[test_idx], prob)

    tr, te = train_test_split(np.arange(len(df)), test_size=0.25, random_state=42, stratify=y)
    results = {
        "full_random_holdout": fit_eval(tr, te, feats),
        "without_subject": fit_eval(tr, te, [c for c in feats if c != "subject"]),
        "train_math_test_portuguese": fit_eval(np.where(df.subject == "math")[0], np.where(df.subject == "portuguese")[0], feats),
        "train_portuguese_test_math": fit_eval(np.where(df.subject == "portuguese")[0], np.where(df.subject == "math")[0], feats),
    }
    return results


def institution_sensitivity():
    path = DATA / "oulad_engineered.parquet"
    df = pd.read_parquet(path).dropna(subset=["target_attrition"]).copy()
    saved = joblib.load(MODELS / "institution_mind.joblib")
    model = saved["model"]
    feats = saved["features"]
    X = df[feats].copy()
    for c in ["code_module", "code_presentation"]:
        X[c] = X[c].astype("category").cat.codes
    y = df["target_attrition"].astype(int)
    ids = df["id_student"].drop_duplicates().to_numpy()
    train_ids, test_ids = train_test_split(ids, test_size=0.2, random_state=42)
    te = df["id_student"].isin(test_ids).to_numpy()
    prob = model.predict_proba(X[te])[:, 1]
    result = {"student_holdout": metrics_binary(y[te], prob)}
    tmp = df.loc[te, ["code_module", "target_attrition"]].copy()
    tmp["prob"] = prob
    for module, g in tmp.groupby("code_module"):
        if g["target_attrition"].nunique() > 1:
            result[f"module_{module}"] = metrics_binary(g["target_attrition"], g["prob"])
    return result


def inference_checks():
    checks = {}
    # Student: report both the post-hoc benchmark and the deployable pre-answer model.
    student_bench = joblib.load(MODELS / "student_mind.joblib")
    x_student_bench = pd.DataFrame([{f: 0.0 for f in student_bench["features"]}])
    x_student_bench.loc[0, "opportunity"] = 2.0
    x_student_bench.loc[0, "prior_user_correct"] = 0.5
    x_student_bench.loc[0, "prior_skill_correct"] = 0.4
    student_ops = joblib.load(MODELS / "student_mind_pre_answer.joblib")
    x_student_ops = x_student_bench[student_ops["features"]]
    checks["student"] = {
        "operational_features": student_ops["features"],
        "pre_answer_prediction": round4(student_ops["model"].predict_proba(x_student_ops)[0, 1]),
        "research_benchmark_features": student_bench["features"],
        "posthoc_benchmark_prediction": round4(student_bench["model"].predict_proba(x_student_bench)[0, 1]),
    }
    # Teacher
    teacher = joblib.load(MODELS / "teacher_mind.joblib")
    sample_text = "What strategy did you use, and can you explain why your answer works?"
    p = teacher["classifier"].predict_proba(teacher["vectorizer"].transform([sample_text]))[0]
    checks["teacher"] = {
        "text": sample_text,
        "top_labels": [
            {"label": teacher["labels"][i], "probability": round4(p[i])}
            for i in np.argsort(-p)[:3]
        ],
    }
    # Sales: report both leaky research benchmark and pre-contact operational variant.
    sales_bench = joblib.load(MODELS / "sales_mind.joblib")
    sales_ops = joblib.load(MODELS / "sales_mind_pre_contact.joblib")
    row_bench = {
        "Lead Origin": "Landing Page Submission",
        "Lead Source": "Google",
        "Last Activity": "SMS Sent",
        "Tags": "Interested in other courses",
        "What is your current occupation": "Working Professional",
    }
    row_ops = {k: row_bench[k] for k in sales_ops["features"]}
    checks["sales"] = {
        "operational_input": row_ops,
        "pre_contact_prediction": round4(sales_ops["pipeline"].predict_proba(pd.DataFrame([row_ops]))[0, 1]),
        "research_benchmark_input": row_bench,
        "posthoc_benchmark_prediction": round4(sales_bench["pipeline"].predict_proba(pd.DataFrame([row_bench]))[0, 1]),
    }
    # Parent
    parent = joblib.load(MODELS / "parent_mind.joblib")
    parent_row = {
        "Medu": 3, "Fedu": 3, "Pstatus": "T", "famsup": "yes", "paid": "no",
        "schoolsup": "no", "studytime": 2, "famrel": 4, "internet": "yes",
        "address": "U", "subject": "math",
    }
    checks["parent"] = {
        "input": parent_row,
        "high_absence_risk_proxy": round4(parent["pipeline"].predict_proba(pd.DataFrame([parent_row]))[0, 1]),
    }
    # Institution
    inst = joblib.load(MODELS / "institution_mind.joblib")
    sample = pd.read_parquet(DATA / "oulad_engineered.parquet", columns=inst["features"]).dropna().head(1).copy()
    for c in ["code_module", "code_presentation"]:
        sample[c] = sample[c].astype("category").cat.codes
    checks["institution"] = {
        "input": {k: (int(v) if isinstance(v, np.integer) else float(v) if isinstance(v, np.floating) else v) for k, v in sample.iloc[0].items()},
        "weekly_attrition_risk_proxy": round4(inst["model"].predict_proba(sample)[0, 1]),
    }
    return checks

def plot_ablations(student, sales):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for ax, results, title in [
        (axes[0], student, "StudentMind leakage ablation (AUC)"),
        (axes[1], sales, "SalesMind leakage ablation (AUC)"),
    ]:
        names = list(results)
        vals = [results[k]["auc"] for k in names]
        colors = ["#236B8E" if i == 0 else "#D08C60" for i in range(len(names))]
        ax.barh(range(len(names)), vals, color=colors)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels([n.replace("_", " ") for n in names], fontsize=8)
        ax.set_xlim(0, 1.05)
        ax.set_xlabel("AUC")
        ax.set_title(title)
        ax.grid(axis="x", alpha=0.2)
        for i, v in enumerate(vals):
            ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_ablation_auc.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    print("[1/5] hashing datasets")
    files = [
        DATA / "assistments2009.csv",
        DATA / "talkmoves_annotated.parquet",
        DATA / "oulad_engineered.parquet",
        DATA / "student_performance_uci" / "student-mat.csv",
        DATA / "student_performance_uci" / "student-por.csv",
    ]
    hashes = {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in files}
    print("[2/5] student ablation")
    student, student_meta = student_ablations()
    print("[3/5] sales ablation")
    sales, sales_meta = sales_ablations()
    print("[4/5] model checks and sensitivity")
    inference = inference_checks()
    parent = parent_sensitivity()
    institution = institution_sensitivity()
    print("[5/5] saving")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "sklearn": sklearn.__version__,
        },
        "data_hashes": hashes,
        "student": {"meta": student_meta, "ablations": student},
        "sales": {"meta": sales_meta, "ablations": sales},
        "parent": {"sensitivity": parent},
        "institution": {"sensitivity": institution},
        "inference_checks": inference,
    }
    save_json("ablation_and_validation.json", payload)
    save_json("model_inference_checks.json", inference)
    rows = []
    for role, section in [("student", student), ("sales", sales)]:
        for variant, m in section.items():
            rows.append({"role": role, "variant": variant, "auc": m.get("auc"), "ap": m.get("ap"), "logloss": m.get("logloss"), "brier": m.get("brier")})
    pd.DataFrame(rows).to_csv(OUT / "ablation_summary.csv", index=False, encoding="utf-8-sig")
    plot_ablations(student, sales)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()



