# Ranked evidence gaps at the ShiftGuard decision gate

The current gate adjudication is summarized in
[`decision_gate_report_2026-10-26.md`](decision_gate_report_2026-10-26.md).
Its conclusion is to stop new-method development for this iteration while
keeping the independent real-data and manuscript gates open.

**Status:** working-tree synthesis, 2026-10-26. This is a decision-gate
analysis, not a claim that Phase B or C is complete. It uses the current
evidence inventory, real-data availability audit, SOTA fidelity matrix,
Comparecast/PPRM/PPE studies, the matched integrated benchmark, and the WILDS
fixed-split development run.
Historical result manifests take precedence over current source when
identifying experiment provenance.

**Latest decision-gate update (2026-10-26):** the frozen integrated efficacy
confirmation is complete and independently verified (100 disjoint seeds per
profile, eight profiles, nine methods, 7,200 metric rows, 22 registered
contrasts, and the 640-label cap). The reserved EIA 2026 temporal replay has
also completed on CUDA with verified source/protocol/output hashes. It found
lower RMSE for every adaptive schedule than frozen Ridge on CISO and ERCO at
all three assumed feedback delays; descriptive paired 168-hour block intervals
were below zero across 42 blocks per authority. EIA remains prediction-risk
and refit-resource evidence only: publication timing is unknown, costs are not
grounded in downstream utility, and the authorities are not independent
replications. The latest full test suite passes (1,566 passed, 1 skipped in
629.95 seconds). Ruff reports all checks passed, formatting reports 820 files
already formatted, and configured Mypy reports no issues in two source files.
The 1,566-test run completed on 2026-10-26. These updates
close the EIA replay and current software-verification items, not Phase F.
The integrated result closes its synthetic efficacy gate only. The full
pipeline improves on continuing when harmful adaptation overlaps the Q1
monitor window, but it loses to the simpler two-gate and fixed-candidate
arms in those aligned-harm profiles; it misses native late-onset harm,
performs poorly under post-promotion reversal, and the controller ablation is
identical. Therefore the integrated result does not support a general system
advantage or a new intervention algorithm. The corrected Robust ASI original
task is also independently verified; it closes one fixed-horizon Q3
reproduction gap, not a sequential-validity or independent-dataset gap. The
current checks cover source/tests; they do not satisfy the real-data
confirmation conditions.

## Ranked gaps

