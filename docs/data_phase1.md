# Data framework: implementation and reproducibility

The existing `shiftlab.data.make_stream` API and the three benchmark tracks remain available.
`shiftlab.data` is now a package with versioned contracts, streaming messages, immutable
Parquet datasets, checksummed raw acquisition, a scenario registry, optional CUDA generation,
and executable reports. No new research algorithm is implemented.

## Exact commands

Run from the repository root with Python 3.11+:

```bash
uv sync --extra dev
uv run pytest -q
uv run python scripts/data_inventory.py
uv run python scripts/generate_synthetic.py --config configs/data/synthetic/smoke.yaml
uv run python scripts/download_data.py --dataset gas_sensor
uv run python scripts/download_data.py --dataset gas_sensor --execute
uv run python scripts/download_data.py --dataset opsd --config configs/data/public/opsd.yaml --execute
uv run python scripts/download_data.py --dataset noaa --config configs/data/public/noaa.yaml --execute
uv sync --extra dev --extra data-sources
uv run --extra data-sources python scripts/download_data.py --dataset folktables --config configs/data/public/folktables.yaml --execute
uv run python scripts/download_data.py --dataset binance --config configs/data/finance/binance.yaml --execute
uv run python scripts/validate_datasets.py
uv run python scripts/build_data_report.py
uv run pytest tests/data/ -q
```

All download commands default to dry-run; `--execute` allows acquisition. Source failures are
errors, never replaced by synthetic or unrelated data. EIA, FRED/ALFRED, Monash, WILDS and Criteo
have explicit deferred/credential/terms statuses in the catalogue. Their download commands
describe the status in dry-run and fail explicitly on execution. There are no placeholder adapters.

For this NVIDIA Windows machine:

```bash
uv sync --extra dev --extra data-sources --extra neural
uv run --extra neural python scripts/generate_synthetic.py --config configs/data/synthetic/gpu_smoke.yaml --device cuda
uv run --extra neural python scripts/benchmark_generation.py --config configs/data/synthetic/benchmark.yaml
# Optional, approximately 1 GB just for uncompressed float32 features:
uv run --extra neural python scripts/generate_synthetic.py --config configs/data/synthetic/gpu_large.yaml --device cuda
```

The neural extra pins a CUDA 13.0 PyTorch build from the official PyTorch index. A compatible
driver is required; base CPU installation does not install torch. CUDA requests fail clearly
if unavailable. `auto` resolves the actual backend before computing a dataset identity.
Independent NumPy and torch RNGs provide distributional parity, not matching random arrays.
Float32/64 refer to feature generation; oracle arithmetic may use float64. Chunk size is part
of the identity and RNG trajectory. Memory budgets bound feature chunks and intermediates;
the regime schedule uses O(n) memory. Stateful temporal recurrences and oracle calculations
run on CPU; torch generates vectorized latent arrays on CUDA. Affine preprocessing can also
apply training-fitted parameters on CUDA. Arrow compression and disk writes are on CPU.
Benchmark scopes include host transfer and DataFrame assembly, excluding disk writes.

## Data contract and observability

Schema 1.0.0 stores stable sample IDs, optional entity/domain IDs, event time, feature
availability, prediction time, outcome event time, label availability, features, target,
optional regime, decision context, weights, split, and provenance. Times are simulation indices
for synthetic data, UTC epoch seconds for timestamped real data, and null where not known.
Real original timestamps, offsets, flags and source fields remain in metadata or raw files.

Read Parquet only in evaluator/acquisition code. `data.streaming.replay` yields immutable
`Request` and `Label` messages, excluding targets, regimes and oracles from requests. Features
must be available by prediction time. Requests at equal timestamps precede feedback at that
timestamp. Pending labels beyond the prediction horizon are not flushed into online learners.
Unknown label availability withholds labels. Unknown prediction/feature availability blocks
replay rather than inventing timestamps. This API is not a sandbox against malicious Python
code reading arbitrary files. Oracle files are physically separated in `evaluator_only/`.

Training-only scaling and horizon-safe lag construction are implemented. Synthetic partition
boundaries are fixed at 50%, 65%, and 80%; labels that arrive across the next partition boundary
are marked unassigned. Partitioning is based on time groups, preserving simultaneous samples.
Calibration/test utilities must still respect the replay protocol rather than reading stored
evaluator targets directly. No source missingness is silently forward-filled.

## Synthetic scope

The registry implements 41 explicit mechanisms (see `synthetic_catalogue.md`) across iid and
dependent controls, covariance/mixture changes, class prior shift, label corruption, conditional
mean and variance changes, heavy/asymmetric tails, local decision changes, costs, constraints,
feedback availability and resource-cost schedules. Nine temporal patterns compose with these:
abrupt, multiple, linear, sigmoid, recurring, binary HMM, seasonal, temporary and variable dwell.
Gradual changes record intervals, not artificial point changepoints. `regimes` controls segment
count for multiple/recurring/variable-dwell patterns; the HMM always has two states. Regimes=1
suppresses exogenous changes. Parameter values are configurable; presets avoid Cartesian grids.
The medium plan uses 30 seeds; the optional large plan is never materialized automatically.

