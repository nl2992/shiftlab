# WP B — Implicit learner-side optimisation (families B1–B4)

**Date:** 2026-11-10. **Branch:** `research/paper4-antitone-frontier-2026-11-09` (uncommitted work, base `affd5077`).
**Question:** can nonanticipating learner acquisition/switching policies be optimised *without* explicitly building
the full learner public-history tree, while keeping exact full-history causal-null safety and a global bound
`L <= V* <= U` against the **unrestricted** optimum?

Status labels: PROVED · NUMERICALLY VERIFIED · CONJECTURED · FALSIFIED · PRIOR ART · UNRESOLVED.
Citation honesty: "(read)" means read in this or a cited repo audit with a primary link; "(unverified)" means cited
from memory, not re-read this session. Same-family review only (ARIS external reviewers BLOCKED, see `BLOCKERS.md`).

Scripts: `scripts/paper4_continuation/theory_B/`. Outputs (refuse overwrite):
`docs/paper4_continuation/theory_B/results/`. Every number below is copied from those JSON files.

## 0. Common setting and the one bound that is always valid

After the exact first-promotion decomposition (`docs/switching_first_promotion_decomposition_v1.md`), the learner
chooses, before its first promotion, a query bit and a promote bit at each event; promotion pays the exact
alternative continuation value `V_t(b, rem, q)`. Let `P` be the finite set of deterministic pre-promotion policies,
`C(p)` the alternative cost and `R_nu(p)` the first-promotion probability under pure endpoint null `nu`
(`p_t in {0,1/2}` keyed by the full generated history, Lemma 2 of `docs/paper4/theory/01`). The problem is the LP

    V* = min_{z in Delta(P)} sum_p z_p C(p)   s.t.  sum_p z_p R_nu(p) <= alpha  for all nu in N_ext.

**Proposition 0 (Lagrangian bound; PROVED, standard).** For any finite `K ⊆ N_ext` and any `lam in R_+^K`,

    g_K(lam) = min_{p in P} [ C(p) + sum_{nu in K} lam_nu R_nu(p) ] - alpha * sum lam_nu  <=  V*.

*Proof.* Let `z*` attain `V*`. Its objective plus `sum lam_nu (R_nu(z*) - alpha) <= 0` is at most `V*`, and the
minimum of a linear function over `Delta(P)` is attained at a vertex `p in P`. ∎ The minimum must be over the
**whole** of `P`. If pricing is restricted to `P' ⊊ P`, `g'` is only a bound for the restricted problem and can
exceed `V*` (measured in §1.4). If pricing is solved only approximately, the bound stays valid when a certified lower
bound on the pricing minimum is used in place of the minimum (this is what B2 does).

Prior art: Lagrangian / Dantzig–Wolfe bounds with exact pricing (Lübbecke & Desrosiers 2005, unverified);
constrained-POMDP column generation (Walraven & Spaan, JAIR 2018; repo link in
`CANDIDATE_B_POLICY_PRICING_AUDIT_V1.md`, not re-read this session).

## 1. B1 — implicit policy-column generation

### 1.1 Exact formulation

Restricted master over columns `P' ⊆ P` and rows `K ⊆ N_ext` (IID ∈ K initially). Inner loop: column generation
with exact pricing at the master duals `lam`. Outer loop: exact full-null separation of the master's root mixture
(the null sees public actions and every generated outcome, not the root coin). The best response is an endpoint
strategy keyed by the full generated history, and it becomes a new row. On termination `U` is the exact cost of the
mixture, root-repaired with never-promote if needed, and `L = max g_K(lam)`. Implementation:
`b1_pricing.py` (pricing DP, column extraction, mixture verifier), `b1_run.py` (driver).

### 1.2 The pricing problem and its minimal sufficient state

For fixed `lam`, pricing is an unconstrained finite-horizon POMDP with hidden root mode
`m in {alt, iid, nu_1..nu_k}`, prior masses `(1, lam_iid, lam_1, ...)`. The learner observes only released labels.
**Pricing key** (per unit of alternative mass):

    kappa(h) = ( t, rem, b_alt(h),  rho(h) = P_iid(h)/P_alt(h),
                 for each nu_i: { (pending generated outcomes c, [nu_i]_{h,c}, P_nu_i(h,c)/P_alt(h)) } )

