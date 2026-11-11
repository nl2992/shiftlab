# Reviewer 1 (mathematical correctness): Theorem SP1 and corollaries

`review_independence: same-family` · `acceptance_status: provisional`

**Date:** 2026-11-10. **Target:** `STOCHASTIC_POSITIVE_PREMIUM.md`, covering Lemmas S, Pre, W and K, Theorem SP1,
Corollaries SP1-A to SP1-E, §3 (C2d) and Proposition C3 (the continuity modulus).
**Method:** ARIS proof-checker. Each step was rebuilt from the primitive model (`CAUSAL_SAFETY_PREMIUM_THEORY.md` §0)
and Theorem N1 (§F5, accepted in `THEOREM_PROOF_AUDIT.md` §4). The checks were an obligation ledger, a Phase 1.5
counterexample red team and exact computation.
The reviewer is a model of the same family (Claude). No ARIS external reviewer was available, so this is a native
fresh-context review.

## 0. Verdict

**The core result is correct.** Theorem SP1 and Lemmas S, Pre, W and K are ACCEPTED, with minor exposition gaps.
Corollaries SP1-A, SP1-B, SP1-C (as a statement) and SP1-E, and Proposition C3 are ACCEPTED.

**One stated result is WRONG.** SP1-D, first bullet: "If T−d is even, **or g ≤ 2k**, then Γ = 0". This fails at
T = d+1 whenever `k < g ≤ 2k` and `2c < g−k`. The certified counterexample is in §3.
The theorem itself is correct in this case. Only the corollary's case split and the line
`Δ = (|P_0|−|P_1|)(g−2k)⁺` in its proof are wrong, because that line ignores `P_1 = ∅`.

**Minor numerical or wording errors in the discussion:**
- the SP1-C worked example;
- the T→∞ "average" remark;
- the delay-factor interval in §3;
- "largest start" in Lemma W.

None of these affects SP1.

**Recommendation:** fix SP1-D (corrected statement in §3), fix the minor items, and leave SP1 as PROVED. The
result still rests on N1 (α ≤ 1/2), which is accepted elsewhere.

## 1. Obligation ledger

| ID | Obligation | Where used | Status |
|---|---|---|---|
| O1 | `P(Y_t=1)=1/2` for all t; pre-release `q_t = 1/2` | Lemma S(i)(ii), Pre, label weights `P_0=P_1=1/2` | ACCEPTED. Needs prior 1/2 and `e1 = 1−e` (both stated) |
| O2 | Post-release weight `w_y(j) = (2y−1)g ρ^j`, with j ranging over `d..T−τ` (release at τ+d conditions the action at τ+d) | Lemma S(iii) | ACCEPTED. The timing convention is a model fact, confirmed by gamma_cell agreement (§4); it is not derivable from the text alone |
| O3 | Every pre-release or unconditional-promotion plan has gain ≤ that of a design with the same τ | Lemma Pre | ACCEPTED (§2.1) |
| O4 | `max_M G_y(M) = k + max over nonempty block sets of Σ(v_b − 2k)` | Lemma W, step 1 | ACCEPTED. Free final switch: there is no switch after T, and τ ≥ 1 gives M ≤ T−1 |
| O5 | `v_b ≤ a_{start}` for a block starting at a positive step; WLOG blocks start at positive steps | Lemma W, step 2 | ACCEPTED, with GAP-minor: the proof does not say that a lone negative-singleton block is deleted rather than "trimmed" (deleting it is better, given `P_y ≠ ∅`) |
| O6 | All `a_j ≤ 2k` ⇒ best is the singleton at `j*` | Lemma W | ACCEPTED. **Typo:** the text says "largest start"; it must be the smallest start, i.e. the largest weight |
| O7 | Both-branch bound at a common window end M | Lemma K | ACCEPTED, with GAP-minor (§2.2) |
| O8 | (★) from N1 + Pre: `Γ/α = (Ḡ_0−2c − max{0, Ḡ_1−2c, max_τ(G_0⁺+G_1⁺)/2 − c})⁺` | SP1 | ACCEPTED. `max(g_z0, g_z1, g_both)(τ) = (G_0⁺+G_1⁺)/2 − c` whenever one of the G's is positive; otherwise the 0 in r_c absorbs it |
| O9 | 5-term min reduces to 3 terms under `(·)⁺` | SP1, step 1 | ACCEPTED. Also implicitly needs: if `Ḡ_0 ≤ 0`, both sides are 0 (true because c ≥ 0) |
| O10 | Primitive geometric forms and the alternating identity | SP1, step 3 | ACCEPTED. Exact equality with the Lemma-W sums in 1,592/1,592 cells (§4) |
| O11 | Even d ⇒ `Ḡ_0 ≤ Ḡ_1` | SP1-A | ACCEPTED. T = d+1 (`P_0 = ∅`, so `Ḡ_0 = −a_d − k < 0`) and T ≤ d (no release) are covered |
| O12 | `Ḡ_0 ≥ a_d − k`, `Δ ≥ a_d − a_{d+1}`, monotone in (Ḡ_0, Δ), exact when `a_{d+1} ≤ 2k` | SP1-B | ACCEPTED. The equality case with `a_{d+1} ≤ k` (so `Ḡ_1 ≤ 0` and `Δ = Ḡ_0 = a_d − k`) is not spelled out, but the L-min still equals `(a_d−k)/2 − c`. Checked: 891/891 exact equalities |
| O13 | SP1-C algebra | SP1-C | ACCEPTED. "Open set" is relative to c, k ≥ 0 and α ≤ 1/2 |
| O14 | r = 1 case split | SP1-D | **WRONG** at T = d+1 (§3) |
| O15 | k = 0: `Ḡ_1 ≥ 0` ⇒ `Δ ≤ Ḡ_0`, so the min is `Δ/2 − c` | SP1-E | ACCEPTED |
| O16 | T-saturation for `T ≥ max(J, d+1)+1` | §3 | ACCEPTED. Exact check 1,023/1,023 |
| O17 | Lipschitz modulus `8α(T(1+k)+c)·TVB` | Prop. C3 | ACCEPTED (§2.4) |
| O18 | Hidden assumptions | all | See §2.5 |

