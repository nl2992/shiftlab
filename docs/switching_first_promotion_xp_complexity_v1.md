# First-promotion solver: fixed-query-budget complexity screen

**Date:** 2026-10-29. **Status:** closed as a standalone method candidate after source-level
equivalence audit. Preserve the exact algorithm and bound as a reference implementation/result,
not as a novelty or publication claim.

## Contract

Use a known finite-state alternative HMM with `K` latent states, binary queried labels,
action-independent state transitions and label emissions, two deployed
models, fixed known label delay, and a pathwise request-time query cap `B` over `T` rounds.
Only released labels are visible to the learner. The causal null may choose each queried label's
full-history conditional success probability in `[0,1/2]` and observes generated labels
immediately, including labels still pending for the learner. The null's extreme choices are
`p=0` and `p=1/2`. The safety event is at least one
promotion from incumbent to challenger. Objective cost is bounded and accumulated under the
alternative HMM, including decision, query and switching costs. The learner may rollback and
re-promote after the first promotion.

This is not the arbitrary action-dependent-label model: actions do not alter the alternative
HMM or label process. That assumption is required for the post-promotion belief state below.

## Exact decomposition and history count

Let

```text
N_L(T,B) = sum_{j=0}^{min(B,T)} binom(T,j) 2^j.
N_N(T,B) = sum_{j=0}^{min(B,T)} binom(T,j) 3^j.
```

`N_L` counts learner query tapes: a subset of at most `B` event times and one binary queried
outcome per selected time. A pre-promotion learner history is determined by public time, its
query tape so far, and the subset of outcomes already released, so there are at most
`O(T*N_L)` learner histories. For a conservative extensive-form count, each queried null event
has three possible response/outcome branches: `(p=0,y=0)`, `(p=1/2,y=0)`, and `(p=1/2,y=1)`.
Thus `N_N` bounds null response/action paths, including pending outcomes known to the null.
Fixed delay changes which labels are released to the learner, but creates no new query-time
subsets.

The first-promotion event is absorbing: after its first occurrence, rollback, later promotion,
queries and costs cannot alter whether it occurred. For every learner information history at
promotion, compute the continuation value by exact belief-state dynamic programming under the
alternative HMM. The continuation state is (time, incumbent model, remaining query rights,
belief over the hidden HMM state and pending queried outcomes). In this contract, every reachable
belief is induced by a learner query tape, so there are at most
`O(T * N_L(T,B) * (B+1) * |A|)` reachable DP keys, where `|A|=2`. The hidden joint-state
belief has at most `K*2^B` entries. Current action is sufficient for switching charges because
future outcome and state laws are action-independent.

Substitute the exact continuation value at each first-promotion history into the pre-promotion
robust stopping game. Its explicit extensive-form tree has `O(T*N_N(T,B))` nodes up to a
constant depending on learner action alphabets. Its sequence-form LP has linearly many realization-flow
variables/constraints in that tree; endpoint optimization gives exact worst-case causal-null
risk for the full-history conditional null. Solving this LP and the continuation DP gives an exact
optimal policy for the declared finite model, with an exact risk certificate and exact alternative
cost. For rational inputs, the LP is rational and can be solved in polynomial time in its explicit
encoding length; arithmetic bit growth and the polynomial's degree are part of that encoding cost.

For fixed `B,K`, this is polynomial in `T`. In general it is XP in the query budget, since
`N_N(T,B) <= (B+1)(3T)^B` for `B>=1`; it is not FPT in `B` and gives no polynomial-in-T promise
when `B` grows with `T`. A worst-case per-state continuation backup over the full joint
belief costs `O(K^2*4^B)`, so a conservative arithmetic-operation bound is

```text
poly(T*N_N(T,B), input_bits) + O(T*N_L(T,B)*K^2*4^B).
```

This bound is intentionally conservative. It makes no numerical-stability claim and does not
imply an online regret guarantee under model misspecification.

## Proof obligations and failure conditions

1. The robust risk tree ends at first promotion because the event is already decided on each
   path. The null's generated pending outcomes remain in its history before promotion, so the
   construction does not collapse risk to the learner's observed filtration.
2. The continuation optimizer sees only learner-released outcomes. Its belief over the HMM and
   pending outcomes is the Bayesian sufficient statistic under the known alternative. It does
   not reuse pre-promotion test wealth as evidence of current value.
