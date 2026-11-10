# Causal-safety premium Γ = V*_causal − V*_IID (Paper 4, Work Package C)

**Date:** 2026-11-10. **Branch:** `research/paper4-antitone-frontier-2026-11-09` (base `affd5077`), uncommitted.
**Author:** WP C theory agent (Opus), same-family native review only; nothing here has had an external review.
Status labels: PROVED (full proof written below), NUMERICALLY VERIFIED (exact-rational or certified [L,U]
computation on stated instances), CONJECTURED, FALSIFIED.

Scripts: `scripts/paper4_continuation/theory_C/`. Outputs (JSON, refuse-overwrite): `docs/paper4_continuation/theory_C/`.
Reproduce with `cd scripts/paper4_continuation/theory_C && uv run --no-sync python <script> <out.json> ...`.

## 0. Setting and the computation used

The model is the exact first-promotion decomposed game (`src/shiftlab/dive/first_promotion_decomposition.py`).
- Hidden two-state chain with `P(S_{t+1}=1|S_t=0)=t01` and `P(S_{t+1}=0|S_t=1)=t10`, and `P(S_1=1)=propagate(prior1,1)`.
- Labels are `Y_t ~ Ber(e_{S_t})` with `e0 < 1/2 < e1` (MLR is built into the model class).
- Per-step losses: the incumbent (action 0) pays `q_t = P(Y_t=1)` and the challenger pays `1-q_t`.
- Each step the learner chooses an action and whether to query. A queried label is released `d` steps later.
- Costs and constraints: query cost `c`, switch cost `k` on every action change (`A_0 = 0`), and a hard pathwise budget `B`.
- Risk is the probability of a first promotion (`A_t = 1` for the first time). After a promotion, the continuation is
  the exact belief DP, which may roll back, re-promote and use the remaining budget.

The two problems share the learner class Π_B.
- `V*_IID`: minimise the alternative cost subject to `P_{IID Ber(1/2)}(promote) ≤ α`.
- `V*_causal`: the same objective, subject to `sup_ν P_ν(promote) ≤ α` over every causal null with `p_t ∈ [0,1/2]`.
  The null may depend on the full generated history, including pending labels and public actions, but not on the
  learner's private coins.

IID(1/2) is a member of the causal family, so `Γ := V*_causal − V*_IID ≥ 0`.

**Certified computation** (`gamma_lib.py`). For each cell:
- `L_IID` is the exact rationalised dual bound of the IID LP (FCG iteration 0).
- `U_IID` is the exact cost of the recovered LP policy, root-mixed with never-promote down to exact IID risk ≤ α.
- `[L_causal, U_causal]` comes from FCG-fast, whose final certificate is exact. When the repaired IID optimum is
  already causal-safe, `U_causal ≤ U_IID` and FCG is skipped.
- Γ is then certified to lie in `[L_causal − U_IID, U_causal − L_IID]`. "Γ>0 certified" means `L_causal − U_IID > 0`
  in exact rationals.

Reproduction check: C2 Γ = 0.0416704, C3 Γ = 0.01177125 and C1 Γ = 0 all agree with
`docs/paper4/experiments/results/fcg_dev_v1.json` (CE-5).

**Alternative optimal vertices.** Every Γ = 0 statement below is a statement about *values*: `U_causal − L_IID ≤ 3e-15`.
None of them depends on which LP vertex HiGHS returned. Every Γ > 0 statement uses `L_causal − U_IID`, which is
vertex-independent.

---

## 1. Lemma R (Lagrangian reduction) — PROVED

Let `P` be the finite set of pure (deterministic) pre-promotion plans of the decomposed game. Let `M ⊆ P` be the plans
whose promotion event `g(y_1..y_T)` on the full potential label tape is coordinatewise nondecreasing. Never-promote
belongs to `M`. Write `C(π)` for the alternative cost and `R(π)` for the IID risk.

**Lemma R.** Suppose that for every `λ ≥ 0`, `min_{π∈P} [C(π) + λR(π)] = min_{π∈M} [C(π) + λR(π)]`. Then `Γ = 0`.

*Proof.*
1. **Mixtures.** By Kuhn's theorem (perfect recall of the public learner tree), every realization plan is a mixture of
   pure plans, and `C` and `R` are linear in the mixture. Therefore `V*_IID = min{E_μ C : E_μ R ≤ α, μ ∈ Δ(P)}`, and
   likewise `V_IID(M)` over `Δ(M)`.
2. **Duality.** Both are finite LPs with one inequality, and never-promote is feasible with risk 0. Strong duality
   gives `V_IID(S) = max_{λ≥0} [min_{π∈S}(C+λR) − λα]` for `S ∈ {P, M}`. The hypothesis says the two dual functions
   coincide, so `V_IID(M) = V*_IID`.
3. **Causal risk of monotone mixtures.** Take any mixture μ supported on `M` and any causal null ν, and couple the null
   tape `Y_t = 1{U_t ≤ p_t}` with `Y*_t = 1{U_t ≤ 1/2}`. This is the coupling of
   `docs/switching_monotone_promotion_reduction_v1.md`, and it holds pathwise for any adapted `p_t`, including `p_t`
   that react to public actions revealing which plan was drawn. Monotonicity gives `g_π(Y) ≤ g_π(Y*)`, so
   `P_ν(promote) ≤ R(μ)`.
4. **Conclusion.** The IID-optimal mixture over `M` is causal-feasible. Hence
   `V*_IID ≤ V*_causal ≤ V_IID(M) = V*_IID`. ∎

*Remarks.*
1. Only the dual-function equality matters. It is not enough that the vertex HiGHS returns is monotone, and that is
   not necessary either.
2. A weaker one-λ version holds. At the optimal IID multiplier λ*, suppose `M` contains Lagrangian-optimal plans
   `π⁻, π⁺` with `R(π⁻) ≤ α ≤ R(π⁺)`. Then a mixture of them is IID-optimal and causal-safe.
3. The converse direction is just the definition: Γ = 0 iff some IID-optimal mixture has causal risk ≤ α.

## 2. Target C2 — zero-premium conditions

### 2.1 Theorem Z1 (single label, B = 1) — PROVED

**Theorem Z1.** Let `B = 1`, and let `T`, `d ≥ 1`, `c, k ≥ 0` and `α ∈ [0,1]` be arbitrary. Assume:
- **(TP2)** `t01 + t10 ≤ 1`, i.e. the transition matrix has nonnegative determinant `ρ := 1 − t01 − t10 ≥ 0`;
- **(MLR)** `e1 > e0`, which the model class already enforces;
- **(M)** `P_A(Y_τ = 1) ≥ 1/2` for every query time `τ ≤ T − d`. This is the alternative's marginal at the query time.
  It holds with equality in every symmetric stationary cell (`t01 = t10`, `e0 = 1 − e1`, `prior1 = 1/2`).

Then for every `λ ≥ 0` some Lagrangian-optimal pure plan has a monotone promotion event, and so `Γ = 0` by Lemma R.

*Proof.* Fix a pure plan π.
- **Plans with a constant event.** If π never queries, or promotes at some `s < τ + d` (before its single label is
  released), its promotion event is constant (∅ or everything). Here τ is the deterministic query time, since nothing
  has been observed before τ.
- **Plans that use the label.** Otherwise, after release the plan is an open-loop schedule chosen by the label value
  `y = y_τ`. It promotes at `s_y ∈ {τ+d, …, T} ∪ {∞}`. A simultaneous promote-and-query is a promotion leaf with a
  constant event. The event is `g(y) = 1{s_{y_τ} < ∞}`, which is non-monotone only if `s_0 < ∞ = s_1`.
