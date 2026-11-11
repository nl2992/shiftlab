# Positive causal-safety premium beyond deterministic alternation (Paper 4 theory_v2, WP C)

**Date:** 2026-11-10. **Branch:** `research/paper4-causal-premium-theory-2026-11-10`, uncommitted.
**Author:** WP C theory agent (Opus 5.5). Same-family work only; nothing here has had an independent proof review.
**Labels:** PROVED (full proof below), NUMERICALLY VERIFIED (exact rational or certified `[L,U]` on stated cells),
CONJECTURED, FALSIFIED.

**Dependencies.**
- Model and Γ: `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0.
- Theorem N1: §F5 of the same file. **N1 requires α ≤ 1/2** (WP A audit). Every B = 1 statement below inherits
  this hypothesis.
- WP A is auditing N1 in parallel. To avoid relying on N1 alone, every closed form below was checked directly
  against `gamma_cell`'s certified interval (§6).
- WP A found that C3′ (`Γ = α·min{(g−k)/2 − c, g − 2k}`) is wrong at T = 2. There the value is
  `α((g−k)/2 − c)` (C3″). Corollary SP1-D below reproduces C3″ at T = 2 and C3′ for even T ≥ 4.

---

## 0. Summary of results

| # | Statement | Status |
|---|---|---|
| Lemma S | Symmetric stationary chain: post-release gain weights `w_y(j) = (2y−1)·g·ρ^j`; pre-release weights 0 | PROVED |
| Lemma Pre | In that family, `g_pre` never binds in N1 | PROVED |
| Lemma W | `max_τ G_y(τ)` in closed form (singleton-cover structure) | PROVED |
| Lemma K | Best both-branch design: `max_M Σ_y G_y(M)⁺ = max(Ḡ_0, Ḡ_1, Ḡ_0+Ḡ_1−k)` | PROVED |
| **Theorem SP1** | Exact `Γ = α[min{Ḡ_0/2 − c, Δ, (Δ+k)/2 − c}]⁺` for all `r=|ρ|∈(0,1]`, d, T, c, k ≥ 0, α ≤ 1/2, B = 1 | PROVED; 5,400/5,400 certified cells and 25,920 exact window-DP cells |
| SP1-A | Even d ⇒ Γ = 0 (B = 1, any k, c, T, r ∈ (0,1]) | PROVED |
| SP1-B (C2b) | T-uniform lower bound `Γ ≥ α[min{(a_d−k)/2−c, a_d−a_{d+1}, (a_d−a_{d+1}+k)/2−c}]⁺`, `a_j = g r^j`; exact when `g r^{d+1} ≤ 2k` | PROVED |
| SP1-C (C2a) | Explicit open region: d odd, T ≥ d+1, `0 < r < 1`, `2c + k < g r^d(1−r)` ⇒ `Γ ≥ (α/2)[g r^d − 2c − max(k, g r^{d+1} − k)] > 0` | PROVED |
| SP1-D | r = 1 (deterministic alternation), any odd d: Γ > 0 iff T−d odd, g > 2k, 2c < g−k. Recovers C3′ (even T ≥ 4) and C3″ (T = 2), and **proves the odd-T Γ = 0 observation of C3** | PROVED |
| SP1-E (k = 0) | `Γ = α[g r^d(1−ρ^{T−d}) / (2(1+r)) − c]⁺` (d odd) | PROVED |
| C2d | Horizon, delay and mixing behaviour (§3) | PROVED (from SP1); tables NUMERICALLY VERIFIED |
| Prop. C3 | Explicit continuity modulus `|ΔΓ| ≤ 8α(T(1+k)+c)·TVB` | PROVED; 600/600 asymmetric cells consistent |
| Asymmetric anti-persistent | Γ > 0 in 100/600 random cells, all with odd d (0/212 with d = 2) | NUMERICALLY VERIFIED; no closed form |
| B ≥ 2 | d = 1: Γ(B) > 0 for all B ≤ 4 in 96/96 cells. Γ is non-monotone in B (41/192 cells). **Even d no longer forces Γ = 0** (52/96 d = 2 cells have Γ(B ≥ 2) > 0) | NUMERICALLY VERIFIED; only identity bounds proved |

---

## 1. Setting: symmetric stationary anti-persistent family

Take the model of `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0. Fix:
- `t01 = t10 = t ∈ (1/2, 1]`, so `ρ := 1 − 2t ∈ [−1, 0)`; write `r := |ρ| = 2t − 1 ∈ (0, 1]`;
- `prior1 = 1/2`, which is stationary;
- `e0 = e`, `e1 = 1 − e` with `0 < e < 1/2`, and `g := (1−2e)²`;
- `B = 1`, delay d ≥ 1, horizon T, query cost c ≥ 0, switch cost k ≥ 0, `α ≤ 1/2`.

Write `a_j := g r^j`. It is non-increasing in j, and strictly decreasing if r < 1.

**Lemma S (PROVED).**
(i) `P_A(Y_τ = 1) = 1/2` for every τ.
(ii) Before any label is released, `q_t = 1/2` for every t.
(iii) After `Y_τ = y` is released, the gain of action 1 over action 0 at time `τ + j` (j ≥ d) is
`w_y(j) := 2q_{τ+j}(y) − 1 = (2y−1)·g·ρ^j`.
So `w_1(j) = (−1)^j a_j` and `w_0(j) = −w_1(j)`. Branch y's **positive steps** are the j of parity `(1−y)` mod 2.

