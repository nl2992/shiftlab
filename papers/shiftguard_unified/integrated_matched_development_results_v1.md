# Integrated 30-seed matched development results

**Status:** exploratory development comparison; not an efficacy confirmation.  
**Date:** 2026-10-26.

## Run and verification

The frozen protocol is [`integrated_matched_development_protocol_v1.md`](integrated_matched_development_protocol_v1.md). The CUDA run used seeds 2026103000–2026103029 on each of eight profiles and nine methods, for 2,160 method-stream rows. It wrote 6,912,000 learner-visible and 6,912,000 evaluator-only event rows. The largest per-stream label count was 640; there were no cap violations. The output manifest records code snapshots, source/protocol hashes, hardware, and metric hashes. The separately frozen protocol was added to the run manifest with its own SHA-256 after execution; no run parameters or results changed during that provenance addition.

## Main results

Expected and realized utility are mean cumulative paired-cost reductions after declared intervention charges. Labels remain a separate resource metric. Each cell has 30 streams.

| Profile | Method | Promotion | Rollback | Mean labels | Expected utility | Realized utility |
|---|---|---:|---:|---:|---:|---:|
| Boundary-local harm | Q2-only fixed candidate | 29/30 | 0/30 | 314.0 | 290.75 | 292.25 |
| Boundary-local harm | Two-gate Target-Scout | 16/30 | 0/30 | 398.1 | 163.00 | 165.64 |
| Boundary-local harm | Q1→Target-Scout | 13/30 | 0/30 | 525.7 | 133.72 | 136.61 |
| Boundary-local harm | Q1→fixed candidate | 28/30 | 0/30 | 604.1 | 282.20 | 284.12 |
| Boundary-local harm | Q1 fallback | 0/30 | 0/30 | 183.3 | 722.66 | 720.85 |
| Harm begins at Q1 monitor | Q2-only fixed candidate | 29/30 | 0/30 | 314.0 | 271.18 | 272.02 |
| Harm begins at Q1 monitor | Two-gate Target-Scout | 23/30 | 0/30 | 434.5 | 210.73 | 212.06 |
| Harm begins at Q1 monitor | Q1→Target-Scout | 22/30 | 0/30 | 568.5 | 200.23 | 201.86 |
| Harm begins at Q1 monitor | Q1→fixed candidate | 28/30 | 0/30 | 600.0 | 261.16 | 262.39 |
| Harm begins after Q1 window | Two-gate Target-Scout | 23/30 | 0/30 | 434.5 | 210.73 | 212.06 |
| Harm begins after Q1 window | Q1→Target-Scout | 0/30 | 0/30 | 315.3 | 0.00 | 0.00 |
| Harm begins after Q1 window | Q1→fixed candidate | 0/30 | 0/30 | 315.3 | 0.00 | 0.00 |
| Post-promotion reversal | Two-gate Target-Scout | 23/30 | 23/30 | 331.9 | −183.91 | −183.91 |
| Post-promotion reversal | Q1→Target-Scout | 22/30 | 22/30 | 470.8 | −186.24 | −186.24 |
| Post-promotion reversal | Q1→fixed candidate | 28/30 | 28/30 | 475.1 | −231.43 | −231.43 |
| Post-promotion reversal | Q1 fallback | 0/30 | 0/30 | 171.8 | −1,165.27 | −1,165.85 |

Stationary and benign-nuisance Q1 alarm counts were 0/30 in each profile. The native event-1,600 onset is intentionally outside Q1's event-800–1,599 window; Q1-gated methods therefore do not act on it, while two-gate methods observe the later Q2 block and can certify a candidate. That shows a timing limitation of the staged Q1 gate, not a false alarm or a general result about late-onset monitoring.

In both aligned harm profiles, the frozen candidate outperformed scout-selected candidates descriptively. The unadjusted seed-paired bootstrap difference for full Target-Scout minus full fixed-candidate expected utility was −148.48 in boundary-local harm (95% interval [−205.34, −92.48]) and −60.93 when harm began at Q1 ([−109.18, −13.54]). The Q1 fallback exceeded full Target-Scout by 588.93 and 510.47 utility units in those profiles. This fallback is the synthetic reference policy under the imposed cost law; the result does not establish a safe operational fallback or financial value.

Under post-promotion reversal, rollback occurred in 73% of two-gate and full Target-Scout streams and 93% of full fixed-candidate streams, but mean utility remained negative. Thus rollback detection did not recover the costs accumulated before reversion. In this synthetic reversal, full Target-Scout exceeded full fixed certification by 45.19 paired expected-utility units (unadjusted 95% interval [2.33, 90.04]); both remained below continuing with the incumbent. The Q1 fallback did especially poorly because the declared reference action became harmful under the reversal schedule.

Controller gating made no promotion changes in these 30-seed profiles: full-controller versus full-pipeline and two-gate-controller versus two-gate paired utility differences were exactly zero in every profile. This indicates no incremental value for this controller configuration in these streams; it does not rule out other information, forecast, or cost contracts.

All paired intervals are 10,000-resample, seed-level bootstrap intervals, unadjusted for multiplicity and intended only as development diagnostics. The results expose design-specific tradeoffs and do not support a general superiority claim. The benchmark uses immediate labels, a synthetic non-performative classification stream, and imposed decision/switching costs. No real-data external evaluation is present here.

## Artifacts and next decision

The run artifacts are [`manifest.json`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1/manifest.json), [`experiment_protocol.md`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1/experiment_protocol.md), [`integrated_pipeline_seed_metrics.parquet`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1/integrated_pipeline_seed_metrics.parquet), [`integrated_pipeline_summary.csv`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1/integrated_pipeline_summary.csv), and the two event logs in that same directory. Additional planned contrasts, including controller ablations, are in [`additional_paired_contrasts.csv`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1/additional_contrasts_v3/additional_paired_contrasts.csv), with their own [`analysis manifest`](../../outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1/additional_contrasts_v3/manifest.json).

The development signal is mixed: fixed candidate choice has an advantage in the two aligned harm settings, Q1 gating misses post-window onset by construction, rollback can be too late, and the present controller adds no utility. Do not develop RIVE/ASC from this evidence alone. Next, finish source-faithful published-comparator and real-data task contracts; if the synthetic choice between fixed and scout selection remains a target, run a fresh, larger development block before freezing any disjoint efficacy confirmation.
