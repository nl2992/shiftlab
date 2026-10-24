# Evidence-directed allocation at a 20% hard budget: results

**Protocol:** [`evidence_budget20_comparison_protocol.md`](evidence_budget20_comparison_protocol.md)
**Run:** [`outputs/evidence_budget20_comparison_60/`](../outputs/evidence_budget20_comparison_60/)
**Status:** Fresh-seed comparison complete. The evidence-directed candidate does not advance.

## Validation

The CUDA run evaluated 60 fresh seeds in each of stationary, benign-nuisance, and boundary-local
harm scenarios, with five methods per seed (900 rows). Every method respected its pathwise dollar
cap; caps were identical within each scenario and seed. All 60 boundary-harm onsets were reached by
every method. The exported metrics contain no evaluator probability or expected-cost truth columns.
The manifest's artifact and source hashes validate. No figure was generated because PaperBanana
was unavailable.

## Boundary-harm comparison

| Method | Detected / 60 (exact 95% interval) | Reached | Mean spend / cap | Mean labels | Processed horizon | Stream-mean RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 6/60 (3.8%–20.5%) | 60/60 | 704.81 / 720.51 | 469.8 | 0.982 | 0.0504 |
| Evidence curve (`a=0.05`, `gamma=0.5`) | 4/60 (1.9%–16.2%) | 60/60 | 691.57 / 720.51 | 461.5 | 0.979 | 0.0542 |
| Variance | 3/60 (1.0%–13.9%) | 60/60 | 707.08 / 720.51 | 472.7 | 0.971 | 0.0546 |
| Cost-aware Neyman | 2/60 (0.4%–11.5%) | 60/60 | 707.79 / 720.51 | 494.5 | 0.972 | 0.0549 |
| Cost-stabilized Neyman | 5/60 (2.8%–18.4%) | 60/60 | 707.05 / 720.51 | 515.7 | 0.981 | 0.0510 |

The candidate's paired detection-rate difference from uniform was **−3.3 percentage points**
(2 candidate-only versus 4 uniform-only streams; paired seed-bootstrap 95% interval
`[-11.7, +5.0]` percentage points; exact two-sided McNemar `p=0.6875`). This does not support the
registered +10-point improvement. Its mean propensity was 0.197, close to uniform's fixed 0.20.

The candidate spent $13.24 less on average than uniform (paired 95% t interval `[-$22.96, -$3.52]`)
and used 8.3 fewer labels (interval `[-14.6, -2.0]`), but its paired stream-mean RMSE difference
was `+0.0038` (95% bootstrap interval `[-0.0031, +0.0108]`). Thus the small spending reduction
does not come with a demonstrated accuracy or detection gain. Conditional detection delays are
based on only two to six detections per method and are too sparse for meaningful ranking.

All methods had zero false escalations in 60 streams for each null control. These diagnostic counts
do not constitute false-alarm calibration. Detection itself was sparse: even uniform detected only
6/60 streams. Because each onset was reached, the low rates reflect weak observed sequential
evidence under this design rather than budget censoring.

## Decision

Do not advance the evidence-directed curve. At both the 10% development cap and the fresh 20% cap,
it failed to improve detection over uniform; at 20% it had slightly fewer detections and
numerically higher RMSE, while using marginally less spend. This is a negative result for this
preselected curve under the registered synthetic design, not a general result about adaptive
querying.

The next work should diagnose the weak e-process signal and the scarcity of detections before
allocating further effort to propensity-curve tuning. Map the per-stream expected harm margin,
prediction-powered increment variance, and cumulative log-e trajectories on existing synthetic
artifacts, without using those diagnostics to alter this evaluation. Then lock a separate diagnostic
study that compares longer monitoring horizons and larger expected-harm effects against
full-feedback oracle evidence. Keep null calibration independent and use PaperBanana for any
research figures when available.

The reproducible stream-level Parquet, summary CSV, paired contrasts, generated report, and hash
manifest are stored in the run directory.
