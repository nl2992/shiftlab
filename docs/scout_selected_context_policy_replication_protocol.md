# Independent development replication of target-scout selection

**Status:** frozen 2026-10-24 before execution. This is a fresh synthetic
development replication, not null calibration or real-world confirmation.

## Question

The first frozen 30-seed target-scout screen produced positive paired utility
estimates, with the lower 97.5% limit for scout minus nested-volume slightly
below the predeclared +1 margin (0.893 versus 1.0). Repeat the exact design on
an independent seed block to assess whether the effect clears that same margin.
Do not pool seed-level records with prior screens.

## Frozen design

- Use the exact two-stage target-scout policy, candidate family, DGP,
  propensity, e-process, report endpoints, and hard label caps from
  [`scout_selected_context_policy_protocol.md`](scout_selected_context_policy_protocol.md).
- Fresh seed IDs `20261200`–`20261259`, 60 matched seeds per cell, disjoint from
  all earlier context-policy seed ranges.
- Keep all 27 prevalence × signal × proxy-error cells, `n=3,200`, `d=16`,
  CUDA generation, uniform direct-IPW queries, alpha 0.05, and the 20%/40%
  realized label caps.
- Primary endpoint remains evaluator-known cumulative future net gain at the
  40% cap. Primary comparisons remain scout minus pooled rank and scout minus
  nested volume, averaged equally over the 18 positive-signal cells, with
  matched seed-block bootstrap intervals at 97.5% per contrast.
- Proceed to independent null calibration only if both lower interval limits
  exceed +1 and all registered zero-signal cells have zero promotions. If not,
  stop this rule or formulate a new design in a separate protocol.

The study remains limited to the registered iid synthetic process, predictable
known query propensities, bounded paired costs, and fixed policy during
certification. The result does not establish robustness to delayed labels,
serial dependence, selective feedback, context drift, or real applications. No
figure is planned; use PaperBanana for any figure.

## Reproduction

```powershell
uv run shiftlab-dive-budgeted-context-grid scout-develop `
  --seeds 60 --seed-offset 20261200 --n 3200 --d 16 --device cuda `
  --protocol docs/scout_selected_context_policy_replication_protocol.md `
  --output outputs/scout_selected_context_policy_replication_60
```
