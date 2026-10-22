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