| Rank | Gap | Evidence and consequence | What closes the gap | Priority |
|---|---|---|---|---|
| 1 | **No real-data source yet supports an end-to-end online decision-harm confirmation.** | The frozen EIA 2026 temporal replay compares predictive risk and retraining resources under assumed delays; a separate CUDA re-execution reproduced its aggregate metrics, intervals, and report. Upworthy's protocol-frozen project-relative holdout evaluates an actual headline-package choice against uniform choice by observed CTR, with a separate full reconstruction. These distinct task families meet the Phase F minimum family count at the task/component level. However, EIA has unknown source-release timing and no electricity-system utility; Upworthy has no individual feedback clock, revenue, or deployment costs. Neither executes the complete monitor–candidate-certification–intervention stack. CRSP's test period is exposed; WILDS and Gas Sensor are offline domain tasks; Criteo's 30-day convention leaves only 3.31% labels mature by the last event; OBD lacks timing/support evidence; Hillstrom's evaluation split is exposed with imposed email costs; Project GATE has differential response and unreconstructable partnership interference. | Treat the two completed tasks as bounded component-level external evidence. To claim integrated online decision-harm confirmation, obtain a source with event/feature/label availability, action outcome or defensible paired loss, and resource costs, then freeze a matched protocol before its final evaluation. If unavailable, report the integrated result as synthetic-only and state the real-data limits precisely. | **Critical for broad claims.** Two-family task count is met; integrated/prospective decision-harm evidence is not. |
| 2 | **The complete integrated stack has no demonstrated general advantage over simpler intervention baselines.** | The frozen 100-seed-per-profile CUDA efficacy run compared nine methods across eight profiles. Full pipeline improved over continue by +118.01 under boundary-local harm and +161.16 under monitor-aligned adaptation, but was worse than two-gate by 68.53 and 40.10 units, and worse than fixed-candidate certification by 129.51 and 82.32 in those same profiles. Full pipeline utility was −143.76 under post-promotion reversal; native late-onset harm was missed by the Q1-gated methods; rollback did not recover accumulated loss. Controller and non-controller arms matched exactly. All 22 frozen contrasts and artifact checks passed, but the one-sided family tests were designed for full-pipeline gains and do not establish the reverse superiority direction. | Do not add a new controller or intervention algorithm. Complete the finite source-based comparator audit, decide whether a narrower monitor/certification benchmark has a distinct contribution, and preserve the matched result as the integrated-system conclusion for this frozen design. | **Synthetic efficacy gate closed; general system advantage unsupported.** |
| 3 | **Published Q1–Q3 baselines are not yet reproduced broadly enough to establish a credible frontier.** | Q1 now has source-audited Comparecast with weak-null calibration and fresh paired-cost confirmation, plus independent synthetic PPRM and PPE comparisons; their nulls and score targets remain distinct. Q2 has independent Target-Scout confirmation against fixed split and pooled rank on one synthetic family, offline sample-split selection on WILDS and Gas, and a six-stream AnyRank candidate-versus-incumbent pilot with no promotions in either cell. The AnyRank pilot is inconclusive and does not provide full-ranking reproduction, null calibration, or a powered efficacy comparison. The OBD fixed-candidate replay provides one exploratory logged-bandit gate outcome (MOPE empty set at event 866, no promotion); it is not a validity-bearing result or independent confirmation. No matched real-data Target-Scout or faithful OCS/HCPI comparison exists. Project GATE is now an acquired randomized offer dataset with a documented 0.5 assignment probability, candidate outcome and reported average program cost, but differential response and 120 unreconstructable mixed-arm partnership exclusions prevent a faithful no-interference population policy evaluation from the public files. Q3 has a corrected Robust ASI original-task reproduction, fixed-horizon ASI adaptation, and task-specific UPF/RCCDA/CARA/ADWIN/DDM EIA frontiers; these do not reproduce the published tasks or form a comparable end-to-end frontier. Conformal Policy Selection (CPS, arXiv:2610.22930) is a strong selective-deployment comparator, but targets selected-unit outcome-threshold FDR under behavior/target treatment shift, not temporal population-average paired-cost harm; its EHR evaluation uses semi-synthetic counterfactual outcomes. | Complete a calibrated, adequately powered AnyRank comparison only if it can answer the candidate-promotion question beyond the stricter pilot; retain the finite applicability exclusions for OCS/HCPI/CPS and other incompatible methods. If Project GATE is used as a development task, preregister how differential response and partnership interference are handled; do not count its exposed aggregate audit as an independent final evaluation. | **Synthetic component evidence is substantial; Q1–Q3 frontier and compatible real intervention comparator remain open.** |
| 4 | **Monitoring power remains weak for late-onset and residual-variance harm.** | Existing fixed-start and query-allocation studies show scenario-specific gains, but absolute late-onset detection is low. Residual-variance PVA tuning failed to improve on fixed betting; the context-subgroup apparent gain was rejected because it tested a stronger contextwise null already false in population-null controls. | Treat this as a measured weakness, not a mandate for a new method. First compare the strongest compatible published monitors at matched label budgets and perform one task-valid real-data development replay. Any later proposal needs a separate proof and disjoint calibration/confirmation. | **High, contingent on gaps 1–3.** |
| 5 | **Target-Scout's advantage is supported on registered synthetic families, but its real-data and broader-method frontier remains incomplete.** | The 600-seed independent confirmation beat pooled rank and context-volume baselines on its registered IID family. The matched fixed-split development comparison found +9.714 expected future net gain over source-validation sample split and +6.873 over pooled rank, with seed-overlap caveat documented. The fresh exact-rule null calibration passed (5/27,000 false promotions; largest simultaneous upper bound 0.85%). Its gated independent confirmation then passed the +1.0 practical-margin criterion: +8.7607 over fixed split ([+7.2301,+10.3668]) and +6.6660 over pooled rank ([+5.2745,+8.0539]). This confirms only the registered synthetic DGP/workflow. Context-drift results remain mixed; Upworthy evaluates a different text-only package selector and is not a real-data Target-Scout comparison; no matched real Target-Scout, full AnyRank, or OCS frontier exists. | Compare a task-compatible sequential ranking/OPE method or document its feedback mismatch; keep the new two-family external evidence task-specific rather than pooling it with Target-Scout. | **Synthetic confirmation met; real-data Target-Scout and broader frontier open.** |
| 6 | **The external package emits masked-log warnings; verify they do not change returned evidence.** | At pinned commit `52748c86e0429a9612dc79892c3be6156a524132`, the source matches the paper's positive-z mixture and documented nonpositive-z upper-bound branch. Across the frozen audit grid it produced finite, exactly repeatable outputs matching the safe formula; positive-z values matched independent quadrature within 5.5e-13 and nonpositive-z bounds exceeded exact integrals by at least 0.101. The warnings stem from masked calls without `out`; their masked entries are discarded by the outer branch. A fresh 300-seed-per-scenario alternative confirmation passed independent verification, with the warnings captured in every Comparecast stream and finite e-values throughout. | Preserve the source-hashed audit, regression tests, calibration, and confirmation. Keep the two methods' different nulls distinct; do not treat the matched power summary as cross-method validity evidence. | **Resolved for numerical correctness, registered weak-null calibration, and the registered synthetic alternative confirmation.** |

