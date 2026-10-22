# ShiftLab Data Dictionary

This guide explains the versioned data format, the datasets represented in the project, and safe
starting points for analysis. It describes the current Phase 1 catalogue and documented data
artifacts; check each version's `dataset_manifest.json` and `data/reports/` before using a dataset.
Manifests are authoritative for that immutable version and may have more precise scope than the
summary counts below.

## Where data lives

| Path | Contents |
| --- | --- |
| `data/processed/<dataset>/<version>/` | Standardized real-source observations and source-specific inputs. |
| `data/synthetic/<scenario>/<version>/` | Synthetic observations with known simulation truth separated from learner inputs. |
| `data/raw/` | Downloaded source archives or original files, when retained locally. Ignored by ordinary Git. |
| `data/interim/` | Temporary or intermediate preparation artifacts. Ignored by ordinary Git. |
| `data/manifests/` | Lightweight pointers and inventory metadata for immutable dataset versions. |
| `data/reports/` | Generated inventory, readiness, quality, provenance, diagnostics, and validation reports. |
| `data/processed/.../dataset_manifest.json` | Version-specific metadata, task contract, provenance, limitations, and file checksums. |
| `data/processed/.../observations.parquet` | Standardized observation table, where a dataset has been converted to the common schema. |
| `data/synthetic/.../evaluator_only/` | Synthetic oracle data for scoring or checking simulations. Never pass these files to a learner. |

