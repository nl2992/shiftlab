# Implementation record: `UPFStyleSwitchTimingT3` (Regol et al., ICML 2025 style)

Status: built 2026-11-06. **Tier T3 (common-contract adaptation). Not UPF, not Regol et al.'s algorithm,
no harm guarantee. Uncertified class.** Never label it "UPF" or "Regol et al." in result tables.
Decision record: `LEDGER.md` (Regol entry); mapping: `specs/regol_when_to_retrain.md` section 6; checks:
`checks/regol_when_to_retrain.md` (fairness concerns a-e are all addressed or declared below).
The T2 native port stays in `src/shiftlab/dive/upf_retraining.py` (unmodified, not called by the
adapter at runtime; tests cross-check the Beta conversion and the one-period rule against it).

## Files
- `scripts/promising_directions/sota/competitors/upf_style_switch_timing.py`
  (`UPFStyleSwitchTimingT3`, `plan_switch`, `beta_parameters`, factory `make_upf_style_switch_timing`
  with the `extra=` signature of `suite.build_suite`; not registered anywhere, shared files untouched).
- `tests/sota_fidelity/test_upf_style_switch_timing.py`.

## What is built (spec section 6, steps 1-5)
Periods of `m=100` rounds (20 for T=2000; **lock m before any run**, default is the pre-run value, not
tuned). Cell `A[k,j]` = period-mean of `1[disagree]*loss_k`, Horvitz-Thompson IPW over labels released by
the decision round, using the issue-time propensities; labels come from the shared
`PacedDisagreementAcquisition` (same rule as `EconomicReplacement`), not adapter-chosen. Forecaster:
ElasticNetCV on `[arm, period, z_shift]`; sigma^2 = residual MSE + mean HT variance of the training
cells; Beta by Eq. 51-52 with the T2 port's clipping. Backward recursion Eq. 17-20 with reversible
switching (switch cost `c_s/m + A[other,j]`, keep `A[a,j]`), shared Monte Carlo draws (default 2000),
strict `<` on delta=0.95 quantiles (Eq. 16). First action only, replanned at every period boundary from
whatever cells are complete and released. Warm-up: stay with the incumbent until 3 usable periods exist
(first possible switch at round 400 with delay 100).

## Deviations (all of them)
1. Reversible switching between two frozen models; `i` and `j-i` features collapse to arm and period, so
   the forecaster is a trend-plus-arm regressor, weaker than native UPF.
2. Free period length `m`; no offline w=7 table; warm-up instead.
3. Cells cover disagreement rounds only (agreement-round loss is common to both arms, never labelled by
   the shared pacer, and cancels); cells are clipped to [0,1] before fitting.
4. Cells are sparse, delayed IPW estimates; sigma adds the HT variance estimator (conservative: the
   residual already holds part of that noise, so it is double counted). Declared extra, not in the paper.
5. `z_shift` = L1 change of mean context between consecutive periods if contexts exist, else change in
   the public disagreement rate (the loss-only streams have no features). Future periods use the latest z.
6. Labels are exogenous and shared; label price is ignored by the planner.
7. numpy Beta sampling and `np.quantile` instead of torch; one independent draw set per planning call.
8. Decisions only at period boundaries; `T` must be a multiple of `m`.
9. Periods with any disagreement round of propensity 0 (budget exhausted) are excluded (IPW positivity),
   so after exhaustion the forecaster stops learning and extrapolates from older cells.
10. Nested delta-quantiles are not a coherent risk measure and give no type-I control (spec sec. 3).

## Tests
`uv run pytest tests/sota_fidelity/test_upf_style_switch_timing.py -q` -> 11 passed, 2 skipped in ~20 s
(the 2 skips need `torch`, which the uv environment here lacks: they compare `beta_parameters` with
`BetaPerformanceForecaster.predict_beta_parameters` and the one-period rule with `upf_retraining_schedule`;
run with `PYTHONPATH=src /opt/anaconda3/bin/python -m pytest ... -k t2_port` -> 2 passed).
`uv run ruff check` and `ruff format --check` clean on the new files.
Covered: hand-built two-period quantile case (including exact margin and a deferred switch), reversal back
to the incumbent, delta-quantile risk aversion (delta .5 switches, .95 stays), equal-cell plans stay on 10
seeds, no-disagreement stream never switches, strong challenger (p=.9) switches by 3/3 seeds and not before
round 300, IPW cell estimates unbiased in a 3000-replicate Monte Carlo (4 SE), and simulator smoke on
F0_null / F0_better / F3_reversal_800 (hard budget, delay check, determinism per seed, every cell used at
a planning step is over and has all its labels released by that step, switches only at boundaries).

## 5-seed SMOKE (not evidence)
Contract T=2000, B=200, c_q=.05, c_s=5, regime registry of `scripts/failure_atlas_v2_flq/regimes.py`,
stream seeds `2026110600+s`, policy seed base 2026110601, s=0..4. Net cost = loss + label price + switch
cost (simulator definition). "Never switch" is `FixedModel(0)` on the same stream.

| regime | mean net (T3) | mean net (never switch) | seeds that ever switch | first switch rounds |
|---|---|---|---|---|
| F0_null | 379.4 | 372.8 | 1/5 | 400 |
| F0_better | 351.8 | 431.2 | 5/5 | 400,400,400,400,500 |
| F3_reversal_800 | 426.8 | 362.2 | 5/5 | 400 x5; never reverts |

Reading: on the reversal regime (advantage until 800, then the challenger is worse) the rule switches at
400 and never returns, losing about 65 net to staying put; labels are mostly spent by then (deviation 9).
This is a smoke run, not a locked-protocol result, with 5 seeds.

Separate unplanned diagnostic (20 seeds, seeds `900+s`, policy base 7): ever-switch rate on a **null**
stream was 8/20 on F0_null and 8/20 on V_null. So "stays on null with high probability" does not hold
for the full adapter at the default delta=0.95: the IPW-noisy arm coefficient is extrapolated over up to
17 remaining periods against a one-off cost of only c_s/m per period. The tests therefore assert the
null property only at the rule level and on a stream with no disagreements. This is a descriptive result
about an uncertified baseline, consistent with spec section 5/6; it was not tuned away (m, delta,
`draws`, `min_periods` unchanged).

## Continue / pivot / stop
Continue as a labelled uncertified baseline in the comparator pool. Not a candidate for null-safe claims.
Open: whether to register `m`, `delta` and `min_periods` formally before confirmatory runs.
