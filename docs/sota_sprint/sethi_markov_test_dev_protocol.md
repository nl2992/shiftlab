# Composite Markov test comparator development screen

**Status:** exploratory implementation/comparator screen only. This adds an implementation of the
published binary specialization in Sethi et al., *Asymptotically Optimal Sequential Testing with
Markovian Data* (ICML 2026). It is not a novelty claim. The policy uses a label-independent fixed
gap of six events and no label reserve, matching `A5-fixedgap6-full` acquisition.

## Why this port applies

Sethi et al.'s test observes a homogeneous finite-state Markov chain. Under the sprint's stationary
binary refresh-or-hold null with marginal p<=.5 and persistence rho, a fixed label-independent query
schedule produces i.i.d. event gaps G independent of the sign chain. The sampled sign sequence is
again a homogeneous binary Markov chain with the same stationary p and effective persistence
`rho_bar = E[rho**G]` in [0,1]. Thus the published null set remains the same. This argument requires
constant Bernoulli disagreement probability independent of the sign, as in the registered regimes
below; it does not cover bursty or sign-dependent query opportunities.

The binary null transition rows are parameterized by `u=P(1|0)` and `v=P(0|1)`, with
`u<=v`, `u+v<=1`, and `u,v>=0`. For each update, the statistic is the empirical transition
row KL divergence minimized over this triangle, minus Sethi et al.'s state-visitation penalty.
The policy ignores the first observed state in each test and uses the published anytime boundary
inside the existing cycle-spending deployment skeleton.

## Screen

* Fresh paired seed base: `2026110904`, 20 seeds per regime.
* Regimes: `V_better_a`, `V_late_600`, `W_late_1000`, `V_dep_better_r5`,
  `W_better_dep_r7`, `V_null_dep_r8`, `W_null_dep_r95`.
* Policies: `Sethi-MC-fixedgap6`, `A5-fixedgap6-full` (matched acquisition), `A5b`, Xu,
  gated adaptive range + tuned pacing, and corrected DISCERN.
* Contract: T=2000, B=200, c_q=.05, c_s=5, alpha=.05.
* Outcomes: paired net deployment cost, promotion rate, label use, and runtime. Twenty-seed null
  rates are diagnostics, not safety evidence.

## Outcome

The port was much more conservative than its matched fixed-gap SUI control. Mean net cost was
higher by 14.20 [1.94,26.46] on `V_better_a`, 12.02 [4.79,19.26] on `V_late_600`, 6.95
[1.61,12.29] on `W_late_1000`, 37.99 [21.36,54.62] on `V_dep_better_r5`, and 35.19
[20.65,49.74] on `W_better_dep_r7`. It promoted in 0/20 on both late regimes; the matched SUI
control promoted in 10/20 and 10/20. Mean runtime was about .01 seconds per episode versus .24
for the matched SUI policy. All three methods had 0/20 promotions on the two null regimes, which
is only a diagnostic at this sample size.

**Conclusion:** the direct composite-Markov comparator is materially more conservative at this
budget and did not improve cost or power. Keep it as a comparator/prior-art record; stop this port
as a candidate. This small development screen does not establish validity or broad superiority.
Raw records and manifest are under ignored `outputs/sota_sprint/sethi_markov_dev/`.

## Interpretation

This is a development comparator, not a registered validation. Any promising result requires an
independent implementation audit, fresh regimes, the full comparator panel, and at least 1000
seeds per relevant null. If the method is poor in cost or safety under the matched acquisition, stop
the port rather than claim the new gap-indexed SUI is novel by exclusion.
