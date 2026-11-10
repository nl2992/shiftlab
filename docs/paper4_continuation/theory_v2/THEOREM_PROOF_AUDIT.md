# WP A — Theorem proof audit of the causal-safety premium results

**Date:** 2026-11-10. **Branch:** `research/paper4-causal-premium-theory-2026-11-10` (HEAD `a7a1673f`, audit files uncommitted).
**Reviewer:** fresh-context Opus 5.5 subagent acting as the substitute reviewer for the unavailable ARIS/Codex slot (BL-1).
`review_independence: same-family` · `acceptance_status: provisional`. The method follows `.agents/skills/proof-checker/SKILL.md`:
an obligation ledger, the issue taxonomy, two-axis severity, and a counterexample red team. No external-family review has
taken place. A label of PROVED below means that I reconstructed the proof from the primitive model and found no gap. It
does not mean the proof has been accepted.

**Sources audited:**
- `docs/paper4_continuation/CAUSAL_SAFETY_PREMIUM_THEORY.md`: §0, §1 (Lemma R), §2.1 (Z1), §3.1 (C3), and F1, F2, F4 and F5
  (Zc, P, S1, N1);
- `docs/paper4_continuation/CAUSAL_SAFETY_PREMIUM_REVIEW_CORRECTIONS.md`;
- the solver `src/shiftlab/dive/first_promotion_decomposition.py` and `causal_switching_game.py` (the `_null` tree and
  `null_risk`);
- `scripts/paper4_continuation/theory_C/gamma_lib.py`.

## 0. Model facts confirmed from code (used by every proof)

| Fact | Where verified | Consequence |
|---|---|---|
| The null moves only at pre-promotion query nodes. Its information is `(learner history, all generated outcomes incl. pending, own past moves)`, and its move is `p ∈ {0, 1/2}` | `causal_switching_game._null`, `null_risk` | Choosing `p ∈ [0,1/2]` is the same as mixing the endpoints `0` and `1/2` (the label laws are identical), so endpoints are WLOG. A non-queried label never affects learner behaviour or risk |
| Risk is the probability of the first `action = 1`. A simultaneous promote-and-query is a promotion leaf, and the null does not move at it | `_null` (`if action: risk += weight; continue`) | Z1 and N1 are right to treat promote-and-query as a constant event |
| Post-promotion play is the exact belief DP with the remaining budget, pending labels and delay | `_promote_value`, `_value_at` | The decomposition is exact for both problems, because risk is fixed at promotion and post-promotion cost is evaluated under the HMM only |
| `S_1 = propagate(prior1, 1)`, i.e. one transition after the prior | `_alternative` root, `RegimeModel.propagate` | "Stationary start" means `propagate(prior,1) = π∞` |
| `0 < e0 < 1/2 < e1 < 1` is enforced | `RegimeModel.__post_init__` | (MLR) always holds, and `P_A(Y_τ = y) > 0` |
| The learner has perfect recall: its information is its own actions plus released labels | `information()` | Kuhn's theorem applies |

## 1. Independent computation

`scripts/paper4_continuation/theory_v2/wpA_audit_checks.py` re-implements the B = 1 model from scratch:
- the hidden-path enumeration and the exact posteriors `P(Y_t=1 | released labels)`;
- the post-promotion belief DP, with an optional query, delay and switch costs;
- the design gains `g_pre`, `g_z0(τ)`, `g_z1(τ)` and `g_both(τ)`;
- the N1 closed form.

It does **not** import `fu_b1_formula.py`. The only reference it imports is `gamma_cell`, the certified LP/FCG computation.
For each cell it checks three separate exact-rational containments, each with a 1e-9 slack for the rationalised duals:
- `V_IID` against `[L_IID, U_IID]`;
- `V_causal` against `[L_causal, U_causal]`;
- `Γ` against `[Γ_lo, Γ_hi]`.

