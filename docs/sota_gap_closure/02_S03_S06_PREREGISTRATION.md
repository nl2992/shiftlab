# S03-S06 preregistration (written and committed before any S03-S06 run)

Branch `research/shiftlab-mandate-gap-closure-2026-10-30`. Synthetic data only. Engine `src/shiftlab/gap/engine.py`
(parity-tested against the legacy implementation, `tests/gap`). All arms use the **repaired** configuration
(`cap_mode="sup"`, in-order `prefix` release) unless stated; the legacy covariate-dependent cap is not used for any claim.

## Common design
* Streams T=2000, alpha=0.05, threshold log(1/alpha) on the e-process (anytime-valid under the stated null).
* Paired design: arms share worlds, seeds and the query uniform matrix (common random numbers, `qseed`). Arms with equal q_t query identical events.
* Per-seed records stored (`outputs/gap_closure/<exp>/perseed.parquet`); aggregates derived. Registry: `outputs/gap_closure/registry.sqlite` (append-only).
* Development seeds only. Nothing here is confirmation; G1/G2 held-out pools from the previous phase are not reused as untouched evidence.
* Selection across many configurations is done on development seeds; the shortlist is later frozen and re-evaluated on new seeds (Phase 12).

## S03 proxy-reliability-adaptive monitoring
Mechanism: the proxy weight theta_t in X = theta_t*proxy + (Q/q)(r - theta_t*proxy) - r0 is a predictable function of resolved labels
(PPI++-style). Any predictable theta keeps E[X | past, x] = R(x) - r0, so the supermartingale argument is unchanged; the bound used by the cap is
theta_t*pmax*(1/qmin - 1) + r0 + tol, also predictable. Gates: hard (theta in {0,1} by smoothed proxy skill), soft (theta = smoothed clipped OLS slope),
unc (soft shrunk by label count). Fallbacks when unreliable: none / uniform (theta=0) / conservative_bet (theta=0, bet halved).
Grid (mandate): window {32,64,128,256} x smoothing {.90,.95,.99} x fallback x gate x label fraction {.01,.05,.10,.20} = 432 per parent.
Execution plan: stage 1 screens all 108 (window, smoothing, fallback, gate) combinations at fraction .10 for each parent (`pprm_tight`, HG) on the dev G5 pool;
stage 2 re-runs the top 8 per parent plus any per-regime winner at all four fractions. Reported as a structured subset, not as the full 432 per parent.
Dev pool (`pools.g5_pool`): harm worlds = concept shift with proxy in {accurate, bias_after_shift, anti, subgroup, calibration, oracle_adapt}; non-harm worlds = benign covariate shift with proxy in {accurate, anti, bias_after_shift} and null with proxy in {static_bias, calibration, recover}.
**Adverse set A** (declared now) = harm worlds with proxy in {bias_after_shift, anti, subgroup, calibration}. Benign set B = harm worlds {accurate, oracle_adapt}.
**Acceptance:** a candidate improves on its parent if (i) mean power gain on A >= +0.05, (ii) mean power change on B >= -0.03, (iii) mean non-harm false alarm change <= +0.02 and per-world null false alarm <= 0.07, all at the same label fraction.

## S04 growth-aware active querying
Query score = value of labelling the current event, from the two-point loss model with P(y=1|x) estimated from resolved labels (proxy bins, shrunk to the deployed score); 'oracle_alt' uses the true P(y=1|x) (evaluator information, ORACLE) to bound what estimation costs.
Arms: uniform; variance (Neyman/ASI-like with start-prior shrinkage, the repo's residual-variance analogue); growth (estimated); growth (oracle alternative); growth_harm (weighted by estimated decision-cost excess); growth_look (wealth-urgency multiplier); budget-aware growth (hard budget B=frac*T with remaining-budget pacing).
Analytical expectation (stated before running): to second order in the bet, E log(1+lambda X) = lambda*m(x) - lambda^2/2 (m(x)^2 + (1/q-1) v(x)); m(x) does not depend on q, so growth-optimal q at fixed lambda is Neyman, q ~ sqrt(v(x)). Growth-aware and variance-only querying should then differ only through higher-order terms, the cap coupling and estimation error. **Hypothesis H4: growth-aware does not beat variance-only by more than +0.03 mean power.**
Worlds: G1 dev harm worlds (concept abrupt/gradual/transient d=1.5,2,3; subgroup), G2 concept, G3 recurrent, G4 finance; non-harm: cov_benign, cov_inform, prior, null. Label fractions {.05,.10}, delay {5,20}, parents `pprm_tight` and HG.
**Acceptance:** improves over the best of {uniform, variance, robust mixture} at matched hard budget if mean harm-world power gain >= +0.03, no harm world worse than -0.03 in more than 25% of worlds, non-harm false alarm change <= +0.02.

## S05 robust growth/variance hybrid
Mixtures of propensities q = u*frac + v*q_var + g*q_growth over the full probability simplex grid (u in {0,.1,.25,.5,.75,1}, g in {0,.25,.5,.75,1}, u+g<=1; v=1-u-g) x reliability mode {fixed, adaptive (shares scaled by label confidence), conservative (u>=.5)}. Parent: HG, fraction .10, delay 5. Comparators: uniform, pure variance, pure growth, Robust-ASI analogue = (u=.5, v=.5). The published Robust-ASI guarantees are estimator-side and are **not** claimed for any mixture here.
**Acceptance:** Pareto position over the robust-ASI analogue on (harm power, non-harm false alarm, power in the two worst worlds).

## S06 budget-paced delayed query allocation
Hard pathwise budget B=frac*T charged when issued; exhausted paths become inactive (no evidence, factor 1). Pacing rules: none (Bernoulli q=frac), const, remaining, info_value, reserve, two_stage, growth_pace; short-horizon DP and exact references only on the small RPOQ instances (`dive.rpoq_exact`).
Grid: horizon {100,500,2000} (full grid at 2000; 100/500 on a reduced set), budget fraction {.01,.05,.10,.20}, delay {0,1,5,20}, onset {early .2T, middle .5T, late .8T}, regime {abrupt, gradual, transient, recurrent}: structured subset documented in the results.
**Acceptance:** a pacing rule improves on tuned uniform if harm power gain >= +0.03 averaged over onset x regime at some budget, with 100% pathwise compliance.

## What would count as failure
Any arm with null false alarm > 0.07 in a null/no-harm world is reported as failing validity regardless of power. Negative results stay in the registry and the docs.
