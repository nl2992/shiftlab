# Repeated-candidate monitoring-rule comparison protocol

**Protocol lock:** 2026-10-23, before running the fresh seed block. This is an
exploratory comparison of established monitoring baselines, not a search for a new
algorithm. Earlier single-candidate betting studies are pilot evidence and do not
use this promotion outcome, candidate family, or seed block.

## Question

Under the same candidate policies, queried outcomes, hard label cap, support bound,
and validation-spent familywise alpha, how do established sequential monitors differ
in false promotion on an exact-copy family, promotion of useful candidates, and
post-promotion expected decision value?

The primary safety diagnostic is the exact-copy family promotion rate. The main
utility outcomes are promotion probability and evaluator-known future net decision
gain on the six non-null scenarios. Label count and processed horizon describe the
budget use. Paired seed differences are descriptive; intervals are not adjusted for
the scenario grid, and no monitor is selected from this evaluation block.

## Frozen design

- Scenarios: the six registered ShiftLab DGPs plus `candidate_family_null`, where
  all 13 frozen candidates are copies of the incumbent.
- 60 independent seeds, offset `25102026`; 3,200 observations and 16 features per
  seed; alpha `0.05`; switching cost `0.05`.
- Hard label caps: 10% and 20% of the monitor horizon. Every rule uses the same
  seeded query uniforms within a scenario/seed/cap cell, so it sees identical
  labels and stops at the same budget time.
- Fixed query policy `uniform`, estimator `direct_ipw`, candidate alpha spending
  `rank`, and a common global support bound. These were chosen before this run to
  isolate monitor design using an estimator and alpha allocation already present in
  the registered promotion benchmark.
- Six monitors: fixed-stake mixture at candidate alpha; the same mixture at
  candidate alpha/2; predictable plug-in Kelly; predictable plug-in
  empirical-Bernstein (PM-EB); full-alpha one-sided positive betting; and the
  half-weighted positive branch of the hedged process at candidate alpha/2.
- All candidate tests share queried labels. Validation freezes the candidate
  family and alpha allocation before monitoring. The evaluator alone sees true
  probabilities and unqueried labels. GPU generation is requested; the manifest
  records the resolved device and runtime.

## Statistical scope

The fixed mixture is a nonnegative betting e-process for the bounded
history-conditional mean null. Predictable Kelly is a valid baseline because its
stake is predictable and in `[0,1]`; it is not claimed to optimize power. PM-EB uses
the published one-sided upper-null process and its predictable plug-in variance
schedule. Positive betting tests the same upper null using a predictable stake and
the nonnegative factor `1 + lambda (Z_t - 1/2)`. The hedged comparator uses the
positive branch with capital weight one half, which spends candidate alpha/2.
Candidate-level alpha allocations sum to at most 0.05, giving familywise control by
the union bound when each candidate process is valid. The alpha/2 mixture is
included to compare the hedge at a matched threshold.

These are design-level guarantees under the stated bounded increments, predictable
query probabilities, immediate randomized label observation, and fixed candidate
family. This synthetic benchmark does not establish validity under delayed labels,
adaptive candidate generation during monitoring, action-dependent outcomes, or
misspecified support bounds. Empirical false-promotion rates from 60 seeds are
calibration diagnostics, not proof of the guarantee.

## Reproduction

```powershell
uv run shiftlab-dive-budgeted-promotion `
  --seeds 60 --seed-offset 25102026 --n 3200 --device cuda `
  --bound-mode global `
  --monitoring-rules fixed_mixture fixed_mixture_half_alpha predictable_kelly pm_eb positive_betting hedged_positive `
  --query-policies uniform --estimators direct_ipw --alpha-allocations rank `
  --budget-rates 0.10 0.20 `
  --output outputs/promotion_monitor_comparison_60
```

If CUDA is unavailable, repeat with `--device cpu`; record that as a separate run.
The benchmark writes seed-level Parquet, summary and paired-contrast Parquet, a
figure, a report, and a hashed manifest under the output directory.
