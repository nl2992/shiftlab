# Additional source adapters (2026-10-19)

This extends the earlier data-foundation snapshot. Schema 1.1.0 adds optional structured input
references; existing 1.0 manifests remain readable. These changes do not claim completion of
the entire Phase 1 brief or introduce new research algorithms.

## Commands

```bash
uv sync --extra dev --extra data-sources --extra neural --extra wilds
uv run python scripts/download_data.py --dataset monash --config configs/data/public/monash.yaml --execute
uv run python scripts/download_data.py --dataset eia --config configs/data/public/eia.yaml --execute
uv run python scripts/download_data.py --dataset eia --config configs/data/public/eia_bulk.yaml --execute
uv run python scripts/download_data.py --dataset eia --config configs/data/public/eia_bulk_multi.yaml --execute
uv run python scripts/download_data.py --dataset fred --config configs/data/finance/fred.yaml --execute
uv run python scripts/download_data.py --dataset wilds --config configs/data/public/wilds.yaml --execute
uv run pytest tests/data/test_acquisition_extensions.py tests/data/test_wilds_package.py -q
```

## Contracts and verification

EIA API v2 requires `EIA_API_KEY`; FRED/ALFRED requires `FRED_API_KEY`. Configure them locally,
never in YAML or Git. The official EIA bulk-download facility does not require an API key. The
opt-in EBA path downloads its approximately 700 MB compressed archive only when `--execute` is
provided and requires an explicit byte budget. It streams JSON lines and retains only selected
UTC hourly series and date ranges. The committed example config selects three years for NYIS,
then assigns retrospective event-time splits and purges rows whose one-hour target crosses a
split boundary. `eia_bulk_multi.yaml` reuses the same checksummed archive for CISO and ERCO; its
combined 52,606 rows have 26,303 observations per respondent and six boundary purges. The
three-authority train-only diagnostic is in
`data/reports/acquisition_extensions.json`; its retrospective Ridge comparison is included in
`data/reports/time_series_real_diagnostics.json`. Unknown source release timing is still not
inferred.
EIA API responses use bounded pagination, retries and immutable snapshots. Credential echoes are
scrubbed before storage. Receipts distinguish publisher-byte hashes from stored sanitized-file
hashes. Fixtures verify formats and transport.

EIA preserves balancing-authority demand, forecast, generation, interchange and source units.
Calendar gaps are excluded from fixed-horizon pairs. Retrospective splits use event time and purge
cross-boundary outcomes; they do not imply historical feature or label availability. FRED
preserves every returned revision interval; `asof_vintage` excludes future
revisions. Date-only release metadata has an explicit conservative end-of-day assumption;
intraday release time is not fabricated. The revision table is not a ready forecasting design.

Monash supports verified M4 hourly/daily/weekly, electricity-hourly and weather record versions.
TSF attributes, missingness, frequency and declared official horizons are preserved. Every
holdout step uses the same training-only forecast origin. Deterministic series subsets are
identified as subsets, not full competition results. Source start dates do not establish
observation or release times. M4 hourly, weekly and daily subsets have been executed. The
electricity-hourly and weather Zenodo archives were downloaded, but their TSF headers omit
`@horizon`; conversion is refused until an authoritative forecasting horizon is supplied. We do
not substitute commonly used benchmark horizons for a source-declared horizon. Run
`python -m uv run python scripts/monash_report.py` to regenerate per-record checksums, header
evidence, split counts and processed-manifest hashes in `data/reports/monash_execution.json`.

