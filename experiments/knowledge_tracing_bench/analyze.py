# -*- coding: utf-8 -*-
"""知识追踪基准：分析、图表与报告。"""
from __future__ import annotations

import io
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from ktbench import metrics as M
from ktbench import tender as T
from ktbench.data import filter_skills, load_assistments, split_by_student

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "outputs"
_FONT = pathlib.Path(r"D:\Tender\external_corpus_report\fonts\simhei.ttf")
if _FONT.exists():
    font_manager.fontManager.addfont(str(_FONT))
    _NAME = font_manager.FontProperties(fname=str(_FONT)).get_name()
    matplotlib.rcParams["font.sans-serif"] = [_NAME, "Microsoft YaHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False


def logistic_baseline(tr, te, y_te):
    """控制组：用"学生历史均值 + 技能均值 + 位置"做逻辑回归。"""
    from sklearn.linear_model import LogisticRegression

    def feats(df, ref_mean):
        rows = []
        hist = {}
        pos = {}
        for _, g in df.groupby("user_id", sort=False):
            run = 0.0
            for i, (sk, y) in enumerate(zip(g["skill_name"], g["correct"])):
                n = hist.get("_n_" + sk, 0)
                h = run / i if i > 0 else ref_mean
                rows.append([h, ref_mean, np.log1p(i), np.log1p(n), 1.0 if sk not in pos else 0.0])
                run += y
                hist["_n_" + sk] = n + 1
                pos[sk] = 1
        return np.asarray(rows)

    ref = tr["correct"].mean()
    Xtr = feats(tr, ref)
    # 技能均值先验并入
    sm = tr.groupby("skill_name")["correct"].mean().to_dict()
    Xtr[:, 1] = tr["skill_name"].map(sm).fillna(ref).to_numpy()
    Xte = feats(te, ref)
    Xte[:, 1] = te["skill_name"].map(sm).fillna(ref).to_numpy()
    model = LogisticRegression(max_iter=2000)
    model.fit(Xtr, tr["correct"].to_numpy())
    return model.predict_proba(Xte)[:, 1]


def eta_sensitivity(tr, te, skill_index, y_te):
    """固定 ξ=0，扫描 η，记录训练 loglik 与测试 loglik/AUC。"""
    tr_seqs = [(g["skill_name"].to_numpy(), g["correct"].to_numpy())
               for _, g in tr.groupby("user_id", sort=False)]
    te_seqs = [(g["skill_name"].to_numpy(), g["correct"].to_numpy())
               for _, g in te.groupby("user_id", sort=False)]
    obs_tr, mask_tr, sidx_tr = T.build_padded(tr_seqs, skill_index)
    obs_te, mask_te, sidx_te = T.build_padded(te_seqs, skill_index)
    n_sk = len(skill_index)
    ytr_b = obs_tr == 1
    yte_b = obs_te == 1
    rows = []
    for eta in [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.45, 0.60, 0.80]:
        p_tr = T.predict_padded(obs_tr, mask_tr, sidx_tr, n_sk, 1.3417, eta, 0.0)
        p_te_m = T.predict_padded(obs_te, mask_te, sidx_te, n_sk, 1.3417, eta, 0.0)
        p_te = np.concatenate([p_te_m[i, : len(o)] for i, (_, o) in enumerate(te_seqs)])
        ll_tr = float(np.where(ytr_b, np.log(p_tr), np.log(1 - p_tr))[mask_tr].sum())
        rows.append({"eta": eta, "train_loglik": ll_tr / mask_tr.sum(),
                     "test_loglik": M.log_loss(y_te, p_te),
                     "test_auc": M.auc(y_te, p_te)})
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = filter_skills(load_assistments(), 200)
    tr, te = split_by_student(df, 0.2)
    tr = tr.sort_values(["user_id", "order_id"]).reset_index(drop=True)
    te = te.sort_values(["user_id", "order_id"]).reset_index(drop=True)
    y_te = te["correct"].to_numpy()
    skill_index = {s: i for i, s in enumerate(sorted(df["skill_name"].unique()))}

    preds = pd.read_parquet(OUT / "test_predictions.parquet")
    assert len(preds) == len(te)

    print("计算逻辑回归控制组 ...", flush=True)
    p_lr = logistic_baseline(tr, te, y_te)

    print("扫描 η ...", flush=True)
    eta_df = eta_sensitivity(tr, te, skill_index, y_te)
    eta_df.to_csv(OUT / "eta_sensitivity.csv", index=False, encoding="utf-8-sig")

    # ---------------- 图 1：模型对比 ----------------
    metrics = pd.read_csv(OUT / "metrics.csv")
    metrics = pd.concat([metrics, pd.DataFrame([{
        "model": "Logistic (hist+skill+pos)", "params": "控制组",
        "auc": round(M.auc(y_te, p_lr), 4),
        "rmse": round(M.rmse(y_te, p_lr), 4),
        "logloss": round(M.log_loss(y_te, p_lr), 4)}])], ignore_index=True)
    metrics.to_csv(OUT / "metrics_with_lr.csv", index=False, encoding="utf-8-sig")

    labels = metrics["model"].tolist()
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.6))
    for ax, col, title, color in zip(axes, ["auc", "rmse", "logloss"],
                                     ["AUC（越高越好）", "RMSE（越低越好）", "LogLoss（越低越好）"],
                                     ["#2f6fb5", "#e07b39", "#8c5aa8"]):
        vals = metrics[col].tolist()
        ax.barh(labels, vals, color=color)
        ax.invert_yaxis()
        ax.set_title(title)
        ax.grid(axis="x", alpha=0.25)
        for i, v in enumerate(vals):
            ax.text(v, i, f" {v:.3f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_model_comparison.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # ---------------- 图 2：校准曲线 ----------------
    def calib(p, y, bins=12):
        q = np.quantile(p, np.linspace(0, 1, bins + 1))
        q[0], q[-1] = -0.01, 1.01
        idx = np.digitize(p, q[1:-1])
        xs, ys = [], []
        for b in range(bins):
            m = idx == b
            if m.sum() > 30:
                xs.append(p[m].mean()); ys.append(y[m].mean())
        return np.array(xs), np.array(ys)

    fig, ax = plt.subplots(figsize=(6.4, 6))
    ax.plot([0, 1], [0, 1], "--", color="#888", label="完美校准")
    for col, lab, c in [("pred_bkt", "BKT", "#2f6fb5"),
                        ("pred_tender_perskill", "Tender θ（分技能）", "#e07b39"),
                        ("pred_tender_default", "Tender θ（文档默认 η=0.3）", "#c0392b")]:
        xs, ys = calib(preds[col].to_numpy(), y_te)
        ax.plot(xs, ys, "o-", color=c, label=lab, markersize=4)
    ax.set_xlabel("模型预测的答对概率")
    ax.set_ylabel("实际答对频率")
    ax.set_title("概率校准（越贴近对角线越好）")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "fig_calibration.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # ---------------- 图 3：分技能对比 ----------------
    per = []
    for sk, g in preds.groupby("skill_name"):
        if g["correct"].nunique() < 2 or len(g) < 60:
            continue
        per.append({"skill": sk, "n": len(g),
                    "auc_bkt": M.auc(g["correct"], g["pred_bkt"]),
                    "auc_tender": M.auc(g["correct"], g["pred_tender_perskill"])})
    per = pd.DataFrame(per)
    per["delta"] = per["auc_tender"] - per["auc_bkt"]
    per.to_csv(OUT / "per_skill_auc.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    ax.scatter(per["auc_bkt"], per["auc_tender"], s=np.clip(per["n"] / 40, 8, 160),
               alpha=0.6, color="#2f6fb5", edgecolor="white")
    lim = [0.4, 0.95]
    ax.plot(lim, lim, "--", color="#888")
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("BKT 分技能 AUC")
    ax.set_ylabel("Tender θ 分技能 AUC")
    ax.set_title(f"分技能 AUC 对比（点大小=样本量，共 {len(per)} 个技能）")
    ax.grid(alpha=0.25)
    box = (f"Tender 更好: {(per['delta']>0).sum()} 个\nBKT 更好: {(per['delta']<0).sum()} 个\n"
           f"中位差: {per['delta'].median():+.4f}")
    ax.text(0.03, 0.97, box, transform=ax.transAxes, va="top", fontsize=10,
            bbox=dict(boxstyle="round", fc="#f6f6f6", ec="#bbb"))
    fig.tight_layout()
    fig.savefig(OUT / "fig_per_skill_scatter.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # ---------------- 图 4：η 敏感性 ----------------
    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(eta_df["eta"], eta_df["test_auc"], "o-", color="#2f6fb5", label="测试 AUC")
    ax1.set_xlabel("η（每步 θ 的更新幅度）")
    ax1.set_ylabel("测试 AUC", color="#2f6fb5")
    ax1.tick_params(axis="y", labelcolor="#2f6fb5")
    ax1.grid(alpha=0.25)
    ax2 = ax1.twinx()
    ax2.plot(eta_df["eta"], eta_df["test_loglik"], "s--", color="#c0392b", label="测试 LogLoss")
    ax2.set_ylabel("测试 LogLoss", color="#c0392b")
    ax2.tick_params(axis="y", labelcolor="#c0392b")
    ax1.axvline(0.3, color="#555", linestyle=":", linewidth=1.5)
    ax1.text(0.31, ax1.get_ylim()[0], " 文档默认 η=0.3", fontsize=9, color="#555")
    ax1.set_title("η 敏感性：AUC 与概率校准的矛盾")
    fig.tight_layout()
    fig.savefig(OUT / "fig_eta_sensitivity.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # ---------------- 图 5：示例 θ 轨迹 ----------------
    sample_user = None
    for uid, g in te.groupby("user_id"):
        if 25 <= len(g) <= 45 and g["skill_name"].nunique() >= 3:
            sample_user = uid; break
    g = te[te["user_id"] == sample_user].sort_values("order_id")
    obs = g["correct"].to_numpy()
    sk = g["skill_name"].to_numpy()
    th = T.prob_to_theta(0.65)
    traj = []
    states = {}
    last = None
    eta_demo = 0.02
    for t in range(len(obs)):
        k = sk[t]
        cur = states.get(k, th)
        traj.append(cur)
        trend = 1.0 if obs[t] == 0 else -1.0
        states[k] = float(np.clip(cur + eta_demo * trend, 0.0, np.pi))
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.plot(range(1, len(traj) + 1), traj, "-", color="#2f6fb5", label="θ（当前作答的融合角）")
    ok = obs == 1
    ax.scatter(np.arange(1, len(obs) + 1)[ok], np.asarray(traj)[ok], color="#2e8b57", s=28, label="答对", zorder=3)
    ax.scatter(np.arange(1, len(obs) + 1)[~ok], np.asarray(traj)[~ok], color="#c0392b", s=28, label="答错", zorder=3)
    ax.axhline(T.THETA_TH, color="#e07b39", linestyle="--", label=f"θ_th = {T.THETA_TH:.3f}")
    ax.set_xlabel("作答序号")
    ax.set_ylabel("θ（0=完全区分，π=完全融合）")
    ax.set_title(f"示例学生 θ 轨迹（用户 {sample_user}，{len(obs)} 次作答，η={eta_demo}）")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT / "fig_theta_trajectory.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    summary = {
        "models": metrics.to_dict(orient="records"),
        "per_skill": {
            "n_skills": int(len(per)),
            "tender_better": int((per["delta"] > 0).sum()),
            "bkt_better": int((per["delta"] < 0).sum()),
            "median_delta": float(per["delta"].median()),
        },
        "eta_sensitivity": eta_df.to_dict(orient="records"),
        "sample_user": int(sample_user),
    }
    (OUT / "analysis_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["per_skill"], ensure_ascii=False, indent=2), flush=True)
    print("figures written", flush=True)


if __name__ == "__main__":
    main()
