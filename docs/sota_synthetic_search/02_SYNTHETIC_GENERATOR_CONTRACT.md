# Synthetic generator contract

Code: `src/shiftlab/sota_search/generators.py`. Streams are `S` independent replicates of length `T = 2000`, `d = 4` features, `X ~ N(μ_t, I)`, `P(y=1|x) = σ(w_t·x + b_t + subgroup term)`. The deployed model is the source Bayes classifier and takes cost-sensitive decisions (`FN = 5`, `FP = 1`, predict positive when `p ≥ 1/6`). Source mean decision cost 0.409.

**Shift kinds** (strength `m(t) ∈ [0,1]` follows an abrupt, gradual, transient or recurrent schedule): `none`; `cov_benign` (nuisance-dimension mean shift); `cov_inform` (mean shift along an informative direction); `prior` (intercept); `concept` (rotated informative weights); `subgroup` (conditional change only where `x₂ > 1`).

**Three separately measured dimensions** (evaluator-only, Monte Carlo at 11 strengths, interpolated along the schedule): distribution discrepancy (RBF MMD² between source and shifted joint `(x, y)`), predictive deterioration (change in Brier score), and decision harm (change in expected decision cost). A step is *harmful* when decision harm ≥ 0.10.

**Disagreement is built in and tested** (`tests/sota_search/test_generators.py`), at full strength:

| World | Discrepancy | Predictive change | Decision harm |
|---|---|---|---|
| `cov_benign` δ=3 | 0.296 | 0.000 | +0.001 |
| `concept` δ=2 | 0.0035 | +0.095 | +0.233 |
| `concept` δ=1 | 0.0012 | +0.042 | +0.094 |
| `cov_inform` δ=2 | 0.192 | −0.086 | −0.292 (cost falls) |
| `prior` δ=1 | 0.0028 | +0.017 | −0.032 |
| `subgroup` δ=4 | 0.0006 | +0.023 | +0.058 |

**Families.** G1 (this file) is implemented. G2 (nonlinear, heterogeneous), G3 (Markov-switching regimes) and G4 (finance-style decisions) are **not yet implemented**; G2 and G3 are reserved as the held-out generator families for confirmation, so detectors and candidates must not be tuned on them.

**Information rules.** Detectors receive only `x`, `y` (when queried and resolved), model score `p`, and nominal source statistics estimated from an independent source stream. Ground-truth arrays are never passed.
