# 13 A2c: branch-conflict structure of the risk-specific timing gap

**Status (audit correction, 2026-11-04).**

- Lemmas 1–2 and Theorem 7 below concern the stated policy classes and remain valid.
- The original Proposition 3/Corollary 4 used an invalid branch-additive risk budget. Proposition 3
  is replaced below by an exact robust branch-risk bound for d=1 when the minimizing calendar
  policy queries at t=1 almost surely. The numerical branch-conflict constants and Corollary 4
  remain unestablished under that bound.
- The exact A1/A1d finite-instance gaps remain valid as solver outputs. Their qualitative
  confirmation-versus-recheck interpretation remains a hypothesis, not a theorem derived from
  Proposition 3/Corollary 4.
- The robust branch bound below does not explain the selected A3c calendar-mixture gap: in a
  representative A3c cell, the joint policy queries at t=1 with probability 3/5, while the best
  pure calendar is `{2,3,4,5}` and cannot query at t=1. Proposition 3b below gives a general
  first-query-time decomposition for calendar mixtures. On the selected grid-hull mixture, its
  conditional continuation gaps are all zero, so that decomposition does not explain the gap.
- A separate Lagrangian lower bound, evaluated over all 99 calendars, certifies at least a 1.11%
  gap in that selected cell. The joint policy's root-query branch has support at five different
  times despite the pathwise budget of four; this is evidence for a finite label-adaptive timing
  effect, not a SOTA method improvement.
- Conjecture 5 is not currently supported for the implemented risk contract. The fixed-policy
  robust recursion is now explicit, but no useful growing-family lower bound follows from it yet.
- No novelty claim: broad chance-constrained POMDP planning and adaptive sensing are established.

## Setting

The setting is the exact two-law game of A1 (`03`, `04`), with these quantities:

- **Risk level `a`.** A policy is feasible when its worst-case causal-null false-promotion
  probability is at most `a`.
- **Joint value `J(a)`.** The minimum expected cost over all policies.
- **Calendar value `C_S(a)`.** For a slot set `S` with `|S| <= B`, the minimum over policies that
  may query only at times in `S`. Using or skipping a slot, and every action, may depend on the
  history and may be randomised.
- **Best pure calendar** `C*(a) = min_S C_S(a)`.
- **Mixture value `C_mix(alpha)`.** The infimum of `sum_i lambda_i C_{S_i}(a_i)` over finite
  mixtures with `sum_i lambda_i a_i <= alpha`. This is a public coin at the root.
- **Pure-calendar gap** `delta(a) = C*(a) - J(a)`, which is at least 0.

## Lemma 1 (convexity)

`J` and every `C_S` are nonincreasing and convex on [0, 1].

*Proof.*

- *Nonincreasing.* Raising `a` enlarges the feasible set.
- *Convex.* In sequence form (realisation plans), both the cost and the null risk are linear in
  the learner's plan. The feasible set for level `a` is a polytope cut by the linear constraint
  `risk <= a`. Take `x_1` feasible at `a_1` and `x_2` feasible at `a_2`. Then
  `lambda x_1 + (1 - lambda) x_2` is a valid realisation plan with risk at most
  `lambda a_1 + (1 - lambda) a_2`. Its cost is the same convex combination of the two costs.
  Hence `J(lambda a_1 + (1 - lambda) a_2) <= lambda J(a_1) + (1 - lambda) J(a_2)`.
- The worst case over the null family is a maximum of linear functions. It is still convex in
  the plan, so the sublevel set is convex and the argument goes through unchanged.
- The same argument holds within each `Pi_S`. QED.

## Lemma 2 (mixture lemma)

Let `breve-delta` be the largest convex, nonincreasing-from-the-left minorant of `delta` on
[0, 1]. Formally, `breve-delta(alpha) = inf { E_mu[delta(A)] : mu a law on [0, 1], E_mu[A] <= alpha }`.
Then for every `alpha`,

    C_mix(alpha) - J(alpha) >= breve-delta(alpha).

*Proof.* Take any mixture `(lambda_i, S_i, a_i)` with `sum_i lambda_i a_i <= alpha`. Then

- `sum_i lambda_i C_{S_i}(a_i) >= sum_i lambda_i (J(a_i) + delta(a_i))`, by the definition of
  `delta`;
