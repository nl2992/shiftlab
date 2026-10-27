# Comparecast weak-null calibration protocol

## Question and scope

Check whether the pinned official ComparingForecasters one-sided
gamma-exponential e-process exhibits gross false-escalation inflation on
registered synthetic population-null controls. This is a calibration
diagnostic for the **weak running-average score null**. It does not calibrate
DIVE's eventwise conditional-mean null and does not compare the methods' error
rates as if the nulls were the same.

## Frozen design

- External source: `yjchoe/ComparingForecasters`, commit
  `52748c86e0429a9612dc79892c3be6156a524132`.
- Scenarios: `stationary` and `benign_nuisance` from
  `decision_harm_experiment.py::POPULATION_NULL_CONTROLS`.
- Independent generator seeds: 2,000 per scenario, starting at 60,000,000.
- Stream: 2,400 events, dimension 16; monitoring begins at event 800 and
  observes the remaining 1,600 events with immediate full feedback.
- E-process: official `eprocess_expm` called unchanged, score increment equal
  to paired decision-cost difference minus the frozen 0.10 margin, support
  width `c=2B`, one-sided evidence threshold `1/0.05=20`.
- The generator runs on CUDA when available; the CPU path remains available.
- The primary calibration outcome is any threshold crossing over the horizon.
  Report a one-sided exact Clopper–Pearson upper bound with Bonferroni 95%
  familywise coverage across the two scenario cells.
- Evaluator truth is used only to audit the weak-null expected-prefix path and
  is never passed to the e-process. The DIVE conditional-mean process is not
  part of this calibration because these controls do not establish its
  eventwise conditional null relative to the observed filtration.

## Interpretation and stop rule

This frozen run is a finite Monte Carlo audit, not a proof of the published
theorem or a new validity guarantee. Report the observed false-escalation
count/rate and exact simultaneous upper limit. Flag the calibration as
inconclusive if either scenario's empirical weak-null prefix audit is not
nonpositive or if its simultaneous upper limit exceeds 0.05. Do not tune the
method or thresholds on these streams. Alternative power requires a separate,
disjoint registered seed block.

## Reproduction

```powershell
uv run python scripts/calibrate_comparecast_weak_null.py `
  --comparecast-source C:\path\to\ComparingForecasters `
  --output-dir outputs/shiftguard_unified/sota_reproductions/comparecast_weak_null_calibration_v2 `
  --seeds 2000 --seed-offset 60000000 --device cuda
```
