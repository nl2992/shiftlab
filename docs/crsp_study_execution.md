# CRSP ShiftLab study: execution plan

## Objective

Create a reproducible, retrospective daily U.S. common-equity panel from WRDS CRSP
Stock Version 2/CIZ, then use it to evaluate shift detection, conformal prediction,
and model adaptation on next-trading-day returns. The data supports empirical
forecasting and regime analysis; it does not supply operational decision utility.

## Extraction specification

- WRDS table: `crspq.wrds_dsfv2_query`
- Dates: 2000-01-01 through 2025-12-31, inclusive
- Universe: `securitytype=EQTY`, `securitysubtype=COM`, `sharetype=NS`, and
  `primaryexch` in `A, B, I, N, Q, R`
- Keep historical delistings and every trading/return quality flag. Do not filter
  on current active status or drop missing-return reasons during acquisition.
- Deduplicate only exact duplicates across the selected output columns with
  `SELECT DISTINCT`; retain the strict `(permno, dlycaldt)` uniqueness check so
  conflicting same-day records fail visibly.
- Output: one `year=YYYY` directory per calendar year, chunked compressed CSVs,
  plus a per-year manifest with query hash and file SHA-256 checksums.

The extractor is `scripts/extract_crsp_ciz_wrds_cloud.py`. Its default output is
`~/shiftlab_crsp_ciz_2000_2025_verified` in the WRDS Cloud home directory.

## Run prompt for the WRDS Cloud agent

> Continue the ShiftLab CRSP CIZ extraction in the currently authenticated WRDS
> Cloud JupyterLab session. First inspect the active kernel and current cell state.
> If an extraction cell is already running, do not start another; monitor that
> run until it finishes. If no extraction is running, upload and run
> `extract_crsp_ciz_wrds_cloud.py` with output
> `~/shiftlab_crsp_ciz_2000_2025_verified` and the default 2000–2025 range.
> Preserve the current filters and script. Let each year publish only after its
> manifest is written. At completion, verify all 26 annual manifests and every
> file checksum. Report only annual row counts, total row count, completed/failed
> years, manifest/checksum results, output path, and script SHA-256. Do not print
> dataset observations. If an error occurs, preserve the partial staging output
> and report the year and traceback; do not delete or overwrite it.

If a fresh run is needed, execute this notebook cell after uploading the script:

```python
%run extract_crsp_ciz_wrds_cloud.py --output ~/shiftlab_crsp_ciz_2000_2025_verified
```

## Extraction completion criteria

The extraction is complete only when all criteria pass:

1. All 26 years from 2000 through 2025 have a `manifest.json` and at least one
   nonempty output part.
2. Each manifest's row count equals the sum of its output-part row counts; the
   sum across manifests equals the reported total.
3. Every output part matches its manifest SHA-256; no missing, extra, or partial
   files remain in published year directories.
4. Dates stay within their year, and every row satisfies the documented
   security-type and exchange filters.
5. `(permno, dlycaldt)` is unique after exact-projection deduplication. Any
   non-identical duplicate key is a hard failure, not a row to discard.
6. The query hash and script SHA-256 are recorded with the run results.

## Build the derived study panel

The WRDS download is the raw source extract. Build the standardized next-observed-return panel
after all 26 years and their manifests have been restored:

```powershell
uv run python scripts/build_crsp_study_panel.py `
  --raw-root data/raw/licensed/crsp --root data --chunk-rows 100000
```

The builder verifies all annual query hashes, every part checksum, row counts, source filters,
and strict `(permno, dlycaldt)` order before processing. It processes chunks without loading the
full 32-million-row source into memory, and handles securities whose next observation occurs in a
later calendar year. It stores the immutable panel under
`data/processed/crsp_ciz_next_day/<version>/` and writes
`data/reports/crsp_study_panel_validation.json` with row counts and SHA-256 values.

The target is the immediately next observed `dlyret` for the same PERMNO. A row is retained only
when that next return is finite, its `dlyretmissflg` is `NA` (documented as not missing), and its
`dlyretdurflg` is `D1`, `D2`, `D3`, `D4`, or `DU` (a one-trading-day return). An invalid immediate
next observation is not skipped to find a later return. Historical delisting observations remain
in the panel when they meet this mask; original current and target quality flags are retained as
audit columns. Predictor features are same-date returns, log absolute price, log volume, log market
capitalization, log trade count, and CRSP market-index returns. Missing predictor values remain
missing in the panel and are median-imputed using the training split only in the smoke model.

Splits use prediction-date years: train 2000–2014, validation 2015–2017, calibration 2018–2019,
and test 2020–2025. A row whose target date enters a different split is marked `unassigned`; it is
not used in any split. The panel clock orders features at the daily close and the prediction after
that close, with the next return observed at its target-date close. This is a retrospective daily
ordering convention, **not a verified history of when CRSP data became available to market
participants**. Do not present it as real-time replay evidence.

## Smoke analysis

After building the panel, run the reproducible 100-security smoke cohort:

```powershell
uv run python scripts/smoke_crsp_study.py --root data --securities 100 `
  --seed 20261022 --output data/reports/crsp_study_smoke.json
```

