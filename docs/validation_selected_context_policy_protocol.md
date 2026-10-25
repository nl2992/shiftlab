# Validation-selected contextual challenger: fresh development protocol

**Status:** frozen development protocol, 2026-10-24. This is a new exploratory
comparison on a seed block disjoint from the earlier context-alpha grid. It is
not calibration or confirmation.

## Question

Can a single validation-selected contextual challenger retain the utility of
context-specific candidate choice while avoiding the loss of power from
dividing monitor alpha across candidate-by-context tests? Compare it with
pooled candidate-rank, nested equal-context, and nested validation-volume alpha
on identical fitted candidate families, streams, labels, and hard caps.

## Pre-monitor policy selection

For candidate `k` and observable context `g`, calculate the fully labelled
validation average paired gain and subtract the registered exposure charge
`c_switch/H`. Select the validation-best candidate in each context only when
that context's best net validation gain is positive; otherwise use the
incumbent in that context. Freeze the resulting composite policy before the
monitor begins. It is one deterministic policy mapping the visible context to
one frozen candidate or to the incumbent fallback.

Validation outcomes may select this policy because the monitor is a separate
forward slice. Conditional on the complete validation history, the composite
policy is fixed before monitor feedback. Monitor feedback may authorize or
reject that one policy, but it cannot change its component candidates.

## Single-policy sequential test and validity

On each monitor event, form the direct-IPW estimate of the selected composite
policy's paired decision-cost gain. For an active context, use
`I_t * Delta_t / q_t - c_switch/H`; for an incumbent-fallback context, use zero.
Here `q_t` is the registered predictable query propensity and `Delta_t` is the
incumbent cost minus the selected candidate cost. Use the existing fixed-stake
mixture e-process at the full alpha level. The support bound is
`M/q_min + c_switch/H`, with `M=max(FN,FP)`. Preserve the common realized label
cap and stop before accessing the next event when the remaining cap cannot
fund a query.

The tested null is the **overall history-conditional mean net gain of this one
fixed composite policy**, integrating over the incoming event context:
`E[G_t | F_{t-1}] <= 0`. The method does not certify nonpositive gain in each
context separately. Its validity follows from the existing fixed-stake
bounded-mean e-process when, conditional on validation history, the selected
policy is fixed, the IPW query is conditionally randomized with known positive
propensity, the stated increment bound holds, and the null holds at every
monitor step. If decisions must be protected context-by-context, use the
nested context tests instead. This is sample-split policy selection plus an
established e-process, not a novelty claim.

Deployment utility includes the same exposure-prorated switching charge used
in the nested controller. If a candidate is selected for context `g`, charge
`c_switch/H` on events in `g`; incumbent fallback incurs no charge. The
evaluator alone uses latent context and true target probabilities.

## Frozen DGP and grid

Use the exact controlled DGP and factors from
[`contextual_budgeted_promotion_grid_protocol.md`](contextual_budgeted_promotion_grid_protocol.md):
stationary source training/validation, latent context defined by `X[0]`, an
independently misclassified learner-visible proxy feature, and a target-only
Bernoulli shift from the validation boundary at `1/6 ± delta` by latent group.
The zero-signal condition is the nondegenerate decision-threshold null.

- `n=3,200`, `d=16`, 30 matched seeds per cell, fresh seed root `20261026`.
- Context prevalence: 0.10, 0.50, 0.90.
- Signal displacement: 0, 0.05, 0.10.
- Proxy error: 0, 0.10, 0.25.
- Uniform acquisition, direct IPW, fixed-mixture monitor, alpha 0.05.
- Shared 20% and 40% realized label caps.
- Methods: pooled rank, nested equal, nested volume, and the single
  validation-selected composite policy.

The primary endpoint is evaluator-known cumulative future net decision-cost
gain at the 40% cap. The primary contrasts are composite-policy minus pooled
rank and composite-policy minus nested volume, equally averaged over the 18
positive-signal prevalence/error cells. Use paired seed-block bootstrap
intervals at 97.5% for each primary contrast. The existing +1 utility margin
must be exceeded by both lower limits before designing a fresh calibration and
confirmation. All cellwise effects, promotion rates, null crossings, labels,
and processed horizons are secondary development diagnostics. Do not pool this
seed block with the earlier grid, any null calibration, or any confirmation.

No figure is planned; any figure added later must use PaperBanana.

Reproduce with:

```powershell
uv run shiftlab-dive-budgeted-context-grid policy-develop `
  --seeds 30 --seed-offset 20261026 --n 3200 --d 16 --device cuda `
  --output outputs/validation_selected_context_policy_30
```