Here `b_alt` is the exact belief over (regime, pending outcomes), and `[nu]_{h,c}` is the Myhill–Nerode residual class
(minimal-automaton state) of `nu` after the generated history `(h, c)`.

**Proposition 1.1 (sufficiency; PROVED).** Stage costs, promotion rewards, transition kernels and the next key are
functions of `kappa`. Therefore an exact Bellman recursion on keys returns the pricing minimum over the
**unrestricted** class `P`, and a key-measurable optimal column exists.
*Proof.* Under `alt` the HMM filter over (regime, pending) is the standard sufficient statistic. Under `iid` the
pending outcomes are uniform and independent of the learner's information, so only the likelihood ratio matters.
Under `nu_i` the future kernel depends on the generated history only through its residual class, and the learner
cannot observe pending outcomes, so it must carry the joint (pending, class, likelihood) measure. Linearity of the
objective in the unnormalised mode masses gives the per-alt-unit recursion. ∎
**Numerical check:** in all 10 cells the memoised key DP equals the un-memoised tree DP exactly (`memo_equals_tree_dp`),
and on 6 cells it matches an independent sequence-form LP of the same Lagrangian (`lp_check_abs_diff = 0.0`).

Minimality, stated carefully: the key is the belief over the hidden mode × physical/pending state, plus the residual
classes. For exactness that is uniform over all `lam` and all cost parameters, the belief cannot be coarsened. This is
the standard belief-sufficiency property of POMDPs (Åström 1965; Smallwood & Sondik 1973, unverified). For one fixed
`lam`, the coarser value-equivalence quotient exists, but computing it requires solving the problem. Candidates B and
C (`CANDIDATE_B_PRICING_STATE_COUNTEREXAMPLE_V1.md`, `CANDIDATE_C_RESPONSE_QUOTIENT_LOWER_BOUND_V1.md`) show that
residual classes of arbitrary nulls cannot be dropped.

### 1.3 Measured pricing-state counts and exact column generation

`results/b1_column_generation_v1.json` (script `b1_run.py`, SHA-256 of output
`9002250456a755cd87f09d14221d7aef4382c74abed0f7f7bb47d4e57d2cb64d`). Here `|I|` is the number of learner
pre-promotion information sets (public tree), "keys" is the number of IID-only pricing keys, and "alt-only" is the
number of keys when only `(t, rem, b_alt)` is used.

| Cell | regime | T,B,d | `\|I\|` | keys | alt-only | null rows | keys with rows | CG `L` = `U` | `V*` (FCG) |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| C1 | HMM 1/4 | 5,2,1 | 65 | 65 | 65 | 0 | 65 | 193099/80000 | 193099/80000 |
| C2 | HMM 9/10 (reversal) | 5,2,1 | 65 | 65 | 65 | 7 | 65 | 76309/31250 | 76309/31250 |
| C3 | HMM 3/4 (reversal) | 6,3,1 | 236 | 236 | 236 | 12 | 236 | 118361/40000 (L short by < 1e-13) | 118361/40000 |
| C4 | HMM 1/4 | 6,3,1 | 236 | 236 | 236 | 0 | 236 | 461083/160000 | 461083/160000 |
| H5 | HMM 1/10 | 6,2,2 | 91 | 91 | 91 | 0 | 91 | 92179/31250 | 92179/31250 |
| C6 | HMM 3/4 (reversal) | 8,3,1 | 848 | 848 | 848 | 21 | 848 | 39589/10000 (L short by < 1e-13) | 39589/10000 |
| S1 | static | 6,3,1 | 236 | **40** | 40 | 0 | 40 | 212409/100000 | 212409/100000 |
| S2 | static | 6,2,2 | 91 | **36** | 36 | 0 | 36 | 5741/2000 | 5741/2000 |
| S3 | static | 8,3,1 | 848 | **60** | 60 | 0 | 60 | 14503/4000 | 14503/4000 |
| S4 | static | 8,3,2 | 659 | **85** | 85 | 0 | 85 | 297/80 | 297/80 |

