# Initial Q1 grid results

**Run:** 4,275 registry runs (225 configurations × 19 development worlds; 200 seeds each; seed block 1000), registry files `outputs/sota_search/registry_q1_{cheap,window,cand}.sqlite`, summaries `q1_baselines_summary_*.csv`, per-config table `q1_all_config_table.csv`. Roles by ground truth: **9 harm worlds** (concept shifts, all shapes), **9 benign-shift worlds** (`cov_benign`, `cov_inform`, `prior`, and the below-threshold `subgroup` world), 1 null world. Successive halving (50→100→200 seeds) was unnecessary at this cost and was replaced by running all configurations at 200 seeds, a superset of the preregistered screen.

## Calibration finding
Empirical thresholds set on a 400-seed null stream do **not** always transfer to fresh null streams. Null false-alarm exceeded 0.07 in 23 of 225 configurations (11 `sr_brier_tight`, 6 `twowin`, 3 `cusum`, and 1 each `sr_cost_tight`, `c2st`, `mmd`), up to 0.29. Screening below uses only calibration-eligible configurations (null false alarm ≤ 0.07); ineligible ones remain in the registry marked by their null rate.

## Best eligible configuration per detector
Screen = power on harm worlds − false alarm on benign-shift worlds.

| Detector (provenance) | Power (harm) | False alarm (benign) | False alarm (null) | Harm before alarm | Screen |
|---|---|---|---|---|---|
| Page–Hinkley (source-inspired) | 0.734 | 0.064 | 0.025 | 118.5 | 0.671 |
| two-window mean (local) | 0.744 | 0.081 | 0.040 | 110.9 | 0.664 |
| SR e-detector, decision cost (empirical thr.) | 0.711 | 0.058 | 0.045 | 126.1 | 0.653 |
| SR e-detector, Brier (empirical thr.) | 0.798 | 0.157 | 0.065 | 115.5 | 0.641 |
| **`pprm_tight`** (theory thr.) | 0.730 | 0.096 | 0.010 | 120.3 | 0.634 |
| CUSUM (source-inspired) | 0.671 | 0.093 | 0.050 | 111.9 | 0.578 |
| `pprm` loose (historical) | 0.586 | 0.041 | 0.000 | 154.6 | 0.544 |
| conformal martingale (unweighted WATCH) | 0.568 | 0.036 | 0.010 | 148.3 | 0.532 |
| `pp_cost_tight` | 0.369 | 0.017 | 0.010 | 178.8 | 0.352 |
| `pp_cost` loose (historical) | 0.156 | 0.001 | 0.000 | 207.9 | 0.155 |
| stitched-Hoeffding CS (P–R style) | 0.000 | 0.000 | 0.000 | 219.1 | 0.000 |
| BBSD / MMD / C2ST (unlabeled) | 0.02–0.03 | 0.25–0.68 | ≈ 0.03 | ≈ 215 | negative |

Source mean harm accrued over the horizon (no detection) is about 219–220 in these units, so "harm before alarm" 110–120 means roughly half of the avoidable cumulative harm is still incurred.

## Contract caveat
Unlabeled detectors pay no label cost; labeled ones use 20% of observations (best configs). They are compared only on the harm-specific metrics.

## Strongest valid baseline
`pprm_tight` is anytime-valid by construction (null crossing 0.010) and matches the empirically calibrated Page–Hinkley on power (0.730 vs 0.734) with somewhat higher benign false alarm (0.096 vs 0.064).
