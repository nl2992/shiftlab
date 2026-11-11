# WP F: Prior-art audit of the causal-safety premium results (Reviewer 2, novelty)

**Date:** 2026-11-10. **Branch:** `research/paper4-causal-premium-theory-2026-11-10` (uncommitted).
**Reviewer:** fresh-context Opus 5.5 subagent, acting as the substitute for the unavailable ARIS/Codex reviewer slot (BL-1).
`review_independence: same-family` · `acceptance_status: provisional`.
**Protocol:** ARIS `novelty-check` (`.agents/skills/novelty-check/SKILL.md`), Phases A–D, with its NOVELTY VERDICT LIMITS applied.
I am both the searcher and the substitute reviewer, so the Phase C "fresh agent" check is the same-family check recorded here.
Search followed the HKUSTDial `deep-research` verification discipline: claims were read in primary text where possible, and each
source has a read status. The ARIS trace directory (`.aris/traces/novelty-check/`) was **not** written, because the brief allowed
only this file.
**Stance:** adversarial. For every result I try to reduce it to the closest published statement, then state exactly what is left.
**Inputs:**
- `PRIOR_ART_SOURCES.md` (WP F retrieval);
- `../NOVELTY_AUDIT_SURVIVORS.md`, `../PRIOR_ART_MATRIX.md`, `../LITERATURE_NOTES.md`;
- the result statements in `THEOREM_PROOF_AUDIT.md`, `MULTILABEL_ZERO_PREMIUM.md`, `REVIEW_S0.md`,
  `STOCHASTIC_POSITIVE_PREMIUM.md` and `STRUCTURAL_CHARACTERIZATION.md`;
- `../COUNTEREXAMPLE_REGISTRY.md` (CE-12, CE-14).

**Untrusted-file handling.** New PDFs were saved in the new directory
`/private/tmp/claude-501/-Users-nigelli-Desktop-ICML-Shift-lab--claude-worktrees-shiftlab-methods-strategy-dba13e/06bf436b-d27c-42d6-9116-89f769a07352/scratchpad/rev2_sources/`.
Only `pdftotext` was used on them, and nothing was executed. One download (`math/9512218`, a wrong guess for Liggett–Schonmann–Stacey)
turned out to be an unrelated PDE paper. It was deleted unread beyond its title. A JAIR download returned non-PDF text and was deleted.

**Classifications used:**
- PROVED EQUIVALENT: the result is contained in, or is an immediate composition of, published statements.
- PARTIAL OVERLAP: a known mechanism applied in a new setting.
- PROVED DISTINCT: a different statement, with no reduction found.
- UNRESOLVED: the evidence is insufficient to decide.

Separately, each result is marked **new theorem** vs **new application**.

---

## 0. Verdict in one paragraph

No result here is a published theorem verbatim. Every name-able step does reduce to a known mechanism, though. The
two reductions that matter most are new in this audit:

- **(i) B = 1 is not adaptive.** At B = 1 the "adaptive causal null" acts once per public query node. So every B = 1
  result (Z1/W/W\*, N1, S1, C3″, SP1) is a **single-observation composite-null Neyman–Pearson problem**,
  H0: Y ~ Ber(p), p ≤ 1/2, against a weighted alternative. These problems are mixed by an LP over query times.
  Condition W is the weighted monotone-likelihood-ratio (Karlin–Rubin) condition under which the boundary point
  p = 1/2 is least favourable.
- **(ii) The zero side is classical.** "Monotone events are not inflated by any adapted p_t ≤ 1/2" is sequential
  stochastic domination. Doerr's Lemma 1.8.7 states it for sums, and the uniform-coupling or Strassen–Markov form
  (Roch Thm 4.17) gives it for arbitrary up-sets.

Two items remain unpublished:
- the *object* Γ = V\*_causal − V\*_IID, specialised to a budgeted, delayed-label promotion decision;
- a handful of exact, elementary evaluations of it: N1, SP1, S0, and the certified counterexamples CE-12 and CE-14.

None of these is a new theorem at main-track level.
**Novelty-check recommendation: PROCEED WITH CAUTION.** No named paper contains Γ or its formulas, so ABANDON is
not justified. The delta is thin for a nameable reason: the multi-label (B ≥ 2) regime, which is the only place
adaptivity matters, has no general theorem.

---

## 1. Phase A: core claims under test