*Proof.*
- **Marginal.** `P(S_t=1) = 1/2` for all t. Hence `P(Y_t=1) = e/2 + (1−e)/2 = 1/2`, which gives (i) and (ii).
- **Posterior at the query.** Bayes gives `P(S_τ=1 | Y_τ=1) = 1−e` and `P(S_τ=1 | Y_τ=0) = e`, i.e. `1/2 ± (1−2e)/2`.
- **Propagation.** For the symmetric kernel, `P(S_{s+1}=1) − 1/2 = ρ(P(S_s=1) − 1/2)`.
- **Gain.** `q = e + (1−2e)P(S=1)` gives `2q − 1 = (1−2e)·2(P(S=1) − 1/2) = ±(1−2e)²ρ^j`.
- **Timing.** Labels released at `τ+d` condition the action at `τ+d`
  (`first_promotion_decomposition.py`, "Condition on labels released at the current event"), so j ranges over
  `d, …, T−τ`.
∎

**Design gains.** For a query time `τ ≤ T−d`, let `G_y(τ)` be the largest value of
`Σ_j x_j w_y(j) − k·sw(x)` over nonzero 0/1 schedules x on `j ∈ [d, T−τ]`. Here `A = 0` before release, and every
action change costs k, but there is no switch after T. A promotion followed by rollback or re-promotion is just a
schedule with several blocks, so this is exactly N1's post-release open-loop continuation (budget exhausted).

Lemma S(i) then gives `g_z0(τ) = G_0(τ)/2 − c`, `g_z1(τ) = G_1(τ)/2 − c` and
`g_both(τ) = (G_0(τ)+G_1(τ))/2 − c`.

**Lemma Pre (PROVED).** `g_pre ≤ max(0, max_τ max{g_z0(τ), g_z1(τ), g_both(τ)})`. Hence
`r_c = max(0, max_τ{2g_z1(τ), g_z0(τ), g_both(τ)})` in this family.

*Proof.* Take a pure plan that promotes unconditionally, either before its label is released or with no query at all.
- **No label released by T.** All weights are 0 (Lemma S(ii)), so the gain is `−k·sw − c·1[query] ≤ 0`.
- **Label queried at τ and released at `τ+d ≤ T`.** The plan is open loop before the release and open loop per
  branch after it. In each branch y, zero out every action before `τ+d`.
  - The weights there are 0, so no gain is lost.
  - The number of switches cannot rise: the original path already goes from `A_0 = 0` to its value at `τ+d`.
  - Each branch is now either empty or a post-release schedule.
  - So the gain is at most that of the design with promotion set `Z = {y : branch nonempty}`. That is `g_both(τ)`,
    `g_z0(τ)`, `g_z1(τ)`, or `−c` when Z = ∅.
- **Conclusion.** Finally `g_z1 ≤ max(0, 2g_z1)`.
∎

*Verified:* `g_pre ≤ r_c` holds in 5,400/5,400 certified cells (`g_pre_le_r_c`, §6).

**Reduced formula.** Write `Ḡ_y := max_τ G_y(τ)`. Combining N1 (α ≤ 1/2) with Lemma Pre gives

`Γ/α = ( Ḡ_0 − 2c − max{0, Ḡ_1 − 2c, max_τ (G_0(τ)⁺ + G_1(τ)⁺)/2 − c} )⁺.`   (★)

The z0 and z1 designs are the both-branch terms with one branch dropped.

---

## 2. The optimal post-release schedule and the closed form

Let `P_y` be branch y's positive steps in `[d, T−1]`, and `j*_y := min P_y`.

**Lemma W (closed form for Ḡ_y) — PROVED.** If `P_y ≠ ∅`:
- if `a_{j*_y} > 2k`, then `Ḡ_y = k + Σ_{j∈P_y} (a_j − 2k)⁺`;
- otherwise `Ḡ_y = a_{j*_y} − k`.

*Proof.*
1. **Reduction to block sets.** Choosing τ is choosing the last window step `M = T−τ ∈ [d, T−1]`. A schedule pays
   2k per block of 1s, or only k for a block that ends at M. So `max_τ G_y(τ)` is `k` plus the maximum, over
   **nonempty** sets of disjoint blocks in `[d, T−1]`, of `Σ_b (v_b − 2k)`. Here `v_b` is the block's weight sum,
   and we pick M as the end of the last block; any other M is dominated.
2. **Upper bound.** WLOG each block starts at a positive step; dropping a leading negative step only helps. A block
   `[s, e]` has `v_b = a_s − (a_{s+1} − a_{s+2}) − … ≤ a_s`, because each bracketed pair is ≥ 0 for non-increasing
   `a`, and a trailing negative term only lowers it. Distinct blocks have distinct starts, so
   `Σ_b (v_b − 2k) ≤ Σ_{j∈P_y}(a_j − 2k)⁺`. When every `a_j ≤ 2k`, the best nonempty set is the single block
   with the largest start, `a_{j*} − 2k`.
3. **Attained** by singletons at `{j ∈ P_y : a_j > 2k}`, or by the singleton `{j*}`.
∎

