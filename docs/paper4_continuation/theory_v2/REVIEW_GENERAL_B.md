# P2 review: GENERAL_B_PREMIUM.md (wpG)

**Date:** 2026-11-11. **Reviewer:** fresh-context Opus 5.5 subagent, adversarial, ARIS proof-checker method (obligation
ledger, 20-category taxonomy, two-axis severity, counterexample red team).
**review_independence: same-family. acceptance_status: provisional.** The ARIS external reviewer backends were not
used; this is a native same-family review. Nothing here is an independent acceptance.

Target: `docs/paper4_continuation/theory_v2/GENERAL_B_PREMIUM.md`. Background used: §0 of
`CAUSAL_SAFETY_PREMIUM_THEORY.md`, Lemma R / Zc / N1 in `THEOREM_PROOF_AUDIT.md`, and the exact tool `gamma_cell`.
Every proof step below was rederived from the primitive model (hidden chain at t = 1: `S_s = θ` at odd s, `1 − θ` at
even s; `Y_s ~ Ber(1−e)` iff `S_s = 1`; loss `q_t` vs `1 − q_t`; delay d; hard budget B; first-promotion risk; causal
null `p_t ∈ [0, 1/2]` adapted to the full generated history).

## 0. Verdict

| Claim | Status | Severity of open items |
|---|---|---|
| T1 recursion (+ cor. a, b) | **ACCEPTED** | MINOR (indexing of pre-release promotions) |
| Lemma A | **ACCEPTED** | none |
| RIPr consequence (LR bound) | **ACCEPTED** (LR part); KL part not re-checked | — |
| Prop L | **ACCEPTED with GAP** | MAJOR→fixable (UNJUSTIFIED + LOCAL): post-promotion re-timing not handled |
| Prop P | **ACCEPTED**; scope correctly stated as fixed calendar | MINOR (loose exponent; cell-count inconsistency; "fixed calendar" means calendar 1..B) |
| **Thm A** | **ACCEPTED with GAP** | MINOR: step 4 "every pure plan has a z-up-set event" is **false at T = 2B** (counterexample below); the conclusion survives. MINOR: `O(B/T)` hides `1/S_IID(α)`; α ≤ 1/2 unused |
| **Thm V** | **ACCEPTED** | MINOR (exposition) |
| ADAPT, as worded in the §0 table ("strictly beats **every** fixed calendar") | **WRONG** at one cell of the wpG family | CRITICAL (INVALID + LOCAL). The weaker claim "fixed calendars are not WLOG for V*_causal" is **CONFIRMED** |
| c = k = 0, d = 1 in Thms A and V | **REQUIRED by the proofs as written** (MISSING-ASSUMPTION check passes: the hypotheses are stated) | — |

No FATAL issue. One CRITICAL (a summary-table overclaim, local to ADAPT, not used by any theorem). The negative
characterisation (Thm A: Γ bounded in T; Thm V: ρ → 0 as B → ∞) survives intact.

## 1. Obligation ledger

