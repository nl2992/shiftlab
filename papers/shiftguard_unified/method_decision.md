# Method-development decision

The cross-track decision gate is closed for this iteration. The dated synthesis
and ranked remaining gaps are recorded in
[`decision_gate_report_2026-10-26.md`](decision_gate_report_2026-10-26.md).
The decision is **NO-GO for a new algorithm in this iteration**. The selected
working path is a retrospective benchmark/failure-analysis manuscript, with
the remaining charter-aligned empirical, comparator, and manuscript gates
still to close. This does not mark the full research programme complete.

## Publication-scope decision — 2026-10-26

The research decision is **NO-GO** for a novel unified intervention algorithm, broad integrated-system superiority, or an end-to-end real-world claim. **PIVOT** to a retrospective benchmark/failure-analysis manuscript with separate Q1/Q2/Q3 estimands and task-specific real-data panels. This does not certify publication-level novelty or manuscript readiness; the finite closure criteria are in [`publication_scope_decision_v1.md`](publication_scope_decision_v1.md).

## Current decision-gate update — 2026-10-26

**Decision remains NO-GO for RIVE, ASC, or another new algorithm.** The
previously open disjoint integrated efficacy experiment is now complete and
independently verified. Two task-specific real-data final evaluations are now
available: the frozen EIA 2026 temporal retraining/resource replay and the
frozen Upworthy randomized package-choice holdout. The EIA outcomes reproduce
on a separate CUDA process; Upworthy's policy and uncertainty independently
reconstruct. These meet the minimum two-family count at component level but
do not evaluate the integrated pipeline or establish prospective availability.
The latest full current-worktree test suite passes (1,566 passed, 1 skipped in 629.95 seconds), with
Ruff lint/format, configured Mypy, and `git diff --check` also passing.
**Open Bandit update (2026-10-26):** a separate fixed-candidate position-1 MOPE replay processed 274,737 held-forward events. Item 41 had an IPW contrast of +0.001809, but the MOPE set became empty at event 866 and neither MOPE nor fixed-horizon Hoeffding promoted. Exact-solver validation and independent full-path/artifact reconstruction passed. This is retrospective exploratory evidence only; unresolved decision-unit, dependence, feature-time, and feedback-time contracts preclude an OBD validity claim. See `open_bandit_mope_development_execution_note_2026-10-26.md` and `mope_fast_optimizer_validation.md`.

The integrated synthetic result does not reveal a general system gain
that would justify another intervention design: the full stack helps over
continue in two monitor-aligned harm profiles, while simpler two-gate and
fixed-candidate arms achieve higher utility there. It misses native late
onset, suffers under post-promotion reversal, and the controller contributes
no measurable change in this simulator. Robust ASI's corrected original-task
reproduction is also complete. A WILDS PACE fixed-candidate adaptation now has
verified artifact and execution-source provenance. A source-pinned AnyRank reference-comparison
adaptation has a corrected six-stream replay and passed an independent
artifact verifier. The original v1 run is invalid because its cost builder
reversed false-positive and false-negative costs; v2 corrects this but reuses
the same six seed IDs. All methods made no promotions, which is inconclusive
at three streams per cell. An evaluator-only diagnostic found positive
mean-cost-gain candidates in one positive-signal context but no candidate
that strictly first-order stochastically dominated the incumbent. This is
evidence of an estimand mismatch for this small instance, not method efficacy
or FWER evidence. The star-shaped implementation remains an adaptation, not a
full all-pairs AnyRank reproduction. CPC and OCS/HCPI/CABAI still do not fit
the current datasets' common-label feedback contracts.

This is a method-development stop decision, not completion of the research
programme. The remaining work includes a finite fidelity audit of the
task-compatible Q1–Q3 comparators, verification that real-data experiments
satisfy the charter's execution requirements, and completion of the selected
manuscript scope. Current real-data experiments are meaningful development
studies, including CRSP monitor logic, and CriteoPrivateAds now provides a
day-block click-prediction study under explicit but assumed feedback delays.
This CriteoPrivateAds source is distinct from the acquired Criteo Attribution
conversion data; the latter's maturity audit remains negative for informative
within-stream monitoring under the 30-day convention. The PrivateAds result
does not establish verified label-release timing or campaign value. However,
no available source
supplies an untouched final holdout together with verified full event-time
availability and a defensible downstream intervention contract. Do not relabel
retrospective results as confirmation. If those requirements remain unmet
after the comparator audit and the completed CriteoPrivateAds development replay, the
defensible manuscript must state the missing external-confirmation condition
explicitly; do not claim the full unified framework has passed the objective.

