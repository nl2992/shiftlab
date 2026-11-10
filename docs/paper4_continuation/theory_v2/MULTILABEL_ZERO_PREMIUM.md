# WP B: the multi-label zero-premium question (Lemma U)

**Date:** 2026-11-10. **Branch:** `research/paper4-causal-premium-theory-2026-11-10` (uncommitted).
**Author:** WP B theory agent (Opus 5.5). There has been no independent review: `review_independence: none`,
`acceptance_status: provisional`.
**Status labels:** PROVED means a full proof is written here. NUMERICALLY VERIFIED means exact or certified computation
on the stated instances. CONJECTURED, FALSIFIED and UNRESOLVED have their usual meanings.
**Scripts:** `scripts/paper4_continuation/theory_v2/wpB_*.py`.
**Outputs:** refuse-overwrite JSON in `docs/paper4_continuation/theory_v2/results/`.
**How to run:** from the repo root, `uv run --no-sync python <script> ...`. The exact commands are in §7.
**Compute:** the ablation campaign had finished. At most 4 solver processes ran at once, each for 2.5 minutes or less.

## 0. Verdict

**Proved restricted theorem + counterexample.**

| Statement | Status |
|---|---|
| **Theorem S0.** Static alternative (`t01=t10=0`), `c = 0`, any prior in (0,1), any `T, B, d ≥ 1`, `k ≥ 0`, α ⇒ U1-pointwise/U2 hold, the optimal plan is tape-monotone, **Γ = 0** | **PROVED** (§2), with a numerical audit of every step |
| Static alternative, `c > 0`, `B ≥ 2` ⇒ Γ = 0 | NUMERICALLY VERIFIED: 0 failures in 29,297 cells / 79,195 hull vertices with `T ≤ 12`, `B ≤ 6`. **UNRESOLVED**; the open lemma is stated in §3 |
| **Z2: symmetric stationary persistent ⇒ Γ = 0** | **FALSIFIED** at B = 4 (§4). Smallest certified cell: T=5, B=4, d=1, `t01=t10=1/10`, `e=(1/100, 99/100)`, prior 1/2, `c=k=0`, α=25/32, **Γ ∈ [0.00209251952, 13078247/6250000000 = 0.0020925195200]** |
| U-M: TP2 + `M_marg` ⇒ Γ = 0 (any B) | **FALSIFIED** by the same cell, where `M_marg` holds with equality |
| "TP2 + multi-label W ⇒ Γ = 0", with W as defined in F3 (open-loop gain, no further labels) | **FALSIFIED.** W holds vacuously in the new cell, and also in the old CE-10 (§5) |
| U1, U2, U3 in the symmetric stationary family | All three fail in the counterexample (§4.3) |
| Symmetric stationary with B ≤ 3 | No failure in 720 grid cells (T ≤ 7) plus the earlier WP C cells. CONJECTURED only, with no structural reason found |

**Remaining obligation.** It is the static `c > 0` lemma (§3, Lemma S+). The symmetric and TP2+(M) programme is closed
negatively. A correct general HMM statement would need a condition on the *history* likelihoods, namely flip-monotone
null odds (§4.4). That is not a primitive assumption, so I do not propose it as a theorem.

## 1. Setting and the three targets