| ID | Obligation | Used by | Result |
|---|---|---|---|
| O1 | Before first promotion the null's information on the calendar tree is a function of the label prefix h only | T1 | ACCEPTED: actions are all 0, the calendar is fixed, coins are private; extra null-generated noise (unqueried labels) cannot raise a sup over adapted p |
| O2 | `P_ν(promote) = Σ_h Q(h)x(h)`, linear in the per-node p | T1 | ACCEPTED |
| O3 | Backward induction; endpoint optimum p ∈ {0, 1/2} | T1 | ACCEPTED. 62/62 pattern leaves give `2^{−#ones}`; 1,500 random up-set functions give causal = IID (`rev2_genB_lemmas_v1.json`) |
| O4 | `D` moves by exactly ±1 per new label; at t = 1 the X_j are i.i.d. given θ **whatever the query times** (needs `e1 = 1 − e0`) | Lemma A, Thm A, Prop L | ACCEPTED |
| O5 | Lemma A(ii) `w_t > 0 ⇒ w_{t+1} ≤ 0` | Lemma A, Prop L, Thm V | ACCEPTED. Note: it holds for **any** query schedule (D changes by ≤ 1 per step, sign of `s_t` flips), which Prop L needs (O8) |
| O6 | Pair count ⌈(B−1)/2⌉ = ⌊B/2⌋ | Lemma A(iii) | ACCEPTED. Exhaustive: 80 (e, B) rows, B ≤ 16 (exact rationals B ≤ 10), max count = ⌊B/2⌋, 0 consecutive positives |
| O7 | `max_y P_A/Q* ≤ (2(1−e))^{⌊B/2⌋}` | Prop P | ACCEPTED (80/80 rows) |
| O8 | Prop L upper bound: for t > B the gain is `±m(D_B)` on alternate steps | Prop L, Thm A step 5 | **GAP** (see §2.2) |
| O9 | Prop P algebra | Prop P | ACCEPTED; the proof actually gives exponent ⌈B/2⌉ (stronger) |
| O10 | Aligned learner is feasible: one query per step, hard budget B, d = 1, `τ_i ≤ 2i − 1`, labels released by 2B ≤ T | Thm A | ACCEPTED |
| O11 | `|D_i|` is a coordinatewise nondecreasing function of z | Thm A step 2 | ACCEPTED (induction rederived; parity `|D_i| ≡ i` excludes the bad case) |
| O12 | Each pure plan of the step-4 construction has a z-up-set promotion event | Thm A step 4 | **FALSE at T = 2B**, TRUE for T ≥ 2B + 1 (§2.3) |
| O13 | Lemma Zc applies (query order indexes the uniforms; d fixed so release order = query order) | Thm A step 4 | ACCEPTED for T ≥ 2B + 1. Exact independent recursion on the z-tree: causal risk = IID risk ≤ α in 220/220 cells with T > 2B |
| O14 | Subtraction in step 5: `⌈(T−B)/2⌉ − ⌊(T−2B+1)/2⌋ ≤ ⌈B/2⌉ ≤ B/2 + 1` and `S_IID ≤ 1 − 2e` | Thm A | ACCEPTED (case check on parities of B and T − B) |
| O15 | `E_n` is a nonnegative test supermartingale under every causal null | Thm V | ACCEPTED (§2.4) |
| O16 | Ville, Wald with overshoot, Hoeffding constants | Thm V | ACCEPTED (§2.4) |
| O17 | `VOI_IID ≤ VOI_full = Σ_t E(w_t)^+` | Thm V | ACCEPTED (CAL-t1 at α = 1, or Jensen + O5 directly); 268/268 cells |
| O18 | `VOI_full ≥ (T−1)g/2` | Thm V | ACCEPTED; 268/268 cells |

## 2. Per-claim findings

### 2.1 T1 and Lemma A — ACCEPTED

Rederived. One MINOR indexing point: the text puts a promotion at `s ∈ [τ_j, τ_{j+1})` at the depth-j node, which
includes label j. With d ≥ 1 that label is generated but not yet released at s = τ_j. The recursion is still exact:
such a promotion has `x(h0) = x(h1)`, and the recursion with an arbitrary x on the tree is exact. State this.

### 2.2 Prop L — ACCEPTED with GAP (UNJUSTIFIED + LOCAL, fixable)

The upper bound writes `w_t = s_t m(D_B)·sign` for t > B. That holds only if every promoted plan has all B labels
released by B + 1. But the calendar class lets the learner do "anything" after promotion, so a plan promoted at σ < B
may query its remaining labels later. **Fix** (rederived):
- (i) O5 holds for any schedule, so (B, T] still contains at most ⌈(T−B)/2⌉ positive steps.
- (ii) On a positive step `(w_t)^+ = m(D_{n_t}) ≤ E[m(D_full) | F_t]`, by Jensen (m is |martingale| × const).
- (iii) By O4, `(θ, pre-promotion calendar labels, later X's)` has the same law as on the calendar. So
  `E[1{σ≤T} m(D_full)] = Σ_y P_A(y) m(D_B(y)) f_σ(y)`.

The conclusion is unchanged. Thm A step 5 inherits this gap and this fix. No numerical violation: the IID-side Prop L
bounds hold in 268/268 certified cells.

### 2.3 Theorem A — ACCEPTED with GAP

**Feasibility (O10), monotone encoding (O11) and same laws: ACCEPTED.**
- The plan uses exactly B queries, one per step.
- `D_{i−1}` is visible at `τ_{i−1} + 1` (d = 1).
- `τ_B ≤ 2B − 1`.

**Counterexample to step 4 as written (O12).** The rule promotes at the first `t ≥ 2B` with `w_t > 0`. At T = 2B
only t = 2B is available, and `w_{2B} > 0 ⇔ D_B < 0`. So the event is `{U ≤ f*(|D_B|)} ∩ {D_B < 0}`, which is not a
z-up-set.

