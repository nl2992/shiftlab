# P5 review: `MIXING_PREMIUM_THEOREM.md` (M1–M5)

**Date:** 2026-11-11. **Reviewer:** fresh-context Opus 5.5, adversarial. **review_independence: same-family**,
**acceptance_status: provisional.** ARIS reviewer backends were not used; this is a native subagent review using the
proof-checker method (obligation ledger, taxonomy, two-axis severity, counterexample red team). Uncommitted.
Model: `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0. N1 and SP1 are taken as reviewed elsewhere (REVIEW_SP1,
THEOREM_PROOF_AUDIT). Falsified sub-claims would count as evidence, not findings. None were found.

## 0. Verdict

| Result | Status | Severity of open items |
|---|---|---|
| M1 (B = 1, α-free closed form, c₁, k = c = 0 limit) | **ACCEPTED** (conditional on N1, SP1; α ≤ 1/2 is necessary, §3) | MINOR |
| M2 (VOI monotone in T; VOI ≤ αU_B; ρΓ → 0 ⇔ Γ/α → 0) | **ACCEPTED** | MINOR (exposition) |
| M3 (first-label relaxation) | **ACCEPTED**: ν₁ is a legitimate causal null against every plan | MINOR |
| M4 (B = 2, k = 0, d odd) | **ACCEPTED with corrections** (scope wording, two implicit steps) | MAJOR on scope wording only |
| M5 | **ACCEPTED** | – |
| §0 "NO-GO answer" sentence | **OVERSTATED**: needs c < g r^d/(16(1+r)) and T ≥ T₀ at B = 2 | MAJOR (scope, not math) |

There are no counterexamples. **312 certified gamma_cell cells** (233 at B = 1, 79 at B = 2) failed **0** theorem
checks. There are also 2,160 brute-force M1 cells and 320 brute-force M4.2 cells. The P1 T₀ table is reproduced
exactly.

## 1. Obligation ledger

| # | Obligation | Where | Status | Note |
|---|---|---|---|---|
| O1 | VOI_IID = α·r_IID and Γ = α(2 max g_z0 − r_c)⁺ | M1.1 via N1 | ACCEPTED (inherited) | Needs α ≤ 1/2; see §3 |
| O2 | 2 max g_z0 = Ḡ₀ − 2c and Π = 2 max g_z0 − r_c | M1.1 via SP1 (★) | ACCEPTED | Π brute-forced from schedules, not from Lemma W (§4) |
| O3 | Ḡ₀ ≤ k + g r^d/(1 − r²), and Ḡ₀ − 2c > 0 under the condition | M1.2 | ACCEPTED | c₁ ≤ exact ρΓ in 2,160/2,160 brute-force cells, min slack 0.0045 |
| O4 | k = 0 algebra; n_0 = ⌈n/2⌉; inf = lim = (1 − r)/2 | M1.3 | ACCEPTED | Re-derived. Equals M1.1 in 218/218 certified cells |
| O5 | Constancy for T ≥ max(J, d+1)+1 | M1.4 | ACCEPTED | Brute-force, 0 violations |
| O6 | Shift map μ ↦ μ⁺ preserves VOI and both feasibilities | M2(a) | ACCEPTED | Uses stationarity (prior 1/2) and no query at step 1. 183/183 consecutive-T certified pairs monotone |
| O7 | x_s = ρ^{s−τ}x_τ for the latest released label; Σ\|w_s\| ≤ aBr^d/(1−r) | M2(b) | ACCEPTED, GAP-minor | Implicitly uses in-order release (constant d), which holds in the model. State it |
| O8 | P_A(promote) ≤ (1+ar)^{B−1}·R_IID by the likelihood ratio | M2(b) | ACCEPTED | P_A(y_i \| y_{<i}) uses all earlier queried labels (released or not); \|x\| ≤ r because τ_i > τ_{i−1} |
| O9 | ρΓ → 0 ⇔ Γ/α → 0 | M2(c) | ACCEPTED, GAP-minor | "⇐" needs VOI_IID(T₁) > 0 for some T₁. If VOI_IID ≡ 0, both sides are 0 under the convention ρΓ := 0. Say so |
| O10 | Pure plans split into P (constant event) and Q (no promotion before τ + d); τ is deterministic | M3 | ACCEPTED | Promote-and-query is a promotion leaf (P) |
| O11 | ν₁ is a causal null, and R_{ν₁}(π) = r₀(π) on Q | M3 | ACCEPTED | §2 |
| O12 | gain(μ) ≤ S′·max(R_{ν₁}, R_IID) | M3(i) | ACCEPTED | Both cases (D ≤ A, D > A) re-derived. CASE-minor: never-query/never-promote plans have risk 0, not 1, so they are not in m. They have gain 0, so the bound is unaffected |
| O13 | VOI_IID ≤ αS_I; mixing π̂ with never-promote | M3(ii),(iii) | ACCEPTED | S_I = VOI_IID/α exactly in **121/121** certified c = 0 cells (70 at B = 1, 51 at B = 2), using my independent S_I |
| O14 | H_y(δ) closed form; pattern ratios; H_∅ ≤ 2v₁ | M4.1 | ACCEPTED | Matches exact forward sums at T = 60 for δ = 1..5 and y = 0, 1. **UNCLEAR-minor:** for y = 1, "immediate promotion at u + d" is not what H₁ measures, because w₁(d) < 0 for odd d. H₁ is the free positive-part sum, which is a valid upper bound for the "everything" event. Reword |
| O15 | s₀(T) ≤ s₀^∞, s₁(T) ≤ s₁^∞, H_∅(T) ≤ 2v₁, s₀^∞ > s₁^∞ = 2v₁ | M4.2 | ACCEPTED | Exhaustive pure-plan enumeration (all u, u₂, per-label promotion times): 320/320 cells, t ∈ {0.55, 2/3, 3/4, 0.85, 0.9}, e ∈ {1/10, 1/5}, d ∈ {1, 3}, T ≤ 18 |
| O16 | Inequality directions in M4 | M4 | ACCEPTED | §2.2 |
| O17 | ζ(T) nondecreasing; truncation bound; liminf | M4 | ACCEPTED, GAP-minor | Needs ζ(T) ≤ s₀^∞ (true, by O15) for "the bound tends to the liminf value". No limit interchange is used: the bound holds at every T |
| O18 | T₀ table | M4 | ACCEPTED | All 6 rows reproduced. The exact-ζ T₀ is 1–3 steps smaller (§4) |
| O19 | M5 | M5 | ACCEPTED | 282/282 certified cells consistent |

## 2. Focus checks

### 2.1 (1) Is M3 a valid lower bound on Γ for the exact adaptive learner? Yes.

- **ν₁ is in the causal family.** In `frontier_cuts.best_response_null` and `risk_row_for_null`, the null's p is
  attached to the learner's (action 0, query 1) child, after the query choice, and is keyed by the public history
  (plus pending outcomes). "First query on this history" is a function of the public action sequence. p = 0 lies
  in [0, 1/2].
- **Every plan shape is covered.**
  - Re-timing or skipping the first query: s_y and H_∅ maximise over every τ, and over plans with no query.
  - Promoting before release: class P. Its event is constant, with risk 1 under every null.
  - Private randomisation: Kuhn mixtures. Both risks are linear, and the null cannot see the coins.
  - Post-promotion use of budget: inside g_y.
- **The bound only needs two members of the family.** VOI_causal ≤ max gain subject to R_IID ≤ α and R_{ν₁} ≤ α.
  Adding nulls only shrinks the feasible set, so how strong the adversary is does not matter.
- **Hidden assumption: MISSING ASSUMPTION, minor.** P_A(Y_τ = y) = 1/2 is used in gain = (g₀ + g₁)/2. This is
  Lemma S(i): a symmetric stationary chain with symmetric emissions. The heading "any B, T, c, k, d" is correct
  only inside the §0 family. It does not hold for a general HMM.

### 2.2 (2) Directions in M4

| Use | Direction | Correct? |
|---|---|---|
| ζ(T) − 4c is a lower bound on the IID ratio of π̂ | The true ratio is ζ − 3c (two queries in branch 0, one in branch 1). 4c is conservative | Yes |
| (s₀^∞ + s₁^∞)/2 is an upper bound on S′ | Larger c only lowers g_y | Yes |
| s₀^∞ is an upper bound on S_I in the ρΓ denominator | Applied only when the numerator is ≥ 0 (the ⁺) | Yes |

- **Limits.** The bound is pointwise in T. Then ζ(T) → s₀^∞ via the explicit truncation bound (δ = ⌊T/2⌋) and
  ζ ≤ s₀^∞. T₀ is explicit and ζ is monotone, so the bound is uniform on T ≥ T₀.
- **Certified checks.** Γ/α ≥ bound, ρΓ ≥ bound, VOI_IID/α ≥ ζ − 4c and VOI_IID/α ≤ s₀^∞ hold in **79/79** B = 2
  cells. The bound is positive in 35 of them.

### 2.3 (3) M1's α-freeness needs α ≤ 1/2

The theorem asserts this only for α ≤ 1/2, and that hypothesis is necessary. Probe cells at t = 3/4, e = 1/10,
d = 1, c = k = 0, α = 3/4 give certified ρΓ = 1/8, 0.1058, 0.1014 at T = 4, 6, 8. M1's α ≤ 1/2 values there are
0.300, 0.262, 0.253. α-freeness was confirmed at α ∈ {1/20, 1/4, 1/2} at T = 10 for every (t, d, c) family.

### 2.4 (4) M2 monotonicity

The proof is correct. Every consecutive-T pair in the stored certified families satisfies VOI_hi(T′) ≥ VOI_lo(T),
for both IID and causal (183 pairs).

### 2.5 (5) Hidden assumptions, stated per result

| Result | Assumptions it depends on |
|---|---|
| M1 | N1 (α ≤ 1/2), SP1, d odd |
| M2(a) | Stationary prior |
| M2(b) | Symmetric kernel, prior 1/2, constant delay |
| M3 | P_A(Y_τ) = 1/2 |
| M4 | k = 0 (positive-part calculus), d odd (E_d/O_d roles), small c, T ≥ T₀ |

All are in the stated setting except where noted above.

## 3. Scope corrections (required)

1. **§0, "M1 and M4 prove the opposite there (k = 0 for B = 2)".** For B = 2 add "and
   c < g r^d/(16(1 + r)), uniformly for T ≥ T₀". At larger c, at k > 0, and at T < T₀, nothing is proved.
   - **Exact example (t = 3/4, e = 1/10, d = 1, α = 1/20).** At c = 1/75 (the threshold) and c = 1/80, the M4 bound
     is negative at T = 10 and 12 (−0.030 / −0.015 and −0.026 / −0.012). Certified Γ/α is 0.0935 / 0.0934 and
     0.0944 / 0.0942.
   - **T₀ is far beyond any certified horizon** (truncation version / exact-ζ version):
     - t = 0.85: T₀ = 21 / 19;
     - t = 0.9: T₀ = 37 / 34.
2. **"S-1 for B = 2" satisfies only part of the salvage criterion.** It is uniform in T ≥ T₀, at k = 0, d odd and
   small c. That is not "uniform in T" without qualification. The lead should apply CONDITIONAL GO only with these
   qualifiers written into the claim.
3. **M3 heading.** Restrict it to the §0 family, because it needs P_A(Y_τ = y) = 1/2.

## 4. Red team (independent implementation)

**Code.** `scripts/paper4_continuation/theory_v2/rev3_mix_lib.py` was written from the primitive model and does not
import any wpM_* code. It has:
- a B = 1 schedule brute force for Ḡ_y;
- exhaustive B ≤ 2, k = 0 pure-plan enumeration for s_y(T), H_∅(T), S_I and S′;
- M4's closed forms, ζ and T₀ taken from the statement text.

**Runners.**
- `rev3_mix_redteam.py` checks the theorems against `gamma_cell`, one process at a time, with `nice 10`.
- `rev3_mix_recheck.py` re-evaluates the stored intervals without calling the solver.

| Output | Cells | Result |
|---|---|---|
| `results/rev3_mix_b1_v1.json` | 233 | All checks pass: M1.1 ρΓ and Γ inside the certified intervals 230/230; M1.3 = M1.1 218/218; c₁ ≤ ρΓ 195/195; M2(b) 233/233; M3(i)–(iii) 221/221; M5 207/207 |
| `results/rev3_mix_b2_v1.json` | 79 | All theorem checks pass: M2(b), M3(i),(ii), M4 (four checks), M5 |
| `results/rev3_mix_b{1,2}_recheck_v1.json` | 300 | M3(iii) 300/300; consistency 300/300; S_I = VOI_IID/α at c = 0 in 121/121 |

**Grid.**
- t ∈ {11/20, 2/3, 3/4, 17/20, 9/10}, d ∈ {1, 3}, c ∈ {0, 1/200, 1/100}, α ∈ {1/20, 1/4, 1/2}, T ≤ 14, e = 1/10.
- At B = 1: k ∈ {0, 1/50}.
- Near-threshold costs:
  - M1.2 boundary (2c + k = g r(1 − r), and 1/1000 below it);
  - Π threshold c = g r/(2(1 + r)), where certified ρΓ is exactly 0 at even n and positive at odd n, as predicted;
  - M4 threshold c ∈ {1/80, 1/75}.
- T₀ boundaries at B = 2: T₀ ± 1 for t ∈ {11/20, 2/3, 3/4}.

**Own bug, recorded.** In the v1 runner, my pure-plan *lower* bound ζ_best combined branch options whose second
query time u₂ < u + d differed between branches. No single plan can do that. This produced 3 spurious check
failures (cells T = 8, d = 3, c = 1/100, t = 2/3 and 3/4). Example: ζ_best = 77/600 against certified VOI_IID/α =
0.1275. The corrected combiner (`best_ratio_pure_v2`) clears all of them. The theorem's s_y are per-branch
suprema, so they are unaffected.

**Descriptive.** At B = 2, certified Γ/α is flat in T:
- t = 3/4, d = 1: 0.1075, 0.1063, 0.1069, 0.1066, 0.1067, 0.1067 at T = 8–12 and 14;
- t = 2/3, d = 1: about 0.080 at T = 4–14.

ρΓ drifts down only because VOI_IID/α rises toward s₀^∞, as M2 and M4 predict. The M4 relaxation recovers about
43% (t = 3/4) to 50% (t = 2/3) of Γ/α at T = 14.

## 5. Routine vs specific

- **Routine.**
  - M1 is algebra on SP1 + N1.
  - M2(a) is a shift argument.
  - M2(b) is a standard pathwise information bound plus a likelihood-ratio change of measure.
  - M3's inequality is weak duality against two nulls.
  - M5 is one line.
- **Specific (the real content).**
  - The choice of ν₁, which penalises only the first label while all later labels and the free post-promotion
    value go into the branch slopes.
  - The k = 0 positive-part calculus P(y)x′ = (x + s a)/2, which gives closed-form T = ∞ slopes and the gap
    s₀^∞ − s₁^∞ = g r^d/(2(1 + r)).
- **Weakness.** The relaxation is lossy, and it is vacuous whenever the IID-optimal pattern has its zero after the
  first label (t ≥ 0.85 for T < T₀). Extending to general B needs the ν_i family (§5 of the target), which is not
  attempted.

## 6. Reproduce

```
nice -n 10 uv run --no-sync python scripts/paper4_continuation/theory_v2/rev3_mix_redteam.py b1 <out_b1.json>   # ~6 min
nice -n 10 uv run --no-sync python scripts/paper4_continuation/theory_v2/rev3_mix_redteam.py b2 <out_b2.json>   # ~14 min (T = 14 cells ~160 s)
uv run --no-sync python scripts/paper4_continuation/theory_v2/rev3_mix_recheck.py <in.json> <out.json>
```