3. Query choices reduce reachable posterior histories to at most the count above because at most
   `B` labels can be requested. Deployment paths need not be enumerated after promotion: with
   action-independent dynamics, their economic effect is summarized by current deployment and
   the alternative belief.
4. If queried labels depend on deployed action, the alternative belief may depend on the full
   action history and this state-count proof fails. If the risk event also constrains rollback or
   post-promotion loss, first-promotion absorption no longer removes the continuation from the
   robust branch. If the outcome alphabet or query cap is unrestricted, the displayed bound can
   be exponential in horizon.

## Existing implementation evidence

`src/shiftlab/dive/first_promotion_decomposition.py` implements this exact split. The registered
fixed-`B=3`, `d=1` scaling output in
`outputs/first_promotion_decomposition_scaling_v1/results.json` reports exact equality of the
full and reduced recovered rational costs/metrics at `T=6,7`; only `T=6` has an independent
full-oracle bracket certificate. At `T=8`, the full reference reaches its
registered 200,000-node cap while the decomposed solver completes with 5,700 builder nodes,
2,273 learner sequences and exact causal-null risk `1/10`. The `T=8` optimum is not certified
against the failed full reference; the implementation uses a floating-point LP and exact
forward-verifies its returned policy, so it does not provide an exact optimality certificate.
The existing focused tests compare both formulations on smaller cells.

These are solver-complexity diagnostics, not matched-budget efficacy, independent confirmation,
or real-data evidence.

## Source-level equivalence audit and decision

Finite-horizon belief-state dynamic programming, query-budget state augmentation, reachability
constraints, constrained POMDPs, multi-environment POMDPs, and sequence-form extensive-game
optimization are established. For every Lagrange multiplier, the repository's hidden-root
construction represents the shared-policy objective as a one-sided POSG. Equivalently, enumerate
deterministic full-history null response policies as environments and give each environment a
hidden initial chance mode mixing the alternative-HMM cost branch and that null policy's
promotion-payoff branch. Maximizing the learner's common policy against those environments
recovers the scalarized objective exactly. The null policy set can be exponentially large, so
this is a model-class equivalence, not a compact implementation claim.

The first-promotion truncation and the post-promotion HMM belief continuation are standard
absorbing-event decomposition and belief-state planning. The displayed `N_N(T,B)` count is a
straightforward query-history bound under the declared hard budget and action-independent label
law. It is a valid bound for this implementation, but this work has not established that the
bound yields a complexity separation from established robust POMDP / multi-environment POMDP /
one-sided-POSG planning, or that the decomposition is a new algorithmic mechanism.

The source-level comparison includes RAO* finite-horizon chance-constrained POMDP planning;
Khonji et al.'s sequence-tree constrained-POMDP approximation; Ho et al.'s recursive constraints;
and Horák et al.'s one-sided-POSG strategy composition. More directly, Bovy et al. study robust
planning over multiple POMDP environments, and Brice et al. give finite-horizon multi-environment
POMDP complexity and exact/approximate algorithms. Those works do not, in the sources reviewed,
state this exact economic-cost/causal-null formulation or this particular query-history bound.
However, their robust shared-policy model class, together with the already-audited hidden-root
one-sided-POSG reduction, is sufficient to show that the candidate is an instance of established
robust partially observed planning. The local evidence only shows implementation efficiency
against this repository's generic reference solver on one small scaling cell, not an advantage over
the strongest applicable algorithms. Relevant primary-source audits are
`switching_causal_risk_planner_audit_v1.md`, `switching_ccpomdp_approximation_audit_v1.md`,
`switching_rc_pomdp_prior_audit_v1.md`, `switching_lagrangian_posg_reduction_v1.md`, and
`switching_first_promotion_decomposition_v1.md`.

The candidate is therefore closed as a standalone contribution route. Keep the decomposition,
solver, and tests as exact reference artifacts; do not scale them or describe the XP bound as a
novelty result without a later proof of a strict algorithmic separation from robust-FSC,
multi-environment-POMDP, or one-sided-POSG methods. G1 remains open for a different candidate.
G2–G5 remain held, and no real-data or efficacy study is authorized by this solver result.

## Verification boundary

The complexity proof remains a conditional statement for the finite registered model. It does not
provide a regret bound under misspecification, guarantee utility after regime reversal, or show
that historical promotion evidence certifies current challenger benefit. Economic continuation
forecasts and historical null-risk evidence remain separate quantities.