**Criteo Uplift v2.1 eligibility correction (2026-10-26):** a primary-source follow-up confirms that non-uniform negative-label sampling was applied but provides no inclusion probabilities or complete sampling mechanism. The earlier “candidate for fixed-horizon policy evaluation” designation was too permissive. The checksum and AUC 0.5076 feature-only diagnostic do not establish a causal policy-value estimand after outcome-dependent sampling. Keep the source to descriptive prediction or replications of its published uplift-benchmark protocol unless Criteo clarifies the sampling design. No candidate-policy value was computed. See `criteo_uplift_eligibility_audit.md` and `../../data/reports/criteo_uplift_stream_audit.json`.

**Real-data feasibility update (2026-10-26):** a 412-impression public Criteo
Banner Filling Challenge sample has now been structurally audited, and the
publisher's helper code confirms its non-click subsampling correction and
one-slot baseline path. This does not change the real-data eligibility
decision: the sample is shuffled and too small, the 103M+ event archive is
about 35 GB compressed, and this machine currently has less than 1 GB of free
storage. Keep it as a candidate acquisition route only; no Criteo BLBF policy
evaluation or real-data confirmation has occurred. See
`criteo_blbf_readiness_audit.md` and
`../../data/reports/criteo_blbf_sample_manifest.json`.

**CriteoPrivateAds availability correction (2026-10-26):** a separate pinned
CriteoPrivateAds snapshot is present locally: 103,862,032 records across 30
day partitions, with publisher delay fields and feature-availability groups.
Both the structural metadata audit and a full aggregate-only scan passed for
all 288 files, 30 partitions and 103,862,032 records; a fresh SHA-256 pass
also matches all 288 publisher checksums. Stored delay values
support minute units (sale maximum 1,678 versus the stated 1,680-minute
window), but click/landed-click arrays contain negative offsets with no
publisher interpretation; sale-delay entries also do not align one-to-one
with the derived sale label. A two-day block maturity is therefore recorded
as a conservative replay assumption, with immediate and one-day sensitivities,
not as verified release timing. This supports a promising delayed-feedback
and cost-sensitive prediction development task under the publisher's
nonuniform-label weighting. It does not provide an untouched final holdout,
exact global display/feature-release times, logged bid propensities, or causal
auction outcomes; decision costs remain research-imposed. The host has less
than 1 GiB free, so the next run must stream the existing Parquet files without
creating a full copy. The data registry and task contract now record these
boundaries. See
`real_data_inventory.md`, `criteo_privateads_task_contract.md`, and
`../../data/reports/criteo_privatead_snapshot_audit.json` and
`../../data/reports/criteo_privatead_delay_audit.json`.

**Decision:** **NO-GO for new algorithm development at this gate.** Do not
begin RIVE, ASC, or another speculative method yet. **GO for a finite closure
pass on comparator fidelity, matched end-to-end development evidence, and
real-data task execution.** This is a decision about evidence readiness, not a
conclusion that existing methods are inferior or that the study is complete.

A targeted primary-source extension strengthens this no-go: Ren et al. (UAI
2024) already study decision-aligned worst-case shift in resource allocation,
and Wei (ICML 2021) optimizes online utility under action-dependent selective
labels. These do not implement ShiftLab's sequential paired-harm gate, but rule
out claiming novelty for downstream decision alignment or utility-aware label
acquisition by themselves. See
[`decision-costed shift prior-work audit`](decision_costed_shift_prior_work_audit_v1.md).

**Q2 comparator update (2026-10-26):** the official MOPE author code now has
a frozen 1,000-stream-per-cell IID calibration and power comparison, with an
independent verifier. The maximum simultaneous one-sided error bound across
four nonpositive promotion rates and three empty-confidence-set rates was
1.5036%, below the registered 5% gate. In the +0.12 cell MOPE promoted
99.1% versus 71.7% for fixed-N Hoeffding; paired power gain was 27.4 points
(95% seed-bootstrap interval [24.7, 30.2]), using 94.315 fewer labels on
average. This establishes a bounded advantage on that one synthetic DGP,
not real-data transfer or novelty. The 2022/2024 anytime-valid OPE paper also
has a source-level applicability audit: it permits context dependence only
under its history-exogeneity condition and targets the running average of
conditional policy values in its nonstationary section. OBD's decision unit,
slate dependence, feature timing and click-release time remain unresolved;
the OBD IPS/SNIPS/DM/DR checks are point-estimation development only. Thus
sequential off-policy certification alone remains an established comparator,
and OBD is not real-data confirmation. See `mope_obd_applicability_audit.md`,
`mope_gated_calibration_protocol_v1.md`, and the independently verified
MOPE output directory; do not invent a new gate algorithm from this result.

