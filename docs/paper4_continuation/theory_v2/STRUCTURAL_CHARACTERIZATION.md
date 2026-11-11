# WP-D — Structural characterisation of the causal-safety premium Γ

**Author:** lead (Opus 5.5), 2026-11-10. Built only from results that are proved and independently audited in
`THEOREM_PROOF_AUDIT.md`, `REVIEW_S0.md` (and, once returned, `REVIEW_SP1.md`), plus counterexamples re-computed by
the lead. Labels: PROVED (audited), PROVED (unreviewed), NUMERICALLY VERIFIED, FALSIFIED, CONJECTURED.

## 1. The exact reformulation (PROVED; elementary)

Γ = 0 iff the IID-optimal value at level α is attained by a mixture whose worst-case risk over adaptive causal nulls
is ≤ α (Lemma R, remark 3). Two facts make this checkable:
- **Safe class.** Plans whose promotion event is nondecreasing in the labels, either on the label tape or in query
  order, have causal risk equal to IID risk (pathwise coupling; Lemma R′ / Zc). The two classes are incomparable
  (WP-A: 8 plans at (T,B,d) = (4,3,1) are tape- but not z-monotone), so the union is the safe class used.
- **Bound.** 0 ≤ Γ ≤ V_IID(monotone mixtures; α) − V*_IID(α): the premium is at most the IID value lost by
  restricting to monotone events (corollary of the coupling; no standalone novelty).
Monotonicity is **sufficient, not necessary**: 50 of 103 cells flagged with a non-monotone Lagrangian-optimal vertex
still have Γ = 0 (WP-B), because a non-monotone event can still be one the adaptive null cannot inflate.

## 2. The organising quantity: how the alternative ranks label histories

For a plan with a fixed query calendar and a single post-release promotion decision, the Lagrangian problem at
multiplier λ is a Neyman–Pearson problem over label histories y ∈ {0,1}^B (elementary):

  promote on y  ⇔  P_A(y) · G(y) ≥ λ · P_N(y),  with P_N(y) = 2^{−B},

where G(y) is the best continuation gain after y. Write s(y) = P_A(y)G(y)⁺ for the **score**. If s is
coordinatewise nondecreasing, every NP region is an up-set and the event is safe. Γ > 0 needs the optimal region at
level α to fail to be an up-set **in a way the adaptive null can exploit** (it does so by playing p_t = 0 at a
public query time, driving mass onto negative labels). Adaptive query timing and promotion timing enlarge this
picture (they are why Lemma U was hard), but every positive-premium cell found so far is explained by one of four
failures of score monotonicity, each a property of primitives.

| Mechanism | What breaks in s(y) | Primitive cause | Status / witness |
|---|---|---|---|
| **M0 exchangeable evidence** (nothing breaks) | s depends on y only through the count of ones and increases in it | static alternative (exchangeable labels) + MLR | **Γ = 0 PROVED:** S1 (B = 1, any c); **S0** (any T, B, d, k, α, with c = 0; reviewed, minor corrections). c > 0 for B ≥ 2: CONJECTURED (Lemma S+; 0 counterexamples in ≈ 42,000 cells) |
| **M1 sign-reversing evidence** | G(0) > G(1): a negative label predicts a favourable future | anti-persistence ρ = 1 − t01 − t10 < 0, odd release lag | **Γ > 0 PROVED with exact value:** C3″ (deterministic alternation), SP1 (stochastic symmetric, B = 1, any d, c, k): positive iff d odd and costs below g r^d(1 − r) scale; Γ = 0 for even d; decays like r^d |
| **M2 correlated coin** | P_A(Y = 0) > 1/2 makes a negative-label event cheaper per unit IID risk than a positive one | marginal imbalance (condition (M) fails), e.g. non-stationary start | **Γ > 0** at B = 1 (39/32000, CE-8) and B ≥ 2 (9/50000, CE-10; 657/5e6, CE-6); exact at B = 1 via N1 |
| **M3 persistence penalty on isolated flips** | P_A(0101) ≪ P_A(0001) under persistence, so a 0→1 flip that isolates a 1 *lowers* s even though G is ordered | TP2 / persistence with accurate labels, B ≥ 4 | **Γ > 0** even in symmetric stationary cells: α = 25/32 (CE-12) and at practical α down to 21/128 (CE-14: Γ = 1.28e-4 at α = 5/16) |

**Main structural reading.** The conjectured direction "persistence (TP2) ⇒ zero premium" is backwards beyond small
B. TP2 orders the *continuation gain* G (it gives G(1) ≥ G(0)), but it also makes the *likelihood* of a history
sensitive to the arrangement of its labels; once the budget allows histories with isolated flips (B ≥ 4), the
likelihood factor breaks score monotonicity. Exchangeability (the static model) is the property that keeps both
factors ordered, which is exactly where the zero-premium theorems hold.

## 3. Single-label case: an exact characterisation (PROVED, audited)

For B = 1 and α ≤ 1/2, N1 gives Γ = α·κ⁺ with
  κ = 2·max_τ g_z0(τ) − max(0, g_pre, max_τ{2 g_z1(τ), g_z0(τ), g_both(τ)}),
the per-unit-IID-risk advantage of the best negative-label design over the best design the adaptive null cannot
exploit. Condition W (P_1G_1 ≥ P_0G_0) is the sufficient side (Z1; sharpened to W* by WP-A). κ is the interpretable
controlling parameter; SP1 expresses it in primitives for the symmetric anti-persistent family
(κ = min{Ḡ₀/2 − c, Δ, (Δ+k)/2 − c}, Δ = Ḡ₀ − Ḡ₁⁺). α ≤ 1/2 is necessary for N1 (WP-A: fails in 40 cells with
α > 1/2). Γ is linear in α at B = 1; at B ≥ 2 it is not (CE-12: positive at one α only; CE-14: non-monotone in α).

## 4. What is not characterised

- No primitive **necessary and sufficient** condition for Γ = 0 at B ≥ 2. Score monotonicity is sufficient (via the
  safe class) only in the fixed-calendar form; adaptive timing is not covered by a proof outside S0.
- No closed form or bound for Γ at B ≥ 2 beyond identity bounds Γ(1) − [V_c(1) − V_c(B)] ≤ Γ(B) ≤ Γ(1) +
  [V_I(1) − V_I(B)]; Γ is non-monotone in B (CE-17) and in the switching cost (CE-16).
- Mechanisms M2 and M3 are identified from witnesses and the score picture, not proved as general theorems.
- The 4-mechanism table is a taxonomy of every positive cell found, not a theorem that no other mechanism exists.

## 5. Verdict for WP-D

A coherent **qualitative** characterisation exists and is supported by proofs at its two ends (exchangeable ⇒ free;
sign-reversing ⇒ exact positive price), by an exact B = 1 formula, and by verified counterexamples for the two other
mechanisms. It is **not** a unified theorem: the multi-label zero side is proved only for static alternatives with
free labels, and the persistent side turned out to carry a premium. Status: PROVED components + NUMERICALLY
VERIFIED taxonomy; no claim of a general equivalence.
