# Search space and preregistration (frozen before any grid run)

## Pools
- **Calibration pool (null):** `none`, `T = 2000`, 400 seeds, seed block 9000; used only to set empirical thresholds (`1−α` quantile of the horizon maximum, `α = 0.05`).
- **Development pool (G1):**
  - harm worlds: `concept` δ ∈ {1.5, 2, 3} × shape ∈ {abrupt, gradual, transient}; `subgroup` δ = 4 abrupt;
  - benign-shift worlds: `cov_benign` δ ∈ {2, 3} abrupt and gradual; `cov_inform` δ ∈ {1, 2} abrupt; `prior` δ ∈ {1, 2} abrupt;
  - null world: `none`.
  Shift onset `t0 = 800` (reference window precedes it). 200 seeds per world, seed block 1000.
- **Held-out confirmation pool (never used for selection):** G1 with *different* δ, onsets and schedules (recurrent, onset 500 and 1100, δ = 1.2, 2.5), plus the unimplemented families G2 and G3 once built. 400 seeds, seed block 5000.

## Metrics (per detector and world, over seeds)
Detection probability after harm onset; false-alarm probability (alarm before the first harmful step, or any alarm in a world with no harmful step); mean detection delay in steps after harm onset; cumulative expected decision harm accrued before the alarm; labels used by the alarm.

## Screening metric and survival rule
`screen = mean over harm worlds of detection probability − mean over benign-shift worlds of false-alarm probability`, each world weighted equally. Worlds with undefined delay are excluded from delay averages only. Survival: the top 30% by `screen` at each halving round (seed counts 50 → 100 → 200), plus any configuration that is best by detection delay or by cumulative harm within some harm-world family (a regime winner is preserved). Ties go to lower runtime.

## Configuration axes (valid combinations only; no full Cartesian product)
```text
detector: mmd, c2st, bbsd, cusum, page_hinkley, twowin, pr_cs, pprm, watch, pp_cost
frac (labeled detectors): 0.05, 0.10, 0.20
delay (labeled detectors): 0, 5, 20
window / stride (mmd, c2st, bbsd): 50, 100, 200 / 20
slack, delta, w (cusum, page_hinkley, twowin): small grids
tolerance tol (prediction-powered detectors): 0, 0.05
```
Candidate families S01–S06 add: risk type (decision cost vs Brier), multi-resolution reset times, proxy-reliance gating, and query allocation (uniform, residual-variance, growth-aware, mixtures), each introduced through a documented modification record (parent, change, predicted benefit, failure condition).

## Contracts that must not be mixed in one claim
Unlabeled shift detectors (MMD, C2ST, BBSD) detect distribution change and have no label cost; labeled monitors (risk CS, PPRM, e-processes, CUSUM) pay for labels with delay. Both are reported but compared only on the harm-specific metrics above, and any "win" is stated within its contract.

## Compute budget
At most about 6 CPU-hours in total; each batch stops cleanly at a declared wall-clock limit; every attempted run is recorded in the registry, including failures.