- **Benefit of promoting.** For `y ∈ {0,1}` and `s ≥ τ+d`, let `G_y(s)` be the expected alternative cost saved by
  "promote at s, then the optimal continuation" over "never promote", conditional on `Y_τ = y`. After the single query
  the budget is 0, so the continuation is open loop. Therefore
  `G_y(s) = max_{a: a_s=1, a_t∈{0,1}} Σ_{t≥s} a_t(2q_t(y) − 1) − k·sw(a)`, where `q_t(y) = e0 + (e1−e0)P(S_t=1|Y_τ=y)`.
  - By MLR, `P(S_τ=1|Y_τ=1) ≥ P(S_τ=1|Y_τ=0)`.
  - Propagation gives `P(S_t=1|y) = π∞ + (P(S_τ=1|y) − π∞)ρ^{t−τ}` with `ρ ≥ 0` by TP2, so `q_t(1) ≥ q_t(0)` for all
    `t ≥ τ`.
  - Each candidate schedule is nondecreasing in `(q_t)` because `a_t ≥ 0`. A max of nondecreasing functions is
    nondecreasing, so **G_1(s) ≥ G_0(s)**.
- **Replacement.** Let π have `s_0 < ∞ = s_1`, and write `K` for the common cost of never promoting after the query.
  Then `C(π) = K − P_0 G_0(s_0)` and `R(π) = 1/2`, where `P_y = P_A(Y_τ = y)`.
  - (a) If `G_0(s_0) ≤ 0`: replace π by the same plan with `s_0 = ∞`. The event is ∅ (monotone), the cost is ≤, and
    the risk is 0 ≤ 1/2. The Lagrangian does not increase because λ ≥ 0.
  - (b) If `G_0(s_0) > 0`: replace π by π′ with `s′_1 = s_0` and `s′_0 = ∞`. The event is `{y_τ = 1}` (monotone) with
    the same IID risk 1/2. Its cost is `K − P_1G_1(s_0)`. Since `G_1 ≥ G_0 > 0` and `P_1 ≥ P_0` by (M),
    `P_1G_1 ≥ P_0G_0`, so `C(π′) ≤ C(π)`.
- **Conclusion.** In both cases the Lagrangian does not increase. Applying this to a Lagrangian-optimal pure plan gives
  a monotone Lagrangian-optimal plan for every λ. ∎

*Where each assumption is used.*
- TP2 is used only to get `G_1 ≥ G_0`.
- (M) is used only to compare the label weights `P_1` and `P_0`. This is the **label-as-correlated-coin** mechanism: a
  label event `{Y_τ = 0}` has IID probability 1/2, but alternative probability `P_0`. When `P_0 > 1/2`, it is a
  cheaper "coin" for the Neyman–Pearson-type Lagrangian than `{Y_τ = 1}`.
- Delay `d`, `c`, `k`, rollback and re-promotion after promotion enter only through `G_y`, which is
  monotone for any of them.

*Necessity checks.*
- **TP2 cannot be dropped.** Theorem C3 below gives `Γ > 0` with `B = 1` and `t01 = t10 = 1`.
- **(M) is sufficient, but its necessity at B = 1 is OPEN.** In 300 random TP2 cells with `B = 1`, 170 of them
  violate (M), yet all have `Γ = 0` (`theory_C/c2_b1_s3.json`). Once (M) fails, the label coin must also beat
  information-free private randomisation and later query times, and the search found no cell where it does.

### 2.2 Multi-label case (B ≥ 2)

**Conjecture Z-gen (TP2 + MLR ⇒ Γ = 0) — FALSIFIED for B = 2.** The counterexample is found by
`c2_search.py`, recorded in `theory_C/c2_asym_persistent_s2.json` and confirmed with exact certificates.

| Cell | Parameters | Γ (exact) |
|---|---|---|
| CE-C2a | T=4, B=2, d=2, t01=2/5, t10=1/20 (ρ = 11/20 > 0), e=(1/10, 3/5), prior1=0, c=k=0, α=1/10 | `V*_IID = 8379231/5000000`, `V*_causal = 523743/312500`, `Γ = 657/5000000 = 1.314e-4` (`L = U` on both sides) |
| CE-C2b | T=5, B=2, d=2, t01=1/2, t10=0, e=(1/20, 3/5), prior1=0, c=0, k=1/10, α=1/20 | `Γ ∈ [279/1280000, 2.18e-4]` |

The IID optimum in CE-C2a (`inspect_policy.py 4 2 2 2/5 1/20 1/10 3/5 0 0 0 1/10`) works as follows:
- Query at round 1. At round 2, query again with probability 2/5.
- Promote at round 4 iff `(Y_1, Y_2) = (0, 1)`.
- The event `{Y_1 = 0, Y_2 = 1}` is not monotone. IID risk is 1/10 and causal risk is 1/5, because the null plays
  `p_1 = 0`.

Mechanism: `P_A(Y_1 = 1) = 3/10 < 1/2`. The first label acts as a correlated coin (the alternative puts mass 7/10 on
`Y_1 = 0`) and the second label carries the signal. This is exactly the failure of (M), now with B = 2. Both
counterexamples have `min_t P_A(Y_t=1) < 1/2`.

**Conjecture Z2 (symmetric persistent ⇒ Γ = 0) — NUMERICALLY VERIFIED, unproved.** Hypothesis:
`t01 = t10 ≤ 1/2`, `e0 = 1 − e1`, `prior1 = 1/2`, any `T, B, d, c, k, α`.

- **Evidence.** Γ = 0 in 400/400 random cells with `T ≤ 5`, `B ≤ 3`, `d ∈ {1, 2}`, `c ∈ {0, 1/100, 1/20}`,
  `k ∈ {0, 1/10, 1/2}` and `α ∈ {1/20, 1/10, 1/4}`. The maximum certified `Γ_hi` is 1.5e-15 (`c2_sym_persistent_s1.json`).
  A second seed (`c2_sym_persistent_s11.json`) gives 800/800 more, with max `Γ_hi` 1.8e-15 (§6).
- **Broader conjecture Z3: TP2 + (M) ⇒ Γ = 0.** Γ = 0 in all 365 asymmetric TP2 cells with `B ≥ 2` that satisfy (M)
  (`c2_asym_persistent_s2.json` and `_s12.json`). The evidence is weaker because (M) constrains only marginals, and §2.3 explains why a
  proof needs more.

### 2.3 Unresolved lemma for B ≥ 2 (precise)

What is missing is the multi-label analogue of the replacement step in Z1.

> **Lemma U.** In a symmetric persistent cell, for every λ ≥ 0 and every pure plan π with a non-monotone event, there
> is a pure plan π′ with a monotone event and `C(π′) + λR(π′) ≤ C(π) + λR(π)`.

Why the Z1 swap does not extend:
1. **Adaptive query paths.** The query path depends on released labels, so flipping `y_t` changes which later labels
   are seen. A swap must remap whole sub-trees, not single outcomes.