Findings.
1. **Correctness:** exact pricing plus row generation reproduces `V*` in every cell, with `L <= V* <= U`. This
   includes the reversal cells, which needed 7, 12 and 21 causal-null rows and 12, 29 and 40 columns.
2. **No compression for HMM alternatives (transition > 0):** keys = `|I|` in all six HMM cells, with or without null
   rows, and even the alternative belief alone separates every public history. This independently reproduces
   Candidate G's 4,867 = 4,867 at T=10. Policy-column generation then just moves the tree into the pricing oracle,
   which was Candidate B's concern, now measured with exact best-response rows.
3. **Static (exchangeable) alternative (transition = 0):** keys collapse to count statistics, and the IID-relaxed
   mixture is already robust-safe, so 0 rows are needed and `L = U = V*`.

### 1.4 The restricted-pricing trap (FALSIFIED as a lower bound)

Pricing restricted to calendar policies (query whenever budget remains) gives a pseudo-bound `g'` that **exceeds
`V*`** in 8/10 cells. For example C1: 193259/80000 > 193099/80000; C2: 152857/62500 > 76309/31250; C6:
3.96339 > 3.9589; S4: 7433/2000 > 297/80. Fixed query schedules, bounded promotion windows and similar structural
*policy* restrictions therefore cannot be used to make pricing cheap if the bound is to hold for the unrestricted
optimum. Only restrictions **proved** to contain an optimal policy are admissible.

### 1.5 The admissible structural assumption: an exchangeable alternative

**Theorem B1-S (PROVED).** Assume a static alternative regime (`transition01 = transition10 = 0`; more generally,
an alternative label law that is exchangeable given a finite hidden type). Assume also fixed delay `d`, one query
per event and a hard budget `B`. Then:
(a) For `K = {iid}`, the pricing key is a function of `(t, query bits of the last d-1 events, n1, n0)`, where
`n1` and `n0` count the released positive and negative labels. Hence
`#keys <= T * 2^(d-1) * (B+1)(B+2)/2`, which is polynomial in `T` and `B` for fixed `d`. The promotion continuation DP
has the same property, with an extra deployed bit. The learner tree instead has
`sum_q binom(T,q) 2^q`-type growth.
(b) Column generation with this exact pricing yields `L_IID = V*_IID <= V*` (Proposition 0) without the tree.
(c) The returned root mixture has at most two deterministic key-measurable columns. Its exact full-causal-null risk
is computed on the product (key, generated pending outcomes, consistent-column set), whose size is at most
`3 * #keys * 2^min(B,d-1)`.
(d) If that risk is `<= alpha`, then `U = L = V*` is **certified**. Otherwise the root repair gives a valid `U`, and
row generation is required (see (e)).
(e) Row generation preserves exactness by Proposition 1.1, but the residual classes of the new rows are **not**
bounded by any proved lemma (UNRESOLVED).
*Proof of (a).* With a static type `s`, the posterior is `∝ prior(s) e_s^{n1} (1-e_s)^{n0}`. Pending outcomes are
conditionally i.i.d. given `s`, and their timing is the public query-bit window. Also
`rho = 2^-(n1+n0) / P_alt(n1, n0)`. `rem = B - n1 - n0 - #pending`. (b)–(d) follow from Proposition 0, Lemma 2 of
`theory/01` and the root-repair argument of the FCG theorem. ∎

**Measured (`results/b1_static_scale_v1.json`, `b1_static_scale.py`; tree counted combinatorially, never built):**

| T,B,d (static, e=1/4,3/4) | `L = U = V*` | pricing keys | verifier states | learner info sets | seconds |
|---|---|---:|---:|---:|---:|
| 8,3,1 | 14503/4000 | 60 | 42 | 848 | 0.0 |
| 10,4,2 | 4.52390625 | 166 | 93 | 4,867 | 0.2 |
| 14,5,2 | 6.15515625 | 359 | 214 | 110,163 | 0.5 |
| 18,6,2 | 7.647939453125 | 652 | 435 | 2,278,851 | 1.0 |
| 24,6,1 | 9.774998046875 | 560 | 483 | 27,231,472 | 0.9 |