| ID | Claim (as stated in the theory_v2 files) | Proof status (from audits) |
|---|---|---|
| Γ | Definition. Γ(α) = V\*_causal(α) − V\*_IID(α). Both are min alternative-cost over learner mixtures, subject to promotion risk ≤ α. The causal side takes sup over adapted nulls p_t ∈ [0, 1/2]; the IID side fixes p_t ≡ 1/2 | definition |
| R / R′ | If, for the relevant λ, a Lagrangian-optimal plan lies in the monotone (tape or z) class, then Γ = 0 | PROVED (WP A), "routine" |
| Zc | z-monotone (query-order) promotion events have causal risk = IID risk. The tape and z classes are incomparable | PROVED (WP A) |
| P | Promoting only where q(h) > 1/2 is WLOG, under every null | PROVED (WP A) |
| Z1 / W / W\* | B = 1: TP2 + MLR + (M), or W, or W\*, implies Γ = 0 | PROVED (WP A) |
| N1 | B = 1, any HMM, α ≤ 1/2: exact Γ = α·κ⁺. FALSE for α > 1/2 | PROVED + 1,905/1,905 cells |
| S1 | B = 1, static alternative ⇒ Γ = 0 | PROVED |
| C3″ | Deterministic alternation, B = 1: exact Γ; odd T ⇒ Γ = 0 | PROVED via N1 |
| S0 | Static alternative, c = 0, any T, B, d, k, α ⇒ Γ = 0 (threshold rule in the binomial count) | PROVED with minor corrections (REVIEW_S0) |
| SP1 (+ A–E) | Symmetric stationary anti-persistent chain, B = 1: closed-form Γ; even d ⇒ Γ = 0; open region with Γ > 0; decay like r^d | PROVED (unreviewed by an independent reviewer) |
| CE-12 / CE-14 | Symmetric stationary *persistent* chains have Γ > 0 at B = 4 (α = 25/32; α = 5/16 and 1/2). This falsifies "TP2/persistence ⇒ Γ = 0" | certified numerics |
| WP-D | Four-mechanism taxonomy M0–M3. "Persistence ⇒ zero premium" is backwards beyond small B | PROVED components + verified taxonomy, not a theorem |

---

## 2. Per-result audit

### 2.1 The problem definition Γ = V\*_causal − V\*_IID

- **Closest sources.**
  - Fauß–Zoubir–Poor (2020), §2.3 eq. (2.6) and Thm 6. Opened and verified by me. (2.6) is a product
    ("rectangular") uncertainty set over per-step conditional laws. Thm 6 says the least-favourable distributions
    are products of per-state maximisers and "adapt to the policy of the test as well as to the history".
  - The robust-constrained-MDP "RC" objective: nominal reward, with the constraint robust over an uncertainty set
    (Mankowitz et al., arXiv:2010.10644; Russel et al., arXiv:2010.04870). Search snippet only.
  - Robust MDP rectangularity (Iyengar 2005; Nilim–El Ghaoui 2005). META only, via WP F.
- **Attempted reduction.** V\*_causal is a finite-horizon constrained POMDP. Its objective is evaluated under one
  law (the alternative HMM). Its single constraint is evaluated as a sup over a history-rectangular family of null
  laws. That is exactly the RC robust-constrained problem, or equivalently a minimax sequential test in which only
  the null is composite and rectangular (Fauß et al. with K = 1 error constraint and the run-length criterion
  replaced by an HMM decision cost). Γ is the gap between that value and the value at one member of the family, the
  top element p ≡ 1/2 in the coordinatewise stochastic order.
- **What remains.**
  - In all the literature I opened, the robust value is computed, and the conservatism of rectangular sets is
    discussed only qualitatively (Ou–Bi via WP F). I found no paper that defines or characterises the gap between a
    rectangular-robust constraint value and the constraint value at the family's stochastically maximal point.
  - **Closest negative-type precedent.** Modak–Bakshi–Dey–Prabhakaran (arXiv:2511.10181, Sequential Adversarial
    Hypothesis Testing; read via fetch summaries) has an adversary that picks each observation's law from a convex
    set using past observations. Its converse is attained by an i.i.d. adversary. So at the level of error
    *exponents*, adversary adaptivity buys nothing. Γ > 0 is therefore a finite-horizon / decision-cost phenomenon.
    That is consistent with, but not contained in, that paper.
- **Classification:** PARTIAL OVERLAP. The object is an instance of a known class (RC-robust constrained POMDP /
  rectangular minimax test). The specific gap-to-nominal quantity is not found. **New application (framing)**, not a
  new theorem.

