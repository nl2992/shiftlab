# General-budget causal-safety premium: one bounded attempt (wpG)

**Date:** 2026-11-11. **Branch:** `research/paper4-causal-premium-theory-2026-11-10`, uncommitted.
**Author:** wpG theory agent (Opus 5.5), one bounded attempt (≈ 3 h, ≤ 3 solver processes, `nice 10`).
Same-family work only; no independent proof review. **Labels:** PROVED (full proof below), NUMERICALLY VERIFIED
(exact-rational `gamma_cell` certificate, or float LP cross-checked against it), CONJECTURED, FALSIFIED.
Model, Γ, Π_B, causal nulls: `CAUSAL_SAFETY_PREMIUM_THEORY.md` §0. Motivating data: `RELATIVE_PREMIUM_SCALING.md`.

## 0. Summary and verdict

Relative premium ρ = Γ / (C₀ − V*_IID), C₀ = T/2 (symmetric stationary chain).

| # | Statement | Status |
|---|---|---|
| T1 | Fixed calendar: worst-case causal risk of any mixture = backward recursion `R(h) = x(h) + max(R(h0), (R(h0)+R(h1))/2)`; worst nulls are bang-bang p ∈ {0, 1/2}; a pattern y has causal risk `2^{−#ones(y)}`; increasing f has causal risk = IID risk | PROVED |
| T1-LF | Fixed calendar: V_causal^cal(α) has a single least-favourable null (LP duality) | PROVED |
| T1-cap | The causal upper probability is **not** 2-alternating for B = 3 (80 violating pairs; none at B = 2), so Huber–Strassen does not apply | NUMERICALLY VERIFIED (exact enumeration) |
| CAL-t1 | t = 1, symmetric emissions, c = 0, any d, k, prior: the calendar 1..B is WLOG for **V*_IID** | PROVED |
| ADAPT | Adaptive timing **strictly beats** every fixed calendar for **V*_causal** once T − B is large (e.g. T = 8, B = 2: calendar Γ = 0.048, exact Γ = 0.032) | NUMERICALLY VERIFIED (exact) |
| Lemma A | t = 1: a positive step is followed by a non-positive one; at most ⌊B/2⌋ of q_1..q_B exceed 1/2 on every path | PROVED |
| Prop L | Fixed calendar, fixed B, T → ∞: ρ^cal(T) → ρ_∞^cal(B,α) = 1 − S_c(α)/S_I(α) (a static robust-NP slope problem) | PROVED |
| Prop P | Fixed calendar, α ≤ 2^{1−B}: ρ_∞^cal(B,α) ≥ 1 − 2/((1−2e)(2(1−e))^{⌊B/2⌋}) → 1 | PROVED; 0 violations in 222 static LP cells |
| **Thm A** | t = 1, d = 1, c = k = 0: for every B, α and T ≥ 2B: **Γ(T) ≤ (1−2e)(B+1)**; hence ρ(T) → 0 as T → ∞ at fixed B | PROVED; exact Γ constant in T at B = 2, 3 |
| **Thm V** | t = 1, d = 1, c = k = 0: `Γ ≤ ((1−2e)/2)[K_α + T·π_B]`, K_α = 2 log(4(1−e)/α)/I_e, π_B → 0 exponentially; hence `sup_{T ≥ B+1} ρ → 0` as B → ∞ at fixed α | PROVED |
| T2 exact | B = 1: ρ_∞ = 0; B = 2: calendar slope ρ_∞^cal = 1/4 exactly (α ≤ 1/2), while the exact Γ is constant (0.032 at e = 1/10, α = 1/20) for T = 6..14 | PROVED (calendar slope); exact Γ values NUMERICALLY VERIFIED |
| T3 | No B-uniform positive lower bound on ρ exists at t = 1 (Thms A, V). For t ∈ (1/2,1) the same is CONJECTURED; no lower bound was proved | PROVED (t = 1 negative); CONJECTURED (t < 1) |
| Lead hypothesis | "Patterns with ≈ B/2 ones are inflated by ≈ 2^{B/2}" | PROVED as a statement about pattern events and the LR against the RIPr null (Prop P); it does **not** control V*_causal once the learner can re-time queries (ADAPT, Thm A) |

