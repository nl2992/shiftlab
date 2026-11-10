# 01 — Structural theorem audit (Paper 4, antitone-frontier directive)

**Date:** 2026-11-09. **Branch:** `research/paper4-antitone-frontier-2026-11-09` (base `f8878053`,
which carries the full `research/risk-preserving-switching-approx-2026-10-29` history; `origin/main` at
`8af33afe`). Status labels: PROVED, NUMERICALLY VERIFIED, PRIOR ART, FALSIFIED, UNRESOLVED.

## 1. Setting

The setting is the two-law switching game of `docs/switching_problem_v1.md`, with the exact first-promotion
decomposition of `docs/switching_first_promotion_decomposition_v1.md`. The learner's realization plan `x`
lives on the full public pre-promotion history tree. The tree is unrestricted, so guarantees are against
the unrestricted optimum `V*`. The causal null `nu` picks `p_t in [0, 1/2]` after seeing the full generated
history, including pending labels and public actions.

## 2. The risk identity (directive §8–9)

**Recursion.** For a deterministic promotion event `g` on the complete potential tape, define
`v(h) = max_{p in [0,1/2]} [(1-p) v(h0) + p v(h1)] = max{v(h0), (v(h0)+v(h1))/2}`. This is linear in `p`,
so endpoints suffice. Terminal: `v(y) = g(y)`. **PROVED.**

**Identity.** `R_causal - R_IID = sum_t 2^-t sum_{|h|=t-1} [v(h0)-v(h1)]_+`. **PROVED** by
subtracting the fair recursion and telescoping.

**Exhaustive check.** `scripts/research_risk_approx/check_negative_influence_identity.py` uses exact
`Fraction` arithmetic over all 276 Boolean events at `T = 1,2,3`, and finds three-way agreement between
(i) the recursion, (ii) brute force over every endpoint strategy (`2^(2^T - 1)` strategies), and
(iii) fair risk plus premium. There are zero failures. Further results from the same run:
- The monotone hull is exact in 4/4, 16/16 and 248/256 events. The largest gap is 1/8, at `{010,101}`
  (IID 1/4, causal 1/2, hull 5/8).
- Monotone events have zero premium, the all-0 and all-1 events are trivially covered, and a never-querying
  policy has `v(h0) = v(h1)` at unqueried bits.

**NUMERICALLY VERIFIED.**

**Randomisation.** The two-branch example has true robust risk 3/4, against 1/2 from the marginal promotion
map. Averaging over private randomisation is therefore **FALSIFIED** as a certificate. The sequence-form /
behavioural treatment, where the null conditions on public actions, is exact: see §4, Lemma 1.

**Prior-art status: PRIOR ART.** The recursion is the extreme-point best response of Krale et al.
(NeurIPS 2025), Theorem 3, on their nature MDP (Definition 3). The full mapping is in
`docs/risk_preserving_approx/PAPER4_G1_NOVELTY_REDUCTION_V1.md`. The identity is algebra on that value.

## 3. WP1.1 — structural parameters for the risk verifier

| Candidate parameter | Already known? | Cheap before the full tree? | Small for switching policies? | Implies faster optimisation? |
|---|---|---|---|---|
| Reduced-OBDD width of the promotion event (event order) | Yes. These are residual-subfunction / Myhill–Nerode classes (Rabin–Scott; Bryant OBDDs) | Only once the policy is fixed | For a fixed finite-state controller: at most controller states × pending queue × budget, i.e. Krale's nature-MDP product | **No**, see below |
| Number of inversion-frontier nodes | Bounded by the width above | Same | Same | No |
| Distinct risk-continuation values | Coarser than the width | Only after evaluation | Same | No |
| Universal null-response quotient | Lower bound `binom(T-2, q)` (Candidate C) | — | Exponential for central `q` | Not applicable |

**Decisive measurement (from existing artifacts, no new run).** The exact robust verifier for the returned
policy already uses **56 product states** (T=8, B=4: `iid_relaxation_certified_pipeline_v1.json`) and
**72** (T=10, B=4, d=2: `iid_relaxation_t10_stress_v1.json`). Meanwhile the learner LP has 3,869 and 13,421
variables, and the reference also carries 4,973 and 13,791 opponent sequences. Verification is not the
bottleneck. A verifier-side structural theorem, however strong, has almost no end-to-end leverage
(Amdahl).