### 2.2 Lemma R / R′ (monotone Lagrangian minimisers ⇒ Γ = 0)

- **Closest sources.**
  - Steps R1–R4 (mixtures over pure plans, a single-constraint LP, Lagrangian duality): Walraven–Spaan, JAIR 62
    (2018), §2–3, LP (8)–(10) and Thm 3. Theorem-level content was OPENED by WP F. I verified only the abstract,
    which confirms "an LP in which each column corresponds to a POMDP policy". Yost–Washburn 2000: META. Altman
    1999: not found.
  - Step R5 (an adapted p_t ≤ 1/2 cannot raise the probability of an up-set): Doerr, arXiv:1801.06733v6,
    **Lemma 1.8.7(a)**. Opened by me. It says: if `Pr[X_i = 1 | X_1..X_{i−1}] ≤ Pr[X_i* = 1]` with the X_i\*
    independent, then Σ X_i is stochastically dominated by Σ X_i\*. Its general form is **Lemma 1.8.8**
    ("unconditional sequential domination"). The uniform-coupling device is in §1.8.4, and the
    domination ⇔ monotone coupling equivalence is **Thm 1.8.10**. For arbitrary up-sets (not just sums):
    Strassen for Markov kernels, Roch notes **Thm 4.17**. OPENED by WP F; it is lecture notes, not peer reviewed.
    Kamae–Krengel–O'Brien 1977: META only.
- **Attempted reduction (succeeds).**
  1. Kuhn plus the LP gives V\* = max_λ[min_π (C + λR) − λα], in both problems.
  2. Put the full history (learner actions, pending labels) in the state of the Strassen–Markov coupling. The
     kernel's next-label probability is p(x) ≤ 1/2 = the IID kernel's. Roch Thm 4.17 then couples the null tape
     below the IID tape pathwise. Equivalently, use the explicit coupling `Y_t = 1{U_t ≤ p_t} ≤ 1{U_t ≤ 1/2}`
     (Doerr §1.8.4).
  3. A nondecreasing g_π then gives P_ν(g_π = 1) ≤ P_{1/2}(g_π = 1) per pure plan. Mixtures follow linearly.
  4. Hence the IID-optimal mixture is causally feasible.
- **Exact difference.** The hypothesis is placed on Lagrangian minimisers, and the bound is applied per pure plan in
  a mixture. Both are bookkeeping. No published source states the combined sentence "a monotone IID-optimal plan
  makes the robust and nominal constrained values coincide", but every step is a cited statement.
- **Classification:** PROVED EQUIVALENT (composition of LP duality and sequential stochastic domination).
  **New application**, not a new theorem. This agrees with WP A ("routine corollary") and `NOVELTY_AUDIT_SURVIVORS.md`.

### 2.3 Lemma Zc (query-order coupling) and the tape/z incomparability

- **Closest sources.** As in 2.2: Doerr Lemma 1.8.7/1.8.8 and Roch Thm 4.17.
- **Attempted reduction (succeeds).**
  - Index labels by query order, z_j.
  - Under any adapted null, `P(z_j = 1 | F_{τ_j}) = p_{τ_j} ≤ 1/2`, and F contains z_{<j}. By the tower property,
    `P(z_j = 1 | z_{<j}) ≤ 1/2`, which is Doerr's sequential-domination hypothesis.
  - Under IID, z is i.i.d. Ber(1/2) whatever the (adapted) query times. That holds because each fresh time's label
    is an independent Ber(1/2).
  - Strassen (vector form) or the uniform coupling indexed by j then gives the result for every up-set in z.
- **Exact difference.** Only the observation that the learner's adaptive query order preserves the sequential
  hypothesis. The incomparability of the tape and z classes (WP A: 8 plans at (4,3,1)) is a combinatorial remark
  about two index sets.
- **Classification:** PROVED EQUIVALENT. **New application.**

### 2.4 Lemma P (promote only where q(h) > 1/2)

- **Closest source.** No published statement was located. The argument is a one-step interchange: delay a promotion
  whose immediate expected gain is negative. That shrinks the event pathwise and does not raise cost. It is
  folklore in optimal stopping.
- **Classification:** PARTIAL OVERLAP (folklore mechanism, no specific citation). **Not a contribution.** Use it as
  a lemma.

### 2.5 Z1 / W / W\* (B = 1 zero premium)