**Verdict.** The rise of ρ with B in the scaling data is real for the cells measured, but it is a **finite-resource
effect**, not a general-budget separation. ρ is large only when (i) the horizon leaves little slack beyond the
budget (T − B small) and (ii) the budget is below the causal detection scale (B·I_e ≲ 2 log(1/α)). Leaving either
regime drives ρ to 0, and both limits are now PROVED for deterministic alternation (Thms A and V). The one
mechanism behind the rise (the adaptive null makes zero labels free, so a one-sided test only learns from about
half the labels) is identified and proved at the level of likelihood ratios (Lemma A, Prop P). Its cure, re-timing
queries so that every label is "aligned", is also proved (Thm A). **No main-track-level positive theorem exists
from this attempt.** What exists is a sharp *negative* characterisation of where a large relative premium can live
(per the publication-outcome rule this is evidence for scoping, not a finding to publish on its own). A positive
theorem would have to be stated in a joint scaling regime (T − B = O(1) and log(1/α) ≍ B), which was not proved.

---

## 1. Setting

Symmetric stationary anti-persistent family of SP1: `t01 = t10 = t ∈ (1/2, 1]`, `e0 = e`, `e1 = 1 − e`,
`0 < e < 1/2`, prior 1/2, `g = (1−2e)²`, `I_e := KL(Ber(1−e) ‖ Ber(1/2)) = log 2 + (1−e)log(1−e) + e log e`,
`L := log((1−e)/e)`. Main focus: **t = 1** (deterministic alternation), d = 1, c = k = 0, α ≤ 1/2 unless stated.

At t = 1, `S_s = θ` for odd s and `1 − θ` for even s, with θ = S_1 ~ Ber(1/2). For labels queried at times τ_j,
put `X_j := Y_{τ_j}` if τ_j is odd and `1 − Y_{τ_j}` if τ_j is even. Given θ the X_j are i.i.d. Ber(1−e) (θ = 1)
or Ber(e) (θ = 0), whatever the query times (uses `e1 = 1 − e0`). With `D_n := Σ_{j≤n}(2X_j − 1)`,
`P(θ = 1 | X_{1:n}) = λ^{D_n}/(1+λ^{D_n})`, λ = (1−e)/e. For the calendar 1..B with d = 1 the per-step gain of
action 1 over action 0 at time t is

`w_t = s_t·(1−2e)·tanh(D_{n_t} L/2)`, `s_t = (−1)^{t+1}`, `n_t = min(t−1, B)`,

and the alternative's predictive probability of label i is `q_i = 1/2 + w_i/2` (labels 1..i−1 are released at i).
Write `m(D) := (1−2e) tanh(|D| L/2)`; note `m(±1) = g`.

---

## 2. T1: fixed calendars

### Theorem T1 (causal risk recursion) — PROVED

Any HMM, d, c, k. Fix a label-independent query calendar `τ_1 < … < τ_B` and a mixture μ of pure plans that all
follow it before their first promotion (after promotion anything is allowed). Index the generated-label tree by
`h ∈ {0,1}^j`, j = 0..B, and let `x(h)` be the μ-probability that the first promotion occurs while the generated
history is exactly h (i.e. at a time `s ∈ [τ_j, τ_{j+1})`, a promote-and-query at τ_{j+1} counting at h). Then

`sup_ν P_ν(promote) = R(∅)`, where `R(h) = x(h) + max(R(h0), (R(h0) + R(h1))/2)` and `R(h) = x(h)` at depth B.

*Proof.*
1. **What the null sees.** Before the first promotion every pure plan plays action 0 and queries on the fixed
   calendar, so the public history on the not-yet-promoted event is a function of (time, generated labels). The
   learner's coins are private. A causal null's choice `p_{j+1}` at τ_{j+1} on that event is therefore a function
   of h only, and the same function for every plan in the support. After a promotion the risk is already incurred,
   so the null's later moves are irrelevant. Hence every causal null induces a label law Q with
   `Q(y_{j+1} = 1 | h) = p(h) ∈ [0, 1/2]`, and conversely every such label-adapted p is a causal null.
2. **Risk is linear in Q.** A pure plan first promotes at a node determined by the labels. Since the coins are
   independent of the labels, `P_ν(promote) = Σ_h Q(h) x(h)`.
3. **Backward induction.** The objective at node h is `x(h) + (1−p)R(h0) + pR(h1)`, linear in p, so its maximum
   over `[0, 1/2]` is attained at an endpoint: p = 0 gives R(h0), p = 1/2 gives the average. ∎

**Corollaries (PROVED).**
- (a) *Patterns.* x = 1 at one leaf y: each 0 on the path is forced (p = 0, factor 1) and each 1 costs a factor
  1/2, so `R = 2^{−#ones(y)}` against IID `2^{−B}`. For an event E (set of leaves),
  `max_{y∈E} 2^{−#ones(y)} ≤ R(E) ≤ Σ_{y∈E} 2^{−#ones(y)}`.
- (b) *Increasing f.* If `f(y) := Σ_{h⊆y} x(h)` is coordinatewise nondecreasing then by induction `R(h1) ≥ R(h0)`
  at every node, the max is always the average, and `R(∅) = E_{IID} f`. This is Lemma Zc in fixed-calendar form.