The optimal post-release schedule is therefore: **cover each positive step whose weight exceeds the round-trip
switch cost 2k, each as its own one-step block, and end the window at the last covered step** (free final switch).
Merging two covered steps across a negative step is never optimal. The negative weight `a_{j+1}` exceeds the next
positive weight `a_{j+2} > 2k`, so it exceeds the 2k saved. Write
`J := max{j : a_j > 2k}` (J = ∞ if k = 0) and `M* := min(T−1, J)`. Then the covered steps of branch y are
`P_y ∩ [d, M*]`, a geometric series.

**Lemma K (best both-branch design) — PROVED.** If `Ḡ_0, Ḡ_1 > 0`, then
`max_M (G_0(M)⁺ + G_1(M)⁺) = max(Ḡ_0, Ḡ_1, Ḡ_0 + Ḡ_1 − k)`.
If `Ḡ_1 ≤ 0` (or `P_1 = ∅`), the maximum is `Ḡ_0⁺`.

*Proof.*
- **Lower bound.** Each `Ḡ_y` is attained at its own M, with the other branch contributing ≥ 0. At
  `M = max(m_0, m_1)`, where `m_y` is the end of branch y's optimal last block, the branch that ends at M keeps
  its free final switch, and the other loses at most k (one down-switch). That attains `Ḡ_0 + Ḡ_1 − k`.
- **Upper bound, at most one free final switch.** Fix M. If only one branch has its last block ending at M, the
  other branch is a bonus-free nonempty block set, worth ≤ `Ḡ − k`.
- **Upper bound, both blocks end at M.** Let y be the branch positive at M and y′ the other.
  - **(A)** y's last block is the singleton {M}, with remaining set R in `[d, M−2]`.
    - If R ≠ ∅: y ≤ `Ḡ_y + a_M − 2k`. Truncating y′'s last block to M−1 removes `−a_M` and keeps a free final
      switch at M−1, so y′ ≤ `Ḡ_{y′} − a_M`. The sum is ≤ `Ḡ_0+Ḡ_1 − 2k`.
    - If R = ∅: y = `a_M − k`, and the sum is ≤ `Ḡ_{y′} − k < Ḡ_0+Ḡ_1−k`.
    - If y′'s last block is the negative singleton {M}, y′ ≤ `Ḡ_{y′} − 2k − a_M` (or is `−a_M − k`), which is
      smaller still.
  - **(B1)** y's last block `[s′, M]` has `s′ ≤ M−2`, and y′'s is `{M−1, M}` with remaining set R′.
    - Truncating y's block to `M−2` gives y ≤ `Ḡ_y − a_{M−1} + a_M`.
    - If R′ ≠ ∅: y′ = `R′ + a_{M−1} − a_M − k ≤ Ḡ_{y′} + a_{M−1} − a_M − 2k`, so the sum is ≤ `Ḡ_0+Ḡ_1−2k`.
    - If R′ = ∅: the sum is ≤ `Ḡ_y − k`.
  - **(B2)** Both last blocks contain `[M−2, M]`. Truncate both by two steps. Branch y gains `a_{M−1} − a_M`,
    branch y′ loses exactly the same, the switch counts are unchanged, and both still end at the window end
    `M−2`. The total is unchanged, so recurse on `M−2`.
  - The blocks shrink, so the recursion ends in (A) or (B1).
- **Conclusion.** Every M gives at most `max(Ḡ_0, Ḡ_1, Ḡ_0+Ḡ_1−k)`.
∎

**Theorem SP1 (exact B = 1 premium, symmetric stationary anti-persistent chains) — PROVED.**
Assume §1 with `r ∈ (0, 1]`, any d ≥ 1, T ≥ d+1, c, k ≥ 0 and `α ≤ 1/2`. Let `Δ := Ḡ_0 − Ḡ_1⁺`, with
`Ḡ_1 := −∞` if `P_1 = ∅`. Then

**`Γ = α · [ min{ Ḡ_0/2 − c,  Δ,  (Δ + k)/2 − c } ]⁺`**,

where, for **d odd** and `n_y` the number of covered steps of branch y (positive steps in `[d, M*]`),
- `Ḡ_0 = k + g r^d (1 − r^{2n_0})/(1 − r²) − 2k·n_0` if `n_0 ≥ 1`, else `g r^d − k`;
- `Ḡ_1 = k + g r^{d+1}(1 − r^{2n_1})/(1 − r²) − 2k·n_1` if `n_1 ≥ 1`, else `g r^{d+1} − k` (when T ≥ d+2);
- for r = 1, read `(1−r^{2n})/(1−r²)` as n;
- for T ≥ d+2 and `M′ := max(M*, d+1)`, `n := M′−d+1`:
  `Ḡ_0 − Ḡ_1 = Σ_{j=d}^{M′} (−1)^{j−d}(a_j − 2k) = g r^d (1 − ρ^n)/(1 − ρ) − 2k·1[n odd]`.

