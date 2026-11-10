# Review of Theorem S0 (static alternative, free labels): Reviewer 1, mathematical correctness

**Date:** 2026-11-10. **Target:** Theorem S0, `MULTILABEL_ZERO_PREMIUM.md` §0 (row 1) and §2.1–2.6, with its uses of
Lemma R / R′ / Zc (`CAUSAL_SAFETY_PREMIUM_THEORY.md` §1, F1; `THEOREM_PROOF_AUDIT.md` §2, §6).
`review_independence: same-family` · `acceptance_status: provisional`.
**Method:** `.agents/skills/proof-checker/SKILL.md`: obligation ledger, issue taxonomy, two-axis severity and a
counterexample red team. I rebuilt every step from the primitive model in §0 of the theory document. I re-derived the
recursions by hand, then implemented them independently in exact rationals and compared them with the exact DPs.
**Scripts:** `scripts/paper4_continuation/theory_v2/rev1_s0_redteam.py`.
**Outputs** (refuse-overwrite): `docs/paper4_continuation/theory_v2/results/rev1_s0_redteam_w{0..3}.json` (fixed
adversarial list) and `rev1_s0_redteam_rand_w{0..3}.json` (seeded random, nontrivial hulls).

## 0. Verdict

**PROVED with corrections.** None of the corrections changes the statement's scope.
- I reconstructed the proof and found no invalid step.
- There are two gaps, both MINOR and both fillable:
  - Lemma G silently assumes that the *post-promotion* query schedule is also the greedy calendar.
  - The CAL proof has to keep querying greedily *after* promotion, so that it can emulate the incumbent plan's later
    queries.
- One cosmetic overload: `y` is both a label and the null coordinate.
- Remark 3 (the "any c" corollary) is UNCLEAR as worded. It holds only if the *whole* schedule, including the
  post-promotion part, is fixed in advance. It is not part of S0.
- No α restriction is needed, and none is hidden.
- The red team found no counterexample: 0 positive certified Γ, 0 exact-arithmetic failures of any proof step.

## 1. Obligation ledger

**Model facts used.** These are confirmed against the solver and against `THEOREM_PROOF_AUDIT.md` §0:
- θ = S_1 is fixed, and `P(S_1 = 1) = propagate(prior,1) = prior`.
- `0 < e0 < 1/2 < e1 < 1` is enforced by `RegimeModel`.
- Promotion is the first `A_t = 1`, with `A_0 = 0`.
- The post-promotion continuation is the exact belief DP, which can roll back, re-promote and use the remaining
  budget.
- `GameConfig` requires `B ≤ T`. "Any B" in S0 therefore means `B ≤ T`. A plan can make at most T queries, so
  `B > T` is equivalent to `B = T`.

| ID | Obligation | Status | Severity / category |
|---|---|---|---|
| O1 | CAL-1: π's j-th query satisfies `τ_j ≥ j`, so the greedy calendar sees label j no later | ACCEPTED | — |
| O2 | CAL-2: π^g can replay π on a virtual clock, and its promotion time is the same function of z | ACCEPTED | — |
| O3 | CAL-3: `(θ, z)` has the same law under both schedules (A worlds and IID null) | ACCEPTED | — |
| O4 | CAL-4/5: `C(π^g) ≤ C(π)`, including the post-promotion phase (rollback, re-promotion, budget) | ACCEPTED **with correction C1** | MINOR (LOGICAL_GAP, fillable) |
| O5 | Three-world linearity: the value is a min of functions linear in `(a0, n, a1)`, so normalising by `a1 > 0` is legitimate | ACCEPTED | — |
| O6 | Lemma G (clip recursion for `G_t = (U_t − W_t)/a1`) | ACCEPTED **with correction C2** | MINOR (HIDDEN_ASSUMPTION, fillable) |
| O7 | Lemma D (recursion for `D_t = (Φ_t − Ψ_t)/a1`) | ACCEPTED | — |
| O8 | Induction claims 1–4 (base and step) | ACCEPTED | — |
| O9 | The threshold rule's promotion event is an up-set in `(Y_1..Y_n)`, so the plan is z- and tape-monotone (pending labels, ties) | ACCEPTED | — |
| O10 | U2 ⇒ Γ = 0 through Lemma R′, for every α ∈ [0,1] | ACCEPTED | — |
| O11 | Hypothesis bookkeeping (Remark 4) | ACCEPTED, with one note | MINOR |
| O12 | Remark 3 (open-loop corollary, any c) | UNCLEAR, not part of S0 | MINOR (SCOPE) |
| — | Notation: `y` is both a label value and the null coordinate `n/a1` | — | COSMETIC |