- (c) *Least-favourable null (T1-LF).* The set 𝒬 of label laws with conditionals in [0, 1/2] is convex (a mixture of
  two such laws has conditionals that are weighted averages). The linearised recursion makes
  `V_causal^cal(α) = min{C(x) : R(∅) ≤ α}` a finite LP; LP duality gives
  `V_causal^cal(α) = max_{λ≥0, Q∈𝒬} [min_x (C(x) + λ⟨x, Q⟩) − λα]`. So a single least-favourable Q (which may
  depend on α) exists, and the inner problem is an optimal-stopping DP against one null law.
- (d) *Not a capacity (T1-cap, exact enumeration, `wpG_capacity_v1.json`).* `v(E) = sup_Q Q(E)` satisfies
  `v(A∪C) + v(A∩C) ≤ v(A) + v(C)` for all pairs at B = 2, but fails for 80 pairs at B = 3, e.g.
  A = {001, 101}, C = {001, 110}. The pattern formula (a) and the up-set identity (b) were confirmed on all 8 and
  20 up-sets. So the Huber–Strassen 2-alternating-capacity theorem cannot be used to get an α-free
  least-favourable law.

### Calendar reductions

**Lemma CAL-t1 (PROVED).** t = 1, `e1 = 1 − e0`, c = 0, any d, k, prior, α. For every pure plan π there is a pure
plan π^g that queries at 1..B with `C(π^g) ≤ C(π)` and equal IID risk. Hence the calendar 1..B is WLOG for V*_IID.

*Proof.* As Lemma CAL (`MULTILABEL_ZERO_PREMIUM.md` §2.1), with one change. π^g feeds π's virtual j-th label the
flipped value `Y_j ⊕ [τ_j ≢ j mod 2]`, which it knows by `τ_j + d ≥ j + d`. Given θ and the past, the flipped
calendar label is `Ber(e_{θ ⊕ (τ_j−1 mod 2)})` (symmetric emissions), which is the law of π's label at τ_j. Under
the IID null both are Ber(1/2) i.i.d. Pre-promotion actions are 0 for both, and after promotion π^g has weakly more
information and plays the optimal continuation. ∎

**The flip breaks the causal problem.** It turns `p ≤ 1/2` into `p ≥ 1/2` on flipped coordinates, so the proof
does not transfer.
- **ADAPT (NUMERICALLY VERIFIED, `wpG_exact_longT_v1.json`).** For T − B ≤ 3 the calendar LP equals exact
  V*_causal in 14/14 cells (`wpG_check_t1_v1.json`; T ≤ 8, B ≤ 5, e ∈ {1/10, 1/5}, α ∈ {1/20..1/2}; max
  difference 4e-16). For larger T − B the exact causal learner is strictly better. At e = 1/10, α = 1/20:
  - B = 2: exact Γ = 0.032 at T = 6, 8, 10, 12, 14, whereas the calendar Γ is 0.032, 0.048, 0.064, 0.080, 0.096;
  - B = 3: exact Γ alternates 0.11648 (odd T) / 0.17472 (even T) for T = 9..13, whereas the calendar Γ grows to 0.293;
  - B = 4: exact Γ = 0.300, 0.420, 0.315 at T = 10, 11, 12 (calendar 0.355, 0.534, 0.473).
  Calendar = exact in every checked cell with T − B ≤ 4 (6 more cells), and calendar > exact in every checked cell
  with T − B ≥ 6. The cell (T, B) = (9, 6) could not be certified: FCG-fast did not terminate in 100 iterations
  (recorded in the JSON).
  The mechanism is Theorem A below.
- **t < 1.** The calendar 1..B is not WLOG even for V*_IID. Against the 280 certified k = 0 F_anti cells of the
  wpC2 run (t ∈ {3/4, 9/10}), the calendar LP is strictly worse for V_IID in 147 cells and for V_causal in 184,
  and is never below the certificate.

---

## 3. T2: deterministic alternation (t = 1, d = 1, c = k = 0)

### Lemma A (alternation) — PROVED

On every label path of the calendar 1..B:
- (i) `w_1 = 0` and `q_1 = 1/2`;
- (ii) `w_t > 0 ⇒ w_{t+1} ≤ 0`;
- (iii) at most ⌊B/2⌋ of `q_1..q_B` exceed 1/2.

*Proof.* (i) No labels are released at t = 1. (ii) `w_t > 0` means `D_{n_t} ≠ 0` with sign `s_t`. D moves by at
most 1 per step, so `D_{n_{t+1}}` has sign `s_t` or is 0. Since `s_{t+1} = −s_t`, this gives `w_{t+1} ≤ 0`.
(iii) `q_i > 1/2 ⇔ w_i > 0`. By (i) and (ii) there is at most one such i in each pair (2,3), (4,5), …, and these
pairs cover 2..B with ⌈(B−1)/2⌉ = ⌊B/2⌋ pairs. ∎