## Evidence balance

The strongest current positives are registered synthetic results for
evidence-directed PPI, fixed-start monitoring, Target-Scout, PPE at a lower
query rate, and context-stratified rollback, plus a registered 2,000-seed closed-loop
promotion/rollback benchmark and the disjoint integrated efficacy comparison.
The integrated comparison does not show uniform added value: its benefit is
profile-specific and simpler two-gate/fixed-candidate arms lead on the two
monitor-aligned harmful profiles. PPRM's independent confirmation is a further
valid method-targeted result but shows only 7/300 predictive-harm detections,
below SRM's 19/300; it provides no evidence of PPRM superiority. The strongest negatives are low absolute
late-onset power, failure of PVA tuning to beat the established start-mixture,
context-null misalignment, weak transfer of synthetic monitors to the
descriptive CRSP path, and the absence of an integrated end-to-end comparison.
PPE's improvement over fixed-mixture is confined to q=.20 in the registered
comparison; at q=.40 it slightly trails and must not be described as a
uniformly stronger monitor.
The closed-loop benchmark is a real integrated synthetic intervention result,
but it tests two sequential gates and simple baselines rather than the full
DIVE–Target-Scout–controller stack. These outcomes concern different DGPs and
estimands and must not be pooled.

## Decision criterion

Do not start RIVE, ASC, or a replacement method until ranks 1–3 have either
been closed for a defensible narrow scope or explicitly shown infeasible under
available data and feedback. A narrower scope must be declared as such, with
the excluded questions and claims removed. A synthetic detection gap alone is
not enough to justify optimization when the strongest published comparator,
the real task contract, or the end-to-end value remains unresolved.

## Source artifacts

- [`evidence_inventory.md`](evidence_inventory.md)
- [`sota_fidelity_matrix.md`](sota_fidelity_matrix.md)
- [`real_data_inventory.md`](real_data_inventory.md)
- [`real_data_task_contracts.md`](real_data_task_contracts.md)
- [`../outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_dev_v1/manifest.json`](../../outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_dev_v1/manifest.json)
- [`../docs/next_phase_plan.md`](../../docs/next_phase_plan.md)

## Q3 EIA update — CARA and drift-trigger baselines (2026-10-26)

