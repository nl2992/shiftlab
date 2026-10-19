# Phase 1 execution summary

Executed on 2026-10-19. Full suite: **132 passed**. CUDA-hidden data suite: **117 passed, 1 skipped**. Ruff, formatting, scoped mypy and locked environment sync passed.

## Implemented and exercised

- 41 registered synthetic mechanisms and nine composable temporal patterns. All mechanisms have reproducibility, contract and replicated oracle-risk tests; selected distributions also have replicated moment/quantile/autocorrelation checks.
- Nine synthetic mechanisms have persistent smoke datasets, including a changing-feedback stream. A CUDA float32 stream was also written to Parquet.
- Five real sources acquired: UCI Gas Sensor Drift, Folktables ACSIncome NJ 2018, OPSD German hourly 2018, NOAA JFK 2023, and Binance BTCUSDT January 2023 daily bars.
- All three existing research tracks executed on the same stored concept-shift regression dataset through the new benchmark bridge.
- Forty-two immutable stored versions passed validation. Multiple historical processing configurations are retained; these are not forty-two independent scientific replicates.
- CPU/CUDA moment parity, exact same-input affine preprocessing parity and backend reproducibility passed on the RTX 4060 laptop GPU.

## Actual shared-data baseline results

| Paper | Method | Test MSE | Coverage | Objective |
|---|---|---:|---:|---:|
| 1 | frozen | 0.93810 | 0.4757 | 2814.308 |
| 2 | fixed | 0.93810 | 0.4757 | 2814.308 |
| 2 | rolling | 0.93810 | 0.8970 | 2814.308 |
| 3 | frozen | 0.93810 | 0.4757 | 2814.308 |
| 3 | periodic | 0.13359 | 0.8847 | 450.764 |
| 3 | triggered | 0.12348 | 0.8853 | 390.436 |

These are one-stream integration results, not comparative scientific conclusions. Fixed/rolling coverage uses arrived feedback; objectives use squared loss plus an imposed per-refit cost.

## Artifacts and reproducibility

- [Quality and invalidation report](data_quality_report.md)
- [Synthetic validation](synthetic_validation.md)
- [Experiment readiness](experiment_readiness.md)
- [Inventory](data_inventory.csv)
- [Manifests and provenance](dataset_manifest.json)
- [Shift evidence and block-bootstrap intervals](shift_diagnostics.csv)
- [Generation throughput](gpu_benchmark.csv)
- [Benchmark configuration and environment](gpu_benchmark.manifest.json)

The first OPSD version had an epoch-unit conversion error and is explicitly invalidated. Its original payload and manifest remain archived. Corrected versions and regression tests use UTC epoch seconds and preserve local daylight-saving offsets.

Reports are snapshots from actual local execution. Raw/processed observations and the machine-local active manifest index are ignored by Git. Fresh clones must run generation/acquisition commands before validating local datasets. Historical report manifests remain portable provenance snapshots.

## Explicitly unfinished

EIA, FRED/ALFRED, Monash, WILDS and Criteo adapters remain deferred with visible catalogue statuses. No credentials or restricted feeds were bypassed. Real release-latency/vintage reconstruction, daily OPSD tasks, richer domain-stratified classifier evaluation, bounded position sizing and dynamic adaptation oracle controllers are not implemented. GPU large-grid and 30-seed medium suites are optional and were not materialized. No novel detector or adaptation method, guaranteed nonstationary coverage, or new theoretical result is claimed.