- **Closest sources.**
  - Krishnamurthy, arXiv:1512.03873v1, **Thm 4.3.1**: the filter or predictor preserves MLR iff the transition
    matrix is TP2 (F2); T(π, y) is MLR-increasing in y iff the observation kernel is TP2 (F1). Theorem headers
    located by me; the statements were quoted by WP F.
  - Thm 5.2.1, 5.3.1 and 6.3.4 give monotone value and threshold policies.
  - For the testing half: the Karlin–Rubin / monotone-likelihood-ratio UMP theorem for one-sided composite nulls
    (Lehmann & Romano, *Testing Statistical Hypotheses*, §3.4). `[unverified: cited from memory, not opened]`.
- **Attempted reduction (new in this audit; succeeds for the testing part).**
  - Fix B = 1 and a query time τ. Before the query nothing is observed (Z1a), and non-queried labels are inert. So
    the causal null's whole influence on any plan through node τ is one choice `p_τ ∈ [0, 1/2]`, taken without
    knowing which plan in the mixture reached the node.
  - The per-node problem is therefore: maximise `Σ_y μ_τ(y)φ(y)` subject to `sup_{p ≤ 1/2} E_p φ ≤ α_τ`, where
    `μ_τ(y) = P_A(Y_τ = y)·G_y(τ)⁺`. This is a **single-observation Neyman–Pearson problem with the composite
    one-sided null {Ber(p) : p ≤ 1/2}** against a (sub-probability) weighted alternative.
  - The boundary point p = 1/2 is least favourable iff the weighted likelihood ratio `μ_τ(y)/Ber(1/2)(y)` is
    nondecreasing in y, i.e. `P_1G_1 ≥ P_0G_0`. **That is condition W.** It is the Karlin–Rubin MLR condition with
    the alternative replaced by the gain-weighted measure.
  - W\* is the same statement after maximising each branch over the promotion time.
  - TP2 + MLR ⇒ G_1 ≥ G_0 is Krishnamurthy Thm 4.3.1(2–3) followed by a linear-cost monotonicity step. Adding (M)
    (P_1 ≥ 1/2) gives W.
- **Exact difference.**
  - μ is a decision-weighted measure, not a likelihood. G_y involves a switching-cost continuation, and delay d.
  - The per-node problems are coupled through a shared LP over τ and through the "both/pre" designs.
  - None of this changes the mechanism.
- **Classification:** PARTIAL OVERLAP. **New application** of Karlin–Rubin + TP2 filtering monotonicity.

### 2.6 N1 (exact Γ, B = 1, any HMM, α ≤ 1/2)

- **Closest sources.**
  - Neyman–Pearson lemma in LP / fractional-knapsack form. Textbook; not re-opened.
  - The per-node composite-null reduction of 2.5.
  - Fauß–Zoubir–Poor Thm 4 (a Lagrange multiplier for constrained sequential tests). OPENED by me at statement
    level.
  - Fauß & Zoubir also have an LP formulation of sequential tests. `[not opened; mentioned from memory as a
    possible neighbour, existence unverified]`.
- **Attempted reduction.**
  - Pure B = 1 plans fall into finitely many design classes per τ: z0, z1, both, pre. Each class has a gain and an
    IID risk 1/2 or 1.
  - IID: the value is "the best gain per unit risk", taken at mass 2α. That is the NP / fractional-knapsack
    solution, and it needs α ≤ 1/2 so that one ray suffices. The falsification for α > 1/2 is exactly the point
    where the knapsack must spill onto a second ray.
  - Causal: at each node, the null's two endpoints give the gauge `a + max(c, (b+c)/2)`. This is the per-node
    composite-null risk from 2.5, linear in p, so maximised at an endpoint.
  - Extreme rays of an ℓ1-sum of per-node gauges then give the formula.
- **Exact difference.** I found no published closed form for the robust-minus-nominal value in a budgeted,
  delayed-label promotion problem (WP F §7 query (ii) negative; my "price of robustness" search found only
  sample-complexity "price" papers, e.g. Shi et al., arXiv:2305.16589, search snippet only). The formula is new as
  a computed object. Every ingredient is textbook: NP/LP, endpoint maximisation of a linear function, and extreme
  points of a gauge ball.
- **Classification:** PARTIAL OVERLAP. **New application, elementary.** A characterisation proposition, not a
  theorem of independent interest.

### 2.7 S1 (static ⇒ Γ = 0, B = 1)

- **Reduction (succeeds).** Static ⇒ `Cov(e_S, Y_τ) = Var(e_S) ≥ 0` ⇒ MLR of the single label. With
  `G_1 ≥ G_0` (Thm 4.3.1, ρ = 1), condition W of 2.5 holds, and Karlin–Rubin gives a monotone NP region.