The immediate EIA resource-frontier omission is now addressed with explicit
task-specific adaptations. CARA's threshold, cumulative-threshold and periodic
rules were tuned only on offline periods 1–5 and scored on periods 7–14; the
best CARA policy improved on the prior best non-oracle method in 16/40
authority-delay-cost cells, tied in 5, and lost in 19. River ADWIN and DDM
adaptations were added on the same frontier; the best detector arm improved
the other non-oracle policies in 3/40 cells, tied in 6, and lost in 31. See
[`real_data_development_results.md`](real_data_development_results.md) and the
versioned CARA/drift artifacts.

This does not convert those task adaptations into published-task
reproductions: CARA's query-proxy/regression loss, DDM's regression-to-binary
mapping, and the detector library differ from the original benchmark setup.
Rank 3 remains open for broad Q1–Q3 fidelity, despite the completed Robust ASI original-task reproduction. The integrated synthetic efficacy gate is now closed for the frozen configuration, but the system shows profile-specific value and no overall advantage over simpler arms. The latest source audit adds Conformal Policy Selection (CPS) as a scope-critical selective-deployment comparator; its individual-unit FDR estimand and treatment-policy assumptions do not map directly to the current common-label paired-cost tasks. Real-data confirmation is still unavailable. Do not start a new optimization branch from these results.

## Q3 update — RCCDA and oracle-aligned EIA frontier (2026-10-26)

The paper-rule RCCDA adaptation now runs on the same EIA event-time frontier as
UPF, with mature-feedback cutoffs independently recomputed. It made three
updates for CISO and four for ERCO under both 0- and 168-hour assumed delays,
but attained the lowest non-oracle cost on only 6 of 40 authority-delay-cost
points. The corrected exact oracle is a lower bound on all 40 points. This
adds a task-specific resource baseline and does not close the Q3 publication
fidelity gate: UPF and RCCDA are adapted to an EIA regression task, CARA and
applicable drift-trigger baselines are not yet included in this shared
frontier, and neither real series has independent replication or grounded
deployment costs. See [`real_data_development_results.md`](real_data_development_results.md)
and the `upf_eia_frontier_v2` / `rccda_eia_frontier_v2` manifests.

**Update — exact-rule null calibration passed (2026-10-26):** 1,000 seeds per each of nine stationary null cells, three methods, 27,000 per-method stream records. False promotions: fixed split 1/9,000; Target-Scout 4/9,000; pooled rank 0/9,000. All 27 familywise-adjusted exact upper limits were below 0.05 (maximum 0.0085); no cap violations, query mismatches, or positive-net-gain promotions occurred. An independent verifier checked every metric artifact, the captured execution-time source snapshot, and protocol hash. This supports calibration only under the stated stationary null. The disjoint confirmation and its verification are complete; see the Q2 confirmation update below. Detailed calibration artifacts: `outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1/`.

**Update — Q2 independent confirmation passed (2026-10-26):** on 300 disjoint paired seeds in each of the 18 positive-signal cells, Target-Scout exceeded fixed sample split by +8.7607 net-gain units (97.5% interval [+7.2301,+10.3668]) and pooled rank by +6.6660 ([+5.2745,+8.0539]); both clear the registered +1 margin. All methods averaged 631.79 queried labels per stream; there were no cap violations or harmful promotions. An independent verifier recomputed both intervals from 16,200 stream records. This closes the synthetic confirmation gap for this exact comparison. Real-data candidate-policy evidence, a full sequential-ranking/OPE frontier, and the integrated Q3 stack remain open. See `outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_confirmation_v1/`.

**Update — Q1 direct paired-cost confirmation passed (2026-10-26):** the frozen Comparecast run contains 3,600 rows (300 seeds × six scenarios × two methods), and the independent verifier passed protocol, source, calibration, seed-block, artifact, interval, and onset-eligibility checks. Comparecast detected 295/300 boundary-local, 212/300 recurring, 300/300 harmful-adaptation, and 0/300 residual-variance runs; DIVE detected 300, 300, 300, and 17. A single residual-variance seed did not realize evaluator-defined material harm and is counted as no detection in the registered all-300 endpoint; the conditional descriptive comparison among 299 onset-eligible runs is 0/299 versus 17/299. No alarms occurred in either control or before onset. Because the nulls differ, this result is descriptive and does not establish relative validity or superiority. Full interpretation: `comparecast_paired_cost_confirmation_results.md`; checksummed outputs: `outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1/`.

