# Adversarial review, round 2

**Recorded 2026-10-28, loop tick 9.**
- **Reviewer:** Codex (`gpt-6.1-sol`, xhigh), read-only `codex exec` on `REFINEMENT_ROUND_2.md`
  and both addenda, at commit `af7b8b1`, under `REVIEW_BRIEF_2.md`.
- **Attempts:** the first attempt hung on stdin and timed out (exit 124, no output). The retry, with
  stdin closed, completed.
- **Independence:** an independent cross-model review. The four perspectives come from one model.
- **Verdict:** BENCHMARK_PAPER, continue conditionally. Scores: ICML main 3/10 (unchanged),
  NeurIPS D&B 5/10 (up from 4).

## Status of round-1 objections

| Round-1 item | Round-2 status (Codex) | Lead note |
|---|---|---|
| F1: null mis-stated | RESOLVED | — |
| F2: Proposition S corollary overreach | RESOLVED | Lemma L is a pathwise algebraic identity, not a validity theorem |
| F3: DISCERN mis-described | RESOLVED | Codex checked the primary PDF. §6.4 Table 3: audited-band median labels are 2,098 (uniform), 2,845 (PPI-style), 1,948.5 (active), 70 (DISCERN) |
| F4: H4 attributed to reference safety | RESOLVED (attribution withdrawn) | The descriptive state-machine result survives |
| F5: Claim A overgeneral | RESOLVED | — |
| Mixture, PPI, adaptive engines, ε remainder, reserve stop | RESOLVED | ε remainder: valid as a local per-event calculation only (new major 2) |
| Multiplicity | PARTIALLY | The E2/E3 families are not yet frozen |
| H1 diagnostic versus deployed wealth; uniform-HT isolation | PARTIALLY | Future E2 work |
| Matching definitions | PARTIALLY | **Terminology fix:** shared streams and uniforms are *coupled replay*, not identical feedback |
| H3 paired uncertainty | NOT RESOLVED | Deferred to E2 |
| Seed reuse; Target-Scout hash drift | NOT RESOLVED | Registry and equivalence check are E1 deliverables |
| H4 precedent (CPC, SPIBB) | PARTIALLY | E3 must find a quantitative operating region |
| D&B reusable contract | PARTIALLY | Specified, not delivered |

## New objections (accepted after lead checks)

1. **Numerical error in Claim B (lead-verified).** "4–6× on three profiles" is wrong. The ratios
   are **5.63× and 4.26× on two profiles**. On recurring regimes it is +448.0 against 0, so the
   ratio is undefined. The reversal ratio is 8.0×. *To be corrected in the final proposal.*
2. **"Fixed-rate gating detects no later" is stronger than the evidence.** Early harmless
   disagreements can exhaust a fixed rule's reserve before a later harmful burst. It must be stated
   as a bounded hypothesis for specified onset and burst classes, with non-inferiority failure
   admissible. (Accepted. It is consistent with the G4 trade-off of exhaustion against allocation.)
3. **The validity table is unfinished.** It needs Xu/PPE rows and the reference-policy training
   channel in the filtration (EIA weekly refits).
4. **The ε calculation is local.** Agreement events contribute negative factors when ε > 0. Define
   "per label" precisely.
5. **The E4 delay contract is ambiguous.** WP4 gives the *reference refits* a 24 h delay, while
   the monitor gets labels immediately. Freeze separate clocks.
6. **E2 is not frozen.** It lacks a sample size, margins, a powered McNemar, an
   acquisition-efficiency endpoint robust to ceiling effects, and a held-out-cell mechanism test.
   TOST and non-inferiority are conflated.
7. **E3 is not yet an identifying factorial.**
   - "Certify-and-promote at alarm" is infeasible as written.
   - Monitoring coverage is missing as a factor.
   - Rollback parity is missing.
   - It needs a "revert while certifying in the background" baseline.
   - A 50% decomposition is non-unique with interactions.
   - All seeds must be included, with no conditioning on alarms.
