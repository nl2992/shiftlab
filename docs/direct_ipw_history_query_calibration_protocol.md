# Direct-IPW history-evidence query null calibration

**Status:** frozen protocol, 2026-10-25. The candidate was selected for this independent
calibration after the exploratory development grid; this calibration does not repair that
development selection for a confirmatory power claim.

## Question and frozen procedures

Estimate the stream-level false-escalation probability of the post-development query rule
`evidence_curve_a0_p0.5` at `q_min=0.05` under the registered `stationary` and
`benign_nuisance` population-null controls. Compare it with `uniform_proxy` using the same
direct-IPW e-process, synthetic stream, random query uniforms, and pathwise dollar cap.
The evidence-directed propensity for event t is selected from prior monitor wealth and
past realized spend; it cannot use current outcomes or evaluator-only oracle fields.

This rule applies an existing history-predictable acquisition policy to a direct-IPW
bounded-mean e-process. It is not presented as a new e-process theorem or as novel allocation
algorithm.

## Frozen design

- 2,000 independent seeds per scenario, IDs `32102026` through `32104025`.
- `n=3,200`, `d=16`, alpha 0.05, decision-harm margin 0.10.
- Query floor 0.05, ceiling 0.80, 20% hard label-dollar budget rate, and a shared global
  direct-IPW support bound within each scenario.
- Scenarios: `stationary` and `benign_nuisance`; both are registered population-null controls.
- Procedures: uniform querying and the single frozen evidence-curve candidate.
- Immediate randomized label feedback, paired deployed/reference binary decision costs, and
  four simultaneous method-by-null cells.
- Request CUDA synthetic generation with four worker processes; record the resolved device.
- No interim looks, tuning, method replacement, or seed replacement based on outcomes.

## Error-rate gate

The primary endpoint is the probability that the fixed-mixture direct-IPW e-process escalates
on a full null stream. For each method/scenario cell, report the count, rate, and exact
one-sided Clopper–Pearson upper confidence limit. Use Bonferroni per-cell alpha `0.05/4` so
the four upper limits cover simultaneously with at least 95% confidence. Each cell passes
only if all 2,000 registered seeds completed and its upper limit is at most 0.05. The family
passes only if all four cells pass and every stream respects the cap, support floor, null
classification, and unique seed key. With zero escalations in 2,000 streams, the simultaneous
upper limit is about 0.219%.

This gate calibrates the registered synthetic procedures and two controls. Formal validity
still relies on the conditional-mean null, frozen evaluated policies, correct bounded costs,
predictable propensities, and immediate unbiased feedback. It does not cover delayed or
selectively observed labels, additional serial dependence, or model misspecification. If the
family passes, any harm-power comparison must use a separately frozen design and disjoint
seeds; failure or inconclusive cells must be reported without tuning on this block.

## Reproduction

```powershell
uv run shiftlab-dive-direct-ipw-query-calibration `
  --output outputs/direct_ipw_query_calibration_2000 `
  --seeds 2000 `
  --seed-offset 32102026 `
  --n 3200 `
  --d 16 `
  --device cuda `
  --workers 4
```

The command refuses to overwrite nonempty output. It writes the full stream metrics,
per-cell exact limits, a report, environment details, and checksums. Runs with fewer than
2,000 streams per cell are marked smoke/incomplete and cannot pass the calibration gate.