- **Classification:** PROVED EQUIVALENT in substance. **Corollary.**

### 2.8 C3″ (deterministic alternation)

- **Reduction.** C3″ is SP1-D at r = 1 (2.9), which is N1 evaluated on the alternation chain. It is a separation
  example. The overview of Bertsimas–Sim (META) shows no overlap in object.
- **Classification:** PARTIAL OVERLAP (example within N1). **Not a contribution on its own.**

### 2.9 SP1 and corollaries A–E (symmetric anti-persistent chain, B = 1)

- **Closest sources.** The two-state chain has second eigenvalue ρ = 1 − t01 − t10. That gives
  `P(S_{t+j} = 1 | S_t) − 1/2 = ρ^j(·)`, which is textbook Markov-chain algebra (not re-opened). After that, N1
  applies.
- **Attempted reduction (brief item (d): "is SP1 just an LP ratio over geometric series once N1 is in hand?").**
  **Yes, essentially.**
  - Lemma S is the eigenvalue formula, giving weights `w_y(j) = (2y−1)gρ^j`.
  - Lemma W is a max-weight selection of disjoint unit blocks on an alternating, monotonically decaying sequence,
    with a per-block switch cost 2k: cover each positive step with `a_j > 2k`. It is a short exchange argument.
  - Lemma K is a case analysis of one shared free final switch.
  - Theorem SP1 is the substitution of Lemmas W and K into N1's κ. The closed forms are geometric sums
    `g r^d (1 − r^{2n})/(1 − r²)`.
  - SP1-A (even d ⇒ Γ = 0) is a sign/parity statement about `ρ^d` with ρ < 0.
  - SP1-B and SP1-C are monotone bounds on the same expression.
- **Exact difference.** The specific formula, the parity phenomenon in d, and the explicit open region
  `2c + k < g r^d (1 − r)` have no published counterpart I could find. All are elementary consequences of N1.
- **Classification:** PARTIAL OVERLAP. **New application / worked example.** The parity effect is a nice expository
  finding, not a theorem-level contribution.

### 2.10 Theorem S0 (static alternative, c = 0, any B ⇒ Γ = 0)

- **Closest sources.**
  - Classical Bayesian sequential testing with costly or free observations and monotone (threshold) stopping
    regions in the binomial sufficient statistic: Wald–Wolfowitz (1948), Arrow–Blackwell–Girshick (1949),
    DeGroot, *Optimal Statistical Decisions* (1970), Chernoff (1959). `[none opened; from memory;
    REVIEW_S0 §4 also flags them as unverified]`. Chernoff 1959 has a META record via WP F.
  - Krishnamurthy Thm 6.3.4 (switching curve for stopping POMDPs under (C), (F1), (F2), (S)).
  - Blackwell's comparison of experiments, for the calendar reduction (not opened).
- **Attempted reduction to Krishnamurthy Thm 6.3.4.**
  - Model the problem as a stopping POMDP on the static three-world state space (A0, N, A1). The identity
    transition is TP2. The observation kernel Ber(e0), Ber(1/2), Ber(e1) is TP2 in that order, because
    e0 < 1/2 < e1. So (F1) and (F2) hold.
  - **The reduction fails at (C):**
    - the continue cost (e0, 0, e1) is not monotone in the world order;
    - the stopping cost is not linear in the belief, since it is a concave continuation value with switch costs and
      rollback.
  - So 6.3.4 does not apply as stated. REVIEW_S0 reached the same conclusion independently.
- **Attempted reduction to Wald–Wolfowitz / SPRT structure.** The classical two-hypothesis results do not cover a
  three-world mixture in which one world (N) carries only the Lagrangian risk, with a post-stopping controlled
  continuation. The calendar reduction (Lemma CAL) is exchangeability plus a Blackwell-type "earlier free information
  is no worse" step. Both are standard.
- **What remains.** The G/D pair induction ("D monotone and D − G monotone in x", the clip identity for rollback).
  It is short and elementary, a monotone-comparative-statics argument in the spirit of Topkis/Lovejoy, but I found
  no direct citation.
- **Classification:** PARTIAL OVERLAP. **New application** of monotone optimal-stopping comparative statics. The
  result is the only proved zero-premium statement with B ≥ 2. Its scope (static, c = 0) is the regime where
  exchangeability makes the problem one-dimensional, i.e. where the result is most expected.

### 2.11 The falsifications CE-12 / CE-14 and the WP-D structural characterisation

