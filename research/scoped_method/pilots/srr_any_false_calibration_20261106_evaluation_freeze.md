# E-SR calibrated operating-point evaluation — frozen

**Frozen before evaluation outcomes:** branch `codex/scoped-method-research-results-2026-11-06`, calibration protocol commit `f7d66aea`, selected alpha `0.0005`. This is the pre-outcome evaluation freeze; keep outcome artifacts separate until commit/push.

## Contract

Candidate: existing `E_srrSR:gated_deployment` with global alpha `0.0005` (same detector, split, acquisition, and code as calibrated). References: `E_swcert` at alpha 0.05 and `CONTROL_never_switch`. Horizon 2,000; label budget 200; delay as registered in each regime; label price 0.05; switching cost 5. All methods receive the same generated prediction/loss stream and policy-visible information. Regime truth remains evaluator-only.

## Fresh evaluation and gates

Evaluation seed base: `7110601102`, disjoint from all development/calibration seed bases checked in the repository and from the calibration seed base.

- `F0_null`: 1,000 paired streams. The candidate passes the any-promotion gate only if the one-sided 95% Wilson upper bound is ≤0.05.
- `F3_reversal_1200`: 200 paired streams. Primary economic gate: candidate saves at least 5 net-cost units on average, with the paired two-sided 95% t interval wholly below zero, against both E_swcert and never-switch.
- `F3_reversal_800`: 200 paired streams. Adverse-regime gate: candidate's mean net-cost harm against never-switch is ≤5 units.

All gates are conjunctive. Failure of any gate ends this detector track. If all pass, the evidence supports a calibrated operating adjustment to a known SR detector, not algorithmic novelty by itself. No tuning or alternative threshold is permitted after opening evaluation outcomes.

## Commands

Run the candidate at alpha `0.0005` and references at alpha `0.05` separately on identical regime seed bases. `screen.py` derives loss streams and policy RNG from the shared `(seed_base, regime, seed)` keys, so same-seed rows can be paired across these invocations.

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F0_null --policies E_srrSR:gated_deployment --seeds 1000 --seed-base 7110601102 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_any_false_calibration_20261106/evaluation_candidate_null
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F0_null --policies E_swcert,CONTROL_never_switch --seeds 1000 --seed-base 7110601102 --workers 4 --alpha 0.05 --out research/scoped_method/pilots/srr_any_false_calibration_20261106/evaluation_reference_null
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F3_reversal_1200,F3_reversal_800 --policies E_srrSR:gated_deployment --seeds 200 --seed-base 7110601102 --workers 4 --alpha 0.0005 --out research/scoped_method/pilots/srr_any_false_calibration_20261106/evaluation_candidate_reversals
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py --kind synthetic --regimes F3_reversal_1200,F3_reversal_800 --policies E_swcert,CONTROL_never_switch --seeds 200 --seed-base 7110601102 --workers 4 --alpha 0.05 --out research/scoped_method/pilots/srr_any_false_calibration_20261106/evaluation_reference_reversals
```
