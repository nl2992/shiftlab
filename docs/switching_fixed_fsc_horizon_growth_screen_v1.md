# Fixed compact switching controller: horizon-growth screen

**Date:** 2026-10-29. **Status:** targeted finite-family screen; fixed-graph candidate rejected as
a scalable rule. No novelty or efficacy claim.

## Contract

This screen holds the model and costs fixed and grows the horizon. There are two actions, one
paired binary label per query, fixed delay `d=1`, pathwise cap `B=3`, query cost `1/100`, switch
cost `1/10`, and robust causal-null promotion risk `alpha=1/10`. The alternative is the registered
two-state recurrent HMM with symmetric transition `1/4`, emissions `1/20` and `19/20`, and prior
`1/2`. The null sees all generated labels and has conditional success probability in `[0,1/2]`.

## Fixed finite-state rule

Use one persistent root lottery: activate a deterministic FSM with probability `2/5`, otherwise
stay on the incumbent. In the active component, query at event 1; query at event 2 only if the
first released label is positive; promote at event 3 after two positive labels; query maintenance
at event 4 while deployed; roll back at event 5 if the maintenance label is zero; then hold. The
controller stops spending after those three possible requests.

The active FSM has exact full-history causal-null risk `1/4`, verified with the compact recursion in
[`switching_fsc_risk.py`](../src/shiftlab/dive/switching_fsc_risk.py). The persistent mixture has
risk `1/10`; its cost and risk were also recomputed by the full-history game evaluator. A fresh
behavioral lottery at every event is not used.

## Results

| Horizon | Fixed FSM cost | Risk | Decomposed solver cost | Cost difference |
|---:|---:|---:|---:|---:|
| 6 | `461083/160000` | `1/10` | `461083/160000` | `0` |
| 7 | `1349103/400000` | `1/10` | `10788127/3200000` | `4697/3200000` |
| 8 | `6189203/1600000` | `1/10` | `24735833/6400000` | `20979/6400000` |
| 9 | `13971197/3200000` | `1/10` | `55820069/12800000` | `64719/12800000` |

The component's exact risk remains unchanged across all four horizons, but its economic cost gap
increases after `T=6`. The `T=6` unrestricted sequence-form optimum has an independent rational
certificate. The `T=7,8,9` comparator is the recovered policy of the exact first-promotion
decomposition solved numerically; those rows do not certify global optimum. Costs are exact
rational evaluations of the recovered policies, not Monte Carlo estimates.

Reproduce with `uv run python scripts/screen_switching_fixed_fsc_horizon_growth.py`. The output
including code hash is written to the ignored path
`outputs/switching_fixed_fsc_horizon_growth_v1/results.json`.

## Decision

Close the specific “distill the six-event controller and hold its graph fixed” candidate. It has a
valid compact risk state but no horizon-uniform economic-value guarantee in this recurrent family.
The small observed gaps are not a method advantage: the controller was distilled from `T=6`, and
the longer-horizon oracle values are numerical. A viable continuation would need a horizon-aware
state/action rule and a theorem comparing its utility and risk with both the full-history oracle and
resource-matched sequential-design baselines. Generic belief updates, finite-state control and
robust risk verification remain established ingredients. G1 stays open; G2–G5 remain held.

The null certificate controls the first-promotion event only. It does not certify current challenger
value after an unobserved reversal; the FSM's rollback decision uses separate post-promotion labels.