The model and notation are those of `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0:
- the decomposed first-promotion game, with promotion = the first `A_t = 1`;
- the exact alternative-only continuation after promotion (rollback and re-promotion allowed);
- `C(π)` is the alternative cost and `R(π) = P_IID(1/2)(promote)`;
- the Lagrangian is `L_λ(π) = C(π) + λR(π)` over pure plans `P`;
- a plan is **z-monotone** if its promotion indicator is nondecreasing in its labels *in query order*, and
  **tape-monotone** if it is nondecreasing in `(Y_1..Y_T)`.
By Lemma Zc and Lemma R′, mixtures of z-monotone and tape-monotone plans have causal risk equal to their IID risk.

The three targets are kept distinct:
- **U1 (uniform domination).** For every non-monotone pure π there is a monotone pure π′ with `C(π′) ≤ C(π)` and
  `R(π′) ≤ R(π)`. This holds for all λ at once and is what the Z1 swap delivers. The pointwise-in-λ version, where π′
  may depend on λ, is equivalent to U2.
- **U2 (monotone optimal support).** For every λ ≥ 0 some Lagrangian-optimal pure plan is monotone. U2 together with
  Lemma R′ gives Γ = 0.
- **U3 (value equality at α).** Some IID-optimal mixture has causal risk ≤ α, i.e. Γ = 0. This needs only the λ* hull
  edge (Lemma R, remark 2).

Implications: U1 ⇒ U2 ⇒ U3.

**Exact Lagrangian solver** (`wpB_lib.py`, new in this WP).
- It runs backward induction over the learner's information histories. The alternative state is the unnormalised mass
  over `(S_t, pending labels)`. The null mass is `λ·2^{-#released}`.
- It works in exact rationals or floats.
- It matches exhaustive pure-plan enumeration (`theory_C/fu_*` tools) exactly in 24/24 (cell, λ) checks, including
  non-static cells (`wpB_validate.py`).
- The static count-based solver `wpB_static.py` matches `wpB_lib` exactly in 12/12 checks.
- `tie ∈ {minR, maxR}` returns the least and largest IID risk over *all* Lagrangian-optimal pure plans. This is exact
  lexicographic DP.

## 2. Theorem S0 (static, c = 0): PROVED

**Hypotheses.**
- `t01 = t10 = 0`: θ := S_1 is fixed, with `P(θ=1) = π ∈ (0,1)`.
- Labels `Y_t ~ Ber(e_θ)` are i.i.d. given θ, with `0 < e0 < 1/2 < e1 < 1`.
- `c = 0`.
- Any `T ≥ 1`, `B ≥ 1`, `d ≥ 1`, `k ≥ 0` and `α ∈ [0,1]`.

**Theorem S0.** For every λ ≥ 0 there is a Lagrangian-optimal pure plan with these properties:
- it queries at times `1, …, min(B,T)`;
- it promotes at the first t with `D_t(x_t, y_t) ≤ 0`, where `D_t` is defined below;
- its promotion event is coordinatewise nondecreasing in `(Y_1, …, Y_min(B,T))`, i.e. both tape-monotone and
  z-monotone.

Hence U2 holds, the pointwise form of U1 holds, and **Γ = 0** by Lemma R′.

### 2.1 Lemma CAL (calendar reduction; uses c = 0 and staticity)

**Lemma CAL.** For every pure plan π there is a pure plan π^g with these properties:
- it queries at times `1..min(B,T)` and plays the decomposed game's optimal continuation after promotion;
- `C(π^g) ≤ C(π)` and `R(π^g) = R(π)`;
- its promotion event, as a function of the query-order label vector `z`, equals π's.

*Proof.*
1. **Information is never behind.** Let `τ_j` be π's j-th query time, which is adapted. Then `τ_j ≥ j`, so π's j-th
   label is visible from `τ_j + d ≥ j + d`. The greedy calendar shows label j from `j + d`. So at every t, π^g sees a
   superset of the z-coordinates π sees.
2. **π^g can simulate π.** It replays π's decisions on the virtual clock: it tracks π's virtual query times and treats
   `z_j` as visible from `τ_j + d`. It promotes exactly when π does, so the promotion events agree as functions of `z`.
3. **Equal laws.** Under the static alternative, given θ the label at any fresh time is `Ber(e_θ)` and independent of
   all earlier labels. Hence `(θ, z_1, z_2, …)` has the same law under both query schedules (i.i.d. `Ber(e_θ)` given
   θ). Under the IID null, z is i.i.d. Ber(1/2) for both, so `R(π^g) = R(π)`.
4. **Cost before promotion.** Before promotion both plans play action 0, which costs `e_θ` per step in world θ. The
   promotion times are equal in law jointly with θ. Query costs are 0.
5. **Cost after promotion.** At promotion π^g has weakly more information than π. Its later labels are visible no
   later than π's (step 1). So it can emulate π's continuation with the same joint law of `(θ, actions)`. Its optimal
   continuation is therefore no worse. ∎

**Why c = 0 is needed.** With c > 0, π may save query cost by delaying a query until earlier labels show the query is
unnecessary. The greedy schedule then pays more. This is the only place c = 0 is used. The rest of the proof holds for
*any* label-independent (open-loop) query calendar and any c.

### 2.2 The three-world form and the normalisation by the A1 mass

Fix the calendar. Let `ρ_{t}` indicate that a calendar label is released at t. With `m` released labels of which `s`
are ones, a released sequence has these masses:

`a0 = (1−π) e0^s (1−e0)^{m−s}`, `n = λ 2^{−m}`, `a1 = π e1^s (1−e1)^{m−s}`.

These are the worlds A0, N and A1. N carries the IID-null risk.

Every value below is a minimum of functions that are linear in `(a0, n, a1)`. This is because, given θ (resp. under N),
future labels are independent of the past. Normalise by the A1 mass:

`x := a0/a1` and `y := n/a1`.

A label flip 0→1 multiplies x by `r0/r1 < 1` and y by `1/r1 < 1`, where `r_i = e_i/(1−e_i)`. The proof needs `e0 < e1`
and `e1 > 1/2`.

For the **alternative-only** problem with old action 0 at time t, define:
- `U_t`: promote at t, then optimal (this is the stop cost minus the null part);
- `W_t`: stay at 0 at t, then optimal;
- `V^a_{t+1}`: optimal from t+1 with old action a.

Set `G_t(x) := (U_t − W_t)/a1`. For the **Lagrangian** problem, set `D_t(x,y) := (Φ_t − Ψ_t)/a1`, where:
- `Φ_t = n + U_t` (stop);
- `Ψ_t = a0e0 + a1e1 + Σ_y J_{t+1}(w⊙L_y)` (continue);
- `J = min(Φ, Ψ)`.

Branch weights at t+1:
- if `ρ_{t+1} = 1`: `(L0_y, L^N_y, L1_y) = (e0^y(1−e0)^{1−y}, 1/2, e1^y(1−e1)^{1−y})` for y ∈ {0,1};
- otherwise a single branch with all weights equal to 1.

Write `ℓ_y = L0_y/L1_y`, `ℓ^N_y = L^N_y/L1_y` and `κ(x) = 2k(1+x)`.

### 2.3 Lemma G (closed 1-D recursion for the alternative-only promote advantage)

`G_T(x) = x(1−2e0+k) + (1−2e1+k)`, and for t < T:

**`G_t(x) = x(1−2e0) + (1−2e1) + Σ_y L1_y · clip(G_{t+1}(xℓ_y), 0, κ(xℓ_y))`.**

*Proof.* The three Bellman identities are:
- `U_t = (1−q) + k + Σ V^1_{t+1}`;
- `W_t = q + Σ V^0_{t+1}`, with q mass-weighted, `q = a0e0 + a1e1`;
- `V^1 = min(U − k, W + k)`, i.e. stay at 1 or roll back; and `V^0 = min(U, W)`.

With `g = U − W`, the difference `V^1 − V^0` takes three values:

| Range of g | `V^1 − V^0` |
|---|---|
| `g ≤ 0` | `−k` |
| `0 < g ≤ 2k` | `g − k` |
| `g > 2k` | `+k` |

So `V^1 − V^0 = clip(g, 0, 2k) − k`, mass-weighted. Then the k-terms cancel:
`U_t − W_t = (1−2q) + k + Σ_y [clip(g_y, 0, 2k A_y) − k A_y]`, since `Σ_y A_y = A`.
Normalising by a1 gives the formula. ∎

### 2.4 Lemma D (recursion for the Lagrangian stop advantage)

`D_T(x,y) = y + G_T(x)`, and for t < T:

**`D_t(x,y) = G_t(x) + Σ_y L1_y [D_{t+1}^+(xℓ_y, yℓ^N_y) − G_{t+1}^+(xℓ_y)]`.**

*Proof.*
- Write `J_{t+1} = Φ_{t+1} − (Φ_{t+1} − Ψ_{t+1})^+`.
- The null part of the stop cost is a martingale: `Σ_y n L^N_y = n`, because promoting now or at t+1 costs the null
  world 1 either way.
- Hence `Φ_t − Ψ_t = [U_t − a0e0 − a1e1 − Σ_y U_{t+1}(·)] + Σ_y (Φ_{t+1} − Ψ_{t+1})^+`.
- Using `W_t = q + Σ V^0_{t+1}` with `V^0 = U − (U − W)^+`, the bracket equals `(U_t − W_t) − Σ_y (U_{t+1} − W_{t+1})^+`.
- Normalise by a1. ∎

### 2.5 Induction

**Claim.** For all t:
1. G_t is continuous and nondecreasing in x.
2. D_t is nondecreasing in x and in y.
3. `D_t − G_t` is nondecreasing in x.
4. `D_t ≥ G_t`.

*Base t = T.*
- G_T is linear with slope `1−2e0+k > 0`.
- `D_T − G_T = y`, which is constant in x and nonnegative.

*Step (assume the claim at t+1).*
1. **G_t monotone.** `clip(G_{t+1}(xℓ), 0, κ(xℓ))` is nondecreasing and continuous in x, because the function and both
   bounds are. The linear part has slope `1−2e0 > 0`, since `e0 < 1/2`.
2. **The identity for F.** Using `clip(G,0,κ) − G^+ = −(G−κ)^+` and part 4, Lemmas D and G combine to
   `D_t = x(1−2e0) + (1−2e1) + Σ_y L1_y F(xℓ_y, yℓ^N_y)`, where
   **`F := D^+ − (G−κ)^+ = min(D^+, D − G + κ)`**. The second equality is checked by cases:
   - if `G ≤ κ`, then `D−G+κ ≥ max(D,0)`;
   - if `G > κ`, then `D ≥ G > κ ≥ 0` gives `D^+ = D`.
3. **D_t monotone.** Both arguments of the min are nondecreasing in x: `D^+` by part 2, and `D−G+κ` by part 3 and
   `κ′ = 2k ≥ 0`. Both are nondecreasing in y, because G and κ do not depend on y.
4. **D_t − G_t monotone.** `D_t − G_t = Σ_y L1_y (D^+ − G^+)(xℓ_y, yℓ^N_y)`. The map `f = D^+ − G^+` is nondecreasing
   in x. Take `x1 < x2` and consider three cases:
   - If `G(x1) ≥ 0`, then `f = D − G` at both points, which is nondecreasing by part 3.
   - If `G(x2) < 0`, then `f = D^+`, which is nondecreasing.
   - Otherwise pick `x0 ∈ (x1, x2]` with `G(x0) = 0`, using continuity. Then
     `f(x2) = (D−G)(x2) ≥ (D−G)(x0) = D(x0) = D^+(x0) ≥ D^+(x1) = f(x1)`.
5. **D_t ≥ G_t.** This holds because `D^+ ≥ G^+`. ∎

### 2.6 Monotone event and conclusion

- The DP rule "promote at t iff `D_t(x_t, y_t) ≤ 0`" is optimal within the calendar class. By Lemma CAL, the calendar
  class contains a globally Lagrangian-optimal plan.
- At time t, `m_t` is deterministic. `x_t` and `y_t` are strictly decreasing in `s_t = Σ_{j≤m_t} Y_j`. By part 2 of
  the induction, `{s : D_t ≤ 0}` is an up-set.
- The promotion event `∪_t {s_t ∈ Stop_t}` is therefore nondecreasing in `(Y_1..Y_B)`.
- Lemma R′ then gives Γ = 0. ∎

**Remarks.**
1. **Tie-breaking.** Any consistent rule works, whether `≤ 0` or `< 0`.
2. **Stronger than needed.** The result is a *threshold* structure: at each t there is `s*_t` with promote iff
   `s_t ≥ s*_t`. The stop region is a **down-set in (π_A0/π_A1, π_N/π_A1)**, which is stronger than monotonicity along
   lines toward `e_{A1}` (compare Krishnamurthy, Thm 6.3.4, §6(f)).
3. **Corollary (open-loop query schedules, any c ≥ 0).** Steps 2.2–2.6 use only a label-independent release calendar.
   So for every c, within the class of plans whose query schedule is fixed in advance, every λ has a monotone optimal
   plan. Within that class the premium is 0. This is a statement about a restricted learner class, not about Π_B.
4. **Hypotheses used.**
   - `e0 < 1/2`: slope of the linear term.
   - `e0 < e1`, `e1 > 1/2`: flips decrease x and y.
   - staticity and c = 0: Lemma CAL, plus linearity in world masses.
   - k, d, T, B and the prior are unrestricted.

**Numerical audit** (`wpB_static_proofcheck.py`, 254 random static greedy cells with `T ≤ 10`, `e0 ∈ [0.001,0.49]`,
`e1 ∈ [0.51,0.999]`, `k ≤ 3`):
- the closed recursions agree with the exact DP to within `4.5e-13` (G) and `6.8e-13` (D);
- induction claims 2 and 3 hold on a 73×42 log-grid of (x, y) at every t, with **0 violations**
  (`wpB_static_proofcheck_s1.json`).

Separately, D is monotone at all reachable effective (x, y) in 1,292 greedy configurations (scratch run).

## 3. Static alternative with c > 0: UNRESOLVED (numerically verified)

**Evidence.**
- `wpB_static_falsify.py`: every λ-hull vertex was found by parametric DP, and the DP-optimal plan was tested for
  z-monotonicity under two tie-breaks. With c ∈ {1e-4, …, 0.3}:
  - **0 flagged vertices** in 7,035 cells with `T ≤ 12`, `B ≤ 6`, `d ≤ 3` (22,932 vertices);
  - **0 flagged vertices** in 22,262 cells with `T ≤ 9`, `B ≤ 4` (56,263 vertices).
- The general solver (`wpB_falsify.py static`) found 0 flags in 884 cells, including c = 0.
- U1 in the uniform sense holds in 25/25 enumerated static cells with `B ≤ 3` (`wpB_u1_static_s1.json`).

**Where the proof of §2 breaks with endogenous queries** (route (a)):
1. **No calendar reduction.** Query timing becomes label-dependent.
2. **D is not monotone in x.** At a fixed structural state `(t, pending, b)`, D is no longer monotone in x. Witness
   (`wpB_static_patterns_s4.json`): T=3, B=1, d=1, e=(0.49, 0.75), c=0.2, k=0 gives `D(0.02, 1) = −0.4532 > D(0.1, 1)
   = −0.4660`. Its sign behaviour is still consistent with a down-set stop region. Lemma D's identity also fails,
   because stop and continue may choose different queries at t.
3. **Decisions are ordered in s, but that does not settle the event.** In 3,615,159 structural states from 124,126
   DP-optimal static plans, the decision as a function of s always follows the order **dead < wait-alive <
   query < promote**, with zero reversals. The rare patterns `wQ`, `wQP` and `xwQ` (125 states) show that the query
   decision does depend on s. When the decisions at h and at its flip h′ differ in the query, the two paths have
   different calendars. A single-state order then does not imply containment of the promotion events. This is exactly
   the interior-exchange obstacle.

**Open lemma (smallest irreducible form).**

> **Lemma S+.** Static model, c > 0, B ≥ 2. Let h and h′ be pre-promotion states at the same time with the same
> pending set and budget, where h′ is h with one released 0 flipped to 1. Then the promotion event of the DP-optimal
> continuation from h′ contains the event from h, as functions of the future labels in query order.

Lemma S+ applied at every state implies z-monotonicity of the DP plan, hence U2 and Γ = 0. By §2 it holds when both
continuations follow the same calendar. What remains is the case where the decisions at h and h′ differ in whether to
query. Patterns `xQ`, `wQ`, `xwQ` and `wQP` occur, and when h is dead the case is trivial. So the only nontrivial case
is **h waits alive while h′ queries**.

## 4. Symmetric stationary persistent: FALSIFIED (B = 4)

### 4.1 Smallest certified counterexample found (CE-B1)

**Cell.** T=5, B=4, d=1, `t01=t10=1/10` (ρ = 4/5), `e0=1/100`, `e1=99/100`, prior 1/2 (stationary), `c = k = 0`,
α = 25/32. (M) holds with equality: `P_A(Y_t=1) = 1/2` for all t.

**Certified values** (`wpB_ce_record_v1.json`):
- `gamma_cell`, using repo FCG with exact certificates: **Γ ∈ [0.0020925195199995, 0.0020925195200005]**, `Γ_lo > 0`
  exactly.
- `V*_IID = 1588759181/1562500000`, with primal = dual = `J(λ*) − λ*α` at `λ* = 4386627/9765625`. This is computed
  independently by the new DP and matches `U_IID` exactly.
- A feasible causal policy costs `U_causal = 6368114971/6250000000`, so **Γ ≤ 13078247/6250000000** exactly.
- **Independent lower bound** (`wpB_dual_check.py`, no FCG). One explicit causal null is used, together with weak
  duality on the 2-row Lagrangian. The null sets `p = 0` for a query made at t = 2 when `Y_1 = 0` was seen, and
  `p = 1/2` otherwise; it keys only on public information. This gives
  `V*_causal ≥ 92408221607580963141/90694246400000000000`, so **Γ ≥ 0.0020925138 > 0**
  (`wpB_dual_check_symCE_T5B4.json`).

**Hull of the pure-plan (R, C) set** (exact DP):

| λ range | Vertex R | z-monotone optimal plan? |
|---|---|---|
| (0, 0.31527) | 15/16 | yes |
| (0.31527, 0.44919) | **13/16** | **no** |
| (0.44919, 0.50119) | 3/4 | yes |
| … | 5/8, 1/2, 1/4, 1/8, 0 | yes |

- At λ = 2/5, the lexicographic DP shows that **every** Lagrangian-optimal pure plan has `R = 13/16` and
  `C = 783413023/781250000`. These plans are not z-monotone and have causal risk 7/8.
- The witness is that the plan promotes after `z = (0,0,0,1)` but not after `(0,1,0,1)`.

**The IID-optimal policy** (`inspect_policy.py 5 4 1 1/10 1/10 1/100 99/100 1/2 0 0 25/32`):
- It queries at 1, 2 and 3.
- It promotes at t = 2 if `Y_1 = 1`, and at t = 4 if `(Y_1, Y_3) = (0, 1)`.
- After `(0,0,0)` it queries `Y_4` with probability 1/2 and promotes at t = 5 iff `Y_4 = 1`.
- After `(0,1,0)` it never promotes.

IID risk is 25/32, causal risk 13/16.

### 4.2 Mechanism (route (b)/(c) obstruction)

The alternative's history likelihood is not monotone under label flips. With accurate labels and a persistent chain:
- `P_A(0,0,0,1)` needs about one switch;
- `P_A(0,1,0,1)` needs about three switches or label errors, and is far smaller.

The value of promoting at the leaf is similar in both cases (both end with a fresh 1). Promotion there is worth the
null price `λ·2^{-4}` only on the likely history. In the 3-world language of §2, a flip moves the alternative state up
in the MLR order. But it can **raise** the null odds `y = n/P_A(h)`: the "top world" normalisation of §2 has no analogue
when the alternative is a mixture over hidden paths. In that setting, the stop-minus-continue cost is not monotone in
every path-world's relative mass.

This is the fixed-calendar Neyman–Pearson failure predicted in THEORY §2.3, point 2. It is now realised by an
*adaptive* optimum. The causal null exploits it by playing `p = 0` on the second query after `Y_1 = 0`.

### 4.3 Consequences for U1/U2/U3

- **U3 fails at α = 25/32.** This is the certified Γ > 0.
- **U2 fails** for every λ ∈ (0.31527, 0.44919): no Lagrangian-optimal pure plan is z-monotone or tape-monotone.
  - All optimal plans at such λ have `(R, C) = (13/16, C1)`. This is verified exactly at λ = 2/5 by the minR/maxR
    lexicographic DP.
  - Suppose a monotone plan attained that vertex. Mixing it 1:1 with the z-monotone R = 3/4 vertex plan would give an
    IID-optimal mixture at λ* with causal risk = IID risk = α (Lemma Zc). That would make Γ = 0, a contradiction.
- **U1 fails**, because U1 ⇒ U2.
- All four outcomes of the falsification brief are realised:
  1. a non-monotone Lagrangian-optimal pure plan;
  2. failure of pure-plan replacement;
  3. failure of monotone optimal support;
  4. certified Γ > 0.

### 4.4 Further certified cells and α-range

All cells below have the symmetric stationary prior. Data are in `wpB_symce_*.json` and `wpB_ce_record_v1.json`.

| T | B | d | t | e1 | c | k | α | certified Γ |
|---|---|---|---|---|---|---|---|---|
| 5 | 4 | 1 | 1/10 | 999/1000 | 0 | 0 | 25/32 | 2.950e-3 |
| 5 | 4 | 1 | 1/4 | 99/100 | 0 | 1/100 | 25/32 | 2.02e-5 |
| 6 | 4 | 2 | 1/20 | 999/1000 | 0 | 1/20 | 25/32 | 1.66396e-3 |
| 6 | 5 | 1 | 1/20 | 99/100 | 0 | 1/100 | 13/16 | 5.827e-3 |
| 9 | 6 | 1 | 1/100 | 99/100 | 1/1000 | 1/1000 | **69/128 ≈ 0.539** | 8.763e-4 |

**Scan coverage.**
- **B ∈ {2, 3}, T ≤ 7, d ≤ 2:** 0 flagged vertices in 720 cells, using a grid with `t ∈ {1/100, 1/20, 1/10, 1/4}`,
  `e1 ∈ {9/10, 99/100, 999/1000}` and `k ∈ {0, 1/100, 1/20}`.
- **Every B ≥ 4 slice:** positive Γ was found.
- **The α threshold falls as B grows.** The smallest α with certified Γ > 0 so far is 69/128, at B = 6.
- **Emission accuracy matters.** No positive cell has `e1 = 9/10` in the scanned grid.

**Not established.**
- Γ = 0 for B ≤ 3, or for α ≤ 1/2, in the symmetric family. Both are CONJECTURED only, with no proof route.
- Symmetry gives no flip order on `P_A(h)`; see route (d).

## 5. Case (iii): TP2 + multi-label W

- **TP2 + `M_marg`.** FALSIFIED by CE-B1, where `M_marg` holds with equality.
- **`M_cond`.** CE-B1 violates `M_cond`: `P(Y_2 = 1 | Y_1 = 0) < 1/2`. `M_cond` is not refuted, but it is a very strong
  "challenger conditionally never worse" condition.
- **Multi-label W in F3's definition.** W uses the open-loop promotion gain with *no further labels*.
  `wpB_multiW.py` checked every reachable `(h, τ, s)` with `|h| ≤ B−1`, including gapped query sets.
  - **W holds, vacuously, in CE-B1**: 58 checks, and `G_0 > 0` never occurs.
  - **It also holds vacuously in the old CE-10** (T=3, B=2, Γ = 9/50000).
  - So "TP2 + multi-label W ⇒ Γ = 0" is FALSIFIED.
  - The reason is that W, as defined, constrains only the *last* label. Every known multi-label failure, CE-6, CE-10
    and CE-B1, is non-monotone in an *interior* label. An interior version of W would have to use the optimal
    continuation with further labels, which is a value-function condition and not a primitive one.
- **Falsification in the TP2+`M_marg` family** (`wpB_falsify_tp2m_s1.json`): 5 of 828 cells were flagged, all with
  B = 4. Their Γ was not certified individually; CE-B1 already settles the question.

## 6. Proof routes: record

- **(a) Homogeneous weight-space stopping region. SUCCEEDED for the static case with c = 0** (§2).
  - The needed ∂_y sign is the envelope fact: `D` has slope `1 − P_N(promote | continue) ≥ 0` in y.
  - The needed ∂_x sign is **not** an envelope fact. `E_t(x) := G_t − Σ L1 G_{t+1}^+` is often *decreasing*: in 1,022
    of 2,835 (cell, t) checks (scratch run `g2.py`). So "promoting one step earlier is worse in A0" is false.
  - The working induction hypothesis is instead the pair (D monotone, `D − G` monotone).
  - The interior-exchange obstacle is avoided, not solved, by Lemma CAL: with c = 0 the static query schedule can be
    chosen independent of labels.
  - With c > 0 the obstacle is Lemma S+ (§3).
- **(b) Constrained optimal stopping with endogenous acquisition, symmetric persistent.** No monotone-boundary theorem
  can hold, by CE-B1. The obstruction is the non-monotone null odds of §4.2.
- **(c) Exchange arguments.** In the symmetric family no exchange can succeed. At λ = 2/5 in CE-B1, every optimal plan
  is non-monotone and no monotone plan attains the optimum. So no potential function exists there.
  - The static c = 0 proof needs no exchange.
  - For static c > 0, U1 holds in uniform form in 25/25 small enumerated cells, but no exchange map was found for the
    "wait-alive vs query" case.
- **(d) Involution S↦1−S, Y↦1−Y** (symmetric stationary).
  - **What it gives:** `P_A(h) = P_A(h̄)`, posterior `p(h̄) = 1 − p(h)`, the null odds are invariant, and `M_marg` holds
    with equality.
  - **What it does not give:**
    - an order of `P_A` across single flips, which CE-B1 breaks;
    - an invariance of the plan class. Promotion is the first 0→1 switch with `A_0 = 0` fixed, so the mirrored plan
      is not in the class.
- **(e) Dual-support characterisation (U3 without U2).** Not needed in the static case. In the symmetric family U3
  fails exactly when the only plans on the λ* edge with risk above α are non-monotone (CE-B1). In the scans, most
  vertices with U2 candidates produced certified Γ > 0 at the adjacent-edge α. No cell was found with U2 failing and
  U3 holding at every α.
- **(f) Classical monotone-policy theorems.** The statements were read from Krishnamurthy, arXiv 1512.03873 (2015
  version, extracted text).
  - **Thm 5.3.1 (X = 2 POMDP)** assumes:
    - (C) cost decreasing in the state;
    - (F1) TP2 observations;
    - (F2) TP2 transitions;
    - (F3′) tail-sum supermodularity;
    - (S) submodular costs.

    It does not apply, because our world space has X = 3 (A0, N, A1).
  - **Thm 6.3.4 (stopping-time POMDP; nonlinear costs allowed)** assumes:
    - (C) `C(π,u)` is first-order stochastically decreasing in π for each u;
    - (F1), (F2);
    - (S) submodularity on lines `L(e_X, π̄)` and `L(e_1, π̄)`.

    The conclusion is monotonicity only along those lines, i.e. a switching curve. In our static 3-world reformulation
    (F1) holds (`e0 < 1/2 < e1`) and so does (F2) (identity kernel). **(C) fails for the continue action:** its per-step
    cost `(e0, 0, e1)` is not monotone in A0 < N < A1, in either direction.
    - Per-world constant shifts do not repair this in a stopping problem. Stopping ends the accrual, so the shift moves
      into the stop cost.
    - Rescaling N fixes the one-step promote-minus-stay difference, but not (C).
  - **Multiple continue actions and delayed observations.** Querying or not makes several continue actions, and
    delayed observations make a non-stopping, non-standard POMDP. The book's controlled-sampling example (§7.4) is a
    different 2-state model without delays.
  - **Summary.** Theorem S0 replaces (C)+(S) with the explicit G/D recursion. It also gives a stronger conclusion: a
    down-set in `(π_A0/π_A1, π_N/π_A1)`, which contains the line-monotonicity toward `e_{A1}`.
  - **Lovejoy (1987)** is cited in the book only for its suboptimal bounding algorithm. I did not read the paper:
    `[unverified: Lovejoy 1987 not re-read]`.

## 7. Experiments (exact commands; all from the repo root)

| Purpose | Command | Output (results/) | Result |
|---|---|---|---|
| Solver validation | `wpB_validate.py` (prints) | — | 24/24 exact matches with enumeration |
| Proof audit, static c=0 | `wpB_static_proofcheck.py results/wpB_static_proofcheck_s1.json 1 110` | `wpB_static_proofcheck_s1.json` | 254 cells, recursion error ≤ 6.8e-13, 0 violations |
| Static c>0 falsification | `wpB_static_falsify.py results/wpB_static_falsify_s1_T12B6.json 1 110 12 6` and `... _s2_T9B4.json 2 110 9 4` | same names | 0 / 22,932 and 0 / 56,263 vertices flagged |
| Static diagnostics | `wpB_static_patterns.py results/wpB_static_patterns_s4.json 4 80` | same | order x<w<Q<P, 0 reversals in 3.6M states; D non-monotone witness |
| Hull/U2 scan, 4 families | `wpB_falsify.py results/wpB_falsify_{static,sym,tp2m,tp2any}_s1.json FAMILY 1 100` | same | flagged cells: static 0/884, sym 18/677 (all B=4), tp2m 5/828, tp2any 10/932 |
| Hull scan, larger sym | `wpB_falsify.py results/wpB_falsify_sym_s2_T10B6.json sym 2 110 10 6` | same | 6/142 flagged; smallest flagged vertex R = 35/64 |
| Smallest-CE scan | `wpB_symce.py results/wpB_symce_sym_B23_T3-7.json sym 3 7 2,3 1,2` (and `_B4_T4-5` `4 5 4 1,2`, `_B4_T6` `6 6 4 1,2`, `_B5_T5-6` `5 6 5 1`) | same | B≤3: 0/720; B=4,T≤5: 20 certified Γ>0 (all T=5); B=4,T=6: 75; B=5: 192 |
| U1 (uniform) | `wpB_u1_check.py results/wpB_u1_{static,sym}_s1.json FAMILY 1 25` | same | 0/25 failures each (B ≤ 3 shapes) |
| CE record | `wpB_ce_record.py results/wpB_ce_record_v1.json` | same | §4.1 / §4.4 values |
| Independent Γ>0 bound | `wpB_dual_check.py results/wpB_dual_check_symCE_T5B4.json "(5,4,1,F(1,10),F(1,10),F(1,100),F(99,100),F(1,2),F(0),F(0))" 25/32 "lambda tq, rel: F(0) if (tq == 2 and rel == ((1, 0),)) else F(1, 2)"` | same | Γ ≥ 0.0020925138 |
| Multi-label W | `wpB_multiW.py results/wpB_multiW_symCE_T5B4.json "(5,4,1,0.1,0.1,0.01,0.99,0.5,0,0)"` and `results/wpB_multiW_control_CE10.json "(3,2,1,0.5,0.1,0.1,0.6,0,0,0)"` | same | W holds vacuously in both |

**Code version.** Branch HEAD `a7a1673f` plus the uncommitted `scripts/paper4_continuation/theory_v2/wpB_*.py`.
**What each check establishes.**
- The float hull scans locate candidates. They are descriptive search, not evidence of absence beyond the grid.
- The certified statements rest on `gamma_cell` (exact rationals) and on the exact DP.
- The scratch runs (`s1.py`, `s2.py`, `g2.py`) are exploratory and are cited only as diagnostics.

## 8. Continue / pivot / stop

- **Stop** the symmetric and TP2+(M) zero-premium conjecture. It is false at B ≥ 4, with a 4-label correlated-history
  mechanism, at moderately large α.
- **Continue (narrowly)** with the static case. Theorem S0 is a clean, assumption-light result: the static
  alternative, free labels, any budget, delay and switch cost. Closing Lemma S+ would extend it to c > 0.
- For Paper 4, the honest multi-label statement is "Γ = 0 for static alternatives with free labels; Γ > 0 can occur
  for persistent symmetric alternatives once B ≥ 4". The positive-premium side should note that CE-B1 has
  `M_marg` with equality, so (M)-type marginal conditions cannot be the dividing line.
- **Pending lead actions.**
  - Add CE-B1 to `COUNTEREXAMPLE_REGISTRY.md`.
  - Re-compute it independently (WP A).
  - Review the proof of §2.

## Lead verification (2026-11-10)

- Counterexample re-computed by the lead with the repo `gamma_cell` (FCG-fast, exact rationals): T=5, B=4, d=1,
  t01=t10=1/10, e=(1/100, 99/100), prior 1/2, c=k=0, α=25/32 ⇒ certified **Γ ∈ [0.0020925195, 0.0020925195] > 0**;
  IID optimum has IID risk 25/32 and causal risk 13/16.
- **α sweep on the same cell:** Γ = 0 (certified upper bound 0) at α ∈ {1/20, 1/10, 1/4, 3/8, 1/2, 9/16, 5/8,
  11/16, 3/4, 7/8}; Γ > 0 only at α = 25/32. The failure sits on one Lagrangian hull edge.
- **Consequence for the conjecture.** Z2 / U-M "for every α" is FALSIFIED. The restricted statement
  **Z2≤½: symmetric stationary persistent and α ≤ 1/2 ⇒ Γ = 0** has no counterexample yet and remains CONJECTURED.
  α ≤ 1/2 is the regime of N1 and of any practical promotion-error level; it is not added to exclude this cell but
  is recorded because every failure found so far has α > 1/2 (smallest 69/128). Follow-up: hull-targeted search at
  α ≤ 1/2 (requested from WP-B).
