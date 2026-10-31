"""Synthetic multi-arm experiment for the dynamic golden-bias regulator.

This is an in-silico mechanism test, not a human efficacy trial.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SEED = 20261101
N_PER_ARM = 1000
DAYS = 84
MINOR_FLOOR = 0.382
MAJOR_CEILING = 0.618
OUT = Path(__file__).resolve().parent
ARMS = ("no_regulation", "fixed_50", "fixed_band", "dynamic_golden")


def clip(value, low, high):
    return max(low, min(high, value))


def make_profiles():
    rng = np.random.default_rng(SEED)
    profiles = []
    for i in range(N_PER_ARM):
        base_pref = clip(0.5 + rng.normal(0, 0.18), 0.12, 0.88)
        profiles.append({
            "learner": i,
            "base_pref": base_pref,
            "shock": rng.normal(0, 0.035, DAYS),
            "fatigue_noise": rng.normal(0, 0.015, DAYS),
            "calibration_noise": rng.normal(0, 0.04, DAYS),
        })
    return profiles


def inside_band(learning_share):
    return MINOR_FLOOR <= learning_share <= MAJOR_CEILING


def simulate_learner(profile, arm):
    rng = np.random.default_rng(SEED + profile["learner"] * 37 + ARMS.index(arm) * 100003)
    knowledge = 0.20
    branching = 0.04
    debt = 0.0
    fatigue = 0.12
    offset = 0.0
    history = []
    burden = 0
    recovery = []
    calibration_events = 0
    creation_events = 0
    balance_days = 0
    for day in range(DAYS):
        phase_learning_target = 0.618 if knowledge < 0.58 else 0.50
        phase_creation_target = 0.382 if knowledge >= 0.52 and branching >= 0.10 else 0.50
        preferred_target = phase_learning_target if branching < knowledge * 0.55 else phase_creation_target
        long_window = history[-28:] or [profile["base_pref"]]
        short_window = history[-7:] or [profile["base_pref"]]
        long_share = float(np.mean(long_window))
        short_share = float(np.mean(short_window))
        target = profile["base_pref"]
        adjust = 0.0
        if arm == "fixed_50":
            target = 0.5
            if abs(long_share - 0.5) > 0.04:
                adjust = 0.16 * (target - profile["base_pref"] - offset)
                burden += 1
        elif arm == "fixed_band":
            target = clip(profile["base_pref"], MINOR_FLOOR, MAJOR_CEILING)
            if day % 7 == 0 and not inside_band(long_share):
                outside_target = MINOR_FLOOR if long_share < MINOR_FLOOR else MAJOR_CEILING
                adjust = 0.18 * (outside_target - profile["base_pref"] - offset)
                burden += 1
        elif arm == "dynamic_golden":
            target = preferred_target
            short_inside = inside_band(short_share)
            long_inside = inside_band(long_share)
            due = (not short_inside and not long_inside) or (not short_inside and day % 7 == 0)
            if due:
                adjust = 0.14 * (target - profile["base_pref"] - offset)
                burden += 1
        offset = clip(offset * 0.82 + adjust, -0.24, 0.24)
        learning = clip(profile["base_pref"] + offset + profile["shock"][day], 0.08, 0.92)
        creation = 1.0 - learning
        calibration_prob = clip(0.16 + 0.50 * learning + profile["calibration_noise"][day], 0.08, 0.88)
        if arm in {"fixed_band", "dynamic_golden"} and creation > MAJOR_CEILING:
            calibration_prob = clip(calibration_prob + 0.10, 0.08, 0.94)
        calibrated = rng.random() < calibration_prob
        creation_events += 1
        if calibrated:
            calibration_events += 1
        novelty = clip(0.25 + 0.72 * knowledge - 0.22 * abs(learning - 0.5), 0.05, 0.95)
        knowledge = clip(knowledge + 0.020 * learning * (0.55 + 0.75 * knowledge) * (1 - 0.35 * fatigue), 0.0, 1.0)
        branching = clip(branching + 0.018 * creation * (0.18 + 1.05 * knowledge) * (0.65 + novelty), 0.0, 1.0)
        debt = clip(debt + 0.045 * creation * (1 - calibration_prob) - (0.060 if calibrated else 0), 0.0, 1.0)
        fatigue = clip(0.88 * fatigue + 0.035 + 0.12 * abs(learning - 0.5) + 0.025 * creation * (1 - calibration_prob) + profile["fatigue_noise"][day], 0.0, 1.0)
        history.append(learning)
        if day >= 7 and inside_band(float(np.mean(history[-7:]))):
            balance_days += 1
        recovery.append(1 / (1 + np.exp(-5 * (0.15 + 0.7 * knowledge + 0.6 * branching - 0.5 * debt - 0.35 * fatigue - 0.20))))
    novelty_sustain = branching / (knowledge + branching + 1e-6)
    return {
        "action_recovery": float(np.mean(recovery[-28:])),
        "knowledge": float(knowledge),
        "branching": float(branching),
        "novelty_sustain": float(novelty_sustain),
        "post_creation_calibration": float(calibration_events / creation_events),
        "band_inside": float(balance_days / max(1, DAYS - 7)),
        "burden": float(burden),
        "fatigue": float(fatigue),
    }


def bootstrap_ci(values, rng, n_boot=2000):
    values = np.asarray(values, dtype=float)
    means = []
    for _ in range(n_boot):
        means.append(float(np.mean(rng.choice(values, size=len(values), replace=True))))
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def main():
    profiles = make_profiles()
    raw = {arm: [] for arm in ARMS}
    for arm in ARMS:
        for profile in profiles:
            raw[arm].append(simulate_learner(profile, arm))
    metrics = ("action_recovery", "knowledge", "branching", "novelty_sustain", "post_creation_calibration", "band_inside", "burden", "fatigue")
    rng = np.random.default_rng(SEED + 99)
    summaries = {}
    for arm in ARMS:
        summaries[arm] = {}
        for metric in metrics:
            values = [row[metric] for row in raw[arm]]
            summaries[arm][metric] = {
                "mean": float(np.mean(values)),
                "sd": float(np.std(values, ddof=1)),
                "ci95": bootstrap_ci(values, rng),
            }
    pairwise = {}
    for control in ("no_regulation", "fixed_50", "fixed_band"):
        pairwise[control] = {}
        for metric in metrics:
            x = np.asarray([row[metric] for row in raw["dynamic_golden"]])
            y = np.asarray([row[metric] for row in raw[control]])
            diff = x - y
            ci = bootstrap_ci(diff, rng)
            pairwise[control][metric] = {
                "mean_difference": float(np.mean(diff)),
                "ci95": ci,
                "synthetic_significant_95": not (ci[0] <= 0 <= ci[1]),
            }
    result = {
        "version": "golden-bias-experiment-1.0",
        "design": "in_silico_multi_arm_simulation",
        "seed": SEED,
        "n_per_arm": N_PER_ARM,
        "days": DAYS,
        "arms": list(ARMS),
        "band": {"minor_floor": MINOR_FLOOR, "major_ceiling": MAJOR_CEILING},
        "summaries": summaries,
        "pairwise_vs_dynamic_golden": pairwise,
        "boundary": "Synthetic mechanism test only. Results do not establish human learning, relationship or clinical effects.",
    }
    (OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Dynamic Golden-Bias Regulation — Synthetic Experiment", "", f"- Seed: {SEED}", f"- Learners per arm: {N_PER_ARM}", f"- Days: {DAYS}", "", "| Arm | Recovery | Knowledge | Novelty | Calibration | In-band | Burden | Fatigue |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        s = summaries[arm]
        lines.append(f"| {arm} | {s['action_recovery']['mean']:.3f} | {s['knowledge']['mean']:.3f} | {s['novelty_sustain']['mean']:.3f} | {s['post_creation_calibration']['mean']:.3f} | {s['band_inside']['mean']:.3f} | {s['burden']['mean']:.1f} | {s['fatigue']['mean']:.3f} |")
    lines += ["", "## Hypotheses", "", "- H1: dynamic golden-bias increases time inside the 38.2/61.8 band versus no regulation.", "- H2: dynamic golden-bias uses fewer prompts than fixed 50:50 while preserving action recovery.", "- H3: dynamic golden-bias improves novelty and post-creation calibration versus a fixed band."]
    lines += ["", "## Pairwise differences: dynamic golden minus control", "", "| Control | Metric | Mean difference | 95% bootstrap CI | CI excludes zero |", "|---|---|---:|---:|:---:|"]
    for control in ("no_regulation", "fixed_50", "fixed_band"):
        p = pairwise[control]
        for metric in metrics:
            item = p[metric]
            lines.append(f"| {control} | {metric} | {item['mean_difference']:.3f} | [{item['ci95'][0]:.3f}, {item['ci95'][1]:.3f}] | {'yes' if item['synthetic_significant_95'] else 'no'} |")
    lines += ["", "## Interpretation", "", "- Versus no regulation, dynamic golden-bias improves action recovery, calibration and time inside the band, but it adds prompts.", "- Versus fixed 50:50, dynamic golden-bias uses about half the prompts and slightly improves calibration, but fixed 50:50 keeps more time inside the strict band.", "- Versus the fixed band, dynamic golden-bias improves recovery and in-band time, but needs more prompts and does not improve calibration.", "- H1 is supported in this simulation. H2 is partially supported: burden falls sharply while recovery is preserved. H3 is not supported: novelty is similar and calibration is slightly lower than the fixed band.", "- These tradeoffs should be kept rather than hidden: the regulator is a burden-aware band rule, not a claim of universal superiority."]
    lines += ["", "## Design", "", "- Four arms: no regulation, fixed 50:50, fixed 38.2/61.8 band, and dynamic golden-bias with phase targets and hysteresis.", "- Common synthetic learner profiles are reused across arms; bootstrap intervals are paired over learner-level differences.", "- Primary outcomes: action recovery, post-creation calibration and time inside the adaptive band.", "- Secondary outcomes: knowledge, branching, novelty sustainability, burden and fatigue.", "- The simulation is deterministic for seed 20261101 and can be rerun with `python simulate_golden_bias.py`."]
    lines += ["", "## Boundary", "", "This is a synthetic multi-arm mechanism experiment. It does not prove human educational or clinical efficacy. The rule should be pre-registered and tested against simple thresholds before any strong product claim. It should not be used as a daily KPI, personality score or relationship-match score."]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({arm: {m: round(summaries[arm][m]['mean'], 4) for m in metrics} for arm in ARMS}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()