- `sum_i lambda_i J(a_i) >= J(sum_i lambda_i a_i)`, by the convexity in Lemma 1;
- `J(sum_i lambda_i a_i) >= J(alpha)`, by monotonicity.

So the mixture cost is at least `J(alpha) + sum_i lambda_i delta(a_i)`, which is at least
`J(alpha) + breve-delta(alpha)`. Taking the infimum gives the claim. QED.

**Remark 1 (correction, 2026-11-01): Lemma 2 is vacuous here.**

- In every family computed, all calendars and J coincide at a = 0, so `delta(0) = 0`.
- The law `mu` = point mass at 0 has mean 0 <= alpha. Hence `breve-delta(alpha) = 0` for every
  alpha, and the lemma's lower bound is trivially 0.
- The earlier wording ("valid but loose") understated the problem: the bound carries no
  information at all. The cause is that the proof discards the Jensen slack
  `sum_i lambda_i J(a_i) - J(alpha)`.

The correct and informative statement is definitional: `C_mix = conv(C*)`, the lower convex
envelope of `C*` on [0, 1]. The mixture gap is therefore `conv(C*)(alpha) - J(alpha)`.

Lower-bounding this gap needs information about each `C_c` between grid points. Each `C_c` is a
convex LP value function, which supplies that information:

- On a grid interval `[a_k, a_{k+1}]`, `C_c` lies above the extensions of the secants on the
  neighbouring intervals `[a_{k-1}, a_k]` and `[a_{k+1}, a_{k+2}]`. Call this pointwise maximum
  `L_c`.
- Let `L = min_c L_c`. Then `conv(L) <= conv(C*)`.
- Hence `conv(L)(alpha) - J(alpha)` is a valid lower bound on the mixture gap.
- The grid-point envelope gives an upper bound.

A1d and A2b initially reported only the upper bound. That was enough to *refute* a gap whenever
the upper bound was <= 0, but not enough to *establish* one. The follow-up `mixture_bounds.py`
construction supplies lower bounds from the same finite grid, using monotonicity and convexity
of each calendar value curve. The T=9 results and their limits are recorded in
[`results/a1d/LOWER_BOUNDS.md`](results/a1d/LOWER_BOUNDS.md). A3c separately computes two-sided
bounds for B=4, alpha=0.10. The earlier A1d "H-risk SURVIVES" labels based only on upper bounds
are superseded by these lower-bound records; do not treat the old status line as an independent
proof.

**Why the interval lower supports are valid.** On a grid interval `[a_k,a_{k+1}]`, convexity
makes the secant on `[a_{k-1},a_k]` a lower support to the right of `a_k`, and the secant on
`[a_{k+1},a_{k+2}]` a lower support to the left of `a_{k+1}`. Monotonicity gives the floor
`C_c(a_{k+1})`. Their pointwise maximum is therefore below `C_c` on this interval. Each
generated point `(a,L_c(a))` is a lower point for its corresponding calendar at the *same*
`a`; taking the lower convex hull of these points gives a lower bound on the public-coin
calendar-mixture value. The secant lines are used only on their defining interval. Extending
them elsewhere is not part of the argument.

The finite-grid audit checks monotonicity and convexity at the 14 supplied levels; it is not an
independent proof of those properties. The analytical justification is that each calendar value
is the optimum of a linear program with a single scalar risk budget, hence is nonincreasing and
convex in that budget. The saved exact rational grid costs and solver provenance remain the
computational evidence for the reported lower bounds.

**Remark 2.** Convexification (`C_mix = conv(C*)`), not Lemma 2, is why the A1c pure-calendar excess shrank under A1d. The dips in
`delta(alpha)` are non-convexities, and mixtures fill them in.

## Proposition 3 (robust branch-risk lower bound; d=1)

**Setup.**

- Suppose the calendar policy realizing `C_S` chooses `(continue, query)` at t = 1 with
  probability one. The joint planner need not be assumed to do so: the comparison policy used to
  upper-bound J copies this prefix and then chooses its continuation slots separately by branch.
- Let the first query be at t = 1 and its label be released before the t = 2 decision (delay
  `d=1`). Write `w_y` for the label branch probability under the alternative law that weights
  expected cost. The causal-null opponent chooses its conditional probability of label 1 from
  `{0, 1/2}` at each queried history.
