# E-CUSUM independent operating-point evaluation freeze

**Frozen after Stage 1, before evaluation outcomes:** 2026-11-07, branch
`codex/scoped-method-research-results-2026-11-06`. This is a distinct synthetic seed block and a
pre-outcome comparator/analysis freeze.

## Selected operating point

Select `E_srr:gated_deployment` alpha `0.005`, the largest value in the protocol's fixed grid whose
Bonferroni-adjusted one-sided 99% Wilson upper bound is no greater than 0.05. Stage 1 used 1,000
`F0_null` streams at seed base `7110701101`; its exact counts, source hashes and rule calculation
will be recorded in `CALIBRATION_RESULTS.md`. This empirical calibration applies only to the
registered iid null and simulator contract. Do not describe it as an anytime guarantee.

## Evaluation registry

Use independent seed base `7110701102` with 1,000 streams in `F0_null` and 200 streams each in
`F3_reversal_1200` and `F3_reversal_800`. Contract and observable information match the frozen
calibration protocol. Evaluator regime labels remain unavailable to all policies.

Methods and fixed alpha values:

* Candidate under assessment: `E_srr:gated_deployment`, alpha `0.005`.
* References: `E_swcert`, `E_rb:gated_adaptive_range`, `CONTROL_never_switch`, all at alpha `0.05`;
  and calibrated `E_srrSR:gated_deployment` at alpha `0.0005`.

The primary cell is `F3_reversal_1200`. Candidate-minus-reference paired 95% t intervals must be
entirely below zero and the mean saving must be at least 5 net-cost units versus **each** of
`E_swcert`, `E_rb:gated_adaptive_range`, and never-switch. The adverse-cell criterion on
`F3_reversal_800` is mean candidate harm versus never-switch no greater than 5 units. On `F0_null`,
the candidate's ordinary one-sided 95% Wilson upper bound for any promotion must be at most 0.05.
These requirements are conjunctive. Report all five methods in every cell, all paired cost contrasts,
cost decomposition, labels, switches, promotions, rollbacks, and timing regardless of direction.

If any criterion fails, stop this CUSUM track; do not tune alpha or select a different detector from
these evaluation outcomes. If all criteria pass, only then consider a separately frozen independent
chronological real-data replay. Such a replay would validate transfer of a known calibrated e-CUSUM
operating point, not a novel algorithm. This evaluation itself does not open any real data.

## Commands

Run candidate and references separately so that each retains its frozen alpha; `screen.py` derives
the same generated streams from the shared seed-base/regime/seed keys for pairing. Use separate
invocations because the null and alternative cells have different registered sample sizes.

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srr:gated_deployment \
  --seeds 1000 --seed-base 7110701102 \
  --workers 4 --alpha 0.005 \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/eval_candidate_null

PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F3_reversal_1200,F3_reversal_800 \
  --policies E_srr:gated_deployment --seeds 200 --seed-base 7110701102 \
  --workers 4 --alpha 0.005 \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/eval_candidate_reversal

PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_swcert,E_rb:gated_adaptive_range,CONTROL_never_switch \
  --seeds 1000 --seed-base 7110701102 --workers 4 --alpha 0.05 \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/eval_references_null

PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F3_reversal_1200,F3_reversal_800 \
  --policies E_swcert,E_rb:gated_adaptive_range,CONTROL_never_switch \
  --seeds 200 --seed-base 7110701102 --workers 4 --alpha 0.05 \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/eval_references_reversal

PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:gated_deployment \
  --seeds 1000 --seed-base 7110701102 \
  --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/eval_esr_null

PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F3_reversal_1200,F3_reversal_800 \
  --policies E_srrSR:gated_deployment --seeds 200 --seed-base 7110701102 \
  --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/cusum_any_false_calibration_20261107/eval_esr_reversal
```