**WP1 decision for the verifier-centred theorem: FAIL / PRIOR ART.** The identity, the BDD or
nature-MDP verifier, and any width parameter on it are excluded by directive §15 ("restating the
robust Bellman recursion / negative-influence decomposition", "representing a Boolean event as a BDD").

## 4. PIVOT — Frontier-Cut Generation (FCG)

The leverage is on the **null side of the optimisation LP**, not in verifying a single policy. The reference
encodes every null response as sequence-form variables. FCG encodes only the null strategies that bind.

**Lemma 1 (linearity).** Fix a pure null strategy `nu`. Then the first-promotion probability equals
`r_nu · x`, where `r_nu(sigma)` sums, over generated outcome paths consistent with `sigma`, the product of
`nu`'s queried-outcome probabilities. This holds for first-promotion sequences `sigma` of the decomposed
game, where promotion is a leaf for risk accounting.
*Proof.* This is the standard sequence-form reach factorisation (learner realization × null realization).
It uses perfect recall of the learner's public tree. **PROVED.**

**Lemma 2 (finite extreme set).** `R_causal(x) = sup_nu r_nu · x = max_{nu in N_ext} r_nu · x`, where
`N_ext` is the finite set of deterministic `{0, 1/2}`-valued null strategies.
*Proof.* For a fixed behavioural learner policy, whose actions are public, the null faces a finite-horizon
MDP over generated histories. Its value is linear in `p` at each node, so a deterministic endpoint policy is
optimal. This is the recursion of `CausalSwitchingGame.null_risk`. Private learner coins are covered,
because a root mixture's realization plan is the convex combination and the null sees only public actions,
as in Kuhn's theorem. **PROVED.**
*Threat-model caveat.* This is the ShiftLab null: it sees public actions and every generated outcome,
including pending ones, but **not** the learner's private randomness. Krale et al.'s nature also sees the agent's
memory. Against a coin-seeing null, Lemma 2 fails for randomised `x`: the supremum is no longer linear over a
fixed set of rows, and the problem becomes combinatorial. The extreme-point reduction is borrowed from Krale
only for a fixed, observed behaviour.

**Theorem (FCG correctness).** Let `P_K` be the LP restricted to the rows `nu in K ⊆ N_ext`, with
`IID ∈ K`, and let `x_K` be its solution.
1. `L_K <= V*`, provided `L_K` is a valid dual bound for `P_K`. The rationalised dual with an exact
   reduced-cost correction gives this, using `0 <= x <= 1`.
2. Let `q = min(1, alpha / R_causal(x_K))` and form the root mixture with never-promote. Then
   `U_K = C_alt(mixture) >= V*` and `R_causal(mixture) = q R_causal(x_K) <= alpha`.
3. If `R_causal(x_K) > alpha`, the best response `nu*` is not in `K` and `r_nu* · x_K > alpha`. The new
   row therefore strictly cuts `x_K`, and the loop ends after at most `|N_ext|` iterations.
4. At termination `x_K` is robust-feasible, so `U = L = V*` up to LP tolerance.

*Proof.*
1. Lemma 2 shows the robust feasible set is `∩_{N_ext}`, so `P_K` is a relaxation. Weak duality holds
   with the bounded-variable correction.
2. The repaired policy is feasible. The risk of the root mixture is linear in the realization plan, and
   never-promote has risk 0.
3. `x_K` satisfies every row in `K`, so the violated row is new.
4. A feasible point of the full problem is optimal for the relaxation.

**PROVED** for the finite game.

**What is not claimed.**
- `|N_ext| = 2^(#null decision nodes)`, so the worst-case iteration count is exponential. No polynomial bound.
- Each LP still has the full learner tree. Savings can only come from replacing opponent sequences and null
  flow rows (13,790 at T=10) with `|K|` rows.
- On all registered persistent cells the IID optimum is already safe (activation 1), so FCG stops at zero
  cuts and coincides with the existing Candidate B pipeline. It can show anything only where the IID
  optimum is unsafe, for example in anti-persistent (reversal) regimes.

**Prior-art boundary.** FCG is constraint generation (a cutting-set / single-oracle scheme). This is the
sequence-form double-oracle idea of Bošanský et al. (JAIR 2014) and cutting-set robust optimisation
(Mutapcic & Boyd 2009). Both are cited from memory and were *not re-read this session*. The
problem-specific content is:
- the exact separation oracle, whose cut is the inversion-frontier strategy from the product-state best
  response;
- its use inside the two-law certified interval against `V*`.

Under the user's lax standard (2026-11-09) this is a candidate **problem-specific computational
algorithm**, not a new optimisation principle. **UNRESOLVED** pending the development screen.

## 5. Counterexample coverage (WP1.3)

| Attack | Where | Effect on FCG |
|---|---|---|
| Posterior aliasing | `docs/switching_alt_belief_risk_alias_counterexample_v1.md` | None. FCG keeps the full public tree and never merges histories |
| Hidden pending outcomes | Null strategy keyed by full outcomes (Lemma 1) | Preserved |
| Nonmonotone promotion | §2 example, `docs/switching_monotone_class_separation_v1.md` | Valid. No monotonicity is used |
| Randomisation leakage | §2 counterexample (3/4 vs 1/2) | Handled exactly via Lemma 2 (behavioural / Kuhn) |
| Universal quotient blow-up | Candidate C | Not used. FCG generates strategies, not quotient states |
| Weak lower bound | IID relaxation can be loose when the IID optimum is unsafe | This is exactly what the cuts tighten; measured in the dev screen |

## 6. Decision at this checkpoint

- Verifier-centred antitone theorem: **STOP (prior art + no leverage).**
- FCG: **CONTINUE** to the registered development screen `docs/paper4/experiments/protocols/FCG_DEV_PROTOCOL_V1.md`,
  with lax gates.