2. **Fixed-calendar NP form.** With all queries at fixed times and a single promotion decision, the Lagrangian-optimal
   event is `{y : P_A(y)·G(y) ≥ λ2^{−B}}`. Monotonicity requires `P_A(y)G(y)⁺` to be coordinatewise increasing.
   - In symmetric persistent chains, `P_A(001) ≥ P_A(101)`, because flipping an isolated early 0 to 1 lowers the
     likelihood under persistence. Meanwhile `G(001) ≈ G(101)` when mixing is fast.
   - So with `B ≥ 3`, a fixed-calendar *restricted* problem can have a non-monotone NP region. Adaptive plans could
     avoid it, for example by not spending the early query.
   - No cell in the B ≤ 3 search realised this, but nothing in the search rules it out at larger B.
3. **No direct TP2 shortcut.** The Krishnamurthy-style monotone-policy results (MLR-ordered beliefs with TP2 kernels)
   order the *alternative belief*. Here the Lagrangian POMDP has a two-world hidden root, the HMM versus the IID null,
   and the null-world likelihood ratio `2^{−k}/P_A(observed)` is not MLR-monotone in the labels. That is precisely the
   correlated-coin effect. I know of no structural theorem that covers this product of an MLR-ordered belief with a
   non-ordered world posterior (`[unverified: Lovejoy 1987; Krishnamurthy 2016, ch. 10–11, cited from memory, not re-read]`).

**C2 conclusion: GO-theory candidate (narrow).**
- What is PROVED is Lemma R together with Theorem Z1 (B = 1, TP2 + (M)).
- The general "TP2 + MLR" statement is FALSIFIED at B = 2 (CE-C2a). The (M)-type correlated-coin condition is the
  ingredient a correct statement needs.
- The symmetric multi-label case is a well-supported CONJECTURE with a precisely stated missing lemma (Lemma U).
- Γ = 0 at B ≥ 2 is not established by proof.

## 3. Target C3 — a positive-premium family with a proved bound

### 3.1 Theorem C3 (deterministic-alternation family) — PROVED, exact value

**Family.** Set `t01 = t10 = 1`, so `S_{t+1} = 1 − S_t`. Take `e0 = e`, `e1 = 1 − e` with `0 < e < 1/2`,
`prior1 = 1/2`, `B = 1`, `d = 1`, and `T` even with `T ≥ 4`. Write `g := (1−2e)²`. Define

`G_0 := (T/2)(g − 2k) + k` and `G_1 := (T/2 − 1)(g − 2k)`.

Assume `g > 2k`, `g > 3k − 2c`, `c ≤ (g−k)/2`, `G_1 ≥ 2c` and `α ≤ 1/2`.

**Theorem C3.** Under these assumptions:
- `V*_IID = T/2 − α(G_0 − 2c)`;
- `V*_causal = T/2 − α((G_0+G_1)/2 − c)`;
- **Γ = α[(g − k)/2 − c]**, independent of T.

For odd T, Γ = 0 was observed in all 288 odd-T cells checked. That is not part of the theorem.

*Proof.*
- **Base cost.** The chain starts stationary at 1/2 and alternates deterministically. Without information every
  `q_t = 1/2`, so never-promote costs `T/2` and any information-free action sequence has gain `−k·#switches ≤ 0`.
- **What one label reveals.** A label `Y_τ`, released at `τ+1`, predicts `S_t = y_τ ⊕ (t−τ)` for all t, correct with
  probability `1−e`.
  - Following the prediction at a step costs `2e(1−e)`. Going against it costs `1 − 2e(1−e)`.
  - Relative to action 0, being at action 1 gains `+g` at a predicted-1 step and `−g` at a predicted-0 step. Before
    release it gains 0.
- **Branch bound.** Consider any action path in branch y. Each maximal block of 1-actions contains at most one more
  predicted-1 step than predicted-0 steps, because predictions alternate. It pays two switches, or one if it reaches T.
  Hence the gain in branch y is at most `Ĝ_y(τ) := m_y(τ)(g−2k) + k·1[pred_y(T)=1]`, where `m_y(τ)` counts the
  predicted-1 steps in `[τ+1, T]`. This uses `g > 2k`.
  - For `τ = 1` and even T: `Ĝ_0(1) = G_0` and `Ĝ_1(1) = G_1`.
  - For `τ ≥ 2`: `Ĝ_y(τ) ≤ G_1 + k`.
  - For every τ: `Ĝ_0(τ) + Ĝ_1(τ) ≤ (T−τ)(g−2k) + k ≤ G_0 + G_1`.
- **Upper bounds (explicit plans).**
  - IID plan: with probability 2α, query at 1 and follow the prediction from step 2 iff `Y_1 = 0`. It promotes
    immediately at step 2 and covers the steps 2, 4, …, T. IID risk is α, and the alternative gain is `α(G_0 − 2c)`.
  - Causal plan: with probability α, query at 1 and follow in both branches. The event is "always" given activation,
    which is monotone, so causal risk is α. The gain is `α((G_0+G_1)/2 − c)`.
- **Lower bounds (dual certificates on all pure plans).** A pure plan is described by its query time τ, its
  per-branch promotion indicators `z_y`, and branch gains `H_y ≤ z_y Ĝ_y(τ)`. Unconditional promotion and
  post-promotion queries are covered by the D bound below.
  - **IID.** Take multiplier `μ = G_0 − 2c`. Every pure plan has gain ≤ `μ·R_IID`:
    - single-branch plans need `Ĝ_y(τ) ≤ G_0`, which holds;
    - both-branch plans need `((T−τ)(g−2k)+k)/2 − c ≤ G_0 − 2c`, which reduces to `c ≤ (g−k)/2`.
    So `V*_IID ≥ T/2 − α(G_0 − 2c)`.
  - **Causal.** Use two members of the causal family: the IID null with weight `μ_I = G_1 − 2c ≥ 0`, and the null ν′
    with weight `μ_0 = (G_0 − G_1)/2 = (g−k)/2`. ν′ sets `p = 0` at a query made at time 1 and `p = 1/2` at any later
    query; it is a valid causal null because it keys on the public query time.
    - For τ = 1: z₁-only, z₀-only and both-branch plans give `G_1/2 − c ≤ μ_I/2`, `G_0/2 − c ≤ μ_0 + μ_I/2` and
      `(G_0+G_1)/2 − c ≤ μ_0 + μ_I`. All three hold with equality.
    - For τ ≥ 2: both nulls give risk `R_IID`. The conditions become `Ĝ_y(τ) − 2c ≤ μ_0 + μ_I`, which needs
      `G_1 + k ≤ (G_0+G_1)/2 + c`, i.e. `g ≥ 3k − 2c`. The both-branch condition holds by the D bound.
    Weak duality with these two rows gives `V*_causal ≥ T/2 − α(μ_I + μ_0)`, which equals the upper bound.
- **Γ.** Subtracting, `Γ = α[(G_0 − G_1)/2 − c] = α[(g − k)/2 − c]`. ∎

*Mechanism.* With an even horizon, the branch whose first predicted-1 step is immediate (`Y_1 = 0`) also contains the
final step. That branch is worth `g − k` more than the `Y_1 = 1` branch. The IID optimum therefore promotes on the
**negative** label, a non-monotone event. The causal null drives that branch to probability 1 by playing `p_1 = 0`.
For odd T, the more valuable branch is `Y_1 = 1`, and Γ = 0.

**NUMERICALLY VERIFIED.** `c3_alternation_check.py` produced `theory_C/c3_alternation_check_v1.json`.
- Grid: 720 cells with T ∈ {4..8}, e ∈ {1/20, 1/10, 1/5, 3/10}, c ∈ {0, 1/100, 1/50}, k ∈ {0, 1/20, 1/10, 1/4} and
  α ∈ {1/20, 1/10, 1/4}.
