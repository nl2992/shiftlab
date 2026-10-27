# Composition compatibility audit: Q1–Q3 components

**Date:** 2026-10-26. **Purpose:** determine which existing components can be
combined without silently inheriting guarantees they do not jointly have.
This is a source-and-contract audit, not an integrated experiment or a new
theorem.

## Components and compatible contracts

| Component | Learner-facing quantity and evidence | Conditions needed in its current implementation | Composition consequence |
|---|---|---|---|
| DIVE bounded-mean monitor | A predictable bounded increment derived from paired deployed-minus-reference decision cost, with its sign and materiality margin fixed before monitoring. | Correct conditional mean null, valid bounded support, event order matching the filtration, and a predictable acquisition propensity when using query-corrected observations. | Can trigger an intervention if the monitoring block and cost contract are fixed. Reusing the same observations to select and certify a replacement needs a separate proof or a fresh split. |
| Target-Scout | Selects a candidate from a fixed family using one target-period scout slice and certifies the selected candidate on a later slice. The eventwise variant uses actual predictable propensities and the corresponding bound. | Candidate family and context definition fixed before target feedback; selection outcomes excluded from the certification process; valid propensity floor and support; immediate feedback under the registered runs. | A DIVE-triggered Target-Scout stage can be conditionally valid only if it starts on fresh future data and its own null/alpha allocation remains valid after the trigger. The earlier DIVE data cannot be recycled as scout or certification evidence. |
| Promotion/rollback process | First certifies a candidate, then tests it using forward deployment feedback for rollback. | The rollback process starts after the promotion decision, uses fresh feedback, and tests its declared candidate-harm null with a compatible bound. The existing simulator intentionally makes shadow and deployment potential-cost draws independent. | Can follow Target-Scout only with a new post-promotion monitoring block. A candidate selected or repeatedly replaced during rollback monitoring is outside the current guarantee. |
| `InterventionController` | Chooses the largest supplied positive one-step net-value estimate after declared costs. | Forecasts and authorization booleans are inputs; the controller does not certify them. | It may allocate resources among actions already authorized by separate gates. It cannot replace the e-processes or convert uncertified forecasts into a safe deployment guarantee. |

## Cross-stage requirements for a valid integrated comparison

1. Define one event stream with event time, feature availability, decision,
   label request, feedback maturity, and action costs. A common event label may
   reveal losses for multiple fixed policies only in the non-performative
   setting; if an action changes the outcome, the benchmark needs causal or
   off-policy identification instead.
2. Freeze the incumbent, fallback, candidate family, context partition,
   action-cost matrix, and switching, rollback, retraining, and label costs
   before the run. Keep expected costs, scenario labels, and oracle policy
   identity in evaluator-only state.
3. Use non-overlapping time blocks for incumbent monitoring, candidate
   scouting, candidate certification, and post-promotion rollback. A stage
   begins only after its trigger is predictable from the past; conditional
   validity after that trigger must be established for that stage's data law.
4. Define the family of error events before assigning alpha. If the study
   claims control of false fallback, false promotion, and false rollback
   jointly, allocate the total error budget across those named events and
   prove each stage's conditional control. Distinct weak-running-average,
   eventwise-conditional-mean, and candidate-value nulls must remain distinct.
5. Enforce a single hard label-dollar budget across all stages, with stage
   reservations and an explicit rule for unused budget. Match seeds, potential
   outcomes, query uniforms, and total observed labels across comparators.
   Report both labels and calendar/events processed.
6. Include `continue`, unconditional/periodic adaptation, the existing
   two-gate promotion/rollback system, and the full staged system. Add a
   published Q3 baseline only after its observation and action-feedback
   assumptions are shown compatible; do not relabel a heuristic as ASI, RCCDA,
   or *When to Retrain*.
7. Evaluate net decision utility and intervention cost on evaluator-only
   outcomes. Report false escalations by their declared null, detection delay,
   harmful promotions, rollback timing, labels/cost, and paired seed-level
   uncertainty. A component-level gain is not evidence that the full stack
   helps.

## Current status and decision

The source code contains reusable implementations for each component, and the
Target-Scout information-flow audit found that mutating oracle `h_truth` does
not change candidate IDs, promotion decisions, label counts, or stop reasons.
The 2,000-seed closed-loop experiment verifies a promotion/rollback component
under its own explicit paired-gain simulator. The Q1 paired-cost confirmation
and Q2 Target-Scout confirmation are now independently verified, but each uses
its own registered design. **No current experiment composes all four stages
under one common stream and one hard total budget.** The existing closed-loop
result therefore remains a component benchmark, not end-to-end evidence.

Before code or data generation, freeze the common stream and cost contract,
stage order, alpha family, candidate family, stage budget, comparator set, and
sequential test. The primary falsification target is that the full staged
system may spend its label and switching budget without improving net utility
over `continue` or the simpler two-gate workflow, especially under early
reversal or weak residual-variance harm. If no valid common contract can be
specified without changing the source methods' estimands, keep the Q1–Q3
results separate and make a narrower empirical contribution decision.

## Q3 comparator compatibility update (2026-10-26)