- **Closest sources.**
  - Fauß–Zoubir–Poor §7. Opened by me. It contrasts single-threshold tests (fixed-sample, quickest change),
    whose least-favourable laws are "of the capacity type" and do not depend on the decision rule, with
    multi-threshold sequential tests, whose least-favourable laws depend on the history.
  - Huber–Strassen (1973; META, via the Fauß et al. 2021 survey).
  - For M3: the optimality of runs-type tests of i.i.d. Bernoulli against a two-state Markov (persistent)
    alternative. Lehmann (TSH), as cited by Campbell–Godbole–Schaller (Comm. Statist. 1994).
    `[abstract-level search snippet only; Lehmann not opened]`.
- **Attempted reduction of the WP-D dichotomy.**
  - "Γ = 0 when the Lagrangian-optimal decision region is an up-set; Γ > 0 needs a non-up-set region the adaptive
    null can exploit" restates, for this model, the classical dichotomy:
    - one-sided/single-threshold regions have a fixed least-favourable law, here the top point IID(1/2), by
      Strassen domination;
    - regions that are not up-sets have history-adaptive least-favourable laws (Fauß et al. Thm 6 and §7).
  - The mechanisms:
    - **M0** (exchangeable + MLR ⇒ the likelihood ratio is monotone in the count): Karlin–Rubin.
    - **M2** ("correlated coin": `P_A(Y = 0) > 1/2` makes the region {Y = 0} NP-preferred): the NP lemma.
    - **M1** (anti-persistence makes a negative label predict favourable steps): `ρ < 0`.
    - **M3** (persistence makes `P_A(0101) ≪ P_A(0001)`, so the likelihood ratio against IID depends on the
      number of runs and is not coordinatewise monotone): the classical reason runs tests are optimal against
      Markov dependence.
  - Once the region is not an up-set, an adaptive null playing `p_t = 0` at a public node inflates its probability.
    That is the trivial direction of domination.
- **What remains.**
  - The certified witnesses: CE-12 at B = 4, α = 25/32; CE-14 at α = 5/16 and 1/2, with Γ ≈ 1.3e-4 and 3.2e-5.
  - The *finding* that the premium survives the decision weights G at practical α in symmetric stationary
    persistent chains.
  - These are new numerical facts that refute an in-house conjecture. They are not new mechanisms. The magnitudes
    (≤ 2.1e-3) are small.
  - WP-D itself says the taxonomy is not a theorem.
- **Classification:** PARTIAL OVERLAP (known mechanisms; new instances). **New finding, not a theorem.**

---

## 3. Phase C: closest prior work

