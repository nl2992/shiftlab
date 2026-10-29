# Registered screen: economic cost of monotone promotion restriction

**Registered:** 2026-10-29 before solver execution. **Question:** does requiring the terminal
promotion probability to be increasing on the full queried-label tape lose value, even when both
the unrestricted and monotone classes satisfy the same causal-null risk constraint?

## Frozen finite contract

- Horizon `T=4`; fixed delay `d=1`; hard label cap `B=3`.
- Query exactly at events 1, 2 and 3. Hold action 0 through event 3; at event 4 either remain at
  0 or promote to 1 for that event. Thus every learner has identical information timing, query
  count and post-promotion exposure.
- Paired losses are `(Y_t,1-Y_t)`. Query fee is `c=1/100`; promotion switch fee is `k=1/10`.
- Risk is `sup_P P(promotion)` over all event-time causal nulls with
  `P(Y_t=1 | full prior outcome history, public query/action choices)<=1/2`; require `alpha=1/20`.
  At `T=3` the exact null extreme points comprise `2^(1+2+4)=128` endpoint response trees.
- Alternative HMM: `prior1=0`, `transition01=1`, `transition10=9/10`,
  `emission0=1/100`, `emission1=99/100`. These satisfy strict interior emission assumptions and
  generate a recurrent near-alternating regime. The label `Y_4` remains hidden until after the
  promotion decision.
- Compare all randomized terminal decision maps `q(y_1,y_2,y_3) in [0,1]` against the subclass
  whose map is coordinatewise nondecreasing. Optimize expected alternative net-cost savings
  subject to the same exact causal-null risk inequalities. Query fees are common constants and
  cancel in the difference.

## Frozen analysis and stop rule

Compute all 8 alternative tape probabilities and conditional `P(Y_4=1|y_1,y_2,y_3)` by exact
Fraction HMM filtering. Enumerate all 128 endpoint causal-null response trees and construct the
exact rational risk matrix. Solve both small LPs in floating point only to discover candidate
solutions; independently round/recover rational feasible primal policies and verify their risks
exactly. A strict monotone-class loss is established only if an exact feasible unrestricted
policy has larger savings than an independently certified upper bound for the monotone LP. If
the gap disappears or no rational certificate can be checked, record a screen failure and do not
advance a novelty claim. This is a structural counterexample screen, not a new algorithm or an
efficacy experiment.

Reproduce from repository root with `python scripts/check_switching_monotone_restriction_counterexample.py`.

## Verified result and interpretation

The exact run produced an unrestricted feasible promotion map with `q(010)=q(110)=1/10`
and zero elsewhere. Its causal-null risk is exactly `1/20`, and expected net savings before
common query charges are `19384101/250000000 = 0.077536404`. The monotone optimum has
`q(010)=q(011)=q(110)=q(111)=1/10`, risk `1/20`, and savings `174141/2500000 =
0.0696564`. The script independently checks rational primal feasibility and a rational dual
upper bound for the monotone LP. Subtracting that upper bound from the unrestricted feasible
value certifies a gap of
`2055041515184389872731146945410573/260791938073177512669324992500000000`
(approximately `0.007880004`). Both maps use the same schedule, action time, risk limit and
fees. The monotone constraint forces inclusion of tape `011`, which has negative terminal
promotion value, when it includes `010`, which has positive value.

This is a finite counterexample to monotone promotion-map restriction as an economically
without-loss simplification under recurrent regimes. It does not establish that optimal maps are
usually nonmonotone, give a scalable algorithm, or beat unrestricted adaptive acquisition. The
alternative is a fixed known HMM and the guarantee is only a finite-horizon causal-null false-
promotion constraint. Do not claim anytime validity, regret, novelty, or empirical efficacy from
this result. The cited existing line of work already treats regime-changing Markov decisions and
belief-state control; the specific exact separation above is not by itself evidence of an unoccupied
gap. The useful algorithm-design consequence is narrower: retain the full label-pattern belief (or
sufficient regime belief) in the synthesis state, and do not impose monotone promotion as a safety
shortcut. Next test whether an exact safe optimization rule with nonmonotone action regions can
beat an unrestricted robust FSC / sequence-form oracle at growing horizon and under unknown-model
robustness. That is a comparator screen, not yet a paper claim.