## Integrated Q1–Q3 null-calibration update (2026-10-26)

The integrated state machine now has a frozen v1 conditional-null calibration and an independently verified CUDA run. Across four registered endpoints, all error counts were 0/1,000 eligible streams: stationary Q1, benign nuisance-shift Q1, Q2 false promotion after Q1 trigger and actual candidate selection, and Q3 false rollback after evaluator-only independent population-null eligibility. The simultaneous one-sided exact upper bound was 0.4372% per endpoint; the observed maximum label use was 640. The verifier replayed all 1,266 Q3 attempts and reproduced policy decisions, resource counts, and oracle gain bounds. This closes only the registered synthetic calibration gate. It does not establish integrated efficacy, cover unregistered/dependent/delayed/performative nulls, or resolve the full published-baseline and real-data gaps. The complete report and artifacts are in `integrated_results.md` and `outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v1/`.

**Historical status superseded by the 2026-10-26 efficacy update above:** the disjoint integrated efficacy confirmation has now run and passed independent verification. The remaining integrated-system gap is a lack of general advantage over simpler arms and no compatible real-data intervention confirmation. Fixed-candidate and Target-Scout synthetic comparisons are both complete for their registered designs; neither establishes real-data transfer. The applicable published-baseline and final holdout gaps remain open.

## Fixed-candidate certification calibration update (2026-10-26)

The Q2 no-scout arm now has a separate frozen protocol and passed a CUDA null-calibration run: 0 false promotions in 1,000 eligible streams (1,030 attempts), one-sided 95% exact upper bound 0.2991% versus alpha 0.015, and maximum 480/640 queried labels. An independent verifier replayed all attempted seeds and recomputed pointwise conditional gains from the candidate and incumbent actions. This removes the fixed-arm implementation-calibration gap, but leaves its utility relative to Target-Scout unknown. The next integrated experiment must compare fixed selection, scout selection, Q1 gating, controller gating, simple no-adaptation/always-adapt controls, and matched resource costs on fresh development streams before any disjoint confirmation.

The nine-arm, eight-profile CUDA smoke comparison is now available (144 rows, two seeds/profile, maximum 632/640 labels). Its small sample suggests Q1 fallback may dominate promotion in the imposed harm scenarios and shows negative utility under post-promotion reversal even with rollback. These are design-specific descriptive observations only. A current-source rerun of the four-cell null calibration passes with all 1,266 Q3 attempts independently replayed. See `integrated_fixed_certification_development_report.md` and the `integrated_null_calibration_v2/` and `pipeline_fixed_certification_dev_v1/` outputs. A larger matched development analysis with appropriate frozen estimands and baseline fidelity remains necessary before efficacy confirmation.

The frozen 30-seed-per-profile development comparison now sharpens those observations. Fixed candidate choice exceeded scout selection in the two aligned harm profiles, Q1 gating missed the post-window onset by design, rollback remained too late to recover reversal losses, and the current controller made no action differences across the eight profiles. The Q1 fallback led the aligned harm profiles under the imposed reference-policy cost law. These are exploratory synthetic results with unadjusted paired intervals. They argue against claiming value from the current integrated controller and motivate either a narrower fixed-candidate/monitoring study or better fallback/cost contracts; they do not justify RIVE/ASC. Strong published baselines, paper-faithful comparisons, and independent real-data evaluation remain the decisive open gates. See `integrated_matched_development_results_v1.md` and its 30-seed output manifest.

