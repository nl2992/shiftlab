# Policy-specific-bound null calibration for query allocations

**Protocol lock:** 2026-10-24. This calibration is separate from all prior seed blocks and is not a method-selection or harm-power confirmation.

## Question and procedures

Estimate whether the fixed-mixture decision-harm monitor escalates on the two registered population-null controls when paired with each of the five query policies in the hard-budget allocation study. The monitor must use the policy's guaranteed minimum propensity in its PPI support bound: uniform querying has `q=budget_rate=0.20`, while the adaptive policies guarantee `q_min=0.10`. The shared-bound option is disabled. Predictable variance is a secondary comparator; predictable plug-in empirical Bernstein (PM-EB) is exploratory. All monitors for one policy process the same queried feedback.

The primary family consists of fixed-mixture false-escalation rates across five policies and two null scenarios (10 cells). For each cell, report a one-sided exact Clopper–Pearson upper limit with Bonferroni familywise 95% coverage across those 10 cells. The primary calibration criterion passes only if every such simultaneous upper limit is below 0.05. Report Wilson intervals and pointwise exact limits as well. PVA and PM-EB rates are secondary/exploratory and do not affect the primary criterion.

## Frozen design

- Scenarios: `stationary` and `benign_nuisance`, both registered population-null controls.
- Policies: `uniform_proxy`, `variance_proxy`, `decision_value_proxy`, `cost_variance_proxy`, and `cost_stabilized_proxy`.
- 500 independent stream seeds per scenario, seed block `54000000–54000499`; this block is disjoint from the previously recorded 52M, 53M, and 53.99M runs.
- `n=3200`, `d=16`, `alpha=0.05`, excess-cost margin `epsilon=0.10`, hard label-dollar budget rate `0.20`, `q_min=0.10`, `q_max=0.80`, maximum tariff `2.5`.
- `common_eprocess_bound=False`. Verify the saved per-method floor is 0.20 for uniform and 0.10 for every adaptive policy, and that realized propensities never fall below those floors.
- Run on CUDA with two concurrent seed workers; require the manifest to confirm NVIDIA CUDA execution. Worker concurrency is an execution detail only: each seed has independent, explicitly seeded synthetic and query RNGs, and final rows are sorted by scenario, seed, and method. Do not generate a plot: PaperBanana is the project visual tool, and no PaperBanana interface is available in this session.
- Use shared seed-level random variates across methods; keep all generated oracle information evaluator-only. Do not stop early, replace seeds, tune methods, or change thresholds after looking at results.

## Interpretation and limits

The independent stream seed is the calibration unit. Shared seeds across policies create a paired design, but each method-scenario rate is still reported separately. The experiment can reveal calibration failures in the registered simulator and policy family; it cannot establish the conditional-mean assumptions on real data or under delayed, dependent, selectively sampled, or post-selected feedback. A failed or inconclusive cell is reported as such; do not tune this seed block. Any later harmful-stream comparison must use a disjoint seed block and the same policy-specific bound rule.

## Reproduction

```powershell
uv run python scripts/run_policy_bound_null_calibration.py
uv run python scripts/analyze_policy_bound_null_calibration.py
uv run pytest tests/test_policy_bound_null_calibration.py -q
```