## 2. Step-by-step reconstruction

### 2.1 Lemma CAL (items 1 and 2 of the brief)

**O1–O3: ACCEPTED.**
- `τ_j` is chosen from information that contains only released labels, i.e. a subset of `z_{<j}`. The times are
  distinct and increasing, so `τ_j ≥ j`.
- Given θ, `Y_{τ_j}` is a fresh `Ber(e_θ)` draw independent of `z_{<j}`.
- Under the IID null every time carries an independent Ber(1/2), whatever the schedule.
- Hence `(θ, z)` has the same law for π and for the greedy schedule, and `R(π^g) = R(π)`.
- **"Does an early query change what the null sees?"** The Lagrangian contains only the IID null, and its label law
  does not depend on query times. The causal null enters only through Lemma R′. R′ needs only:
  - Lagrangian optimality over the full pure-plan class `P` (CAL supplies this);
  - z- or tape-monotonicity of the optimal plan.

  Adapting the causal null to the earlier schedule therefore has no effect on the argument.

**O4: ACCEPTED with correction C1.** The issue is the post-promotion phase and the hard budget.
- At promotion π^g has spent `min(B, t*)` queries, while π has spent `N_π ≤ min(B, t*)`. So π^g has **fewer remaining**
  queries, and π's continuation may want to query after promotion, for example to decide on a rollback.
- The proof's step 1 handles this, but only implicitly. It applies `τ_j ≥ j` to *all* of π's queries, both pre- and
  post-promotion. That requires the emulating π^g to keep querying greedily after promotion, at `t*+1, …, min(B,T)`.
- With that convention:
  - π^g's labels `N_π+1 … min(B,t*)`, which were already queried, stand in for π's first post-promotion queries;
  - each is released at `j + d ≤ τ_j + d`;
  - given θ each has the same `Ber(e_θ)` law, independent of the past.

  The emulation therefore reproduces π's continuation, including rollback and re-promotion, with the same joint law of
  `(θ, actions)`. The decomposed game's optimal continuation is no worse.
- **Fix:** in step 5, state that π^g's emulating continuation keeps the greedy calendar, and that the substitution
  respects the budget: the totals are `min(B,T) ≥ N_π^{total}`.
- **Consequence for the statement.** "Queries at 1..min(B,T)" should be read as the *pre-promotion* schedule plus
  "greedy-calendar continuation is optimal". The optimal continuation need not query, and with `c = 0` querying is
  free.
- **T < B** (outside `GameConfig`) and the T-end: the last labels are never released. That is harmless.
- **Is the budget "needed later"?** In the static model a label's information does not depend on when it was queried.
  An early label dominates a later one in information (Blackwell) and costs the same (0), so spending the budget up
  front never loses.
- **Exact check:** `J_general(λ) = J_greedy(λ)` held in every check of the full-class exact DP against the
  calendar-class DP. The counts are in §3.

### 2.2 Normalisation (O5): ACCEPTED

The coordinates are well defined:
- given θ (resp. under N), future labels are independent of the past;
- every fixed continuation strategy therefore has cost linear in `(a0, n, a1)`;
- the value is a min of such functions;
- `a1 = π e1^s(1−e1)^{m−s} > 0` because `π ∈ (0,1)` and `e1 ∈ (0,1)`.

