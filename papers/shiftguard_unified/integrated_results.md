# Integrated monitor–certify–rollback results

**Status:** current-source synthetic null calibration and the frozen disjoint efficacy confirmation are complete and independently verified. The efficacy result is profile-specific synthetic evidence, not real-data confirmation or a novelty result. **Date:** 2026-10-26.

## Calibration question

Does the current 3,200-event CUDA state machine exhibit false Q1 escalation, false Q2 promotion after actual scout selection, or false Q3 rollback after a beneficial candidate is deployed under the registered synthetic nulls? This is an implementation-calibration question. It is separate from whether the integrated method improves cumulative utility over its baselines.

## Protocol and execution

The frozen null design is in [`integrated_null_calibration_protocol_v1.md`](integrated_null_calibration_protocol_v1.md). It uses the existing 800/800/800/800 stages, immediate feedback, a pathwise 640-label cap, three error budgets (0.02, 0.015, 0.015), and disjoint seed ranges. Q1 has two 1,000-stream controls. Q2 scans until 1,000 streams trigger Q1, select a candidate, and satisfy the evaluator-defined null. Q3 scans until 1,000 promoted policies pass an independent population-gain lower bound, without using deployment outcomes to determine eligibility.

Command:

```powershell
uv run python scripts/calibrate_integrated_pipeline.py `
  --replicates 1000 `
  --max-q3-streams 2500 `
  --device cuda `
  --output outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v2
uv run python scripts/verify_integrated_pipeline_calibration.py `
  --output outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v2