The older numbered rationale and finite-gate notes below preserve the
decision history. Where they say that integrated efficacy or Robust ASI
reproduction is still open, the current update at the top of this file
supersedes that status.

## CriteoPrivateAds development replay verified (2026-10-26)

The full single-seed CUDA comparison was repeated after adding output artifact
checksums. Both runs used the same seed and protocol; their summary metrics
agree within `7.2e-8` absolute difference, consistent with small GPU
reduction-order variation. The independent verifier checked four input
artifact hashes, all five output-file hashes, 35 unique daily model metrics,
90 unique paired cost contrasts, finite metric values, and 15,917,641 scored
rows per model. The final run took 403.6 seconds. Updated models modestly
improved the target-weighted metrics and imposed decision costs, while
unweighted Brier score worsened slightly. This is descriptive CriteoPrivateAds
click-prediction evidence under assumed block delays; it is distinct from
Criteo Attribution and does not change the NO-GO for new algorithm development
or close the independent real-data gate. See
`criteo_privateads_cost_development_v1.md` and the checksummed output directory
`outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026/`.

## Why this is the decision

1. The repository has substantial controlled synthetic evidence, including
   independent null calibrations, disjoint confirmations, resource caps,
   positive findings, and preserved negative findings.
2. The official Comparecast direct-score reproduction now has a verified
   300-seed-per-scenario confirmation, in addition to its 2,000-stream-per-
   control weak-null calibration. Its matched results show low residual-
   variance detection and later crossings on recurring regimes than DIVE in
   this simulator, but the methods' different nulls preclude a validity or
   superiority conclusion. Several relevant Q1–Q3 published methods still do
   not have verified matched reproductions.
3. Existing real-data results are retrospective or offline development
   studies. CRSP lacks verified point-in-time releases and observed trading
   costs; Criteo Attribution has no verified publisher release times or policy
   counterfactuals and only 3.31% of labels mature within the impression stream
   under the declared 30-day convention. No untouched real confirmation set
   is currently established.
4. A registered 2,000-seed CUDA closed-loop benchmark evaluates two-gate
   promotion/rollback against continue, unconditional promotion, and
   promotion-only baselines under explicit costs and hard label caps. It is
   meaningful integrated intervention evidence: in early reversal,
   rollback gained about +3.07 expected utility over promotion-only but
   remained about −81.50 below continue. It does not integrate the DIVE
   pre-monitor, Target-Scout candidate discovery, and cost-aware controller
   into one comparison. The separate component improvements still cannot
   establish the complete system's value. A source-level composition audit
   now specifies the fresh data blocks, alpha-family, and total-budget
   requirements; a first common-stream Q1 → Target-Scout → rollback pilot now
   exists, but it has no joint calibration or full comparator set. A
   follow-up seven-policy, two-seed CUDA run exercises controller-gated Q2
   and full-pipeline arms. Its added future-reversal profile crossed rollback
   once at event 2,538 after 21 labels; the candidate still incurred −320.10
   realized utility before fallback. The run shares seeds with the pilot and
   is smoke evidence only, with no calibration or efficacy claim. See
   `composition_compatibility_audit.md`,
   `integrated_controller_smoke_report.md`, and
   `integrated_reversal_development_report.md`.
5. The residual-variance weakness is real in registered synthetic work, but
   candidate tuning either failed to improve the established start-mixture
   or tested an estimand that did not match population-average harm. This does
   not yet justify an algorithm branch.
6. An independent paper-driven implementation of the highest-priority Q3
   retraining comparator, UPF (*When to Retrain a Machine Learning Model*,
   ICML 2025), passes focused tests and a CUDA smoke check. Its first matched
   finite-horizon cost-frontier development run is now complete on EIA CISO
   and ERCO (two delay assumptions, ten cost values, 2,240 period rows).
   Findings are mixed and exploratory; UPF does not dominate simple fixed
   baselines. This is a regression adaptation, not a paper-faithful
   classification reproduction, and it does not close the Q3 comparator gate
   because CARA/drift-detector comparisons and author-code validation remain
   absent. The audit also identifies an executable counterexample to
   Proposition 3.1's stated retraining-count bound. This prevents use of that
   bound as stated, but does not refute UPF's separate decision rule or
   empirical results. See `upf_primary_paper_audit.md` and
   `real_data_development_results.md`.
