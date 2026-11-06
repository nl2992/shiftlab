# E-SR false-promotion calibration — frozen protocol

**Status:** prospective calibration of an existing conventional detector, not a new method and not a confirmation. Frozen before calibration outputs are generated. Branch: `codex/scoped-method-research-results-2026-11-06`.

## Question and target

Can the existing `E_srrSR:gated_deployment` implementation be assigned an operating threshold that controls **probability of any challenger promotion over the full 2,000-event horizon** under the registered iid conditional null, while retaining a practical net-cost advantage in the economically worthwhile reversal regime?

The calibration target is a one-sided 95% upper confidence bound of at most 0.05 for any false promotion. This is an empirical operating-point target for the specified simulator contract, not a theorem. SR's published ARL target remains distinct and will not be described as the same guarantee.

## Fixed contracts and cells

Reuse the registered simulator, shared model-loss streams, delayed label releases, 200-label cap, label price 0.05, switch price 5, and 2,000-event horizon from the economic headroom matrix. The primary profitable alternative is `F3_reversal_1200`; `F3_reversal_800` is the economically unfavorable reversal. `F0_null` is the correctly specified iid conditional null. Policy information is limited to predictions, acquired labels when released, and policy state; evaluator regime truth is not exposed.

The registered comparators are never-switch and `E_swcert` at alpha 0.05. The candidate is the existing `E_srrSR:gated_deployment` port, whose alpha controls the base and SR detector through its existing split. Its other code, acquisition, restart, and alpha split are unchanged.

## Calibration, distinct from evaluation

- Candidate alpha grid, fixed in advance: `0.05, 0.02, 0.01, 0.005, 0.002, 0.001, 0.0005`.
- Calibration cell: `F0_null`; 1,000 fresh paired seeds at seed base `7110601101`, identical across grid values.
- For each alpha, compute the one-sided Wilson upper bound for the episode-level indicator of any challenger promotion. Use 99% one-sided bounds (Bonferroni across seven alpha candidates) for calibration selection.
- Select the **largest** grid alpha whose adjusted upper bound is at most 0.05. If no alpha qualifies, stop this detector track without evaluation on alternatives.
- Calibration data may select only alpha. Do not change policy code, pacing, detector bets, comparator, or criteria after seeing calibration outcomes.

## Independent operating-point evaluation

If calibration selects an alpha, commit that alpha and this evaluation freeze before running fresh seed base `7110601102`:

**Selected alpha: `0.0005`.** It is the largest grid point satisfying the preregistered
Bonferroni-adjusted 99% one-sided Wilson upper bound criterion (see `CALIBRATION_RESULTS.md`). The
evaluation protocol is frozen in `srr_any_false_calibration_20261106_evaluation_freeze.md` at
commit `PENDING_COMMIT` before any evaluation run.

- `F0_null`: 1,000 fresh paired seeds; pass only if the ordinary one-sided 95% Wilson upper bound for any promotion is at most 0.05.
- `F3_reversal_1200` and `F3_reversal_800`: 200 fresh paired seeds per cell. Compare candidate net cost against `E_swcert` (fixed alpha 0.05) and never-switch on identical streams. Primary economic success requires at least 5 net-cost units of mean saving with the two-sided paired 95% t interval entirely below zero against both references in `F3_reversal_1200`; mean harm to never-switch must be at most 5 in `F3_reversal_800`.
- Report loss, label count and cost, switches and cost, first promotion, rollback timing/count, all-false-promotion count and interval, and paired cost decomposition. Do not pool the three cells.
- If the null gate fails or the economic criterion fails, report the outcome and stop this calibration track. If all gates pass, the result supports an operating adjustment of an existing algorithm only; it is not evidence of algorithmic novelty. Any new-method claim still requires a separate prior-art audit and independently sourced real-data validation.

## Commands

Calibration uses `scripts/sota_sprint/screen.py` with `--kind synthetic --regimes F0_null --policies E_srrSR:gated_deployment --seeds 1000 --seed-base 7110601101`, one output directory per alpha, and `--alpha <grid-value>`. The exact invocations and output hashes will be recorded in the calibration results. Evaluation may use `screen.py` in separate candidate and comparator invocations with the same seed base; `screen.py` uses identical generated loss streams and policy RNG keys at a given regime/seed, allowing exact seed pairing while holding E_swcert at 0.05.