- In the 324 cells that meet the assumptions, both closed forms lie inside the certified intervals (324/324 each).
- For odd T, Γ_hi = 0 in all cells.
- The original instance (e = 1/10, c = 1/100, k = 1/10, α = 1/10) gives `Γ = 13/500` at T = 2, 4, …, 10
  (`c3_T_B1_tr1_e1_10.json`).

*Limits.* The bound needs deterministic alternation (`|ρ| = 1`) and `B = 1`. It is linear in α, so Γ/α is the
natural normalised premium. It does not grow with T: the family is "Γ bounded away from 0 uniformly in T", not
"Γ growing in T".

### 3.2 Horizon structure of the registered anti-persistent families (coordinator query)

**Lemma H (prepend-idle) — PROVED.** Suppose the chain starts stationary (`propagate(prior1, 1) = π∞`). Write
`q̄ = e0 + (e1−e0)π∞`, so `q̄ = 1/2` in symmetric cells. Then, for both problems X ∈ {IID, causal},
`V*_X(T+1) ≤ V*_X(T) + q̄`.

*Proof.* Let a horizon-(T+1) learner idle at step 1 (action 0, no query), then run any horizon-T policy
on steps 2…T+1. `S_2` has the law π∞, the chain is homogeneous, and release times shift with the policy.
- The idle step costs exactly q̄.
- Nulls act only at queries, so for every null the promotion probability equals that of the unshifted policy; both risk
  constraints carry over unchanged.
- `A_1 = 0` adds no switch.
∎

*Corollary.* If `V*_IID(T+1) = V*_IID(T) + q̄`, then `Γ(T+1) ≤ Γ(T)`.

**Data** (`c3_T_family.py`; certified, U = L to 1e-12):

| Family | T | V*_IID | V*_causal | Γ |
|---|---|---|---|---|
| C6-type: B=3, d=1, tr=3/4, e=1/20 | 4 | 779063/400000 | 19613/10000 | 0.0136425 |
| | 5 | 1957803/800000 | 7871791/3200000 | 0.0126809375 |
| | 6 | 2357803/800000 | 118361/40000 | 0.01177125 |
| | 7 | 2757803/800000 | 34589/10000 | **9317/800000 = 0.01164625** |
| | 8 | 3157803/800000 | 39589/10000 | 9317/800000 |
| | 9 | 3557803/800000 | 44589/10000 | 9317/800000 |
| C2-type: B=2, d=1, tr=9/10, e=1/10 | 5…10 | (see JSON) | (see JSON) | 0.04167, 0.03488, 0.03600, 0.03257, 0.02946, 0.02871 |

*Answer to the coordinator.*
- **(i) Γ is not T-invariant in general.**
  - In the C6-type family, both values rise by exactly 1/2 per step from T = 7 (`V*_IID` already from T = 6), so Γ is
    constant at `9317/800000` for T = 7, 8, 9.
  - T = 10 was not run here. The coordinator's T10D1 `V*_causal = 49589/10000` is consistent with this, and predicts
    `V*_IID(10) = 3957803/800000` and the same Γ.
  - In the C2-type family, `V*_IID` rises by 1/2 per step from T = 8, but `V*_causal` rises by less than 1/2. Γ is
    strictly decreasing over T = 8, 9, 10: 0.032567, 0.029459, 0.028712. The causal learner keeps profiting from a
    longer horizon.
- **(ii) Where the +1/2 per step comes from.**
  - Lemma H explains the `≤` direction: an idle prefix at the stationary symmetric prior costs exactly 1/2 per step,
    because the incumbent's expected loss is `q = 1/2`.
  - Equality, "no gain from a longer horizon", is NUMERICALLY OBSERVED in the C6-type family from T = 7. It is
    unproved. It says the optimal policy can be taken to be an idle prefix followed by a fixed-length active tail.
- **(iii) A family-level C3 statement.** Constancy in this family is not proved. The proved T-invariant family is
  Theorem C3. Lemma H gives only monotone non-increase of Γ once `V*_IID` saturates.

**C3 conclusion: GO-theory candidate.** Theorem C3 is a closed-form, exactly matched Γ, uniform in T, with a clean
mechanism: a parity-driven negative-label coin. Two caveats:
- It is a single-label, deterministic-dynamics family. A reviewer may see it as a hand-built instance rather than a
  structural result.
- It is not a growing-premium family.

## 4. Target C4 — upper bounds on Γ

All four results below are PROVED, except where marked as observed.

1. **Repair bound (trivial).** Let `x_I` be an IID optimum with causal risk `R_c > α`, set `q = α/R_c`, and let
   `C_0` be the cost of never promoting. Then `Γ ≤ (1−q)(C_0 − V*_IID)`. This is root-mixing with never-promote,
   FCG Theorem item 2.
2. **Monotone-restriction bound.** `Γ ≤ V_IID(conv M) − V*_IID`, by step 3 of Lemma R. In Lagrangian form,
   `Γ ≤ max_{λ≥0} [min_M(C+λR) − min_P(C+λR)]`. *Proof:* write `g_S(λ) = min_S(C+λR) − λα`. Then
   `max g_M − max g_P ≤ g_M(λ_M) − g_P(λ_M) = min_M(C+λ_MR) − min_P(C+λ_MR)`. ∎
   So Γ is bounded by the largest Lagrangian gap between monotone and unrestricted pure plans. This turns
   Lemma R into a quantitative statement.
3. **Bound 1 can be loose by a factor Θ(T).** In the Theorem C3 family the IID optimum has `R_c/R_IID = 2`, so q = 1/2.
   Bound 1 is then `α(G_0 − 2c)/2 = Θ(αT)`, while `Γ = Θ(α)`.
4. **Bound 2 is tight on the C3 family** (the causal optimum, follow-always, has a monotone event). It can still be
   loose by a factor 2: in the non-HMM separation example of `docs/switching_monotone_class_separation_v1.md`, the
   monotone class is worth 0 but Γ is half the IID value. Bounds 1 and 2 are incomparable in general.
5. **Nothing sharper, instance-free, is proved.** A natural candidate is `Γ ≤ λ*·(R_c(x_I) − α)`, i.e. multiplier
   times excess risk. It does not follow from convexity of the IID frontier `φ(α)`: the bound one gets from scaling is
   `φ(α/κ) − φ(α)` with `κ = R_c/R_IID`, which reduces to bound 1 whenever φ is linear on `[α/κ, α]`. Status:
   CONJECTURED-false; no attempt beyond this argument.

**C4 conclusion: NO-GO as a standalone result.**
- Bound 1 is trivial, and Bound 2 is a direct corollary of the monotone-coupling lemma in
  `docs/switching_monotone_promotion_reduction_v1.md`.
- The useful content is the comparison: bound 1 is Θ(T)-loose on a proved family, while bound 2 is tight there.

## 5. Target C5 — adaptivity gap under full causal safety

**Classes compared.**
- *Opportunity calendar* `C` (|C| = B), as in `scripts/decompose_switching_calendar_gap.py`. Pre-promotion queries are
  allowed only at the slots in C, and a slot may be skipped. The post-promotion continuation is unrestricted.
- *Portfolio*: a private root lottery over calendars.
- *Adaptive*: the unrestricted class Π_B.

`Δ_X = V_X(best single calendar) − V*_X`, for X ∈ {IID, causal}.

