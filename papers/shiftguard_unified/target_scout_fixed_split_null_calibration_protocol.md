# Exact-rule null calibration for the three-way Q2 comparison

**Status:** frozen before execution, 2026-10-26. This calibration is a gate for
the exact source-validation fixed-split, Target-Scout, and pooled-rank rules in
the matched development runner. It is not a power or superiority experiment.

## Question and null

Under the registered stationary target law, do any of the three promotion
rules exceed a 5% false-promotion rate across the prespecified prevalence and
visible-proxy-error settings?

The zero-signal outcome probability in each target context is exactly the
FN/FP decision threshold `1/6`, with FN cost 5 and FP cost 1. Thus every
candidate action has zero gross conditional expected gain at every target
event. Any selected policy also incurs the positive one-time switch charge
0.05, so every promoted policy has nonpositive evaluator-known net expected
future gain. The relevant calibration outcome is a promotion under this
eventwise nonpositive-mean null. Validation selection is separated from the
monitor for fixed split and pooled rank; Target-Scout selects its context
mapping on the first target slice and certifies only on the remaining slice.
This design does not establish validity under serially dependent outcomes,
delayed feedback, adaptive query probabilities, misspecified propensities,
distributional changes during certification, or real deployments.

## Frozen design

- 1,000 independent matched seed blocks per cell, seeds
  `99,000,000–99,000,999`. A repository-wide scan of experiment manifests and
  registered seed ranges was performed before freezing; this block does not
  overlap the Q2 development range or the existing Target-Scout Markov-null
  calibration range.
- Nine cells: target context prevalence `0.10/0.50/0.90` crossed with visible
  proxy error `0/0.10/0.25`. Signal is fixed at zero.
- `n=3,200`, `d=16`, FN/FP costs 5/1, switching cost 0.05, alpha 0.05, uniform
  direct-IPW monitoring, fixed-mixture betting, and a 40% pathwise label cap.
- Compare `fixed_sample_split`, `target_scout`, and `pooled_rank` on the same
  generated outcome stream and query-uniform path for every seed/cell.
- Primary calibration metric: promotion frequency. Report one-sided exact
  Clopper–Pearson upper confidence bounds with familywise alpha 0.05 divided
  across all 27 method-by-cell strata. The calibration passes only if every
  upper bound is at most 0.05, the evaluator-known net gain is nonpositive for
  every promotion, the true eventwise null holds, and no pathwise label cap is
  exceeded. A failed gate retires a baseline-relative claim for this exact
  configuration; do not tune on this calibration block.
- No plots are planned. This is a calibration table, not an efficacy figure.

## Reproduction

```powershell
uv run python scripts/calibrate_target_scout_fixed_split.py `
  --seeds 1000 --seed-offset 99000000 --device cuda `
  --output outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1
```

The runner writes per-seed metrics, exact intervals, an environment record,
source hashes, and checksums. It supports cellwise checkpoints and refuses to
overwrite non-checkpoint files. Any confirmation must use a new frozen protocol
and a seed block disjoint from this calibration.