A first run caught a transposed `t10` in my own path enumeration. All three checks failed until it was fixed, which
shows that the check discriminates. All numbers below are from the fixed code.

**Reproduce** (repo root; the outputs refuse to overwrite and live in `docs/paper4_continuation/theory_v2/results/`):
```
S=scripts/paper4_continuation/theory_v2/wpA_audit_checks.py; R=docs/paper4_continuation/theory_v2/results
uv run --no-sync python $S random $R/wpA_n1_random_s101.json 101 150      # also seeds 202 (150) and 303 (400)
uv run --no-sync python $S cells  $R/wpA_n1_targeted.json <targeted.json>  # cell lists: session scratchpad wpA/
uv run --no-sync python $S cells  $R/wpA_n1_scope_alpha_gt_half.json <scope.json>
uv run --no-sync python $S cells  $R/wpA_s1_static_certified.json <static.json>
uv run --no-sync python $S c3grid $R/wpA_c3prime_grid_T246.json 2,4,6
uv run --no-sync python $S c3grid $R/wpA_c3_grid_oddT35.json 3,5
uv run --no-sync python scripts/paper4_continuation/theory_v2/wpA_formula_search.py static 11 3000   # also: tp2M 12 3000
uv run --no-sync python scripts/paper4_continuation/theory_v2/wpA_zc_enum.py T B d                 # → wpA_zc_enum.txt
```

**Result table:**

| Run | Cells | N1 matches the certified V_IID / V_causal / Γ | Γ > 0 (certified) | Notes |
|---|---|---|---|---|
| random s101, s202, s303 | 700 | **700 / 700 / 700** | 12 | 322 non-TP2; T ≤ 6, d ≤ 3, α ∈ {1/20, 1/10, 1/4, 1/2} |
| targeted (anti-persistent, drifting, off-stationary, edge cases) | 165 | **165 / 165 / 165** | 17 | 108 non-TP2. Edge cases T=1, d ≥ T and α=0 included |
| static (certified) | 80 | 80 / 80 / 80 | 0 | t01 = t10 = 0, d ≤ 3, priors 0…1 |
| C3 grid, T ∈ {2,4,6} | 576 | 576 / 576 / 576 | 480 | alternation family |
| C3 grid, T ∈ {3,5} | 384 | 384 / 384 / 384 | **0** | odd T |
| **scope red team, α > 1/2** | 40 | 28 / 30 / 37 | 1 | **N1 fails outside α ≤ 1/2, as expected** |

In total, **1,905 / 1,905 cells with α ≤ 1/2 match exactly on all three quantities**, 509 of them with Γ > 0.

Formula-only searches, using my N1 implementation, which is validated above:
- 3,000 random static cells: Γ = 0 in all;
- 3,000 random TP2 + (M) cells, drawn from 5,065 TP2 draws: Γ = 0 in all.

---

## 2. Lemma R (and R′)

**Obligation ledger:**
- R1: Kuhn equivalence between behavioural and mixed learners, against every null.
- R2: `C` and `R` are linear on `Δ(P)`.
- R3: strong duality with one inequality.
- R4: the hypothesis ⇒ `V_IID(M) = V*_IID`.
- R5: every mixture over `M` has causal risk ≤ its IID risk.
- R6: the chain of inequalities.

