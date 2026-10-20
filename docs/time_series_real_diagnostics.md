# Retrospective time-series task diagnostics

`scripts/time_series_real_diagnostics.py` fits a simple median-impute/standardize/Ridge
regression pipeline on each domain's training partition, obtains an 80% symmetric split
residual interval from the separate calibration partition, and reports held-out test RMSE,
MAE, coverage, rolling squared loss, and paired squared-loss difference from a training-mean
baseline. A circular moving-block bootstrap summarizes uncertainty in that test loss
difference. The script does not tune on validation/test rows or pass evaluator labels into
the fitted model.

Example using the current OPSD hourly and daily tasks, expanded NOAA panel and EIA NYIS panel:

```powershell
python -m uv run python scripts/time_series_real_diagnostics.py --dataset-path `
  data/processed/opsd/b7f39fa513865eb14696 `
  data/processed/opsd/b659a26235aec9be4299 `
  data/processed/noaa/250db0578188e92615ea `
  data/processed/eia/066f854744aea721eae5
```

The output is `data/reports/time_series_real_diagnostics.json`. The current diagnostics show
lower RMSE than the training-mean baseline on OPSD hourly, all three NOAA stations and EIA NYIS,
while the small OPSD daily task performs worse than that baseline. Empirical 80% interval
coverage ranges from 0.685 to 0.884 across these tasks. On EIA, Ridge RMSE is 641 versus 3,615
for the training-mean baseline and the empirical interval coverage is 0.719. These are
retrospective comparisons: label
availability is unknown for these sources, and the event-time partitions do not establish
what a forecaster could observe operationally. Moving-block intervals use a declared
`sqrt(test_n)` block length and are descriptive. The report also includes 95% intervals using
half, baseline, and double the baseline block length (clipped to the test length) for each task.
These are sensitivity checks, not a principled block-length selector or a correction for
model-selection uncertainty.
The report omits decision loss because no application-grounded utility was supplied for these
continuous forecasts.

## Monash official multi-step holdouts

`scripts/monash_forecast_diagnostics.py` evaluates the acquired M4 hourly, daily, and weekly
subsets using each publisher-declared fixed-origin horizon. It fits a per-series Ridge model
on the official training rows only and compares it with the last-value and training-mean
baselines. Metrics are reported by series and forecast step, with a training-only MASE scale.
It rejects a holdout if training outcomes cross the origin or if covariates vary across steps
that share one official forecast origin.

The committed report is `data/reports/monash_forecast_diagnostics.json`: horizons are 48, 14,
and 13 for hourly, daily, and weekly; mean per-series MASE for Ridge is 5.14, 4.06, and 3.36,
respectively. Ridge beats last-value MASE on 8/10 hourly, 11/20 daily, and 17/20 weekly
series. These are deterministic first-series subsets, so the entity counts are descriptive and
not population-level confidence intervals. Sequence indices do not establish actual release
times, and the results remain retrospective.
