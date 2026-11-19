# RB-DP for delay d = 2: derivation

**Date:** 2026-11-13. **Author:** lead (Fable 5.2). **Status:** derivation (proof at the level of `PROOFS.md` §1–2,
not independently reviewed). Results in §5.

## 1. What changes at d = 2

A label queried at t is released before the decision at t + 2. At the decision at time t the label queried at
t − 1 (if any) is **pending**: the null has seen it, the learner has not. The null's choice of p for a query at t
may depend on the pending value z. So the worst-case risk-to-go lives on null-side states (h, z), with h the
learner's history and z ∈ {0, 1} the pending value, and the learner at h must carry **one risk budget per pending
value**: a pair (w⁰, w¹) when a label is pending, a scalar w otherwise.

## 2. Risk recursion (Lemma A₂)

Behavioural strategy: at learner history h, π(h) = probability of promoting now, κ(h) = probability of querying
given no promotion. Both are functions of h only: the learner does not know z. With m(a, b) = max(a, (a + b)/2)
(causal) or (a + b)/2 (IID):

- pending label z at h (queried at t − 1; it is released before t + 1, giving learner history (h, ·, z)):

      R(h, z) = π(h) + (1 − π(h)) · [ (1 − κ(h)) · R((h, n, z))  +  κ(h) · m( R((h, q, z), 0), R((h, q, z), 1) ) ]

- no pending label at h:

      R(h) = π(h) + (1 − π(h)) · [ (1 − κ(h)) · R((h, n))  +  κ(h) · m( R((h, q), 0), R((h, q), 1) ) ]

