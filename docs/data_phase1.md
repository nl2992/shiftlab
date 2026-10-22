# Data framework: implementation and reproducibility

The existing `shiftlab.data.make_stream` API and the three benchmark tracks remain available.
`shiftlab.data` is now a package with versioned contracts, streaming messages, immutable
Parquet datasets, checksummed raw acquisition, a scenario registry, optional CUDA generation,
and executable reports. No new research algorithm is implemented.

Later extensions and their live-source limitations are in [acquisition_extensions.md](acquisition_extensions.md).
Those extensions supersede adapter-deferred statements in this earlier snapshot.

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
uv run python scripts/download_data.py --dataset eia --config configs/data/public/eia_bulk.yaml --execute
uv run python scripts/download_data.py --dataset eia --config configs/data/public/eia_bulk_multi.yaml --execute
uv sync --extra dev --extra data-sources
uv run --extra data-sources python scripts/download_data.py --dataset folktables --config configs/data/public/folktables.yaml --execute
uv run python scripts/download_data.py --dataset binance --config configs/data/finance/binance.yaml --execute
uv run python scripts/validate_datasets.py
uv run python scripts/build_data_report.py
uv run pytest tests/data/ -q
```

### Reproduce the stored synthetic smoke suite

`configs/data/synthetic/smoke.yaml` fixes eight scenarios, 5,000 observations, four
features, and DGP seed 42. Generate it on CPU with:

```bash
uv run python scripts/generate_synthetic.py --config configs/data/synthetic/smoke.yaml --root data --device cpu
uv run python scripts/validate_datasets.py --root data
uv run python scripts/build_data_report.py --root data
```

Each immutable version records the full generation configuration (including seed and
chunk size), source hash, Git commit, and SHA-256 hashes for observations and evaluator-only
oracle files. The same CPU configuration is bitwise-repeatable, and existing versions are
checksum-validated and reused. The archived smoke set includes eight original versions
created before Git provenance was available; their manifests retain seed 42 and a source
hash, but have no recoverable Git commit. Regenerating the smoke suite in a Git checkout
creates fully commit-pinned versions alongside those preserved originals. Use distinct DGP
seeds for independent replicates and reuse the same seeds across methods for paired
comparisons. CUDA uses an independent Torch RNG, so same-seed CPU/CUDA runs target
distributional parity rather than identical arrays. Oracle files are evaluator-only and
must not be passed to learners.

All download commands default to dry-run; `--execute` allows acquisition. Source failures are
errors, never replaced by synthetic or unrelated data. EIA bulk archive extraction supports multiple balancing authorities from the same checksummed archive; `eia_bulk_multi.yaml` builds CISO and ERCO retrospective next-hour tasks. Event-time splits do not imply publisher release availability. A credentialed FRED/ALFRED extract covers five series and 630 dated vintage records; WILDS and Criteo retain explicit source/terms limitations. There are no placeholder adapters.

The Monash Electricity hourly and Weather TSF archives omit `@horizon`. Their configured
168-step hourly and 30-step daily fixed-origin horizons follow the archive authors' benchmark
paper ([arXiv:2105.06643](https://arxiv.org/abs/2105.06643)); the citation is captured in each
configuration, task binding, observation metadata, and manifest limitation. This does not imply
real-time release availability.
The executed per-series metrics and per-step error plot are in
`data/reports/monash_forecast_diagnostics.json` and
`data/reports/monash_forecast_diagnostics.png`; plotted inter-series bands are descriptive
quantiles over the deterministic selected subsets, not confidence intervals.

For this NVIDIA Windows machine:

```bash
uv sync --extra dev --extra data-sources --extra neural
uv run --extra neural python scripts/generate_synthetic.py --config configs/data/synthetic/gpu_smoke.yaml --device cuda
uv run --extra neural python scripts/benchmark_generation.py --config configs/data/synthetic/benchmark.yaml
# Sustained 200,000-row sweep for 100 ms GPU-utilization sampling:
uv run --extra neural python scripts/benchmark_generation.py --config configs/data/synthetic/gpu_telemetry.yaml
# Optional, approximately 1 GB just for uncompressed float32 features:
uv run --extra neural python scripts/generate_synthetic.py --config configs/data/synthetic/gpu_large.yaml --device cuda
```

The neural extra pins a CUDA 13.0 PyTorch build from the official PyTorch index. A compatible
driver is required; base CPU installation does not install torch. CUDA requests fail clearly
if unavailable. `auto` resolves the actual backend before computing a dataset identity.
Independent NumPy and torch RNGs provide distributional parity, not matching random arrays.
Float32/64 refer to feature generation; oracle arithmetic may use float64. Chunk size is part
of the identity and RNG trajectory. `memory_mb` strictly caps the estimated per-chunk feature
and transformation workspace; it does not cap total process RSS, Python/Pandas overhead, or
the O(n) regime schedule. If one estimated feature row exceeds the budget, generation fails
with an actionable error rather than forcing a 16-row minimum. Stateful temporal recurrences and oracle calculations
run on CPU; torch generates vectorized latent arrays on CUDA. Affine preprocessing can also
apply training-fitted parameters on CUDA. Arrow compression and disk writes are on CPU.
Benchmark scopes include host transfer and DataFrame assembly, excluding disk writes. CUDA
benchmarks record per-repeat peak PyTorch allocation and device-wide `nvidia-smi` utilization
and memory samples across the repeat batch at 100 ms intervals. Those samples are not
process-specific, and very short workloads can fall below the driver's utilization sampling
resolution; they are context, not a process utilization measurement.
The benchmark config uses a 128 MiB estimated workspace cap and sweeps float32/float64 and
chunk sizes 1,000/5,000/10,000 with three repeats on each available backend. Compare warmed repeats as exploratory throughput evidence;
the default configuration does not imply that CUDA is faster for every workload.
The committed sustained 200,000-row run collected 24–40 device-wide telemetry samples per CUDA
dtype/chunk-size cell. At chunk size 10,000 it measured 233k rows/s (float32) and 206k rows/s
(float64) on CUDA versus 200k and 192k rows/s on CPU; at chunk size 1,000 CUDA float64 was
slower than CPU. These are host-specific end-to-end results, including host transfer and
DataFrame assembly, not a general acceleration claim. The report's completeness and telemetry
gates are checked by `tests/data/test_gpu_benchmark_report.py`.

## Data contract and observability

Schema 1.1.0 stores stable sample IDs, optional entity/domain IDs, event time, feature
availability, prediction time, outcome event time, label availability, features, target,
optional regime, decision context, weights, split, and provenance. Times are simulation indices
for synthetic data, UTC epoch seconds for timestamped real data, and null where not known.
Real original timestamps, offsets, flags and source fields remain in metadata or raw files.
Known clock values, targets, feature vectors and sample weights must be numeric and finite;
missing feature/target values and unknown clocks remain nullable where the task permits them.

Every newly published dataset manifest also includes `task_specs`: the target definition,
task kind, declared horizon semantics (including per-row irregular horizons), metric names,
valid-target mask and utility provenance. These contracts distinguish source tables from
forecast tasks, keep incomplete delayed-feedback labels masked, and leave utility unset where
no application cost is sourced. Historical manifests created before this field was added are
still readable and receive an empty list when loaded.

Read Parquet only in evaluator/acquisition code. `data.streaming.replay` yields immutable
`Request` and `Label` messages, excluding targets, regimes and oracles from requests. Features
must be available by prediction time. Requests at equal timestamps precede feedback at that
timestamp. Pending labels after the final request are emitted in availability order so delayed
feedback is not lost when no later prediction is scheduled.
The shared `data.label_availability` helpers use strict-before cutoffs for training at a request
time and keep unknown or missing outcomes masked.
Unknown label availability withholds labels. Unknown prediction/feature availability blocks
replay rather than inventing timestamps. This API is not a sandbox against malicious Python
code reading arbitrary files. Oracle files are physically separated in `evaluator_only/`.

Training-only scaling and horizon-safe lag construction are implemented. Synthetic partition
boundaries default to 20%, 30%, and 40% (configurable fractions), placing the default 50% change
inside the test stream; labels that arrive across the next partition boundary
are marked unassigned. Partitioning is based on time groups, preserving simultaneous samples.
Calibration/test utilities must still respect the replay protocol rather than reading stored
evaluator targets directly. No source missingness is silently forward-filled.

## Synthetic scope

The registry implements 43 explicit mechanisms (see `synthetic_catalogue.md`) across iid and
dependent controls, covariance/mixture changes, class prior shift, label corruption, conditional
mean and variance changes, heavy/asymmetric tails, local decision changes, costs, constraints,
feedback availability and resource-cost schedules. Nine core temporal patterns compose with these:
abrupt, multiple, linear, sigmoid, recurring, binary HMM, seasonal, temporary and variable dwell;
an additional ex-ante oblivious adversarial schedule is available for adaptation stress.
Gradual changes record intervals, not artificial point changepoints. `regimes` controls segment
count for multiple/recurring/variable-dwell patterns; the HMM always has two states. Regimes=1
suppresses exogenous changes. `data/reports/temporal_pattern_validation.json` records five-seed
checks for all ten schedules, including transition intervals, reported switch indices,
zero-strength nulls and the HMM dwell-rate diagnostic. Parameter values are configurable;
presets avoid Cartesian grids.
`uv run python scripts/validate_covariate_properties.py` checks all nine pure-covariate mechanisms
through dimension 1024 with independent conditional-mean formula comparisons and mechanism-specific
feature-marginal moments in `data/reports/covariate_property_validation.json`. Dimensions 2, 4, 8
and 16 use five seeds, n=30000 and severities 0, 0.5, 1 and 2; dimensions 32 through 1024 use
three seeds, n=5000 and severity 1. High-dimensional skewness is gated on positive direction;
other moments use analytic targets and finite-sample tolerances. Dimensions 32 and 1024 also
include null and strong-shift endpoints (severity 0 and 2).
`uv run python scripts/validate_concept_residuals.py` checks independent conditional mean/scale
formulas, unchanged feature moments, Gaussian residual variance and 90% oracle-radius coverage,
and Bernoulli boundary-rotation rates across eight concept mechanisms, dimensions 2, 3, 8 and 16,
and four severities (224 regime cells); replicated results are in
`data/reports/concept_residual_validation.json`.
`uv run python scripts/validate_scenario_quantiles.py` checks every registered scenario against
the exact CDF for its declared residual law and estimates oracle-radius coverage across three
independent seeds. Regression coverage uses history-conditional means/radii for dependent errors;
classification scenarios are explicitly recorded as having no residual interval radius. The
43-scenario evidence is in `data/reports/scenario_quantile_validation.json` and is folded into
`synthetic_validation.md` when the data report is built.
The `resource_cost` scenario changes only evaluator-side retraining cost, from 10 units at baseline
to `10 * (1 + severity)` after activation; other synthetic scenarios keep the default 10 units.
`rare_cost` and `resource_cost` generated values are checked against their analytic oracle formulas.
The medium plan uses 30 seeds; the optional large plan is never materialized automatically.
`uv run python scripts/plan_synthetic.py --config configs/data/synthetic/balanced_initial.yaml`
exports a reproducible balanced-marginal plan without generating streams. Its 12 profiles pair
all four scenarios with the same 30 DGP seeds, yielding 1,440 planned streams, 405 million
observations and an estimated 418 GB of uncompressed feature payload. The estimate is recorded
in `data/reports/sampling_plan.json`; the plan is deliberately previewed rather than executed.

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
`uv run python scripts/validate_performative_dynamics.py` checks its stable Gaussian state
mean/variance, joint-action effect, target and state innovation means/variances, 90% innovation
coverage and innovation independence over five seeds; results are in
`data/reports/performative_validation.json`.
Its documented stability condition concerns linear feedback. `allocate_update_budget` provides
an exact discrete-budget oracle for independent additive update proposals; interacting sequential
controllers and application-specific optimal interventions are not implemented. Saved manifests
state that no dynamic oracle is implemented. Resource-cost metadata do not establish optimal
interventions. Capacity, cost-sensitive binary and abstention decisions plus forecasting,
quantile-response, volatility and threshold tasks
are implemented. `multi_step_forecast_task` returns a fixed-origin target vector with per-step
outcome indices and finite-target masks; the whole task is available only after its final
requested outcome. Bounded mean-variance positions and finite multiclass cost matrices are also
executable when utility inputs are supplied; these remain imposed research objectives, not
application-grounded cost estimates. Dynamic optimal interventions remain unimplemented.

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
  mappings. Numeric epoch fields require explicit `time_units` (`s`, `ms`, `us`, or `ns`);
  timezone-naive datetime fields require an explicit IANA `time_zones` mapping. Ambiguous or
  nonexistent local DST times are refused unless the source supplies a resolved timestamp.
  Original contracts, quotes and quality columns remain in metadata. No restricted
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
reported without attributing concept drift. KS uses the explicit asymptotic two-sample method;
its uncorrected p-values remain descriptive under dependence and confounding. Multiple seeds test each generator's Bayes-risk
reference; further replicated tests check moments, class priors, quantiles and autocorrelation.
`scripts/time_series_real_diagnostics.py` uses train-only preprocessing and, when feature,
prediction and label-availability clocks are complete, strictly filters training and calibration
rows at their fit/prediction cutoffs. If clocks are unknown, it records a retrospective-only
protocol instead of implying online calibration.

Moving-block bootstrap intervals for first/last-window feature means are implemented under explicit
within-window stationarity and weak-dependence assumptions. They do not correct confounding,
missing-data selection or multiple comparisons.

The current implementation includes domain/group comparisons, OPSD hourly and daily tasks,
and adapters for the registered sources; their tests and limits are summarized in
[`phase1_completion_audit.md`](phase1_completion_audit.md). Remaining work is substantive:
observational diagnostics do not identify causal drift without a defensible design; FRED
vintages retain date-level revision events but not exact intraday release times; Criteo and
WILDS live data remain unavailable from the current sources; application-grounded decision
utilities have not been supplied; and large 100-seed final experiments or exhaustive GPU
parameter sweeps have not been run. Do not treat these constraints as evidence of successful
acquisition or as scientific results.


The original baseline tracks can consume these versioned regression data through
`uv run python scripts/evaluate_data.py --dataset-path <version-directory> --paper 1`
(and Papers 2/3). This bridge rejects real sources with unknown feature/prediction availability
and rejects classification rather than silently substituting a regressor for a classifier.
It fits only train/calibration labels available before test start and applies the streaming
feedback protocol thereafter. Decision metrics in this bridge retain the original fixed 5:1
research utility; context-varying utility studies should use the evaluator oracle and explicit
context-aware policies. Partition fractions and source-code identities distinguish historical
versions generated with the earlier 50/65/80% default from the current default.
