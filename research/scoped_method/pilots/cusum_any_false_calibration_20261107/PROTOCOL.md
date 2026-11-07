# E-CUSUM false-promotion calibration and bounded reversal evaluation

**Frozen before new outcomes:** 2026-11-07, branch `codex/scoped-method-research-results-2026-11-06`.
This evaluates an existing published e-CUSUM restart detector at an empirically calibrated
operating point. The detector and threshold calibration are not claimed as novel.

## Question

Does `E_srr:gated_deployment` (the repository's e-CUSUM variant, distinct from its e-SR variant)
retain useful cost performance in the economically worthwhile temporary-improvement regime after
selecting its threshold using a finite-horizon any-promotion null criterion? This closes a
baseline-fidelity gap in the Failure Atlas headroom matrix; it does not reopen rejected overlay,
Beta-start, or E_rb composition lanes.

## Contract and information

Use the Failure Atlas simulator, horizon 2,000, pathwise label budget 200, registered cell-specific
delay, label cost 0.05, switch cost 5, and alpha input as implemented in `scripts/sota_sprint/fam_e.py`.
The policy sees only model predictions, queried disagreement outcomes when released, and its own
state. Evaluator regime truth remains unavailable. A false promotion is any episode in `F0_null`
with one or more challenger promotions. Calibration is empirical for this specific iid null and
contract; it is not a replacement for the method's published ARL statement or a theorem of
probability-of-any-false-promotion control.

## Stage 1: fixed null calibration

Evaluate only `E_srr:gated_deployment` on `F0_null`, 1,000 streams per alpha, seed base
`7110701101`, using the frozen grid `0.05, 0.02, 0.01, 0.005, 0.002, 0.001, 0.0005`. The same
generated streams are used across grid values. Calculate a one-sided 99% Wilson upper bound for
each false-promotion proportion, Bonferroni adjusted across seven alpha values. Select the largest
alpha whose adjusted upper bound is at most 0.05. Do not tune any other parameter. If no grid value
qualifies, stop this CUSUM screen without opening alternative cells.

## Stage 2: independent evaluation freeze and cells

If Stage 1 selects an alpha, commit a dated evaluation freeze before running any evaluation seed.
Use seed base `7110701102`, disjoint from calibration. Run the selected CUSUM alpha alongside the
following fixed comparators on identical seeds and streams: `E_swcert` at alpha 0.05,
`E_rb:gated_adaptive_range` at alpha 0.05, `E_srrSR:gated_deployment` at its already calibrated
alpha 0.0005, and `CONTROL_never_switch`.

Cells and sample sizes:

* `F0_null`: 1,000 paired streams. Pass only if the one-sided 95% Wilson upper bound on any
  challenger promotion for CUSUM is at most 0.05.
* `F3_reversal_1200`: 200 paired streams (economically worthwhile temporary improvement). For a
  scoped operating-point advantage, the paired 95% t interval for CUSUM minus **each** of
  `E_swcert`, `E_rb:gated_adaptive_range`, and never-switch must be wholly below zero and each mean
  saving must be at least 5 net-cost units.
* `F3_reversal_800`: 200 paired streams (unfavorable shorter improvement). Mean excess cost against
  never-switch must be at most 5 units; report all other contrasts and adverse outcomes.

For every method/cell report predictive loss, label count and expenditure, switching count and
expenditure, net cost identity, promotion and rollback counts/timing, and the paired cost differences
with 95% intervals. Keep the null calibration and independent evaluation disjoint. No real-data
source will be opened from this screen. If any conjunctive gate fails, end this CUSUM operating-point
track and retain the negative result. If all pass, the result supports only a scoped empirical
deployment recommendation for a known detector; any real-data transfer requires a separate frozen
source and chronology protocol and cannot be represented as algorithmic novelty.

## Exact Stage 1 command

One output directory per alpha; no evaluation outcomes are requested by this command:

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srr:gated_deployment \
  --seeds 1000 --seed-base 7110701101 --workers 4 --alpha ALPHA \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/null_ALPHA
```

`ALPHA` is replaced with each fixed grid value. Preserve every manifest and raw record file. No
candidate threshold may be added after seeing this grid. The existing E-CUSUM implementation is
the registered comparator under evaluation; if results suggest a different detector, that is a new
question and is outside this protocol.