8. **E4 selection issues.**
   - Coverage is value-blind but not selection-free.
   - Task eligibility needs D, DF, NG and TI series plus at least 20 rehearsal procure events
     (`scripts/audit_eia_2026_holdout_readiness.py:87`).
   - Shared calendar dependence remains.
   - "No text reference" is not proof of no exposure.
   - **Held-out authorities are not a second task.**
   - The PPI arm needs a real delayed-feedback implementation.
9. **Abandonment criteria mix falsification with desired outcomes.** Separate claim withdrawal,
   validity stops, benchmark-value assessment and compute decisions.

## Convergence decision (loop exit condition 2)

Codex: *"Another broad refinement round is unlikely to resolve significant evidential
objections."* A short protocol-finalisation pass can fix the remaining definitions and ambiguities.
After that, only E1–E4 can settle the open items.

The lead agrees. Round 2 resolved all five fatals. Every remaining objection is either a
definitional fix (folded into the final proposal) or needs experimental evidence. **Refinement
stops at two rounds; the loop proceeds to F1.** The protocol-finalisation items above become
required content of `FINAL_RESEARCH_PROPOSAL.md` and `IMPLEMENTATION_READINESS_GATE.md`.

**Codex's verification limits:** it checked the CSV/JSON values and manifest hashes for S3, the
integrated outputs, both event logs, and the EIA results, protocol and code hashes, and all
matched. Python execution was denied, so Parquet-level statistics were not recomputed.

---

## Full review (Codex, verbatim final answer)

**Recommendation: BENCHMARK_PAPER, with substantial revision. Scores: ICML main 3/10; NeurIPS Datasets & Benchmarks 5/10.**

Round 2 repairs the central mathematical overclaims. It does not yet establish Claim B’s broader empirical conclusions or deliver a reusable benchmark. The next useful step is a concrete protocol freeze followed by experiments, rather than another general refinement essay.

I reviewed `af7b8b11eca277aec3434462c86f27ece4047bc2`, including both addenda. The four reviewers below are four perspectives from one assistant. No files were modified; the working tree remained clean.

**Reviewer 1: Statistical theorist**

**FATAL weaknesses:** None found in the restricted, zero-tolerance Lemma L. Its validity should not be extended to the broader empirical statements in Claim B.

The identity is correct. At a queried disagreement,
\[
1+\lambda_tV_t
=1+\frac{cq_t}{C}\frac{Z_t}{q_t}
=1+cZ_t/C.
\]
At an unqueried event, the factor is one when \(\epsilon=0\). Consequently, for the same labelled-loss sequence and initial wealth, each component product is propensity-independent. A fixed mixture preserves that identity.

The important qualification is that this is a **pathwise algebraic identity**, not a validity theorem obtained by conditioning on the selected labelled sequence. It neither equates the distributions of sampled losses nor establishes equal threshold-crossing times.

| Round-1 item | Round-2 status | Assessment |
|---|---|---|
| F1: incorrect current-context null | **RESOLVED** | The primary null now matches the charter. The registered independent-event controls support that interpretation. |
| F2: label counts determine calendar-time evidence/delay | **RESOLVED** | The corollary is removed; L fixes the labelled losses. |
| Mixture extension | **RESOLVED** | The fixed-weight mixture identity follows componentwise. |
| PPI extension | **RESOLVED** | Correctly excluded, with a valid counterexample. |
| Adaptive betting engines | **RESOLVED** | Correctly excluded from L. |
| \(\epsilon\) remainder | **RESOLVED**, within its stated local calculation | The remainder bound is correct; relative error near zero growth is acknowledged. |
| Reserve stopping versus allocation equivalence | **RESOLVED** | Predictable stopping preserves validity, while different rules retain different sampled prefixes. |
| Multiplicity and composition | **PARTIALLY** | Frozen study families are now distinguishable; E2/E3 families remain unspecified. Operational composition is appropriately disclaimed. |