Numerical confirmation: `wpG_lrbound_v1.json`, 64 (e, B) rows, B ≤ 16. The maximum count equals ⌊B/2⌋ exactly.

**Consequence (RIPr null).** Let `Q*` be the causal null with `p_i = min(q_i, 1/2)`. It agrees with the
alternative on every label with `q_i ≤ 1/2`, so these labels are "free" for the null. On the other labels the
per-label likelihood ratio is at most `2(1−e)`. Hence `max_y P_A(y)/Q*(y) ≤ (2(1−e))^{⌊B/2⌋}` and
`KL(P_A ‖ Q*) ≤ B·I_e/2`; both hold in all 64 rows. By contrast `max_y P_A(y)/2^{−B} ≥ (2(1−e))^B/2`. This is
the precise form of the lead hypothesis: the adaptive null halves the informative exponent of a fixed calendar.

### Proposition L (long-horizon limit for a fixed calendar) — PROVED

For X ∈ {IID, causal} define the static slope problem

`S_X(α) := max { Σ_y P_A(y) m(D_B(y)) f(y) : f ∈ [0,1]^{{0,1}^B}, Risk_X(f) ≤ α }`,

with `Risk_IID(f) = 2^{−B} Σ f` and `Risk_causal(f) = R(f)` (the T1 recursion with leaf values f). Then for every
T ≥ B+1:

`⌊(T−B)/2⌋·S_X(α) ≤ VOI_X^cal(T) ≤ (1−2e)⌊B/2⌋ + ⌈(T−B)/2⌉·S_X(α)`.

So `ρ^cal(T) → ρ_∞^cal(B, α) := 1 − S_causal/S_IID` as T → ∞. By CAL-t1 the IID side is the true V*_IID.

*Proof.*
- **Lower bound.** Take the optimal static f. At time B+1 promote, with probability f(y), at the first t ≥ B+1
  with `w_t > 0`. The risk is `Risk_X(f) ≤ α`. Risk is monotone in f; if D_B = 0 we do not promote, which only
  lowers the risk. After promotion the free continuation gains at least `m(D_B)` at each of the
  `≥ ⌊(T−B)/2⌋` steps of the right sign in [B+1, T].
- **Upper bound.** For any calendar policy with first promotion σ, the VOI is at most `Σ_t E_A[1{σ ≤ t}(w_t)^+]`.
  For t ≤ B, Lemma A(i, ii) allows at most ⌊B/2⌋ positive steps, each ≤ 1−2e. For t > B,
  `w_t = s_t m(D_B)·sign`, and at most ⌈(T−B)/2⌉ of those steps have the right sign. With
  `f_σ(y) := P(σ ≤ T | y)` the sum is `≤ ⌈(T−B)/2⌉·Σ_y P_A(y) m f_σ(y)`. By T1,
  `Risk_X(policy) = Risk_X(f_σ) ≤ α`.
∎

**Exact small cases (PROVED).**
- **B = 1.** `S_IID = S_causal = gα` (α ≤ 1/2), so ρ_∞ = 0. This agrees with SP1-D: Γ is bounded in T and ρ ~ 1/T.
- **B = 2.** Only the patterns 10 and 01 have |D| = 2, with weight `P_A·m = g/2` each; the |D| = 0 patterns have
  weight 0. So `S_IID = 2αg` (α ≤ 1/2). The causal LP is: maximise `f10 + f01` subject to `f01/2 ≤ α` and
  `f01/4 + f10/2 ≤ α`. It has primal `(f01, f10) = (2α, α)` and dual `(1, 2)`, both of value 3α. Hence
  `S_causal = (3/2)αg` and **ρ_∞^cal(2, α) = 1/4**. The calendar LP gives 0.25 at T − B = 30, but the true value
  is smaller (ADAPT, Theorem A).

### Proposition P (small-α regime of the calendar slope problem) — PROVED

For `α ≤ 2^{1−B}`: `ρ_∞^cal(B, α) ≥ 1 − 2 / ((1−2e)(2(1−e))^{⌊B/2⌋})`.

*Proof.*
- **IID side.** The two patterns with |D| = B have weight `½[(1−e)^B + e^B]·m(B) ≥ (1−e)^B (1−2e)²/2` (using
  `tanh(BL/2) ≥ tanh(L/2) = 1−2e`) and IID risk `2^{−B}` each. For `α ≤ 2^{1−B}` putting f on them gives
  `S_IID(α) ≥ α(2(1−e))^B (1−2e)²/2`.