## 2. Reconstruction notes on the focal questions

### 2.1 Lemma Pre: promote-then-query, and pre-release promotion with rollback

Take any plan whose first promotion occurs before its label is released. This includes:
- promote at s, then query at τ ≥ s;
- query at τ, then promote at `s ∈ (τ, τ+d)`;
- either of these with rollbacks and re-promotions, before or after the release.

Its path splits into an open-loop prefix on `[1, τ+d−1]` and a branch-y suffix.

1. **Prefix weights are 0** by O1, so the prefix contributes `−k·(switches)` only.
2. **Replace the prefix by all-zeros.** This loses no weight. The suffix is unchanged. The boundary switch at τ+d
   costs `1[x_{τ+d}=1]`, which is ≤ the switches the original prefix-plus-boundary needed to reach `x_{τ+d}` from
   `A_0 = 0`.
3. **Classify the result.** It is a z0, z1 or both design with the same τ, or never-promote (gain −c).
4. **Compare ratios.** Since `g_z1 ≤ max(0, 2g_z1)`, every ratio in r_c dominates `g_pre`.
5. **No release by T.** Then the gain is `−k·sw − c·1[q] ≤ 0`.

The lemma is correct. My brute-force DP enumerates every promote-before-release plan independently, without using
Pre. It reproduced SP1 exactly in 3,000 + 2,420 cells.

### 2.2 Single-step on/off versus holding across a bad step; the T-end

Holding the challenger from j to j+2 across the negative step j+1 is a block `[j, j+2]`. Its value is
`a_j − a_{j+1} + a_{j+2} − 2k`, against two singletons at `a_j + a_{j+2} − 4k`.

- Holding wins iff `a_{j+1} < 2k`.
- But `a_{j+2}` is covered only if `a_{j+2} > 2k`, and then `a_{j+1} ≥ a_{j+2} > 2k`.
- If `a_{j+2} ≤ 2k`, holding adds `a_{j+2} − a_{j+1} ≤ 0` to the singleton at j.

So the k-threshold logic is right, and the general bound `v_b ≤ a_s` (O5) covers every merge. With r < 1 this holds
for every alternating pattern. With r = 1 merging ties, and the value is unchanged.