Exact example (`aligned_eval`, independent of `gamma_cell`): T = 2, B = 1, e = 1/20, α = 1/20.
- `f* ≡ 1/20`, and the event is `{U ≤ 1/20, z_1 = 0}`.
- **IID risk = 1/40, causal risk = 1/20**, so causal ≠ IID.
- In all 48/48 red-team cells with T = 2B, causal risk ≠ IID risk; in all 220/220 cells with T > 2B they are equal.

**Why the theorem survives.** The event is a subset of the up-set `{U ≤ f*(|D_B|)}`. Causal risk is monotone in the
event, so causal risk ≤ E_IID f* ≤ α and the plan is still safe. Also, at T = 2B the claimed VOI bound
`⌊(T−2B+1)/2⌋S = 0` is trivial anyway.

**Corrected statement of step 4.** For T ≥ 2B + 1 the event is the up-set `{U ≤ f*(|D_B|)·1{|D_B| ≥ 1}}`, so Zc
gives causal risk = IID risk. For T = 2B use never-promote, or note the subset argument.

**Other points.**
- *Hypothesis α ≤ 1/2 is unused* (`S_IID ≤ 1 − 2e` holds for all α). MINOR.
- *Rate.* `ρ(T) = O(B/T)` is OVERSTATED: the constant is `1/S_IID(α)`, and S_IID can be about
  `α(2(1−e))^B g/2`. Corrected: `ρ(T) ≤ [(1−2e)⌊B/2⌋ + ⌈B/2⌉S_IID] / (⌊(T−B)/2⌋ S_IID)`, so ρ = O(1/T) at fixed
  (B, α, e). MINOR.
- *Sharper form proved by the same steps* (no violations): `Γ(T) ≤ (1−2e)⌊B/2⌋ + (⌈(T−B)/2⌉ − ⌊(T−2B+1)/2⌋)S_IID ≤ (1−2e)⌊B/2⌋ + ⌈B/2⌉ S_IID`.
  - The largest observed ratio Γ / (this bound) is 0.5, at T = 2, B = 1, e = α = 1/20.
  - At B = 1 and odd T it gives Γ ≤ 0, and the certificate gives Γ = 0 in all 32 such cells, consistent with C3′.
- *The aligned plan is often exactly optimal.* Its exact VOI equals the certified VOI_causal in 169/268 cells
  (161 at B ≤ 3, 8 at B = 4).
- *Hypotheses c = k = 0, d = 1, t = 1, symmetric emissions, prior 1/2 are all used:*
  - k = 0: the post-promotion gain is `m(D_B)` on every right-sign step only with free switching;
  - c = 0: the Prop L upper bound ignores query costs;
  - d = 1: the parity choice at `τ_{i−1} + 1`, and `τ_i ≤ 2i − 1`;
  - t = 1 and symmetric emissions: O4 and CAL-t1.

  They are stated in the theorem and in §7. Extension to d > 1 (slack about (d+1)B) is plausible but not proved.

### 2.4 Theorem V — ACCEPTED

- **Filtration.** Take `G_i` = the full generated history before `Y_i`: past labels including pending ones, public
  actions, and the null's own randomness. The test runs on the **fixed calendar 1..B**, so query times are not
  adaptive. Delay affects only when the learner may act (t ≥ τ + 1), not the supermartingale property. The step
  `E[φ(Y_i) | G_i] = 1 + (1−2e)(2p_i − 1) ≤ 1` holds for every adapted `p_i ∈ [0, 1/2]`, whatever the null sees.
  φ ≥ 2e > 0 and the average of two test supermartingales is one. Ville applies, and the promotion event is a subset
  of the Ville event, so the policy is causal-feasible.
- **Lost gain.** For τ < t < σ, `w_t ≤ 0` by the definition of σ. On [1, τ] there are at most ⌊τ/2⌋ positive steps
  (O5).
- **Wald.** The odd-label log-wealth is a random walk with mean I_e > 0, so E N < ∞. The overshoot is at most
  `log 2(1−e)`, so `E N ≤ log(4(1−e)/α)/I_e` and `τ ≤ 2N`.
- **Hoeffding.** There are ≥ ⌊B/2⌋ odd (resp. even) labels in 1..B, the increment range is exactly L, and crossing
  by label count ⌊B/2⌋ implies τ ≤ B.
