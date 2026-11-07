# Fixed-alpha E-SR reversal screen — protocol freeze

**Status:** prospective existing-method falsification; not a new-method test or confirmation.

## Question

Does the existing `E_srrSR:gated_deployment` policy at its previously selected alpha 0.0005 produce an economically meaningful advantage in the Failure Atlas `F3_reversal_1200` regime while satisfying a fresh independent iid-null calibration? This checks whether the identified gap is already closed by published restart-detection prior art.

## Hypothesis and immutable candidate

Candidate: unmodified `E_srrSR:gated_deployment`; global alpha `0.0005`; default 50/50 promotion/rollback alpha split; default acquisition and restart rules. No code or hyperparameter search. The alpha was selected in the previous `srr_any_false_calibration_20261106` protocol; the new null seed base is a fresh verification sample, not another alpha-selection stage.

Null calibration: 1,000 fresh `F0_null` iid streams, horizon 2,000, budget 200, delay 100, label cost 0.05, switch cost 5, seed base `7110601401`. Count any promotion. Gate: one-sided 95% Wilson upper bound on the promotion probability must be <= 0.05. If it fails, stop this candidate and do not inspect evaluation outcomes.

## Conditional evaluation (open only after calibration passes)

Run 30 paired streams/cell with seed base `7110601402` on `F3_reversal_1200` (primary), `F3_reversal_800` (unfavorable reversal), `F0_better` (persistent alternative), and `F0_null` (descriptive null cost). Use the common 2,000 horizon, pathwise label budget 200, label delay 100, label cost 0.05 and switch cost 5. Report loss, label expenditure, switch expenditure, time to first promotion/rollback, net cost, and null promotions. Compare identical streams against `CONTROL_never_switch`, `E_swcert`, `E_rb:gated_adaptive_range`, `rmm:gated_adaptive_range+RMM`, `PFA-SR:gated_adaptive_range`, and `economic_replacement`. Keep each method's null guarantee distinct; the cost-aware reference and E-SR do not receive an anytime false-promotion theorem from this experiment.

Primary development gate: on `F3_reversal_1200`, candidate must save at least 5 net-cost units against both never-switch and the strongest applicable risk-qualified comparator selected by the frozen prior matrix (`CONTROL_never_switch`), with both paired two-sided 95% intervals entirely below zero. On the `F3_reversal_800` adverse cell, candidate mean cost may not exceed never-switch by more than 5 units. The `F0_better` and `F0_null` cells are fully reported, not used to retune. Thirty seeds are development evidence only. A pass means an existing-method result, not novelty; a failure ends this E-SR lane and triggers no parameter retuning.

## Reproduction commands

Calibration:

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:gated_deployment \
  --seeds 1000 --seed-base 7110601401 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_reversal_20261106/calibration
```

Evaluation, only after recorded calibration pass:

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes F3_reversal_1200,F3_reversal_800,F0_better,F0_null \
  --policies CONTROL_never_switch,E_swcert,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,PFA-SR:gated_adaptive_range,economic_replacement,E_srrSR:gated_deployment \
  --seeds 30 --seed-base 7110601402 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_reversal_20261106/evaluation
```

The screen runner passes alpha to all candidate policies. The names other than E-SR are registry-bound and their factory-level alpha settings follow their registered implementations. Source hashes, command, and raw records must be frozen in the manifest. Do not edit or replace existing pilot artifacts.