A flip 0→1 multiplies x by `r0/r1 < 1` (this needs `e0 < e1`) and y by `1/r1 < 1` (this needs `e1 > 1/2`). Both
conditions are built into the model class.

### 2.3 Lemma G (O6): ACCEPTED with correction C2

I re-derived the recursion:
- `V^0 = min(U, W)` and `V^1 = min(U − k, W + k)`;
- `V^1 − V^0 = clip(U − W, 0, 2k) − k` in all three ranges, mass-weighted with `kA_y`;
- the `+kA` from `U_t` cancels against `−Σ_y kA_y`;
- normalising branch y by `a1 L1_y` gives `κ(xℓ_y) = 2k(1 + xℓ_y)`.

The terminal case `G_T = x(1−2e0+k) + (1−2e1+k)` is correct.

**Hidden assumption (C2).** The identity sums over *one* branch structure at t+1. It is the same for `U_t` and `W_t`,
and the same inside `V^0_{t+1}` and `V^1_{t+1}`. That holds only if the alternative-only continuation also queries on
the greedy calendar. In the decomposed game the continuation's query choice is free, and `post()` in `wpB_static`
allows `q ∈ {0,1}`. So two facts are needed:
- the alternative-only optimal value, from any post-promotion state, equals its greedy-calendar value;
- the greedy choice is simultaneously optimal for both actions.

Both follow from the CAL emulation applied to the continuation sub-problem (static, `c = 0`). The proof does not say
this. **Fix:** add one sentence: "By the argument of CAL applied from any state, the greedy calendar is optimal for the
alternative-only problem as well, so U, W and V^a all branch identically."

**Exact check.** My recursion uses the greedy post-calendar. `wpB_static`'s Dtab optimises the post-promotion queries
freely. The two agree **exactly, with difference 0 in rationals**, at every reachable state in every λ-check (§3). So
the gap is not a falsehood.

### 2.4 Lemma D (O7): ACCEPTED

The derivation, using the same notation:
- `Φ_t − Ψ_t = n + U_t − q − Σ_y[n_y + U_{t+1,y} − (Φ−Ψ)^+_{t+1,y}]`;
- `Σ_y n_y = n`, because `Σ L^N_y = 1`; this is the null martingale;
- `W_t = q + Σ[U_{t+1} − (U−W)^+_{t+1}]`.

Together these give `D_t = G_t + Σ_y L1_y[D^+_{t+1} − G^+_{t+1}](xℓ_y, yℓ^N_y)`. The terminal case is
`D_T = y + G_T`.

The stop branch uses the alternative-only `U_t` with old action 0. That is right, because before promotion the action
is always 0.

### 2.5 Induction (O8): ACCEPTED

I checked every case.

| Claim | How it is checked |
|---|---|
| 1 (G monotone and continuous) | `clip(·, 0, κ)` is nondecreasing in its argument and in `κ ≥ 0`. The linear slope is `1 − 2e0 > 0`, and `≥ 0` would suffice |
| 4 (D ≥ G) | `D_{t+1} ≥ G_{t+1}` gives `D^+ ≥ G^+` |
| F-identity | `clip(G,0,κ) − G^+ = −(G−κ)^+` uses `κ ≥ 0`. `min(D^+, D−G+κ)`: in the case `G ≤ κ` it uses claim 4 (`D − G ≥ 0`). In the case `G > κ` it uses `D ≥ G > κ ≥ 0` |
| 2 (D monotone) | In x, through IH2 and IH3 and `κ′ = 2k ≥ 0`. In y, through IH2, since G and κ do not depend on y. The arguments `(xℓ_y, yℓ^N_y)` are increasing in `(x, y)` |
| 3 (D − G monotone in x) | The three cases are complete. The crossing case needs continuity of `G_{t+1}` (true: it is piecewise linear) and `D(x0) ≥ G(x0) = 0` |