**Does “fixed fraction of the cap” match the engines?** Yes for the default mixture: the implementation multiplies each component by \(1+c_jV_t/B_t\), with fixed fractions \(c_j\). It does not describe plug-in, empirical-Bernstein or GRAPA bets. The comparison engine additionally documents GRAPA’s calendar-event burn-in. See [the mixture implementation](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/eprocess.py:154).

The PPI counterexample also checks numerically:
\[
\log(1+0.8)=0.587787,\qquad
\log(1+0.8/1.9)=0.351398.
\]
Thus PPI’s propensity dependence is substantive, rather than a mixing artefact.

**MAJOR 1 — The validity table is still an unfinished proof obligation.**

For fixed and paced HT, the needed argument is available: the base disagreement propensity and bound are chosen from prior information; averaging over the independent query coin recovers \(Z_t-\epsilon\); averaging over current events invokes the past-conditional null. The code reads the pacer before updating it with the current event. That supports these rows. See [the replay](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/gated_monitor_comparison.py:188).

However, §4 leaves Xu/PPE as “to be tabulated,” omits explicit treatment of some engine/construction combinations, and inherits the filtration from round 1. The reference-policy training channel also needs to appear in that filtration, particularly for EIA’s weekly refits.

**Remedy and resolving evidence:** Finish one arm-by-arm argument specifying the pre-event information, query randomization, support bound, stake measurability, proxy updates, reference-policy updates and stopping indicator. The existing Xu/PPE audits contain much of the necessary algebra. Calibration experiments supplement this proof; they cannot replace it.

**MAJOR 2 — The positive-\(\epsilon\) calculation is local, not approximate global invariance.**

The displayed expression is interpretable as a conditional one-event expected log gain divided by its query probability. With varying propensities, it is not automatically an expected gain between successive labels. Also, the bound on \(R\) controls the linearization of the unqueried-event term; it does not bound every difference from the \(\epsilon=0\) wealth identity. Agreement events contribute negative factors when \(\epsilon>0\).

**Remedy and resolving evidence:** Explicitly condition the expectation, define “per label,” and restrict the applicability-table wording accordingly. A global approximation would require an additional bound covering the entire processed event sequence, including agreements.

**MAJOR 3 — The delay contract is ambiguous in revised E4.**

The existing WP4 protocol gives the **reference’s refits** a 24-hour label delay while supplying monitor labels immediately. Addendum 2’s “with a 24-hour label delay” could mean either that same construction or delayed monitoring as well.

**Remedy and resolving evidence:** Freeze separate clocks for event occurrence, reference-training availability, queried-monitor feedback and alarm reporting. If monitoring is delayed, specify pending queries, reserve charges, end-of-window censoring and how queries/bets use available history. An unchanged immediate-feedback replay plus a blanket time shift is insufficient for every proposed adaptive construction.

The multiplicity revision is otherwise materially better. For example, the conservative simultaneous upper bound across WP4’s 68 primary zero-alarm cells is indeed
\[
1-(0.05/68)^{1/1000}=0.007189,
\]
approximately 0.72%. This is simultaneous uncertainty about calibration probabilities, rather than operational control across all future interventions.

**Reviewer 2: Prior-literature specialist**

**FATAL weaknesses:** No identified paper establishes that the entire proposed benchmark already exists. However, Claim A has no surviving contribution as a general explanation, and Lemma L should remain credited explanatory algebra.

| Round-1 item | Round-2 status | Assessment |
|---|---|---|
| F3: DISCERN mischaracterized as theory-only | **RESOLVED** | The revised credit is appropriate; I checked the primary PDF. |
| Proposition S’s standalone novelty | **RESOLVED** | L explicitly disclaims novelty. |
| H4’s qualitative precedent | **PARTIALLY** | The causal attribution is withdrawn, but a distinct contribution beyond established fallback principles remains unproved. |
| Precision about adjacent literature and estimands | **PARTIALLY** | The distinctions improve, but they do not establish the claimed benchmark’s unique scientific value. |

