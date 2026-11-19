# RB-DP: proofs of the reduction and the dyadic-lattice property

**Date:** 2026-11-13. **Author:** lead (Fable 5.2). **Status:** PROVED as written below; **not independently
reviewed**. Numerical stress tests: `scripts/paper4_continuation/rbdp/proof_stress.py`, results in §5.
Model: `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0, with delay d = 1 throughout.

## 0. Setting and notation

Times t = 1, …, T. The alternative is a two-state HMM; β_t = P(S_t = 1 | labels released before the decision at t)
and pos(β) = e0 + (e1 − e0)β = P(Y_t = 1 | β). With d = 1 a label queried at t is released before the decision at
t + 1, so at every decision the learner has seen every label queried so far.

A **pre-promotion history** h at time t is the list of query decisions at times < t with the released labels; all
actions so far are 0. It determines (t, β(h), n(h)), with n the remaining budget. At h the learner chooses one of:
promote (with or without a query), continue with a query, continue without a query. After the first promotion the
learner is unconstrained; let P(t, n, β) be the optimal expected cost from t on when promoting at t (switch cost,
optional query, optimal belief DP afterwards).

**Null classes.** A causal null ν assigns to each queried label a conditional probability
p = P(Y_t = 1 | public history, query at t) ∈ [0, 1/2]. It sees the public history (queries, released labels, the
fact that no promotion has happened), not the learner's private coins. With d = 1 there is no label the null knows
and the learner does not. The IID null fixes p = 1/2.

**Problems.** V*_X = min expected alternative cost over learner strategies with sup_{ν ∈ X} P_ν(ever promote) ≤ α,
X ∈ {causal, IID}.

## 1. Lemma A (risk-to-go recursion)

A behavioural strategy σ gives at each pre-promotion history h: π(h) = probability of promoting now, and, given no
promotion, κ(h) = probability of querying. Let R_σ(h) := sup_ν P_{ν,σ}(promotion at some time ≥ t | h reached,
not yet promoted). Then, with h·n the successor after no query and h·y the successor after a query with label y,

    R_σ(h) = π(h) + (1 − π(h)) · [ (1 − κ(h)) · R_σ(h·n) + κ(h) · m(R_σ(h·0), R_σ(h·1)) ],

where m(a, b) = max(a, (a + b)/2) for the causal class and m(a, b) = (a + b)/2 for the IID null; R_σ = 0 after T.

*Proof.* Backward induction on t. Given h and no promotion at t, a query produces Y_t ~ Bernoulli(p) with p chosen
by the null as a function of the public history. The null's choices inside the subtrees of h·0 and h·1 and its
choice of p at h are free of one another (the class is a product over histories), so the supremum of
(1 − p)·P(promote later | h·0) + p·P(promote later | h·1) is the supremum over p ∈ [0, 1/2] of
(1 − p)R_σ(h·0) + p R_σ(h·1). This is linear in p, so the maximum is at p = 0 or p = 1/2, which is m. The learner's
coins at h are drawn independently of everything the null controls, so the outer expression is the stated mixture.
For the IID null p = 1/2 is forced. ∎

*Assumptions the statement uses (added after review).* (i) The learner's coins are drawn fresh at each step and are
not visible to the null; coins already used are public through the realised actions. If the learner pre-draws a
whole plan that the null can see, the recursion fails: with T = 2 and promotion probability 1/2 after either label
the behavioural risk is 1/2 but a null that sees the pre-drawn plan reaches 5/8. (ii) The label convention is
p = P(Y_t = 1) ∈ [0, 1/2], as in the reference code. (iii) At d = 1 the null knows nothing the learner does not;
at d = 2 this fails and §2 of `DELAY2.md` applies.

## 2. Theorem 1 (exact reduction)

Define W_X(t, β, n, w) as the infimum of the expected alternative cost from time t on, over continuation strategies
whose risk-to-go is at most w, started unpromoted from belief β with n queries left. Then:

1. **V*_X = W_X(1, β_1, B, α).**
2. W_X(T + 1, ·) = 0, and for t ≤ T, W_X(t, β, n, ·) is the **lower convex hull on [0, 1]** of the function
   f(w') = min(C_N(w'), C_Q(w')) for w' < 1, f(1) = min(C_N(1), C_Q(1), P(t, n, β)), with

       C_N(w') = pos(β) + W_X(t + 1, β', n, w'),
       C_Q(w') = pos(β) + c + min { Σ_y P(y | β) · W_X(t + 1, β_y, n − 1, w_y) : m(w_0, w_1) ≤ w', w_y ∈ [0, 1] },

   (C_Q = +∞ if n = 0), β' the propagated belief and β_y the propagated posterior after label y.
3. W_X is nonincreasing and convex in w, and concave in β.

*Proof.*
(a) *Behavioural strategies suffice.* The learner has perfect recall and the null's strategy is a function of the
public history only. By Kuhn's theorem every mixed learner strategy (a private draw over pure plans) has a
behavioural strategy inducing the same distribution over public histories and promotion times against every null.
Cost and risk are functions of that distribution.

(b) *State.* For a fixed continuation strategy, the expected alternative cost from h depends on h only through
(t, β(h), n(h)) (the HMM filter is a sufficient statistic for the alternative law of the future), and the
risk-to-go does not depend on β at all. Two histories with the same (t, n) admit the same continuation strategies.
So W_X is well defined and item 1 holds by Lemma A at the root.

(c) *Bellman equation.* By Lemma A, a continuation from (t, β, n) is a choice of π, κ, and continuations at the
successors with risk-to-go values w_n, w_0, w_1; successors are distinct histories, so their continuations are
chosen independently. Its cost is π·P + (1 − π)[pos + (1 − κ)W(t+1, β', n, w_n) + κ(c + Σ_y P(y|β)W(t+1, β_y, n−1, w_y))]
and its risk-to-go is π + (1 − π)[(1 − κ)w_n + κ·m(w_0, w_1)]. Minimising the cost subject to risk-to-go ≤ w is
minimising over mixtures, with weights (π, (1−π)(1−κ), (1−π)κ), of the three points (1, P), (w_n, C_N(w_n)),
(w_q, C_Q(w_q)) with mean abscissa ≤ w.

(d) *Hull.* By induction W(t + 1, ·) is convex and nonincreasing in w. Then C_N is convex, and C_Q is convex as the
partial minimum of a jointly convex function over a convex set. For convex C_N, C_Q, mixing two points on the same
branch never beats one point on it, so the three-point mixtures in (c) attain exactly the lower convex hull of
f. All three ingredients are nonincreasing in w (the point (1, P) sits at the right end), so the hull is
nonincreasing and "mean abscissa ≤ w" may be taken with equality. This gives item 2 and the w-part of item 3.

(e) *Concavity in β.* For a fixed continuation strategy the cost is linear in the initial state distribution and
the feasible set does not depend on β; an infimum of linear functions is concave. ∎

**Corollary 1 (the premium is one constraint).** The two programs differ only in m: the causal program adds
`w_0 ≤ w'` to the IID constraint `(w_0 + w_1)/2 ≤ w'`. Γ = V*_causal − V*_IID is the cost of forbidding the risk
budget to increase after a negative label.

*Remark (where d = 1 is used).* For d ≥ 2 the null generating Y_t may know earlier labels the learner has not seen,
so the null's information is strictly finer than the learner's and Lemma A's recursion on learner histories fails
(see the witness in `docs/switching_causal_risk_planner_audit_v1.md`). The natural extension carries one risk
budget per pending-label configuration; it is not proved or built here.

## 3. Theorem 2 (dyadic lattice)

Let D_n = {k/2^n : k = 0, …, 2^n}. For X ∈ {causal, IID} and every t, β, n: **W_X(t, β, n, ·) is piecewise linear
with all breakpoints in D_n.**

*Proof.* Induction backward on t, for all β and n at once. W(T + 1) = 0. Assume the claim at t + 1.

(i) C_N(w') = pos + W(t+1, β', n, w') has breakpoints in D_n.

(ii) *Query branch, IID.* Let g_y = P(y|β)·W(t+1, β_y, n−1, ·) on [0, 1]: convex, nonincreasing, piecewise linear
with breakpoints in D_{n−1}. Because g_y are nonincreasing, the constraint w_0 + w_1 ≤ 2w' is tight (up to the cap
at 1), so C_Q(w') = pos + c + F(2w') with F(s) = min{g_0(w_0) + g_1(w_1) : w_0 + w_1 = min(s, 2)}, the infimal
convolution of g_0 and g_1. For convex piecewise-linear functions on intervals, the infimal convolution is obtained
by concatenating the linear pieces of both in order of increasing slope: the minimiser (w_0(s), w_1(s)) moves along
a monotone staircase, one coordinate at a time, and the breakpoints of F are the partial sums of the piece lengths.
Each piece length is a difference of two points of D_{n−1}, so every breakpoint of F is a multiple of 2^{−(n−1)}
and every corner of the staircase has both coordinates in D_{n−1}. Hence C_Q has breakpoints at s/2 ∈ D_n.

(iii) *Query branch, causal.* Now also w_0 ≤ w'. For fixed s = 2w' the objective φ(w_0) = g_0(w_0) + g_1(s − w_0)
is convex, so the constrained minimiser is min(w_0(s), w'), where w_0(s) is the staircase minimiser with smallest
w_0. So C_Q(w') − pos − c equals F(2w') on A = {w' : w_0(2w') ≤ w'} and H(w') = g_0(w') + g_1(w') on its
complement. F(2·) has breakpoints in D_n and H in D_{n−1}. The boundary of A is where the staircase crosses the
diagonal w_0 = w_1. Each staircase segment is parallel to an axis with its fixed coordinate v in D_{n−1}, so it
meets the diagonal at (v, v), i.e. at w' = v ∈ D_{n−1}. Hence C_Q, which is convex by Theorem 1(d), is piecewise
linear with breakpoints in D_n.

(iv) *Minimum and hull.* f = min(C_N, C_Q), modified at w' = 1 by P, is piecewise linear; its breakpoints are in
D_n or are crossing points of C_N and C_Q. Let g be the lower convex hull of f. A breakpoint x ∈ (0, 1) of g is a
point where g(x) = f(x). If f is linear near x, then g ≤ f, g convex and g(x) = f(x) imply that g is differentiable
at x (a convex function touching a differentiable-at-x majorant from below at x has a unique supporting slope),
so x is not a breakpoint of g. Ties between the branches are broken in favour of C_N; this affects no value. If x is a crossing point at which both branches are linear with different slopes, f has a
concave kink at x (left slope a > right slope b); then g ≤ f on both sides with equality at x gives left derivative
of g ≥ a > b ≥ right derivative of g, contradicting convexity. So every breakpoint of g is a breakpoint of C_N or
C_Q, hence in D_n. ∎

**Corollary 2 (exact finite program).** Let N be any integer multiple of 2^B and restrict every risk budget
(w', w_0, w_1 and hull vertices) to the grid {j/N}. The restricted program has the same value as W_X at every
grid point; if α is not on the grid, W_X(·, α) is the linear interpolation of its two neighbours.

*Proof.* By Theorem 2 it suffices that optimal controls can be taken on the grid when w' is on it. Hull vertices
are in D_n, which is contained in the grid because 2^B divides N. For w' = j/N the sum s = 2w' is a multiple of
1/N. A staircase minimiser for s has one coordinate at a corner value in D_{n−1}, which is on the grid, so the
other coordinate, s minus it, is on the grid as well. In the capped case w_0 = w_1 = w' is on the grid. ∎

**Corollary 3 (complexity and bounds).** With a belief grid of G points the program has T(B + 1)·G·(N + 1) states
with N = 2^B (times the denominator of α if α is to be a grid point), and each backward step costs O(N log N) per
belief row by slope merging. Replace exact beliefs by linear interpolation on the belief grid; interpolated rows are
convex piecewise linear in w with breakpoints in D_n, so Theorem 2 and Corollary 2 apply to the interpolated
program unchanged, and since W is concave in β (Theorem 1.3) and the Bellman operator is monotone, the interpolated
value L satisfies L ≤ V*_X. The extracted policy, executed on exact beliefs, is a legitimate strategy; its exactly
evaluated cost U satisfies V*_X ≤ U provided its exactly evaluated risk is ≤ α. So **L ≤ V*_X ≤ U** with the only
slack coming from belief interpolation.

*Remark (general rectangular nulls).* For p ∈ [0, p̄] the same argument gives m(a, b) = max(a, (1 − p̄)a + p̄ b);
Theorem 1 goes through verbatim. The lattice is then generated by p̄ and 1 − p̄ instead of 1/2 and is not checked
here.

## 4. What is and is not established

- Theorems 1–2 and the corollaries are proved above for d = 1, two-state alternatives (the two-state restriction
  is used only for the one-dimensional belief grid, not in the proofs), in exact arithmetic.
- The implementation is float64: L and U are subject to round-off, and policy-evaluation memo keys round β to 1e-12.
- An independent adversarial review was done on 2026-11-16 (`PROOF_REVIEW.md`): no claim was found wrong. It required
  the stated assumptions on Lemma A, the fix to step (iv) of Theorem 2, and these unstated facts, now recorded: the
  infimum in Theorem 1 is attained; the post-promotion cost P is concave in β; the belief grid must contain 0 and 1
  for the interpolation bound L ≤ V*; Corollary 2 holds for N a multiple of 2^B (a grid N = 3d_α that contains α but
  is not such a multiple was worse than exact in 14 of 100 reviewer runs, by up to 0.0669). The review was by a model
  subagent, not a human referee. The first version of the Bellman equation (without the hull) had been wrong and
  was caught by a numerical test.

## 5. Stress tests

Run 2026-11-13, seed 20261114, `results/proof_stress_v1.json`. Random cells: transitions and emissions in
twentieths (half the cells anti-persistent, asymmetric allowed), prior ∈ {0, 1/3, 1/2}, c ∈ {0, 1/100},
k ∈ {0, 1/20}, α ∈ {1/10, 1/7, 3/20, 1/4, 1/20}, n_beta = 201.

| Test | What it checks | Result |
|---|---|---|
| S1 (Theorem 2) | 30 cells × 2 modes, T ≤ 12, B ≤ 4, w grid of step 1/(6·2^B) so most grid points are not dyadic. Second difference in w of every stored row V(t, β, n, ·), at every grid point that is not a multiple of 2^−n | Largest off-lattice second difference 5.2e-16 (relative). 527,456 kinks, all on the lattice |
| S2 (Corollary 2) | 20 cells × 2 modes, B ≤ 4. Root value on the lattice d·2^B against 3× and 5× refinements; control grid of 3d cells (contains α, not a multiple of 2^B) | Refinements change the value by at most 8.9e-16. The control grid is worse in 9 of 40 runs, by up to 6.6e-3, and never better |
| S3 (Theorem 1, Corollary 3) | 40 fresh anti-persistent cells, T ≤ 7, B ≤ 3, lattice mode against the exact sequence-form reference `gamma_cell`, both modes | max abs(U − exact) = 8.9e-16; max abs(L − exact) = 1.1e-13. 10 of the 40 cells have a positive premium |

No test failed. These checks are numerical evidence on small and medium cells; they do not replace a review of the
written proofs.
