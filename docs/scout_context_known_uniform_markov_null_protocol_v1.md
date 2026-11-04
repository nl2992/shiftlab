# Exact-uniform contextual scout: Markov null calibration v1

**Frozen:** 2026-11-04 before execution. **Status:** calibration of the specified synthetic
conditional-mean null only. This calibration is required before a disjoint positive-signal
confirmation of the known-uniform-propensity scout.

## Registered null and family

- 1,000 independent seed streams per cell, seed block `21,600,000–21,600,999`. A scan of current
  output manifests found no overlapping range; the block is disjoint from the preceding
  development block `21,510,000–21,510,059`.
- 36 simultaneous cells: stationary context prevalence `{0.10, 0.50, 0.90}` × Markov persistence
  `{0.0, 0.50, 0.80}` × proxy error `{0, 0.25}` × hard label cap `{0.20, 0.40}`.
- Every cell uses zero context signal, so the target outcome probability is exactly the
  FN/FP decision threshold in each context and at every event. The outcome null is checked against
  evaluator probabilities on every stream.
- Test the eventwise contextual scout with direct IPW, fixed-mixture betting, alpha 0.05, FN cost 5,
  FP cost 1, switching charge 0.05, `n=3,200`, and `d=16`.
- Uniform query probability is exactly the label-budget rate. Use the exact support floor
  `q_min = q_t = budget_rate`; query propensity and floor must agree in all rows.
- Require 1,000 rows per cell, zero hard-cap violations, verified conditional-mean nulls, and a
  simultaneous familywise one-sided Clopper–Pearson 95% upper limit no greater than 0.05 in every
  cell, with per-cell alpha `0.05/36`.

## Decision

Calibration passes only if every registered cell meets the exact upper-bound gate. A pass supports
only this specified synthetic null, query policy, propensity floor, stopping rule, and context
family; it is not a general theorem and does not establish a benefit over prior methods. If any cell
fails, do not run a positive-signal confirmation under this rule. Report all cells and preserve the
failed result without tuning on this block.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-eventwise-calibration `
  --seeds 1000 --seed-offset 21600000 --n 3200 --d 16 --device cpu --workers 6 `
  --query-policies uniform --exact-uniform-propensity-floor `
  --protocol docs/scout_context_known_uniform_markov_null_protocol_v1.md `
  --output outputs/scout_context_known_uniform_markov_null_v1
```