| Source | Year | Venue | Read status (this audit) | Overlap | Key difference |
|---|---|---|---|---|---|
| Fauß, Zoubir, Poor, *Minimax optimal sequential hypothesis tests for Markov processes*, arXiv:1811.04286v2 | 2020 | Ann. Statist. 48(5) | **OPENED** (§2.3 eq. 2.6, Thms 4–6, §7 read by me) | Rectangular per-step uncertainty; history-adaptive LFDs; Lagrangian for error constraints; single- vs multi-threshold LFD dichotomy (§7, discussion) | No nominal-point gap, no HMM decision cost, no query budget or delay; Markov-statistic sets, not fully history-adapted |
| Doerr, *Probabilistic Tools for the Analysis of Randomized Optimization Heuristics*, arXiv:1801.06733v6 | 2020 | Springer book chapter | **OPENED** (§1.8.3–1.8.4: Lemmas 1.8.7, 1.8.8, Thm 1.8.10) | Sequential domination by independent Bernoullis under conditional-probability bounds; uniform coupling | Stated for sums. The up-set form needs Strassen (Thm 1.8.10 / Roch 4.17) |
| Roch, *Modern Discrete Probability*, Ch. 4 | 2014 | lecture notes | OPENED by WP F (not re-opened) | Strassen for Markov kernels (Thm 4.17) | Not peer reviewed; cite Strassen 1965 / Kamae–Krengel–O'Brien 1977 (META) instead |
| Krishnamurthy, *Structural results for POMDPs*, arXiv:1512.03873v1 | 2015 | tutorial (CUP 2016 book) | Statements OPENED by WP F; I located the Thm 4.3.1/5.2.1/6.3.4 headers and the "open problem" remarks in the text | TP2/MLR filtering monotonicity; threshold stopping | Condition (C) fails for S0; single law, no robust constraint |
| Walraven & Spaan, *Column Generation Algorithms for Constrained POMDPs* | 2018 | JAIR 62 | Theorems OPENED by WP F; abstract verified by me | LP over policy mixtures, Lagrangian bound | One law, no robust constraint |
| Waudby-Smith & Ramdas, arXiv:2010.09686 | 2024 | JRSSB (journal metadata not verified) | **OPENED** by me at Prop. 3 (universal representation, "≤ 0" supermartingale version) | Composite nulls of conditional-mean type ⊇ adapted p_t ≤ 1/2 | Validity of constructed test supermartingales, not optimal-value comparison |
| Modak, Bakshi, Dey, Prabhakaran, *Sequential Adversarial Hypothesis Testing*, arXiv:2511.10181 | 2025 | arXiv (ISIT 2024 short version) | Abstract + HTML read **via a fetch-tool summary only** | Adaptive adversary choosing laws from convex sets using the past; the converse is attained by an i.i.d. adversary (adaptivity does not change exponents) | Asymptotic exponents, not finite-horizon constrained values; no decision cost |
| Mankowitz et al. (RC/R3C), arXiv:2010.10644; Russel et al., arXiv:2010.04870 | 2020 | arXiv | search snippet only | Robust constraint + nominal reward (the "RC" objective) | No gap-to-nominal characterisation; continuous control |
| Fauß, Zoubir, Poor, *Minimax robust detection* survey, arXiv:2105.09836 | 2021 | IEEE TSP 69 | OPENED by WP F | Huber 1965 stochastic-dominance criterion; Huber–Strassen capacities | Fixed-sample, marginal (not adapted) uncertainty |
| Karlin–Rubin / Lehmann–Romano TSH §3.4 | — | book | **not opened (memory)** | Monotone-likelihood-ratio UMP for one-sided composite nulls, i.e. W at B = 1 | Decision-weighted alternative |
| Wald–Wolfowitz 1948; Arrow–Blackwell–Girshick 1949; DeGroot 1970; Chernoff 1959 | — | — | **not opened (memory)**; Chernoff META | Bayes sequential testing with thresholds in the sufficient statistic (S0) | Three-world Lagrangian with controlled continuation |
| Campbell, Godbole, Schaller 1994 (citing Lehmann) | 1994 | Comm. Statist. | search snippet only | Runs tests optimal for i.i.d. vs Markov-Bernoulli (M3 mechanism) | Testing only |
| Shi et al., *Curious price of distributional robustness*, arXiv:2305.16589 | 2023 | NeurIPS | search snippet only | "Price" of robustness in RMDPs | Sample complexity, not a value gap |
| De Cooman & Hermans, *Imprecise probability trees*, arXiv:0801.1196 | 2008 | AIJ | search snippet only | The causal null is an imprecise probability tree with local credal set [0, 1/2]; upper probabilities via backward recursion | I did not find an explicit "up-set upper probability = top i.i.d. point" statement; not claimed |

**Sources cited in `PRIOR_ART_SOURCES.md` that I did not re-open:** Krishnamurthy–Pareek (2015), Lovejoy (1987,
both papers), Yost–Washburn, Poupart et al., Helmeczi et al., Kim et al., Altman, Ramdas et al. (2023), Grünwald
et al., Ruf et al., Kamae–Krengel–O'Brien, Liggett–Schonmann–Stacey, Shaked–Shanthikumar, Bertsimas–Sim, the
conservative-bandit papers, Arora–Dekel–Tewari, Dekel et al., Iyengar, Nilim–El Ghaoui, Wiesemann et al.,
Epstein–Schneider, Shapiro, Goyal–Grand-Clément, Krale et al., Naghshvar–Javidi, Heck et al. Their read statuses
in that file stand. I spot-checked WP F's Krishnamurthy and Waudby-Smith–Ramdas claims in the primary text and
found them accurate.

---

## 4. Verdict table