- **Causal side.** For any f, `Σ P_A m f ≤ (1−2e) Σ P_A f ≤ (1−2e)·max_y(P_A/Q*)·Σ Q* f`, and
  `Σ Q* f ≤ R(f) ≤ α`. By Lemma A this is at most `(1−2e)(2(1−e))^{⌊B/2⌋}α`.
- Divide.
∎

*Check* (`wpG_static_t1_v1.json`, exact-sort IID, LP causal, e ∈ {1/50, 1/10, 1/5}, B ≤ 17): all 222 cells with
`α ≤ 2^{1−B}` satisfy the bound. Example: e = 1/50, B = 11, α = 2^{−10} gives 0.965 ≥ 0.928.

### Theorem A (time slack removes the premium; t = 1) — PROVED

d = 1, c = k = 0, any B, α ∈ (0, 1/2], e ∈ (0, 1/2). For every T ≥ 2B,

**`Γ(T) ≤ (1−2e)⌊B/2⌋ + S_IID(α)(B/2 + 1) ≤ (1−2e)(B + 1)`**,

and `C₀ − V*_IID ≥ ⌊(T−B)/2⌋ S_IID(α)`. Hence `ρ(T) = O(B/T) → 0` as T → ∞ at fixed B.

*Proof (aligned re-timing).*
1. **The aligned learner.** Query label 1 at τ_1 = 1. Given `D_{i−1}` (visible at `τ_{i−1} + 1`; labels released
   at an event condition its action and query, `first_promotion_decomposition.py` l. 209), query label i at the
   first `s ≥ τ_{i−1} + 1` with:
   - s odd, if `D_{i−1} > 0`;
   - s even, if `D_{i−1} < 0`;
   - `s = τ_{i−1} + 1`, if `D_{i−1} = 0`.
   So `τ_i ≤ 2i − 1`, and every label is released by 2B.
2. **The query-order encoding is monotone.** Let `z_i := Y_{τ_i}`. By the parity choice, `z_i = 1` iff X_i agrees
   with the sign of `D_{i−1}` (when `D_{i−1} = 0`, |D| becomes 1 either way). So `|D_i| = 1` if `D_{i−1} = 0`, and
   `|D_i| = |D_{i−1}| + 2z_i − 1` otherwise. Also `|D_i| ≡ i (mod 2)`.
   - Claim: `z ≤ z′` coordinatewise implies `|D_i(z)| ≤ |D_i(z′)|` for all i.
   - Induction: equal parity rules out the pair (1, 0). If both values are 0, both move to 1. If only the smaller
     is 0, it moves to 1 ≤ the other's new value (≥ 1). If both are ≥ 1, the step is monotone.
   - Hence any nondecreasing `f(|D_B|)` is a nondecreasing function of z.
3. **Same laws.** Given θ the X_i are i.i.d. as on the calendar, so `(θ, |D_B|)` has the calendar law under A.
   Under the IID null, z is i.i.d. Ber(1/2), and so is X.
4. **Safe use of the IID optimum.** The weights `P_A(y)m(D_B)` are increasing in |D_B| and IID risk is uniform.
   So an optimal static IID f* can be taken as `1{|D_B| > κ} + γ1{|D_B| = κ}`, nondecreasing in |D_B|. Implement it
   with a private uniform U: promote iff `U ≤ f*`, at the first t ≥ 2B with `w_t > 0`. Each pure plan (fixed U)
   has a z-up-set event, so by Lemma Zc (query-order coupling; audited) its causal risk equals its IID risk
   `E_IID f* ≤ α`.
5. **Count.** Its VOI is `≥ ⌊(T−2B+1)/2⌋ S_IID(α)`. By Prop L and CAL-t1,
   `C₀ − V*_IID ≤ (1−2e)⌊B/2⌋ + ⌈(T−B)/2⌉ S_IID(α)`. Subtracting gives the bound, using `S_IID ≤ 1−2e`.
   The lower bound on `C₀ − V*_IID` is Prop L.
∎

*Check.* At B = 2 and B = 3 the exact Γ is constant in T (ADAPT table); the bound (0.8·3 = 2.4, resp. 3.2) is
loose but valid.

### Theorem V (large budget removes the relative premium; t = 1) — PROVED

d = 1, c = k = 0, α ∈ (0,1), any B ≥ 1, T ≥ B+1. Let
- `K_α := 2 log(4(1−e)/α)/I_e`;
- `π_B := exp(−2(⌊B/2⌋ I_e − log(2/α))² / (⌊B/2⌋ L²))` if `⌊B/2⌋ I_e > log(2/α)`, else 1.

Then