**Data.** Scripts `c5_adaptivity_gap.py` (cell sets `small` and `long`), `c5_portfolio_exact.py` and
`c5_portfolio.py`. Outputs `theory_C/c5_adaptivity_gap_v1.json`, `c5_adaptivity_gap_long_v1.json`,
`c5_portfolio_exact_asym7_v1.json` and `c5_portfolio_asym7_v1.json`. All values are certified to ≤ 3e-15.

| Cells | Δ_IID | Δ_causal | Γ (adaptive) |
|---|---|---|---|
| C1, P_d2, C4, P7 d1/d2, P8 (persistent) | 0 | 0 | 0 |
| C2, C3, A7, A8, alternation T6 B2 (anti-persistent) | 0 | 0 | 0.0417, 0.0118, 0.0130, 0.0057, 0.0533 |
| asym CE-C2a (T=4) | 0 | 0 | 1.31e-4 |
| **asym7: T=7, B=2, d=2, t01=2/5, t10=1/20, e=(1/10, 3/5), prior1=0, c=k=0** | **0** | **5.797e-4** | 5.41e-3 |

**Finding (NUMERICALLY VERIFIED) for the asym7 cell.**
- Δ_IID = 0, but the best single calendar under causal safety is (1, 2), worth `3.246092847375`.
- The adaptive causal optimum is `25964105379/8000000000 = 3.245513172375`.
- A **private portfolio** of calendars attains *exactly* the adaptive value (LP + exact verification + exact cost,
  `c5_portfolio_exact_asym7_v1.json`). Its weights are (1,2): 1/5, (1,3): 1/5 and (2,7): 3/5, and the (2,7) component
  never promotes.
- The certified causal optimum (`inspect_causal_policy.py 7 2 2 2/5 1/20 1/10 3/5 0 0 0 1/10`) shows the mechanism:
  - Query at 1. Then, by a private coin at round 2, either query at 2 and promote at 4 iff `Y_1 = Y_2 = 1`, or wait
    and, if `Y_1 = 0`, query at 3 and promote at 5 iff `Y_3 = 1`.
  - The two components want opposite null moves at the shared query node 1: `p_1 = 1/2` against the first,
    `p_1 = 0` against the second.
  - The null must commit `p_1` before the learner's coin is visible in public actions, so the mixture's risk is
    strictly below the sum of the components' risks.
  - The portfolio LP with additive risk (`c5_portfolio.py`, which ignores this hedge) does *not* close the gap. That
    confirms the hedge is the source of the value.

**Reduction (PROVED).** The causal problem over a portfolio of calendar classes `{Π_C}` is the FCG LP over
`x = Σ_C x_C` with `x_C ∈ w_C·Flow(Π_C)`. Every such `x` is a realization plan of Π_B, so
`V*_causal ≤ V_causal(portfolio) ≤ V_causal(best single calendar)`. Risk is `max_ν r_ν·x`, a convex function of `x`
(Lemma 2 of `docs/paper4/theory/01_structural_theorem_audit.md`). That makes risk subadditive over portfolio
components, while IID risk is additive. The single-calendar gap `Δ_causal > Δ_IID = 0` is therefore exactly the value
of private randomisation against an adversary that cannot see the coin: the strict-convexity gap of
`ν ↦ max_ν r_ν·x`. It is not information-adaptive design.

**C5 conclusion: NO-GO (not new).**
- No cell showed a gap between the private calendar portfolio and the adaptive class, under either IID or causal
  safety. This was checked exactly only in the asym7 cell; in every other cell the single-calendar Δ was already 0.
- The only causal-specific separation found is the value of *mixing* calendars against a committed causal null. That
  is the standard mixed-versus-pure-strategy gap of zero-sum games: Kuhn/von Neumann, and the
  randomisation-leakage line already recorded in audit §2.
- Genuinely label-adaptive timing gaps were not observed at these sizes. Where they exist they are ordinary
  sequential-design adaptivity gaps, e.g. stochastic-probing adaptivity gaps `[unverified citation: Gupta–Nagarajan;
  Asadpour–Nazerzadeh, from memory]`.

## 6. Counterexample-search coverage (C2)

All searches use `c2_search.py OUT SEED N FAMILY [budget]`: random exact cells with `T ∈ {3,4,5}`, `B ≤ min(3,T)`,
`d ∈ {1,2}`, `c ∈ {0, 1/100, 1/20}`, `k ∈ {0, 1/10, 1/2}` and `α ∈ {1/20, 1/10, 1/4}`. The `b1` family uses
`T ≤ 6, B = 1`. Γ>0 counts are cells with certified `L_causal − U_IID > 0`.

| Family | File | Cells | Γ > 0 | max Γ_hi otherwise | Notes |
|---|---|---|---|---|---|
| symmetric persistent | `c2_sym_persistent_s1.json`, `_s11.json` | 400 + 800 | 0 | 1.8e-15 | 803 cells with B ≥ 2, 387 with B = 3, 582 with d = 2 |
| asymmetric TP2 (t01+t10 ≤ 1, any prior/emissions) | `c2_asym_persistent_s2.json`, `_s12.json` | 400 + 800 | 2 (CE-C2a, CE-C2b) | 4.9e-14 | 365 cells with B ≥ 2 satisfy (M): all Γ = 0; both Γ > 0 cells violate (M) |
| B = 1 TP2 | `c2_b1_s3.json` | 300 | 0 | 2.8e-15 | 170 cells violate (M): Theorem Z1's (M) is not shown necessary |
| anti-persistent (TP2 fails) | registered C2/C3/C6, `c3_*` | — | yes | — | Theorem C3 with B = 1 |

The searches ran 0 errors. The counterexample density is low: 2/1200 in asymmetric TP2 cells, with Γ ≈ 1e-4.
Small premiums of this size are why the registered persistent cells all show Γ = 0.

## 7. Source comparison (what is and is not known)

- **Monotone-event coupling.** `docs/switching_monotone_promotion_reduction_v1.md` is repo-internal. It is
  first-order stochastic dominance under a pointwise coupling, standard in robust testing.
- **Lagrangian/CMDP reduction.** One constraint gives a mixture of at most two Lagrangian-optimal deterministic
  policies; this is standard in constrained MDPs (Altman 1999, *Constrained Markov Decision Processes*, from memory).
  Lemma R's use of it, to transfer monotone *events* through the dual function, is a short new composition. It is not a
  new principle.
- **MLR/TP2 monotone POMDP policies.** Lovejoy (1987, Operations Research) and Krishnamurthy (2016, *Partially Observed
  Markov Decision Processes*, chs. 10–12) are cited from memory and were not re-read in this session. These results
  order beliefs over the hidden state. The two-world Lagrangian POMDP here has a world posterior that is not
  MLR-monotone in labels (§2.3), which is exactly why CE-C2a exists. I am not aware of a published monotone-policy
  theorem covering it `[unverified]`.
- **Neyman–Pearson view.** For a fixed calendar and a single decision, the IID-constrained Lagrangian optimum is the
  likelihood-ratio-type test `{P_A(y)G(y) ≥ λ2^{−B}}` (NP lemma with a payoff weight). The correlated-coin mechanism is
  the observation that this region is an upper set only if `P_A(y)G(y)⁺` is coordinatewise increasing. That is
  textbook NP. Its interaction with the causal null is what is problem-specific.
- **Randomisation versus a committed adversary (C5).** This is the minimax/mixed-strategy value; see Kuhn (1953) for
  behavioural strategies under perfect recall.

## 8. Per-target conclusions