**T-end.** The free final switch is worth k exactly once. Moving it to an extra uncovered singleton `J+2` with
`k < a_{J+2} ≤ 2k` changes the value by `a_{J+2} − 2k ≤ 0`, so `k + Σ(a_j−2k)⁺` is right.

**Lemma K gap (minor).** Cases (B1)/(B2) silently use the facts below, which hold for each branch's optimal set at M
(WLOG):
- every block starts at that branch's positive step;
- so y's last block starts at `s′ ≤ M−2`, with the parity of M;
- y′'s last block starts at `M−1` (B1) or at `≤ M−3` (B2).

With these facts the case split is exhaustive. The truncation bounds use only `G_y(M′) ≤ Ḡ_y` for the truncated sets,
so the recursion does not need optimality at M−2. Lower bound: `M = max(m_0, m_1)` is valid. I rebuilt every case
and found no error.

### 2.3 Both-branch hedge and the min

Substituting Lemma K into (★) when `Ḡ_0, Ḡ_1 > 0` gives five terms:
- `Ḡ_0 − 2c`;
- `Δ`;
- `Ḡ_0/2 − c`;
- `Ḡ_0 − Ḡ_1/2 − c`;
- `(Δ+k)/2 − c`.

Two of them are redundant under `(·)⁺`:
- the 1st is ≥ the 3rd once the 3rd is ≥ 0;
- the 4th equals the 3rd plus `Δ/2`.

**Each of the three remaining terms binds somewhere.** Dropping any one of them is refuted by the certified intervals:

| Variant | Certified cells that exclude it |
|---|---|
| no hedge term | 243 |
| no Δ term | 275 |
| hedge without `+k` | 265 |

### 2.4 Continuity modulus (Prop. C3)

1. **Gain as a path function.** Each N1 gain is a max over a θ-independent class of pure plans of `E_θ h_π(Y_{1:T})`,
   with `h = Σ_t A_t(2Y_t−1) − c·n_q − k·sw`. The tower property applies because actions depend only on queried
   labels.
2. **Bound on h.** `|h| ≤ T + c + kT`.
3. **One gain.** `|ΔE h| ≤ 2 sup|h|·TV`, and the step-by-step maximal coupling gives `TV ≤ TVB` (union bound over
   the first disagreement).
4. **Max and Γ.** A max of such gains keeps the constant. Then
   `|Δ(2X − Y)⁺| ≤ 2|ΔX| + |ΔY| ≤ 4·sup|Δg| ≤ 8(T(1+k)+c)·TVB`.

The derivation is correct. It needs N1 at both θ and θ′, so α ≤ 1/2 and θ′ in the model class (e0 < 1/2 < e1).
Exact check on asymmetric perturbations: 400/400 within the bound.

### 2.5 Hidden assumptions

| Assumption | Status |
|---|---|
| T ≥ d+1 | Stated. For T ≤ d, Γ = 0 trivially, so SP1-A's "every T" is fine |
| α ≤ 1/2 | Inherited from N1 and necessary (N1 fails for α > 1/2, per the WP A audit) |
| r ∈ (0, 1] | r = 0 gives Γ = 0, consistent with the formula |
| Stationarity and symmetry | Used essentially in O1 (zero pre-release weights and `P_0 = P_1`). Without them Lemma Pre fails and the formula no longer applies; the continuity modulus is the only bridge, as the document says |
| c, k ≥ 0 | Used in O9 and Lemma Pre |
| B = 1 | Used throughout |
| Timing convention (O2) | Model-specific. A one-step-later release convention would shift every parity |
| `J = ∞` convention | Also needed for r = 1 with `g > 2k`, not only for k = 0 (wording) |

## 3. Counterexamples and corrected statements

All values are certified by `gamma_cell(..., force_fcg=True)` with `L = U`
(`results/rev1_sp1_witness_v1.json`).

**CE-R1 (SP1-D, first bullet: WRONG).**

| Cell (r = 1, B = 1) | SP1-D bullet 1 | Certified Γ |
|---|---|---|
| T=2, d=1, e=1/10 (g=16/25), c=0, k=8/25 (g = 2k), α=1/2 | 0 | **2/25** |
| T=2, d=1, e=1/10, c=0, k=2/5 (g < 2k), α=1/10 | 0 | **3/250** |
| T=4, d=3, e=1/4, c=0, k=1001/8000, α=1/2 | 0 | **999/32000** |

