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

## Prospective supplementary baseline completion (frozen before the run)

The repository audit after the first E-SR screen found an established cost-aware certificate adapter, `R:economic_stop` (`scripts/promising_directions/sota/competitors/economic_stop.py`, registered in `scripts/sota_sprint/fam_r.py`), that was absent from the original matrix. The first evaluation's outcomes are already open, so this supplemental panel is explicitly exploratory and cannot be called independent confirmation. It completes the baseline comparison before any candidate design.

Run 30 paired streams/cell on the same four cells and common cost contract, with fresh seed base `7110601403`, comparing the exact previous panel plus `R:economic_stop`. Pass `--alpha 0.0005` to all alpha-aware methods. The economic-stop adapter is a feasible, certificate-thresholded, cost-aware decision method; its finite-sample safety interpretation remains limited to its stated confidence-sequence assumptions. The screen runner records all policies on identical streams. Report the same cost decomposition and paired contrasts. No tuning, candidate selection, or claim of confirmation follows from this supplemental run. If `R:economic_stop` is competitive, preserve it as an existing-method explanation; if not, no new method is implied until a separate mechanism protocol and targeted prior-art audit are completed.

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes F3_reversal_1200,F3_reversal_800,F0_better,F0_null \
  --policies CONTROL_never_switch,E_swcert,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,PFA-SR:gated_adaptive_range,economic_replacement,R:economic_stop,E_srrSR:gated_deployment \
  --seeds 30 --seed-base 7110601403 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_reversal_20261106/costaware_baseline
```

## Existing reserve/rollback/deadline comparator completion

The original economic matrix omitted the already implemented `B5` composition (15% pre-decision label reserve + RMM rollback + economic deadline). Since this is an established repository baseline and is directly relevant to the interaction under study, run one additional fresh exploratory panel before any candidate implementation. This is not confirmation: the target regime was already examined in the preceding development screens, and B5's existence is prior knowledge.

Use seed base `7110601404`, 30 paired streams per cell, the same four cells and cost contract, and pass global alpha 0.0005. Compare `B5`, `B2`, `CONTROL_never_switch`, `E_swcert`, `E_rb:gated_adaptive_range`, `rmm:gated_adaptive_range+RMM`, `R:economic_stop`, and `E_srrSR:gated_deployment`. `B2` is the simplest rollback-without-reserve/deadline ablation. The target gate remains the same primary scenario: at least 5 mean net-cost units saved vs never-switch with the paired 95% interval below zero; the unfavorable `F3_reversal_800` harm must be <=5 units vs never-switch. Any pass is an existing-method result. Do not adjust B5's registered reserve fraction, deadline, monitor, or alpha after outcomes.

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F3_reversal_1200,F3_reversal_800,F0_better,F0_null \
  --policies B5,B2,CONTROL_never_switch,E_swcert,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,R:economic_stop,E_srrSR:gated_deployment \
  --seeds 30 --seed-base 7110601404 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_reversal_20261106/reserve_rollback_baseline
```