| Step | Status | Note |
|---|---|---|
| R1 | ACCEPTED | The learner has perfect recall. Kuhn's theorem gives the same joint law of (actions, labels) against **any fixed** opponent strategy, so it holds for every null at once |
| R2, R3 | ACCEPTED | Finite LP, feasible (never-promote has risk 0) and bounded. LP duality needs no Slater condition |
| R4 | ACCEPTED | Equal dual functions give equal `max_λ`. The "for all λ" hypothesis is stronger than needed. Remark 2 (at λ* alone, π⁻ and π⁺ in `M` bracketing α) is the correct minimal form |
| R5 | ACCEPTED | Fix a pure π and a null ν. Set `Y_t = 1{U_t ≤ p_t}`, with `p_t` arbitrary (≤ 1/2) at non-queried t, and `Y*_t = 1{U_t ≤ 1/2}`. Because `U_t` is independent of the past, `Y` has the ν-law even though `p_t` reads pending labels and public actions. `Y*` is i.i.d. Ber(1/2), so `g_π(Y*)` has the exact IID law. The IID run may query at different times, and that is harmless because `g_π` is a function of the whole tape. Pathwise `Y ≤ Y*` together with monotone `g_π` gives `g_π(Y) ≤ g_π(Y*)`. For a mixture: ν restricted to the histories of one pure plan is an adapted null, so `sup_ν Σ μ(π)P_ν(π) ≤ Σ μ(π)R(π)` |
| R6 | ACCEPTED | |
| Role of monotonicity | — | Monotonicity is used only in R5, and only for pure plans in the support. Monotone vertices that HiGHS returns are irrelevant, as Remark 1 says |

**Red team.** The obvious attack is a null that learns the drawn plan from public actions and adapts to it. It is
neutralised because the bound holds per pure plan. I found no counterexample.

**R′.** Replace `M` by `M_z ∪ M_tape` (see Zc). The step is ACCEPTED, because R5 holds per plan for either class.

**Routine vs specific.** This is a **routine corollary**: single-constraint LP duality over mixed strategies (Kuhn), plus
the standard monotone coupling for first-order stochastic dominance. Its only model-specific content is noting that the
causal family is dominated coordinatewise by Ber(1/2), so monotone events are maximised by the IID null.

**Label: PROVED** (R and R′).

## 3. Theorem Z1 (B = 1), and its W form

**Obligation ledger:**
- Z1a: the classification of pure B = 1 plans.
- Z1b: after release the continuation is open loop.
- Z1c: `G_1 ≥ G_0` under TP2 + MLR.
- Z1d: replacement (a).
- Z1e: replacement (b), including feasibility.
- Z1f: lifting to all λ and to mixtures via Lemma R.

| Step | Status | Note |
|---|---|---|
| Z1a | ACCEPTED | Before the query nothing is observed, so the pre-promotion actions are all 0 and the query time τ is deterministic. Any promotion at `s < τ+d`, including one simultaneous with the query, gives a constant event. **A pure plan cannot query after promoting and still use the label for its event:** at B = 1 a post-promotion query exists only in plans that had not queried, and those have constant events. Re-promotion and rollback happen after the first promotion, so they affect only `G_y` |
| Z1b | ACCEPTED | The budget is 0 after the query, so post-release play is open loop per branch. `G_y(s)` correctly maximises over open-loop paths with `a_s = 1` and switch costs counted from `a_{s−1} = 0` |
| Z1c | ACCEPTED | `P(S_τ=1|Y_τ=1) ≥ P(S_τ=1|Y_τ=0)` needs `e1 > e0`. Propagation with `ρ ≥ 0` preserves the order, and `q_t(y)` is affine increasing. Each schedule's value is nondecreasing in `(q_t)` because `a_t ≥ 0`, so the max is too |
| Z1d | ACCEPTED | |
| Z1e | ACCEPTED | `s_0 ≥ τ + d` is a time at which branch 1 also has its label, so π′ is feasible. Its IID risk stays 1/2. Its cost is `K − P_1G_1(s_0)` (or lower with re-optimised timing). The comparison needs only `P_1G_1(s_0) ≥ P_0G_0(s_0)`, which is exactly (W) at `(τ, s_0)` |
| Z1f | ACCEPTED | This holds for every λ ≥ 0 and therefore for every α ∈ [0,1]. Z1 does **not** need α ≤ 1/2, unlike N1 |

