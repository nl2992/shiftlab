# Risk-separated rollback falsification pilot — protocol freeze

**Status:** one bounded development pilot of an existing E-SR restart detector configuration. No new theorem, novelty claim, or confirmation claim is made.

## Hypothesis

In `F3_reversal_1200`, the calibrated E-SR detector promotes early enough to exploit part of the persistent initial advantage but its strict post-promotion alarm level leaves costly stale deployment after reversal. Keep the global promotion alpha and all acquisition/model rules fixed at the previously selected E-SR setup; set only the post-promotion rollback alarm level to 0.05. A false rollback is a deployment cost, not a false promotion. Because rollback can create another promotion opportunity, the candidate must pass a new whole-stream any-promotion null calibration.

This is an existing-method parameter separation: the repository's E_rb/RMM implementations already use distinct rollback levels. The test can show only whether this configuration helps in the stated operating region; it cannot support algorithmic novelty unless a further matched ablation establishes a distinct mechanism and prior art is re-reviewed.

## Candidate and calibration gate

Candidate `E_srrSR:rb05:gated_deployment` is unmodified `E_srrSR:gated_deployment` with `alpha_rb=0.05`; global `alpha=0.0005` and default alpha split, start grid, bet mixture, horizon-weighted acquisition, label clock, and switch mechanics remain fixed. Code adds this named registry configuration; test asserts that the promotion detector retains alpha 0.00025 while rollback uses alpha 0.05.

First run 1,000 fresh iid `F0_null` streams, horizon 2,000, budget 200, delay 100, label price 0.05, switch cost 5; seed base `7110601405`. Count any promotion, including repeat promotions. Pass only if the one-sided 95% Wilson upper bound is <=0.05. If calibration fails, stop without opening any alternative outcomes.

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic --regimes F0_null --policies E_srrSR:rb05:gated_deployment \
  --seeds 1000 --seed-base 7110601405 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_risk_separated_rollback_20261106/calibration
```

## Conditional development evaluation

Only after calibration passes, evaluate 50 fresh paired streams/cell at seed base `7110601406` on `F3_reversal_1200` (primary), `F3_reversal_800` (unfavorable reversal boundary), `F0_better` (persistent alternative), and `F0_null` (descriptive cost/error). Contract: horizon 2,000, delay 100, pathwise label budget 200, label price 0.05, switch cost 5. Global alpha 0.0005 for all alpha-aware methods.

Frozen panel: candidate; `E_srrSR:gated_deployment` (single ablation: rollback alpha stays at 0.0005); `E_rb:gated_adaptive_range`; `rmm:gated_adaptive_range+RMM`; `E_swcert`; `B5`; `CONTROL_never_switch`; and `R:economic_stop`. Report mean predictive loss, label/switch costs, net cost, promotion/rollback counts and times, and paired 95% t intervals on common streams. Preserve each method's own guarantee; empirical candidate null calibration is limited to the registered iid null generator.

Development signal requires at least 5 net-cost units of savings on `F3_reversal_1200` with the full paired interval below zero versus both never-switch and the strongest applicable feasible comparator from the frozen panel. On `F3_reversal_800`, mean excess cost over never-switch may not exceed 5. `F0_better` and `F0_null` are fully reported; they do not trigger retuning. A pass is only a candidate for separately frozen independent validation. A failure ends this mechanism search. No thresholds, seeds, alpha levels, or operating cells may be changed after opening outcomes.

```sh
PYTHONPATH=scripts/promising_directions/sota uv run python scripts/sota_sprint/screen.py \
  --kind synthetic \
  --regimes F3_reversal_1200,F3_reversal_800,F0_better,F0_null \
  --policies E_srrSR:rb05:gated_deployment,E_srrSR:gated_deployment,E_rb:gated_adaptive_range,rmm:gated_adaptive_range+RMM,E_swcert,B5,CONTROL_never_switch,R:economic_stop \
  --seeds 50 --seed-base 7110601406 --workers 4 --alpha 0.0005 \
  --out research/scoped_method/pilots/srr_risk_separated_rollback_20261106/evaluation
```