A random screen of 40 static cells (`T in 4..8`, `B in 1..4`, `d in 1..3`, random emissions, `alpha in {1/20,1/10,1/4}`)
gave **40/40 certified optimal** (`U - L = 0`). In every cell the IID-relaxed mixture's robust risk equalled its IID
risk.

**Conjecture B1-S-Γ (CONJECTURED; NUMERICALLY SUPPORTED 44 + 5 cells):** under a static alternative with
`e0 < 1/2 < e1`, the IID-relaxation optimum of the decomposed game is robust-safe, so `Gamma = 0`. A proof would need
a monotone-event argument (P4-3) for count-measurable pricing optima. Adaptive query timing can break coordinatewise
monotonicity of the promotion event, so the proof is open. This is handed to WP C (C-1) as a candidate primitive
condition.

**Prior art.** Count sufficient statistics for exchangeable Bernoulli models in Bayesian sequential decision problems
are classical (Wald 1947; DeGroot 1970; Chernoff 1972; all unverified). The Lagrangian/CG scheme is standard (§0).
The monotone-event IID reduction is P4-3 (repo). Nothing in B1-S is a new optimisation principle. The only
problem-specific element is the exact product verifier against the causal null, and that is Krale et al.'s nature-MDP
best response for a fixed controller (`theory/01` §2).

### 1.6 B1 decision

- **General two-state HMM alternative (the registered problem): NO-GO — computational.** The minimal λ-uniform
  pricing state equals the public tree in every measured cell. Exact pricing is necessary for a valid unrestricted
  `L` (§1.4), so the oracle inherits the tree.
- **Static/exchangeable alternative: GO candidate, computational only, with NO novelty claim (prior art: sufficient
  statistics + column generation + P4-3).** It certifies `V*` exactly at T=24 (2.7×10^7 public information sets) in
  under 1 s, wherever the IID mixture is robust-safe. Scope: degenerate "shift" in which the regime never changes.
  This is not the registered HMM setting.

## 2. B2 — adaptive state refinement with a sound certificate `L_k <= V* <= U_k`

### 2.1 Exact formulation and soundness

Coarse state: the decision-time belief over hidden modes. With the IID relaxation, the modes are
`{alt s=0, alt s=1, iid}`; at `d = 1` this belief lies on a 2-simplex for every `(t, rem)`. Refinement is done with a
grid of resolution `N`.
- **`L_N` (PROVED sound, modulo floating point).** The pricing value is a min-cost POMDP value, hence concave in the
  belief. Linear interpolation on a Freudenthal/Kuhn triangulation of grid values therefore under-estimates it, and
  the monotone Bellman backup propagates the under-estimate (Lovejoy-type lower bound). The promotion continuation is
  lower-bounded in the same way on a 1-D grid in `pi`. Proposition 0 then gives
  `L_N(lam) = J_low(root) - alpha lam <= V*_IID <= V*`. This is a bound against the **unrestricted** optimum, because
  the grid bound under-estimates the exact pricing minimum over all of `P`.
- **`U_N` (exact rational).** A deterministic finite-state controller with memory `(t, rem, snapped grid point)`
  acts greedily on the grid values, and post-promotion it uses a snapped 1-D controller. Its exact alternative cost is
  evaluated on (memory × regime). Its exact full-causal-null risk is evaluated on (memory) with endpoint
  maximisation, which is the Krale nature-MDP recursion for a fixed controller; at `d = 1` no label is pending at a
  decision. Root repair with never-promote follows. Neither bound builds the learner tree.

Implementation: `b2_grid_certificate.py`; output `results/b2_grid_certificate_v1.json`. Limits of this
implementation: `d = 1` only (with `d >= 2` the simplex dimension is `2*2^(d-1)`); `L` is float64 with a 1e-9 margin,
so it is *not* a rational certificate (directed rounding or a rational re-check would be needed). `U`, its causal
risk and the repair are exact.

### 2.2 Results (global refinement `N = 4..64`, `Nc = 8N`)

