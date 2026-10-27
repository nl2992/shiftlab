# Comparecast paired-cost development comparison

## Question and scope

This is a bounded reproduction seam for the e-process in the official
ComparingForecasters implementation. It asks whether that published weak
running-average score comparison can be evaluated on the same full-feedback
paired downstream-cost sequence used by ShiftLab's bounded conditional-mean
monitor. This is a development comparison, not a null calibration, a
confirmation experiment, or evidence of superiority.

## Methods and estimands

Both methods receive the same realized candidate-minus-reference cost
increments, with positive values indicating that the candidate policy costs
more. ShiftLab's `BoundedMeanEProcess` tests an eventwise conditional-mean
null. Comparecast's official `eprocess_expm` tests its weak running-average
score null. These hypotheses differ; alarm rates and detection rates must not
be presented as like-for-like guarantees. The increment support is
`[-B, B]`, so the upstream score-difference width is set to `2B`.

This uses immediate, full-feedback synthetic streams. It does not evaluate
label acquisition, delayed feedback, action-dependent outcomes, or real-data
validity. The six registered scenarios are the existing stationary control,
benign nuisance shift, boundary-local harm, residual-variance shift, recurring
regimes, and harmful adaptation generators. Generator truth remains evaluator
only.

## Run design

The development screen uses 30 independent seeds per scenario, seed offset
`30325000`, stream length 2,400, feature dimension 16, alpha 0.05, and CUDA
generation when available. It reports alarms, first crossings, post-onset
detections, pre-onset alarms, processed events, and evaluator-known mean
margin excess. There is no inferential winner rule and no tuning based on this
screen. A separate fresh null-calibration design and disjoint alternative
confirmation would be required before making error-control or power claims.

## Provenance and execution

Use the official MIT-licensed `yjchoe/ComparingForecasters` checkout and record
its exact commit and source hashes in the generated manifest. The script calls
only the upstream e-process module unchanged. A narrow import shim is used
only for the confidence-sequence boundary dependency, which this experiment
does not call; the shim raises if invoked. This allows the official e-process
path to run without building the upstream C++ extension on Windows.

Run from the repository root:

```powershell
uv run python scripts/reproduce_comparecast_paired_cost.py `
  --comparecast-source C:\path\to\ComparingForecasters `
  --seeds 30 --seed-offset 30325000 --n 2400 --d 16 --device cuda
```

The runner refuses to overwrite a nonempty explicitly supplied output
directory. If `--output-dir` is omitted, it selects the base directory
`outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_dev_v1/`
or the next unused `_runNNN` suffix, preserving every earlier run. Metrics and
a manifest are written to the selected directory; the exact path is recorded
in the manifest. The manifest includes protocol, local and upstream source
hashes, environment, configuration, results, warning diagnostics, and
limitations. Upstream NumPy warnings are captured and recorded, not suppressed
or changed. No figure is specified for this comparison.

## Interpretation limits

Thirty streams per cell do not establish alpha calibration. Any difference in
alarms may reflect the methods' different nulls and test construction, not a
head-to-head advantage. The benchmark uses synthetic evaluator-known costs
and makes no claim about online release clocks, real deployment utility, or
novelty.