| Result | Closest source (section) | Classification | New theorem vs new application |
|---|---|---|---|
| Γ definition | Fauß et al. (2.6) + Thm 6; RC robust-constrained MDP | PARTIAL OVERLAP | new application (framing) |
| R / R′ | Walraven–Spaan §3 + Doerr L1.8.7/1.8.8, Thm 1.8.10; Roch Thm 4.17 | PROVED EQUIVALENT | application |
| Zc | Doerr L1.8.7 (sequential hypothesis on z) + Strassen | PROVED EQUIVALENT | application |
| P | folklore interchange | PARTIAL OVERLAP | lemma only |
| Z1 / W / W\* | Karlin–Rubin (memory) + Krishnamurthy Thm 4.3.1 | PARTIAL OVERLAP | application |
| N1 | NP lemma (LP form) + per-node composite null; Fauß Thm 4 | PARTIAL OVERLAP | application (exact, elementary) |
| S1 | Karlin–Rubin + Thm 4.3.1 | PROVED EQUIVALENT in substance | corollary |
| C3″ | special case of SP1/N1 | PARTIAL OVERLAP | example |
| SP1 (A–E) | N1 + two-state-chain eigenvalue algebra | PARTIAL OVERLAP | application / worked example |
| S0 | Wald–Wolfowitz/DeGroot-type threshold stopping (memory); Krishnamurthy 6.3.4 fails at (C) | PARTIAL OVERLAP | application; G/D induction is the only uncited step |
| CE-12 / CE-14 | Fauß §7 dichotomy + runs-test likelihood structure | PARTIAL OVERLAP | new numerical finding |
| WP-D taxonomy | Fauß §7; NP/Karlin–Rubin | PARTIAL OVERLAP | descriptive, not a theorem |

**No result is PROVED DISTINCT, and none is UNRESOLVED in the sense of "possibly already published verbatim".**
The residual unknown is whether a statistics or OR paper has computed robust-minus-nominal values for a specific
sequential design. Three formulations each found nothing; absence of a hit is not proof of absence.

---

## 5. What would be needed to claim novelty at main-track level

1. **A general multi-label theorem.** B ≥ 2 is the only regime where the null's adaptivity is real, since at B = 1
   it is a per-node composite null.
   - Candidate: a primitive necessary-and-sufficient condition for Γ = 0, e.g. on the history likelihood ratio
     `P_A(y)/2^{−B}` weighted by continuation gains (the "flip-monotone null odds" idea in
     `MULTILABEL_ZERO_PREMIUM.md` §4.4).
   - Or a sharp bound on Γ in terms of an "inflatability" functional of the optimal region, e.g. the sup over
     adapted nulls of the mass outside its up-set hull.
   - Either must be proved for adaptive query and promotion timing, not only fixed calendars.
2. **A scaling law that contrasts with the asymptotic literature.** Modak et al. show that adaptivity does not change
   error exponents. A theorem giving Γ's order in (T, B, mixing) would make "finite-horizon decision premium vs zero
   exponent premium" a crisp, citable separation. Candidates: Γ = Θ(·) as B grows; Γ → 0 under mixing at rate ...;
   or Γ bounded away from 0.
3. **Closing S0's open case** (static, c > 0; Lemma S+) would extend the only multi-label zero result. On its own
   it would still be a restricted proposition.
4. **Citations to fix before any write-up:**
   - cite Doerr L1.8.7 / Strassen for R5 and Zc instead of presenting them as new;
   - present W as the decision-weighted Karlin–Rubin condition (open Lehmann–Romano §3.4 and verify the theorem
     number);
   - cite Fauß et al. §7 for the threshold/LFD dichotomy;
   - open Wald–Wolfowitz / DeGroot before claiming anything about S0's threshold structure.

**Suggested honest positioning (one verifiable sentence).** "We define the premium Γ that a budgeted,
delayed-label promotion rule pays for being calibrated against every adapted null p_t ≤ 1/2 rather than the
IID(1/2) null. We show it vanishes whenever the IID-optimal promotion region is an up-set (via sequential stochastic
domination), compute it exactly for single-label designs (where it reduces to a composite-null Neyman–Pearson LP),
and exhibit certified positive premia in persistent multi-label cells." That is a solid workshop or applied-section
contribution. It is not a main-track theory paper as it stands.

**Novelty-check report summary.** Score **3/10 as a theory contribution**: the mechanisms are known, though no
named paper contains the results, so this is not the 1–3 "already published" band in spirit. Score **5/10 as a
problem-plus-finding**. Recommendation: **PROCEED WITH CAUTION.** The thin point is item 1 above.
Risk: a reviewer will cite Fauß–Zoubir–Poor (2020), Karlin–Rubin, and Strassen/Doerr, and say "B = 1 is a composite
null; B ≥ 2 is unresolved".

**Continue / pivot / stop (novelty axis only):**
- **Continue** only if the programme commits to item 1 or item 2.
- Otherwise **pivot** the B = 1 results into a supporting proposition inside an applied paper.
- Do not present R, Zc, P, Z1, S1 or SP1 as standalone theorems.
