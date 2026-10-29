# Final research proposal

> **Historical proposal; direction superseded 2026-10-28 by the user.** Follow
> [budgeted switching research goals](../budgeted_switching_research_goals.md).
> The benchmark-paper selection below is retained as a decision record; its evidence remains valid.

**Recorded 2026-10-28, loop tick 10 (Phase F1).** This proposal follows two refinement rounds and
two independent Codex (`gpt-6.1-sol`, xhigh) adversarial reviews. All five round-1 fatal
objections were resolved, and refinement converged under loop exit condition 2.

**Status labels:**
- [established]: a frozen, verified result or a published theorem;
- [lemma]: an exact identity, with the proof still to be written;
- [hypothesis]: a registered prediction, not yet tested;
- [heuristic]: an engineering rule.

## 1. Decision

**BENCHMARK_PAPER.**

- **NEW_METHOD is not selected.** No candidate mechanism survived its registered screen: stratified
  allocation (WP2), the data-efficient controller (WP3), the ADG anchor, and the integrated
  controller. Every broad framing fails the "two existing algorithms" test (prior-art matrix
  §1 and B2). The one gap that cleared novelty review, G4 (finite-budget allocation under bursts),
  reduces to temporal budget allocation (tick-6 correction) and is expected to stop at its
  theory pre-screen.
- **PIVOT is not selected.** No other problem has materially stronger support. Partial
  identification, tail harm, G2 and G3 have no repository evidence and an unfixed estimand.