In all 72 structured cells of this kind (T = d+1, `k < g ≤ 2k`), the certified `Γ_lo > 0`.

*Cause.* At T = d+1, `P_1 = ∅`, so `Ḡ_1 = −∞` and `Δ = Ḡ_0 = g−k`, not `(|P_0|−|P_1|)(g−2k)⁺ = 0`.
SP1-D's own third bullet already gives `α((g−k)/2 − c)⁺` at T = d+1, so the first and third bullets contradict each
other.

*Corrected SP1-D* (r = 1, d odd):
- **(i)** At T = d+1: `Γ = α((g−k)/2 − c)⁺` for all g, k, c.
- **(ii)** At T ≥ d+2: if T−d is even or g ≤ 2k, then Γ = 0.
- **(iii)** At T ≥ d+2 with T−d odd and g > 2k: as stated.

The summary-table entry "Γ > 0 iff T−d odd, g > 2k, 2c < g−k" should become:
"Γ > 0 iff (T = d+1 and g > k+2c) or (T ≥ d+2, T−d odd, g > 2k, 2c < g−k)".
The odd-T Γ = 0 statement for d = 1 (T ≥ 3) and C3″ at T = 2 are unaffected; C3″ now holds without g > 2k.

**CE-R2 (SP1-C worked example: numerical slip).**
- Cell: t = 3/4, e = 1/10, c = 1/100, k = 1/50, α = 1/10.
- The bound is `α·L = α·min{0.14, 0.16, 0.08} = 0.008`. The document says "Γ ≥ 0.01".
- The exact T = 3 value is Γ = **1/125 = 0.008** (certified), so the stated 0.01 contradicts the document's own
  table. The bound is attained at T = 3.
- Correction: "the bound gives Γ ≥ 0.008, attained at T = 3".

**CE-R3 (§3 delay-factor interval: wrong for finite T).**
- With k = 0, `Γ/α + c = g r^d·(1 − ρ^{T−d})/(2(1+r))`. Over T ≥ d+1 the factor ranges over **`[(1−r)/2, 1/2]`**,
  with the low end at T = d+2.
- `1/(2(1+r))` is only the T→∞ limit, and the text also omits g.
- Exact violations: 35/74. Example: T=5, d=1, t=9/10, e=49/100 gives factor 41/250 < 5/18.

**CE-R4 (§3 limit remark: minor).**
- At r = 1 the two parity values are `(g/2 − c)⁺` and 0. Their average is `g/4 − c/2`, not `g/4 − c`.
- The statement is only correct for c = 0.

**CE-R5 (monotonicity in d for k > 0: the qualifier is needed).** The document labels this "observed, not proved". At
fixed T it fails near the boundary T = d+1:

| Cell | Γ at d | Γ at d+2 |
|---|---|---|
| T=6, t=1, e=1/4, c=0, k=1/8, α=1/20 | Γ(d=3) = 0 | Γ(d=5) = 1/320 |
| T=8, t=99/100, e=1/4, c=1/100, k=1/10, α=1/4 | Γ(d=5) ≈ 0.005388 | Γ(d=7) ≈ 0.012129 |

Both are certified. Exact search: 22/1,206 violations, all with T = (d+2)+1.

In the exact formula search at T ∈ {40, 41}, there were 0/2,016 violations. So the observation should be stated for
T ≥ d+4 (or large T). The k = 0 claim was checked exactly: 201/201.

## 4. Red-team record (Phase 1.5)

The independent implementation is `scripts/paper4_continuation/theory_v2/rev1_sp1_lib.py`, which imports no `wpC_*`
code. It provides:
- **`sp1_formula`:** SP1 as stated, built from Lemma W sums.
- **`n1_brute`:** N1 with every design gain, including g_pre, computed by exact Fraction DP from the primitive HMM by
  forward filtering. It does not use Lemmas S, W, K or Pre.