| Cell | regime | `\|I\|` | `V*` | `L_8` | `L_64` | `U_16` (exact) | `U - L_64` | grid states (`N=64`) | controller memory reached | s (N=64) |
|---|---|---:|---|---:|---:|---|---:|---:|---:|---:|
| C1 5,2,1 | persistent | 65 | 2.4137375 | 2.372915 | 2.412743 | 193099/80000 = **V*** | 9.9e-4 | 32,175 | 10 | 0.9 |
| C4 6,3,1 | persistent | 236 | 2.88176875 | 2.835665 | 2.879814 | 461083/160000 = **V*** | 2.0e-3 | 51,480 | 12 | 1.6 |
| C5 8,3,1 | persistent | 848 | 3.86497390625 | 3.812819 | 3.862899 | 24735833/6400000 = **V*** | 2.1e-3 | 68,640 | 22 | 1.9 |
| C2 5,2,1 | reversal | 65 | 2.441888 | 2.377444 | 2.399771 | 76309/31250 = **V*** | 4.2e-2 | 32,175 | 10 | 0.8 |
| C3 6,3,1 | reversal | 236 | 2.959025 | 2.924331 | 2.947135 | 118361/40000 = **V*** | 1.2e-2 | 51,480 | 11 | 1.5 |
| C6 8,3,1 | reversal | 848 | 3.9589 | 3.924331 | 3.947135 | 158361/40000 (`N=64`: 39589/10000 = **V***) | 1.2e-2 | 68,640 | 13 | 1.9 |
| P12 12,4,1 | persistent | 17,656 | — | 5.749077 | 5.798214 | 5.798668 (`N=64`: 5.798576) | 3.6e-4 | 128,700 | 43 | 3.7 |
| P16 16,5,1 | persistent | 343,200 | — | 7.666877 | 7.726029 | 7.733662 (`N=64`: 7.733569) | 7.5e-3 | 205,920 | 59 | 6.2 |

`L <= V* <= U` holds in every cell with a reference (`L_le_Vstar`, `U_ge_Vstar` all true).

Findings.
1. **The upper side closes.** In all six small cells a controller with 10–22 memory states, after root repair, equals
   `V*` exactly. In the persistent cells the controller has causal risk 1/4 at activation 2/5. In the reversal cells
   it has causal risk 1 at activation 1/10 = `alpha`, so `V* = alpha C(p) + (1-alpha) C_never` for one deterministic
   controller `p`.
2. **The lower side closes only to `V*_IID`.** On persistent (Gamma = 0) cells the gap shrinks roughly like `1/N`
   (C1: 4.1e-2 → 9.9e-4). On reversal cells it stalls at the causal premium `V* - V*_IID` (C2: limit 2.4002176 vs
   `V*` 2.441888). No belief-grid refinement can remove this, because it is a constraint-relaxation bias, not a
   resolution error.
3. **The state counts are not smaller at moderate T.** For `N = 64` the grid has more states than the tree up to
   T=12 (128,700 vs 17,656). It is smaller only asymptotically (`O(T B N^2)` vs `sum_q binom(T,q)2^q`; P16: 205,920 vs
   343,200).

### 2.3 Does identifying refinement regions require examining all histories?

**For the resolution error: no.** Gaps can be localised at grid points and controller memory states (polynomially
many). The local `U`–`L` contribution of a memory state is computable on the product without histories, so
adaptive local refinement (implemented here only as global refinement) is history-free. **For the causal-premium
error: yes, in general.** Closing `L` toward `V*` when Gamma > 0 requires causal-null rows. A row is a full-history
strategy, and by §1.2/§1.3 its residual classes plus the HMM belief re-introduce the public tree. Candidate C's
universal-quotient lower bound applies to any strategy-independent abstraction of the null side.

**Prior art.** Grid-based POMDP bounds via concavity and interpolation (Lovejoy 1991; Hauskrecht 2000; unverified).
Belief-MDP over- and under-approximation with refinement in probabilistic model checking (Bork, Junges, Katoen &
Quatmann, ATVA 2020 and TACAS 2022; unverified). Abstraction refinement / CEGAR for partially observable games and
POMDPs (unverified; not read). Finite-state controllers with exact product verification (Cubuktepe et al., AAAI 2021,
repo link; Candidate J). The Krale fixed-controller best response (`theory/01`). The B2 pipeline is a composition of
these; nothing in it is new.