- For branch y and continuation slot set `R` with `|R| <= B - 1`, let
  `V_y(R, a_y)` be the minimum conditional alternative continuation cost when the continuation
  policy's worst-case causal-null promotion probability, starting from branch y, is at most
  `a_y`.
- Let `V_y^free(a_y) = min_{|R| <= B-1} V_y(R, a_y)`. This is the continuation in which each
  branch picks its own slots.
- Let `Delta_y(R, a_y) = V_y(R, a_y) - V_y^free(a_y)`, which is at least 0.

Define the robustly feasible continuation-risk shares

```text
F_alpha = {(a_0,a_1) in [0,1]^2 : a_0 <= alpha, a_0 + a_1 <= 2 alpha}.
```

For a calendar `S = {1} ∪ R` whose minimizing policy queries at t=1 almost surely,

    C_S(alpha) - J(alpha)
      >= min_{(a_0,a_1) in F_alpha} sum_y w_y Delta_y(R, a_y).

*Proof.*

- If the continuation worst-case risks after first label 0 and 1 are `r_0,r_1`, the root null
  opponent can choose label-1 probability 0 or 1/2. It can also choose future responses
  independently after observing the branch. Hence root risk is exactly
  `max(r_0, (r_0+r_1)/2)`. The global risk cap implies
  `(r_0,r_1) in F_alpha`.
- The calendar's conditional alternative cost is at least
  `c_1 + sum_y w_y V_y(R,a_y)` at its achieved branch risk shares. The joint planner can use
  the same feasible shares and choose the continuation slot set separately in each branch, so
  `J(alpha) <= c_1 + sum_y w_y V_y^free(a_y)` for those shares.
- Subtract at those shares, then lower-bound by the minimum over `F_alpha`. QED.

The theorem is deliberately scoped to a query at t=1 released at t=2. For `d>1`, the learner
can make decisions while the first label is pending, so those prefix actions cannot be treated as
branch-specific continuations without an additional decomposition.

**Scope check against A3c.** For the selected cell `T=8, B=4, d=1`, transition `1/20`,
emissions `(1/50,49/50)`, prior `1/20`, `alpha=1/10`, and switch cost `1/20`, the source-verified
solver recovers joint root query probability `3/5`. The A3 result row records the best pure
calendar as `{2,3,4,5}`, which has no t=1 query opportunity. Therefore the common-root-query
assumption of this proposition fails on that cell. The proposition is an exact restricted-case
bound, not a proof of the reported A3c gap. A relevant generalization must also account for
adaptive first-query time and public mixtures across different calendar supports.

The original fixed-null version of Proposition 3 does not hold for the implemented causal-null
game. In `src/shiftlab/dive/causal_switching_game.py::_null`, after a query the null opponent
selects the conditional probability of label 1 from `{0, 1/2}` separately at each history. If
`r_0,r_1` are the worst continuation promotion risks after the first queried label, then the root
worst-case risk is

```text
max_{q in {0,1/2}} [(1-q) r_0 + q r_1]
= max(r_0, (r_0+r_1)/2),
```

not the alternative-model weighted sum `w_0 r_0 + w_1 r_1`. For example, `r_0=1/10,
r_1=4/5` gives robust risk `9/20`, whereas alternative weights `w_1=301/1250` and
`w_0=949/1250` give `0.26856`. The replacement Proposition 3 uses the exact one-query root
constraint, which is equivalent to

```text
r_0 <= alpha,    r_0 + r_1 <= 2 alpha.
```

This is a concrete robust branch-risk allocation rule, but it is not the original single
alternative-weighted budget. Proposition 3 now uses this constraint at its first-query split;
the branch values themselves must still carry the recursive robust ledger below.

## Proposition 3b (first-query-time decomposition for public calendar mixtures; d=1)

This extends the comparison to a calendar component whose first query time is random or later than
t=1. Consider an optimal feasible public-coin mixture for `C_mix(alpha)`, with components indexed
by k, weights `lambda_k`, calendar slot sets `S_k`, and component policies `pi_k`. Component k is
solved at risk level `a_k`, with `sum_k lambda_k a_k <= alpha`. Assume fixed delay `d=1`, no
outcome-bearing signal is observed before a query, and the action/query policy uses only public
history and its own randomization. Partition each component's paths that have not promoted before
their first query into pre-query action-history nodes `u` at time `tau`. Conditioning on the node
is necessary if multiple histories or public-coin outcomes share the same first-query time. For
each k and node u:

- `p_{k,u}` is the alternative probability of reaching that node before any promotion. It is also
  the causal-null probability because no labels have yet been generated.
- `w_{k,u,y}` is the alternative probability of label y at that first query, conditional on u.
- `r_{k,u,y}` is the worst conditional null promotion probability in the continuation after
  label y is generated and released at `tau+1`.
- `R_{k,u}=S_k intersect {tau+1,...,T}` is the component's remaining calendar. Its size is at
  most `B-1` because tau is the first query on that path.
- `V_{k,u,y}(R,r)` is the minimum conditional alternative continuation cost using only slots
  in R and with worst conditional null promotion risk at most r. Let `V^free` minimize over all
  slot sets of size at most `B-1`, and define
  `Delta_{k,u,y}=V_{k,u,y}(R_{k,u},r_{k,u,y})-
  V^free_{k,u,y}(r_{k,u,y}) >= 0`.

Then

```text
C_mix(alpha) - J(alpha)
  >= sum_k lambda_k sum_u p_{k,u} sum_y w_{k,u,y} Delta_{k,u,y}.
```

The sum excludes paths that promote before their first query or never query; the constructed joint
policy leaves those paths unchanged.

*Proof.* At each node u, the null opponent's first-label choice is 0 or 1/2. Since d=1, that
label is released before the next learner decision. The opponent's later information sets retain
the generated label and the history, so it can choose continuation strategies independently
after y=0 and y=1. The exact nodewise robust risk operator is therefore
`rho(r_0,r_1)=max(r_0,(r_0+r_1)/2)`, which is coordinatewise nondecreasing. Replace each
post-label continuation by the unrestricted-slot continuation at the same conditional risk cap.
Its child risks are no larger, so `rho` cannot increase. Do this separately at every pre-query
history node u and in every public-coin component. Prefix choices, first-query probabilities,
and promotion-before-query paths stay unchanged; the pathwise cap still holds because each
replacement has at most B-1 additional queries. Thus robust null risk does not increase and
alternative cost falls by at least the displayed mixture-weighted continuation savings. The
resulting policy is feasible for J(alpha), proving the inequality. QED.

This bound is exact as a comparison template but not a positive numerical certificate. The
selected A3c grid-hull mixture (a feasible upper-bound witness) has zero recovered continuation
savings for each inspected child, so this bound evaluates to zero on that witness. The witness is
not by itself proof that every continuous-risk optimal mixture has zero savings. The saved
calendar curves alone do not identify nodewise continuation values for other mixtures. A positive
uniform gap would need a quantitative obstruction for at least one child of every feasible
optimal public mixture, uniformly over its risk allocations and first-query histories. The
independent all-calendar Lagrangian certificate remains the quantitative certificate for the
selected finite-cell gap; this continuation decomposition has not yet explained it.
The bound preserves each calendar mixture's pre-query prefix and first-query-node distribution.
It therefore measures only post-label continuation-slot savings; it does not bound value from
changing the first-query-time distribution itself. That is a remaining proof obligation for the
observed adaptive-timing gap.
For d>1, this replacement is not valid as stated: while the first label is pending, only the null
opponent sees its value, so the learner must use one common pending-period continuation policy.
An extension needs an augmented pending-label state. The decomposition itself does not establish
novelty.

### A3c first-query and dual audit (exploratory)

For the selected cell `T=8, B=4, d=1`, transition `1/20`, emissions `(1/50,49/50)`, prior `1/20`,
switch cost `1/20`, and `alpha=1/10`, the saved grid-hull mixture uses equal weight on calendar
`{2,3,4,5}` at risk `3/40` and calendar `{2,3,4,6}` at risk `1/8`. Exact policy recovery shows
both components first query at t=2. For each component and each first label, the continuation
cost under its calendar equals the best fixed-calendar continuation cost at the same conditional
null risk cap. Proposition 3b's computed branch-saving term is therefore zero for this explicit
feasible upper-bound mixture. This does not rule out positive savings in another optimal
continuous-risk mixture, so it does not establish an explanation for the observed gap.