`Γ ≤ ((1−2e)/2)·(K_α + T π_B)` and `ρ ≤ (K_α + T π_B) / ((T−1)(1−2e) − K_α − T π_B)` (when the denominator is > 0).

Hence `sup_{T≥B+1} ρ → 0` as B → ∞ at fixed α. At fixed B, `lim sup_T ρ ≤ π_B/((1−2e) − π_B)`. And at
`T − B = O(1)`, Γ stays bounded in B by `(1−2e)K_α/2 + o(1)`.

*Proof.*
1. **Test.** For θ = 1 the state is 1 at odd times, so bet on odd labels; for θ = 0, on even labels. Put
   `E^{(1)}_n = Π_{odd i≤n} φ(Y_i)` and `E^{(0)}_n = Π_{even i≤n} φ(Y_i)`, with
   `φ(y) = 1 + (1−2e)(2y−1) ∈ {2e, 2(1−e)}`, and `E_n = (E^{(1)}_n + E^{(0)}_n)/2`.
   - Under any causal null, `E[φ(Y_i) | past] = 1 + (1−2e)(2p_i − 1) ≤ 1`, so `E_n` is a nonnegative
     supermartingale with `E_0 = 1`.
   - Ville: `P_ν(sup_n E_n ≥ 1/α) ≤ α`.
2. **Policy.** Query at 1..B. Let τ be the first n ≤ B with `E_n ≥ 1/α`. Promote at the first t ≥ τ+1 with
   `w_t > 0` and continue optimally. The promotion event is contained in the Ville event, so this policy is
   causal-feasible.
3. **Lost gain.** Gains with `w_t ≤ 0` are 0. So `VOI_full − VOI_test = E_A Σ_{t<σ} (w_t)^+`. By Lemma A(ii),
   this is at most `(1−2e)·E_A[τ/2]` on {τ ≤ B} and `(1−2e)T/2` otherwise. Since the IID value of information (bounded by the
   unconstrained calendar optimum, WLOG by CAL-t1 at α = 1) satisfies VOI_IID ≤ VOI_full, we get `Γ = VOI_IID − VOI_causal ≤ VOI_full − VOI_test`, with `E_A[τ; τ ≤ B] ≤ E_A τ_∞ ≤ K_α` (τ_∞ the unrestricted hitting time).
4. **Detection time.** Under θ = 1, τ ≤ the first n with `E^{(1)}_n ≥ 2/α`. That is a random walk over odd
   labels with i.i.d. increments of mean I_e and steps ≤ log(2(1−e)). Wald with bounded overshoot gives
   `E N ≤ log(4(1−e)/α)/I_e` odd labels, so `E τ ≤ 2E N`; θ = 0 is symmetric. Hoeffding over ⌊B/2⌋ increments
   (range L) bounds `P_A(τ > B) ≤ π_B`.
5. **Denominator.** `VOI_IID ≥ VOI_test ≥ VOI_full − bound`. Also
   `VOI_full ≥ Σ_{t=2}^T E(w_t)^+ = Σ_t ½ E m(D_{n_t}) ≥ (T−1)g/2`, by symmetry and because E m(D_n) is
   nondecreasing in n (more information) with m(D_1) = g.
∎

*Check* (`wpG_alpha_t1_v1.json`): the betting policy's exact worst-case causal risk is ≤ α in 240/240 cells.
- At e = 1/10, α = 1/20, `K_α ≈ 19.5` labels. The theorem is informative only for B ≳ 50, far beyond the
  computed range.
- It is an asymptotic statement, and it is consistent with the data (it is an upper bound).

### Numerical picture (t = 1; calendar LP: an upper bound on Γ, exact for T − B ≤ 4 where checked)

`wpG_grid_t1_e1_10_v1.json` and `wpG_grid_t1_e1_5_v1.json` (float HiGHS, 0.6 h CPU in total). ρ^cal at α = 1/20,
e = 1/10, rows B, columns T − B:

```
B   1     2     3     4     6     8    | 30 (≈ ρ_∞^cal)
3  0.563 0.455 0.569 0.451 0.451 0.451 | 0.451
5  0.679 0.693 0.708 0.692 0.692 0.692 | 0.692
6  0.725 0.740 0.747 0.714 0.691 0.679 | 0.647
8  0.747 0.714 0.695 0.630 0.569 0.530 | 0.471
10 0.700 0.639 0.614 0.565 0.504 0.460 | 0.325
12 0.617 0.565 0.533 0.501 0.455 0.427 | 0.356
14 0.534 0.504 0.487 0.471 0.447 0.428 |  –
```

Static slope ρ_∞^cal(B, α) (`wpG_static_t1_v1.json`, e = 1/10):