| Target | Status | Strongest surviving statement | Verdict |
|---|---|---|---|
| C2 zero premium | Lemma R PROVED. Z1 PROVED (B = 1). "TP2+MLR ⇒ Γ=0" FALSIFIED (B = 2, CE-C2a). Symmetric multi-label NUMERICALLY VERIFIED (1200 cells), unproved (Lemma U open) | Theorem Z1 (§2.1) | GO-theory candidate (narrow); the multi-label case needs Lemma U |
| C3 positive premium | PROVED, closed form, verified 324/324 | Theorem C3: Γ = α[(g−k)/2 − c] for all even T ≥ 4 | GO-theory candidate (bounded, not growing in T; hand-built family) |
| C4 upper bound | Two bounds PROVED; repair bound shown Θ(T)-loose; monotone bound tight on the C3 family | `Γ ≤ max_λ [min_M(C+λR) − min_P(C+λR)]` | NO-GO standalone (corollary of existing coupling) |
| C5 adaptivity gap | Gap found only for single calendars under causal safety; closed exactly by a private portfolio (one cell) | Single-calendar causal gap = private-randomisation hedge | NO-GO (standard mixed-strategy value) |

**Continue / pivot / stop.**
- *Continue*, only if Paper 4 wants a characterisation paragraph: Lemma R, Theorem Z1, Theorem C3 and CE-C2a together
  explain *why* Γ = 0 on the registered persistent cells and Γ > 0 on the reversal cells. The correlated-coin mechanism
  and the parity mechanism of C3 cover them.
- *Stop* pursuing a general primitive zero-premium theorem unless Lemma U is resolved. It is a genuine structural-POMDP
  question with a two-world posterior. Exact search finds no counterexample, but there is no proof route.

---

## § Follow-up: Lemma U and necessity (2026-11-10, appended; earlier sections unchanged)

This section answers the two items the idea-evaluator gated on, plus the coordinator's static-alternative query.
It adopts the corrections in `CAUSAL_SAFETY_PREMIUM_REVIEW_CORRECTIONS.md`:
- Z1 holds under the weaker condition **(W)**: `P_1(τ)G_1(τ,s) ≥ P_0(τ)G_0(τ,s)` whenever `G_0 > 0`, for all
  `τ ≤ T−d` and `s ≥ τ+d`. TP2 + (M) ⇒ W.
- "TP2 + MLR ⇒ Γ = 0" already fails at B = 1.
- Theorem C3 now reads `Γ = α·min{(g−k)/2 − c, g − 2k}`.
- The (M) check in `c2_search.py` used `t ≤ T`.
Lemma U is framed below as a **multi-label analogue of W**.
Scripts are in `scripts/paper4_continuation/theory_C/fu_*.py`. Outputs are in
`docs/paper4_continuation/theory_C/fu_*.json` (refuse-overwrite). The aggregate is `fu_summary_v1.json`, produced by
`fu_summarize.py`. Total compute was about 35 CPU-minutes, and every job took under 6 minutes.

### F1. Lemma Zc (query-order coupling) — PROVED

Let `z_j` be the label of the j-th query a deterministic plan makes, in query order. Because the delay is fixed,
release order equals query order. The plan's promotion indicator is then a function `g̃(z_1..z_B)`.

**Lemma Zc.** If `g̃` is coordinatewise nondecreasing, the plan's causal risk equals its IID risk. The same holds for
any root mixture of such plans, and of tape-monotone plans.

*Proof.* Draw `U_1, U_2, … ~ Unif[0,1]` indexed by query order. Under a causal null, set `Z_j = 1{U_j ≤ p_j}`, where
`p_j ≤ 1/2` is the null's choice at the j-th query given everything generated so far. Run the same plan on
`Z*_j = 1{U_j ≤ 1/2}`. That run has exactly the IID(1/2) law, because labels at distinct times are i.i.d. under the
IID null whatever the query times. The two runs may query at different times, but the j-th coordinates always satisfy
`Z_j ≤ Z*_j`. Monotonicity then gives `g̃(Z) ≤ g̃(Z*)` pathwise. Averaging over plans covers mixtures, since a causal
null restricted to one plan's histories is still a causal null. ∎

**Consequences.**
- **Lemma R′.** Lemma R holds with `M` replaced by `M_z ∪ M_tape`.
- **Strictness (NUMERICALLY VERIFIED,** `fu_zcoupling_check.py` → `fu_zcoupling_check_v1.json`). All reachable pure
  plans of `(T,B,d) ∈ {(3,2,1), (3,2,2), (4,2,1), (3,3,1)}` were enumerated, 1,233 plans in all.
  - Every tape-monotone plan was z-monotone.
  - Four plans at (4,2,1) are z-monotone but not tape-monotone.
  - No z-monotone plan has `R_causal ≠ R_IID`.

### F2. Lemma P (promotions only where the next label favours promotion) — PROVED, any model

For every λ ≥ 0, some Lagrangian-optimal pure plan promotes only at information states h with
`q(h) := P_A(Y_t = 1 | h) > 1/2`.

*Proof.* Suppose a plan promotes at s with continuation σ, and `q(h_s) ≤ 1/2`. Replace step s by `(0, same query)` and
follow σ's actions from s+1 on. The information is identical, so this is a valid plan.
- **Cost.** Step s costs `q ≤ 1−q`. Switching costs are equal if σ keeps action 1 at s+1, and are 2k lower if σ
  returns to 0 (k lower if s = T).
- **Risk.** The new promotion event is contained in the old one.
- **Conclusion.** The Lagrangian does not increase. Repeat until no promotion occurs at a state with q ≤ 1/2. The
  process terminates because each step strictly delays a promotion.
∎

### F3. Exhaustive TP2 grid (item 1) — NUMERICALLY VERIFIED

**Grid** (`fu_lemmaU_grid.py`; files `fu_lemmaU_T{3,4,5}_B{2,3}.json` and `fu_lemmaU_T6_B{2,3}_d{1,2}.json`).
- `T ∈ {3,4,5,6}`, `B ∈ {2,3}`, `d ∈ {1,2}`.
- 12 TP2 transition pairs: three symmetric (1/10, 1/4, 1/2), seven asymmetric with `t01 + t10 ≤ 1` and two drifting
  ones with an absorbing state (`(0,1/2)`, `(1/2,0)`), plus the **static** pair (0,0).
- Emissions: (1/10, 9/10), (1/10, 3/5) and (2/5, 9/10).
- `prior1 ∈ {0, 1/2, stationary}`; static cells use `{0, 1/2, 1/4}`.
- `c, k ∈ {0, 1/100, 1/10}` and `α ∈ {1/20, 1/10}`.
- This gives **27,648 cells**, with 0 errors and no cell skipped for time.

**Two multi-label versions of (M) were checked:**
- `M_marg`: `min_{t ≤ T−d} P_A(Y_t=1) ≥ 1/2`, which is Z1's (M).
- `M_cond`: `P_A(Y_t=1 | Y_S = y_S) ≥ 1/2` for every `t ≤ T−d`, every `S ⊆ {1..t−d}` with `|S| ≤ B−1`, and every
  `y_S` of positive probability. This is the per-query-node analogue.

**Results:**
- **206/27,648 cells have certified Γ > 0. Every one violates `M_marg`, and hence `M_cond`.** Γ = 0 in all 12,060
  cells satisfying `M_marg`, and in all 10,530 satisfying `M_cond`. The maximum `Γ_hi` outside the 206 is 3.4e-14.
