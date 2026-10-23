# Matched-bound hard-budget replication protocol

**Protocol lock:** 2026-10-23, before evaluating the fresh seed block below. The earlier 30-seed
results are pilot evidence and were used to identify the e-process bound as a comparison confound.
This run is a fresh replication, not a claim of a fully powered confirmatory study.

## Question and hypotheses

Under a common realized label-dollar cap and the same valid fixed e-process increment bound, do
variance, decision-value, cost-variance, or cost-stabilized query allocations change (a) detection of
boundary-local decision harm, (b) false escalation under stationary or benign nuisance streams, or
(c) estimation accuracy, relative to uniform querying?

The primary estimand is the paired-seed difference in the probability of detecting material
boundary-local harm by the pathwise budget stopping time, among all generated boundary-harm streams.
The registered practical null is that adaptive allocation does not improve this detection
probability over uniform by at least 0.10. This is a decision threshold for the study, not an
anytime-valid statistical null. False escalation on stationary streams is a safety outcome; benign
nuisance streams test whether distribution change alone leads to escalation. Secondary outcomes are
stream-mean excess-cost RMSE, cumulative labels and realized spend, fraction of monitor events
processed, and detection delay conditional on detection. Nondetections remain in the denominator.

## Fixed design

- Synthetic scenarios: `boundary_local_harm` (primary), `stationary`, and `benign_nuisance`.
- Methods: uniform, residual-variance, decision-value, cost-variance Neyman, and cost-stabilized
  cost-variance allocation.
- 60 fresh stream seeds beginning at seed offset `20362022`; 3,200 events, 16 features.
- Target query rate: `0.20`; common propensity floor: `0.10`; maximum propensity: `0.80`. The
  increased budget target is necessary for the cost-neutral branch to be feasible on the declared
  tariff support: with observed mean validation tariff near 1.5 and tariff support `[0.5, 2.5]`,
  `b/k` is approximately `[0.12, 0.60]` and remains inside the common propensity bounds.
- E-process significance level: `alpha=0.05`; use the same fixed bound based on `q_min=0.10` for
  every method. No threshold tuning on this seed block.
- Common hard dollar cap: target rate times mean validation tariff times monitor length; stop before
  opening an event when remaining balance cannot cover the known maximum tariff.
- Common random numbers for sampling and paired stream seeds. Synthetic evaluator truth remains
  available only to outcome scoring and harm-reach diagnostics.
- Execute synthetic generation on CUDA when available; record resolved device and runtime metadata.

## Analysis rules

Report counts and exact binomial confidence intervals for boundary-harm detection and false
escalations. Show paired-seed bootstrap intervals for RMSE differences and paired differences in
label use and spend. Include all 60 streams per scenario, including budget-censored harm onsets;
also separately report how many onsets were reached before stopping. Do not rank methods from this
single block or claim a general allocation optimum. If few or no detections occur across methods,
report that the run is underinformative about comparative power and design the next study from
simulation-based power analysis without reusing these evaluation seeds.

Reproduction command:

```powershell
uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20362022 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy --output outputs/hard_budget_matched_qmin_010_replication_60
```
