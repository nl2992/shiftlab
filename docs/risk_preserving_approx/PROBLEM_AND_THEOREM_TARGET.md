# Problem reconstruction and theorem target

**2026-10-29. Status:** reference reconstructed and small-cell checks reproduced;
compact approximation theorem CONJECTURED; supporting repair lemma PROVED below.
No novelty, scalable planner, or baseline win is established.

## Contract and exact reference

There are T decisions. At the start of event t release previously requested labels
whose request time plus fixed integer delay d is t. The learner sees its past
requests, deployment actions and released binary labels, then chooses deployment
and whether to request the current label. The request consumes one of B query
rights immediately, including while pending. One common outcome identifies both
bounded action losses. Decisions use the observed history and private coins only.
A switch from action 0 (the initial action) to 1 is promotion; later switches in
both directions remain permitted and cost k each. Each query costs c >= 0.

The known alternative HMM supplies expected economic cost C(pi); it is not the
null law. The null player can condition the next generated outcome distribution
on full generated history, including unreleased labels and public choices, with
conditional positive-label probability in [0, 1/2]. With tau the first event at
which action 1 is selected, define R(pi)=sup_null P(tau <= T). The target is
V*=inf{C(pi): R(pi)<=alpha, pi nonanticipating and pathwise budget <=B}.
This guarantee is for first promotion under the global null. It does not certify
future value following a regime change. Post-promotion query/rollback decisions
continue to affect C and the hard cap even after the risk event has occurred.

The generic `CausalSwitchingGame` constructs a learner realization-flow polytope
and full-information null endpoint-response flow, dualizes the null best response,
and solves the finite LP. The reduced `FirstPromotionDecomposedGame` retains the
robust pre-promotion tree but replaces each promotion continuation with an exact
alternative-HMM belief DP including pending outcomes, budget, current deployment,
and switch charges. Belief is over hidden regime and pending queried outcomes,
not merely current regime. The solver is a numerical LP with rationalized policy
and exact recovered-policy evaluations; the reported LP optimum alone is not an
exact rational optimality certificate. Fixed B history enumeration is XP in B,
not a uniform polynomial or FPT result.

## Verification performed in this worktree

- `uv sync --locked --extra dev` created the local environment.
- `uv run --no-sync pytest tests/test_first_promotion_decomposition.py tests/test_causal_switching_game.py -q`: 14 passed in 25.47 s. The tests include the
  three full/reduced cells and selected causality, timing, hard-cap and boundary
  checks; they do not certify all policies or all theorem assumptions.
- Re-ran the already registered fixed-B scaling protocol in a new output location
  using `uv run --no-sync python -c "from pathlib import Path; import scripts.benchmark_first_promotion_decomposition as m; m.OUTPUT=Path('outputs/risk_preserving_approx/oracle_reproduction_20261029'); m.main()"`.
  The untouched runner preserved its 200,000-node and 60-second LP limits. Saved
  results and source hashes: `oracle_reproduction_20261029.json` (SHA-256
  `8dfa7dbd6a90a6910b9016720ded1119abe9be87e4a7a80e5d4c702748b1663c`).
  T=6: both recover cost 461083/160000 and risk 1/10, with 21,733/1,799 nodes
  and 15,693/705 learner sequences. T=7: both recover 10788127/3200000 and risk
  1/10. T=8: full builder hit the node cap; reduced recovered 24735833/6400000
  and risk 1/10. Do not infer an independent full-oracle optimum at T=8.
- The 16 manifest reference blobs match the base Git revision. These results
  reproduce known-model synthetic solver anchors, not candidate efficacy.

## Nine-part theorem specification: joint approximation target

1. **Assumptions:** fixed finite T, B <= T and d >= 1; binary finite-outcome
   reference game; known finite-state alternative HMM; bounded losses [0,1],
   nonnegative c and k; full-history causal null above; 0 < alpha < 1.
   Any further mixing, observability, positivity or regularity assumption must be
   stated explicitly before use. Variable/informative delay is outside this target.
2. **Policy class:** all randomized nonanticipating hard-budget policies of the
   original game, including rollback and re-promotion. Approximate controllers may
   be represented compactly but the comparison remains V* over the full class.