- **The 206 positive cells come from only four alternative models:**
  - `(t01, t10, e0, e1, prior1) = (2/5, 1/20, 1/10, 3/5, 0)`;
  - `(1/2, 1/10, 1/10, 3/5, 0)`;
  - `(1/2, 0, 1/10, 3/5, 0)`;
  - `(1/4, 1/4, 1/10, 9/10, 0)`.
  Each starts away from stationarity, with `P_A(Y_1 = 1) ∈ {3/10, 7/20}`.
- **Smallest counterexample:** T=3, B=2, d=1, `t01=1/2`, `t10=1/10`, `e=(1/10, 3/5)`, `prior1=0`, `c=k=0`.
  **Γ = 9/50000 at α = 1/10** and 9/100000 at α = 1/20 (`fu_lemmaU_T3_B2.json`, exact `L = U`). B = 3 gives the same
  values.
- **Largest:** T=6, B=2, d=1, `t01=1/2`, `t10=0`, `e=(1/10, 3/5)`, `prior1=0`, `c=k=0`, α=1/10.
  **Γ ∈ [0.0090499999999994, 0.0090500000000011].**
- **New, and decisive for Z2:** T=6, B=3, d=1 with *symmetric* transitions `t01=t10=1/4` and symmetric emissions
  (1/10, 9/10), but non-stationary `prior1 = 0` (so `P(S_1=1) = 1/4`), `c=k=0`, α=1/10.
  **Γ ∈ [0.00215999999999858, 0.00216000000000204].** Conjecture Z2 therefore genuinely needs the stationary prior. The
  ingredient (M) cannot be traded for symmetry of the transition and emission kernels.
- **Direct check of the Lemma U premise** (`fu_lagrangian_monotone.py` → `fu_lagrangian_monotone_{static,sympersist,mixed}.json`).
  All pure plans were enumerated exactly, and I tested whether every λ ≥ 0 vertex of the lower hull of `{(R_IID, C)}`
  is attained by a z-monotone plan.
  - It is in **374/374 static** and **315/315 symmetric-stationary** unique cells, and also by tape-monotone plans in
    all of them.
  - In the mixed TP2 family it fails exactly in 2/295 unique cells. Both are (M)-violating Γ > 0 models from the list
    above.

**Lemma U as a multi-label W.** Let h be a reachable information state and τ a query time on the path, with
`τ ≤ T − d`. Let `G_y(h,τ,s)` be the open-loop gain of promoting at `s ≥ τ+d` after `Y_τ = y` when no further label
arrives.
- **Multi-label W** is: `P_A(Y_τ=1|h)·G_1 ≥ P_A(Y_τ=0|h)·G_0` whenever `G_0 > 0`.
- It is exactly what makes the Z1 swap valid at the *last* released label of a path.
- `M_cond` + TP2 ⇒ multi-label W, by the Z1 argument conditional on h. `M_cond` and `M_marg` are cheap,
  conservative proxies.
- W itself was not tabulated on this grid. The reviewer tabulated it on B = 1 cells: W held in all 1,126 cells with
  Γ = 0 and failed in all 105 cells with Γ > 0.

**Strongest multi-label statement I can PROVE: none beyond B = 1.** The precise status is below.
- **Conjecture U-M (TP2 + `M_marg` ⇒ Γ = 0, any B, d, c, k, α): NUMERICALLY VERIFIED** on 12,060 grid cells with
  T ≤ 6, B ≤ 3 (no counterexample), plus the earlier 2,000 random cells. Unproved. The intended theorem is
  "multi-label W at every interior label ⇒ Γ = 0".
- **"TP2 + MLR ⇒ Γ = 0": FALSIFIED.** There are 206 cells; the smallest is above.
- **The missing step.** A bottom-up subtree exchange. At the *last* released label of a path, the Z1 swap works: the
  continuation is open loop, and only `P(Y_τ=1 | h)` against `P(Y_τ=0 | h)` matters. At interior labels, the two
  subtrees use different query timing, and making one level monotone can break the optimality of the level above. No
  potential function was found that decreases under the exchange.

### F4. Static alternative (coordinator query)

**Theorem S1 (static, B = 1, no (M) needed) — PROVED.** Assume `t01 = t10 = 0`, any prior, `e0 < e1`, any T, `d`,
`c, k ≥ 0` and α. Then Γ = 0.

*Proof.* Show that **static ⇒ W**; Z1 under W then gives the result. Only case (b) of the Z1 argument needs it. There `G_0(s_0) > 0`, and in a static model the
post-release continuation faces the constant `q_0 = P(Y_t = 1 | Y_τ = 0)`. So `G_0 > 0` forces `2q_0 − 1 > 0`, since
every term of the schedule sum is otherwise ≤ 0 while the first switch costs k. By MLR,
`q_0 = E[e_S | Y_τ=0] ≤ E[e_S] = P_A(Y_τ = 1) = P_1`. Hence `P_1 > 1/2 > P_0`, and the swap of case (b) applies. ∎

This also explains why static alternatives never show the correlated coin: a negative label cannot be "cheap" in
the alternative while the later promotion is still valuable, because there is no drift to decouple the two.

**Static, general B and d: CONJECTURED, very strong numerics, proof OPEN.**
- **Evidence.**
  - 2,592 static grid cells (Γ = 0 in all).
  - 3,000 random static cells with `T ≤ 7`, `B ≤ 4`, `d ≤ 3` and priors 1/20…9/10, of which 1,836 violate `M_marg`
    (`fu_static_search.py` → `fu_static_s31.json`). Γ = 0 in all, and the returned IID vertex was causal-safe in all.
  - The Lemma U premise holds for every λ in 374/374 static cells (z-monotone and tape-monotone).
  - WP B's 49 static cells up to T = 24.
- **Reformulation (PROVED, elementary).** In the static case the Lagrangian problem is a POMDP over a *static* hidden
  parameter θ ∈ {A0, N, A1}. Labels are `Bernoulli(e0)`, `Bernoulli(1/2)` and `Bernoulli(e1)`, with unnormalised prior
  weights `(1−π, λ, π)`. So the observation kernel is MLR in the order **A0 < N < A1**: the null sits in the middle.
  A label flip multiplies the weights by `(r0, 1, r1)`, where `r0 = e0/(1−e0) < 1 < r1`.
- **Leaf dominance (PROVED).** At any promotion state h with `q(h) > 1/2` (all of them, by Lemma P), flip an earlier
  released 0 to a 1, giving h″. Then the posterior is MLR-higher, and the alternative likelihood rises:
  `A(h″)/A(h) = q(h⁻)/(1−q(h⁻)) ≥ q(h)/(1−q(h)) > 1`, where `h⁻` is h with that label removed. So at the leaves,
  flips help on both the belief and the null-odds axes.
- **The open step is the same subtree exchange as in F3.**
  - The classical monotone-policy theorems for MLR/TP2 POMDPs need cost monotonicity or submodularity in θ
    `[unverified citation: Lovejoy 1987; Krishnamurthy 2016, chs. 10–12, from memory]`. The per-step costs of the
    non-promote action are `(e0, 0, e1)` across `(A0, N, A1)`, which is **not monotone in θ**.
  - Rescaling the N-world (`κ·cost`, `prior/κ`) keeps beliefs MLR-ordered and can place the promotion-cost difference
    between A0 and A1. It cannot repair the per-step cost order.
  - So the textbook result does not apply as stated. Query choice and delay add further state.

### F5. Necessity (item 2)

