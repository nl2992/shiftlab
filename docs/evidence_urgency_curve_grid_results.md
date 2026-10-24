# Evidence-directed urgency-curve grid: development results

**Protocol:** [`evidence_urgency_curve_grid_protocol.md`](evidence_urgency_curve_grid_protocol.md)
**Run:** [`outputs/evidence_urgency_curve_grid_30/`](../outputs/evidence_urgency_curve_grid_30/)
**Status:** Exploratory grid search. No candidate advanced to confirmation.

## Run validation

The run evaluated nine evidence curves and uniform querying over 30 seeds in each of three
scenarios: stationary, benign nuisance, and boundary-local harm. This produced 900 method-stream
rows on CUDA. All rows respected their shared pathwise dollar caps; all 30 boundary-harm onsets were
reached for every method. Both query-policy methods used the same seed-level random uniforms, cost
support, 10% target dollar rate, and common e-process bound (`q_min=0.05`). No figure was generated
because PaperBanana was not available in the active environment.

## Boundary-harm results

| Method | Activation `a` | Power `gamma` | Mean query rate | Mean spend | Mean labels | Mean events | Stream-mean RMSE | Detected / reached |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform | — | — | 0.1000 | 350.52 | 233.8 | 2,321 | 0.0759 | 0/30 |
| Evidence curve | 0.000 | 0.5 | 0.0810 | 289.77 | 194.2 | 2,390 | 0.0971 | 0/30 |
| Evidence curve | 0.000 | 1 | 0.0662 | 240.19 | 161.0 | 2,400 | 0.1083 | 0/30 |
| Evidence curve | 0.000 | 2 | 0.0549 | 199.12 | 133.3 | 2,400 | 0.1124 | 0/30 |
| Evidence curve | 0.025 | 0.5 | 0.0918 | 326.59 | 218.4 | 2,364 | 0.0803 | 0/30 |
| Evidence curve | 0.025 | 1 | 0.0688 | 249.77 | 167.1 | 2,400 | 0.1035 | 0/30 |
| Evidence curve | 0.025 | 2 | 0.0556 | 202.54 | 135.6 | 2,400 | 0.1100 | 0/30 |
| Evidence curve | 0.050 | 0.5 | 0.0989 | 345.97 | 231.4 | 2,323 | 0.0662 | 0/30 |
| Evidence curve | 0.050 | 1 | 0.0734 | 265.54 | 177.6 | 2,400 | 0.0957 | 0/30 |
| Evidence curve | 0.050 | 2 | 0.0570 | 207.19 | 138.6 | 2,400 | 0.1097 | 0/30 |

Every method detected 0/30 material-harm streams, even though all onsets were reached. Uniform
sampling also detected 0/30, so this grid does not rank the methods by power. No curve improved the
registered primary detection count. The best numerical RMSE candidate, `a=0.05, gamma=0.5`, had
paired RMSE difference `-0.0097` versus uniform (95% seed-bootstrap interval `[-0.0241, 0.0054]`),
paired spend difference `-$4.54`, and `-2.3` labels. The interval includes zero, and the spend
difference is small; this is not evidence of a practically meaningful improvement. It is also
nearly uniform querying (`mean q=0.0989`).

All methods had 0/30 false escalations in each null scenario. These small descriptive counts do not
calibrate the false-alarm rate. The results show a tradeoff in this implementation: convex evidence
curves conserve labels but have higher stream-mean error; the concave curve that approached uniform
had the best numerical error but no detection advantage. **Do not promote any curve.**

## Decision and next milestone

Stop tuning this nine-cell curve family at the 10% cap. Because even uniform sampling detected no
harm, its zero signal prevents a useful allocation ranking. The next informative experiment is a
fresh, frozen comparison at the previously studied 20% cap, where the monitor has shown nonzero
boundary-harm detection, using uniform plus only the near-uniform concave curve and the cost-aware
Neyman and cost-stabilized baselines. Match the fixed e-process bound and actual dollar cap, and
include sufficient fresh seeds to estimate paired differences. Keep all null calibration separate;
if the monitor again has no power, diagnose the harm signal and horizon before searching more
allocation curves.

The results are not a theorem, a false-alarm certification, or a novelty claim. See the seed-level
Parquet, summaries, paired contrasts, report, and hashes in the run directory. Reproduce using the
command in the protocol.
