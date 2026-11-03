# Validity and estimand audit — partial, 2026-11-01

Status: INTERNAL_ONLY; W04/G04 not complete. No independent theorem review occurred.

## Q2 context-selected hurdle versus one-time switching utility

At base e74fdc3, `src/shiftlab/dive/budgeted_promotion.py:1152` forms the certification increment `I_selected * (Q*g/q - s/H)`, with H the declared deployment length and s the configured switching cost. The sequential branch implements the same quantity at line 1198 (locate with `rg -n 'increment = estimate'`). This tests the selected-context average benefit against the selected-event hurdle under the requisite conditional query/null assumptions. It is not automatically a test of full one-time switching utility.

Exact counterexample: H=10, selected-event probability 1/10, selected-event expected gain g=.02, fee s=.1. The tested conditional mean is .1*(.02-.01)=.001>0, while ten-event expected gross benefit is .02 and benefit after one full fee is -.08. The selected-event charge totals .01 rather than .1. A theorem about the first estimand cannot certify the second without additional cost accounting/coverage assumptions. The test passes by exact rational arithmetic; it does not assert an observed false-alarm rate or refute the scoped conditional-mean test.

The implementation also evaluates an exposure-proportional charge (`switch_rate * selected_count`) in its context-policy accounting. That is a different economic convention and must be named. Repairing a claim by narrowing it preserves the implementation; changing to a one-time fee requires a versioned estimand/protocol, not a silent numerical patch. The fixed-candidate integrated ablation subtracts the hurdle on every monitored event (`integrated_pipeline.py:309–316`), so this selected-context counterexample must not be applied indiscriminately to that ablation.

Current `papers/shiftguard_unified/claims_and_limitations.md:84` already disclaims guaranteed future utility from a positive shadow certificate and the next bullet disclaims automatic valid composition. Preserve those statements. No claim that the entire current repository still asserts full net-benefit certification is justified by this partial scan. Downstream source census and propagation remain required.

## Products of dependent e-processes

A shared fair coin produces two identical one-step e-values, each 2 on heads and 0 on tails. Each has expectation 1, their product has expectation 2. Consequently an unguarded product is not generally an e-value. A fixed convex mixture has expectation 1 in the same example. This mathematical counterexample does not establish that the current HGxH2c engine still uses the invalid product; source/repair verification remains pending.

Validation: `python -B -m pytest tests/retrospective_audit -q` — exit 0, 6 passed. Exact counterexamples are in `tests/retrospective_audit/test_validity_counterexamples.py`. They check unsupported stronger inference, not nominal-risk calibration or a complete filtration proof. No new experiment or seed exposure occurred.
