# Integrated matched development comparison protocol v1

**Status:** frozen development protocol; exploratory, not efficacy confirmation.  
**Date:** 2026-10-26.

## Question

On common synthetic streams, how do fixed candidate certification, Target-Scout selection, upstream Q1 gating, and controller gating affect cumulative downstream decision utility, rollback behavior, and label spend? This run diagnoses which components deserve inclusion in a later independent confirmation; it cannot establish a general superiority claim.

## Frozen design

- 30 independent streams per profile, using seeds `2026103000`–`2026103029`.
- Eight profiles: `stationary`, `benign_nuisance`, `boundary_local_harm`, `post_promotion_reversal`, `recurring_regimes`, `residual_variance`, `harmful_adaptation_at_monitor`, and `harmful_adaptation_native`.
- Nine methods: continue, scheduled promotion, two-gate Target-Scout, two-gate controller, Q1 fallback, full Q1→Target-Scout, full controller, Q2-only fixed candidate, and Q1-triggered full fixed candidate.
- Each method receives the same generated feature/outcome path and seed-derived query uniforms within a seed. Candidate policies are trained and frozen before the Q1 block. Q2 certification and Q3 rollback use fresh chronological blocks. The hard cap is 640 labels per method-stream.
- Run on CUDA when available, with the runner recording resolved device, hardware, source snapshots and hashes, protocol hash, and separate learner-visible/evaluator-only event Parquet logs.

## Outcomes and analysis

Primary descriptive endpoints are expected and realized cumulative paired decision utility net of declared intervention charges. Report label counts separately; do not convert label spend to decision-cost units. Secondary endpoints are Q1 trigger rate, promotion rate, rollback rate, detection timing, labels by stage, rollback timing, cap use, and expected versus realized utility. Compare paired seed-level differences for full Target-Scout versus full fixed certification, full versus two-gate, controller versus non-controller, and each intervention arm versus continue/fallback. Report 95% paired bootstrap intervals using 10,000 resamples, seed 2026102701; these are descriptive, unadjusted, and not confirmatory.

No outcomes are used to modify candidate families, costs, alpha allocations, method logic, profile definitions, or analysis choices. Stop at 30 seeds per profile. Save all per-stream metrics, summary, paired contrasts, event logs, manifest, and source snapshots. Do not make publication figures from this development comparison; a confirmatory figure should be generated later with the requested PaperBanana workflow after the scientific claim is frozen.

Run:

```powershell
uv run python -m shiftlab.dive.integrated_pipeline `
  --seeds 30 `
  --seed-offset 2026103000 `
  --device cuda `
  --output outputs/shiftguard_unified/integrated_development/pipeline_fixed_certification_dev_30_v1
```