### 2.4 B2 decision

**NO-GO as a contribution (prior art). Retained as a computational baseline: GO candidate for a tree-free anytime
certificate in IID-tight regimes only.** It is sound for the unrestricted optimum (`L` up to float rounding) and
exact in safety. On reversal regimes it cannot certify below the causal premium, and at moderate T its state count
does not beat the tree.

## 3. B3 — certified policy distillation

### 3.1 Formulation, certificate and the cheaper-certificate question

Teacher: the exact FCG optimum (`theory/01` §4), small T. Student: a per-`(t, rem)` threshold rule on the alternative
belief `pi` (promote iff `sign (pi - theta_P) >= 0`, otherwise query iff `pi in [lo, hi]`), fitted by exhaustive
threshold search. The student is certified **directly**: exact alternative cost, exact full-causal-null risk, root
repair, giving `U_S`. The lower bound must come from elsewhere (the teacher's `V*` at small T; §0, B1 or B2 at
large T).

**Proposition B3.1 (coupling certificate; PROVED, standard).** Couple teacher and student on the same randomness and
let `D` be the event that their realised actions differ before the first promotion. Then
`|C(S) - C(T)| <= span(C) * P_alt(D)`, and for every null `nu`, `|R_nu(S) - R_nu(T)| <= P_nu(D)`, so
`R_rob(S) <= R_rob(T) + sup_nu P_nu(D)`. Computing `sup_nu P_nu(D)` is a robust reachability problem on the **joint**
product of teacher and student. Its state space contains the teacher's own verification state space, which for an
exact teacher is the public tree (§1.3). Direct student verification needs only the student product. **Hence no
divergence certificate of this type is cheaper than verifying the student directly.** This is the standard
coupling/TV argument (Lindvall, unverified); separate null and alternative versions are the two displayed
inequalities.

### 3.2 Small exact tests (`b3_distill.py`)

Recorded failures, kept: v1 distilled the root-randomised repaired teacher by majority and every student collapsed to
never-promote. v2 used the raw pre-repair teacher (same collapse). v3 used a support target for promotion only, and
the teacher's root query is randomised (`P = 2/5`), so the collapse persisted (`b3_distillation_v1..v3.json`).
**v4** uses support targets for both promotion and query, so the student is the support of the teacher's
randomisation and the root repair supplies the mixing (`results/b3_distillation_v4.json`).

| Cell | `V*` | student `U` (exact, repaired) | student causal / IID risk | coupling risk bound | `sup_nu P_nu(D)` | teacher tree info sets | rule cells |
|---|---|---|---|---|---|---:|---:|
| C1 | 193099/80000 | 193099/80000 (**= V***) | 1/4 / 1/4 | 7/10 | 3/5 | 65 | 12 |
| C4 | 461083/160000 | 461083/160000 (**= V***) | 1/4 / 1/4 | 7/10 | 3/5 | 236 | 15 |
| C5 | 24735833/6400000 | 24735833/6400000 (**= V***) | 1/4 / 1/4 | 7/10 | 3/5 | 848 | 21 |
| C2 | 76309/31250 | 12219/5000 (+1.9e-3) | 1 / 3/4 | 27/25 (> 1, vacuous) | 19/20 | 65 | 12 |
| C3 | 118361/40000 | 1895853/640000 (+3.2e-3) | 1 / 3/4 | 43/40 (> 1, vacuous) | 19/20 | 236 | 17 |

So a belief-threshold student, certified directly, is exactly optimal on persistent cells and within 0.08–0.11 % on
reversal cells. The coupling bound is valid but loose (0.7 vs the true 1/4) or vacuous (> 1). It needs the teacher
tree, while direct verification needs only the student product.

### 3.3 B3 decision