**Sharpening (new, PROVED via the same swap).** In (b) the replacement may promote in branch 1 at
`argmax_s G_1(s)` rather than at `s_0`. So the per-`s` condition (W) can be weakened to
**(W\*)**: for every τ, `max_s G_0(τ,s) > 0 ⇒ P_1(τ)·max_s G_1(τ,s) ≥ P_0(τ)·max_s G_0(τ,s)`.
Via N1, (W\*) says `g_{z1}(τ) ≥ g_{z0}(τ)` whenever `g_{z0}(τ) > −c`. That gives `2 max g_{z0} ≤ r_c`, so Γ = 0
immediately.

Data check: in the 865 random and targeted cells, W\* held in 766, and **none of those 766 had Γ > 0**. W\* is still not
necessary: odd-T alternation cells violate it and still have Γ = 0.

**Red team.**
1. **TP2 + (M) cells:** 3,000 formula cells, Γ > 0 in none. The 183 TP2 + (M) cells among the certified random cells
   all have Γ = 0.
2. **α > 1/2 with TP2:** none of the 14 TP2 scope cells has Γ > 0.
3. **Simultaneous promote-and-query:** the code confirms it is a promotion leaf.

**Routine vs specific.** The exchange argument itself is elementary. The specific content is the **label-weight
condition (W)**: a negative label is a "correlated coin" whose alternative probability differs from 1/2. TP2 + (M) ⇒ W is
a corollary.

**Label: PROVED** (TP2 + MLR + (M), or W, or W\*; any T, d, c, k, α; B = 1).

## 4. Theorem N1 (exact B = 1 formula, any HMM, α ≤ 1/2)

**Obligation ledger:**
- N1a: the classification and the risk of pure plans.
- N1b: the causal risk of a mixture is `Σ_τ[a_τ + max(c_τ, (b_τ+c_τ)/2)] + m`.
- N1c: the gain identity.
- N1d: the extreme-ray reduction.
- N1e: feasibility for α ≤ 1/2.
- N1f: each design gain is the best within its class.

| Step | Status | Note |
|---|---|---|
| N1a | ACCEPTED | As in Z1a, for any HMM. TP2 is not used anywhere in the classification |
| N1b | ACCEPTED, with an exposition GAP (MINOR) | **Public distinguishability holds.** At B = 1, every pre-promotion history reaching a query is `(0,0)^{τ−1}(0,1)`, so query nodes are indexed by τ alone. Private randomisation of τ is fine: each plan in the support reaches exactly one node, and the null's move at node τ affects only the mass there. **Pre-release and unconditional promotions:** unconditional promotions before τ never reach node τ. Plans that query at τ and then promote before release, or never promote, do reach node τ but contribute a p-independent amount (1 or 0). So `m` is additive. **Other times:** the null has no other move at B = 1 (one query per path), and non-queried labels affect neither the learner nor the risk. At node τ the risk is linear in p, so the max is at an endpoint: `p=0 ↦ a+c`, `p=1/2 ↦ a+(b+c)/2`. The proof's "nodes are publicly distinguishable" should spell out the history form `(0,0)^{τ−1}(0,1)` |
| N1c | ACCEPTED (an identity, not just an inequality) | By the tower property, `C_0 = Σ_{t<τ+d} q_t + P_0N_0 + P_1N_1`. So `g_{z0} = P_0G_0 − c`, `g_{z1} = P_1G_1 − c` and `g_both = P_0G_0 + P_1G_1 − c`. Hence `g_{z0} + g_{z1} = g_both − c` exactly, and the ray `b = c` is dominated by `a` because `c ≥ 0`. Checked in all 865 cells, with 0 failures |
| N1d | ACCEPTED | The per-node unit gauge ball `{a + max(c,(b+c)/2) ≤ 1}` has vertices `(1,0,0)`, `(0,2,0)`, `(0,0,1)` and `(0,1,1)`. A sum of gauges across nodes is an ℓ1-type sum, so the extreme points sit on one block. The IID gauge is linear, with c-only vertex `(0,0,2)` |
| N1e | ACCEPTED | The largest mass any ray needs is 2α ≤ 1. **The hypothesis α ≤ 1/2 is necessary:** N1 is wrong in 3/40 (Γ), 12/40 (V_IID) and 10/40 (V_causal) of the α ∈ {3/4, 9/10, 1} cells. Example: T=6, d=1, t01=1, t10=9/10, e=(1/10, 9/10), prior 0, c=k=0, α=3/4. N1 gives Γ = 2157/15625 ≈ 0.138, but the certified interval is Γ ∈ [0.0460, 0.0460] |
| N1f | ACCEPTED | `g_pre` must range over (i) promote at s with no prior query, with or without a query at s or later, and (ii) query at τ, then promote at `τ < s < τ+d`, including `τ + d > T`. My implementation enumerates exactly these, and they match the certificate |

