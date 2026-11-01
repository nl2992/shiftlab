# Common failures and novelty opportunities

Source: `scripts/sota_search/failure_matrix.py` over the full registry (4,275 unique runs, 225 configurations, 19 development worlds), restricted to calibration-eligible configurations (null false alarm ≤ 0.07; 202 of 225).

## Cross-method failure matrix (summary of measurements)
| # | Pattern | Evidence | Families affected | Persists after tuning? |
|---|---|---|---|---|
| F1 | **Feature-space shift detectors cannot separate harm from benign change.** Power on harmful concept shifts ≤ 0.05; false alarm up to 1.00 on large benign covariate shifts | MMD, C2ST, BBSD best-config power 0.02–0.05 on every harm world; lowest achievable false alarm 1.00 on `cov_benign` (MMD, C2ST) and `cov_inform` (BBSD, C2ST, MMD) | 3 unlabeled families | Yes (every window size) |
| F2 | **Transient harm is missed by every family.** Best-config power on `concept/transient/1.5` ≤ 0.34 for all 14 families; 0.55 at δ=2 and 0.72 at δ=3 | Failure matrix | all labeled families | Yes. May be partly information-limited (about 80 labels fall inside a 400-step transient at 20% labels) |
| F3 | **Slow adaptation after a change.** Mean detection delay is about 500–700 steps for the e-process family even on abrupt, large shifts | `pprm_tight` delay 515, `pp_cost_tight` 654 vs CUSUM 399 | `pprm`, `pp_cost` (loose and tight) | Yes. Plausible cause: the plug-in Kelly bet averages all history, so it stays near zero after a change |
| F4 | **Decision-cost evidence trades power for benign-shift robustness.** `pp_cost_tight` power 0.12 vs `pprm_tight` 0.25 overall, but `prior`-world false alarm 0.007 vs 0.092 | `06_*` | e-process family | Yes |
| F5 | **Label rate dominates, delay does not.** Median power 0.14 / 0.25 / 0.40–0.45 at 5% / 10% / 20% labels; nearly flat across delay 0 / 5 / 20 | Failure matrix | all labeled families | Yes |
| F6 | **Over-conservative theory methods.** Stitched-Hoeffding CS never alarms (power 0.000); loose-cap e-processes 5–8× weaker than tight | `04_*`, `06_*` | CS and loose e-process | Fixed for e-processes by the tight cap (a baseline correction, not a method) |
| F7 | **Calibration drift of empirical thresholds.** 23 of 225 configurations exceed 0.07 null false alarm on fresh streams, up to 0.29 | `05_*` | SR e-detectors, two-window, CUSUM | Yes for heavy-tailed statistics |

F6 and F7 are implementation or evaluation findings and are not treated as algorithmic opportunities.

## Candidate shared mechanisms and ranked fixes
1. **F3 and F2 share a plausible cause: bet adaptation lag.** A discounted (forgetful) plug-in Kelly bet adapts after a change while remaining predictable, hence valid. It can be applied to both tight e-process parents (`pprm_tight`, `pp_cost_tight`), i.e. at least two parents. *Fix DK.*
2. **F4 suggests a hybrid of two parents.** The Brier evidence has power; the decision-cost evidence knows when a shift actually costs. Gate the Brier bet on non-negative decision-cost evidence from the same labels (a predictable bet, still valid). *Fix HG.*
3. **F5 and F2 suggest label allocation toward the decision boundary**, where harm manifests (false negatives pile up for scores just below the decision threshold), instead of uniform querying. Applicable to both parents. *Fix BD.*

Not selected: anything addressing F1 (that is the point of the benchmark: unlabeled discrepancy detectors are not harm detectors); BOCPD and Q2/Q3 candidates are open work.