7. The ICML 2024 Active Statistical Inference mean estimator and uncertainty-
   weighted expected-budget allocation now have a fixed-horizon paired-cost
   adaptation. Across 30 development seeds, ASI and uniform used exactly the
   same expected labels per target batch (mean 526.15); ASI's MAE was 0.0087
   versus 0.0176 and mean asymptotic interval width 0.0488 versus 0.0801.
   The run and summary verifier reproduce all 120 rows and paired contrasts.
   This is a small synthetic adaptation, not original-task reproduction,
   sequential validity, hard-cap evidence, or independent confirmation. It
   reduces one allocation-baseline gap but does not change the NO-GO decision
   for new method development. See `asi_paired_cost_protocol.md` and
   `outputs/shiftguard_unified/sota_reproductions/asi_paired_cost_dev_v5/`.

## Finite next gate

1. **Q1 component comparison completed for the registered synthetic design.**
   Comparecast's formula audit, weak-null calibration, and 300-seed-per-
   scenario paired-cost confirmation are independently verified. Comparecast
   detected boundary-local harm in 295/300 streams, recurring harm in 212/300,
   harmful adaptation in 300/300, and residual-variance harm in 0/300; DIVE's
   corresponding counts were 300, 300, 300, and 17. There were no alarms in
   the two 300-stream controls. A single residual-variance stream had no
   evaluator-defined harm onset and is counted as no detection in the
   registered 300-run interval. These are matched descriptive outcomes, not
   a head-to-head validity test: Comparecast tests a weak running-average null
   and DIVE an eventwise conditional-mean null. PPRM's disjoint 300-seed
   confirmation detected predictive harm in 7/300 streams versus 19/300 for
   SRM, with 0/300 alarms in either of two controls. These findings establish
   low operating-point power in the tested settings and no superiority claim.
   See `comparecast_paired_cost_confirmation_results.md` and
   `pprm_paper_implementation_audit.md`.
2. **Matched synthetic development comparison complete:** on 18 positive
   cells × 60 paired seed blocks, Target-Scout exceeded fixed source-validation
   sample-split certification by +9.714 expected future net-gain units
   (97.5% bootstrap interval per contrast; Bonferroni familywise target ≥95%,
   [+6.008,+13.537]) and pooled-rank testing by
   +6.873 ([+3.857,+10.270]); all three methods shared candidate streams and a
   40% cap. Zero-signal cells had no promotions and no harmful promotion was
   observed. This is development evidence, not independent confirmation. The
   seed IDs overlap a separate Markov-context null block under a different DGP;
   the within-run matched contrasts remain valid, but cross-experiment
   independence is disclaimed in
   `target_scout_fixed_split_seed_overlap_correction.md`. The exact three-rule
   null calibration passed independently: 5/27,000 false promotions and a
   largest simultaneous one-sided exact upper limit of 0.85%. The gated
   300-seed-per-cell confirmation then passed its registered +1.0 practical
   margin against both fixed sample split (+8.7607; 97.5% interval
   [+7.2301,+10.3668]) and pooled rank (+6.6660; [+5.2745,+8.0539]). This is
   independent synthetic confirmation for that DGP, not real-data evidence or
   a novelty result. Both artifacts have independent verifiers.
3. **Integrated synthetic efficacy gate closed for the frozen configuration.**
   The frozen 100-seed-per-profile comparison completed on disjoint seeds and
   passed independent artifact and cap checks. Its primary results and
   limitations are in `integrated_efficacy_confirmation_results_v1.md`.
   The earlier 2,000-seed promotion/rollback run remains the component
   calibration benchmark. Neither establishes real-data transfer or general
   superiority; do not repeat the integrated synthetic run without a new
   falsifiable question.
4. **Two task-specific real-data evaluations now pass the family-count gate,**
   without closing integrated confirmation. EIA provides a frozen 2026
   event-time retraining/resource replay; its aggregate predictions, intervals,
   and reports now reproduce exactly in a separate CUDA process. Upworthy
   provides a frozen randomized headline-package choice evaluation on a
   project-relative holdout, with observed CTR and independent reconstruction.
   These are distinct task families and retain different information/utility
   units, so do not pool them. Neither exercises the complete monitor,
   candidate-certification, and intervention sequence. The aggregate Criteo
   audit resolves its current within-stream suitability negatively: only
   3.31% of outcomes mature during the impression stream under the assumed
   30-day convention. See `real_data_confirmation_gate_audit.md` for the exact
   remaining real-data claim boundary.
