# Independent PPRM mixture validation protocol

**Status:** frozen before the independent evaluation run.
**Candidate:** fixed 10% CM-EB / positive-betting block e-process mixture.
**Implementation:** `PPIBlockMixtureEProcess`, evaluated through the existing paired hard-budget experiment.

## Question and estimand

The selected mixture was chosen using the 30-seed development block documented in
`pprm_paired_decision_benchmark.md`. This independent experiment asks whether its stream-level
harm-detection rate differs from eventwise updating PPI on the registered synthetic generators.
The primary estimand in each harmful scenario is the paired difference in detection probability,
with the same seed, generated stream, costs, budget, and event horizon supplied to both methods.

## Frozen design

- Independent seed block: integers 20,373,000 through 20,373,199 (200 streams per scenario).
- Scenarios: stationary, benign nuisance, boundary-local harm, residual variance, recurring regimes,
  and harmful adaptation.
- Horizon: 6,400 events; block size 20; four labels sampled per block; nominal label budget 20%.
- PPI maximum and initial reliance: 0.1. The candidate mixture weight remains 0.1.
- Methods: eventwise updating PPI, eventwise frozen PPI, and block PPI, with the mixture evaluated
  as a pre-specified monitor on each block-PPI stream.
- Runtime: CUDA requested and recorded by the run manifest; CPU fallback remains available.

The 30-seed development block suggested 80% paired-test sample sizes of 36, 19, and 61 for the
boundary-local, harmful-adaptation, and recurring-regime detection contrasts against eventwise
updating PPI, respectively, using a normal approximation to the paired McNemar difference. The
independent block of 200 per scenario was fixed to exceed the largest of these estimates by more
than threefold. These pilot-based estimates are planning aids, not guarantees of power.

## Outcomes and analysis

The three primary harmful-scenario comparisons use exact two-sided paired McNemar tests and Holm
adjustment across scenarios. Detection rate, paired discordances, and rate difference are reported.
The fixed mixture is also compared descriptively with frozen eventwise PPI and CM-EB alone. The
stationary, benign-nuisance, and residual-variance cells report false-escalation counts and Wilson
intervals. Estimation RMSE, label use, and spend are secondary descriptive outcomes.

The analysis script checks the exact seed range, 200 streams, configured reliance cap, complete
paired methods, and known-harm labels before writing the report. No candidate parameter will be
selected or tuned on this independent block.

## Reproduction

```powershell
uv run python scripts/run_pprm_block_grid.py `
  --output-root outputs/pprm_block_mixture_independent_v1 `
  --seeds 200 --seed-offset 20373000 --n 6400 --device cuda `
  --block-sizes 20 `
  --scenarios stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation `
  --reliance-cap 0.1

uv run python scripts/analyze_pprm_block_mixture_confirmation.py
```

This protocol supports conclusions only about the registered generators and feedback path. It does
not demonstrate validity for arbitrary serial dependence, adaptive query mechanisms, delayed labels,
or real-world shifts; nor does a monitor's rejection certify a replacement policy for deployment.