*Proof.* Substitute Lemmas W and K into (★).
1. **Case `Ḡ_1 > 0`.** Then
   `Γ/α = (Ḡ_0 − 2c − max{0, Ḡ_1−2c, max(Ḡ_0,Ḡ_1,Ḡ_0+Ḡ_1−k)/2 − c})⁺`, which is the minimum of these terms:
   - `Ḡ_0 − 2c`;
   - `Δ`;
   - `Ḡ_0/2 − c`;
   - `Ḡ_0 − Ḡ_1/2 − c`;
   - `(Δ+k)/2 − c`.
   The first is ≥ the third whenever the third is ≥ 0. The fourth is ≥ the third when Δ > 0, and Γ = 0 anyway when
   Δ ≤ 0.
2. **Case `Ḡ_1 ≤ 0`.** Then `Γ/α = (Ḡ_0 − 2c − max(0, Ḡ_0/2 − c))⁺ = (Ḡ_0/2 − c)⁺`. This agrees with the formula,
   since `Δ = Ḡ_0` and the other two terms are then not smaller.
3. **Primitive forms.** These are Lemma W with geometric sums over alternate steps. The alternating-sum identity
   comes from pairing covered steps of the two parities.
   - When `M* ≤ d`, both branches are in the "else" case: `Ḡ_0 − Ḡ_1 = a_d − a_{d+1}`, which is the `n = 2` case
     of the identity.
   - When `M* = d+1`, branch 0 covers d (`n_0 = 1`) and branch 1 covers d+1 (`n_1 = 1`). The difference is again
     `a_d − a_{d+1}`.
∎

**Corollary SP1-A (even delay kills the premium at B = 1) — PROVED.** If d is even (r ∈ (0,1]), then Γ = 0 for
every T, c, k and α ≤ 1/2.

*Proof.* For even d, `P_1` starts at d and `j ↦ j−1` maps `P_0` injectively into `P_1`, with `a_{j−1} ≥ a_j`.
- If `a_{d+1} > 2k`, Lemma W gives `Ḡ_0 ≤ Ḡ_1` term by term.
- If `a_{d+1} ≤ 2k`, then `Ḡ_0 = a_{d+1} − k ≤ k`, while `Ḡ_1 ≥ min(k, a_d − k)`, and `a_d − k ≥ a_{d+1} − k`.
- If `P_0 = ∅` there is no z0 design.
In every case `2 max g_z0 = Ḡ_0 − 2c ≤ Ḡ_1 − 2c = 2 max g_z1 ≤ r_c`, so Γ = 0 by N1. ∎

**Corollary SP1-B (C2b: T-uniform lower bound; exact in the high-switching-cost regime) — PROVED.** For d odd,
r ∈ (0,1] and every T ≥ d+1,

`Γ ≥ α·[ min{ (a_d − k)/2 − c,  a_d − a_{d+1},  (a_d − a_{d+1} + k)/2 − c } ]⁺ =: α·L(d,r,g,c,k)`,

with **equality** whenever T ≥ d+2 and `g r^{d+1} ≤ 2k`. The bound depends on T only through T ≥ d+1.

*Proof.* Lemma W gives `Ḡ_0 ≥ a_d − k`. In the alternating sum, each pair `(a_j − a_{j+1})` is ≥ 0, and an
unpaired final term `a_{M′} − 2k` is > 0 because that step is covered. So `Δ ≥ a_d − a_{d+1}`. The SP1 expression
is nondecreasing in `Ḡ_0` and `Δ`. For T = d+1 the formula is `(Ḡ_0/2 − c)⁺ ≥ L`. When `a_{d+1} ≤ 2k`, both
inequalities are equalities. ∎

*Interpretation.* The premium is at least the **first-step contrast**. The negative label's first post-release step
is worth `a_d = g r^d`. The positive label's first useful step is one step later and worth only `a_{d+1} = g r^{d+1}`.
For r < 1 this is `g r^d(1 − r) > 0`. It stays bounded away from 0 as r moves away from 1, and depends on T only
through `T ≥ d+1`.

**Corollary SP1-C (C2a: explicit open region with Γ > 0) — PROVED.** Let d be odd, T ≥ d+1, `0 < r < 1`,
`0 < e < 1/2`, `α ∈ (0, 1/2]`, and

**`2c + k < g r^d (1 − r)`**   (strict; an open set in (t, e, c, k, α), for each T ≥ d+1 and odd d).

Then **`Γ ≥ (α/2)·[ g r^d − 2c − max(k, g r^{d+1} − k) ] > 0`**.

*Proof.* Under the condition, `a_d − a_{d+1} ≥ (a_d − a_{d+1} + k)/2 − c`, because
`a_d − a_{d+1} > k + 2c ≥ k − 2c`. So `L = (1/2)·min{a_d − k, a_d − a_{d+1} + k} − c`, which is the displayed
quantity.
- If the max is k: `a_d − 2c − k > a_d(1−r) − 2c − k > 0`.
- Otherwise: `a_d(1−r) + k − 2c > 0`.
∎

*Example.* t = 3/4, e = 1/10, c = 1/100, k = 1/50, α = 1/10, d = 1, any T ≥ 2. Here
`g r(1−r) = 0.16 > 0.04`, and the bound gives Γ ≥ 0.01. The exact values are 0.014, 0.008, then 0.010 for all
T ≥ 4 (§3 table, `k1/50_c1/100`).

