# Retrospective time-series task diagnostics

`scripts/time_series_real_diagnostics.py` fits a simple median-impute/standardize/Ridge
regression pipeline on each domain's training partition, obtains an 80% symmetric split
residual interval from the separate calibration partition, and reports held-out test RMSE,
MAE, coverage, rolling squared loss, and paired squared-loss difference from a training-mean
baseline. A circular moving-block bootstrap summarizes uncertainty in that test loss
difference. The script does not tune on validation/test rows or pass evaluator labels into
the fitted model.

Example using the current OPSD hourly and daily tasks and expanded NOAA panel:

```powershell
python -m uv run python scripts/time_series_real_diagnostics.py --dataset-path `
  data/processed/opsd/b7f39fa513865eb14696 `
  data/processed/opsd/b659a26235aec9be4299 `
  data/processed/noaa/250db0578188e92615ea
```

The output is `data/reports/time_series_real_diagnostics.json`. The current diagnostics show
lower RMSE than the training-mean baseline on OPSD hourly and all three NOAA stations, while
the small OPSD daily task performs worse than that baseline. Empirical 80% interval coverage
ranges from 0.685 to 0.884 across these tasks. These are retrospective comparisons: label
availability is unknown for these sources, and the event-time partitions do not establish
what a forecaster could observe operationally. Moving-block intervals use a declared
`sqrt(test_n)` block length and are descriptive; sensitivity analysis remains appropriate.
The report omits decision loss because no application-grounded utility was supplied for these
continuous forecasts.