```
alpha:  1/2   1/4   1/10  1/20  2^-5  2^-7  2^-10
B=2   0.250 0.250 0.250 0.250 0.250 0.250 0.250
B=5   0.063 0.075 0.538 0.692 0.692 0.692 0.692
B=8   0.026 0.137 0.224 0.459 0.594 0.865 0.865
B=11  0.013 0.070 0.228 0.299 0.314 0.762 0.947
B=14  0.009 0.043 0.120 0.273 0.338 0.530 0.896
B=17  0.004 0.024 0.099 0.171 0.231 0.449 0.832
```

**Reading.**
- At every fixed α, ρ rises with B, peaks, and then falls. The peak moves to larger B as α falls, roughly where
  `(2(1−e))^{B/2} α ≈ 1`.
- At α → 0 with B fixed, ρ_∞^cal → 1 (Prop P). At B → ∞ with α fixed, ρ → 0 (Thm V).
- With slack in T, the true ρ → 0 at every B (Thm A). The calendar ρ_∞^cal therefore overstates the true
  long-horizon premium.

### Scaling with α (`wpG_alpha_t1_v1.json`)

- **B fixed, α ↓ 0.** Below a B-dependent threshold Γ becomes **linear in α** and ρ constant: for B = 4 that
  happens from α ≈ 1/16; for B = 12 it has not happened by α = 2^{−10}. This is the same "single coin" regime as
  B = 1 (SP1).
- **Large α.** Γ is concave and non-monotone in α. Example: B = 12, T = 32, e = 1/50, Γ peaks at ≈ 8.3 near
  α = 2^{−9}.
- **Plateau value.** The plateau value of ρ increases with B toward 1 (Prop P).

---

## 4. Artefact check (requested)

| Question | Answer | Basis |
|---|---|---|
| Is the rise of ρ in B at T ≈ B+3 a T–B coupling artefact? | **Partly.** At fixed T, ρ hardly changes with B once B ≥ T−3. For example, at T = 9 the calendar ρ is 0.747 for B = 6, 7, 8: the last labels arrive too late to matter. In the wpC2 table the "B" axis is largely a "T" axis | grid |
| ρ at fixed α, growing T, fixed B | **→ 0** (true premium). Exact Γ is constant in T at B = 2, 3. The calendar class instead converges to ρ_∞^cal > 0, an artefact of fixing query times | Thm A; ADAPT |
| ρ at fixed T − B, growing B | Rises then falls. At T − B = 1, α = 1/20: 0.68 (B=4) → 0.75 (B=8) → 0.53 (B=14), calendar values (upper bounds). → 0 as B → ∞ | grid; Thm V |
| VOI shrinking at small α? | Not the driver. At small α both Γ and VOI are linear in α, so ρ is constant there. The driver is the information exponent: one-sided tests learn from ≈ half the labels | Prop P, Lemma A |
| Does the data's t = 9/10 family behave the same? | Not computed beyond B = 6. Calendar LPs are not valid there (§2). CONJECTURED: the same rise-then-fall, with T-slack and B-growth both killing ρ | – |

---

## 5. T3: stochastic t ∈ (1/2, 1)

**No lower bound was proved, and none can be uniform in B at t = 1.**
- At t = 1, Thm V gives ρ → 0 as B → ∞, and Thm A gives ρ → 0 as T → ∞. So no `c(t, e, α) > 0` lower bound
  uniform in B or T exists at t = 1.
- **CONJECTURED for t < 1.** Both arguments extend:
  - (V) the one-sided betting test on aligned labels has positive growth rate under the ergodic HMM;
  - (A) re-timing to times with `q > 1/2` costs bounded time.
  Proofs need concentration for HMM-driven increments and were not written.
- The certified wpC2 cells (B ≤ 6) remain the only t < 1 evidence; no new t < 1 cells were certified in this
  attempt, since the budget went to the t = 1 analysis.

---

## 6. T4: prior art for the mechanism (read status)