**Where k, d, T and rollback enter.**
- `k` enters only through `κ`, and the base slope `+k`.
- `d`, `B` and `T` enter only through which transitions carry a release (`ρ_{t+1}`). A step with no release has a
  single branch with ℓ = 1, which the induction handles in the same way.
- Rollback and re-promotion enter only through the `clip` (the `V^1/V^0` table).
- T-end effects are only in the base case.

None of these needs a sign condition beyond `k ≥ 0`.

### 2.6 Monotone event (O9, item 3 of the brief): ACCEPTED

- On the greedy calendar, `m_t = clamp(t−d, 0, min(B,T))` is deterministic.
- `x_t` and `y_t` are nonincreasing in `s_t`, strictly when λ > 0. So by claim 2, `{s : D_t ≤ 0}` and `{s : D_t < 0}`
  are up-sets.
- The promotion event is `∪_t {s_t ∈ Stop_t}`. Each `s_t` is a nondecreasing function of `(Y_1..Y_{m_t})`.

**Pending labels.** Promotion before every label is released depends only on the released prefix. The unreleased
coordinates are dummies, and the event is still an up-set in the full vector.

**Ties.** Both deterministic rules, `≤ 0` and `< 0`, give up-sets. Randomising at a tie is a mixture of the two pure
plans, and Lemma Zc/R′ covers mixtures.

On the greedy calendar `z_j = Y_j`, so the plan is z-monotone and tape-monotone at once. R′ needs only one of the two.

### 2.7 Use of Lemma R′ (O10, item 4 of the brief): ACCEPTED

The assumption-free parts of R′ (`THEOREM_PROOF_AUDIT.md` §2) are:
- the Kuhn/LP-duality reduction, which holds for every α ∈ [0,1];
- the coordinate coupling.

S0 supplies "for every λ some optimal pure plan lies in `M_z ∪ M_tape`", which is exactly R′'s hypothesis.
**No condition `α ≤ 1/2` is needed.** The red team covered 1,204 certificates with α > 1/2, including α = 99/100, and
found no positive premium in any of them.

There are no other unstated conditions beyond two points:
- (i) `prior ∈ (0,1)`; at 0 or 1 the normalisation by `a1` fails, and the theorem excludes those values;
- (ii) the `B ≤ T` convention of the code.

### 2.8 Remark 3 (O12): UNCLEAR, outside S0

"Steps 2.2–2.6 use only a label-independent release calendar, hence any c" is right only if the *post-promotion* query
schedule is also fixed in advance. That is the condition C2 needs.
- If only the pre-promotion schedule is fixed and the continuation chooses its queries optimally with `c > 0`, then
  `U_t` and `W_t` can branch differently, and Lemma G's identity does not apply.
- **Fix:** define the restricted class as "the entire query schedule is open-loop".

I did not test this corollary.

## 3. Red team (exact / certified)

**Design.** All runs use `rev1_s0_redteam.py`, with up to 4 processes. Each cell (`t01=t10=0`, `c=0`) goes through
these checks:
- **(H)** The exact lower hull of `{(R_IID, C)}` over the **full** pure-plan class, computed by parametric search with
  `wpB_lib.solve` in exact rationals, when `T ≤ 7`. This solver has no calendar restriction.
- **(CAL)** At every exact breakpoint λ and every edge midpoint: `J_general == J_greedy`. Here `J_greedy` is
  `wpB_static.static_solve(greedy=True)`.
- **(MON)** The greedy DP plan is z-monotone under both tie rules.
- **(REC)** My own implementation of the G/D recursions:
  - equals the DP advantage Dtab exactly at every reachable state;
  - gives up-set stop sets;
  - gives a threshold event that is monotone, with exact IID risk equal to the DP plan's;
  - satisfies claims 1–4 on a 10×7 rational (x, y) grid at every t.
