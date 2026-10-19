# Additional source adapters (2026-10-19)

This extends the earlier data-foundation snapshot. Schema 1.1.0 adds optional structured input
references; existing 1.0 manifests remain readable. These changes do not claim completion of
the entire Phase 1 brief or introduce new research algorithms.

## Commands

```bash
uv sync --extra dev --extra data-sources --extra neural --extra wilds
uv run python scripts/download_data.py --dataset monash --config configs/data/public/monash.yaml --execute
uv run python scripts/download_data.py --dataset eia --config configs/data/public/eia.yaml --execute
uv run python scripts/download_data.py --dataset fred --config configs/data/finance/fred.yaml --execute
uv run python scripts/download_data.py --dataset wilds --config configs/data/public/wilds.yaml --execute
uv run pytest tests/data/test_acquisition_extensions.py tests/data/test_wilds_package.py -q
```

## Contracts and verification

EIA requires `EIA_API_KEY`; FRED/ALFRED requires `FRED_API_KEY`. Configure them locally, never
in YAML or Git. Responses use bounded pagination, retries and immutable snapshots. Credential
echoes are scrubbed before storage. Receipts distinguish publisher-byte hashes from stored
sanitized-file hashes. Fixtures verify formats and transport, not successful live acquisition.

EIA preserves balancing-authority demand, forecast, generation, interchange and source units.
Calendar gaps are excluded from fixed-horizon pairs. Historical publication availability stays
unknown. FRED preserves every returned revision interval; `asof_vintage` excludes future
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
metadata stay intact. CivilComments text is stored separately from targets. Other inputs refer
to an existing official installation; export never decodes images. `load_input` loads one input.
The official WILDS package supplies metric definitions. If compiled torch_scatter is unavailable,
only arithmetic group means use an equivalent native torch reduction; the returned description
identifies this backend. No installed package files or package globals are changed. Pandas 3
compatibility is scoped to official dataset construction. A generated local fixture exercises
the genuine WILDS 2.0 constructor, exported references and metric evaluator.

Criteo imports separate click time, conversion event time and outcome availability. Outcomes,
conversion revenue and delay cannot be features. Delay units must come from a verified README
or export specification. Negatives without complete follow-up retain unknown availability.
Instantaneous click-feature delivery is an explicit assumption when selected. The publisher
describes a roughly 310 MB compressed archive under CC BY-NC-SA 4.0; it is never downloaded during
installation or CI. Permitted existing local exports can be imported with `path`.

## Observed external limitations

- EIA/FRED: required API keys are absent. No live acquisition with invented credentials is claimed.
- CivilComments: the official CodaLab host fails certificate validation. TLS verification stays
  enabled. [Upstream issue](https://github.com/p-lambda/wilds/issues/173) also records the outage.
- Criteo: the publisher-linked archive returned HEAD 404 and a failed streamed GET. No unrelated
  click dataset or unofficial mirror was substituted.

Timestamped outcomes are recorded in `data/reports/acquisition_extensions.json`.

Primary references: [EIA API](https://www.eia.gov/opendata/documentation.php),
[FRED observations/vintages](https://fred.stlouisfed.org/docs/api/fred/series_observations.html),
[Monash repository](https://forecastingdata.org/),
[WILDS](https://github.com/p-lambda/wilds),
[Criteo source and terms](https://ailab.criteo.com/criteo-sponsored-search-conversion-log-dataset/).