**WILDS PACE comparator update (2026-10-26):** an article-disjoint, offline single-candidate PACE adaptation is now compared with fixed-N exact McNemar. PACE retained the incumbent after 3,491 certification articles; fixed-N promoted (`p=0.02016`). The exploratory test outcome favors the fixed-N decision but is exposed to prior test use and does not establish online utility, active-label savings, or run-level error control. This narrows one PACE implementation gap; it does not close the real-data confirmation or Q2 frontier gaps. Protocol and integrity-checked artifacts: `papers/shiftguard_unified/wilds_pace_gate_protocol_v1.md` and `outputs/shiftguard_unified/real_data_development/wilds_pace_gate_v1/`.

**Correction and AnyRank Q2 update (2026-10-26):** the v1 six-stream AnyRank results are invalid because the implementation reversed false-positive and false-negative costs; its artifact verifier did not test that semantic mapping. The corrected v2 replay fixes the mapping, asserts it at runtime, reuses the same six seeds, and independently verifies all 24 rows and source/protocol/output hashes. All four methods made zero promotions, which remains inconclusive. The evaluator-only oracle diagnostic shows that one positive-signal context had 12 candidates with positive finite-design mean gain (mean best gain +35.775), but no candidate strictly first-order stochastically dominated the incumbent on the registered 11-threshold grid. The strict AnyRank distribution-ordering target therefore does not align with the mean-cost promotion estimand in this small instance. This is a diagnostic, not evidence of efficacy or calibrated FWER. The star-shaped replay is not full all-pairs AnyRank; the Q2 frontier and real-data confirmation decision remain open. See `anyrank_adaptation_protocol_v2.md` and `outputs/shiftguard_unified/sota_reproductions/anyrank_shiftguard_pilot_v2/` plus `anyrank_pilot_oracle_diagnostic_v2/`.

**Finite Q2/Q3 comparator-source audit (2026-10-26):** official AnyRank author code and its dependency licenses have been verified. AnyRank is task-compatible as a bounded common-score synthetic comparator, while its active per-policy trial allocation cannot claim label savings when one shared label scores every candidate. OCS, HCPI, CPC, CPS and CABAI remain scope comparators only for the current datasets because their treatment/behavior propensities, action-dependent outcomes, safe-reference samples, or arm-specific testing costs are unavailable. CPC's public author repository is now recorded; earlier notes saying none was located are corrected. UPF/RCCDA/CARA/ADWIN/DDM EIA comparisons exist as task-specific adaptations, not original-task reproductions. See `comparator_applicability_audit_v1.md`.

**OBD logged-policy-value development update (2026-10-26):** the complete
official BTS/all archive was streamed through IPS/SNIPS and a cross-fitted
item-position DM/DR adaptation for the uniform Random policy, with the
concurrent Random/all value as reference. DM is 0.14% from that reference,
IPS 1.03%, DR 3.90%, and SNIPS 4.75%; the pinned official DR formula matched
on a deterministic check. However, post-hoc date-by-position IPS diagnostics
show mean absolute error 0.000553 across 21 cells (maximum 0.001520); positions
2 and 3 retain about 0.115% aggregate importance-weight ESS. No interval or
candidate-promotion test was run. The archive's 12,357,200 BTS rows remain
189,116 above the paper's all-campaign table; a version difference is
plausible but not established by the official release's aggregate
description. This supplies real logged-bandit OPE development evidence, not
real-data confirmation. See [`OBD OPE results`](open_bandit_ope_development_results.md)
and the checksummed v2 IPS/SNIPS and cross-fitted DM/DR manifests.

**CriteoPrivateAds cost-sensitive development update (2026-10-26):** a full
single-seed CUDA run completed on the pre-existing snapshot: 72,004,608
training labels, 15,917,641 scored rows per model, and 400.6 seconds elapsed.
Updated candidates had modestly lower target-weighted log loss and lower
imposed decision costs than the frozen incumbent; intercept recalibration
alone changed costs very little. Unweighted Brier score moved slightly in
the opposite direction. This comparison uses five adjacent daily blocks,
assumed label-maturity delays, imposed costs and prevalence weighting, and no
uncertainty interval. It is retrospective development evidence only, not
independent confirmation or evidence of causal/operational utility. See
[`Criteo development report`](criteo_privateads_cost_development_v1.md) and
`outputs/shiftguard_unified/real_data_development/criteo_privateads_cost_baseline_v2_20261026/`.