WILDS adapters cover CivilComments, Amazon, FMoW, iWildCam and Camelyon17. Official partitions and
metadata stay intact. CivilComments text is stored separately from targets. The official CodaLab
host currently fails TLS certificate validation, so the full raw 448,000-row parquet mirror from
`pietrolesci/civilcomments-wilds` is pinned by revision and SHA-256, with official split counts
checked before export. Use its `raw/` file only: the mirror's processed default drops repeated
text rows and is not the full benchmark. The source is CC0 as documented by WILDS; the mirror is
a transport alternative, not a replacement dataset. Other inputs refer
to an existing official installation; export never decodes images. `load_input` loads one input.
The official WILDS package supplies metric definitions. If compiled torch_scatter is unavailable,
only arithmetic group means use an equivalent native torch reduction; the returned description
identifies this backend. No installed package files or package globals are changed. Pandas 3
compatibility is scoped to official dataset construction. A generated local fixture exercises
the genuine WILDS 2.0 constructor, exported references and metric evaluator.

Criteo imports separate click time, conversion event time and outcome availability. Outcomes,
conversion revenue and delay cannot be features. Delay units must come from a verified README
or export specification. Negatives without complete follow-up retain unknown availability.
Instantaneous click-feature delivery is an explicit assumption when selected. The publisher's
90-day sponsored-search archive is distinct from its 1TB click-log benchmark and CriteoPrivateAds.
The old sponsored-search archive URL was unavailable in our environment; the Reddit report that
the 1TB benchmark mirror was fixed is consistent with the current official CriteoClickLogs listing,
but that click-only corpus does not contain conversion-delay labels. Separately, the complete
official CriteoPrivateAds snapshot is acquired at pinned revision
`343645889b157f104ac23d0d07afa6a18115eb30`: 288 files, 30 day partitions, 103,862,032 rows,
34,029,639,414 bytes, one stable Parquet schema, and all publisher SHA-256 values verified. Its
100M-impression, 30-day design includes click, landing, visit and sale outcomes; Criteo documents
click/sale event delays in minutes. The Parquet schema exposes delay arrays for click, landed-click
and sale outcomes. It is a distinct delayed-feedback source, not a substitute for sponsored-search
records. `source_manifest.json` records the file inventory and metadata-only structural checks.
See `scripts/acquire_criteo_private_ad.py`.

## Observed external limitations

- FRED: a credentialed live five-series vintage/revision extract (UNRATE, CPIAUCSL, FEDFUNDS,
  DGS10 and GDPC1) for 2022-01 through 2023-12 was acquired as 630 rows. The real-time vintage
  window matches the observation window to stay below the publisher's vintage-date query limit.
  The caller-supplied key was used only through `FRED_API_KEY` for that process and was not saved
  in source data, configuration or reports. The exact release instant remains unknown; the adapter
  records conservative date-resolution availability. EIA API-key access is not configured, while
  the real NYIS subset is acquired from the official keyless bulk archive.
- CivilComments: the official CodaLab host fails certificate validation. TLS verification stays
  enabled. The complete raw mirror was acquired and verified instead; see the WILDS section above.
  [Upstream issue](https://github.com/p-lambda/wilds/issues/173) records the outage.
- Criteo: rechecked the official landing page and linked archive on 2026-10-20. The landing page
  still documents the 90-day click/conversion sample and CC BY-NC-SA 4.0 terms; its linked `go.criteo.net`
  archive currently returns HTTP 404 to this host, and the named Azure Blob hostname returns DNS
  NXDOMAIN. No archive bytes were acquired and no unrelated click dataset or unofficial mirror was
  substituted. The latest probe is recorded separately in `acquisition_extensions.json`.

Timestamped outcomes are recorded in `data/reports/acquisition_extensions.json`.

Primary references: [EIA API](https://www.eia.gov/opendata/documentation.php),
[EIA bulk downloads](https://www.eia.gov/opendata/bulk-downloads.php),
[EIA bulk format and manifest](https://www.eia.gov/opendata/v1/bulkfiles.php),
[EIA copyrights and reuse](https://www.eia.gov/about/copyrights_reuse.php),
[FRED observations/vintages](https://fred.stlouisfed.org/docs/api/fred/series_observations.html),
[Monash repository](https://forecastingdata.org/),
[WILDS](https://github.com/p-lambda/wilds),
[Criteo source and terms](https://ailab.criteo.com/criteo-sponsored-search-conversion-log-dataset/).