**NO-GO — prior art / computational.** Distillation reduces to Candidate J (finite-controller search plus exact
product verification plus an externally supplied lower bound). The structural teacher–student certificate is never
cheaper than direct verification, and the teacher itself needs the tree. The useful empirical fact, that compact
students reach `V*` (shared with B2), is recorded as the lead in §5.

## 4. B4 — dual decompositions exploiting first-promotion structure

### 4.1 Exact formulation

The components are already separated exactly: post-promotion continuation by the first-promotion DP (repo, standard),
alternative objective and first-promotion risk by Proposition 0, and pending outcomes inside the pricing key. The full
dual is

    V* = max_{lam >= 0, y in Y_null} min_{x in X} [ c.x + lam (x^T R y - alpha) ],

where `Y_null` is the null's behavioural (sequence-form) strategy set. This holds by LP strong duality: Slater holds
because never-promote has risk 0 < alpha, and Kuhn's theorem applies to the perfect-recall null. Hence there is a
single **least-favourable behavioural null** `y*`, and pricing with one null mode `{alt, y*}` at `lam*` has zero
duality gap (PROVED, standard minimax/LP duality; least-favourable priors in robust testing: Huber & Strassen 1973,
unverified). The C2/C3/C6 runs show `y*` is genuinely non-IID there (7/12/21 active rows). Its residual classes, and
the HMM belief, again force the tree (§1.3).

### 4.2 The proposed structural simplification and its status

Claim tested: "under d=1 and a persistent HMM, the pre-promotion problem reduces to a stopping problem on
(belief, budget, t)".
- **Persistent HMM with transition in (0,1/2): TRUE BUT VACUOUS.** In every measured HMM cell the
  `(t, budget, alternative belief)` key already separates every public history (alt-only keys = `|I|`: 65, 236, 848),
  so "belief-measurable" equals "unrestricted" and nothing is gained.
- **Degenerate/transient HMM: FALSIFIED.** In the repo's exact alias counterexample (`T=5, B=2, d=1`, deterministic
  transition to an absorbing state; `docs/switching_alt_belief_risk_alias_counterexample_v1.md`), belief-measurable
  policies lose `58/125` at `alpha = 1/10`.
- **Static alternative: TRUE AND COMPRESSIVE wherever the IID mixture is robust-safe** (Theorem B1-S(d), certified in
  49 cells). Locked-calendar test (`b4_static_calendar.py`, `results/b4_static_calendar_v1.json`): a fixed calendar of
  `q in {2,3,4}` queries, one promotion decision, three emission pairs and three alphas. In all 27 cases the
  count-symmetric (= belief-measurable) optimum equals the unrestricted causal LP optimum (exact gap 0). There is a
  proof for this locked case (PROVED). The IID-relaxed optimum is the Neyman–Pearson rule
  `1[u(tape) 2^q > lam]`, with `u(tape) = P1(tape) - P0(tape)` increasing in the count. It is therefore a mixture of
  monotone threshold events, whose causal risk equals their IID risk (P4-3), so it is causal-feasible and optimal.
  PRIOR ART: Neyman–Pearson plus monotone likelihood ratio (Karlin–Rubin, unverified) plus P4-3.

My initial counterexample hypothesis, that order-sensitivity of the causal risk would make count-symmetric policies
suboptimal under exchangeability, was **refuted** by this test. The LP duals at `q = 4` are not IID-only, but the
primal optimum is still count-symmetric.

### 4.3 Other decompositions examined

- **Dualising the query budget** (pathwise → expected) is a valid relaxation, so the `L` stays valid. It removes
  `rem` from the key but not the history dependence of the HMM belief, so there is no compression for HMM.
- **Promotion as optimal stopping with a robust constraint** is exactly the pre-promotion problem: a robust
  constrained stopping problem whose robust part is the Krale recursion. No tractable special case beyond the
  exchangeable one was found that a generic CPOMDP / POSG solver could not also exploit.

### 4.4 B4 decision

**NO-GO — prior art / correctness.** The least-favourable-null dual is standard LP duality. The belief-stopping
reduction is either false (alias counterexample), vacuous (HMM), or reduces to B1-S plus Neyman–Pearson/P4-3
(static).

## 5. Summary, strongest surviving statement, remaining lead

