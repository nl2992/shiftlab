# Integrated Q1–Q3 efficacy confirmation results v1

**Status:** completed and independently verified, 2026-10-26. Independent synthetic seeds; not real-data confirmation and not a novelty result.

## Run and integrity

The frozen [protocol](integrated_efficacy_confirmation_protocol_v1.md) used seeds `2026104000`–`2026104099` across eight profiles and all nine registered methods. The CUDA run produced 7,200 seed-method metric rows, 23,040,000 learner-visible event rows, and 23,040,000 evaluator-only event rows. Maximum pathwise label use was exactly the registered 640-label cap; no run exceeded it. The independent analyzer verified all 72 profile-method cells, the full seed block per profile, learner/evaluator schema separation, recomputed summary values, source snapshots and output hashes. Its verification status is `passed`.

The full machine-readable summary is [`integrated_pipeline_summary.csv`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv); all stream metrics and event logs, the run manifest and the independent verification are in [`efficacy_100_v1`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/). The corrected independent analyses are in [`analysis_v3`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/analysis_v3/), whose verification includes the analyzer source hash. [`analysis_v1`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/analysis_v1/) and [`analysis_v2`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/analysis_v2/) are retained as earlier passes.

## Predeclared primary comparisons

The primary outcome is evaluator-expected cumulative paired-cost reduction net of the method's declared switching and rollback charges. Inference uses independent stream seeds. The 22 one-sided tests are Holm-adjusted at familywise 0.05; the lower bounds shown are simultaneous Bonferroni bounds. Realized utility and action rates remain separate secondary outcomes.

| Profile | Treatment vs comparator | Mean paired expected utility | Holm-adjusted p | Simultaneous lower 95% |
|---|---|---:|---:|---:|
| Boundary-local harm | Full pipeline vs continue | +118.006 | 2.09e-11 | +75.374 |
| Post-promotion reversal | Full pipeline vs continue | −143.758 | 1.000 | −182.477 |
| Recurring regimes | Full pipeline vs continue | 0.000 | 1.000 | 0.000 |
| Residual-variance shift | Full pipeline vs continue | 0.000 | 1.000 | 0.000 |
| Harm begins at monitor | Full pipeline vs continue | +161.161 | 3.15e-19 | +120.996 |
| Harm begins after monitor | Full pipeline vs continue | 0.000 | 1.000 | 0.000 |
| Stationary | Full pipeline vs two-gate | 0.000 | 1.000 | 0.000 |
| Benign nuisance | Full pipeline vs two-gate | 0.000 | 1.000 | 0.000 |
| Boundary-local harm | Full pipeline vs two-gate | −68.530 | 1.000 | −106.413 |
| Post-promotion reversal | Full pipeline vs two-gate | +37.264 | 0.00248 | +8.693 |
| Recurring regimes | Full pipeline vs two-gate | 0.000 | 1.000 | 0.000 |
| Residual-variance shift | Full pipeline vs two-gate | −8.916 | 1.000 | −18.493 |
| Harm begins at monitor | Full pipeline vs two-gate | −40.095 | 1.000 | −68.887 |
| Harm begins after monitor | Full pipeline vs two-gate | −201.256 | 1.000 | −238.066 |
| Stationary | Full pipeline vs fixed-candidate pipeline | 0.000 | 1.000 | 0.000 |
| Benign nuisance | Full pipeline vs fixed-candidate pipeline | 0.000 | 1.000 | 0.000 |
| Boundary-local harm | Full pipeline vs fixed-candidate pipeline | −129.508 | 1.000 | −172.629 |
| Post-promotion reversal | Full pipeline vs fixed-candidate pipeline | +73.228 | 3.31e-06 | +34.394 |
| Recurring regimes | Full pipeline vs fixed-candidate pipeline | 0.000 | 1.000 | 0.000 |
| Residual-variance shift | Full pipeline vs fixed-candidate pipeline | 0.000 | 1.000 | 0.000 |
| Harm begins at monitor | Full pipeline vs fixed-candidate pipeline | −82.317 | 1.000 | −120.911 |
| Harm begins after monitor | Full pipeline vs fixed-candidate pipeline | 0.000 | 1.000 | 0.000 |

The primary family has 22 contrasts: six full-pipeline-versus-continue comparisons, eight full-pipeline-versus-two-gate comparisons, and eight full-pipeline-versus-fixed-candidate comparisons. All 22 are shown; exact zero contrasts have a Holm-adjusted p-value of 1 and a lower bound of zero. The machine-readable table is in [`primary_contrasts.csv`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/analysis_v3/primary_contrasts.csv).

## What the results show

The full staged workflow improved expected utility over continuing in two aligned cases: boundary-local harm and adaptation beginning during the monitor window. It did not improve in recurring regimes, a residual-variance shift, or the native onset just after the Q1 window; it incurred substantial negative utility under post-promotion reversal. The timing result is explicit: Q1 triggered in 92–93% of streams when its monitor window overlapped boundary/adaptation harm, but in 0% of native late-onset streams. The two-gate arm, which has no upstream Q1 gate, promoted in 72% of those native late-onset streams and averaged +201.26 utility units over continuing.

The Q1 gate did not add utility over the two-gate workflow on the two aligned positive-harm profiles. The full pipeline averaged 68.53 fewer expected utility units in boundary-local harm and 40.10 fewer in monitor-aligned adaptation. At those same profiles, fixed-candidate certification averaged +247.51 and +243.48 units, respectively, compared with +118.01 and +161.16 for full Target-Scout; the differences favoring the fixed-candidate pipeline were negative for the full pipeline by 129.51 and 82.32 units, with family-adjusted tests not significant for these unfavorable directions because the predeclared one-sided tests only tested positive gains. These descriptive contrasts point to delay and scout-selection opportunity costs in this configuration; they do not establish a universal advantage for fixed selection.

Under the reversal stress, full Target-Scout and fixed-candidate pipelines were both worse than continuing (−143.76 and −216.99 mean expected utility), even though rollback occurred in 58% and 86% of streams. The two-gate workflow was also negative (−181.02) with 72% rollback. Rollback detection therefore did not recover costs accumulated before reversion. Controller and non-controller variants matched exactly in all eight profiles, showing no added value for this controller configuration.

The gated full-pipeline arms had 0/100 promotions in both stationary and benign-nuisance controls, and the Q1 monitor had 0/100 triggers in each. These are efficacy-block observations, not the source of the familywise calibration claim; that claim comes from the separate 1,000-stream-per-cell integrated null-calibration study. `scheduled_promote` has positive utility on some stable profiles because a candidate can improve utility even without a distribution shift; its values are an unconditional-promotion benchmark, not false statistical alarms.

## Research decision

The independent run confirms that the current integrated system has design-specific benefit when harm overlaps its monitor, but it does not show a general gain over the simpler two-gate workflow or fixed-candidate certification. The Q1 gate has a hard timing limitation for shifts beginning after its window. The controller adds no observed utility, and rollback does not neutralize reversal losses. This is a negative result for the claim that the current composition is uniformly better, while preserving a narrower, profile-specific result.

Do not start RIVE/ASC or claim unified superiority from this evidence. The next research decision is whether to narrow the paper to (i) calibrated decision-harm monitoring and a separate evidence-efficient certification comparison, or (ii) a new, tightly scoped intervention contract that addresses monitor timing, promotion delay, and pre-rollback losses. Any new method must be justified against the established baselines, then receive fresh null calibration and a separate efficacy block. The current run does not provide real-data confirmation; its full-system guarantees are limited to immediate feedback and the registered synthetic assumptions.