**Certified run** (`rev1_sp1_redteam.py`; outputs `results/rev1_sp1_redteam_w{0..3}.json` (seed 1, 420 cells) and
`results/rev1_sp1_redteam_s2_w{0..2}.json` (seed 2, 2,000 cells)):
- **Cells:** 2,420 adversarial cells:
  - k at, and ±0.1 % from, `g r^j/2` for j = d, d+1, d+2, and `k = a_d`;
  - c at, and just below, `(a_d−k)/2` and the hedge threshold;
  - T−d ∈ {1: 729, 2: 662, 3: 343, 4: 402, 5: 284};
  - t ∈ {1, 999/1000, 99/100, 9/10, 3/4, 3/5, 51/100, 501/1000};
  - e ∈ {1/1000, 1/20, 1/10, 1/4, 49/100};
  - α ∈ {1/20, 1/4, 1/2}, about 800 each;
  - T ≤ 8, d ≤ 4.
- **SP1 inside the certified interval:** 2,420/2,420.
- **N1-brute inside the certified interval:** 2,420/2,420.
- **SP1 = N1-brute exactly:** 2,420/2,420.
- **Certified Γ > 0:** 675 cells.
- **Interval width:** at most 2.7e-8. Width < 10⁻³·Γ in 2,176 cells.
- **Caveat:** the cells with r = 1/500 and e = 49/100 have Γ near the certificate width, so they carry no information.

**Exact run without the LP** (`rev1_sp1_brute.py` → `results/rev1_sp1_brute_v1.json`; T ≤ 13, d ≤ 5):

| Check | Result |
|---|---|
| SP1 = N1-brute | 3,000/3,000 |
| SP1-A | 1,193/1,193 |
| SP1-B bound | 1,807/1,807 |
| SP1-B equality | 891/891 |
| SP1-C | 243/243 |
| SP1-E | 266/266 |
| Geometric forms and the alternating identity | 1,592/1,592 each |
| T-saturation | 1,023/1,023 |
| Continuity modulus | 400/400 |
| SP1-D bullet 1 | **fails 8/218** (CE-R1) |
| Delay factor | **fails 35/74** (CE-R3) |
| d-monotonicity, k > 0 | **fails 22/1,206** (CE-R5) |

**Witnesses:** `rev1_sp1_witness.py` → `results/rev1_sp1_witness_v1.json`.

Reproduce from the repo root with `uv run --no-sync python scripts/paper4_continuation/theory_v2/<script> <OUT> ...`
(the arguments are in each file's docstring). The certified runs took about 25 s per worker.

## 5. Routine versus specific

**Routine** (textbook steps; correctness is easy once set up):
- Lemma S: Bayes plus two-state propagation, `2q−1 = ±gρ^j`.
- The primitive forms, SP1-E and §3: geometric and alternating sums.
- The SP1 assembly: an LP ratio argument inherited from N1, followed by min/max bookkeeping.
- SP1-B/C: monotone substitution.
- Prop. C3: TV coupling plus Lipschitz continuity of max.
- Lemma W: an interval-scheduling argument with a non-increasing alternating sequence (`v_b ≤ a_s`).

**Specific to this problem** (where the content is):
1. **The reduction to "one free final switch".** The query time τ is chosen as the window end, so the k-bonus is
   paid once (Lemma W, step 1).
2. **Lemma K's common-window analysis.** It shows that the two branches cannot both collect the free final switch
   without paying at least the same amount back. The opposite-parity truncation in (A)/(B1)/(B2) is the one genuinely
   problem-specific combinatorial step.
3. **Lemma Pre.** It needs the zero pre-release weights, so it is specific to stationary symmetric chains.
4. **The parity mechanism.** The negative label owns step d iff d is odd. This yields SP1-A and the first-step
   contrast.

The depth sits in N1 (already audited) and Lemma K. Everything else is short.

## Lead verification (2026-11-10)

SP1-D counterexample re-computed with `gamma_cell`: T=2, d=1, t=1, e=1/10, c=0, k=2/5, α=1/10 ⇒ certified
Γ = 3/250 (= α((g−k)/2 − c) with g = 16/25), although g ≤ 2k. Correction accepted: at T = d+1,
Γ = α((g−k)/2 − c)⁺; "g ≤ 2k ⇒ Γ = 0" holds only for T ≥ d+2.