- **NO_GO is not selected yet.** Reproducible benchmark findings exist, and the experiments that
  could establish benchmark value have not been run (Codex round 2: "premature before the corrected
  experiments").
- **Both prior NO-GO decisions stand**: 2026-10-26 (unified algorithm) and 2026-10-27 (Paper 1
  monitoring algorithm).

**Target venue:** NeurIPS Datasets & Benchmarks or TMLR. An ICML main-track paper is not
supported (Codex 3/10).

## 2. Selected contribution

**A matched-resource evaluation contract for paired decision-harm monitoring and intervention, and
three bounded empirical findings it produces.**

**One-sentence takeaway (Codex):** buy labels where paired losses can differ, and compare fallback
and certification under the same monitoring, intervention and rollback opportunities.

| Component | Content | Status |
|---|---|---|
| **Contract (the reusable deliverable)** | Task and feedback taxonomy; separate clocks for event, reference training, monitor feedback and alarm; evaluator-only oracle separation enforced at the interface; source-fidelity-labelled adapters; a machine-checked seed registry; resource accounting (labels, dollars, compute, action opportunities); uncertainty procedures; hashed reference results | Specified, **not delivered** |
| **Finding 1: gating replicates under decision costs** | DISCERN's disagreement-gating label economics carry over to asymmetric-cost paired harm with finite reserves and non-stationary incumbents. **Credited to DISCERN.** Our part is the replication under this contract. | [established, development] in S3; confirmation in E2 |
| **Finding 2: pacing depends on the burst class** | Fixed against past-paced gating under specified onset and burst classes. Fixed is predicted non-inferior when bursts follow the onset; paced is predicted better when a harmless burst exhausts the reserve before late harm. | [hypothesis]. S3 R7 and WP4 are development observations for the first class only. |
| **Finding 3: intervention rankings depend on design** | In current integrated pipelines, monitor-then-revert beats the certification pipeline by **5.63× and 4.26× on two profiles**. On recurring regimes it gains +448.0 where the pipeline gains 0, so no ratio exists there. It loses by **8.0×** after a post-promotion reversal (−1,148.5 against −143.8). The arms differ in response latency, monitoring coverage and rollback availability. | [established, descriptive, post hoc] for the frozen state machines; which factor matters is tested in E3 |
| **Supporting: Lemma L** | For zero-anchor HT with fixed-fraction stakes and ε = 0, wealth after a given ordered sequence of labelled losses does not depend on the propensities; a fixed-weight stake mixture keeps this property. It is a **pathwise algebraic identity, not a validity theorem**, and it does not set calendar-time delay. **Credited** as elementary algebra on Timans et al. and Waudby-Smith et al. | [lemma]; the proof is two lines (round 2 §3) |

**Corrections carried from review 2:**
- "4–6× on three profiles" is wrong; it is 5.63× and 4.26× on two profiles.
- "Fixed detects no later" is replaced by the burst-class hypothesis H-B2.
- "Identical replay" is renamed **coupled replay**.
- Held-out authorities are **new paths for the same task, not a second task.**

## 3. Formal setup (frozen)

- **Filtration.** `F_t` contains, for events up to `t`:
  - the covariates `X_s`;
  - the deployed and reference policies in force at `s`, **including the reference-training
    channel**, meaning which outcomes the reference was refit on and when they became available;
  - the free disagreement indicator `D_s`;
  - the query coin `G_s`;
  - the outcome `Y_s` only if queried **and** its feedback clock has elapsed;
  - stopping and reserve indicators.
- **Four separate clocks:** event time, reference-training availability (24 h in the EIA task),
  monitor feedback (0 h in the frozen S3/WP4 primary; any delayed variant must specify pending
  queries, reserve charges and censoring), and alarm reporting.
- **Feedback.** The common-label contract: `Y_s` identifies both actions' costs. It holds only in
  the synthetic generators and the imposed-cost EIA reserve task. Action-dependent feedback is out
  of scope.
- **Estimand and null.** `H_0: E[Z_t − ε | F_{t−1}] ≤ 0` for all `t`, with
  `Z_t = c(π_t(X_t), Y_t) − c(π_ref(X_t), Y_t)` and ε = 0.1 (charter). Absolute reference risk is
  reported as a separate endpoint.
- **How the hard cases are handled:**
  - *Candidate selection:* candidates are frozen before evaluation.
  - *Adaptive sampling:* propensities are predictable from pre-event information, with the query
    coin independent of the outcome.
  - *Delayed labels:* explicit clocks; delayed monitoring is a separate registered variant.
  - *Repeated testing:* one e-process per registered arm and cell, with Bonferroni across cells for
    calibration and Holm within each confirmatory family.
  - *Optional stopping:* e-process validity at stopping times under `H_0`; the reserve stop is
    predictable.
  - **Composition across monitor → certify → promote is not controlled and not claimed.**

## 4. Exact falsifiable hypotheses

Each is registered before any run, on a **fresh seed block allocated through the machine-checked
registry**. All seeds are analysed, including no-alarm and no-promotion streams.

| ID | Hypothesis | Test | Supports / falsifies |
|---|---|---|---|
| **H-B1a** | Gated HT detects by the horizon more often than **uniform HT with the same engine and stake grid** at `r ∈ {0.02, 0.05}` in `boundary_local_harm` | Exact one-sided McNemar per budget, Holm over 2; n fixed by a power calculation from development-set discordance (target power ≥ 0.9) | Finding 1 is withdrawn if either budget fails |
| **H-B1b** | Acquisition efficiency (labels spent until alarm or horizon, censored) is at most 0.5× for gated against uniform HT at `r = 0.20`, where detection may saturate | Paired bootstrap upper 97.5% bound < 0.5 | Covers the ceiling-effect objection |
| **H-B2** | Burst classes: **(i)** a burst after the onset; **(ii)** a harmless pre-onset burst, then late harm; **(iii)** recurrent regimes. Fixed gating is non-inferior to paced in (i) and (iii) (margin −5 detection points, one-sided 97.5%). **Paced beats fixed in (ii)** (one-sided McNemar). | Holm over 3 | A discriminating prediction. Fixed failing in (i) or paced not winning in (ii) are both admissible outcomes and are reported. |
| **H-B3** | In a feasible matched-opportunity factorial (§5, E3), the sign of revert-minus-promote utility depends on post-alarm reference deterioration (a crossover interaction). Revert ≥ promote when the reference stays safe; promote > revert when it deteriorates. | Registered interaction contrast; paired seeds; Holm over the registered contrasts; no attribution percentages | Finding 3 becomes quantitative, or is reported as "ranking set by timing and rollback only" if there is no crossover |
| **H-B4** | On the **locked held-out EIA authorities**: (a) per-path orientation nulls hold (exact upper bounds, Bonferroni across authorities × arms); (b) under injected harm, fixed gating at `r ≥ 0.05` matches the full-feedback median delay in at least 80% of detectable cells | (a) a validity criterion; (b) a pre-registered descriptive replication criterion, with per-path and regional-cluster reporting | (a) failing is a validity stop for that arm; (b) failing withdraws the transfer statement |
| **L** | The pathwise identity holds exactly on stored labelled-loss sequences for the default mixture | Deterministic check in E1 | A mismatch is an implementation finding, not a hypothesis failure |

## 5. Experimental design

1. **E1. Reproduction and repair (no new seeds).**
   - An independent verifier recomputes H1–H4, the S2 null table, WP4 and Lemma L from frozen
     artifacts with hash checks.
   - Correct the S2 seed-block typo in a new erratum, not by editing history.
   - Resolve the Target-Scout source-hash drift by running the historical source or demonstrating
     equivalence.
   - Build the **machine-checked seed registry** and record the known overlaps.
   - Fix the WP4 freeze-record LF/CRLF hash issue.
2. **E2. Acquisition and pacing confirmation (H-B1, H-B2). Synthetic, fresh seeds, CPU.**
   - *Arms:* gated HT, uniform HT, uniform PPI; fixed and paced gating; fixed-stake mixture
     (Lemma L applies) and GRAPA (it does not).
   - *Design:* onsets swept independently of stage boundaries; the three burst classes.
   - *Outputs:* deployed mixture log-wealth plus the registered diagnostic.
   - *Mechanism check:* fixed-window informative-label counts predict delay on **held-out
     parameter cells**, reported against a simpler baseline predictor.
3. **E3. Matched-opportunity intervention factorial (H-B3). Synthetic, fresh seeds.**
   - *Timeline:* separate the trigger, certification start, certification completion, deployment
     and optional waiting.
   - *Factors:*
     - response ∈ {revert; certify-then-promote; **revert while certifying in the background**};
     - rollback ∈ {off; on with parity, so fallback arms also get rollback};
     - monitoring coverage ∈ {window ends at 1,600; covers the horizon};
     - onset ∈ {before; at; after the stage boundaries};
     - post-alarm reference ∈ {safe; deteriorating}.
   - *Outputs:* decision utility, reported with labels, compute and intervention counts.
     Monetisation only with a justified scale.
4. **E4. Locked held-out authorities (H-B4). Local snapshot, no download.**
   - *Eligibility, frozen before any value inspection:* exclude the 14 aggregates and CISO, ERCO
     and NYIS. Require D, DF, NG and TI series and next-hour demand coverage (eligibility code:
     `scripts/audit_eia_2026_holdout_readiness.py:87`), and at least 20 rehearsal procure events.
     Record every exclusion.
   - *Split:* about one third development, two thirds locked, by a pre-registered seed.
   - *Task:* the frozen WP4 task, with the four-clock contract.
   - The PPI arm is included only after a validated delayed-feedback proxy implementation;
     otherwise it is excluded and the exclusion stated.
   - *Audit:* outputs and configs, not just text references, for prior exposure.

## 6. Required baselines

- **Monitors:** uniform HT; uniform PPI (correctly bounded); gated HT fixed and paced; Xu active
  betting; the PPE gated alias (an algebraic alias, not an independent win); full feedback (an
  unmatched reference); feature ADWIN (a label-free sentinel); horizon SR/CUSUM.
- **Engines:** fixed-stake mixture, Timans GRAPA, empirical Bernstein.
- **Intervention rules:** continue, revert (`q1_fallback`), revert with rollback, revert while
  certifying in the background, two-gate, fixed-candidate certification, and the full pipeline.
- **Considered and excluded, with stated reasons:** Comparecast, which has a running-average null.
  It is valid on the eventwise subset, so it may be included as a disclosed-null comparator rather
  than excluded outright (Codex R2). Also PPRM, MOPE, OPI and Wang.

## 7. Theory obligations (none claimed as new)

1. Write out Lemma L's proof and its applicability table: holds for zero-anchor HT with
   fixed-fraction stakes and their mixture; **fails** for PPI (`log(1 + c/(2 − q))`); does not
   cover adaptive engines.
2. Complete the arm-by-arm validity table (pre-event information, query randomisation, bound and
   stake measurability, proxy updates, reference updates, stopping) for **every** arm, Xu and PPE
   included.
3. State the ε > 0 calculation as a conditional, local per-event quantity. Agreement events add
   factors `1 − λε`.
4. Credit DISCERN Thm 9 and Cor. 10 for the Θ(1/ρ) gating economics, and G1's prediction as
   consistent with it.

## 8. Decision rules (separated, per Codex R2)

| Kind | Rule |
|---|---|
| **Validity stop** | Any arm whose null calibration fails its registered exact bound (S2-style, or H-B4a) is withdrawn from all efficiency claims. An E1 failure of S2 or of a frozen hash triggers an audit before any new run. |
| **Claim withdrawal** | Each hypothesis H-B1 to H-B4 is withdrawn independently on failure. Results are reported either way. Inadequate power is distinguished from disconfirmation through the registered power calculation. |
| **Benchmark-value gate** | The contract counts as delivered only if an **independently implemented method enters through the public interface without evaluator access** and produces hashed results on the reference suite. A good candidate is a Comparecast or WATCH-style adapter written by a separate agent. |
| **Compute and data** | E2 and E3 run CPU-first after a development-set smoke. Any CUDA-scale run, and any new download (including the deferred post-freeze EIA pull), needs explicit user approval. |

**Abandon the paper (move to NO_GO; technical report only) if any of these holds:**
1. A validity-critical E1 failure is not explained by an implementation fault.
2. H-B1a fails at both budgets **and** H-B2 and H-B3 show no discriminating pattern, leaving
   nothing beyond a DISCERN replication.
3. The benchmark-value gate fails.
4. A published benchmark is found that covers reserve and temporal allocation plus intervention
   comparisons under decision costs.

## 9. Unresolved objections carried forward

1. **Main-track importance:** a benchmark of a narrow estimand family; Codex rates ICML 3/10.
2. **Real-data breadth:** one task family with imposed costs; held-out authorities are correlated
   and share examined calendar windows; no prospective evidence until the deferred pull.
3. **The H4 lesson has qualitative precedent** in Conformal Policy Control and SPIBB. Novelty
   depends on E3 finding a quantitative operating region.
4. **Synthetic evaluator-oracle utilities:** legitimate, but the cost scale is imposed.
5. **The contract is specified, not delivered.**
6. **The common-label contract excludes action-dependent feedback**, the setting where the
   literature's open questions (G1, G3) lie.

## 10. Separately gated track (not part of this paper)

**G4 / Paper 3 theory pre-screen.** Derive the minimax schedule for finite-budget gated detection
under an admissible burst class. **Stop** if it is fixed or uniform gating up to constants, or maps
onto Geng–Bayraktar–Lai sampling rights or Zhang–Cheung reservation. The expected outcome is stop.
The H-B2 class (ii) result will be informative either way.