5. The ranked gap analysis now incorporates the integrated efficacy result.
   Complete the finite comparator-fidelity audit, then choose among a narrow
   benchmark paper, fresh external-data acquisition, or stop/pivot. A new
   method remains no-go unless that audit exposes a concrete, consequential
   gap with a task-valid evaluation contract.

No new algorithm may be selected merely because it improves on an internal
baseline. The strongest applicable published method and an end-to-end
resource comparison must be included in the decision evidence.

## Evidence links

- [`gap_analysis.md`](gap_analysis.md)
- [`evidence_inventory.md`](evidence_inventory.md)
- [`sota_fidelity_matrix.md`](sota_fidelity_matrix.md)
- [`real_data_inventory.md`](real_data_inventory.md)
- Integrated benchmark protocol: [design draft 0.3](integrated_benchmark_protocol.md), **not frozen**. The five-policy 300-row matched pilot has a missing execution-time protocol snapshot ([provenance audit](integrated_run_provenance_audit.md)); the later controller smoke and reversal runs capture protocol and source snapshots. None calibrates the composed error rates or satisfies confirmation requirements. See the [matched pilot](integrated_pipeline_matched_development_report.md), [controller smoke](integrated_controller_smoke_report.md), and [reversal stress report](integrated_reversal_development_report.md). The draft must pass error-family calibration and Q3 comparator audits before confirmation. Existing two-gate promotion/rollback protocol is
  [`../../docs/closed_loop_intervention_protocol.md`](../../docs/closed_loop_intervention_protocol.md).

**Calibration result (2026-10-26):** the fresh exact-rule Q2 null calibration passed after independent verification of all 27,000 stream rows, method-by-cell counts, paired query counts, hard caps, exact one-sided Clopper–Pearson bounds, frozen protocol hash, and captured runner source hash. Fixed split had 1/9,000 false promotions, Target-Scout 4/9,000, and pooled rank 0/9,000; the largest simultaneous upper bound was 0.85%. The no-positive-net-gain promotion and all-cap checks passed. This is finite evidence for the registered stationary null only. The gated independent 300-seed-per-cell confirmation also completed and passed its registered practical-margin criterion; see the result below. Artifacts: `outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1/`.

**Independent Q2 confirmation result (2026-10-26):** the frozen 300-seed-per-cell run completed on CUDA on the disjoint 99,010,000–99,010,299 block. Across 18 positive-signal cells, Target-Scout's equal-cell paired expected future net gain was +8.7607 over fixed source-validation sample split (97.5% bootstrap interval [+7.2301, +10.3668]) and +6.6660 over pooled rank ([+5.2745, +8.0539]); both lower bounds exceed the registered +1.0 practical margin. All three methods used the same mean of 631.79 queried labels per stream; promotions were 48/5,400, 101/5,400, and 296/5,400 for fixed split, pooled rank, and Target-Scout respectively, with zero harmful promotions and no cap violations. Independent verification reproduced the 16,200-row data set and both bootstrap intervals. This confirms an advantage only for this synthetic DGP and workflow; no real-data or novelty claim follows. Full report and checksummed metrics are in `outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_confirmation_v1/`.

**Independent Q1 paired-cost confirmation result (2026-10-26):** all 3,600 method-stream rows across six scenarios passed independent artifact, source, protocol, seed-block, horizon, finite-e-value, and exact-interval checks. Comparecast/DIVE post-onset detections were 295/300 vs 300/300 for boundary-local harm, 212/300 vs 300/300 for recurring regimes, 300/300 vs 300/300 for harmful adaptation, and 0/300 vs 17/300 for residual variance. A residual-variance path lacked a realized evaluator-defined harm onset and is counted as a non-detection in the registered all-300 endpoint; it is 0/299 vs 17/299 among the onset-eligible streams, descriptively. No pre-onset or control alarms occurred. This does not establish cross-method superiority because the null hypotheses differ. See `comparecast_paired_cost_confirmation_results.md` and `outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1/`.