DISCERN §6.4 already compares uniform, PPI-style, active-testing and disagreement-gated auditing on identical streams with common confidence-sequence machinery. Its Table 3 reports audited-band median label counts of 2,098, 2,845, 1,948.5 and 70, respectively. Theorem 9 and Corollary 10 concern a specified pairing-blind class under their stated setting; they do not establish this repository’s exact growth ratios or finite-reserve nonstationary detection rankings. The remaining proposed delta is the reserve, temporal-allocation and intervention evaluation—not the basic label-economics finding. [DISCERN, primary PDF, §§5.3 and 6.4](https://arxiv.org/pdf/2609.17560v1)

**MAJOR 1 — “The literature does not report these together” is an insufficient novelty argument.**

A conjunction of previously studied components can support a benchmark contribution when it enables meaningful new comparisons. Merely assembling three findings does not establish that value.

Timans et al. already provide bounded-risk betting methods and comparative monitoring experiments. Waudby-Smith et al. explicitly address policy-value differences, adaptive logging and time-varying values. L’s elementary cancellation is consistent with these foundations; I did not establish that its exact sentence appears in a prior paper. [Timans et al., UAI 2025](https://proceedings.mlr.press/v286/timans25a.html), [Waudby-Smith et al., §§3.1–3.3](https://arxiv.org/html/2210.10768)

**Remedy and resolving evidence:** Produce a source-specific experimental-coverage matrix, followed by an implemented example showing what a researcher can learn through this contract that the closest existing evaluations cannot answer.

**MAJOR 2 — The qualitative revert/certify lesson has precedent.**

Conformal Policy Control uses a safe reference to regulate an untested policy; SPIBB retains baseline behaviour under uncertainty. These do not establish H4’s particular sequential ranking, but they prevent “fallback can beat an elaborate improvement procedure” from carrying much novelty alone. [Conformal Policy Control](https://arxiv.org/html/2603.02196), [SPIBB](https://proceedings.mlr.press/v97/laroche19a.html)

**Remedy and resolving evidence:** Establish a quantitative operating region involving reference deterioration, certification latency, resource costs and rollback. E3 must predict where recommendations change, under matched opportunities.

**MAJOR 3 — Different nulls require careful comparison, not automatic exclusion.**

Comparecast targets running-average score differentials. A procedure valid under a broader running-average null can also be valid under its eventwise-null subset. Consequently, a different null does not alone make such a baseline invalid for every comparison; its additional guarantee and potentially different sensitivity must be disclosed. Waudby-Smith et al. explicitly discuss this weak/strong-null relationship. [Comparecast](https://arxiv.org/html/2110.00115), [Waudby-Smith et al., §3.3](https://arxiv.org/html/2210.10768)

Ahmed et al. already demonstrate failures of label-free monitoring and adaptation under natural temporal shift. The paired-cost target distinguishes this project. Agreement blindness under correlated collapse is not, by itself, failure to measure relative decision harm: identical actions can have zero relative harm while both have high absolute risk. [Ahmed et al., 2026](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1928858/full)

**Resolving evidence:** Map each proposed comparator’s assumptions and score transformation explicitly; preserve absolute reference risk as a separate endpoint. Avoid claiming either universal prior coverage or an exhaustive “first benchmark” finding from the present search.

**Reviewer 3: Empirical ML reviewer**

**Artifact check:** H1–H4’s restated numerical values match the cited summary artifacts.

| Finding | Checked result |
|---|---|
| H1 | Growth diagnostic 7.201415, interval [6.884482, 7.551239]; 100/0 discordant outcomes; one-sided McNemar \(p=7.8886\times10^{-31}\). |
| H1 resources | Gated/uniform means: 118.11/114.11 labels and 177.29/170.87 dollars. Comparable spending, not exact matching. |
| H2 | Measured ratios 17.4677 / 20.6148 / 14.7336 / 7.2014 against predictions 18 / 18 / 15 / 7.5. |
| H3 synthetic | Fixed/paced detection 0.86/0.76 for the default mixture and 0.94/0.91 for GRAPA at \(r=.10\). |
| H3 EIA | Rechecking `injected.csv` gives identical fixed/full-feedback median delays in all ten detectable cells at each of \(r=.05,.10,.20\). |
| H4 | Fallback +664.643 / +685.911 / +447.964 versus pipeline +118.006 / +161.161 / 0; reversal −1,148.456 versus −143.758. |

Sources: [S3 decision](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/gated_monitor_compare/analysis/decision.json), [S3 summary](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/gated_monitor_compare/analysis/summary.csv), [EIA injection table](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/eia_real_data_validity/injected.csv), [integrated summary](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv).

| Round-1 item | Round-2 status | Assessment |
|---|---|---|
| F4: H4 isolates reference safety | **RESOLVED** | That attribution is withdrawn. The descriptive state-machine result survives. |
| H1 diagnostic versus deployed wealth | **PARTIALLY** | Renaming is correct; mixture-wealth reporting and synthetic uniform-HT isolation are future work. |
| Matching definitions | **PARTIALLY** | Levels help, but common uniforms do not imply identical observed feedback. |
| Synthetic/oracle and real-data scope | **PARTIALLY** | Limits are acknowledged; more authorities provide new paths within the same task. |
| S3 as development evidence | **RESOLVED** | Correctly labelled. |
| H4 outside the frozen 22-test family | **RESOLVED** | Correctly labelled post hoc. |
| Degenerate bootstrap interval | **RESOLVED** in the revised headline | Exact McNemar replaces the misleading effect-size interval. The old artifact remains identifiable. |
| H3 paired uncertainty | **NOT RESOLVED** | Deferred to E2. |
| Onset-informed scheduling comparator | **PARTIALLY** | Independent onset sweeps are planned; the existing negative screen remains conditional on its late-prior comparator. |
| Seed reuse and historical source drift | **NOT RESOLVED** | Registry and historical equivalence checks remain deliverables. |
| E1–E3 falsifiability | **PARTIALLY** | Fixed-window predictors and label-time identities repair earlier errors; crucial design choices remain open. |

**FATAL to the unrestricted empirical claim — “Fixed-rate gating detects no later” is stronger than the evidence.**

Detection rates and median delays in selected cells do not establish pathwise or general dominance under bursts. Early harmless disagreements can exhaust a fixed rule’s reserve before a later harmful burst, while pacing retains labels.

**Remedy and resolving evidence:** State a bounded empirical hypothesis for specified onset/burst classes. Include late harm after earlier disagreement bursts, recurrent regimes and reference deterioration. A failure of noninferiority must remain an admissible outcome.

There is also a straightforward numerical error in Claim B: “4–6× on three profiles.” The ratios are **5.63× and 4.26× on two profiles**. The recurring-regime comparison is +447.96 versus zero, so its ratio is undefined. This needs correction, rather than a new experiment.

**MAJOR 1 — E2 is improved but not frozen sufficiently to run confirmatory inference.**

Uniform HT with the same engine is the right addition. Fixed-window label counts avoid the earlier alarm-time endogeneity. However:

- No sample size, minimally relevant effect, anticipated paired discordance or numerical noninferiority margin is specified.
- TOST equivalence and one-sided noninferiority appear interchangeably; they answer different questions.
- Strict detection superiority can fail through ceiling effects even when gating saves resources.
- Counts alone cannot explain wealth without loss magnitudes, initial wealth and temporal placement.
- Fresh seeds from the same generator test replication within that family, rather than broad transfer.

**Remedy and resolving evidence:** Freeze the cells, hypotheses, margins, seed count, pairing unit and multiplicity family. Power McNemar using anticipated discordance. Register an acquisition-efficiency endpoint that remains meaningful at saturated detection. Evaluate mechanism predictions on held-out parameter cells, reporting prediction error against simpler alternatives.

**MAJOR 2 — E3 is not yet a feasible, identifying factorial.**

“Certify-and-promote at alarm” needs clarification. Fresh post-alarm evaluation cannot also produce immediate promotion at that alarm. Starting certification at the alarm and acting at the alarm are different interventions.

Monitoring coverage is a stated explanatory factor but is absent from the explicit factorial. Response type also changes the selected policy, its quality and its certification burden. A fitted decomposition assigning “50% of utility differences” is nonunique when interactions matter.

**Remedy and resolving evidence:**

- Separate trigger time, certification start/completion, deployment time and optional waiting.
- Explicitly vary monitoring coverage.
- Define rollback targets and give comparable rollback opportunities to fallback arms.
- Add the practical baseline **revert while certifying a candidate in the background**.
- Freeze policy quality, cost accounting, factorial contrasts and interaction analyses.
- Include every seed, including no-alarm and no-promotion outcomes.

The resolving artifact is an executable timeline specification plus a powered, fresh paired experiment. Conditioning comparisons only on successful alarms or promotions would introduce another selection problem.

The existing H4 asymmetries are real: candidate deployment starts at 2,400; monitoring ends at 1,600; fallback acts after its alarm; rollback is enabled for selected pipeline arms. [Implementation](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/src/shiftlab/dive/integrated_pipeline.py:696)

**MAJOR 3 — Revised E4 adds useful holdouts, with four remaining selection problems.**

1. **Coverage is value-blind, not automatically selection-free.** Demand availability is an outcome-observation property. Missingness may track extreme conditions or reporting disruption. A prespecified coverage filter is defensible, but changes the population to which findings apply.
2. **Demand coverage alone does not establish task eligibility.** The builder needs D, DF, NG and TI plus observed next-hour demand. Injection-band selection also requires at least 20 rehearsal procure events. Post-unlock exclusions for these failures would need predetermined rules. [Eligibility code](C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/scripts/audit_eia_2026_holdout_readiness.py:87)
3. **Random authority splitting does not remove shared-calendar dependence.** Common weather, regional relationships and already examined dates limit independence and temporal generalization. Query replicates are not additional independent deployments.
4. **No text reference does not prove no exposure.** The proposed search is useful evidence, but cannot establish absence of prior output inspection or unrecorded analysis.

**Remedy and resolving evidence:** Freeze the complete eligibility algorithm before inspecting evaluation values; record all exclusions and coverage failures; audit outputs as well as source/config references; register regional grouping and calendar-block inference or remain explicitly per-path descriptive. Distinguish uncertainty over query coins from uncertainty over authorities and future time.

Held-out authorities can be task-untouched retrospective evidence. They are **not a second task**, and the absence of new dates should remain explicit. A second task is not an automatic publication requirement, but this design cannot resolve the existing task-diversity objection.

The new PPI arm also requires real implementation and validation: WP4 expressly excluded it because a delayed-feedback proxy was outside that study’s scope.

**MAJOR 4 — Resource and oracle claims need their existing boundaries preserved.**

Evaluator-expected utility is legitimate synthetic evaluation. I found no basis in the inspected decision paths to allege oracle-driven action selection. Nevertheless, the reversal profile deliberately makes the incumbent optimal after event 2,400; this is a stress construction, not evidence about reversal prevalence.

H4 utility excludes label costs and general retraining costs. EIA’s weekly reference also consumes an outcome channel beyond the monitor’s artificial label budget.

**Remedy and resolving evidence:** Declare which resources are external services and which are charged. Report decision utility alongside labels, compute and interventions. Use a monetary utility conversion only with a justified scale. For reusable adapters, enforce oracle exclusion through the interface and perturbation checks.

**Reviewer 4: Sceptical programme-committee member**

**One-sentence takeaway:** Buy labels where paired losses can differ, and compare fallback and certification under the same monitoring, intervention and rollback opportunities.

That could change practitioner behaviour: include disagreement gating, test a simple fallback, and audit pipeline timing before attributing gains to sophisticated components. The present evidence does not yet support a general recommendation to prefer fixed pacing or certification.

| Round-1 item | Round-2 status | Assessment |
|---|---|---|
| F5: Claim A’s two-factor explanation and universal mechanism dismissal | **RESOLVED** | Claim A is withdrawn and the screened mechanisms are named. |
| Contribution mainly repairs repository practice | **PARTIALLY** | E2–E4 could demonstrate wider relevance; current evidence remains concentrated in project-specific designs. |
| Reusable D&B contribution missing | **PARTIALLY** | §6 specifies a credible deliverable, but does not deliver it. |

**FATAL weaknesses:** None to pursuing a bounded benchmark proposal. A submission claiming an already reusable benchmark or broadly established Claim B would be premature.

**MAJOR 1 — The contract must demonstrate scientific utility beyond documentation.**

Adapters, hashes and a seed registry improve reproducibility. A D&B contribution also needs evidence that the contract reveals consequential evaluation failures across methods and tasks.

**Remedy and resolving evidence:** Demonstrate an independently implemented additional method entering through the public interface, without bespoke evaluator access. Supply a small runnable reference suite, explicit failure handling, source-fidelity labels and reproducible outputs. Test whether its conclusions survive changes in engine, policy pair, onset and resource level.

The matching terminology needs repair here: same streams and query uniforms provide **coupled replay**, not identical feedback when acquisition rules differ.

**MAJOR 2 — The abandonment criteria mix scientific falsification with desired outcomes.**

- “Either answer is publishable” is not an evidential criterion.
- A 50% attribution threshold is undefined without a decomposition and treatment of interactions.
- Failure to confirm the expected fixed-over-paced ranking might strengthen a benchmark by exposing its limits.
- Two failed headline reproductions do not have the same consequence as one validity-critical failure.
- A competitor need not reproduce all three findings jointly to remove much of the proposal’s distinctive value.
- No concrete gate establishes that the contract is reusable or that E4 supplies informative evaluation.

**Remedy and resolving evidence:** Separate claim withdrawal, validity stops, benchmark-value assessment and compute decisions. Define practically meaningful effects and distinguish disconfirmation from inadequate power. Register circumstances under which the benchmark remains useful after its preferred hypotheses fail.

Claim B is therefore an improvement in scope, but currently reads as a work programme combining replication, a pacing hypothesis and state-machine diagnostics. It becomes a contribution through a useful delivered benchmark and discriminating results.

**Joint assessment**

| Venue | Updated score |
|---|---:|
| ICML main | **3/10** |
| NeurIPS Datasets & Benchmarks | **5/10** |

These assess the current proposal, not acceptance probabilities. Main-track strength remains limited by the absence of a new method, substantial theorem or sufficiently broad empirical insight. D&B prospects improve because the deliverable and local holdout plan are more concrete.

**Decision: BENCHMARK_PAPER.** Continue conditionally. NEW_METHOD remains unsupported; PIVOT or NO_GO would be premature before the corrected experiments test the surviving benchmark value.

The three most strengthening changes are:

1. **Complete the executable contract.** Finish validity/availability tables, resource accounting, seed registry, source snapshots and adapter boundaries. Correct matching terminology and Claim B’s overstatements.
2. **Freeze discriminating E2/E3 protocols.** Specify powered endpoints, feasible certification timelines, monitoring coverage, rollback parity and strong simple baselines. Permit negative findings.
3. **Lock and evaluate E4 rigorously.** Freeze full-feature eligibility and exclusions, account for authority/calendar dependence, and preserve the retrospective, imposed-cost interpretation.

**Another broad refinement round is unlikely to resolve significant evidential objections.** A short protocol-finalization pass can resolve the remaining mathematical definitions and design ambiguities. E1 must then establish reproducibility; E2 must test acquisition/pacing claims; E3 must identify intervention effects; E4 must test transfer to untouched authorities. No further wording can substitute for those results.

Verification limits: I independently checked the quoted CSV/JSON values and manifest hashes for S3, integrated metrics/summaries/contrasts and both integrated event logs. EIA result hashes, paired-stream hash, protocol and frozen code hashes also matched. Python execution was denied, so I did not recompute all Parquet-level statistics or run experiments. The historical Target-Scout equivalence check and S2 seed-report correction remain outstanding.