**MOPE Q2 comparator calibration completed (2026-10-26):** the pinned 2021
gated-deployment reference method was compared with a fixed-N Hoeffding gate
on 1,000 independently generated streams in each of three bounded IID cells.
The simultaneous upper bound across four null/strict-control promotion rates
and three empty-confidence-set rates was 1.5036%, passing the frozen 5% gate.
MOPE achieved 99.1% promotion in the +0.12 cell versus 71.7% for Hoeffding,
with a paired +27.4-point power difference (95% interval [+24.7,+30.2]) and
94.315 fewer labels on average. An independent verifier checked all 6,000
method rows, source and output hashes, regenerated CUDA inputs, exact rates,
and bootstrap contrasts. This closes only the registered MOPE IID synthetic
comparator sub-gate; it does not close the broad Q2/Q3 frontier, validate OBD,
or support a new gated-certification novelty claim. See
[`MOPE applicability and results`](mope_obd_applicability_audit.md), the
[`frozen protocol`](mope_gated_calibration_protocol_v1.md), and the
[`independent verification`](../../outputs/shiftguard_unified/sota_reproductions/mope_gated_calibration_v1/independent_verification.json).

**Hillstrom downstream-intervention update (2026-10-26):** a real randomized three-arm email experiment now supports one fixed-horizon downstream allocation development task. The current CUDA v3 T-learner did not beat capacity-matched random allocation at the imposed $0.25/email setting (−$0.02578/customer, 95% paired Wald interval [−$0.16538, $0.11381]); Ridge and historical-spend contrasts were also inconclusive. This establishes task feasibility, not method advantage. Its final partition is exposed, there is no label-release clock, and email costs are imposed; it cannot satisfy independent final confirmation. The Criteo Uplift policy-value avenue is excluded pending missing negative-label inclusion probabilities. No independent untouched downstream decision benchmark remains available in the current worktree. See `hillstrom_email_policy_development_protocol.md`, `criteo_uplift_eligibility_audit.md`, and the Hillstrom aggregate run manifest.

## New direct Q1 comparator result (2026-10-26)

A source-pinned Timans et al. unknown-shift e-process has now been mapped onto
the paired decision-cost null and compared on six registered synthetic
scenarios. Formula replay matched the official implementation; independent
verification checked seed coverage, null bounds, output hashes and 9,600 rows.
The run found no adjusted detection difference from ShiftLab's fixed-stake
mixture. Thus, the direct bounded-risk alarm itself is established prior work;
any novelty must concern the statistically valid and cost-aware transition to
intervention. This result does not close real-data decision utility or the
complete promotion comparator frontier. See
`timans_unknown_shift_paired_cost_protocol_v1.md` and the output report.


## OBD fixed-candidate gate follow-up — 2026-10-26

The frozen Open Bandit replay is complete after validating an exact optimizer for MOPE's per-event two-dimensional concave QP. The 274,737-event position-1 path returned no promotion: its MOPE confidence set first became empty at event 866, and the fixed-horizon Hoeffding lower bound also remained below zero. The first 1,000-event path matches the pinned CVXPY implementation exactly; a second full-data verifier reconstructed the policy, scores, daily values, path and artifact hashes. This adds one exploratory Q2 method-level evaluation but does not meet the OBD theorem assumptions, supply an independent real-data episode, or close the integrated real-data gap. The reported IPW point estimate is positive (+0.001809), which does not override the failed/empty gate. See papers/shiftguard_unified/open_bandit_mope_development_protocol_v1.md, papers/shiftguard_unified/mope_fast_optimizer_validation.md, and outputs/shiftguard_unified/real_data_development/open_bandit_mope_v1/.