**Q1 PPE update (2026-10-26):** the published Prediction-Powered E-Value factor correction was audited and implemented as a fixed-stake paired-cost adaptation. Its frozen 16-cell, 1,000-seed-per-cell CUDA null calibration had zero alarms in each cell and a maximum simultaneous one-sided exact upper limit of 0.5752%. On the disjoint 300-seed-per-alternative block, PPE's detection rate across the registered profile/query-rate grid was 67.71%, versus 55.21% for fixed-mixture; paired seed-cluster gain +12.50 points (95% interval [+11.17,+13.83]). The advantage concentrated at q=.20 and was absent at q=.40. Deterministic replay matched all 6,400 PPE stream outputs; the full suite subsequently passed 1,481 tests with one skip. This strengthens the Q1 synthetic comparator evidence but does not change the **NO-GO** for speculative RIVE/ASC development: the PPE transfer is not a full paper reproduction, the real-data contract is unresolved, and the integrated system still lacks a calibrated matched end-to-end comparison. Next gate: complete the ranked cross-track comparison and real-data feasibility decision; then choose benchmark scope, targeted development only if a measured gap remains, or stop/pivot. See `ppe_paper_implementation_audit.md`, `ppe_paired_cost_confirmation_results_v1.md`, and the verified output under `outputs/shiftguard_unified/sota_reproductions/ppe_paired_cost_confirmation_v1/`.

## Hillstrom real-intervention development update (2026-10-26)

A local-only copy of the official MineThatData randomized email challenge has been evaluated as a fixed-horizon intervention task. The neural T-learner was statistically indistinguishable from randomized allocation at the registered imposed cost, and Ridge/history rules also had wide paired intervals spanning zero. This establishes that the current real-data stack can execute a source-grounded randomized-allocation evaluation, but provides no evidence that a learned policy improves net value. The test split is exposed. The result does not close the independent real-data confirmation gate, provide sequential monitoring evidence, or justify a new algorithm. See `hillstrom_email_policy_development_protocol.md` and `real_data_development_results.md`.

## Project GATE real-data feasibility update (2026-10-26)

The official public-use archives were acquired and aggregate-audited. The final DOL report explains the 4,198-to-4,197 change as removal of one nonrandom assignment. It also excludes 120 applicants in mixed-treatment business partnerships and adjusts weights for partnership membership and survey response; those IDs and weights are absent from the public schema. Wave-3 current self-employment is a candidate fixed-horizon outcome, and the report gives an invoice-based average cost of $1,321 per program-group member. Wave-3 response is differential and 58.4% overall; worst-case missing-outcome bounds cross zero widely, interview timing varies, and label-release time is unknown. This adds a real randomized-offer development candidate, but it does not close the sequential monitoring, no-interference population-policy, or independent confirmation gaps and does not justify RIVE/ASC. Keep the existing **NO-GO** decision. See `project_gate_data_candidate_audit.md` and `project_gate_source_audit.json`.



**Timans Q1 comparator update (2026-10-26):** the standalone paired-cost monitor has now been directly compared with Timans et al.'s UAI 2025 unknown-shift bounded-risk e-process. The published eventwise null maps exactly to the ShiftLab score after an affine bounded transform. The matched CUDA experiment and independent artifact verification found no adjusted detection advantage for the fixed-stake mixture. This further supports **NO-GO** for a new standalone Q1 betting algorithm. The remaining possible contribution is the safe, resource-aware transition from harm evidence to candidate intervention; sequential policy selection and promotion baselines remain to be audited. The real-data and manuscript completion gates remain open. See the [matched results](../../outputs/shiftguard_unified/sota_reproductions/timans_unknown_shift_paired_cost_v1/report.md) and [`novelty_audit.md`](novelty_audit.md).

**Matched Q2 gate comparison (2026-10-26):** the pinned MOPE deployment gate, finite-class OPI, and fixed-horizon controls now have a frozen, 1,300-stream shared-data comparison with independent artifact verification. MOPE had 11/1,000 null promotions and three empty confidence paths, and promoted 279/300 +0.15 alternatives (93.0%) versus 92/300 for the fixed-horizon gate; it used 114.04 labels on average. OPI and fixed-horizon class selection found no singleton within 200 events. Because the gate and policy selectors have different targets, this does not establish a general ranking. It reinforces the existing **NO-GO** for inventing a new gate merely for novelty: MOPE already addresses a fixed candidate-vs-incumbent transition under its logged-bandit assumptions. A resource-aware extension or real-data transfer remains unproven. See [`matched results`](opi_mope_matched_results_v1.md), the [run report](../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/report.md), and the [`empty-path audit`](../../outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1/mope_empty_confidence_set_audit.json).