where R(h', y) is the risk-to-go at the next learner history h' when the label just queried has value y. The proof
is the backward induction of Lemma A on null-side states; Kuhn's theorem for the learner does not depend on the
null's information.

## 3. Bellman equations

Belief state. With a pending label, the joint law of (S_t, z) given the released labels is determined by the
scalar μ = P(S_{t−1} = 1 | labels queried at times ≤ t − 2). Without one, use β = P(S_t = 1 | released labels).
Write prop for one transition step, post(μ, z) for the Bayes update on a label, P(z | μ) for its predictive
probability, and pos(β) = e0 + (e1 − e0)β. Step cost when continuing at t is pos(β_t) with β_t = prop(μ) in the
pending case (z is not known). P⁰, P¹ are the optimal post-promotion costs (ordinary d = 2 belief DP) when
promoting at t without and with a pending label.

**No pending label:** V⁰(t, β, n, ·) is the lower convex hull on [0, 1] of

    no query:   pos(β) + V⁰(t+1, prop(β), n, w')
    query:      pos(β) + c + min { V¹(t+1, β, n−1, a, b) : m(a, b) ≤ w' }
    promote:    the point (1, P⁰(t, n, β)).

**Pending label:** V¹(t, μ, n, ·, ·) is the lower convex hull on [0, 1]² of

    no query:   pos(prop μ) + Σ_z P(z|μ) · V⁰(t+1, prop(prop(post(μ, z))), n, w^z)
    query:      pos(prop μ) + c + Σ_z P(z|μ) · min { V¹(t+1, prop(post(μ, z)), n−1, a, b) : m(a, b) ≤ w^z }
    promote:    the point ((1, 1), P¹(t, n, μ)).

The hull is two-dimensional because π and κ are shared across the two pending values, so the two budgets can only
be mixed jointly. The no-query and query branches are separable sums over z. Answer: V⁰(1, β_1, B, α). Terminal
values are 0.

Indexing (corrected 2026-11-13; the first draft applied prop once in the no-query line, which the builder caught):
μ is the belief about S_{t−1}. post(μ, z) conditions it on the pending label, one prop gives the belief about S_t
(the lagged belief of the next pending state), two give the belief about S_{t+1} (the current belief of the next
no-pending state).

## 4. Expected differences from d = 1

- The risk state is two-dimensional in pending states, so the tables are (N + 1)² per belief point.
- The dyadic-lattice argument of Theorem 2 does not transfer: a facet of a two-dimensional hull can meet the
  diagonal a = b at a non-dyadic point. Whether some finite lattice is exact is open; the solver uses a uniform
  grid and its U is certified by exact evaluation of the policy.
- General d would need 2^(d−1) budgets per state.

## 5. Results (2026-11-13)

Solver: `src/shiftlab/paper4/risk_budget_dp_d2.py` (Sonnet builder), 49 tests pass. Only an upper bound U is
produced (exact evaluation of the extracted policy; worst-case risk by the null-side recursion of §2). The policy is
executed behaviourally: hull vertices of the same type are merged and their budgets averaged, which keeps risk
within budget because m is convex.

| Check | Result |
|---|---|
| Builder: 130 random cells, T ≤ 7, B ≤ 3, both modes, against the exact reference `gamma_cell(d=2)` | At N = d_α·2^B grid cells (d_α the denominator of α), abs(U − exact) ≤ 9e-16 on every cell. The repo's known cell reproduces 8379231/5000000 (IID) and 523743/312500 (causal) |
| Lead: 36 fresh anti-persistent cells (seed 987654), T 5–7, B 2–3, α ∈ {1/10, 1/5, 1/4}, costs on and off | max abs(U − exact) = 8.9e-16 in both modes; 9 cells have a positive premium (1.2e-3 to 4.3e-2); in those the IID-optimal policy's causal risk is 2α or more (0.2 to 0.5) |
| Coarser grids | Not exact in general: 12 of 130 cells have a gap at N = d_α or 2·d_α (worst 0.053 at N = 5); some non-lattice sizes are exact by accident, others are not |
| Scaling (B = 3, t = 3/4, e = 1/10, causal, uniform belief grid of 401 points, N = 40) | T = 12: 9 s; T = 20: 16 s; T = 32: 25 s. No reference exists at these sizes; risk is exactly α |

**Reading.** The derivation of §2–3 reproduces the certified optimum on all 166 cells tried, including 11 with a
positive premium. Contrary to the expectation in §4, the dyadic grid d_α·2^B was exact on every cell; that is an
empirical observation on cells with T ≤ 7, not a theorem, and the d = 1 proof does not cover it.

**Not done.** No lower bound for d = 2. No brute-force enumeration of null strategies (nothing disagreed with the
reference, so the risk recursion is checked only through the certified optima). No long-horizon premium study at
d = 2. Cost grows with (N + 1)² per belief point, so larger budgets are much more expensive than at d = 1. d ≥ 3 is
not built.

## 6. Long-horizon premium at d = 2 (2026-11-14)

Full tables: `D2_LONG_HORIZON.md` (Sonnet builder); cells in `results/d2_longhorizon_cells.jsonl`. Symmetric chains
t ∈ {2/3, 3/4, 9/10}, e = 1/10, α = 1/10, c = k = 0, prior 1/2, risk grid N = 10·2^B, uniform belief grid of 401
points. 81 cells (B ≤ 3 at T = 8…100; B = 4 at T ≤ 16), all completed.

ρΓ at d = 2, with the d = 1 value of the same cell in brackets:

| t, B | T = 8 | T = 16 | T = 32 | T = 64 | T = 100 |
|---|---|---|---|---|---|
| any t, B = 1 | 0 (0.15–0.33) | 0 | 0 | 0 | 0 (0.10–0.33) |
| 2/3 and 3/4, B = 2 | 0 (0.16–0.20) | 0 | 0 | 0 | 0 (0.14–0.20) |
| 9/10, B = 2 | 0.1355 (0.2692) | 0.0562 (0.1514) | 0 (0.0543) | 0 (0.0527) | 0 (0.0526) |
| 2/3, B = 3 | 0 (0.1543) | 0 | 0 | 0 | 0 (0.1429) |
| 3/4, B = 3 | 0.0426 (0.1956) | 0.0120 (0.1188) | 0 (0.1001) | 0 (0.1000) | 0 (0.1000) |
| 9/10, B = 3 | 0.2375 (0.4714) | 0.1495 (0.2713) | 0.0421 (0.1542) | 0.0399 (0.1489) | 0.0399 (0.1460) |
| 2/3, B = 4 | 0.0176 (0.1666) | 0 (0.1130) | not run | not run | not run |
| 3/4, B = 4 | 0.1381 (0.2852) | 0.0678 (0.1832) | not run | not run | not run |
| 9/10, B = 4 | 0.4262 (0.5434) | 0.2435 (0.3498) | not run | not run | not run |

**What was measured.**

- In every cell the d = 2 premium is smaller than the d = 1 premium of the same cell.
- For B = 1 it is zero at every horizon and chain tried. For B = 2 and 3 it is zero at T ≥ 32 except for
  t = 9/10, B = 3, where it is level at 0.0399 from T = 64 to T = 100 (0.039929, 0.039891).
- Where the premium is zero, the policy extracted in IID mode has causal risk exactly α: IID design costs nothing
  and is safe there. Where it is positive, that policy's causal risk is 2α (2.5α to 2.75α at t = 9/10, B = 4).
- B = 4 was run only to T = 16 and is still falling there; nothing is known about its long-horizon value.
- The causal-mode policy's causal risk is at most α + 5e-17 in all 81 cells; no cell has V_causal < V_IID.

**Lead verification.** The exact reference `gamma_cell(d = 2)` was run on all 27 cells with T ∈ {8, 9, 10},
B ≤ 3 (certified bracket ≤ 4e-14). The nine T = 8 study cells agree with it to 4.4e-16 in both modes, zeros
included. The reference gives Γ = 0 for every B = 1 cell and every t = 2/3 cell at T = 8, 9, 10, and Γ > 0 for
t = 9/10 (B = 2, 3) and t = 3/4 (B = 3), the same pattern as the study. Γ is not monotone in T at these sizes
(t = 9/10, B = 3: 0.0471, 0.0749, 0.0529 at T = 8, 9, 10).

**Interpretation (lead; not proved).** A label queried at t is used at t + 2. The two-step chain has eigenvalue
(1 − t01 − t10)² ≥ 0, so it is persistent whatever the one-step chain is: a label 1 is always good news at the
time it arrives. With a single query the learner therefore wants its risk on the label-1 branch, which the causal
constraint w⁰ ≤ w' never blocks. At d = 1 in an anti-persistent chain a label 0 is the good news, and that is
exactly the branch the causal null caps. A premium at d = 2 needs at least two queries whose labels interact.

**Caveats.** Values at T ≥ 11 are costs of feasible policies with no lower bound and no exact reference, so a
zero there says the two solver runs found the same cost, with the causal run feasible; it is certified only up to
T = 10. Belief-grid error at T ≥ 64 is up to 3e-5 in V and about 1e-5 in ρΓ (401 vs 801 points); zeros were
unchanged. The exact-belief grid fails at long horizons for several chains (`belief outside the active set`, cause
not investigated). Symmetric chains, one e, one α, no costs.

**Grid refinement (lead, 2026-11-14).** Six cells (B = 1 at T = 32, 64; B = 2 at T = 16, 32; all three chains
represented), both modes, rerun with the risk grid three times finer (N = 30·2^B): U changes by at most 3.2e-13,
and every zero premium stays zero. This is the d = 2 analogue of stress test S2 and supports, without proving,
that the grid d_α·2^B is exact at these horizons too.

## 7. B = 4 to T = 100, and the memory fix (2026-11-16)

The first attempts at B = 4, T ≥ 24 ran several solves in parallel and exhausted the machine's memory (16 GB): the
solver kept one pending-state table of 401 × 161² floats (83 MB) per time step and budget level. Two changes:
`RBDP2Config.table_dir` (off by default) stores those tables as memory-mapped `.npy` files, and the runner aborts
any solve whose footprint passes a cap (`D2_MEM_CAP_GB`, default 5). On a B = 3, T = 24 cell the in-memory and
on-disk runs give bit-identical U and risk in both modes, with peak footprint 1.87 GB against 0.08 GB. The cells
at T ≥ 48 and (9/10, T = 32) were run one at a time with tables on disk; peak footprint ≤ 0.50 GB. This
supersedes the "not run" entries for B = 4 in §6.

ρΓ at d = 2, B = 4 (d = 1 value of the same cell in brackets); same chains and grids as §6:

| t | T = 16 | T = 24 | T = 32 | T = 48 | T = 64 | T = 100 |
|---|---|---|---|---|---|---|
| 2/3 | 0 (0.1130) | 0 (0.1113) | 0 (0.1111) | 0 (0.1111) | 0 (0.1111) | 0 (0.1111) |
| 3/4 | 0.0678 (0.1832) | 0.0399 (0.1499) | 0.0350 (0.1414) | 0.0332 (0.1383) | 0.0331 (0.1380) | 0.0331 (0.1379) |
| 9/10 | 0.2435 (0.3498) | 0.1540 (0.2548) | 0.1296 (0.2326) | 0.1240 (0.2241) | 0.1231 (0.2227) | 0.1229 (0.2218) |

- t = 3/4 and t = 9/10 level off at a positive premium: 0.03307, 0.03305 and 0.12306, 0.12288 at T = 64, 100.
  With §6 this gives three (t, B) series with a positive long-horizon premium at d = 2: (9/10, 3) at 0.0399,
  (3/4, 4) at 0.0331 and (9/10, 4) at 0.1229. At d = 2 the long-horizon premium rises with B in these chains
  (t = 9/10: 0, 0, 0.040, 0.123 for B = 1…4; t = 3/4: 0, 0, 0, 0.033).
- t = 2/3 is zero from T = 16 on.
- Where the premium is positive at T ≥ 32 the IID-mode policy's causal risk is 2α; the causal-mode policy is at α
  (deviation ≤ 3e-17) in all 24 B = 4 cells.
- Same caveats as §6: T ≥ 11 values are costs of feasible policies with no lower bound; the uniform belief grid of
  401 points was not rechecked at 801 for B = 4; B ≥ 5 is not run (tables grow as 4^B).

## 8. Review notes (2026-11-16)

The independent review (`PROOF_REVIEW.md`) judged §1–4 sound but incomplete as a proof: the risk recursion with a
pending label was confirmed by brute force over up to 65,536 deterministic nulls on 44 random policies (equal in all
44; nulls see the pending label), and the pair of budgets, the 2-D hull and the lagged-belief indexing were found
consistent. Missing for a proof: joint convexity of the value in (w⁰, w¹), the monotonicity that lets the budget
constraint be an equality, the post-promotion value P¹ and edge cases. Lattice exactness at d = 2 remains empirical.
The review did not cover §5–7 (the solver, long-horizon numbers or memory fix) and built no independent d = 2 optimum.