**Corollary SP1-D (deterministic alternation r = 1, any odd d) — PROVED.** Let r = 1 and d odd.
- If T−d is even, or `g ≤ 2k`, then Γ = 0.
- If T−d is odd and g > 2k, then `Γ = α[min{Ḡ_0/2 − c, g − 2k, (g−k)/2 − c}]⁺`, with
  `Ḡ_0 = k + ((T−d+1)/2)(g−2k)`.
- **At T = d+1**, `P_1 = ∅` and `Γ = α((g−k)/2 − c)⁺` (with `Ḡ_0 = g − k`).

*Proof.* All `a_j = g`, so Lemma W gives `Ḡ_y = k + |P_y|(g−2k)` if g > 2k, else `g − k`. Hence
`Δ = (|P_0| − |P_1|)(g−2k)⁺`. On `[d, T−1]` with d odd, `|P_0| − |P_1| = 1[T−d odd]`. ∎

For d = 1 this gives:
- **C3′ for even T ≥ 4**: there `Ḡ_0/2 − c ≥ (g−k)/2 − c`.
- **C3″ at T = 2**: `α((g−k)/2 − c)`, the min with `g − 2k` dropped, exactly as the WP A audit found.
- **Γ = 0 for odd T** (all k, c), which C3 only observed numerically. It is now PROVED.

**Corollary SP1-E (k = 0) — PROVED.** For d odd and T ≥ d+1,
`Γ = α·[ g r^d (1 − ρ^{T−d}) / (2(1 + r)) − c ]⁺`.

*Proof.* With k = 0, J = ∞, so `M* = T−1` and `n = T−d`, giving `Δ = g r^d(1 − ρ^{T−d})/(1+r)`. Moreover
`Δ/2 − c` is the minimum: `Ḡ_0 ≥ Δ`, and `Δ ≥ Δ/2 − c`. ∎

---

## 3. C2d: horizon, delay, mixing (consequences of SP1; values exact)

**Horizon T.**
- **k = 0.** `Γ_T/α = (g r^d(1−ρ^{T−d})/(2(1+r)) − c)⁺`. It oscillates with the parity of T−d, with amplitude
  `∝ r^{T}`, and converges to `g r^d/(2(1+r)) − c`.
  - T−d odd: Γ decreases to the limit.
  - T−d even: Γ increases to the limit.
  - Γ is eventually bounded away from 0 iff `c < g r^d/(2(1+r))`.
  - Since `1 − ρ^{T−d} ≥ 1 − r²` for every T ≥ d+1, `Γ_T/α ≥ g r^d(1−r)/2 − c` uniformly in T. So for r < 1,
    d odd and `c < g r^d(1−r)/2`, **every** T ≥ d+1 has Γ > 0, with no parity condition. Contrast r = 1, where
    T−d must be odd.
  - The limits T→∞ and r→1 do not commute. As T→∞ the limit tends to `g/4 − c` as r→1, which is the average of the
    two parity values `g/2 − c` and 0 at r = 1.
- **k > 0, r < 1.** `Ḡ_0` and `Ḡ_1` depend on T only through `min(T−1, J)`. So **Γ is exactly constant for
  `T ≥ max(J, d+1) + 1`**, where `J = max{j : g r^j > 2k}` is finite. T-invariance therefore holds generically in
  this family, unlike CE-7's B = 2 family.
- **Examples** (Γ/α, e = 1/10, d = 1, T = 2, 3, …):
  - t = 3/4, k = 0, c = 0: 0.16, 0.08, 0.12, 0.10, 0.11, 0.105, … → 0.10667.
  - t = 3/4, k = 1/50, c = 1/100: 0.14, 0.08, then 0.10 for all T ≥ 4.
  - t = 9/10, k = 1/10, c = 0: 0.206, 0.101, 0.165, 0.134, then 0.13883 for all T ≥ 6.
  - All from `wpC_sp1_sweep_v1.json`, `tables`, T = 2..30.

**Delay d.**
- **Even d: Γ = 0 (SP1-A).** The positive label owns the first post-release step. This parity rule replaces C3's
  T-parity rule once r < 1.
- **Odd d:** with k = 0, Γ/α is `r^d` times a factor bounded in `[1/(2(1+r)), 1/2]`, minus c, so it **decays
  geometrically in d**. Signal decays like `|ρ|^d` before release.
  - Example: t = 3/4, k = c = 0, T = 30 gives d = 1: 0.10667 and d = 3: 0.02667, a ratio of `r² = 1/4`.
  - With k > 0 the decay is faster. Once `a_d ≤ k`, `Ḡ_0 ≤ 0` and Γ = 0 (t = 3/4, k = 1/10: d = 3 gives 0).
- **Larger d never increases Γ at fixed (r, g, c, k)** for k = 0, by the formula. For k > 0 this is not separately
  proved; monotone decrease in d was observed in every tabulated row.

**Mixing (|ρ| → 0, i.e. t → 1/2).**
- **Γ → 0.** `Γ/α ≤ Ḡ_0/2 ≤ g r^d/(2(1−r²)) + k/2`, and for k > 0 we need `a_d > k` for any positive premium.
- **Thresholds** (T → ∞, d odd):
  - k = c = 0: Γ > 0 for **every** r > 0. There is no threshold, and `Γ/α ≈ g r^d/2` as r → 0.
  - k = 0, c > 0: Γ > 0 iff `r^d/(1+r) > 2c/g`.
  - c = 0, k > 0: Γ > 0 iff `g r^d > k`. Then `Ḡ_0 > 0`, and Δ > 0 automatically for r < 1.
  - General case: Γ > 0 iff `Ḡ_0 > 2c` and `Δ + k > 2c` (Δ > 0 holds automatically for r < 1, d odd).
