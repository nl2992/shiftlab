# 13 A2c: branch-conflict structure of the risk-specific timing gap

**Status.**

- Lemma 1, Lemma 2 and Proposition 3 are proved below. The arguments are elementary.
- Corollary 4 is proved under its stated hypothesis. That hypothesis has been checked
  *qualitatively* against the A1c P5 policies; it has not been checked as a quantitative bound.
- Conjecture 5, a growing family, is open.
- None of this has been reviewed independently. It has not been audited against the literature on
  adaptivity gaps under chance constraints or on constrained POMDP sensor scheduling. That audit
  is required before any novelty claim.

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

**Remark 1.** In every A1d family the pure gap at zero risk is `delta(0) = 0`: all calendars and
J coincide at a = 0. Therefore `breve-delta(alpha) <= (alpha / a) delta(a)` for every `a >= alpha`.
Lemma 2 is valid but loose. The exact `C_mix` of A1d / A2b remains the operative quantity.

**Remark 2.** Lemma 2 is also why the A1c pure-calendar excess shrank under A1d. The dips in
`delta(alpha)` are non-convexities, and mixtures fill them in.

## Proposition 3 (branch decomposition of a calendar's gap)

**Setup.**

- Suppose both J and every calendar compared against it query at t = 1. In A1c P5 this is true
  for both policies.
- Let the first released label be `Y in {0, 1}`, with probabilities `p_0` and `p_1`.
- For branch y, a branch risk share `a_y`, and a continuation slot set `R` with `|R| <= B - 1`,
  let `V_y(R, a_y)` be the optimal continuation cost.
- Let `V_y^free(a_y) = min_{|R| <= B-1} V_y(R, a_y)`. This is the continuation in which each
  branch picks its own slots.
- Let `Delta_y(R, a_y) = V_y(R, a_y) - V_y^free(a_y)`, which is at least 0.

**Claim.** Assume the worst-case null risk decomposes additively over the two branches with
weights `p_y`. This holds when the null family is fixed before t = 1 and branch risks are
measured under the same null. Then, for a calendar `S = {1} ∪ R`,

    C_S(a) - J(a) >= min_{p_0 a_0 + p_1 a_1 <= a} sum_y p_y Delta_y(R, a_y).

*Proof.*

- `C_S(a) = c_1 + min_{split} sum_y p_y V_y(R, a_y)`, where `c_1` is the cost through t = 1.
- `J(a) <= c_1 + sum_y p_y V_y^free(a_y)` for every feasible split. In particular this holds for
  the split that is optimal for `C_S`.
- Subtracting the two at that split gives the bound. QED.

If the null risk does not decompose additively across branches, the claim needs a different
risk accounting. That is open.

## Corollary 4 (why the gap is risk-specific)

Let `R_y*(a_y)` be the continuation slot sets that are optimal for branch y at share `a_y`.
Suppose there is a range `[a_lo, a_hi]` such that:

- **(i) Positive branch (y = 1).** For any share `a_1` in the range that permits promotion with
  positive probability, optimal continuations must use early confirmation slots
  (here `{2, 3}`). Omitting them costs `Delta_1 >= eta_1 > 0`.
- **(ii) Negative branch (y = 0).** The optimal continuation re-checks at a later slot (here
  `{4}`). Omitting it costs `Delta_0 >= eta_0 > 0`, uniformly over `a_0` in the range.
- **(iii) Budget.** `|{2, 3} ∪ {4}| = 3 > B - 1 = 2`.

Then every calendar loses at least `min(p_1 eta_1, p_0 eta_0)` on any split inside the range.
Moving all risk into one branch is not free, because it changes that branch's own `V^free`.
So `delta(a)` is bounded away from 0 on that range.

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

**What is not shown.** The constants `eta_0` and `eta_1` have not been computed. Doing so needs
branch-restricted solves that the solver does not expose directly. Corollary 4 is therefore a
mechanism statement verified qualitatively, not a computed bound.

## Conjecture 5 (growing family) — open

Consider families in which the following quantities stay bounded away from 0 as T grows:

- the number of confirmation slots needed by the promotion branch, `k(a)`;
- the value of a delayed re-check in the non-promotion branch.

Take `B = k(a) + 1` and let regime-switch rates scale as `1/T`. Then the conjecture is that
`(C_mix - J)/J` is bounded below by a positive constant that does not depend on T, and that
this constant vanishes as `a -> 1`.

A proof would need:

1. an explicit lower bound on `eta_0` and `eta_1` in a parametric model;
2. the additive branch risk accounting in Proposition 3, for the repository's causal-null
   family;
3. a check that the constant can exceed the 10% practical threshold.

The data on hand does not settle point 3. The largest measured `g_mix` is 5.8% (A1d).