| Ingredient | Closest known result | Status of source | Reduction |
|---|---|---|---|
| T1 recursion, bang-bang worst null | Fauß–Zoubir–Poor (2020, Ann. Statist.) rectangular per-step uncertainty, Thm 6 history-adaptive least-favourable laws | OPENED in `PRIOR_ART_AUDIT.md` (not re-opened here) | T1 is a direct special case: a per-node composite null with a two-point extreme set. **Not novel** |
| T1-LF (single least-favourable law per α) | LP duality / robust NP for convex null sets (Lehmann–Romano-style least-favourable distributions) | not opened (textbook, META) | Routine |
| α-free least-favourable law | Huber–Strassen (1973) 2-alternating capacities | META via the Fauß et al. 2021 survey (OPENED by WP F) | **Does not apply**: the upper probability is not 2-alternating for B ≥ 3 (T1-cap) |
| Up-set safety | Strassen / Kamae–Krengel–O'Brien; Doerr Lemma 1.8.7 (Lemma Zc) | OPENED (prior audit) | Known |
| Betting test in Thm V | Waudby-Smith & Ramdas (JRSSB 2024), test supermartingales for conditional-mean nulls; Ville's inequality | OPENED at Prop. 3 in the prior audit | The test is standard |
| "Zero labels are free" (RIPr agrees with A where q ≤ 1/2; halved KL) | Reverse information projection / GROW e-variables (Grünwald, de Heide, Koolen, "Safe testing") | **not opened in this attempt** (from memory) | Likely known in spirit (one-sided composite nulls cost the KL of the projected law). Lemma A's pathwise ⌊B/2⌋ count is a model-specific fact |
| Re-timing (Thm A) | Adaptive sampling / active sequential hypothesis testing (Chernoff 1959; Naghshvar–Javidi) | not opened (META) | The idea "choose when to sample to make the evidence one-sided" is in the spirit of active testing. Whether the monotone-encoding argument appears elsewhere was **not checked** |

The T1/T2 statements reduce to known robust-testing tools, plus elementary model-specific lemmas (A, P, A-thm).
No claim of novelty is made for any ingredient.

---

## 7. Limitations

- **Calendar LP.** It is a float LP (HiGHS, tolerance 1e-10). It is exact only where cross-checked: 20 cells with
  T − B ≤ 4 (B ≤ 5). For T − B ≥ 6 it is strictly above the exact Γ in every checked cell (ADAPT). It is always an
  upper bound on Γ (V*_IID is exact by CAL-t1; V_causal^cal ≥ V*_causal). Grid ρ values with T − B ≥ 5, and all
  values with B ≥ 6, are therefore upper bounds on the true ρ, not exact values.
- **Scope of Thms A and V.** Both are for t = 1, d = 1, c = k = 0, symmetric emissions, prior 1/2. With c > 0,
  re-timing and extra queries cost money; with k > 0 nothing changes in the arguments except the switch count,
  which was not checked.
- **Thm V constants.** They are crude (K_α ≈ 19.5 at the data's parameters). It is a statement about
  asymptotics, not about the computed range.
- **The positive side is still open.** No theorem shows ρ ≥ c > 0 in a joint regime (T − B = O(1),
  log(1/α) ≍ B). Proposition P is the closest, and it is for the calendar class only.
- **Review.** Same-family only. Lemmas A, Thm A step 2 (parity-monotone reflection) and Thm V step 3 most need an
  independent check.

## 8. Reproduction

All from the repo root, `uv run --no-sync python …`, outputs in `results/` (refuse-overwrite):

| Script | Args | Output | Result |
|---|---|---|---|
| `wpG_lib.py` | library: calendar LP; betting-policy evaluator | – | – |
| `wpG_scan.py` | `OUT check` | `wpG_check_t1_v1.json` | 14/14 exact match |
| `wpG_scan.py` | `OUT grid 1/10 14` | `wpG_grid_t1_e1_10_v1.json` | grid |
| `wpG_scan.py` | `OUT grid 1/5 13` | `wpG_grid_t1_e1_5_v1.json` | grid |
| `wpG_alpha.py` | `OUT` | `wpG_alpha_t1_v1.json` | α-scaling; 240/240 betting policies causal-safe |
| `wpG_static.py` | `OUT 17` | `wpG_static_t1_v1.json` | slope problem; Prop P 186/186 |
| `wpG_capacity.py` | `OUT` | `wpG_capacity_v1.json` | not 2-alternating at B = 3 |
| `wpG_lrbound.py` | `OUT` | `wpG_lrbound_v1.json` | Lemma A / LR bound 64/64 |
| `wpG_exact_longT.py` | `OUT` | `wpG_exact_longT_v1.json` | ADAPT: calendar ≠ exact for large T − B |
| `wpG_summarize.py` | grid JSONs | stdout | tables |

**Assessment: PIVOT** away from a general-budget positive theorem in this family. The large relative premiums are
confined to a time-tight, budget-below-detection-scale regime. Any further attempt should fix that joint scaling
first, and must model query-time choice, because the fixed calendar overstates the premium.

## Lead verification (2026-11-11)

`gamma_cell` (exact, certified), t = 1, e = 1/10, B = 2, d = 1, c = k = 0, α = 1/20: **T = 6: Γ = 0.032, VOI = 0.128
(ρΓ = 0.25); T = 12: Γ = 0.032, VOI = 0.32 (ρΓ = 0.10).** The premium is constant in T while the value of information
grows, as claimed; the relative premium falls. Theorems A and V and Lemma A are PROVED (agent) but **not
independently reviewed**; the publication decision does not depend on them.