- **(GAM)** Certified Γ from `gamma_cell`, evaluated at:
  - α = every interior hull-vertex risk (hull breakpoints in α);
  - midpoints between those risks;
  - α ∈ {1/20, 1/2, 3/4, 99/100}.

  It uses `force_fcg=True` for `T ≤ 6`, so `V*_causal` is certified by FCG and not by the IID optimum's safety.

**Adversarial classes in run 1** (312 distinct cells):
- **Large delay:** `d ∈ {T−1, T, T+2}`, 63 cells.
- **B close to T:** 42 cells.
- **Large switch cost:** `k ∈ {1, 3, 10}`, 36 cells.
- **Priors near 0 and 1:** 10⁻³ and 0.999, 56 cells.
- **Emissions** near 1/2 (`0.49/0.51`, `0.499/0.501`), near 0/1 (`0.001/0.999`), and asymmetric mixes.
- **Edge shapes:** T = 1, B = 1, `d > T`; 15 cells.
- **Larger cells:** T = 8–9, B ≤ 6, certified Γ only; 20 cells.
- **Seeded random:** 80 cells.

Run 2 adds 160 seeded random cells chosen to have nontrivial hulls.

| Run | Cells | Exact λ-checks (of which at exact breakpoints) | CAL `J_gen = J_greedy` | z-monotone (both ties) | Recursion = DP (exact 0) | Grid-claim violations | Γ certificates (FCG-certified / α > 1/2 / α at hull vertex) | Γ_lo > 0 | Γ_hi ≤ 1e-9 (exact) |
|---|---|---|---|---|---|---|---|---|---|
| 1 adversarial | 312 (286 with full-class hull; 62 with ≥ 3 vertices) | 934 (272) | 830/830 | 934/934 | 934/934 | 0 | 1,561 (1,122 / 675 / 201) | **0** | 1,542/1,561 |
| 2 random (seed 777) | 160 (all full-class; 130 with ≥ 3 vertices) | 1,338 (589) | 1,338/1,338 | 1,338/1,338 | 1,338/1,338 | 0 | 1,301 (832 / 529 / 443) | **0** | 1,290/1,301 |
| **Total** | **472** | **2,272 (861)** | **2,168/2,168** | **2,272/2,272** | **2,272/2,272** | **0** | **2,862 (1,954 / 1,204 / 644)** | **0** | 2,832/2,862 |

**The 30 certificates with Γ_hi > 1e-9** (19 in run 1, 11 in run 2).
- Every one has `Γ_lo = −Γ_hi`, with `Γ_hi ≤ 1.05e-8`.
- They come from four cells, all with emissions `(1/1000, 999/1000)`:
  - (8,6,1), prior 1/3, k = 1/20;
  - (9,6,1), prior 1/3, k = 1/20;
  - (7,7,1), prior 1/1000, k = 1;
  - (7,6,1), prior 1/4, k = 1/2 (run 2; `Γ_hi = 1.48e-9`).
- The width is the resolution of `gamma_cell`'s rationalised dual (`limit_denominator(1e9)`). There the IID optimum was
  already causal-safe, so `[L_c, U_c] = [L_IID, U_IID]`.
- Since Γ ≥ 0 by definition, Γ ∈ [0, 1.05e-8] in these cells. This is resolution-limited, not a positive premium.
- For the (7,7,1) and (7,6,1) cells, the exact checks (CAL, monotonicity, recursion) all passed.

**Attempts aimed at each step, and their outcomes:**
- **CAL / early queries**, using large d, B = T, and T-end cells where post-promotion queries would matter. The
  full-class exact optimum never beat the calendar class. The difference was 0 in rationals.
- **Lemma G's post-calendar assumption.** The DP with free post-promotion queries equalled the greedy-post recursion
  exactly.
- **Induction near degeneracy**, using e near 1/2 where slopes are tiny, k = 10 where κ dominates, and priors 10⁻³ and
  0.999 where x or y is extreme. There were 0 violations.
