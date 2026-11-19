# RB-DP proofs: independent review

**Date:** 2026-11-16. **Reviewer:** independent referee subagent (Claude). **Scope:** `PROOFS.md` (Lemma A,
Theorems 1–2, Corollaries 1–3, remarks) and `DELAY2.md` §1–4. The model reference is
`src/shiftlab/dive/causal_switching_game.py` and `first_promotion_decomposition.py`. No repository file was edited.
Scratch scripts are under
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML/8ff2e6ac-504f-417d-a434-48f69d63a593/scratchpad/review/`.
That is a temporary directory; copy the scripts into the repo if they need to be kept.

Corollary numbering below follows `PROOFS.md`: Cor 1 = "premium is one constraint", Cor 2 = "exact finite
program (w grid)", Cor 3 = "complexity and bounds L ≤ V* ≤ U". Concavity in belief is Theorem 1, item 3, and has
its own row.

## 1. Verdicts

| Claim | Verdict | Justification |
|---|---|---|
| Lemma A (risk recursion, d = 1) | **PROVED** (one assumption must be stated explicitly) | The causal class is a product over public histories, so in the subtrees after h·n, h·0, h·1 and in the choice of p at h the null chooses independently. Then sup_ν[(1−p)A(ν₀) + pB(ν₁)] = sup_p[(1−p)sup A + p sup B], because the weights are nonnegative and the subtree strategies are separate. This is linear in p, so the supremum is attained at p ∈ {0, 1/2}, which gives m(a,b) = max(a, (a+b)/2) with a = risk after label 0. The formula is asymmetric on purpose: it is correct for the convention that the null bounds P(Y = 1) ≤ 1/2, and that is the convention of the reference code (`null_risk`: `max(zero, (zero+one)/2)`). At d = 1 the null has no information the learner lacks. Past learner coins are public through the realized query and promotion choices. The only assumption doing work is that the learner's coin for a step is drawn at that step and the null never sees it. If the learner instead pre-draws a pure plan and the null can condition on it, the lemma fails. Counterexample: T = 2, query at t = 1, promote at t = 2 with probability 1/2 after either label. The behavioural risk is 1/2, but a null that sees the plan gets 5/8. `PROOFS.md` §0 says the null does not see private coins, so the lemma is correct for the stated model. The policy must also be executed that way (fresh coins at each step). Kuhn's theorem is used correctly: for each fixed null, P(ever promote) is a function of the distribution over terminal histories, which realization-equivalent strategies share, so the supremum over nulls is shared too. Minor wording: R_σ(h) should be defined as the supremum over continuation nulls of the subtree value, not as a conditional probability given h, because h can have probability 0 under the maximizing null. Brute force agrees exactly (§3a). |
| Theorem 1 (exact reduction, d = 1) | **PROVED** (minor gaps in exposition) | (a) Behavioural strategies on learner histories lose nothing, by Kuhn and perfect recall. (b) The cost-to-go depends on h only through (t, β, n) and the risk-to-go not at all, so (t, β, n, w) is a sufficient state, and the root problem decomposes exactly by Lemma A. (c) Promotion is exact: R = π + (1−π)·R_cont, with π known and independent of the null, so π + (1−π)w' ≤ w is the exact worst case, not just an upper bound. (d) Convexification in w is legitimate. The three branches (promote, no query, query) are publicly distinguishable before the null acts, so the worst case of a branch mixture is the mixture of the worst cases. Mixing two budgets inside one branch is never needed, because C_N and C_Q are convex. C_Q is convex as a partial minimum of a jointly convex function over the convex set {m(w₀,w₁) ≤ w'}, since m is convex. Even mixing that the null cannot observe would only lower the true risk (the supremum of a mixture is at most the mixture of suprema), so the hull can never be infeasible. The hull of three convex branch graphs is attained with one point per branch, and equality in "mean ≤ w" is justified because the branches are nonincreasing and the promotion point sits at w = 1. Edge cases are fine: n = 0 gives C_Q = +∞; at t = T the query branch is dominated; a label queried at T is never used; w = 0 forces w₀ = w₁ = 0 in both modes; w = 1 adds P. Gaps to fix: the proof should state that the infimum is attained (finite game, compact strategy set, continuous cost and risk); that P(t, n, β) is also concave in β (Cor 3 needs it); and the formal domain w ∈ [0, 1]. The independent LP matches RB-DP to ≤ 1.3e-15 on 10 cells, 7 of them with a positive premium (§3b). |
| Theorem 1.3 (convex, nonincreasing in w; concave in β) | **PROVED** | In w this follows from the hull construction. In β: for a fixed continuation strategy (post-promotion play included), the alternative cost is linear in the law of S_t, and the set of strategies with risk-to-go ≤ w does not depend on β, so the infimum is concave. The same argument gives concavity of P(t, n, ·), which should be said explicitly. |
| Theorem 2 (breakpoints in D_n) | **PROVED** (two wording fixes) | The statement is about the exact W_X at exact beliefs, for every β at once. Holding β fixed is not an issue: the induction hypothesis at t+1 is for all beliefs, including the posteriors β_y, and the step only uses that the next-stage rows are convex, nonincreasing and PL with breakpoints in D_n (no-query) and D_{n−1} (query), multiplied by nonnegative weights P(y∣β). (ii) IID: the breakpoints of F are partial sums v₀ + v₁ with v_y ∈ D_{n−1}, so C_Q(w') = F(2w') has breakpoints in D_n. Correct. (iii) Causal: on the line w₀ + w₁ = s the objective is convex, so capping the smallest minimiser at w' is right, and the switch points are where the axis-parallel staircase meets the diagonal, at (v, v) with v ∈ D_{n−1}. Correct, given a fixed tie-break (the smallest w₀), which (iii) uses and (ii) should also state. (iv) Hull: crossings of C_N and C_Q are concave kinks and cannot be hull vertices. Correct. The sentence "g ≤ f, g convex, g(x) = f(x) force g = f near x" is false as written: g can lie strictly below f away from x. The correct statement, which is all the proof needs, is that g is differentiable at x with the slope of f. The proof also uses without saying it that hull vertices are contact points of f; that holds because f is lower semicontinuous on [0, 1] (the possible jump at w = 1 is downward). Base case and n = 0 are fine. The cap w₀ ≤ w' never needs w₁ > 1, since w₁ = w' at the cap. Exact rational verification found no violation in 45,768 rows, B ≤ 4 (§3c). |
| Cor 1 (premium = one constraint) | **PROVED** | max(a, (a+b)/2) ≤ w' iff a ≤ w' and (a+b)/2 ≤ w'. "Negative label" means y = 0. |
| Cor 2 (grid N = multiple of 2^B is exact) | **PROVED** | The exact hull vertices are contact points in D_n ⊆ grid. At grid points w', the IID and causal split minimisers can be chosen on the grid: one coordinate is a staircase corner in D_{n−1} and the other is s − corner, or w₀ = w₁ = w'. So by backward induction the restricted f equals the exact f at grid points, and the grid hull equals the exact hull there. For α off the grid, linear interpolation between the two neighbouring grid points is exact because both lie in one D_B cell. Note: "2^B points refined to contain α" is exact only if the refinement keeps N a multiple of 2^B (N = d_α·2^B in the code). A grid that contains α but has N = 3d_α was worse than the exact value in 14 of 100 adversarial runs, by up to 0.0669 (§3c). The proof should state the induction (restricted W(t+1) = exact W(t+1) on the grid) rather than leave it implicit. |
| Cor 3 (L ≤ V* ≤ U) | **PROVED** for the mathematical program; implementation caveats | Linear interpolation of a concave function lies below it. The Bellman operator (min, partial min, lower hull) is monotone. Interpolated rows are convex combinations of rows with breakpoints in D_n, so Theorem 2 and Cor 2 hold for the interpolated program, and L is its exact value, hence L ≤ V*. This needs concavity of the true W and of P in β (true, but the second is not stated) and a belief grid that contains 0 and 1. U ≥ V* holds because U is the exactly evaluated cost of a policy whose risk is verified ≤ α by the Lemma A recursion (in float). With real interpolation error (coarse grids, no reachable-belief extras) the sandwich held in 80/80 runs (§3d). Implementation defect found: when β₁ = 1 exactly (for example prior 0 with t01 = 1), `risk_budget_dp_fast` returns L = NaN (RuntimeWarning at `locate`, line 251). The likely cause is that line 279 appends β₁ to a uniform grid that already contains 1.0, creating a zero-width last interval. In 3 of those 5 cells U was valid but far from optimal (for example U = 5.94 vs V* = 0.7352). The complexity claim O(N log N) was not checked. |
| DELAY2 §1–4 (d = 2 derivation) | **GAP** (sound derivation; several proof steps missing) | Lemma A₂ is right. The null-side state is (h, z); the null may condition p on the pending z; the recursion runs on full histories and matches brute-force enumeration of nulls that see z exactly in 44/44 runs (§3a). The pair state (w⁰, w¹) is sufficient: the parent's constraint m(R(h,0), R(h,1)) ≤ w' depends on the continuation only through that pair, and the cost-to-go only through (t, μ, n). The 2-D hull is the right object because π and κ are shared across z, so all coordinates mix with the same weights. The lagged-belief indexing is consistent: step cost pos(prop μ); no-query → prop∘prop∘post(μ, z); query → prop∘post(μ, z); from a no-pending state a query passes β itself as the next lagged belief; P(z∣μ) = pos(μ). Missing for a proof: (1) joint convexity of V¹ in (w⁰, w¹) and convexity of each branch. Both hold: the no-query branch is a separable sum of convex functions, and the query branch is a separable sum of per-z partial minima of a convex V¹ over the convex set {m(a,b) ≤ w^z}. Without this, "one point per branch" in the 2-D hull is unjustified. (2) Coordinatewise monotonicity, so that the componentwise constraint R(h,z) ≤ w^z can be taken with equality. It holds because the branches are nonincreasing and the promotion point is (1,1). (3) An explicit definition of P¹ and of terminal and edge cases (queries at T−1 and T are never released). (4) Grid exactness is not proved. §4 says the dyadic argument does not transfer; the d = 2 solver is certified only through exact policy evaluation (U), and has no L. None of these gaps is a known error. |

No claim was found WRONG.

## 2. Required fixes

1. **Lemma A / §0:** State as a modelling assumption that learner coins are drawn at decision time and are never visible to the null, and that RB-DP policies must be executed that way. Without it the risk bound is false (1/2 vs 5/8 example above). Define R_σ(h) as a subtree supremum, not as a conditional probability.
2. **Theorem 1:** Add attainment of the infimum, the domain w ∈ [0, 1], and the concavity of P(t, n, ·) in β, by the same argument as (e).
3. **Theorem 2 (iv):** Replace "force g = f near x" with "force g to be differentiable at x with the slope of f". State that hull vertices are contact points because f is lower semicontinuous on [0, 1]. In (ii), state the tie-break (the smallest-w₀ staircase).
4. **Corollary 2:** Write the backward induction explicitly: the restricted W(t+1) equals the exact W(t+1) on the grid, so the restricted f equals the exact f there. State that the refinement containing α must keep N a multiple of 2^B.
5. **Corollary 3:** Say that L ≤ V* also uses concavity of the post-promotion value P in β and a belief grid containing 0 and 1. Note float round-off in the risk check behind U.
6. **Implementation (outside the proofs):** Fix the β₁ = 1 case in `risk_budget_dp_fast` (deduplicate the belief grid or guard the zero-width interval in `locate`). Update the solver docstring, which still says the lattice lemma is "not formally proved in the repo".
7. **DELAY2:** Add items (1)–(3) from the DELAY2 verdict before calling it a proof. Keep the d = 2 lattice exactness labelled as empirical.

## 3. Numerical-check log

All runs used `uv run --no-sync python <script>` from the repo root, on 2026-11-16. The scripts are in the scratch directory named at the top: `common.py` (exact model primitives and post-promotion DP) and the scripts listed in each section below.

### (a) Lemma A and Lemma A₂ against brute-force null enumeration — `check_a_lemmaA.py`, log `check_a.log`

Setup: random behavioural policies (π, κ ∈ {0, 1/10, 1/4, 1/3, 1/2, 2/3, 1}) on learner information sets.
- d = 1: (T, B) ∈ {(2,1), (3,1), (3,2), (4,1), (4,2), (5,1)}, 44 policies.
- d = 2: the same grid and 44 policies. The learner does not see the pending label; the null sees it.

Checks per policy:
- All 2^K deterministic nulls with p ∈ {0, 1/2} at every query node (K ≤ 16, up to 65,536 nulls) give a forward promotion probability. The maximum is compared with the Fraction recursion, and the maximizing null is re-evaluated exactly.
- 20,000 random continuous nulls with p ∈ U[0, 1/2].
- The IID null.

| Result | Value |
|---|---|
| Runs | 88 |
| Exact equality (brute-force arg-max null vs recursion, Fractions) | 88/88 |
| Max float difference | 2.2e-16 |
| Continuous null exceeding the recursion | 0 |
| IID null equal to the IID recursion | 88/88 |
| Plan-observing null (T = 2, q₀ = q₁ = 1/2) | behavioural risk 1/2, plan-observing 5/8 |

### (b) Independent exact optimum vs RB-DP (d = 1) — `check_b_lp.py`, results `check_b_results.json`, log `check_b.log`

The LP runs over the learner's full sequence-form tree, post-promotion play included, so it uses no first-promotion decomposition, no belief state and no w state. The causal risk constraint is imposed in two ways:
- **Dual:** the null's best response over p ∈ [0, 1/2], written as its sequence-form dual. Used on every cell.
- **Enumeration:** one explicit row per reduced deterministic null, used where there are ≤ 40,000 such nulls.

The IID case uses a single row. RB-DP is `risk_budget_dp_fast.solve` with `lattice_exact=True`, n_beta = 201.

| Cell (prior 1/2 unless noted) | V*_IID (LP) | V*_causal (LP) | Γ | max \|RB-DP − LP\| (L, U, both modes) | enumeration − dual |
|---|---|---|---|---|---|
| t=9/10, e=1/10, T5 B2, c=k=0, α=1/10 | 2.3488576 | 2.40784 | 0.0589824 | 1.3e-15 | n/a (4.7M nulls) |
| same, α=1/5 | 2.1977152 | 2.31568 | 0.1179648 | 1.3e-15 | n/a |
| t=9/10, T4 B2, c=1/100, k=1/20, α=1/10 | 1.9214 | 1.941344 | 0.019944 | 2.2e-16 | 0 (17,280 nulls) |
| t01=2/5, t10=1/20, e=(1/10, 3/5), prior 0, T4 B2, α=1/7 | 1.6608967143 | 1.6616092857 | 0.0007126 | 6.7e-16 | 2.2e-16 |
| t=3/4, e=(1/5, 4/5), T5 B1, c=1/100, k=1/10, α=3/20 | 2.491 | 2.4955 | 0.0045 | 4.4e-16 | 0 (32 nulls) |
| t01=4/5, t10=7/10, prior 1/3, T3 B2, c=1/50, α=1/3 | 1.4980667 | 1.4980667 | 0 | 0 | 0 |
| t01=17/20, t10=13/20, e=(3/20, 4/5), prior 1/3, T5 B2, c=1/100, k=1/20, α=1/7 | 2.5961002 | 2.5961002 | 0 | 8.9e-16 | n/a |
| t=1/4 (persistent), T5 B2, c=1/200, k=1/20, α=1/10 | 2.4256 | 2.4256 | 0 | 4.4e-16 | n/a |
| t=9/10, T6 B1, α=1/10 | 2.89506048 | 2.91394304 | 0.01888256 | 8.9e-16 | 0 (64 nulls) |
| t=9/10, T4 B3, c=1/100, α=1/5 | 1.7619836 | 1.8524 | 0.0904164 | 2.2e-16 | n/a |

In every positive-premium cell the IID-mode RB-DP policy has causal risk 2α (2.5α in the last cell), and the causal-mode policy has risk α. Cross-check of my formulation against the repo's reference (`check_b2_vs_repo_reference.py`, log `check_b2.log`), on the test cell t = 9/10, T5 B2, c = 1/100, k = 1/10, α = 1/10:

| Source | V*_causal | V*_IID |
|---|---|---|
| My LP | 2.441888 | 2.4002176 |
| My exact PL DP | 76309/31250 | 187517/78125 |
| `gamma_cell` (U) | 76309/31250 | 187517/78125 |

The exact PL root values (§3c) equal the LP values in every cell above (for example 2.40784 and 1.6616092857142857).

### (c) Theorem 2 in exact arithmetic, and adversarial draws — `check_c_lattice.py`, `check_c2_adversarial.py`, results `check_c_results.json`, `check_c2_results.json`, logs `check_c.log`, `check_c2.log`

Method: W(t, β, n, ·) is built as an exact rational PL function at every reachable exact belief.
- C_Q(w') is evaluated exactly at any rational w' by enumerating all vertices of the (w₀, w₁) polygon arrangement. This does not use the proof's slope-merging argument.
- Linearity of C_Q on every dyadic cell of D_n is tested by exact chord equality at 1/3, 1/2 and 2/3 of the cell. Because C_Q is convex, a single equality at an interior point implies the cell is linear.
- Crossings of C_N and C_Q are inserted, the exact lower hull is taken, and every hull vertex outside D_n is recorded.

| Run | Rows | Chord tests | Chord failures | Off-lattice hull vertices | Crossings (none became vertices) |
|---|---|---|---|---|---|
| 10 fixed cells × 2 modes | (in totals) | | 0 | 0 | |
| 60 random cells × 2 modes (T ≤ 7, B ≤ 3, anti-persistent and asymmetric, c, k ≠ 0, α ∈ {1/10, 1/7, 3/20, 1/3, 2/9, 1/20}) | 8,356 | 28,848 | 0 | 0 | 720 |
| 50 adversarial cells × 2 modes (T ≤ 8, B ≤ 4, t ∈ {0, 1/20, 1/3, 1/2, 13/20, 9/10, 19/20, 1}, e₀ up to 49/100, e₁ down to 51/100, priors {0, 1, 1/2, 3/7}, c up to 1/2, k up to 1/3, α ∈ {1/3, 2/7, 1/11, 3/13, 1/100, 1/10, 5/6}) | 37,412 | 159,468 | 0 | 0 | 2,446 |

RB-DP (lattice_exact) against the exact value on the adversarial cells:
- 90 of 100 runs were finite: max |L − V*| = 1.8e-15 and max |U − V*| = 1.3e-15.
- 10 runs (5 cells with β₁ = 1) returned L = NaN. U was valid but suboptimal in 6 of those 10 runs, by up to 5.2.
- A control grid of N = 3d_α (contains α, not a multiple of 2^B) was worse than V* in 14 of 100 runs, by up to 0.0669.
- 3 of the 50 adversarial cells have a positive premium.

### (d) Corollary 3 with genuine interpolation error — `check_d_sandwich.py`, log `check_d.log`

The 10 cells of (b) × 2 modes × n_beta ∈ {3, 5, 11, 41} were run with n_extra_max = 0 (no reachable-belief points added) and lattice_exact. Over 80 runs the sandwich L ≤ V* ≤ U held with no violation, risk was ≤ α in every run, and the maximum U − L was 0.0288. In the repo's own S3 test, L equals V* to about 1e-13 because reachable beliefs are added to the grid, so that test does not exercise interpolation slack.

## 4. What I did not check

- The O(N log N) per-row complexity and the state count of Cor 3.
- The float round-off of the implementation beyond the observed ~1e-15 agreement. I did not do a formal error analysis of the float risk check behind U.
- The repo's `proof_stress.py` results (§5 of `PROOFS.md`), which I did not rerun; my checks replace them.
- The "general rectangular nulls" remark beyond the m formula, which is correct.
- DELAY2 §5–7: the d = 2 solver, its numbers, the long-horizon tables, and the memory fix. For d = 2 I checked only the risk recursion (Lemma A₂) by brute force, plus the derivation by reading. I did not build an independent d = 2 optimum, and d = 2 grid exactness is unexamined.
- Cells beyond T = 8, B = 4 for Theorem 2, and beyond T = 6 or B = 3 for the LP comparison.
- `RESULTS.md`, `E1_E4_*.md`, `E2_E3_*.md`, `D2_LONG_HORIZON.md`, and the claims about M1–M11.
