# Candidate A1: approximate only the post-promotion economic continuation

**2026-10-29. Status:** proposed construction; transfer bound SKETCHED and
conditional; novelty and computational advantage UNRESOLVED. No implementation
or efficacy comparison has been performed. This is a research direction within the
original unrestricted two-law formulation, not a replacement objective.

## Why this avoids the known aliasing failure

Keep the entire pre-promotion learner history, causal-null response game, query
budget, release timing and risk constraint exactly as in the first-promotion
sequence-form formulation. Only after the first promotion, replace the exact
alternative-HMM continuation DP by an approximate finite-grid POMDP planner. The
first-promotion event has already occurred, so the approximation cannot change its
probability under any null. Continue to model requests, delayed observations,
remaining budget, rollback, re-promotion and switching charges after promotion.
The learner never sees pending values. Do not compress the risk-relevant history
before promotion: the prior equal-posterior counterexample remains intact.

For each first-promotion information history and promotion/query action, compute an
approximate continuation cost and a realizable continuation controller. Insert the
cost as that action's terminal coefficient in the unchanged pre-promotion LP. A
single controller should be shared across repeated occurrences of a grid state,
while time, action, budget and public pending-request schedule remain explicit.
When a grid belief gives zero likelihood to an actually observed release, define a
fallback controller before execution; no division by zero or access to hidden labels
is permitted. A zero-likelihood observation can occur under the true belief even
when it is absent under the rounded belief.

## Conditional transfer lemma

Fix T, B, d, finite-state known alternative model and bounded nonnegative
per-event total cost at most L=1+c+k. At each post-promotion decision, suppose a
projection Q replaces the learner's current conditional distribution on the
current hidden regime and pending outcome values by a belief at total variation
(TV) distance at most delta. Projection must preserve the public pending-request
schedule, remaining rights and deployment. Suppose all initial and subsequent
projections obey the bound, an approximate POMDP DP is solved globally for those
grid transitions, and its selected policy is executed by updating the same grid
memory using only revealed observations. Assume the pre-promotion robust LP is
solved exactly and supplies the same learner decisions under both laws.

Then the constructed policy has pathwise query use <= B, exactly the same
worst-case causal-null first-promotion risk as its selected pre-promotion policy,
and, provided that risk is <= alpha,

    0 <= C_alt(pi_grid) - V* <= L delta T(T+1).

**Proof sketch and audit obligation.** From a public history and belief b, a
maximal coupling of b and Q(b) disagrees with probability at most delta. Couple
all later transition, observation and policy randomization whenever their current
latent/public states agree. If another projection is applied each subsequent
round, the probability of having diverged by event j is at most j delta. This
argument compares a fictitious grid-reset model with the actual alternative model;
it does not expose or physically overwrite pending values. For any fixed grid
controller, the expected cumulative-cost discrepancy is at most
E=L delta T(T+1)/2, by summing the per-event coupling discrepancies. The same
bound applies to any feasible continuation policy expressible in the projected
belief model, with off-support choices defined, and to their optimal values: a
true optimal continuation can be executed using its full observation history in
either model, so the uniform per-policy comparison is essential. The approximate
optimal continuation is thus within 2E of the true continuation optimum in
realized alternative cost.

For each pre-promotion policy, promotion occurs at most once; consequently replacing
its exact continuation by the grid continuation increases its expected cost by at
most 2E. More precisely, the grid model's terminal objective differs from the exact
one by at most E; optimize the former over the same pre-promotion feasible set,
then compare its realized value with the true optimum to obtain the displayed 2E
bound. The causal-null event is unchanged by all post-promotion behavior, including
any fallback. The pathwise budget is preserved by the action set. This proof is
**SKETCHED**: verify carefully that the grid DP really optimizes over all
observation-history continuations in the fictitious reset model and that its
projection is definable on every reachable public queue schedule. LP numerical
feasibility and rational recovery must be certified separately; floating-point
solver success alone does not prove exact alpha-safety.

## Explicit finite-grid size and limitation

For a two-state HMM with one binary request per event and fixed d, immediately
after due releases and before the next decision the queue contains at most
q=min(B,d-1) unresolved labels. Conditional on its public schedule, there are at
most K=2^(q+1) hidden regime/queue configurations. A denominator-N probability
simplex grid has at most binomial(N+K-1,K-1) points, and largest-remainder
rounding gives TV <= K/(2N). For each time, budget, action and public queue
schedule, a direct grid DP has polynomially many action/observation transitions
per grid point, giving an explicit finite cost conditional on fixed d and HMM
size. Substituting yields the conservative cost bound

    L K T(T+1)/(2N).

This bound does **not** make the whole solver FPT in B: the original robust
pre-promotion tree and its LP are still present, and their history count is XP in
B. Grid size is also exponential in the queue-dependent state dimension. The
construction can only improve the continuation subproblem; whether that produces
an end-to-end speed or memory gain is an empirical and complexity question.
For the registered T=6, d=1 cell, K=2 and L=1.11; this bound is 46.62/N, so a
0.01 absolute guarantee requires N>=4662. That is a deliberately conservative
bound and does not imply a practical improvement over the exact reference.

## Prior-art comparison and decision gate

- Finite-grid POMDP value approximation is established by Lovejoy and point-based
  value iteration. The delayed belief/queue information state is established by
  the approximate-information-state and delayed-POMDP literature; see
  `switching_delayed_pomdp_information_state_audit_v1.md`.
- The first-promotion decomposition and fixed-controller safety verification are
  established in this repository and have direct robust-control precedents. The
  sketch above is a composition of those ingredients and does not establish a
  distinct methodological result. The exact source-level reduction to published
  approximation/error results remains **UNRESOLVED — EXACT REDUCTION REQUIRED**.
- This is not a solution to the open pre-promotion risk-memory bottleneck. The
  no-promotion, equal-posterior and signed-event counterexamples remain relevant to
  any further compression. Its claimed advantage must be end-to-end runtime or
  memory at matched safety and cost, not a belief-grid state count in isolation.

**Decision:** continue with a proof audit, source-level comparison and an explicit
complexity comparison against the existing exact continuation cache. Implement a
candidate only if that comparison identifies a defensible advantage and the stated
proof obligations are closed. If the pre-promotion LP dominates or the composition
is equivalent to known methods, retain this as a useful baseline and proceed to
candidate B/C. No real-data or synthetic efficacy result follows from the sketch.