- **Ties at hull breakpoints.** At 861 exact breakpoint λ both tie rules gave monotone plans.
- **Γ at breakpoint α**, i.e. α equal to a vertex risk, the configuration that produced CE-B1 in the symmetric family.
  No positive certificate was found.

**Scope of the evidence.** These are exact checks on finite instances with `T ≤ 9`. They support the proof but cannot
replace it. Many adversarial cells, such as large-d and extreme-prior ones, have trivial 2-vertex hulls. The
nontrivial-hull evidence is 192 cells: 62 from run 1 and 130 from run 2.

## 4. How much of S0 is known

- **CAL** is standard. It combines exchangeability (conditionally i.i.d. labels given a static θ, so the query time is
  irrelevant beyond the count) with value-of-information: free information that arrives earlier weakly helps a single
  Bayesian decision-maker (Blackwell). The emulation argument is routine.
- **The sufficient statistic.** `(m_t, s_t)` is the binomial sufficient statistic. With a deterministic calendar the
  state is one-dimensional in s, which is routine.
- **Threshold structure.**
  - For a *two*-hypothesis Bayesian stopping problem with MLR observations, threshold/SPRT-type stopping regions are
    classical: Wald–Wolfowitz, Arrow–Blackwell–Girshick `[unverified: from memory, not re-read]`.
  - S0's problem is different: a three-world mixture (A0, N, A1), N carrying only the Lagrangian risk, a
    post-stopping continuation with switch costs and rollback, and a per-step continue cost `(e0, 0, e1)` that is not
    monotone in the world order. Krishnamurthy Thm 6.3.4's condition (C) fails, as the authors note in §6(f); I did
    not re-check the book.
  - The genuinely new content is the G/D pair induction, with "D monotone and D − G monotone in x" as the hypothesis,
    plus the clip identity for rollback. It is short and elementary but not a direct citation.
- **Γ = 0 from monotonicity** is Lemma R′, which is routine (LP duality plus a monotone coupling).

**Overall.** S0 is roughly 80% routine reductions (exchangeability, sufficient statistic, Blackwell, R′). Its one
model-specific lemma is an elementary monotone-comparative-statics induction. It should be presented as a clean
restricted proposition, not as a headline theorem.

## 5. Required corrections (for the author; I have not edited the target files)

- **C1 (CAL step 5).** State that π^g keeps querying on the greedy calendar after promotion while it emulates π.
  Note the budget substitution: π^g's already-queried extra labels replace π's later queries and are released no
  later. Clarify that "queries at 1..min(B,T)" refers to the pre-promotion schedule.
- **C2 (Lemma G).** Add the sentence: "by CAL applied from any state, the greedy calendar is optimal for the
  alternative-only continuation, so U, W and V^a branch identically."
- **C3 (Remark 3).** Restrict it to classes whose entire schedule, including the post-promotion part, is open-loop.
- **C4 (notation).** Rename the null coordinate, e.g. to `η = n/a1`, to avoid the clash with the label y. State
  `B ≤ T` (the `GameConfig` convention).

## 6. Reproduce

```
R=docs/paper4_continuation/theory_v2/results; S=scripts/paper4_continuation/theory_v2/rev1_s0_redteam.py
for w in 0 1 2 3; do uv run --no-sync python $S $R/rev1_s0_redteam_w$w.json $w 4 & done; wait
for w in 0 1 2 3; do uv run --no-sync python $S $R/rev1_s0_redteam_rand_w$w.json $w 4 777 160 & done; wait
```

**Code version.** Branch `research/paper4-causal-premium-theory-2026-11-10`, HEAD `6051f2b6`, plus the uncommitted
`rev1_s0_redteam.py`. It depends on `gamma_lib.py`, `wpB_lib.py` and `wpB_static.py` as they stand in the worktree.
Run 1 took about 3.5 minutes per worker and run 2 about 2.7 minutes, with 4 processes each.
