# Competing research directions (Phase C)

**Recorded 2026-10-28, loop tick 5.** The lead (Opus) wrote this from the evidence inventory
(`RESEARCH_EVIDENCE_INVENTORY.md`) and the prior-art matrix (`PRIOR_ART_AND_NOVELTY_MATRIX.md`,
including Codex's independent verdict in Appendix G). No new experiment was run. Every claim
carries one of four status labels:
- **[established]**: a published theorem or a frozen repository result;
- **[derivation]**: the lead's own unchecked algebra;
- **[hypothesis]**: empirical, untested;
- **[heuristic]**: an engineering rule.

## 0. One new derivation that reshapes G4 [derivation, lead, unchecked]

Codex warned that G4 might reduce to an existing problem. Here is a check of when burst-robust
allocation can matter at all. Take a gated HT increment with propensity `q`, paired cost `Z` in
`[-5, 5]`, and conditional mean `μ` on disagreement events. Per disagreement:
- the increment has mean `μ` (unbiased);
- its second moment is about `E[Z²]/q`;
- expected labels spent are `q`.

Small-bet log-wealth growth per disagreement is about `λμ − λ²E[Z²]/(2q)`, maximised at
`λ* = μq/E[Z²]`, with value `μ²q/(2E[Z²])`. **Growth per label is therefore about `μ²/(2E[Z²])`,
independent of `q`,** whenever the predictable bet cap `λ ≤ q/(5+ε)` (from the support bound
`5/q + ε`) does not bind.

The cap binds when `μ/E[Z²] > 1/(5+ε)`, the strong-signal regime. There, growth per label scales
with `q`, and lowering `q` (as a past-paced pacer does during a burst) directly loses evidence per
label.

Consequences:
1. **Weak-signal regime:** the rate `q` does not matter per label. Only *when* labels are spent
   matters, before or after the onset. G4 then reduces to online allocation of a budget against an
   unknown onset. That is close to sampling-rights detection (Geng–Bayraktar–Lai 2014) and online
   knapsack with inventory reservation (Zhang & Cheung 2024). **The novelty risk is high.**
2. **Strong-signal regime:** the bound cap makes low `q` costly. This is a genuinely
   inference-specific trade-off: reserve exhaustion against cap-induced growth loss. It matches
   the repository's evidence that fixed gating beat paced gating:
   - EIA injected harm has a constant `Z = +5` on flipped events, which is strong signal;
   - S3 `harmful_adaptation` showed disagreement rising from 9% to 42%.

   **[hypothesis]** The fixed-versus-paced reversal should vanish in a weak-signal cell. That is a
   cheap, falsifiable prediction from existing code.
3. The derivation must be checked: the second-order expansion, the mixture over stakes, and
   whether the hard reserve stop changes the picture. Until then it is a working hypothesis for
   scoping, not a result.

## 1. Paths evaluated

### Path A: rigorous benchmark and failure-analysis paper (Q1–Q3, separate panels)

- **Problem and estimand.** Where do decision-aware monitors and intervention rules succeed or
  fail at matched information and resource budgets? There are three estimand panels, never pooled:
  distributional change, predictive degradation, and paired decision harm
  `R_t(π_t) − R_t(π_ref)`.
- **Closest prior work and delta:**
  - Ahmed et al. 2026: a label-free temporal-shift audit; predictive endpoints; one natural shift
    pair.
  - DISCERN 2026: gating mechanism and theory, but no benchmark of composed panels.
  - Timans et al. UAI 2025; PPRM ICML 2026; WATCH ICML 2025.
  - **Defensible delta [established components; claim to be tested by review]:** the first
    matched-information benchmark of *paired decision-harm* monitors and costed intervention
    rules. It has calibrated nulls (S2: 2,000 streams per cell; WP4 per-path orientation nulls),
    source-faithful comparators, and four headline findings, each of which is either new or
    contradicts received practice:
    1. **Label waste.** Ungated sparse-label monitoring spends about 91% of labels where the paired
       cost is known to be zero. Gating gives 7.2× evidence growth (S3 P1 [established]) and
       detects in 100 of 100 discordant streams (P2 [established]).
    2. **Analytic growth law.** G1's analytic growth ratio predicted the measured S3 ratios within
       15% at all four budgets [established].
    3. **Pacing reversal.** Fixed gating at least matches past-paced gating under bursty
       disagreement, in synthetic data (R7) and on EIA [established]. Section 0 gives a candidate
       mechanism [derivation].
    4. **Fallback dominance.** Monitor-then-revert (`q1_fallback`) gains +665 against +118 for the
       full pipeline on boundary harm, but −1,148 under post-promotion reversal [established,
       frozen 100-seed confirmation; previously undiscussed]. Certify-then-promote earns its cost
       only when reverting is unavailable or harmful.

    Plus the negative screens (stratified, data-efficient, ADG, integrated controller) with their
    registered margins.
- **New theory?** Limited. The growth law and the Section 0 cap/regime analysis can be stated as
  propositions. They are explanatory, not a new method.
- **Strongest competing baseline:** the published compositions themselves: gated HT with Timans
  GRAPA, and the PPE gated alias. The benchmark's claim is about *where* methods win, not that ours
  wins.
- **Signal already present:** strong. S2, S3, WP2–WP4, the integrated confirmation, PPE, Timans and
  Target-Scout are all frozen and verified.
- **Missing data and identification:** no untouched real-data holdout. Real-data panels must be
  labelled retrospective. Paired costs are identified only in synthetic data and in the
  imposed-cost EIA task.
- **Compute:** low. Mostly re-analysis. At most one registered cheap cell is needed: the
  weak-signal pacing check.
- **Main reviewer objections:**
  1. "A benchmark of your own adaptations." Answer with source-fidelity labels and the
     replay-verified Timans, PPE and Xu factors.
  2. "Synthetic-heavy." EIA WP4 is the only real paired-cost panel, and its costs are imposed.
  3. "Overlap with Ahmed et al. and DISCERN." Differentiate on estimand and matched budgets.
  4. "Is a benchmark enough for ICML/NeurIPS main track?" Possibly only a Datasets & Benchmarks
     track, or TMLR.
- **Minimal falsification experiment:** re-derive every headline from the frozen artifacts with an
  independent verifier (no new seeds). If any headline fails to reproduce, or a stronger published
  comparator with default settings reverses a ranking, drop that headline. A secondary check is a
  pre-registered weak-signal pacing cell. If fixed gating still beats paced gating there, the
  Section 0 mechanism is wrong and the pacing finding is reported without an explanation.
- **Strong enough for a paper?** Yes for a benchmark venue (NeurIPS D&B, TMLR, or JMLR MLOSS-style).
  Uncertain for a main track.

### Path B: statistically controlled policy promotion with adaptive acquisition and switching costs

- **Problem.** Certify a selected candidate's net benefit before promotion, with adaptive label
  acquisition and switching costs.
- **Prior work.** OCS / Karampatziakis 2021, HCPI, OPI/AnyRank alpha-spending, Digalakis 2025/26,
  Zhang–Wu–Qian 2026, PPE / Xu, DISCERN Prop. 13.
- **Combination test: fails** (B1 §1, Codex G2). **Reject as a method.** The only surviving narrow
  form is G2 (Path C2).

### Path C1: a hard-budget allocation theorem for gated anytime-valid monitoring under bursts (G4, Paper 3)

- **Problem and estimand.** For a gated monitor with a hard label budget `N` and an adversarial
  class of disagreement-arrival sequences with an unknown onset, minimise worst-case censored
  detection delay (or maximise fixed-horizon power) at level α.
- **Prior work.**
  - Cheng et al. 2026 (static hard-budget lower bounds).
  - Efroni et al. 2021 (Confidence-Budget Matching).
  - Zhang & Cheung 2024 (inventory reservation).
  - Geng–Bayraktar–Lai 2014 (sampling rights, Bayesian, known densities).
  - Xu et al. (expected budget).
  - DE-CuSum.
  - Codex: PROCEED, the only gap passing both tests.
- **Theory possible?** Plausible but unproven. **Section 0 suggests the weak-signal case reduces to
  known online allocation.** Inference-specific content lives only in the strong-signal,
  cap-binding regime. A theorem would need: a fixed horizon or exposure model; bounded losses; an
  admissible burst class; a lower bound for every predictable allocation; and an attaining schedule
  such as a reserve-doubling rule.
- **Strongest baseline:** fixed gating at the reserve-limited rate, which already beats paced
  gating, plus a Zhang–Cheung-style reservation schedule.
- **Signal already present:** two observations of the motivating failure (S3 R7, WP4 EIA). It is
  also a caution: M4, an evidence-driven observation controller, failed against an onset-informed
  temporal baseline.
- **Missing data:** none for the theory. The empirical test can reuse the WP1 and WP4 generators.
- **Compute:** low.
- **Main objections:**
  - "Uniform is optimal, or it is a knapsack problem" (Codex).
  - "Niche: a label-budget detail of one monitor family."
  - "The strong-signal regime is where detection is already easy."
- **Minimal falsification:** a theory pre-screen with no runs. Derive the minimax delay for the
  two-regime model. If the optimal schedule is uniform or fixed gating up to constants, or the
  problem maps exactly onto a known knapsack or sampling-rights result, stop. Empirically, if the
  derived schedule does not beat fixed gating by the registered margin on the existing burst
  generators, stop.
- **Strong enough?** Only if a non-trivial lower bound plus an attaining rule emerges. Then it is a
  focused theory paper (COLT, AISTATS or ALT more than ICML). Otherwise it is a proposition in
  Path A.

### Path C2: prospective certifiability of post-switch net benefit (G2, Paper 2)

- **Problem.** Characterise when the future net benefit of a promoted candidate can be certified
  from past evidence, and give an attaining procedure and a lower bound.
- **Prior work.** SPIN (Chandak 2020, asymptotic), OPFV (Shimizu 2025), OPEN (Chandak 2022),
  Zhang–Wu–Qian 2026, DISCERN §5.7.
- **Theory possible?** Only with a transport restriction such as a variation budget or a
  structural forecast model. Without one, histories do not determine futures. **Codex's worst
  objection, "the persistence assumption does the work", is decisive unless the characterisation
  itself (necessity plus sufficiency) is the contribution.**
- **Signal present:** the `post_promotion_reversal` profile shows non-persistence destroying value
  (−1,532 for fixed-candidate certification). That motivates the question but tests no theorem.
- **Data:** no real source with a promotion followed by an observed post-switch horizon under a
  known design.
- **Compute:** low (theory plus synthetic).
- **Minimal falsification:** show that under the chosen restriction the certificate reduces to
  "CS minus drift allowance minus cost" with no matching lower bound. If so, stop.
- **Strong enough?** Possible as a theory paper, but the risk is high and no repository evidence
  bears on it yet.

### Path C3: delayed, informative bandit-feedback harm monitoring (G1)

- **Prior work.** Waudby-Smith et al. 2022/24 and Lindon & Kallus ICML 2026 cover the core. The
  combination test fails for ordinary selective feedback.
- **Verdict:** a section at most (Codex concurs). **Reject as a paper.**

### Path D: causal or partially identified decision-harm monitoring

- **Problem.** With a deterministic deployed policy and no randomisation, the reference action's
  loss is unobserved on disagreement events. Harm is then only *partially identified*. Monitor the
  lower bound of the identified set sequentially (Manski-style bounds), or a tail (CVaR) harm
  target.
- **Prior work.** Feng et al. AISTATS 2024 (identification under performativity, asymptotic);
  Valdrighi et al. 2026 (performative selective labels); Lindon & Kallus 2026; anytime-valid
  bounds-based inference in general.
- **Combination test:** **likely yes** ("Manski bounds plus an e-process on the bound";
  "CVaR CS plus gating") [lead judgement; not searched in depth].
- **Signal present:** none. No experiment in the repository targets partial identification.
- **Data:** it needs bandit-feedback data with known logging (OBD, Hillstrom). Both are exposed or
  exploratory.
- **Verdict:** **do not pursue in this phase.** Record it as an open question for a future
  charter revision.

### Path E: unified monitor–certify–intervene method (the brief's unifying question)

**Rejected.** There is a standing NO-GO (2026-10-26); integrated profiles are profile-specific and
the controller is inert; and Drift2Act plus Regol/CARA plus Conformal Policy Control cover the
framing. Nothing in Phases A–B reverses it.

## 2. Ranking

Each criterion is scored 1–5. Scores are lead judgement, informed by Codex.

| Path | Importance | Novelty | Theoretical tractability | Empirical feasibility | Evidence already present | Total |
|---|---:|---:|---:|---:|---:|---:|
| **A. Benchmark / failure analysis** | 4 | 2–3 | 4 (propositions only) | 5 | 5 | **20–21** |
| **C1. G4 hard-budget allocation** | 2–3 | 3–4 | 2 (unproven; partly reduces) | 4 | 2 | **13–15** |
| C2. G2 prospective certifiability | 3–4 | 3 | 1–2 | 2 | 1 | 10–12 |
| D. Partial identification / tail harm | 3 | 2 | 3 | 1 | 0 | 9 |
| C3. G1 delayed bandit feedback | 2 | 1–2 | 3 | 2 | 1 | 9–10 |
| B. Controlled promotion method | 3 | 1 | 3 | 3 | 2 | 12 (reject: fails combination test) |
| E. Unified method | 4 | 1 | 1 | 2 | 1 | rejected |

**No compelling new method has been identified.** C1 is the only candidate with a live novelty
case. Its tractability is unproven, and Section 0 suggests half of it reduces to known allocation.

## 3. Selection for Phase D

**Refine Path A as the dominant contribution.** Phase D writes one proposal:
- **dominant claim:** the matched-information decision-harm benchmark, with the four headline
  findings, every one traceable to frozen, verified artifacts;
- **at most one supporting claim:** the regime analysis from Section 0. It explains why gating and
  pacing behave as observed, it is falsifiable with one cheap pre-registered cell, and it is stated
  as a proposition with explicit proof obligations.

**C1 (G4) is carried as a separately gated Paper 3 theory pre-screen,** not as part of the
benchmark claim. It is a pencil-and-paper minimax derivation with a stop rule (Section 1, C1). It
is not implemented unless the derivation yields a non-uniform optimal schedule and a lower bound.

**C2, C3, D and B are recorded and parked.**

**Abandonment trigger for Path A (to be sharpened in Phase D):**
- independent re-verification fails for two or more of the four headlines; or
- the source-by-source review finds a published matched-information decision-harm benchmark
  covering the same findings.

If either happens, the decision moves to NO_GO for a standalone paper.
