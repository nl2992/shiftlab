# Lagrangian cost-risk frontier recovery screen

**Date:** 2026-10-29. **Status:** generic baseline validated on one certified cell; no novelty
claim or efficacy result.

## Generic recovery statement

For a compact convex learner realization-plan set `X`, let `C(x)` be alternative expected cost,
`R(x)=sup_nu R(x,nu)` be worst full-history causal-null promotion probability, and

`g(lambda)=min_x [C(x)+lambda(R(x)-alpha)]`.

Assume strong duality and let `lambda*` maximize `g`, so `V*=g(lambda*)`. Suppose two policies
`x_-`,`x_+` have separately verified risks `R_-=R(x_-) >= alpha >= R_+=R(x_+)` and are each
`epsilon`-optimal for scalar multipliers `lambda_-`,`lambda_+` within `delta` of `lambda*`.
Because `|R(x)-alpha|<=1` and `g(lambda_i)<=g(lambda*)`, each policy satisfies

`C(x_i)+lambda*(R_i-alpha) <= V*+epsilon+delta`.

Mix the two policies using a persistent root coin so the mixture of their component risks equals
`alpha`. Cost is linear in this mixture, and robust risk is convex in the realization plan, so the
mixed policy has causal-null risk at most `alpha` and cost at most `V*+epsilon+delta`. This is a
standard Lagrangian frontier-recovery lemma; it is not a new result for model switching. A single
policy from one scalar multiplier does not imply feasibility. The mixture must be one committed
root lottery: averaging action probabilities afresh at every information set changes the policy
class and need not preserve either risk or cost.

## Registered exact-contract screen

The development script `scripts/screen_switching_lagrange_frontier_recovery.py` solves scalarized
sequence-form LPs for the certified `T=6,B=3,d=1` recurrent-HMM cell, bisects until exactly
forward-verified policy risks bracket `alpha`, forms the persistent root mixture, and independently
recomputes its alternative cost and causal-null risk.

| Quantity | High-risk component | Low-risk component | Persistent mixture |
|---|---:|---:|---:|
| Multiplier | `1.18231201171875` | `1.182342529296875` | — |
| Cost | `173083/64000` | `3` | `461083/160000` |
| Robust causal-null risk | `1/4` | `0` | `1/10` |
| Weight | — | — | `2/5`, `3/5` |

The multiplier separation is `1/32768`. The resulting mixture exactly matches the certified full-
oracle feasible upper policy's cost and risk on this instance. Its cost gap to that upper policy is
zero. The scalar LPs and multiplier bracket are numerical; this is not a certified global
approximation bound. The purpose is to confirm that a generic scalarize/verify/mix comparator can
recover a useful policy under the project information structure.

Reproduce from the repo root with:

```powershell
uv run python scripts/screen_switching_lagrange_frontier_recovery.py
```

The result is written to the ignored output path
`outputs/switching_lagrange_frontier_recovery_v1/results.json`, including the script hash.

## Research consequence

Retain finite-horizon SAB/one-sided-POSG scalarization plus independent full-null risk verification
and risk-bracketing mixture as a mandatory baseline for any future approximate constrained solver.
The screen does not supply a genuinely new acquisition rule, a growing-family complexity bound,
or performance evidence against scalable established methods. G1 remains open; G2–G5 remain held.

Promotion-risk validity continues to refer to the declared test-epoch null. It does not certify
current challenger value after an unobserved regime reversal; model-based current-value forecasts
and post-reversal loss remain separate quantities.