Regression uses a sign-based decision with false-negative/positive costs; classification uses
its Bernoulli posterior. Costs and constraints are synthetic research utilities. Oracle actions
minimize their known conditional expected loss, subject to feasibility. Hidden-cost worlds
illustrate non-identifiability: identical X/Y laws can imply different actions if undisclosed
utilities differ. No feature-only detector can resolve that example.

Normal, Student-t and centered-lognormal residual probabilities and 90% absolute-error radii
are analytical or numerically inverted from the exact CDF. Mixture CDFs are inverted by bounded
bisection; classification interval radii are unavailable rather than substituted. Dependent
error radii are explicitly marginal, not conditional on the learner's full history. No formal
coverage guarantee under arbitrary nonstationarity follows from these calculations.

An interactive performative environment separately models action-induced feature/target
feedback and joint actions from several predictors. It is not an exogenous precomputed stream.
Its documented stability condition concerns linear feedback. Performance-degrading model
updates, adversarial schedules, dynamic budgeted oracle controllers and application-specific
optimal interventions are deferred; saved manifests state that no dynamic oracle is implemented.
Resource-cost metadata do not establish optimal interventions. Capacity, cost-sensitive binary
and abstention decisions plus forecasting, quantile-response, volatility and threshold tasks
are implemented. Bounded position sizing and general multiclass decision costs are deferred.

## Real acquisition status and limitations

- UCI Gas: all ten batches, 13,910 rows and 128 features. Batch order is preserved, within-batch
  order unknown. Batch groups are not verified changepoints. The source page has conflicting
  CC BY 4.0 and research-only wording; both are recorded and commercial use is not assumed.
- Folktables: ACSIncome, New Jersey, 2018, with 47,781 retained rows, demographic group metadata
  and survey weights. The adapter supports the five requested tasks, one per dataset version,
  and selected state/year lists. Only this modest configuration was acquired and exercised.
  Within-year order and release times are unknown, so sequential replay remains unavailable.
- OPSD: version 2020-10-06 raw hourly CSV and datapackage; selected 2018 German load, wind,
  solar, with 8,759 next-hour rows. Source missingness and UTC/CET-CEST strings are retained.
  Release latency and revisions are unknown; this is a retrospective task, not real-time-ready.
  An early processed version used the wrong epoch unit; it is explicitly invalidated in the
  quality report and its original files/manifest are retained outside the active catalogue.
  Regression tests cover UTC seconds and daylight-saving offset preservation.
  Package metadata do not supply a blanket license; source-specific terms require review before
  redistribution. No price or daily task is silently claimed as evaluated.
- NOAA: JFK station 74486094789, 2023; 13,422 next-record temperature rows. Temperature/dewpoint
  sentinels are decoded and original measurement/quality strings retained. Records can be
  irregular, so the target is next recorded observation, not automatically next hour.
  Historical publication latency is unknown. The original URL returned HTML; that payload
  remains in raw storage but is not included as the processed dataset's source data.
- Binance: a tiny monthly daily-bar adapter verifies publisher SHA256 checksums and detects
  timestamp precision. OHLCV features require bar close; release timestamps remain unknown.
- Licensed-local imports require explicit license, feature/target mappings and optional time
  mappings. Original contracts, quotes and quality columns remain in metadata. No restricted
  feed is accessed, and licensed raw/processed observations are excluded from version control.

Official references: [UCI Gas](https://archive.ics.uci.edu/dataset/224/gas+sensor+array+drift+dataset),
[OPSD](https://data.open-power-system-data.org/time_series/2020-10-06/),
[NOAA ISD](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database),
[Folktables](https://github.com/socialfoundations/folktables),
[Binance public data](https://github.com/binance/binance-public-data).

## Artifacts, validation and outstanding work

Version directories contain observations.parquet, dataset_manifest.json, and (synthetic only)
evaluator_only/oracle.parquet and dgp.json. Version hashes include configuration, source hash,
Git commit and raw checksums. Repeating a version validates existing checksums and reuses it;
corrupt versions fail, and failed temporary directories are retained for diagnosis. Raw downloads
have acquisition receipts, byte limits, retries, timeouts, range resume, and optional publisher
checksum validation. Existing raw versions are never silently replaced. A received checksum
from the same publisher is an integrity check, not independent authenticity evidence.

`data/reports/` contains inventory, aggregate manifests, quality, synthetic validation,
shift evidence, GPU throughput, readiness and actual diagnostic plots. Local raw and processed
datasets are ignored by Git. Reports include no record-level proprietary observations.
Schema/checksum failures fail validation. Duplicates, missingness, range, temporal overlap,
class frequencies, feature means, covariance, KS evidence and offline regression baselines are
reported without attributing concept drift. Multiple seeds test each generator's Bayes-risk
reference; further replicated tests check moments, class priors, quantiles and autocorrelation.

Moving-block bootstrap intervals for first/last-window feature means are implemented under explicit
within-window stationarity and weak-dependence assumptions. They do not correct confounding,
missing-data selection or multiple comparisons.

Domain-stratified classifier comparisons, causal drift
attribution, revision-aware release reconstruction, daily OPSD tasks, the remaining source
adapters and exhaustive selected GPU parameter sweeps remain unfinished. The minimum working
data foundation exceeds four synthetic classes and three acquired real sources, but this is
not a claim that every item in the comprehensive roadmap is complete.