3. **Optimization target:** expected alternative total decision, request and
   switching cost; no change of comparator to a restricted risk-gated class.
4. **Risk:** supremum over the entire causal-null family of ever promoting by T.
   The preferred output is exactly alpha-safe; any intermediate excess must be a
   proved uniform bound, not empirical calibration.
5. **Desired value:** construct pi_hat with 0 <= C(pi_hat)-V* <= epsilon_V,
   where the displayed bound is nonvacuous relative to T and includes all losses
   introduced by approximation, feasibility repair and numerical tolerances.
6. **Desired complexity:** explicitly bound time and space in T, B, d, HMM model
   size, alpha, epsilon_V and input encoding. A useful result must beat the
   appropriate expanded sequence-form/strong FSC alternatives in a declared regime;
   a T^B factor is XP rather than FPT. No such bound is proved at this checkpoint.
7. **Closest established results:** Kara–Yüksel finite-memory discounted POMDP
   approximation, Cubuktepe et al. robust FSC optimization and verification,
   Khonji et al. constant-horizon chance-constrained approximation, and Horák et
   al. one-sided POSG recursion. Precise comparison is in
   `PRIOR_ART_EQUIVALENCE_AUDIT.md`.
8. **Missing step:** construct a compact information abstraction that preserves
   both alternative value and worst-case causal-null risk uniformly, plus an
   efficient optimization/recovery procedure with a comparison to the unrestricted
   oracle. Separate fixed-controller risk verification from finding a near-optimal
   controller. A scalar certificate or alternative posterior is not assumed sufficient.
9. **Minimal discriminating instance:** the existing fixed-query T=5, B=2, d=1
   example has alternative histories 11 and 01 with identical current HMM
   posterior yet different risk-allocation value. At alpha=1/10 the stated
   full-history feasible net gain 128/125 exceeds the posterior-only upper bound
   14/25 by 58/125. It is a conditional fixed-calendar separation, not a lower
   bound for all finite-state controllers; one extra remembered bit repairs it.

## Supporting lemma: safety repair, not a novel algorithm

**PROVED, conditional.** Let pi respect the pathwise budget and nonanticipation,
let C0 be the alternative cost of the no-query, never-promote policy, let
R(pi) <= rbar where rbar is a *valid upper bound* on the full causal-null risk,
and let alpha > 0. Independently activate pi at the start with probability
p = min(1, alpha/rbar) if rbar>0, or p=1 if rbar=0; otherwise use the safe
no-query policy. Then the mixture has R <= alpha, remains budget-feasible on every
path, and C(mix)=p C(pi)+(1-p) C0. If C(pi) <= V*+eta and
rbar <= alpha+rho for rho>=0, bounded action losses and nonnegative costs give
C0 <= T, C(pi)>=0 and therefore

    0 <= C(mix)-V* <= eta + T rho/(alpha+rho).

The left inequality follows because the mixture is feasible for V*. The risk
inequality follows by conditioning on the initial coin: for every causal-null
strategy the active branch has risk at most rbar and the inactive branch has risk
zero, even if the null learns the activation choice. The cost identity follows
from the known alternative law. The repair costs at most (1-p)T; the stated
bound follows from p >= alpha/(alpha+rho). At rho=0 there is no repair loss.
This argument does not require knowing the true risk exactly, but it requires a
*valid* rbar. At alpha=0 this bound is not a small-slack approximation result;
a zero-risk policy or separate argument is required.

This is standard convex mixing, already present in the reference's calibration,
not a novelty claim or a complete algorithm. It makes the actual burden concrete:
produce a policy with a nonvacuous eta and small certified rho efficiently. The
bound may be vacuous unless rho is much smaller than alpha and eta is small.

## Immediate next action

Investigate candidate A via a risk-aware information abstraction, including the
aliasing example, then candidate B's fixed-controller verifier and optimization
separately. Formally test whether a compact abstraction satisfies a uniform
behavioral/history approximation hypothesis with useful delta and state growth;
if not, record the counterexample and move to C. No candidate currently passes
the construction or novelty gate, so no efficacy or real-data claim is supported.