- **Denominator.** `E(w_t)^+ = ½E m(D_{n_t})` by θ-symmetry, and this is nondecreasing in n.
- **Exact per-cell checks, 268/268:**
  - betting policy causal risk ≤ α (independent exact recursion);
  - `E_A[τ; τ ≤ B] ≤ K_α`;
  - `P_A(τ > B) ≤ π_B`;
  - `Γ_lo ≤ VOI_full − VOI_test`;
  - `VOI_IID ≤ VOI_full`;
  - `VOI_full ≥ (T−1)g/2`.
- **Caveat (not an error).** In the red-team range the test fires in only 12/240 B ≤ 3 cells, and the bound is at
  least about 11× Γ (max Γ/bound = 0.090). Thm V is asymptotic, as §7 says.

### 2.5 Prop P — ACCEPTED; scope is stated

The statement and §0 both say "fixed calendar". More precisely it is the calendar **1..B**, and ρ_∞^cal is a
T → ∞ limit inside that class, which is an upper bound on the true premium (ADAPT, Thm A). §0's "Lead hypothesis"
row and §7 say that it does not control V*_causal. Recommend writing "calendar 1..B" in place of "fixed calendar".

- **Sharper exponent.** The proof gives `1 − 2/((1−2e)(2(1−e))^{⌈B/2⌉})`, which is stronger than ⌊B/2⌋ for odd B.
  0 violations in 200 static cells (e ∈ {1/20, 1/10, 1/4, 2/5}, B ≤ 10, α = 2^{1−B−k}, k ∈ {0,1,2,4,7}); 100 of these
  are non-vacuous. The minimum margin is 0.013, at e = 1/20, B = 9, α = 1/256 (ρ_∞ = 0.923 ≥ 0.910).
- **B = 2 closed form.** `S_causal = (3/2)αg` is reproduced (12/12).
- **Cell-count inconsistency (MINOR).** §0 says 222 cells, §3 says 222, §8 says 186. Re-counting
  `wpG_static_t1_v1.json` with α ≤ 2^{1−B} gives 231 cells (including B = 1) and 0 violations.

### 2.6 ADAPT — WRONG as worded; the weaker claim is CONFIRMED

`rev2_genB_adapt.py` enumerates **every** pre-promotion calendar of ≤ B times in 1..T−1. The post-promotion learner
queries as early as possible, which is optimal at t = 1. It solves the T1-linearised LP (float HiGHS) and compares the
result with the exact `gamma_cell` value. It reproduces wpG_lib's calendar-1..B values in all 7 cells.

| Cell (e, α) | Calendars | Best calendar | best cal V_causal | exact V*_causal | Strict? |
|---|---|---|---|---|---|
| T=6, B=2 (1/10, 1/20) | 16 | (1,2) | 2.904 | 2.904 | no (expected: T−B small) |
| T=8, B=2 (1/10, 1/20) | 29 | (1,2) | 3.856 | 3.840 | **yes**, gap 0.016 |
| T=10, B=2 (1/10, 1/20) | 46 | (1,2) | 4.808 | 4.776 | yes, 0.032 |
| T=8, B=2 (1/4, 1/10) | 29 | (1,2) | 3.8875 | 3.875 | yes, 0.0125 |
| T=8, B=2 (1/20, 1/4) | 29 | (1,2) | 3.08875 | 2.9875 | yes, 0.101 |
| **T=9, B=3 (1/10, 1/20)** | 93 | **(1,3,5)** | **4.26704** | **4.26704** | **no** |
| T=10, B=3 (1/10, 1/20) | 130 | (1,2,4) | 4.7512 | 4.7088 | yes, 0.042 |

**Counterexample to "adaptive timing strictly beats every fixed calendar once T − B is large".** At T = 9, B = 3,
e = 1/10, α = 1/20 (T − B = 6), the fixed calendar (1,3,5) attains the exact V*_causal = 4.26704. The exact
Γ = 0.11648 is the one wpG reports; calendar 1..B gives 0.15744. The sentence in §2 "calendar > exact in every checked
cell with T − B ≥ 6" is true only for calendar **1..B**.

**Corrected ADAPT.** The best fixed calendar is not WLOG for V*_causal. Exact certified witnesses:
- (T, B) = (8, 2) and (10, 2) at (e, α) = (1/10, 1/20): exact V*_causal is strictly below every one of the
  29 / 46 fixed calendars;
- likewise (10, 3);
- and the calendar 1..B is strictly suboptimal in every checked cell with T − B ≥ 6.