**Numerical verification (independent implementation): 1,905 / 1,905** cells with α ≤ 1/2 match the certified V_IID,
V_causal and Γ. These include 509 Γ > 0 cells and about 1,390 non-TP2 cells (430 random or targeted, plus all 960 C3-grid
cells, since t01 = t10 = 1 violates TP2).

**Which part is ordinary, and which is specific.**
- The IID half is a fractional-knapsack / Neyman–Pearson LP: the best gain per unit of risk.
- The causal half is a one-move, two-endpoint minimax per public query node.
- The only causal-specific fact is that at B = 1 the null's single lever per node is `p_τ = 0`. This makes a `{Y_τ=0}`
  design cost risk 1 instead of 1/2.
- Once that is seen, the theorem is an elementary LP characterisation.

**Label: PROVED** for B = 1, α ≤ 1/2, any HMM, T, d, c, k. **FALSIFIED** for α > 1/2: the scope condition is necessary.

## 5. Theorem S1 (static ⇒ W, B = 1) and Lemma P

### S1

| Step | Status | Note |
|---|---|---|
| With static `q_t(y)` constant in `t ≠ τ`, `G_0 > 0 ⇒ q_0 > 1/2` | ACCEPTED | Every schedule has sum `Σ a_t(2q_0−1) − k·sw` with `sw ≥ 1` |
| `q_0 = E[e_S | Y_τ=0] ≤ E[e_S] = P_1` | ACCEPTED | `Cov(e_S, Y_τ) = Var(e_S) ≥ 0` |
| So `P_1 > 1/2 > P_0`, and with `G_1 ≥ G_0` the swap applies | GAP (MINOR) | `G_1 ≥ G_0` is used but not stated. It follows from Z1c with ρ = 1 |
| "Any prior" | ACCEPTED | The proof does not use the prior. Static means `S_1 = S_t` for all t |

**Red team.**
- 80 certified static cells: Γ = 0, and N1 matches.
- 3,000 formula-only static cells (T ≤ 6, d ≤ 3, extreme priors 0 and 1, emissions down to 1/100): Γ = 0 in all.

**Label: PROVED** (B = 1).

### Lemma P (promote only where `q(h) > 1/2`)

| Step | Status | Note |
|---|---|---|
| The replacement `(0, same query)` at s, then σ | ACCEPTED | The query set is unchanged, so the information is identical and the budget accounting is the same. If the old step was promote-and-query, the new step is a pre-promotion query. That is allowed, and it changes no information |
| Switch accounting | ACCEPTED | If `σ(s+1) = 1`, the old plan pays k at s and the new plan pays k at s+1, so they are equal. If `σ(s+1) = 0`, the new plan saves 2k. If s = T, it saves k |
| Risk | ACCEPTED | The new event is contained in the old one on every path. The probability of reaching h is unchanged, so the risk is ≤ **under every null** as well as under IID. The lemma therefore also holds for the causal Lagrangian, which the text does not claim |
| After the swap, the first promotion uses the decomposed game's optimal continuation | ACCEPTED | The cost is ≤ σ's |
| Termination | ACCEPTED | Promotions only move later, over a finite horizon |
| Notation | MINOR | `q(h)` should be `P_A(Y_s = 1 | h)`; the text writes `Y_t` |