| Family | Decision | One-line reason |
|---|---|---|
| B1 implicit column generation | **NO-GO computational** (HMM); **GO candidate, computational, no novelty** (static/exchangeable alternative) | The exact λ-uniform pricing state equals the public tree for every HMM cell. Restricted pricing breaks the unrestricted bound (8/10 cells). Count statistics give a tree-free exact certificate when the alternative is static |
| B2 grid refinement certificate | **NO-GO as contribution (prior art)**; retained as baseline | Sound `L`, exact `U`, and `U` hits `V*` with ≤ 22-state controllers. `L` stalls at `V*_IID` under reversals, and the grid is not smaller than the tree at T ≤ 12 |
| B3 certified distillation | **NO-GO prior art / computational** | The coupling certificate needs the teacher-joint product (⊇ tree) and is looser than direct student verification (Candidate J) |
| B4 dual / first-promotion decompositions | **NO-GO prior art / correctness** | The least-favourable-null dual is LP duality. Belief-stopping is false (alias), vacuous (HMM) or Neyman–Pearson + P4-3 (static) |

**Strongest surviving statement (Theorem B1-S, PROVED; numerically certified in 49 cells):**
> Under a static (exchangeable) two-type alternative with fixed delay `d`, one query per event and hard budget `B`,
> exact IID-row pricing for the first-promotion decomposed problem runs on keys `(t, last d-1 query bits, n1, n0)`,
> at most `T 2^(d-1) (B+1)(B+2)/2` of them. Column generation with this pricing returns `L = V*_IID <= V*` against the
> unrestricted optimum without building the learner tree. The returned root mixture's exact full-history causal-null
> risk is computed on a product of size `O(#keys 2^min(B,d-1))`. Whenever that risk is `<= alpha`, `L = U = V*` is
> certified. In all 49 static cells tested, including T=24 (2.7×10^7 public information sets, 0.9 s), it was.

This is not a new principle (sufficient statistics + Dantzig–Wolfe + P4-3 / Krale verification). Its scope excludes
the registered HMM alternatives, where it gives no compression.

**Most promising remaining lead (UNRESOLVED): single-controller sufficiency plus a premium-aware lower bound.** In
all six exact cells, `V*` equals the root repair `a C(p) + (1-a) C_never` of **one** deterministic controller `p`
with 10–22 memory states (B2 §2.2; on reversal cells `a = alpha` with `R_rob(p) = 1`). If this holds, then
`V* = C_never - alpha max_p (C_never - C(p)) / R_rob(p)` over compact controllers. `U` can be found by tree-free
search with exact product verification. What is missing is a matching tree-free **lower bound** on reversal cells. It
would need either (i) a proof that the optimal mixture has a two-column `{p, never}` support under stated primitive
conditions, or (ii) a premium-aware relaxation tighter than IID whose pricing state stays polynomial. Neither exists.
(i) is false in general: root mixtures can hedge, `sup_nu sum z R_nu < sum z R_rob`. Its scope conditions are
therefore the open question. They are closely tied to WP C (Gamma characterisation) and Conjecture B1-S-Γ.

## 6. Reproduction

    uv run --no-sync python scripts/paper4_continuation/theory_B/b1_run.py            # ~27 s
    uv run --no-sync python scripts/paper4_continuation/theory_B/b1_static_scale.py   # ~9 s
    uv run --no-sync python scripts/paper4_continuation/theory_B/b2_grid_certificate.py  # ~52 s
    uv run --no-sync python scripts/paper4_continuation/theory_B/b3_distill.py        # ~12 s (writes v4)
    uv run --no-sync python scripts/paper4_continuation/theory_B/b4_static_calendar.py   # ~62 s

Each script refuses to overwrite its JSON. Delete the file deliberately to re-run. Outputs record the script SHA-256.
Code base: `affd5077` plus the uncommitted `theory_B` scripts. Hardware: local macOS arm64 CPU. No job exceeded 70 s.
Limitations: small exact instances only. B2 is restricted to `d = 1` and its `L` is float64. B1-S is verified on
synthetic static cells, which are a degenerate shift model. Same-family review only.