- **Numerics** (`mixing_d1_T60`, e = 1/10, d = 1, T = 60):
  - k = 0, c = 0: Γ/α = 0.00627 at t = 0.51, 0.0533 at t = 0.6, 0.107 at t = 0.75, 0.152 at t = 0.95.
  - k = 1/50, c = 1/100: Γ = 0 for t ≤ 0.53, and Γ/α = 0.012 at t = 0.55.

**A tempting generalisation that fails: "switching costs reduce the premium".** k enters SP1 as `+k/2` in
`(Δ+k)/2 − c`. A switching cost penalises the hedging both-branch design, which needs two separate promotions, more
than the single-branch design. Example (`mixing_d1_T60`): t = 3/5, c = 0 gives Γ/α = 0.05333 at k = 0 and 0.054
at k = 1/50.

---

## 4. Asymmetric anti-persistent chains, and the continuity fallback (C1/C2 asymmetric, C3)

**Proposition C3 (explicit continuity modulus) — PROVED.** Let θ, θ′ be any two HMM parameter vectors with the same
(T, d, c, k), B = 1 and α ≤ 1/2. Then

`|Γ(θ) − Γ(θ′)| ≤ 8α (T(1+k) + c) · TVB(θ, θ′)`,

where `TVB = |Δp_1| + (T−1) max(|Δt01|, |Δt10|) + T max(|Δe0|, |Δe1|)` and `p_1 = P(S_1 = 1)`.

*Proof.*
1. **Each gain is an expectation of a fixed path function.** Every N1 design gain is a maximum over finitely many
   pure plans π of `E_θ h_π(Y_{1:T})`, with `h_π = Σ_t a_t(Y)(2Y_t − 1) − c·n_q − k·sw`. By the tower property,
   the incumbent's per-step loss `q_t` has expectation `E[Y_t]`. So `|h_π| ≤ T + c + kT`, and
   `|E_θ h − E_θ′ h| ≤ 2 sup|h| · TV(Law_θ Y, Law_θ′ Y)`.
2. **Coupling bound on TV.** Couple the two chains and emissions step by step with maximal couplings. The
   probability that they ever differ is ≤ TVB.
3. **Combine.** A max of functions with a common Lipschitz constant has the same constant. `Γ/α = (2X − Y)⁺`, with
   X = max g_z0 and Y = r_c, which contains `2g_z1`. So `|ΔΓ| ≤ α(2|ΔX| + |ΔY|) ≤ 4α·sup|Δg|`.
∎

*Consequence.* Every SP1 cell with Γ(θ) > 0 has an **explicit open neighbourhood** with Γ > 0, namely
`TVB < Γ(θ)/(8α(T(1+k)+c))`. That neighbourhood includes asymmetric transitions, asymmetric emissions and
non-stationary priors. The modulus is loose (quadratic in T). On 600 random asymmetric cells it was **never
violated** (600/600), but it was informative (gave Γ > 0) in only 15.

**Asymmetric numerics (NUMERICALLY VERIFIED,** `wpC_asym_s7.json`, seed 7**).**
- **Cells.** 600 random cells with:
  - `t01, t10 ∈ {11/20, …, 19/20}` and `t01 + t10 > 1`;
  - stationary prior;
  - 25 % symmetric emissions, otherwise `e0 ∈ {1/20..3/10}`, `e1 ∈ {7/10..19/20}`;
  - T ∈ 3..7, d ∈ 1..3, c, k ∈ {0, 1/100, 1/20} and α = 1/10.
- **N1 lies in the certified interval in 600/600 cells.**
- **Γ > 0 in 100/600:**
  - d = 1: 84/230;
  - d = 2: **0/212**;
  - d = 3: 16/158.
- **By pre-release marginal** `q̄ = e0 + (e1−e0)π`:
  - q̄ > 1/2: 37/269;
  - q̄ < 1/2: 48/294;
  - q̄ = 1/2: 15/37.
- **Reading.**
  - The d-parity rule of SP1-A survived every asymmetric cell sampled. This is CONJECTURED, not proved, for
    asymmetric chains. Asymmetry brings back nonzero pre-release weights and unequal label weights
    `P_0 ≠ P_1` (the Z1 correlated coin), so Lemmas S and Pre do not apply.
  - Unequal marginals reduce the positive rate. Neither sign of `2q̄ − 1` is required.
  - No closed form is claimed for the asymmetric family.

---

## 5. B ≥ 2 (C4)

**Proved (elementary identities).** `V*_X(B)` is non-increasing in B for X ∈ {IID, causal}. Hence

`Γ(1) − [V*_c(1) − V*_c(B)] ≤ Γ(B) ≤ Γ(1) + [V*_I(1) − V*_I(B)]`.

So Γ(B) > 0 whenever the causal value of the extra labels, `V*_c(1) − V*_c(B)`, is below the B = 1 premium of
SP1. This is a statement, not a computation: no closed-form bound on the causal value of extra labels was obtained.