The joint optimum has root behavior `query at t=1` with probability `3/5`, otherwise skip. On the
skip branch, its positive-probability query-time union is `{2,3,4,5}`. On the query branch, the
union is `{1,2,3,4,5}`, although every individual path uses at most four queries. Thus the
label-adaptive branch cannot be represented by one four-slot calendar after conditioning on the
root query choice. This support conflict identifies a plausible source of the gap but does not by
itself lower-bound its cost.

An independent LP-dual certificate supplies a quantitative lower bound. For any risk price
`lambda >= 0`, define

```text
G_cal(lambda) = min over calendars c and their policies pi
                [alternative_cost(pi) + lambda * robust_null_risk(pi)].
```

Every feasible public mixture with average component risk at most `alpha` obeys
`C_mix(alpha) >= G_cal(lambda) - lambda*alpha`. The risk price selected from the saved grid-hull
secant is `lambda = 66535667394203/39062500000000` (about 1.70331). Solving the robust sequence-form
LP at this price for all 99 calendars gives `G_cal=1.6590211805`; hence
`C_mix(0.1) >= 1.4886898720`. The joint value is `1.4722812976`, yielding a numerical LP lower
bound of `0.0164085744` absolute, or `1.1145%` relative. The saved two-sided curve bound is slightly
stronger (`1.1734%`); the dual calculation is an independent check using the same frozen solver,
not an exact-rational proof because the LP is solved in floating point. Full inputs, price,
per-calendar optimum, solver hash, and residuals are in
`results/a3c/dual_calendar_gap.json`; the recovered branch policies are in
`results/a3c/first_query_decomposition.json`.

A control evaluation at the joint LP's risk price (`2.140875...`) gives zero: the joint and
best-calendar penalized values are both `1.6863688045`. Thus the positive certificate requires a
price away from the joint optimum, here the calendar-mixture frontier's supporting price.

The exact recursion for any fixed learner policy `pi` makes the timing/randomization issue explicit.
Let `h` be the full public action history, `o` the full generated label history (including pending
labels), `I(h,o)` the learner's released-information set, and `pi_I(a,q)` its behavior probability.
With `t = |h|+1`, set `R_pi(h,o)=0` after the horizon. Before the horizon,

```text
R_pi(h,o) = sum_(a,q) pi_I(a,q) * G_pi(h,o,a,q)
G_pi(..., a=1, ...) = 1
G_pi(..., a=0, q=0) = R_pi(h',o)
G_pi(..., a=0, q=1) = max(R_pi(h',o0), [R_pi(h',o0)+R_pi(h',o1)]/2),
```

where `h'` appends `(a,q)` and `o_y` appends the newly generated label `y` at time `t`. The
maximization is inside the learner's action average because the opponent observes the realized
`(a,q)` history and may choose its response separately at each queried history. It is also applied
before the learner next acts on a query label, since the opponent state contains the full generated
outcome history even when the label is still pending. Backward induction proves this is the exact
worst-case null promotion probability for fixed `pi`; it is the recursion implemented by
`null_risk`.

For example, if the root mixes `(continue,skip)` with probability `1-p` and
`(continue,query)` with probability `p`, with branch risks `R_skip`, `R_0`, and `R_1`, then

```text
R_pi(root) = (1-p) R_skip + p max(R_0, (R_0+R_1)/2).
```

The skip continuation and queried-label continuations must remain distinct. A scalar split over
`Y` alone misses this adaptive first-query-time branch. Although this recursion exactly evaluates
a fixed policy, optimizing over policies while retaining it does not yet yield a smaller
representation than the sequence-form robust LP: the learner's information sets must still share
behavior across all `(h,o)` pairs with the same released view, while the opponent can distinguish
their full outcome histories. A useful theorem must exploit additional structure beyond this
recursion.

## Corollary 4 (unverified branch conflict under robust risk)

Let `R_y*(a_y)` be the continuation slot sets that are optimal for branch y at share `a_y`.
Suppose there is a range `[a_lo, a_hi]` such that:

- **(i) Positive branch (y = 1).** For any share `a_1` in the range that permits promotion with
  positive probability, optimal continuations must use early confirmation slots
  (here `{2, 3}`). Omitting them costs `Delta_1 >= eta_1 > 0`.