The float-LP gaps (≥ 0.0125) are far above the 1e-10 tolerance, but the calendar side is float, not certified.
Classification: INVALID + LOCAL (no theorem depends on it) = CRITICAL for the claim text only.

## 3. Red team (exact certified cells)

`rev2_genB_cells.py`, `gamma_cell(T, B, d=1, t=1, e, 1−e, prior 1/2, c=0, k=0, α)`:
- B = 1, 2, 3: T = 2B..3B+2, all 16 (e, α) in {1/20, 1/10, 1/4, 2/5} × {1/20, 1/10, 1/4, 1/2}, giving 240 cells;
- B = 4: T = 8..14 × 4 (e, α) pairs, giving 28 cells.

**268 / 268 certified** (FCG-fast or IID-optimum-safe). The largest certificate width is 5e-13. Γ > 0 is certified in
236 cells.

| Check (per cell) | Violations |
|---|---|
| Prop L IID lower `⌊(T−B)/2⌋S ≤ VOI_IID` / upper | 0 / 0 |
| Thm A stated bound, final `(1−2e)(B+1)`, sharper form | 0 / 0 / 0 |
| Thm A `VOI_causal ≥ ⌊(T−2B+1)/2⌋S` | 0 |
| aligned plan: unsafe / VOI below claim / VOI above certificate | 0 / 0 / 0 |
| Thm V bound; lost-gain; `VOI_IID ≤ VOI_full`; `E τ ≤ K_α`; `P(τ>B) ≤ π_B`; denominator; betting unsafe | 0 each |

Exact Γ at e = 1/10, α = 1/20, B = 4, for T = 8..14: 0.2365, 0.3968, 0.3005, 0.4198, 0.3149, 0.4198, 0.3149. It is
bounded and period-2 in T, as Thm A predicts, and matches wpG's T = 10..12 values. ρ there falls from 0.63 (T = 9) to
0.30 (T = 14). The largest ρ in the red team is 0.63.

## 4. Corrected statements (minimal)

- **Thm A.** t = 1, d = 1, c = k = 0, symmetric emissions, prior 1/2, any α ∈ (0, 1], T ≥ 2B:
  `Γ(T) ≤ (1−2e)⌊B/2⌋ + ⌈B/2⌉ S_IID(α) ≤ (1−2e)B`, and
  `ρ(T) ≤ [(1−2e)⌊B/2⌋ + ⌈B/2⌉S_IID(α)] / (⌊(T−B)/2⌋ S_IID(α))`.
  The proof's step 4 should be restricted to T ≥ 2B + 1; T = 2B is trivial.
- **Prop L.** Unchanged, with the post-promotion re-timing fix of §2.2.
- **Prop P.** Calendar 1..B, α ≤ 2^{1−B}: `ρ_∞^cal ≥ 1 − 2/((1−2e)(2(1−e))^{⌈B/2⌉})`.
- **ADAPT.** As corrected in §2.6.

## 5. Reproduction

`uv run --no-sync python scripts/paper4_continuation/theory_v2/<script> <out> …`. Outputs are refuse-overwrite JSON in
`docs/paper4_continuation/theory_v2/results/`. One solver process was used at a time, at `nice 10`.

| Script | Output |
|---|---|
| `rev2_genB_lib.py` | library: independent exact evaluators for the aligned plan, the betting plan, S_IID and tree risk |
| `rev2_genB_cells.py … 1,2,3 all` | `rev2_genB_cells_B123_v1.json` (240 cells) |
| `rev2_genB_cells.py … 4 1/10:1/20,1/4:1/4,2/5:1/2,1/20:1/10` | `rev2_genB_cells_B4_v1.json` (28 cells) |
| `rev2_genB_lemmas.py` | `rev2_genB_lemmas_v1.json` (Lemma A, LR, T1, Prop P) |
| `rev2_genB_adapt.py` | `rev2_genB_adapt_v1.json` (all-calendar ADAPT check) |

**Limitations.**
- The Prop P and ADAPT calendar LPs are float. HiGHS rejected the 1e-11 tolerance in the lemmas script and fell back
  to its defaults, which is irrelevant at the observed margins of ≥ 0.013.
- The KL claim `KL(P_A‖Q*) ≤ B I_e/2` was not re-checked.
- B ≤ 4 only in the exact red team.
- Same-family review.

**Assessment: CONTINUE with corrections.** No theorem is invalidated. Fix the ADAPT wording, the T = 2B case of
Thm A step 4, and the Prop L re-timing gap.