**Label: PROVED.** **Routine**: this is a one-step improvement argument.

## 6. Lemma Zc (query-order coupling)

| Step | Status | Note |
|---|---|---|
| `g̃(z_1..z_B)` is well defined | ACCEPTED | With fixed delay, release order equals query order. Whether the j-th query exists, and when, depends only on released labels, which are a subset of `z_{<j}`. Unused coordinates are dummies |
| "Labels at distinct times are i.i.d. under the IID null, whatever the query times" | ACCEPTED | Under IID, the label at every time is an independent Ber(1/2) draw, so the j-th queried label is Ber(1/2) independent of the past whatever its time. Index the uniforms by query order: `U_j` is independent of everything before the j-th query. So the run on `Z*_j = 1{U_j ≤ 1/2}` has exactly the IID law, even though its query times differ from the null run's |
| Coupling `Z_j ≤ Z*_j` and monotonicity | ACCEPTED | `p_j` may read pending labels and public actions; that is the same argument as R5 |
| Mixtures | ACCEPTED | The bound holds per pure plan |
| "Causal risk **equals** IID risk" | ACCEPTED | ≤ from the coupling, ≥ because IID is in the family |

**Independent enumeration** (`wpA_zc_enum.py`, my own plan enumerator; `results/wpA_zc_enum.txt`).
- Configurations: `(T,B,d)` ∈ {(3,2,1), (3,2,2), (4,2,1), (3,3,1), (4,2,2), (4,3,1), (4,3,2), (5,2,1)}, 19,970 pure plans in all.
- The first four reproduce the earlier count of 1,233 plans exactly.
- **0** z-monotone plans and **0** tape-monotone plans have causal risk ≠ IID risk.

**New observation, correcting an informal claim in F1.** F1 reported that every tape-monotone plan was z-monotone.
**That fails at (4,3,1): 8 plans are tape-monotone but not z-monotone.** Example plan:
- query at 1;
- if `y_1 = 0`, skip step 2 and query at 3;
- if `y_1 = 1`, query at 2 and at 3;
- promote at 4 iff `Y_3 = 1`.

The tape event `{y_3 = 1}` is monotone. The z-event is not, because `z_2` is `Y_3` in one branch and `Y_2` in the other.

So the two classes are **incomparable**, and R′ genuinely needs the union `M_z ∪ M_tape`. In (4,3,1), 30 plans are
neither tape- nor z-monotone and still have causal risk = IID risk, so the union does not characterise causal safety.

**Routine vs specific.** Routine. Zc is the R5 coupling with uniforms indexed by query order (the "reward table" device
used in bandit lower bounds; `[unverified: Lattimore & Szepesvári 2020, §4.6, from memory]`).

**Label: PROVED.** Its "strictly enlarges" consequence is confirmed, and the classes are mutually incomparable.

## 7. Theorem C3 / corrected C3′ (alternation family)

**Rederivation via N1.** Setting: t01 = t10 = 1, e1 = 1−e, prior 1/2, B = 1, d = 1.
- `P_0 = P_1 = 1/2` at every τ.
- Each predicted-1 step is worth +g and each predicted-0 step −g, where `g = (1−2e)²`.
- Assume `g > 2k`. Then the open-loop branch value is `V_y(τ) = m_y(τ)(g−2k) + k·1[pred_y(T)=1]`.
- For even T: `V_0(1) = (T/2)(g−2k)+k`, `V_1(1) = (T/2−1)(g−2k)`, and `V_1(2) = (T/2−1)(g−2k)+k`.
- So `2g_{z0}(1) − g_both(1) = (g−k)/2 − c`, and `2g_{z0}(1) − 2g_{z1}(2) = g − 2k`.
- **Dominance of the other designs:**
  - `2g_{z0}(τ)` and `2g_{z1}(τ)` decrease as τ grows, by nesting of the predicted-1 sets.
  - `g_both(τ) ≤ ((T−τ)(g−2k)+k)/2 − c ≤ g_both(1)`.
  - `g_pre ≤ g_both(1)`. Any unconditional plan's branch gains are bounded by C3's branch bound `Ĝ_y` at its
    (post-promotion) query time, and it pays c.