- **(ii) Negative branch (y = 0).** The optimal continuation re-checks at a later slot (here
  `{4}`). Omitting it costs `Delta_0 >= eta_0 > 0`, uniformly over `a_0` in the range.
- **(iii) Budget.** `|{2, 3} ∪ {4}| = 3 > B - 1 = 2`.

If the stated branch-conflict conditions and constants `eta_0,eta_1` hold uniformly over the
entire robust feasible region `F_alpha`, Proposition 3 gives every calendar a loss of at least
`min(w_1 eta_1, w_0 eta_0)`. Those uniform continuation-cost inequalities have not been computed,
so this corollary does not currently establish a positive gap for the repository's game.

**Why this needs a binding constraint.**

- When `a` is large (unconstrained), the positive branch promotes *without* confirmation. Then
  `R_1* = ∅`, condition (i) fails, and the union fits the budget. Only the ordinary
  timing-adaptivity gap remains: 0.4–2.3% in A1c P3, with no growth in T.
- When `a` is small, below about 1/8 in the A1c family, promotion is infeasible or worthless in
  both branches. No queries are useful, so `delta = 0`.
- The gap therefore appears only at intermediate `a`. This matches A1c P1/P2: zero for
  `a <= 1/8`, positive from 3/20, largest for `a` in [1/4, 1/2], small at `a = 1`.
- The A1c P5 policies (T = 8, `alpha = 1/5`) show this pattern:
  - The joint planner confirms at t = 2 after `Y = 1` and re-checks at t = 4 after `Y = 0`
    (probability 0.6).
  - The best calendar `{1, 2, 3}` serves only the positive branch.
  - The calendar never re-checks after `Y = 0` and never promotes in that branch.

**What is not shown.** The constants `eta_0` and `eta_1` have not been computed over the robust
feasible region `F_alpha`. The conflict pattern alone therefore does not establish a positive
lower bound for A1.

## Conjecture 5 (growing family) — withdrawn for the implemented risk contract

Consider families in which the following quantities stay bounded away from 0 as T grows:

- the number of confirmation slots needed by the promotion branch, `k(a)`;
- the value of a delayed re-check in the non-promotion branch.

Take `B = k(a) + 1` and let regime-switch rates scale as `1/T`. Then the conjecture is that
`(C_mix - J)/J` is bounded below by a positive constant that does not depend on T, and that
this constant vanishes as `a -> 1`.

A proof under a fixed-null branch-additive variant would need:

1. an explicit lower bound on `eta_0` and `eta_1` in a parametric model;
2. an exact robust branch-risk recursion for the repository's adaptive causal-null family, replacing
   Proposition 3's fixed-null additive accounting;
3. a check that the constant can exceed the 10% practical threshold.

The data on hand does not settle point 3. The largest measured `g_mix` is 5.8% (A1d). For the
implemented causal-null game, the branch-additivity premise is additionally absent, so these
constants cannot be carried over. Reopen only after deriving a robust branch-risk decomposition
from the opponent strategy in the exact null LP.

## Empirical corroboration from A2 (added after the screen)

**Tight alpha, `a <= 1/10`.** The A2 screen gives exact zero gaps in all 108 tight-alpha cells.
The optima are contiguous label-independent bursts. This is the regime where Corollary 4's
condition (ii) fails. Under a tight budget, a delayed re-check after a negative label cannot buy
a promotion within the remaining risk share, so `eta_0 = 0`, and nothing conflicts.

This explanation is a hypothesis consistent with the data. It is not proved. It suggests a
proposition worth proving: below a model-dependent threshold `a_0`, some label-independent
calendar is optimal. Proving it would make "calendars are exactly optimal under tight risk" a
theorem rather than an observation.

## Calendar optimality: two proved sufficient conditions (added 2026-10-31)

Notation follows the setting above. A policy is a behaviour strategy over released-information
histories. For a policy `pi`, its **query support** is

    Q(pi) = { t : some history reachable under pi queries at t with positive probability }.

### Proposition 6 (support certificate)

If some optimal joint policy `pi*` at level `a` has `|Q(pi*)| <= B`, then
`J(a) = C_{Q(pi*)}(a) = C*(a)`.

