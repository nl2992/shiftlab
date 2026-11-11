# Mixing-chain relative premium: what is proved (salvage step P1, target S-1)

**Date:** 2026-11-11. **Branch:** `research/paper4-causal-premium-theory-2026-11-10`, uncommitted.
**Author:** P1 prover (Opus 5.5), one bounded attempt (≈ 3 h, one solver process). Same-family work; no
independent review yet (that is P5). **Labels:** PROVED (full proof below), NUMERICALLY VERIFIED (exact-rational
`gamma_cell` certificate, or exact-rational brute force where stated), CONJECTURED, FALSIFIED.
Model and Γ: `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0. Statistic: ρΓ = Γ / (C₀ − V*_IID), C₀ = T/2.

## 0. Setting and summary

Symmetric stationary anti-persistent chain: t01 = t10 = t ∈ (1/2, 1), r = 2t − 1 ∈ (0, 1), ρ = −r, emissions
(e, 1 − e) with 0 < e < 1/2, a := 1 − 2e, g := a², prior 1/2, delay d, query cost c ≥ 0, switch cost k ≥ 0, budget
B, horizon T. VOI_X(T) := C₀ − V*_X(T) for X ∈ {IID, causal}, so ρΓ = 1 − VOI_causal/VOI_IID.
Write Ḡ_0^∞ := g r^d/(1 − r²), Ḡ_1^∞ := r Ḡ_0^∞, v₁ := g r^d/(2(1 − r)) (= (Ḡ_0^∞ + Ḡ_1^∞)/2).

| # | Statement | Status |
|---|---|---|
| **M1** | B = 1, d odd, α ≤ 1/2: ρΓ is α-free and **ρΓ(T) ≥ c₁ > 0 for every T ≥ d + 1**, c₁ explicit, whenever 2c + k < g r^d(1 − r). k = c = 0: inf_T ρΓ = lim_T ρΓ = (1 − r)/2 exactly | PROVED; certified cells below |
| M2 | Any B: VOI_X(T) nondecreasing in T; VOI_X(T) ≤ α·U_B with U_B = (1 + a r)^{B−1}·a B r^d/(1 − r). Hence ρΓ(T) ≥ Γ(T)/(α U_B): **ρΓ → 0 in T iff Γ/α → 0** | PROVED |
| **M3** | Any B, T, c, k, d: first-label relaxation. Γ ≥ α[ζ − max(H_∅⁺, s₁⁺, (s₀⁺ + s₁⁺)/2)] for any IID plan of IID risk ≥ α and ratio ζ; s_y = IID slope of the branch after Y_first = y, H_∅ = best unconditional-promotion gain | PROVED (reduces to N1's lower half at B = 1) |
| **M4** | B = 2, k = 0, d odd, c ≥ 0, α ≤ 1/2: Γ(T)/α ≥ ζ(T) − 4c − (s₀^∞ + s₁^∞)/2 with closed forms s₀^∞ = g r^d(3 + r)/(2(1 − r²)), s₁^∞ = g r^d/(1 − r); **liminf_T ρΓ ≥ (1 − r)/(2(3 + r)) − 8c(1 − r²)/(g r^d(3 + r))**, and an explicit T₀ beyond which the bound is uniform | PROVED; certified cells below |
| M5 | Any B, α ≤ 1: ρΓ ≤ 1 − H_∅/S_I with S_I the IID slope | PROVED |
| General B | Uniform-in-T lower bound for B ≥ 3 | **NOT PROVED.** Obstruction identified (§5); M3 alone is too weak from B ≈ 3–4 at t = 3/4 |

**Answer to the NO-GO trigger.** No proof and no certified datum shows ρΓ → 0 in T for t < 1 at B = 1 or B = 2;
M1 and M4 prove the opposite there (k = 0 for B = 2). For B ≥ 3 nothing is proved: the committed data at
t = 3/4 show ρΓ **decreasing** over T = 4..10 (B = 3: 0.275 → 0.165; B = 4: 0.29 → 0.26), and by M2 that decrease
is a vanishing premium only if Γ/α itself goes to 0, which T ≤ 10 cannot decide. The salvage plan's phrase "flat in
T at fixed B" is accurate for B = 1 only; at B = 2 the ratio falls from 0.231 (T = 4) to 0.149 (T = 10) while Γ/α
stays ≈ 0.107 and VOI/α saturates (M2), consistent with M4's positive limit.

---

## 1. Theorem M1 (B = 1) — PROVED

**Statement.** Let B = 1, d odd, α ∈ (0, 1/2], t ∈ (1/2, 1), and let Π := min{Ḡ_0/2 − c, Δ, (Δ + k)/2 − c} be the
SP1 numerator (`STOCHASTIC_POSITIVE_PREMIUM.md`, Theorem SP1; Ḡ_y, Δ there). Then:

1. **(α-free closed form)** ρΓ(T) = Π⁺/(Ḡ_0 − 2c) whenever Π > 0, and ρΓ(T) = 0 otherwise. In particular
   ρΓ ≤ 1/2, and ρΓ = 1/2 at T = d + 1 when Ḡ_0 > 2c.
2. **(uniform bound)** If 2c + k < g r^d(1 − r), then for **every** T ≥ d + 1
   `ρΓ(T) ≥ c₁ := [g r^d − 2c − max(k, g r^{d+1} − k)] / (2(k + g r^d/(1 − r²) − 2c)) > 0.`
3. **(k = 0, exact)** With n := T − d and c ≥ 0: ρΓ(T) = (Δ_n/2 − c)⁺/(Ḡ_{0,n} − 2c), where
   Δ_n = g r^d(1 − ρ^n)/(1 + r) and Ḡ_{0,n} = g r^d(1 − r^{2⌈n/2⌉})/(1 − r²). For c = 0:
   ρΓ = (1 − r)/2 for n even and (1 − r)(1 + r^n)/(2(1 − r^{n+1})) for n odd, so
   **inf_{T ≥ d+1} ρΓ = lim_T ρΓ = (1 − r)/2**. For c > 0:
   lim_T ρΓ = (g r^d/(2(1 + r)) − c)⁺ / (g r^d/(1 − r²) − 2c).
4. **(k > 0)** ρΓ(T) is constant for T ≥ max(J, d + 1) + 1, J = max{j : g r^j > 2k}.

**Proof.**
1. N1 (α ≤ 1/2) gives V*_IID = C₀ − α r_IID with r_IID = max(r_c, 2 max_τ g_z0) and Γ = α(2 max g_z0 − r_c)⁺. If
   Γ > 0 then r_IID = 2 max g_z0, so ρΓ = (2 max g_z0 − r_c)/(2 max g_z0), which does not involve α. In the SP1
   family, 2 max g_z0 = Ḡ_0 − 2c and 2 max g_z0 − r_c = Π (SP1 proof, formula (★) and Lemmas W, K, Pre). If Γ = 0
   then ρΓ = 0 (VOI_IID ≥ 0; when VOI_IID = 0, set ρΓ := 0). Since Π ≤ Ḡ_0/2 − c, ρΓ ≤ 1/2. At T = d + 1, P_1 = ∅
   and Π = Ḡ_0/2 − c.
2. Under the condition, SP1-C gives Π ≥ L := (1/2)[g r^d − 2c − max(k, g r^{d+1} − k)] > 0 for every T ≥ d + 1.
   For the denominator, Lemma W gives Ḡ_0 = k + Σ_{j∈P_0}(a_j − 2k)⁺ ≤ k + Σ_{m≥0} g r^{d+2m} = k + g r^d/(1 − r²)
   if a_d > 2k, and Ḡ_0 = a_d − k ≤ k otherwise. Also Ḡ_0 − 2c ≥ a_d − k − 2c > 0. Hence
   ρΓ = Π/(Ḡ_0 − 2c) ≥ L/(k + g r^d/(1 − r²) − 2c) = c₁.
3. SP1-E: with k = 0, M* = T − 1, Π = Δ_n/2 − c, and Ḡ_0 sums the n_0 = ⌈n/2⌉ odd offsets
   d, d + 2, …, so Ḡ_{0,n} as stated. For c = 0 and n even, ρ^n = r^n and 2⌈n/2⌉ = n, so the ratio is
   [(1 − r^n)/(2(1 + r))]·[(1 − r²)/(1 − r^n)] = (1 − r)/2. For n odd, ρ^n = −r^n and 2⌈n/2⌉ = n + 1, giving the
   second expression, which exceeds (1 − r)/2. The limits follow from r^n → 0.
4. SP1 §3: for r < 1 and k > 0, Ḡ_0 and Ḡ_1 depend on T only through min(T − 1, J). ∎

*Example.* t = 3/4, e = 1/10, d = 1, k = c = 0: ρΓ = 1/4 for every even T − d, → 1/4 (the data value 0.25).
t = 9/10: (1 − r)/2 = 0.1 (data: 0.1 at odd T, 0.127–0.256 at even T, decreasing to 0.1).

**Verification (NUMERICALLY VERIFIED,** `results/wpM_proof_b1_v1.json`**).** The exact closed form lies inside the
certified ρΓ interval, and c₁ ≤ certified ρΓ, in **480/480** gamma_cell cells (0 failures):
t ∈ {2/3, 3/4, 9/10}, e ∈ {1/10, 1/5}, d ∈ {1, 3}, c ∈ {0, 1/100}, k ∈ {0, 1/50},
T ∈ {d+1, d+2, 6, 8, 10, 11, 12, 14}, α = 1/10, plus α ∈ {1/20, 1/2} at T = 8 (α-freeness).
The closed form also reproduces every B = 1 F_anti cell of `wpC2_relative_premium_v1_compact.json` (**112/112**, to 1e-7).

---

## 2. Proposition M2 (any B: monotonicity, boundedness, reduction to Γ/α) — PROVED

Any B ≥ 1, d ≥ 1, c, k ≥ 0, α ∈ [0, 1], the symmetric stationary chain above.

(a) **VOI_X(T) is nondecreasing in T** for X ∈ {IID, causal}.
*Proof.* Map a horizon-T mixture μ to the horizon-(T+1) mixture μ⁺ that plays action 0 with no query at step 1 and
then runs μ shifted by one step. Step 1 costs q₁ = 1/2, which is also C₀(T+1) − C₀(T); by stationarity
(S₂, …, S_{T+1}) has the law of (S₁, …, S_T), so the remaining expected cost is unchanged and VOI is equal. No query
happens at step 1, so every causal null for T + 1 restricted to steps ≥ 2 is a causal null for μ, and conversely; the
IID risk is unchanged. A₀ = 0 = A₁ adds no switch. ∎

(b) **VOI_X(T) ≤ α U_B, U_B = (1 + a r)^{B−1}·a B r^d/(1 − r)**, for every T.
*Proof.* Let w_s = a x_s be the gain of action 1 at step s, x_s = 2P(S_s = 1 | labels released by s) − 1. If the
latest released label was queried at τ, then x_s = ρ^{s−τ} x_τ (Markov property, symmetric kernel), so
|w_s| ≤ a r^{s−τ} with s − τ ≥ d, and w_s = 0 before the first release (q_s = 1/2, Lemma S). Assigning each s to its
latest released label, Σ_s |w_s| ≤ Σ_{labels} Σ_{j≥d} a r^j ≤ a B r^d/(1 − r) pathwise. Before the first
promotion σ the learner plays 0, so the cost saving is Σ_{s≥σ} a_s w_s − (costs) ≤ 1{σ ≤ T}·a B r^d/(1 − r).
Hence VOI(μ) ≤ P_A(promote)·a B r^d/(1 − r). The promotion event of a pure plan is a set of released-label
histories; for such a history y, P_A(y) = LR(y)·P_IID(y) with LR(y) = Π_i 2P_A(y_i | y_{<i}). The first factor is
1 (P_A(Y = 1) = 1/2); for i ≥ 2, 2P_A(y_i | y_{<i}) = 1 ± a x with x the state deviation at τ_i given the earlier
labels, |x| ≤ r (at least one transition since τ_{i−1}, one query per step). So P_A(promote) ≤ (1 + a r)^{B−1} R_IID
≤ (1 + a r)^{B−1} α for every IID-feasible, hence every causal-feasible, mixture. ∎

(c) **Consequences.** Both VOI_X(T) converge as T → ∞, and ρΓ(T) ≥ Γ(T)/(α U_B). So for t < 1 a uniform-in-T lower
bound on ρΓ is equivalent to a uniform-in-T lower bound on Γ/α; **ρΓ → 0 in T iff Γ(T)/α → 0**. (At t = 1, U_B is
infinite, which is why Thm A's ρ → 0 does not transfer.) Also VOI_IID(T) ≥ VOI_IID(T₀) for T ≥ T₀, so
ρΓ(T) ≥ 1 − VOI_c(∞)/VOI_IID(T₀). ∎

---

## 3. Theorem M3 (first-label relaxation, any B) — PROVED

**Classes of pure plans.** A pure plan π has a deterministic first query time τ (nothing is observed before it).
Class **P**: π promotes before τ + d or never queries; its promotion event is constant, with IID and causal risk 1 or
0. Class **Q**: no promotion before τ + d. For π ∈ Q and y ∈ {0, 1} let g_y(π) be the expected cost saving given
Y_τ = y (all query and switch costs included) and r_y(π) := P_IID(promote | Y_τ = y). Since P_A(Y_τ = y) = 1/2,
gain(π) = (g₀ + g₁)/2 and R_IID(π) = (r₀ + r₁)/2.

**Definitions.** H_∅ := max_{π∈P} gain(π); s_y := max{g_y(π)/r_y(π) : π ∈ Q, r_y(π) > 0}. If r_y(π) = 0 the branch
never promotes and g_y(π) ≤ 0 (it only pays costs), so **g_y(π) ≤ s_y⁺ r_y(π) for every π ∈ Q.**

**Null ν₁.** p = 0 at the first query on every history, p = 1/2 afterwards. It is causal (p ∈ [0, 1/2], adapted to the
public history, in which the first query is visible). For π ∈ Q, R_{ν₁}(π) = r₀(π): the first label is 0 and the
rest are IID(1/2), exactly the conditional law defining r₀.

**Theorem M3.** For every T, B, d, c, k and α ∈ (0, 1]:
(i) VOI_causal ≤ α·S′, with S′ := max(H_∅⁺, s₁⁺, (s₀⁺ + s₁⁺)/2);
(ii) VOI_IID ≤ α·S_I, with S_I := max(H_∅⁺, s₀⁺, s₁⁺);
(iii) for any pure plan π̂ with R_IID(π̂) ≥ α and ratio ζ := gain(π̂)/R_IID(π̂) ≥ 0:
**Γ ≥ α(ζ − S′)** and **ρΓ ≥ (ζ − S′)/S_I.**

*Proof.* (i) Let μ be a causal-feasible mixture with mass m on class P, and let A := Σ_{π∈Q} μ(π) r₀(π),
D := Σ_{π∈Q} μ(π) r₁(π). Then gain(μ) ≤ m H_∅⁺ + (s₀⁺ A + s₁⁺ D)/2. If D ≤ A this is ≤ m H_∅⁺ + A(s₀⁺ + s₁⁺)/2;
if D > A it equals m H_∅⁺ + A(s₀⁺ + s₁⁺)/2 + s₁⁺(D − A)/2 ≤ m H_∅⁺ + S′A + S′(D − A)/2. In both cases
gain(μ) ≤ max(H_∅⁺, S′)·(m + max(A, (A + D)/2)) = S′·max(R_{ν₁}(μ), R_IID(μ)) ≤ S′α, because ν₁ and IID(1/2) are
both causal nulls. (ii) The same computation with only the IID row: (s₀⁺A + s₁⁺D)/2 ≤ max(s₀⁺, s₁⁺)(A + D)/2.
(iii) Mixing π̂ with never-promote (private coin, probability α/R_IID(π̂)) is IID-feasible with VOI = αζ, so
Γ = VOI_IID − VOI_causal ≥ α(ζ − S′); divide by VOI_IID ≤ αS_I. ∎

*Remarks.* At B = 1 and c = 0 the classes are N1's: s₀ = 2 max g_z0, s₁ = 2 max g_z1, (s₀ + s₁)/2 = g_both,
H_∅ = g_pre, and S′ = r_c (the term g_z0 = s₀/2 is dominated), so M3 reproduces N1 exactly (with c > 0 it is a
slightly weaker bound, because s_y charges the first query to one branch only). For B ≥ 2 M3 is a relaxation (later
null moves are fixed at 1/2), so it is a lower bound only. Its content is that **only the first label
is penalised**: everything after it, including the free post-promotion use of the remaining budget, enters through
the branch slopes s_y.

---

## 4. Theorem M4 (B = 2, k = 0, d odd) — PROVED

**Value calculus (k = 0).** After the first promotion with k = 0 the continuation plays a_s = 1{w_s > 0}, so the
post-promotion value is Σ_{s≥σ} E(w_s)⁺; every term is ≥ 0, so values are nondecreasing in T and bounded by their
T = ∞ versions. With x the deviation of S at the query time u and a label Y_u, P(Y_u = 1) = (1 + a x)/2 and the
posterior deviation is (x ± a)/(1 ± a x); hence **P(y)·x′_y = (x + s_y a)/2** (s_y = 2y − 1). Positive
homogeneity of z ↦ z⁺ then makes every expected post-label value a sum of positive parts of linear combinations of
ρ-powers. Put O_d := Σ_{j≥d, j odd} r^j = r^d/(1 − r²), E_d := Σ_{j≥d, j even} r^j = r^{d+1}/(1 − r²) (d odd).

**Lemma M4.1 (T = ∞ branch values; first label at u, second at u + δ, δ ≥ 1).** For y ∈ {0, 1}:
- immediate promotion at u + d, second label free:
  H_y(δ) = Ḡ_y^∞ + v₁ − g r^{d+δ}/(2(1 − r));
- promotion only on the second label's value v, released at u + δ + d (branch risk 1/2), ratio
  P_y(δ, v) = g Σ_{j≥d}((s_y ρ^δ + s_v) ρ^j)⁺, i.e. g(1 + s_yρ^δ)E_d for v = 1 and g(1 − s_yρ^δ)O_d for v = 0;
- unconditional promotion with both labels free: H_∅ ≤ 2v₁ (second label time may depend on Y_u).

*Proof.* Conditioning on Y_u = y, the deviation at u is s_y a. Before the second release the value is
Σ_{j=d}^{δ+d−1} g(s_y ρ^j)⁺. After it, by the calculus with x = s_y a ρ^δ, the value per offset j ≥ d is
(g/2)[((s_yρ^δ + 1)ρ^j)⁺ + ((s_yρ^δ − 1)ρ^j)⁺] = (g/2)[(1 + s_yρ^δ)r^j 1{j even} + (1 − s_yρ^δ) r^j 1{j odd}], using
|ρ^δ| < 1. Summing: (g/2)[(1 + s_yρ^δ)E_d + (1 − s_yρ^δ)O_d] = v₁ − s_y (g r^d/2) ρ^δ/(1 + r). Adding the first
segment and splitting δ by parity (four cases, each a finite geometric sum) gives the same expression
Ḡ_y^∞ + v₁ − g r^{d+δ}/(2(1 − r)) in all four. The pattern ratio is 2·(unnormalised value) with
P(v | y)x″ = (s_y a ρ^δ + s_v a)/2. For H_∅, average the immediate values over y with any δ_y:
(H₀(δ₀) + H₁(δ₁))/2 < (Ḡ_0^∞ + Ḡ_1^∞)/2 + v₁ = 2v₁. ∎

**Lemma M4.2 (branch slopes at B = 2, any T).** s₀(T) ≤ s₀^∞ := Ḡ_0^∞ + v₁ = g r^d(3 + r)/(2(1 − r²)),
s₁(T) ≤ s₁^∞ := g r^d/(1 − r) = 2v₁, H_∅(T) ≤ 2v₁, all with c = k = 0 (larger c only lowers them).
*Proof.* In branch y one label remains, so the branch event is ∅, everything, or {Y₂ = v}. "Everything" is worth at
most sup_δ H_y(δ) = Ḡ_y^∞ + v₁ (promoting later or not querying only loses nonnegative terms); {Y₂ = v} has branch
risk 1/2 and ratio ≤ sup_{δ,v} P_y(δ, v). For y = 0 the best pattern is δ = 2, v = 0: g(1 + r²)O_d, and
(3 + r)/2 − (1 + r²) = (1 − r)(1 + 2r)/2 > 0, so s₀ ≤ Ḡ_0^∞ + v₁. For y = 1 the best pattern is δ = 1, v = 0:
g(1 + r)O_d = g r^d/(1 − r), which exceeds Ḡ_1^∞ + v₁ = g r^d(1 + 3r)/(2(1 − r²)) because 2 + 2r > 1 + 3r. A
first query later than step 1 only shortens the horizon (stationarity). ∎

**Theorem M4.** B = 2, k = 0, d odd, t ∈ (1/2, 1), e ∈ (0, 1/2), c ≥ 0, α ∈ (0, 1/2]. Let
ζ(T) := max_δ H₀(δ; T) be the finite-T value of the plan "query at 1; if Y₁ = 0 promote at 1 + d, query the second
label at 1 + δ and follow sign(w); if Y₁ = 1 do nothing" (computed exactly by forward filtering). Then for every T
`Γ(T)/α ≥ ζ(T) − 4c − (s₀^∞ + s₁^∞)/2,   ρΓ(T) ≥ [ζ(T) − 4c − (s₀^∞ + s₁^∞)/2]⁺ / s₀^∞,`
ζ(T) is nondecreasing, and ζ(T) ≥ s₀^∞ − g(r^{d+δ}/2 + r^{T−δ})/(1 − r) for any 1 ≤ δ ≤ T − d. Consequently
`liminf_T ρΓ ≥ (1 − r)/(2(3 + r)) − 8c(1 − r²)/(g r^d (3 + r))`,
and the bound is uniform for all T ≥ T₀ where T₀ is any T with ζ(T₀) − 4c > (s₀^∞ + s₁^∞)/2.

*Proof.* The plan has IID risk 1/2 ≥ α and IID ratio ≥ ζ(T) − 4c (each branch pays at most two queries; its first
promotion is at a step with w = g r^d > 0, so the k = 0 value is exactly the brute sum). M3(iii) with
S′ ≤ max(2v₁, s₁^∞, (s₀^∞ + s₁^∞)/2) = (s₀^∞ + s₁^∞)/2 (M4.2, since s₀^∞ > s₁^∞ = 2v₁) gives the Γ bound; M3(ii)
with S_I ≤ s₀^∞ gives the ρΓ bound. The truncation bound: the T = ∞ value of δ minus the steps beyond T, each ≤ g r^j
after the second release, Σ_{j ≥ T−δ} g r^j = g r^{T−δ}/(1 − r). Limits: (s₀^∞ − s₁^∞)/2 = g r^d/(4(1 + r)). ∎

**Uniformity thresholds (exact rational evaluation of the explicit truncation bound,
`results/wpM_proof_b3explore_v1.json`, key `T0`; c = 0).** For T ≥ T₀ the M4 bound is positive and nondecreasing
in T (ζ is), so inf_{T ≥ T₀} ρΓ ≥ [ζ(T₀) − (s₀^∞ + s₁^∞)/2]/s₀^∞ > 0, and the bound tends to the liminf value:

| t | d | T₀ (e = 1/10 and 1/5) | liminf ρΓ lower bound (1 − r)/(2(3 + r)) | limit of Γ/α bound, e = 1/10 |
|---|---|---|---|---|
| 2/3 | 1 | 6 | 0.100 | 0.0400 |
| 2/3 | 3 | 8 | 0.100 | 0.0044 |
| 3/4 | 1 | 10 | 0.0714 | 0.0533 |
| 3/4 | 3 | 12 | 0.0714 | 0.0133 |
| 9/10 | 1 | 37 | 0.0263 | 0.0711 |
| 9/10 | 3 | 39 | 0.0263 | 0.0455 |

With c = 1/1000 the thresholds move by at most 4 steps (t = 2/3, d = 3, e = 1/5 loses positivity); with c = 1/100
the limit is negative in most of these families (4c dominates), so **M4 is a small-query-cost result.**

*Instance.* t = 3/4, e = 1/10, d = 1, c = 0: s₀^∞ = 56/75, s₁^∞ = 16/25, Γ/α → bound 4/75 and
liminf ρΓ ≥ 1/14 ≈ 0.071. Certified data: Γ/α ≈ 0.107, ρΓ = 0.149 at T = 10 (the relaxation loses the later
null moves, about a factor 2 here).

**Where M4 is vacuous, and why (NUMERICALLY VERIFIED).** At finite T the exact branch slopes (brute forward filter,
`b2_finite` key) give, for t = 9/10, d = 1: s₁(T) > s₀(T) for T = 6, 8, 10, 12 (e.g. T = 10: s₁ = 2.1305 from the
branch-1 pattern (1, 0) at δ = 1, s₀ = 1.9411). The IID optimum at these horizons promotes on a **zero in the second
position**, which ν₁ does not penalise, so M3/M4 give nothing for T < 37 there, although Γ > 0 is certified in every
committed t = 9/10 cell. The certified IID values agree with M3(ii)'s S_I = max(H_∅, s₀, s₁) computed by brute force:
t = 9/10, T = 6, 8, 10: VOI_IID/α = 1.5114, 1.8889, 2.1305 (= s₁); t = 3/4, T = 6, 8, 10: 0.63, 0.6875, 0.7169
(= s₀); α ∈ {1/20, 1/10} (wpC2 data).

**Verification (NUMERICALLY VERIFIED,** `results/wpM_proof_b2_v1.json`**).** **111/111** certified B = 2 cells, 0 failures (t ∈ {2/3, 3/4, 9/10}, e = 1/10, d ∈ {1, 3},
c ∈ {0, 1/100}, k = 0, T ∈ {4, …, 12} plus T = 14 for three d = 1 families, α ∈ {1/20, 1/4}): certified Γ/α ≥ M4
bound, VOI_IID/α ∈ [ζ(T) − 4c, s₀^∞]. The M4 bound is positive in 22 cells (t = 2/3 and 3/4 at larger T). In all 57
c = 0 cells (i) the certified VOI_IID/α equals the brute-force S_I(T) = max(H_∅, s₀, s₁) exactly, and (ii) the
first-label relaxation LP (rows IID and ν₁) has VOI/α equal to S′(T) = max(H_∅, s₁, (s₀ + s₁)/2) to 1e-6, so M3(i)
and M3(ii) are tight at B = 2; the gap to the true Γ comes only from later null moves.
Selected certified values (c = 0, α = 1/20; Γ/α, ρΓ, M4 bounds on Γ/α and ρΓ):
t = 2/3, d = 1, T = 14: 0.080, 0.200, 0.040, 0.099; t = 3/4, d = 1, T = 14: 0.1067, 0.144, 0.046, 0.061;
t = 9/10, d = 1, T = 12 / 14: Γ/α 0.480 / 0.428, ρΓ 0.210 / 0.180 (M4 vacuous, T < T₀ = 37).

---

## 5. General B: what fails, and the exact obstruction

**Proposition M5 (upper bound) — PROVED.** For any B, T, α ∈ (0, 1]: ρΓ ≤ 1 − H_∅/S_I (when S_I > 0).
*Proof.* Promoting unconditionally at the start with private probability α has causal risk α, so
VOI_causal ≥ αH_∅; and VOI_IID ≤ αS_I (M3(ii)). ∎

**Why M3 does not give a uniform bound for general B.**
1. **α is spent once.** Only the first promotion is constrained, so every slope (s₀, s₁, H_∅) contains the free
   post-promotion value of the unused labels, ≈ (B − n)v₁ for a plan that observes n labels before promoting. The
   first-label gap s₀ − max(s₁, H_∅) does not grow with B, while S_I grows like Bv₁. The windows do **not** each get
   α: the premium comes from one constrained event, and the extra labels dilute it.
2. **Likelihood-ratio boost of the free value.** A branch event that waits for a confirming second label has
   IID-likelihood ratio 2P_A(y₂ | y₁) = 1 + g r^δ > 1, and this ratio multiplies the free value of the remaining
   labels. Exact T = ∞ values of explicit plans (t = 3/4, e = 1/10, d = 1; T = ∞ closed forms, matched by the exact forward filter at T = 22,
   `results/wpM_proof_b3explore_v1.json`):
   - B = 3: branch-0 immediate promotion with two free labels → Ḡ_0^∞ + 2v₁ = 1.0667; branch-1 pattern (1, 0) at
     δ = 1 plus a free label far away → g r/(1 − r) + (1 + g r)v₁ = 1.0624 (both are values of explicit plans, i.e.
     lower bounds on s₀ and s₁; the second T = ∞ value is a limit, not separately proved). Unless some other branch-0
     plan is much better, the first-label margin s₀ − s₁ is of order 0.004 here, against ≈ 0.11 at B = 2.
   - B = 4: the same branch-1 plan with two free labels is worth 0.64 + 1.32·0.64 = 1.4848, versus 1.3867 for the
     branch-0 immediate plan. Unless a branch-0 plan exceeds 1.4848, s₁ > s₀ and **M3 gives nothing**: the IID
     optimum then hinges on a zero in the *second* position, which ν₁ does not penalise. (Not established either way.)
3. **What a general proof needs.** A relaxation that penalises the label position where the IID-optimal pattern has
   its zero (nulls ν_i: p = 0 at the i-th query), together with the branch-slope calculus of §4 for multi-label
   patterns, and a proof that the causal learner's aligned alternative (patterns made of ones, which needs gaps of
   2 and so a weaker boost 1 + g r² instead of 1 + g r) stays strictly worse. This is the t < 1 analogue of the
   re-timing in Thm A; at t = 1 the aligned learner loses nothing (Thm A), while at t < 1 it loses a factor r per
   realignment. Not attempted in the time budget.

**CONJECTURED (not proved, not falsified).** For fixed α and B ≤ log₂(1/α) the premium Γ/α stays bounded away from
0 as T → ∞ for every B (no rate in B is conjectured: the free-value dilution in item 1 pushes ρΓ down like 1/B, the
likelihood-ratio boost in item 2 can push the gap up like B). No counterexample is known. Evidence: B = 3, 4 data at
t = 3/4 (Γ/α ≈ 0.17 and 0.35 at T = 10, still falling slowly at B = 3).

---

## 6. Verification record

All from the repo root with `uv run --no-sync python`, one process, `nice 10`. Outputs refuse to overwrite.

| Script | Output | Result |
|---|---|---|
| `scripts/paper4_continuation/theory_v2/wpM_b1_lib.py` | library (M1 closed forms) | – |
| `wpM_b1_check.py OUT` | `results/wpM_proof_b1_v1.json` | 480/480 cells: closed form inside certified ρΓ, c₁ ≤ ρΓ; α-free at T = 8 (α ∈ {1/20, 1/10, 1/2}); 112/112 wpC2 B = 1 cells reproduced |
| `wpM_b2_lib.py` | library: exact forward filter, M4 closed forms | brute = closed form (H_y(δ), patterns) at T = 24 to < 1e-6 (truncation) |
| `wpM_b3_explore.py OUT 22` | `results/wpM_proof_b3explore_v1.json` | B = 3 explicit plans; B = 2 finite-T slopes; T₀ table |
| `wpM_b2_check.py OUT` | `results/wpM_proof_b2_v1.json` | 111/111 cells, 0 failures; relaxation LP tight (57/57) |

## 7. Limitations

- M1 inherits N1 (α ≤ 1/2) and SP1 (symmetric stationary chain, symmetric emissions); both are same-family reviewed
  only (REVIEW_SP1). The ratio is α-free only at B = 1.
- M4 is for k = 0 and d odd. With k > 0 the post-promotion value is not a sum of positive parts and Lemma M4.1 does
  not apply; with d even the roles of E_d and O_d swap and the first-label gap changes sign (not analysed).
- M4's bound is a relaxation: it keeps only the first-label null move and loses about half of the observed premium.
- General B (≥ 3) is open; §5 gives the obstruction and the needed ingredient. Under the locked criteria this is the
  CONDITIONAL-GO situation at best (B = 1 and B = 2 proved, general B the remaining obligation), subject to P5 review
  and P3 numerics; the lead applies the criteria.
- All evidence is synthetic, T ≤ 14.
