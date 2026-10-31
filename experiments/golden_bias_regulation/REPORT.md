# Dynamic Golden-Bias Regulation — Synthetic Experiment

- Seed: 20261101
- Learners per arm: 1000
- Days: 84

| Arm | Recovery | Knowledge | Novelty | Calibration | In-band | Burden | Fatigue |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_regulation | 0.884 | 0.816 | 0.457 | 0.413 | 0.474 | 0.0 | 0.500 |
| fixed_50 | 0.945 | 0.859 | 0.459 | 0.411 | 0.775 | 63.7 | 0.436 |
| fixed_band | 0.927 | 0.820 | 0.458 | 0.439 | 0.476 | 6.3 | 0.490 |
| dynamic_golden | 0.947 | 0.843 | 0.462 | 0.433 | 0.572 | 33.1 | 0.460 |

## Hypotheses

- H1: dynamic golden-bias increases time inside the 38.2/61.8 band versus no regulation.
- H2: dynamic golden-bias uses fewer prompts than fixed 50:50 while preserving action recovery.
- H3: dynamic golden-bias improves novelty and post-creation calibration versus a fixed band.

## Pairwise differences: dynamic golden minus control

| Control | Metric | Mean difference | 95% bootstrap CI | CI excludes zero |
|---|---|---:|---:|:---:|
| no_regulation | action_recovery | 0.063 | [0.054, 0.073] | yes |
| no_regulation | knowledge | 0.028 | [0.024, 0.032] | yes |
| no_regulation | branching | 0.043 | [0.039, 0.047] | yes |
| no_regulation | novelty_sustain | 0.005 | [0.002, 0.007] | yes |
| no_regulation | post_creation_calibration | 0.021 | [0.015, 0.027] | yes |
| no_regulation | band_inside | 0.099 | [0.090, 0.108] | yes |
| no_regulation | burden | 33.140 | [31.042, 35.320] | yes |
| no_regulation | fatigue | -0.040 | [-0.043, -0.037] | yes |
| fixed_50 | action_recovery | 0.002 | [0.000, 0.003] | yes |
| fixed_50 | knowledge | -0.015 | [-0.017, -0.013] | yes |
| fixed_50 | branching | -0.009 | [-0.010, -0.008] | yes |
| fixed_50 | novelty_sustain | 0.003 | [0.002, 0.003] | yes |
| fixed_50 | post_creation_calibration | 0.022 | [0.017, 0.027] | yes |
| fixed_50 | band_inside | -0.202 | [-0.219, -0.185] | yes |
| fixed_50 | burden | -30.552 | [-32.377, -28.734] | yes |
| fixed_50 | fatigue | 0.025 | [0.023, 0.026] | yes |
| fixed_band | action_recovery | 0.020 | [0.017, 0.024] | yes |
| fixed_band | knowledge | 0.023 | [0.021, 0.026] | yes |
| fixed_band | branching | 0.035 | [0.032, 0.038] | yes |
| fixed_band | novelty_sustain | 0.003 | [0.001, 0.006] | yes |
| fixed_band | post_creation_calibration | -0.005 | [-0.010, -0.000] | yes |
| fixed_band | band_inside | 0.096 | [0.088, 0.105] | yes |
| fixed_band | burden | 26.838 | [25.058, 28.767] | yes |
| fixed_band | fatigue | -0.030 | [-0.032, -0.027] | yes |

## Interpretation

- Versus no regulation, dynamic golden-bias improves action recovery, calibration and time inside the band, but it adds prompts.
- Versus fixed 50:50, dynamic golden-bias uses about half the prompts and slightly improves calibration, but fixed 50:50 keeps more time inside the strict band.
- Versus the fixed band, dynamic golden-bias improves recovery and in-band time, but needs more prompts and does not improve calibration.
- H1 is supported in this simulation. H2 is partially supported: burden falls sharply while recovery is preserved. H3 is not supported: novelty is similar and calibration is slightly lower than the fixed band.
- These tradeoffs should be kept rather than hidden: the regulator is a burden-aware band rule, not a claim of universal superiority.

## Design

- Four arms: no regulation, fixed 50:50, fixed 38.2/61.8 band, and dynamic golden-bias with phase targets and hysteresis.
- Common synthetic learner profiles are reused across arms; bootstrap intervals are paired over learner-level differences.
- Primary outcomes: action recovery, post-creation calibration and time inside the adaptive band.
- Secondary outcomes: knowledge, branching, novelty sustainability, burden and fatigue.
- The simulation is deterministic for seed 20261101 and can be rerun with `python simulate_golden_bias.py`.

## Boundary

This is a synthetic multi-arm mechanism experiment. It does not prove human educational or clinical efficacy. The rule should be pre-registered and tested against simple thresholds before any strong product claim. It should not be used as a daily KPI, personality score or relationship-match score.