**Certified data (NUMERICALLY VERIFIED,** `wpC_budget_v1.json`**).**
- **Grid:** 192 symmetric stationary cells with t ∈ {3/5, 3/4, 9/10}, e ∈ {1/10, 1/5}, T ∈ 4..7, d ∈ {1, 2},
  c ∈ {0, 1/100}, k ∈ {0, 1/50} and α = 1/10. B runs over 1..4, with B = 4 only for T ≤ 6. Every interval was exact
  (`L = U` to 1e-9), and the B = 1 value equals SP1 in all 192 cells.
- **d = 1:** Γ(B) > 0 for **every** B in 96/96 cells.
  - The ratio Γ(B)/Γ(1) lies in [0.65, 7.8] for B = 2, [0.64, 10.3] for B = 3 and [0.62, 12.9] for B = 4.
  - It exceeds 1 for some B in 60/96 cells.
  - With k = 0, Γ(B) = Γ(1) for all B in 42/96 cells.
- **Non-monotone in B (41/192 cells).** Example: t = 3/5, e = 1/10, T = 4, d = 1, c = 0, k = 1/50, α = 1/10:
  - B = 1: Γ = 27/5000 = 0.00540;
  - B = 2: Γ = 103/25000 = 0.00412;
  - B = 3: Γ ≈ 0.004376;
  - B = 4: Γ ≈ 0.004376.
- **FALSIFIED: "even d ⇒ Γ = 0" for B ≥ 2.** It fails in 52/96 d = 2 cells. Smallest witness:
  - T = 4, d = 2, t = 3/4, e = 1/10, c = k = 0, α = 1/10;
  - **Γ(1) = 0** (SP1-A), but **Γ(2) = Γ(3) = Γ(4) = 1/500** (exact `L = U`).
  - Also: t = 3/5, e = 1/10, T = 4, d = 2, c = 0, k = 1/50 gives Γ(B ≥ 2) = 9/50000.
  - The mechanism is not identified. A plausible reading (CONJECTURED) is that two labels at query distance 1
    restore an odd *relative* lag, so the policy's promotion event becomes non-monotone in the pair. The witnessing
    IID policy was not inspected.
- **CONJECTURED (d = 1, symmetric stationary anti-persistent):** Γ(B) > 0 for all B whenever Γ(1) > 0. There is no
  counterexample in 96 cells, and no proof. A monotone-in-B bound is impossible (non-monotonicity above).

---

## 6. Verification record

All commands run from the repo root with `uv run --no-sync python`. Outputs are in
`docs/paper4_continuation/theory_v2/results/` (refuse-overwrite).

| Script (sha256 prefix) | Command args | Output | Result |
|---|---|---|---|
| `wpC_sym_lib.py` (835bb6bdd4cbef0e) | library: window DP, closed forms | – | – |
| `wpC_sym_verify.py` (cca867f85c35f099) | `OUT p 3`, p = 0,1,2 | `wpC_sym_verify_p{0,1,2}.json` | 1,152 cells: window DP, N1, k=0 and k-small forms and LB/UB sandwich all inside certified Γ (1,152/1,152); C3 odd-T zero 60/60 |
| `wpC_sp1_certified.py` (0fabf6a385283867) | `OUT p 2`, p = 0,1 | `wpC_sp1_certified_p{0,1}.json` | **5,400/5,400**: SP1 inside certified Γ, N1 inside, SP1 = window DP; `g_pre ≤ r_c` 5,400/5,400; LB ≤ Γ_hi 2,880/2,880 odd-d; even-d positives 0; t ∈ {11/20,3/5,3/4,9/10,1}, e ∈ {1/20..3/10}, T 2..8, d 1..4, c ∈ {0,1/100,1/20}, k ∈ {0,1/50,1/10}, α ∈ {1/10} (+{1/4,1/2} at T=6); ~160 s per part |
| `wpC_sp1_sweep.py` (68addb4d03433758) | `OUT` | `wpC_sp1_sweep_v1.json` | 25,920/25,920: closed form = window DP (T ≤ 15, d ≤ 5, six k, three c, six t incl. r = 1); LB ≤ exact 15,552/15,552; even-d zero 10,368/10,368; k=0 form 936/936 (T ≤ 40); C2d tables |
| `wpC_asym.py` (35262cae2c823196) | `OUT 7 600 500` | `wpC_asym_s7.json` | §4 |
| `wpC_budget.py` (3c99623901b6ea27) | `OUT 0 1 1500` | `wpC_budget_v1.json` | §5 (143 s) |

The window DP (`open_loop_best`) is a brute-force 2-state DP over schedules. It shares no code with the closed
forms. `gamma_cell` and `fu_b1_formula.formula` come from `scripts/paper4_continuation/theory_C/`, unchanged.

---

## 7. Mechanism (C5) and a controlling parameter

The controlling parameter is N1's per-unit-risk advantage `Π := 2 max g_z0 − r_c`, with `Γ = αΠ⁺`. In this family
it equals `min{Ḡ_0/2 − c, Δ, (Δ+k)/2 − c}`. Each term isolates one mechanism:

| Ingredient | Where it enters |
|---|---|
| **Signal value** | `Ḡ_y`: the sum of covered weights `g r^j` (Lemma W). Its scale is `g = (1−2e)²` |
| **Label frequency / correlated coin** | Neutralised here: `P_0 = P_1 = 1/2`. The premium in this family is purely a **branch-value asymmetry** (Δ > 0), not Z1's label-weight asymmetry (`P_0 > 1/2`). Condition W fails because `G_0 > G_1` at equal weights |
| **Null's manipulation** | The causal null sets `p = 0` at the public query, so the z0 design's causal risk is 1 rather than 1/2. The IID learner gets per-unit ratio `Ḡ_0 − 2c` from z0; the causal learner's best options are z0 at double risk (`Ḡ_0/2 − c`), the monotone z1 design (`Ḡ_1 − 2c`, giving the term Δ), or both-branch hedging (`(Ḡ_0+Ḡ_1−k)/2 − c`, giving `(Δ+k)/2 − c`) |
| **Delay / anti-persistence** | The sign `ρ^d`: with d odd, the negative label predicts state 1 at the first actionable step. Hence SP1-A (even d ⇒ Γ = 0) and the `r^d` decay |
| **Switching cost** | Sets the cover threshold `a_j > 2k`, the horizon saturation J, and the free final switch. It **raises** the hedging cost (`+k/2`), so Γ can increase with k |
| **Query cost** | Paid once per design and halved per unit risk. It enters as `−c` in two terms |
| **Extra queries (B ≥ 2)** | Can raise or lower Γ (non-monotone), and can create a premium at even d (§5) |
| **Reversibility** | The model allows rollback and re-promotion. The optimal post-release schedule is a train of one-step promotions, so reversibility is used essentially. An irreversible-promotion variant was not analysed |
| **Private randomisation** | Root mixing with never-promote, unseen by the null, is what makes Γ linear in α, and is why "z0 at double risk" is still available to the causal learner. The null defeats the *label* coin but not the private coin |

**Simplest interpretable parameter:** the first-step contrast `a_d − a_{d+1} = g|ρ|^d(1 − |ρ|)`, net of the costs
in SP1-B. It is exact when `g r^{d+1} ≤ 2k` and a uniform lower bound otherwise. At fixed d it is maximised at
`|ρ| = d/(d+1)`, which is strictly inside (0,1). The long-horizon k = 0 value `g r^d/(2(1+r))` instead increases
toward the r = 1 parity-averaged value.

---

## 8. Limitations and what remains

- **Scope of the proofs.**
  - All proofs are for **B = 1, α ≤ 1/2, symmetric stationary chains with symmetric emissions**.
  - Asymmetric chains are covered only by the loose continuity modulus and by numerics.
  - The asymmetric d-parity rule is CONJECTURED.
- **Dependence on N1.** SP1 inherits N1, which is under WP A audit. SP1 is independently confirmed against
  certified LP intervals on 5,400 cells (T ≤ 8). The window DP extends the *closed-form-vs-N1-reduction* check to
  T ≤ 40, but not the LP certification.
- **B ≥ 2.**
  - Only identity bounds are proved.
  - The positive d = 1 statement is a conjecture.
  - "Even d ⇒ Γ = 0" is FALSIFIED for B ≥ 2.
  - The B = 2 even-d mechanism is unexplained.
- **Monotonicity in d** for k > 0 is observed, not proved.
- **Same-family review only;** no independent proof audit of Lemmas W, K and Pre yet.
- **New counterexamples for the registry (proposed IDs, not yet entered):**
  - "even d ⇒ Γ = 0 at B ≥ 2": T=4, d=2, t=3/4, e=1/10, c=k=0, α=1/10, Γ(2) = 1/500;
  - "switching cost lowers Γ": t=3/5, e=1/10, d=1, T=60, c=0, with k=0 → k=1/50 raising Γ/α from 0.05333 to 0.054;
  - "Γ monotone in B": T=4, d=1, t=3/5, e=1/10, c=0, k=1/50, with Γ(1) = 0.0054 > Γ(2) = 0.00412 < Γ(3).

**Assessment: CONTINUE.** SP1 turns the C3 separation example into a closed-form family theorem with interpretable
mechanisms (d-parity, first-step contrast, T-saturation). The open items are the B ≥ 2 characterisation and an
asymmetric-chain proof.

## Lead verification (2026-11-10)

Independent spot-checks with the repo `gamma_cell` (exact certified Γ) against the k = 0 corollary of SP1:
| (T, B, d, t, e, c, α) | certified Γ | SP1 / claim |
|---|---|---|
| (6, 1, 1, 3/4, 1/10, 0, 1/10) | 11/1000 | 11/1000 |
| (7, 1, 1, 3/5, 1/5, 1/100, 1/4) | 31247/6250000 | 31247/6250000 |
| (5, 1, 3, 4/5, 1/10, 0, 1/2) | 216/15625 | 216/15625 |
| (6, 1, 2, 3/4, 1/10, 0, 1/10) | 0 | 0 (even d) |
| (4, 1, 2, 3/4, 1/10, 0, 1/10) | 0 | 0 (even d) |
| (4, 2, 2, 3/4, 1/10, 0, 1/10) | 1/500 | "even d ⇒ Γ=0" fails at B = 2 (confirmed) |
Registry entries CE-15..CE-17 added. Lemmas W, K, Pre still need an independent review (WP-G).