Large raw data and licensed WRDS archives are not stored in normal Git history. The private
[`data-2026-10-22` release](https://github.com/nl2992/shiftlab/releases/tag/data-2026-10-22)
contains the Phase 1 archives and bundles. Use [the restore guide](docs/cross_device_data_access.md)
to download and unpack them on another machine. Verify the SHA-256 values in the guide before
analysis. A private repository or release does not change the source's license or sharing terms.

## Shared observation schema, version 1.1.0

Every standardized `observations.parquet` contains the fields below. Parquet physical types can
vary for nullable fields or structured references; the manifest describes feature names and the
task-specific interpretation. The contract is implemented in `src/shiftlab/data/schemas.py`.

| Column | Meaning | Use and cautions |
| --- | --- | --- |
| `sample_id` | Stable identifier for one observation. | Must be present and unique within a dataset version. Use for joins and traceability. |
| `entity_id` | Optional entity such as a firm, station, series, or person pseudonym. | Defines grouping for panel-safe splits and within-entity lags when applicable. |
| `event_time` | Time associated with the source event or measurement. | Numeric in the source/task's declared time unit; null means unknown. It is not automatically a release time. |
| `feature_available_time` | Earliest recorded time the predictor inputs may be used. | Must be known and no later than prediction time for online replay. Unknown values are not imputed. |
| `prediction_time` | Time at which the prediction is made. | Required by `replay`; numeric units are source-specific and must be read from the task/manifest. |
| `label_event_time` | Time the outcome event occurred. | Can differ from label availability, especially for delayed conversions or later-reported values. |
| `label_available_time` | Time the target becomes observable to a learner. | The learner may train on the label only after this time. Null or unknown availability withholds it. |
| `features` | One-dimensional numeric feature vector. | The vector order is `manifest.feature_names`; null feature values may be allowed by the task, infinities are rejected. |
| `target` | Numeric outcome or class code, when available. | A stored target is not permission to expose it before `label_available_time`. Missing targets remain missing. |
| `domain_id` | Optional observed source domain, group, or partition label. | Useful for descriptive domain comparisons; not necessarily a time regime or causal shift label. |
| `regime_id` | Optional generating or source regime identifier. | Synthetic truth belongs to evaluator analysis and must not be used as a learner feature. Real-source values are not ground-truth changepoints unless explicitly documented. |
| `decision_context` | Optional context needed by a declared decision task. | Use only if the `task_specs` contract says it is learner-visible at prediction time. |
| `sample_weight` | Optional nonnegative observation weight. | Weight meaning and normalization are task-specific; do not assume it is a survey weight unless documented. |
| `split` | Named partition: `train`, `validation`, `calibration`, `test`, or `unassigned`. | Preserve the documented chronology and purge rules. Do not reshuffle a time-series split casually. |
| `metadata` | Source-specific details encoded as structured metadata (often JSON text in Parquet). | Keeps original source fields, flags, units, batch/series identifiers, and conversion details that are not common columns. |
| `feature_reference` | Optional structured reference associated with an observation. | For structured-reference datasets, identifies the corresponding record in a companion file such as `inputs.parquet`; it is not itself a numeric model feature. |

The five time columns are numeric values in a declared clock, not necessarily Unix seconds. Synthetic
time is usually a simulation index; timestamped sources may use UTC epoch seconds; some datasets
have no verified clock and therefore store null. **Do not compare time values across datasets or
invent missing release times.**

## Dataset version manifest

Each `dataset_manifest.json` is a JSON record that should travel with its data. Key fields:

| Field | Description |
| --- | --- |
| `schema_version` | Version of the standardized contract, currently `1.1.0`. |
| `dataset`, `version` | Dataset family and immutable version identifier. Use both when recording a result. |
| `publisher`, `source_url`, `citation` | Source identity and attribution information. |
| `license`, `permitted_use` | Recorded terms for this acquired version. Check publisher terms before redistributing or combining data. |
| `acquired_at`, `retrieval_parameters` | Acquisition timestamp and requested source parameters. |
| `raw_checksums` | Hashes of retained publisher files or raw source references. |
| `processing_config`, `source_hash`, `code_commit` | Transformation parameters and code provenance. `code_commit` may be null for older data. |
| `task_specs` | Task ID/kind, target definition, horizon, valid-label mask, metrics, availability rule, and utility provenance. Older manifests may have an empty list. |
| `n_observations`, `feature_names`, `feature_dtype`, `feature_kind` | Row count and feature contract. `feature_kind` may identify numeric features or structured references. |
| `time_coverage`, `domains`, `missingness` | Dataset summary; these are not substitutes for row-level validation. |
| `limitations`, `ground_truth` | Known restrictions and whether truth is synthetic, absent, or only coarse domains. |
| `files` | Relative file paths and SHA-256 checksums for files in the immutable version. |
| `oracle_file`, `environment` | Optional evaluator-only path and environment metadata. |

`task_specs` is the first place to check before fitting a model. It says what the target means, which
rows qualify, what metrics are intended, whether a horizon exists, and how label availability is
handled. If utility provenance says no application-grounded utility, cost-weighted conclusions must
be described as imposed research diagnostics.

## Current dataset families and what they support

Counts below summarize the current project audit and source reports; they are not guaranteed to be
the row count in every historical version. Exact dataset/version counts and source terms are in
`data/reports/data_inventory.csv`, `data/reports/experiment_readiness.md`, and each version's
manifest.

| Family | Data represented in the project | Practical use and limits |
| --- | --- | --- |
| Synthetic suite | 46 immutable versions across controlled mechanisms and schedules; smoke configurations commonly contain 5,000 observations each. | Best for tests with known generating truth, known shifts, controlled nulls, and paired algorithm seeds. Oracle information stays evaluator-only. |
| CRSP CIZ / WRDS finance | Daily US equity extraction for 2000–2025, plus daily factors, Treasury series, Compustat annual fundamentals, and CCM link history in the private release. Annual extraction manifests and checksums accompany the raw archive. | Supports a retrospective equity-return study. Construct and validate a derived next-day panel with per-security ordering, target-date purging, and documented return-quality rules before benchmarking. Intraday availability and causal regime labels are not supplied. See `docs/crsp_study_execution.md`. |
| Folktables | Five ACS tasks across CA, NY, TX, FL, and NJ; the 2019 panels total 143,285 task rows in the Phase 1 additions. | Offline classification and domain/group comparisons. Survey year and state/domain do not establish within-year event times or decision utility. See `docs/folktables_panel.md`. |
| Criteo Attribution Modeling | Pinned official 30-day display-attribution snapshot, 16,468,027 impressions; original source archive is retained in the release. | Delayed-feedback classification under explicit feature-delivery assumptions. Conversion outcomes, revenue, and availability belong in evaluator-side data; timestamps are publisher-relative, not calendar time. |
| CriteoPrivateAds | 30 day partitions, 103,862,032 rows, and 288 verified source files (about 34 GB). | A distinct delayed-outcome advertising dataset. It is not the 90-day Sponsored Search dataset. See `docs/acquisition_extensions.md` for the source schema and recorded assumptions. |
| CivilComments / WILDS | Complete raw CivilComments mirror with 448,000 rows; source revision, hash, and official split counts are recorded. | Offline text classification and official domain partitions. Domain partitions are not timestamped drift or changepoints. Text inputs and labels are kept separate by the adapter. |
| UCI Gas Sensor | 13,910 processed rows over 128 source features and ordered batches. | Offline batch/domain classification. There are no within-batch timestamps. A documented diagnostic applies train-only fitting; its example class costs are imposed, not supplied by the source. |
| Monash | Processed M4 hourly/daily/weekly benchmark subsets; the latest summarized version has 383,332 rows. | Fixed-origin forecasting using official horizons where provided. Electricity and Weather archives are retained, but conversion is withheld when the source header omits its forecast horizon. |
| NOAA, OPSD, EIA | Processed weather and electricity observations, including a multi-authority EIA subset. The audit reports 41,194 NOAA rows, 8,759 OPSD rows, and 52,606 EIA rows in the latest summarized versions. | Retrospective forecasting and measurement diagnostics. Measurement/event time does not establish when a feature or outcome was published. |
| FRED / ALFRED | 630 dated revision records across UNRATE, CPIAUCSL, FEDFUNDS, DGS10, and GDPC1 for the acquired vintage window. | Study revisions and as-of-vintage selection. This is a revision table, not a ready real-time forecasting panel; release instants are not fully known. |
| Binance | Small hourly ETH market-data versions; the current suitability summary reports 743 rows in its latest version. | Demonstration of retrospective next-bar forecasting. Public market bars do not provide an execution-cost model or trading utility. |
| Criteo 90-day Sponsored Search | No source archive acquired; the publisher-linked endpoint was unavailable in the recorded probes. | Do not substitute Criteo Attribution, PrivateAds, or click-only logs and label them as Sponsored Search. The separate 1TB click-log corpus is an optional upstream scale dataset and has no conversion-delay labels. |

The detailed suitability matrix is generated at `data/reports/dataset_paper_suitability.md` and
includes paper-specific task readiness, timing evidence, and utility provenance. Some rows describe
historical immutable versions; repeated configurations are not independent experimental replicates.

## Reading and validating a dataset

For small or moderate Parquet files, read the manifest first, then select the needed columns:

```python
import json
from pathlib import Path

import pandas as pd

path = Path("data/processed/folktables/0fcc49a2576071bf51da")
manifest = json.loads((path / "dataset_manifest.json").read_text())
frame = pd.read_parquet(path / "observations.parquet")

assert len(frame) == manifest["n_observations"]
print(manifest["feature_names"])
print(manifest.get("task_specs", []))
print(frame.groupby("split", dropna=False).size())
```

The version directory may not be present in a fresh clone until the applicable release bundle has
been restored. To inspect available versions, use the inventory and validation tools:

```bash
uv run python scripts/data_inventory.py
uv run python scripts/validate_datasets.py --root data
uv run python scripts/build_data_report.py --root data
```

Validation checks schema, finite values, chronological split order, sample-ID uniqueness, and file
checksums. For large tables, use PyArrow batches rather than loading all columns into memory:

```python
import pyarrow.parquet as pq

parquet = pq.ParquetFile(path / "observations.parquet")
for batch in parquet.iter_batches(
    columns=["sample_id", "prediction_time", "features", "target", "label_available_time"],
    batch_size=100_000,
):
    frame = batch.to_pandas()
    # Apply the dataset's task and availability rules before analysis.
```

## Using data in experiments

### Offline and retrospective analyses

Use `split`, `task_specs`, and source metadata to build a task-specific analysis. Fit imputation,
feature selection, scaling, and model parameters on training data only. Keep validation/calibration
and test partitions in their declared roles. For example, the Gas Sensor diagnostic is:

```bash
uv run python scripts/group_diagnostics.py \
  --dataset-path data/processed/gas_sensor/<version>
```

It reports batch feature summaries and a train-fitted classifier; it explicitly treats its sample
class-cost matrix as an imposed research diagnostic. NOAA, OPSD, Monash, and EIA have their own
report scripts and protocols under `scripts/` and `docs/`.

### Online or delayed-feedback replay

The `shiftlab.data.streaming.replay` iterator emits immutable `Request` messages with features and
prediction-time context, followed by `Label` messages only when the recorded target is available.
Requests sharing a timestamp come before labels available at that timestamp. Labels arriving after
the final request are still emitted. The shared regression evaluator uses this protocol and refuses
datasets without known prediction and feature-availability times:

```bash
uv run python scripts/evaluate_data.py \
  --dataset-path data/processed/<dataset>/<version> --paper 1
```

This bridge supports regression datasets, not classification; a valid time clock, enough training
and calibration observations, and an appropriate chronological task are also required. Many real
datasets are therefore usable for offline or retrospective analysis but not an online benchmark.
`Request` does not expose targets, split labels, regimes, or evaluator oracles. This is API
separation for correct experiments, not a security boundary against arbitrary local Python code.

### Synthetic replication

Use the registered synthetic scenarios to test algorithms under known stationary and shifted
conditions. Reuse the same DGP seeds across methods for paired comparisons, and use distinct seeds
for independent replications. The smoke config is for checking the pipeline; it is not a final
power or performance study. Generated oracle files include mechanism and regime truth for
evaluation only. Do not pass `evaluator_only/` to learner code.

## Source terms and interpretation

Every source's license, citation, acquisition status, and known timing limitations are recorded in
the inventory and manifest. Confirm the current publisher and institutional terms before moving
data outside the approved storage location or redistributing it. Source presence does not establish
online availability, causal shift, statistical representativeness, or application utility. Preserve
those distinctions in code, metrics, figures, and writeups.