```

The run used an NVIDIA GeForce RTX 4060 Laptop GPU, PyTorch 2.9.1, and CUDA 13.0. The manifest records hardware, seed blocks, protocol hash, and source hashes.

## Results

All four endpoints had zero observed errors. The exact one-sided Clopper–Pearson limits use Bonferroni-adjusted 98.75% confidence per endpoint, giving at least 95% simultaneous confidence across the four cells.

| Error endpoint | Eligible streams | Errors | Adjusted exact upper bound | Stage alpha | Result |
|---|---:|---:|---:|---:|---|
| Q1 escalation, stationary | 1,000 | 0 | 0.4372% | 2.0% | Pass |
| Q1 escalation, benign nuisance shift | 1,000 | 0 | 0.4372% | 2.0% | Pass |
| Q2 false promotion after candidate selection | 1,000 | 0 | 0.4372% | 1.5% | Pass |
| Q3 false rollback for eligible beneficial deployment | 1,000 | 0 | 0.4372% | 1.5% | Pass |

The two Q1 cells contained 1,000 attempts each and averaged 314.8 and 314.2 labels, respectively, with maxima of 320. The nuisance features shifted from event 640, before the Q1 monitoring block; the signal coordinates and conditional outcome law remained fixed.

The Q2 cell required 1,089 attempts to obtain 1,000 eligible streams: Q1 triggered on 1,062 attempts, and scout selected a candidate on 1,000. No selected challenger passed certification. These challengers were non-identical to the incumbent but pointwise non-improving by the registered synthetic cost rule, so this tests certification after real candidate selection rather than a degenerate copy-policy case.

The Q3 cell required 1,266 attempts to obtain 1,000 eligible promotions. Its independent oracle evaluation estimated mean per-event incumbent-minus-candidate gain of 0.4992 cost units; the smallest Monte Carlo Hoeffding lower bound among eligible streams was 0.2578. Mean label use was 572.6 and the maximum was exactly the 640-label cap. The Q3 state machine triggered no false rollback.

The independent verifier recomputed all four exact-binomial summaries, checked the protocol/source/artifact hashes and label caps, and replayed all 1,266 Q3 streams. The replay reproduced each promotion, rollback, label count, population-gain estimate, lower bound, and eligibility decision. Current-source verification output: [`verification.json`](../../outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v2/verification.json). Full stream metrics and manifest: [`stream_metrics.parquet`](../../outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v2/stream_metrics.parquet) and [`manifest.json`](../../outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v2/manifest.json).

## Interpretation and remaining limits

The registered synthetic calibration gate passed. This does not prove a combined guarantee by itself; validity still depends on the bounded conditional-mean nulls, predictable query propensities, fresh stage data, and the component e-process assumptions. The calibration result alone does not measure detection power, utility improvement, or performance against a published integrated comparator.

The Q2 calibration family is a purpose-built conditional-null diagnostic, not an efficacy baseline. Q3 null eligibility is supported by a separate 100,000-feature Monte Carlo evaluation and a finite-sample Hoeffding bound; its union-bound error over at most 2,500 examined streams is at most 0.000025. The calibration covers independent synthetic stage blocks only. It does not cover delayed, dependent, recurring, performative, or real-data streams.

## Frozen disjoint efficacy confirmation

The frozen [efficacy protocol](integrated_efficacy_confirmation_protocol_v1.md) completed on disjoint synthetic seeds and passed its independent artifact, source, protocol, cap, and metric verification. It contains 100 seeds for each of eight profiles and nine methods (7,200 seed-method metric rows; 23.04 million learner-visible and 23.04 million evaluator-only event rows). The highest-level finding is mixed: the full pipeline improved on `continue` for boundary-local harm (+118.01 expected utility) and monitor-aligned adaptation (+161.16), but did not improve on `continue` for recurring regimes, residual-variance change, or native late onset. Under post-promotion reversal, its expected utility was −143.76. It underperformed the simpler two-gate arm in the first two aligned-harm profiles; fixed candidate certification also had higher descriptive utility there. Rollback did not recover reversal losses, and controller arms matched their non-controller versions. The full profile-by-method results, paired tests, multiplicity adjustment, and limitations are in [`integrated efficacy confirmation results v1`](integrated_efficacy_confirmation_results_v1.md); checksummed artifacts and verification are under [`outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/`](../../outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/).

This closes the registered synthetic efficacy run for that frozen configuration, but it does not establish integrated-system superiority, real-data transfer, or a paper-level novelty claim. Broader Q1–Q3 comparator fidelity and independent real-data confirmation remain open. The result does not justify a new algorithm branch; the current decision remains NO-GO for RIVE/ASC pending the finite comparator and publication-scope audit.

## Supplementary fixed-candidate certification calibration

The no-scout ablation is implemented as `fixed_candidate_certification` (Q2 only) and `full_pipeline_fixed_certification` (Q1 trigger followed by fixed-candidate Q2 certification and Q3 rollback). Candidate 0 is fixed from initial validation before Q1 begins; the certification e-process sees only fresh labels from events 1,600–2,399. The protocol is frozen separately in [`fixed_candidate_null_protocol_v1.md`](fixed_candidate_null_protocol_v1.md), so the original four-cell v1 simultaneous confidence calculation remains unchanged.

CUDA calibration on the NVIDIA GeForce RTX 4060 Laptop GPU collected 1,000 eligible streams in 1,030 attempts. Eligibility required the Q1 trigger and independent pointwise-null verification of the fixed candidate over the fresh Q2 block. There were **0 false promotions**; the exact one-sided 95% Clopper–Pearson upper bound is **0.2991%**, below the 1.5% promotion alpha. Maximum label use was 480/640. The independent verifier replayed every attempted seed and independently recomputed the pointwise conditional gain from candidate and incumbent actions; all outcomes, null checks, label counts, hashes, and summary bounds matched. The run is diagnostic synthetic calibration, not efficacy evidence.

Artifacts: [`summary.json`](../../outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1/summary.json), [`verification.json`](../../outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1/verification.json), [`manifest.json`](../../outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1/manifest.json), and [`stream_metrics.parquet`](../../outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1/stream_metrics.parquet).

## Current-source refresh and matched development grid

After integrating the fixed-candidate arms, the original four-cell calibration was rerun with the updated `integrated_pipeline.py` source hash under the unchanged frozen null protocol. CUDA results reproduced 0/1,000 errors in all four cells, 4,355 total stream rows, and the same simultaneous 0.4372% upper bound. The independent verifier rechecked all artifacts and replayed all 1,266 Q3 attempts with no mismatches. This is the current-source calibration record linked above.

The initial nine-arm, two-seed smoke grid is documented in [`integrated_fixed_certification_development_report.md`](integrated_fixed_certification_development_report.md). A frozen follow-up with 30 fresh seeds per profile is documented in [`integrated_matched_development_results_v1.md`](integrated_matched_development_results_v1.md); it is still exploratory and not an efficacy confirmation.
