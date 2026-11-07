# Candidate batch 1 results (preregistration: `03b_*`)

2,052 runs, registry `registry_q1_cand.sqlite`, summary `q1_baselines_summary_cand.csv`; analysis `scripts/sota_search/analyze_candidates.py`.

## X1: tight one-sided bet cap (extra candidate from experimental results)
Power on the 9 harm worlds, paired over (frac, delay, tol, world), 162 cells per parent:

| Parent → tight | overall power loose → tight | mean paired diff | **median** paired diff | tight better / worse |
|---|---|---|---|---|
| `pprm` → `pprm_tight` | 0.130 → 0.246 | +0.116 | **+0.025** | 66% / 4% |
| `pp_cost` → `pp_cost_tight` | 0.034 → 0.119 | +0.085 | **+0.040** | 88% / 0% |

Null false alarm of the tight versions: mean 0.007 / 0.005, max 0.025 / 0.015 (validity preserved).
**Preregistered falsification rule: the claim fails if the median paired difference is below +0.05. It is +0.025 and +0.040, so X1 is NOT supported under the registered criterion**, although the effect is one-directional (never materially worse) and large in the mean. The median is low because many (frac, delay, tol, world) cells have near-zero power for both versions; the gain is concentrated in informative regimes (mean +0.164 at 10% labels for `pprm`). More important, X1 corrects my own over-conservative baseline (see `04_*`), so even a pass would not be a contribution over a properly implemented PPRM-style detector.

## S01: decision-harm-aware PPRM (`pp_cost_tight` vs `pprm_tight`)
| | power (harm) | false alarm (benign) | `prior`-world false alarm | harm before alarm |
|---|---|---|---|---|
| `pprm_tight` (predictive risk) | 0.246 | 0.026 | 0.092 | 190 |
| `pp_cost_tight` (decision cost) | 0.119 | 0.006 | 0.007 | 206 |

Registered failure condition ("its power on harm worlds is lower") **is met**. The partial support: the decision-cost version removes the false alarms where predictive loss rises but decision cost falls (`prior`: 0.092 → 0.007), as hypothesized, but pays about half the detection power. S01 as stated is NOT supported; the trade-off is a documented regime effect.

## S02: Shiryaev–Roberts multi-start form
| | power (harm) | false alarm (benign) | null false alarm (mean, max) | harm before alarm |
|---|---|---|---|---|
| `pprm_tight` | 0.246 | 0.026 | 0.007, 0.025 | 190 |
| `sr_brier_tight` | 0.604 | 0.178 | **0.123, 0.290** | 150 |
| `sr_cost_tight` | 0.545 | 0.060 | 0.048, 0.095 | 155 |

The multi-start form cuts harm accrued before the alarm (190 → 150) but its empirically calibrated threshold does **not** hold on fresh null streams for the Brier version (mean 0.123, max 0.290), so its power is inflated by miscalibration. Restricted to calibration-eligible configurations the best SR variant reaches 0.65 screen, below Page–Hinkley (0.671). S02 loses to the classical detectors on harm before alarm (115–126 vs 112–119 for PH/two-window/CUSUM, same range) and is **not supported** as an improvement; the calibration instability is itself a finding.