The primary-paper audit confirms that the published *When to Retrain a Machine Learning Model* policy is a finite-horizon cost decision rule, not a sequential test. It forecasts bounded model-performance variables, recursively forms total-cost distributions under `retrain` and `keep`, then retrains when the selected quantile of total cost under retraining is lower. Its horizon, future-performance forecasts, retraining penalty, and quantile level are part of the method. A faithful benchmark must supply those inputs on the same prespecified horizon and cost scale. A threshold on recent error, including the existing EIA trigger, is not a reproduction of this rule.

Active Statistical Inference (ASI) and Robust Sampling for ASI instead target fixed-horizon estimation and inference under their sampling designs. Their label allocations can be compared on a reserved fixed-horizon decision-cost estimation task, with their original estimators and uncertainty procedures, but they do not inherit anytime-valid guarantees for online monitoring. The local robust residual allocation policy is an adaptation. The official Robust ASI repository has no top-level license in the audited checkout, so its code must not be copied into this repository; the paper algorithm can be independently implemented with provenance and deviations documented.

RCCDA is a resource-constrained predictive-loss update controller. Its update-cost objective and assumptions differ from paired downstream-cost monitoring. It is suitable as a separate matched task only if its supported dataset/update protocol and resource units can be reproduced. No source-level reproduction has been verified. The official repository checkout also had no top-level license in the audit; do not redistribute copied code.

These distinctions rule out a single undifferentiated leaderboard. Q3 should use two linked panels: (a) fixed-horizon allocation and inference baselines (ASI, Robust ASI, and active testing where its estimand fits), and (b) finite-horizon update policies (*When to Retrain*, periodic/triggered controls, and RCCDA where its published assumptions fit). Their outputs may enter the same evaluator-side net-utility accounting only after each method's information, label, compute, horizon, and intervention-cost contract is explicitly mapped. No comparator may be credited with a certificate for an estimand it does not test.

**Status after this audit:** the paper-level decision rules and incompatibilities are clearer, but no common Q3 experiment has been implemented or run. The integrated protocol still needs a shared event stream, fixed action-cost and label budgets, stagewise information access, error-family allocation, and matched comparators. This audit alone does not change the NO-GO decision on new algorithm development.

Primary references: [When to Retrain (ICML 2025)](https://proceedings.mlr.press/v267/regol25a.html), [ASI (ICML 2024)](https://proceedings.mlr.press/v235/zrnic24a.html), [Robust Sampling for ASI (NeurIPS 2025)](https://papers.nips.cc/paper_files/paper/2025/file/6389470564214983604d1ac81631c2c5-Paper-Conference.pdf), and [RCCDA (NeurIPS 2025)](https://proceedings.neurips.cc/paper_files/paper/2025/hash/e3d1b6d954a204267fd334cbaf9cd4af-Abstract-Conference.html).

## Prototype update (2026-10-26)

A first common-stream development runner now composes the direct Q1 paired-cost process, the existing fresh-block Target-Scout selection/certification routine, and forward rollback monitoring. The 3,200-event CUDA pilot used a global 640-label cap and stage-specific alpha values totaling 0.05. On 10 seeds per profile it triggered in 9/10 boundary-local-harm and 10/10 aligned harmful-adaptation streams, with 0/20 stationary/benign-control triggers; one boundary-harm stream promoted, and rollback did not occur. The residual-variance screen had 0/10 triggers. These are exploratory counts only. The runner does not include the `InterventionController`, matched periodic/always-promote and two-gate comparators, simultaneous calibration, or reversal stress, so it still does not satisfy the integrated benchmark requirements above. Report and checksummed artifacts: [`integrated_pipeline_development_report.md`](integrated_pipeline_development_report.md) and `outputs/shiftguard_unified/integrated_development/pipeline_dev_10_v7/`.

## Matched comparison update (2026-10-26)

The initial Q1 → Target-Scout → rollback prototype has now been extended to five matched policies on each generated stream: continue, scheduled promotion, two-gate Target-Scout plus rollback, Q1-triggered fallback, and the full staged pipeline. The eventwise-propensity bound variant yielded 300 method-stream rows across 60 streams in six profiles. No stream exceeded 640 labels. Q1 triggered on 9/10 boundary-local-harm, 9/10 recurring-regime, and 10/10 aligned harmful-adaptation streams; it triggered in 0/20 stationary/benign controls. Gated promotion was 7/10 versus 8/10 for full versus two-gate in boundary harm, 5/10 versus 6/10 for aligned harmful adaptation, and 0/10 for either method in recurring regimes or residual-variance change. No rollback crossing occurred.

The exploratory paired-bootstrap comparison found no utility advantage from adding Q1: expected full-minus-two-gate utility was −29.14 (unadjusted 95% interval [−100.02, 12.61]) under boundary harm and −28.34 ([−85.03, 0]) under aligned harmful adaptation. The fixed source-score fallback produced much larger gains in these designed profiles. These small, unadjusted development comparisons are not confirmatory and do not establish broad utility. The full report and artifacts are in [`integrated_pipeline_matched_development_report.md`](integrated_pipeline_matched_development_report.md) and `outputs/shiftguard_unified/integrated_development/pipeline_matched_eventwise_dev_10_v1/`. The controller, real-data confirmation, rollback reversal test, and joint calibration remain open.