- Hence **for even T ≥ 4: Γ = α·min{(g−k)/2 − c, g − 2k}**, given `g > 2k` and `c ≤ (g−k)/2`, and α ≤ 1/2 for N1.

**New error in the corrections file.** The claim that the C3′ formula "holds at T = 2" and that `T ≥ 4` is unnecessary is
**FALSE**.
- At T = 2, `τ = 2` is not a design (`τ + d > T`), so the `g − 2k` branch does not exist. Here `V_1(1) < 0` and
  `r_c = g_{z0}(1)`.
- So for T = 2: **Γ = α((g−k)/2 − c)**.
- Counterexample, using the corrections file's own instance (e = 1/4, k = 1/10, c = 0, α = 1/10, T = 2): the certified
  Γ is **3/400 = 0.0075**, but C3′ gives 1/200.
- This happens in 24/156 T = 2 hypothesis cells: every one with `g − 2k < (g−k)/2 − c`.
- With the T = 2 branch added, the formula matches **468/468** hypothesis cells (T ∈ {2,4,6}, all e, k, c and α ≤ 1/2).

**Corrected statement C3″:**
- even T ≥ 4, `g > 2k`, `c ≤ (g−k)/2`, `α ≤ 1/2`: `Γ = α·min{(g−k)/2 − c, g − 2k}`;
- T = 2: `Γ = α((g−k)/2 − c)`.

**Odd T, upgraded from NUMERICALLY VERIFIED to PROVED (B = 1, d = 1, α ≤ 1/2, any e, c, k ≥ 0).**
1. The y = 0 design at τ ≥ 2 has the predicted-1 set `{τ+1, τ+3, …}`. That is the same set as the y = 1 design at τ−1,
   which has one extra (predicted-0) step it may idle on. So `g_{z0}(τ) ≤ g_{z1}(τ−1)`.
2. At τ = 1 with odd T, the y = 0 sign pattern over `[2, T]` is `+−…+−`, and the y = 1 pattern is `−+…−+`.
   - Shifting any y = 0 schedule on `[2, T−1]` one step later gives a y = 1 schedule of equal sign-gain.
   - The shifted schedule can end at T, which saves the switch-back.
   - So `g_{z0}(1) ≤ g_{z1}(1)`.
3. Hence `2 max g_{z0} ≤ max 2g_{z1} ≤ r_c`, and Γ = 0 by N1.

This is consistent with 384/384 certified odd-T cells (T = 3, 5), all with Γ = 0.

**Routine vs specific.**
- The IID value `T/2 − α(2g_{z0}(1))` is a plain Neyman–Pearson / LP computation: promote on the more valuable label value
  with probability 2α.
- The causal-specific part is only the single endpoint move `p_1 = 0`, which turns that design's risk into 1. The value is
  then the better of two monotone alternatives: hedge with both branches, or use the positive label one step later.
- C3 is a **separation example**, not a standalone theorem, in agreement with WP G.

**Labels:**
- C3 as originally stated: FALSIFIED in `2k < g ≤ 3k − 2c` (WP G; confirmed).
- C3′: FALSIFIED at T = 2 when `g − 2k < (g−k)/2 − c` (new).
- **C3″: PROVED via N1 and NUMERICALLY VERIFIED** (468/468).
- Odd-T Γ = 0: **PROVED** via N1.

## 8. Issue list (two-axis severity)