**Theorem N1 (exact B = 1 premium formula) — PROVED.** Let B = 1 and α ≤ 1/2, with any HMM: TP2 is not assumed. For
each query time τ with `τ + d ≤ T`, define the design gains below, as exact cost reductions against never-query/never-promote
`C_0`, including the query cost.
- `g_{z0}(τ)`: query at τ and promote, at the best post-release time, only after `Y_τ = 0`.
- `g_{z1}(τ)`: the same, only after `Y_τ = 1`.
- `g_both(τ)`: promote after both values.
- `g_pre`: the best plan that promotes unconditionally, before any release or with no query; its continuation may still
  query.

Let `r_c = max(0, g_pre, max_τ {2g_{z1}(τ), g_{z0}(τ), g_both(τ)})` and `r_IID = max(r_c, 2 max_τ g_{z0}(τ))`. Then

`V*_IID = C_0 − α r_IID`, `V*_causal = C_0 − α r_c`, **`Γ = α (2 max_τ g_{z0}(τ) − r_c)⁺`**.

*Proof.*
1. **Classify pure plans.** A B = 1 pure plan has one of three forms:
   - a constant event (never, or unconditional promotion: IID and causal risk 1);
   - a `{Y_τ=1}` design (IID and causal risk 1/2);
   - a `{Y_τ=0}` design (IID risk 1/2, causal risk 1).
2. **Causal risk of a mixture.** At the public query node τ, the null picks `p ∈ [0, 1/2]`. A mixture with masses
   `a_τ` (both branches), `b_τ` (y=1 only) and `c_τ` (y=0 only), together with pre-release mass `m`, has causal risk
   `Σ_τ [a_τ + max(c_τ, (b_τ+c_τ)/2)] + m`. This is because the null maximises `(1−p)Z_0 + pZ_1` at an endpoint, and
   nodes with different τ are publicly distinguishable. IID risk is the linear `Σ_τ [a_τ + (b_τ+c_τ)/2] + m`.
3. **Both problems reduce to a best ratio.** Each maximises a linear gain under a sum of positively homogeneous convex
   gauges, so the optimum is α times the best gain-per-unit-risk over the extreme rays. For causal risk the rays are
   `b` only (ratio `2g_{z1}`), `c` only (`g_{z0}`), `c = b` (ratio `g_{z0} + g_{z1} = g_both − c ≤ g_both`, dominated),
   `a` (`g_both`) and pre-release (`g_pre`). For IID, `c` only has ratio `2g_{z0}`.
4. **Feasibility.** α ≤ 1/2 makes the risk-1/2 rays feasible at mass 2α ≤ 1.
∎

*Verification.* `fu_b1_formula.py` → `fu_b1_formula_s21.json`. The closed form lies inside the certified Γ interval in
**2,000/2,000** random B = 1 cells. These had T ≤ 6, d ≤ 2, any transitions in {0, 1/10, …, 1} (892 of them
TP2-violating), four emission pairs, five priors and `c, k ∈ {0, 1/100, 1/10}`.

**Answers to item 2.**
- **"TP2 violated or (M) violated ⇒ Γ > 0" is FALSIFIED as stated.** At B = 1, among cells violating TP2 or (M):
  - TP2-violating cells: Γ > 0 in only **59/892 (6.6 %)**;
  - TP2 holding but (M) violated: Γ > 0 in **0/552**.
  In the B ∈ {2,3} grid, Γ > 0 in **206/15,588 (1.3 %)** of the (M)-violating TP2 cells.
  Trivial reasons for Γ = 0 include promotion never paying (large k) and the best IID design being monotone anyway.
  Violations are necessary for the known mechanisms, but not sufficient.
- **Sufficient condition for Γ > 0 with explicit magnitude (PROVED, B = 1):** `2 max_τ g_{z0}(τ) > r_c`, and then
  `Γ = α(2 max_τ g_{z0}(τ) − r_c)`. In words, the best negative-label design beats every monotone design per unit
  IID risk, including the both-branch design that hedges the null. Theorem C3 is the special case where everything is
  available in closed form. The corrected value is `2g_{z0} − r_c = min{(g − k)/2 − c, g − 2k}` per unit α.
  When `g ≤ 3k − 2c`, the binding monotone design is `{Y_2 = 1}` at τ = 2, and the original section's formula was
  wrong in that regime.
- **CORRECTED: TP2 alone does not give Γ = 0 at B = 1 — FALSIFIED** (reviewer's cell, re-verified here).
  - The cell is T=5, B=1, d=2, `t01=1/2`, `t10=0`, emissions (3/20, 3/5), `prior1=0`, `c=k=0`, α=1/10.
    **Γ = 39/32000 exactly.** The certified interval gives `L = U`, and Theorem N1 independently gives
    `r_IID = 1329/3200`, `r_c = 129/320`, `α(2g_{z0} − r_c) = 39/32000`.
  - My B = 1 samples (722 TP2∧¬(M) cells, 552 here and 170 in `c2_b1_s3.json`) missed it because their emission and
    delay grids never produced a W failure. The `c2_b1_s3` (M) flags also used the wrong time range (`t ≤ T`).
  - Theorem S1 shows that static chains always satisfy W.
- **No B ≥ 2 general lower bound was found.** Γ is not monotone in B (CE-C2a has Γ > 0 at B = 2, while TP2 B = 1
  cells have Γ = 0), so B = 1 bounds do not transfer.

### F6. Updated status table (follow-up only)

| Statement | Status |
|---|---|
| Lemma Zc (query-order coupling), Lemma R′ | PROVED |
| Lemma P (promotions only at `q > 1/2`) | PROVED |
| Theorem N1 (exact Γ for B = 1, any HMM, α ≤ 1/2) | PROVED; 2,000/2,000 checked |
| Theorem S1 (static ⇒ W; hence static, B = 1, any prior ⇒ Γ = 0) | PROVED |
| TP2 + MLR ⇒ Γ = 0 at B = 1 | FALSIFIED (T=5, d=2, emissions (3/20, 3/5): Γ = 39/32000) |
| TP2 + MLR ⇒ Γ = 0 (B ≥ 2) | FALSIFIED (206 grid cells; smallest Γ = 9/50000) |
| Symmetric kernels without stationary prior ⇒ Γ = 0 | FALSIFIED (T=6, B=3, `t=1/4`, `prior1=0`: Γ ≈ 0.00216) |
| TP2 + `M_marg` ⇒ Γ = 0 (any B); intended form: multi-label W ⇒ Γ = 0 | NUMERICALLY VERIFIED (12,060 + earlier cells), unproved |
| Static alternative ⇒ Γ = 0 (any B, d, prior) | NUMERICALLY VERIFIED (2,592 + 3,000 + 374 hull checks + WP B 49), unproved beyond B = 1 |
| TP2 violated or (M) violated ⇒ Γ > 0 | FALSIFIED (6.6 % and 0–1.3 % positive rates) |

**Gate assessment.** The evaluator's Lemma U gate is **not passed by proof**. What exists:
- a sharpened, falsifiable conjecture, U-M / multi-label W, with the correct ingredient (the W-type label-weight
  condition) identified and no counterexample in 12,060 cells;
- full proofs at B = 1: Z1, S1 and the exact formula N1;
- a new coupling (Zc) that strictly enlarges the safe class.

If Paper 4 needs a multi-label theorem, the remaining work is the interior subtree-exchange lemma (F3). It is a
structural-POMDP problem with an unordered per-step cost in the 3-hypothesis representation.
