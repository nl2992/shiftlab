# EIA-930 F8 profile decision

**Disposition: F8 transfer not tested; frozen model pair mismatches the target.** This is a
dataset/model-pair development result, not an algorithm result. The run stopped before constructing
policy episodes or computing any method costs.

## Source and paired model profile

The official EIA-930 balance files provide hourly UTC demand, the operator's day-ahead forecast,
and an imputation field. Six files covering 2021–2023 are listed and SHA-256 hashed in
`source_manifest.json`; local raw files are excluded from Git. EIA documents the nominal forecast
and actual-demand availability schedule, but historical values can be revised. This profile uses
retrospective values and a simulated one-hour label release.

The protocol fixed each BA's 2021 90th-percentile demand threshold, one-day persistence incumbent,
and official day-ahead forecast challenger. For the 2022–2023 development window:

| BA | Eligible events | 2,000-hour episodes | Disagreement rate | Challenger correct on disagreements | F8 profile match |
|---|---:|---:|---:|---:|---|
| PJM | 17,424 | 6 | 0.0575 | 0.7046 | no |
| ERCO | 17,520 | 8 | 0.0342 | 0.7613 | no |
| CISO | 17,510 | 7 | 0.0306 | 0.5869 | no |

F8 required disagreement frequency in `[0.01, 0.05]` and challenger correctness on at least
`0.85` of disagreements, in at least two registered BA clusters. Zero BAs met both conditions.
Therefore the runner did not compare PFA-SR, CAMS, or other policies and reports no net-cost or
performance result. The precise profile and stop marker are `DATASET_PROFILE.json` and
`RUN_STOPPED_BEFORE_POLICIES.json`.

## Scope and next step

This does not reject EIA-930 as a chronological dataset or the Failure Atlas question. It rejects
this prespecified pair as an F8 instance. The BAs are correlated subclusters under one provider, so
even a passing result would require an independent source for a generalization claim.

The next bounded development step is to fit a second, stronger forecasting classifier using only
the 2021 training period and assess its F8 profile on the already designated 2022–2023 development
window. If that pair passes, freeze a new method comparison before opening the currently untouched
2024–2025 interval. A future positive result would still require an independent provider/domain and
must describe the label-release clock as simulated.

## Runner integrity

The first run's timestamp segmentation used incompatible microsecond and nanosecond units and
created no policy rows; the correction and exact failed attempt are recorded in
`STREAM_RUN_ATTEMPT.md`. The corrected run reproduced the paired stream, wrote the profile, and
stopped before policy evaluation. All raw response hashes are preserved in `source_manifest.json`.