*Proof.*

- The calendar class `Pi_S` contains every policy that queries only at times in `S`. Inside
  `Pi_S`, the use or skip of each slot and every action may depend on the history and may be
  randomised, subject to the pathwise budget.
- `pi*` queries only in `Q(pi*)`, and it satisfies the budget on every path, so
  `pi* ∈ Pi_{Q(pi*)}`.
- `|Q(pi*)| <= B` makes `Q(pi*)` an admissible calendar.
- Hence `C*(a) <= C_{Q(pi*)}(a) <= cost(pi*) = J(a) <= C*(a)`. QED.

This is an exact certificate for each instance. It is one-directional. If the recovered optimum
has a larger support, the result is inconclusive, because optima need not be unique.

### Theorem 7 (chain reduction)

Fix `a`. Let `pi*` be optimal for `J(a)`, and suppose it satisfies:

- **(P)** `pi*` promotes with positive probability only on histories in which `B` labels have
  been released and all of them are positive. That is, promotion requires the whole budget to
  have been spent on unanimous evidence.

Then there is an optimal policy that is a public-coin mixture of calendar policies, so
`J(a) = C_mix(a)`. If in addition the query times of `pi*` along the all-positive history are
deterministic, then `J(a) = C*(a)`.

*Proof.*

1. **Pruning.** Call a history *dead* if some released label is 0. By (P), no continuation of a
   dead history promotes.
   - Rollback presupposes promotion, so it does not occur after a dead history either.
   - So on the subtree below a dead history every action is "continue". The losses incurred do
     not depend on later queries.
   - Define `pi'` equal to `pi*`, except that it issues no new queries after a dead history.
   - Promotion behaviour is unchanged, so the worst-case null risk is unchanged.
   - Expected cost changes by `-c_q × E[#queries after death] <= 0`.
   - Therefore `pi'` is also optimal.
2. **Chain.** Under `pi'`, a query is issued only when every *released* label is positive.
   - The released-information history is then determined by time, by the public randomisation
     used so far, and by which queries are still outstanding under delay. All released labels
     equal 1, so the label content of the history is the fixed all-positive sequence.
   - Condition on the public coins used for query decisions. Each history then queries at a
     deterministic set of times `S(u)`. It contains at most `B` elements by the pathwise budget.
   - After the coins are fixed, `pi'` is in `Pi_{S(u)}`. Unconditionally it is a mixture over
     `u` of calendar policies.
   - For any fixed null-opponent strategy, risk is linear in the learner's mixing
     distribution. Taking the opponent's supremum gives a risk no larger than the mixture
     of the components' worst-case risks. Thus a mixture of components with risk shares
     `a(u)` has robust risk at most `E[a(u)]`; it is feasible under the stated averaged
     budget. Hence `C_mix(a) <= cost(pi') = J(a)`. Lemma 2 gives `C_mix >= J`, so equality
     holds. Equality of robust risk with the average component risks is not required.
3. **Deterministic timing.** If the chain's query times do not depend on the coins, `S(u) = S`
   is constant and `pi' ∈ Pi_S`. Then `C*(a) = J(a)`. QED.

**Remarks.**

- (P) is a condition on the optimum, not directly on the model. A model-level sufficient
  condition would need two things:
  - risk accounting showing that promoting on any history with fewer than `B` positive labels
    uses more of the risk budget per unit of benefit than the unanimous history does;
  - a reason why the LP never splits promotion mass onto such histories.

  Neither is derived here. That model-level statement is still conjecture (**Conjecture 8**:
  for each model there is `a_0 > 0` such that (P) holds for all `a <= a_0`).
- Delay is handled in step 2, because only *released* labels define deadness. A query issued
  before an earlier label is released can still be wasted on a branch that turns out dead. It
  is then part of the support anyway, and the budget bound still applies.
- Theorem 7 explains the A2 burst shape. Unanimous confirmation uses every query, so the
  optimum is a single chain, and the chain is calendar-implementable.
- Theorem 7 also explains the intermediate regime. Once `a` is large enough that promotion on
  non-unanimous evidence pays (that is, (P) fails), dead-history pruning no longer applies. A
  re-check after a negative label can then be valuable, which is the branch conflict of
  Corollary 4.