| ID | Item | Category | Axis A / Axis B | Severity |
|---|---|---|---|---|
| A-1 | Corrections file: "C3′ holds at T = 2; T ≥ 4 unnecessary" | CASE_INCOMPLETE | INVALID / LOCAL | **CRITICAL**. Fix: C3″ |
| A-2 | N1 stated for α ≤ 1/2; the bound is sharp in the sense that the formula is false for α > 1/2 | — | none | Record as necessary scope |
| A-3 | F1: "every tape-monotone plan was z-monotone" | SCOPE_OVERCLAIM (descriptive) | OVERSTATED / COSMETIC | MINOR. False at (4,3,1) |
| A-4 | N1 step 2: the public-distinguishability argument is terse | UNPROVEN_SUBCLAIM | UNCLEAR / LOCAL | MINOR. State the history form `(0,0)^{τ−1}(0,1)` and the additivity of m |
| A-5 | S1: `G_1 ≥ G_0` used implicitly | HIDDEN_ASSUMPTION (derivable) | UNCLEAR / COSMETIC | MINOR |
| A-6 | Lemma P: `Y_t` should be `Y_s`; the lemma also holds under every null (unstated strengthening) | — | COSMETIC | MINOR |
| A-7 | Z1: W can be weakened to W\* (best-s), which is implied by N1 | — | UNDERSTATED / LOCAL | MINOR (improvement) |
| A-8 | Lemma R: "for every λ" is stronger than needed; Remark 2 is the minimal form | — | COSMETIC | MINOR |

There are no FATAL issues, and no open CRITICAL issue other than A-1, which already has a verified fix.

## 9. Final status table

| Result | Final label | Change vs previous documents |
|---|---|---|
| Lemma R | PROVED; routine corollary of LP duality, Kuhn and monotone coupling | none |
| Lemma R′ / Zc | PROVED; routine coupling variant | the "tape ⊂ z" observation is false; the classes are incomparable |
| Theorem Z1 (TP2 + (M), or W, or W\*) | PROVED | sharpened to W\* |
| Theorem N1 (B = 1, any HMM, α ≤ 1/2) | PROVED + NUMERICALLY VERIFIED (1,905/1,905, independent implementation) | α ≤ 1/2 shown necessary (FALSIFIED for α > 1/2) |
| Theorem S1 | PROVED (minor exposition gap) | none |
| Lemma P | PROVED; also holds under every null | none |
| C3′ (corrections file) | FALSIFIED at T = 2 | **new**. Replaced by C3″ (PROVED via N1; 468/468) |
| C3, odd T, Γ = 0 | PROVED via N1 (B = 1, d = 1, α ≤ 1/2) | **upgraded** from NUMERICALLY VERIFIED |

**Assessment.** Everything at B = 1 is now a complete, elementary characterisation: N1, with Z1, S1 and C3″ as
corollaries. None of it is deep. The contribution worth keeping is the **exact B = 1 premium formula** and the
**label-weight (correlated-coin) condition**. Lemma R and Zc are routine tools.

**Continue / pivot / stop:**
- **Continue** using these B = 1 results as a characterisation proposition.
- **Do not** present R, Zc, P or Z1 as standalone theorem contributions.
- Multi-label (B ≥ 2) results remain unproved and outside this audit.

## Lead verification (2026-11-10)

- C3′ T = 2 counterexample re-computed by the lead with `gamma_cell` (FCG-fast, exact): e = 1/4, k = 1/10, c = 0,
  α = 1/10, B = d = 1, t01 = t10 = 1, prior 1/2. **T = 2: Γ = 3/400** (= α((g−k)/2 − c); C3′ predicts 1/200).
  **T = 4: Γ = 1/200** (= α·min{(g−k)/2 − c, g−2k}). C3″ accepted.
- Cell lists for the targeted, scope and static runs were copied from the session scratchpad into
  `results/wpA_inputs/` so those runs are reproducible.
