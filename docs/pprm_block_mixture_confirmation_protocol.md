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

### Protocol amendment after evaluator metadata audit

The initial protocol incorrectly grouped residual variance with the population-null controls. After
the run, inspection of the evaluator truth labels showed that this scenario is materially harmful
in all 200 streams, with a registered harm onset. It must therefore be analyzed as a harmful
scenario, not as a null calibration cell. Because this classification correction was made after
the outcomes were available, residual-variance detection is exploratory and is excluded from the
three-scenario primary Holm family. Only stationary and benign nuisance are population-null cells.
The result archive preserves all six scenarios and the correction is recorded in the analysis.

The 30-seed development block suggested 80% paired-test sample sizes of 36, 19, and 61 for the
boundary-local, harmful-adaptation, and recurring-regime detection contrasts against eventwise
updating PPI, respectively, using a normal approximation to the paired McNemar difference. The
independent block of 200 per scenario was fixed to exceed the largest of these estimates by more
than threefold. These pilot-based estimates are planning aids, not guarantees of power.

## Outcomes and analysis

The three predeclared primary harmful-scenario comparisons use exact two-sided paired McNemar tests
and Holm adjustment across scenarios. Detection rate, paired discordances, and rate difference are
reported. The fixed mixture is also compared descriptively with frozen eventwise PPI and CM-EB alone.
Stationary and benign-nuisance population-null cells report false-escalation counts and Wilson
intervals. Residual-variance detection is descriptive only under the amendment above. Estimation
RMSE, label use, and spend are secondary descriptive outcomes.

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

### Registered 2,000-stream null calibration

The fixed mixture and block CM-EB were calibrated on fresh seeds 20,374,000–20,375,999 in each of the two evaluator-registered population-null scenarios: stationary and benign nuisance. Both monitors had 0 false escalations in 2,000 streams per scenario (95% Wilson interval [0, 0.0019]). The run used CUDA batching, block size 20, four queried labels per block, a 20% hard label-dollar budget, and reliance cap 0.1. All 4,000 streams respected the hard budget. See `outputs/pprm_registered_null_calibration_2000_v1/reports/registered_null_calibration.md` and its manifest for the run configuration and hashes.

This calibration evaluates only the registered synthetic laws. It does not establish universal sequential validity or cover delayed labels and arbitrary dependence. Residual variance is excluded because evaluator metadata marks it materially harmful; its post-outcome reclassification and exploratory detection results are documented above.