The cohort is selected with a fixed seed from PERMNOs represented in all four splits. It checks
that feature imputation and scaling fit on training data only, uses a mean predictor as a baseline,
and calculates a descriptive 90% split-conformal radius on the calibration partition. The report
includes the panel version and checksums, sampled row counts, aggregate test errors, and per-year
RMSE. This survivor cohort and single run are pipeline checks only; they are not population
inference or evidence for a strategy, application utility, causal shift, or online guarantee.

### Initial smoke result and experiment scope (2026-10-22)

The committed-panel smoke run used 100 sampled PERMNOs (3,204 eligible across all splits), with
270,236 training rows, 74,978 validation rows, 50,122 calibration rows, and 133,505 test rows.
The training-mean baseline had test RMSE 0.041419 and MAE 0.021687; Ridge had RMSE 0.041351 and
MAE 0.021683. The error difference is very small and changes sign by test year. A calibration
radius targeting 90% covered 86.3% of test rows in this selected cohort. Exact metrics, annual
breakdown, panel hashes, and limitations are recorded in `data/reports/crsp_study_smoke.json`.

This supports the following next-experiment choices:

- **Paper 2 (conformal):** the best candidate for a larger CRSP case study. Compare fixed and
  rolling calibration over predeclared contiguous test blocks, with security/time-block uncertainty
  and clear retrospective language. The smoke coverage shortfall motivates investigation; it does
  not by itself establish a coverage failure or a benefit from adaptation.
- **Paper 1 (decision drift):** keep confirmatory claims on synthetic data with known shift times.
  CRSP has no known causal changepoints and no supplied decision utility, so market-period alarms
  can be descriptive only.
- **Paper 3 (cost-aware adaptation):** do not launch a large CRSP adaptation sweep from this smoke
  alone. Predictive improvement over the mean baseline is negligible and there is no source-grounded
  retraining or trading utility. Use the controlled synthetic suite for confirmatory adaptation
  comparisons; consider CRSP as a secondary retrospective sensitivity analysis after fixing a
  research cost schedule.

Repeated random seeds are not the right uncertainty method for a fixed historical CRSP panel. For
real-data inference, prioritize chronological blocks, security-level cohort checks, and
dependence-aware resampling. Use paired independent DGP seeds for the synthetic confirmatory runs
specified by each paper protocol.

## Study flow after extraction

1. Process each security in `permno, dlycaldt` order. Define
   `next_day_return` as the next observed `dlyret` within the same PERMNO, and
   retain the corresponding target date. Do not shift targets across securities.
2. Use only information available at prediction time. Build lagged return,
   price, volume, market-capitalization, and market-index features; exclude
   future target values and rows with invalid target flags according to a
   separately documented rule.
3. Start with chronological partitions: train 2000–2014, validation 2015–2017,
   calibration 2018–2019, and test 2020–2025. Purge any row whose target date
   falls outside its assigned partition. Fit preprocessing on training data
   only. Treat this as retrospective daily replay because CRSP does not provide
   verified intraday release times for these fields.
4. Run frozen, recalibrated, and retrained baselines on the same eligible rows.
   Keep synthetic known-shift controls as the source of ground-truth change
   labels; CRSP regimes are empirical diagnostics, not known causal shift labels.

## Objective study outputs

Report results by time block and, where appropriate, market regime:

- Shift detection: false alarms per 1,000 trading days, detection delay where
  regime boundaries are predeclared, and forecast-loss change after alerts.
- Conformal prediction: nominal 90% interval coverage, block-bootstrap 95%
  confidence intervals, and mean/median interval width.
- Adaptation: next-day return MSE and MAE, cumulative loss, update counts, and
  the loss-versus-compute-cost Pareto frontier for frozen, recalibrated, and
  retrained policies.
- Always include a frozen baseline and the stationary synthetic null controls.
  No model-advantage threshold is assumed in advance; the scientific result may
  be that an intervention does not help. No causal or operational utility claim
  follows from retrospective CRSP data alone.
