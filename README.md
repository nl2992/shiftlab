# ShiftLab

ShiftLab is a reproducible research codebase for studying distribution shift when predictions,
labels, decisions, and model updates happen over time. It combines a focused three-track benchmark
with a reusable data framework for controlled simulations and selected public or licensed sources.
The repository is organized to make data timing, task definitions, provenance, and evaluation limits
visible alongside the code that uses them.

## What is in the codebase

| Area | Location | How it helps |
| --- | --- | --- |
| Core benchmark | `src/shiftlab/`, `configs/experiments/` | Validates experiment settings and runs comparable baselines for decision drift, conformal prediction, and cost-aware adaptation. |
| Data contracts and storage | `src/shiftlab/data/schemas.py`, `storage.py`, `validation.py` | Standardizes observations, writes immutable Parquet versions, records provenance, and checks integrity before use. |
| Data acquisition and tasks | `src/shiftlab/data/real/`, `src/shiftlab/data/tasks.py` | Adapts selected external sources and describes targets, horizons, valid rows, metrics, label timing, and utility assumptions. |
| CRSP panel workflow | `scripts/build_crsp_study_panel.py`, `scripts/smoke_crsp_study.py` | Converts the WRDS daily extract into a versioned next-observed-return panel, validates annual and output checksums, and runs a bounded end-to-end smoke analysis. |
| Synthetic environments | `src/shiftlab/data/synthetic/`, `configs/data/synthetic/` | Produces controlled stationary and shifted streams with known evaluator truth for tests that cannot be done with observational data alone. |
| Feedback replay | `src/shiftlab/data/streaming.py`, `label_availability.py` | Exposes predictions and labels in availability order so delayed or unknown labels are not accidentally used early. |
| Acquisition and experiment tools | `scripts/` | Generates data, inventories sources, validates stored versions, builds reports, and runs benchmark or dataset-specific diagnostics. |
| Paper plans and evidence | `papers/`, `docs/`, `data/reports/` | Keeps hypotheses, protocols, source limitations, validation results, and paper suitability close to the implementation. |
| Tests | `tests/` | Checks schemas, time ordering, leakage boundaries, generator properties, provenance, and report gates. |

The three paper tracks share a streaming learner and controlled data-generation system:

1. **Decision drift** compares statistical alarms while measuring changes in prediction and decision
   loss.
2. **Adaptive conformal prediction** compares fixed and rolling residual calibration under shift
   and delayed feedback.
3. **Cost-aware adaptation** compares frozen, periodic, and triggered retraining under a stated
   update budget and retraining cost.

The broader data package adds 43 registered synthetic mechanisms, multiple temporal schedules,
real-source adapters, task metadata, immutable versions, and report-generation tools. Synthetic
experiments provide known change times and evaluator-only truth. Real datasets provide observed
domains or time series, but generally do not provide causal shift labels, exact release times, or
application-specific decision costs. The framework records those limits instead of filling them in.

## Using the data already in the project

Start with the [Data Dictionary](DATA_DICTIONARY.md). It explains the shared observation columns,
version manifests, dataset-specific files, availability fields, and which analysis paths are
appropriate. The detailed source inventory is generated at `data/reports/data_inventory.csv`;
readiness and quality evidence are in `data/reports/experiment_readiness.md` and
`data/reports/data_quality_report.md`.

Versioned data normally lives under `data/processed/<dataset>/<version>/` or
`data/synthetic/<dataset>/<version>/`. Each version has a `dataset_manifest.json` and, where
applicable, `observations.parquet`; some sources retain original structured inputs in additional
Parquet files. Synthetic evaluator truth is separated under `evaluator_only/`. Large raw and
licensed archives are excluded from ordinary Git commits; when a dataset is not present locally,
follow [the cross-device restore guide](docs/cross_device_data_access.md).

For a quick look at an existing standardized dataset:

```python
import json
from pathlib import Path

import pandas as pd

dataset = Path("data/processed/folktables/0fcc49a2576071bf51da")
manifest = json.loads((dataset / "dataset_manifest.json").read_text())
observations = pd.read_parquet(dataset / "observations.parquet")

print(manifest["dataset"], manifest["version"], manifest["n_observations"])
print(manifest["feature_names"])
print(manifest.get("task_specs", []))
print(observations[["sample_id", "target", "domain_id", "split"]].head())
```

The path above is an example version; use the inventory report or search `data/processed/` for the
version available in your checkout. For online-style evaluation, use the replay API and its
`Request`/`Label` messages rather than training directly from the stored target column. Replay
requires verified prediction and feature-availability times; datasets without those clocks are
appropriate for explicitly retrospective or offline diagnostics instead.

Useful checks and entry points:

```bash
uv run python scripts/data_inventory.py
uv run python scripts/validate_datasets.py --root data
uv run python scripts/build_data_report.py --root data
uv run pytest -q
uv run python scripts/run_diagnostics.py --config configs/experiments/diagnostics.yaml
uv run python scripts/run_baselines.py --paper 1
uv run python scripts/run_baselines.py --paper 2
uv run python scripts/run_baselines.py --paper 3
```

The shared `scripts/evaluate_data.py` bridge currently evaluates **regression datasets only** and
requires known feature and label availability plus usable chronological splits. Source-specific
reports, such as `scripts/group_diagnostics.py` for Gas Sensor and the Monash/NOAA/OPSD/time-series
report scripts, implement their own task-appropriate checks. Consult the Data Dictionary and each
dataset's `task_specs` before choosing an evaluator; an available file is not automatically a valid
benchmark for every paper.

For the WRDS CRSP study, the repository also provides a streaming panel builder and smoke runner.
The builder handles PERMNO-specific next-observation targets, documents a return-quality mask,
purges targets across chronological split boundaries, and writes a checksummed dataset manifest.
Run it only after restoring the raw WRDS archive; see [the CRSP execution guide](docs/crsp_study_execution.md)
for the exact command, target rules, retrospective clock, and limitations.

## Install and run

Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required. From the repository root:

```bash
uv sync --extra dev --extra data-sources
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

To reproduce the small synthetic smoke suite:

```bash
uv run python scripts/generate_synthetic.py \
  --config configs/data/synthetic/smoke.yaml --root data --device cpu
uv run python scripts/validate_datasets.py --root data
uv run python scripts/build_data_report.py --root data
```

Acquisition commands default to a dry run. Network retrieval requires the explicit `--execute`
flag, and some sources require optional dependencies or credentials. See
[docs/data_phase1.md](docs/data_phase1.md) for exact commands and source constraints.

Each benchmark run writes a unique `outputs/<UTC>-<uuid>/` directory with its resolved
configuration, status manifest, dependency versions, Git revision, predictions, metrics, logs,
checkpoints, and figures. Numerical outputs are deterministic for a fixed configuration and seed;
run identifiers and wall-clock timings are not. Large generated outputs are ignored by Git.

## Research safeguards and limits

The first paper studies **decision harm under distribution shift**. Keep three quantities distinct:

\[
D(P_t,P_0), \qquad R_t(f)-R_0(f), \qquad
R_t(\pi)-R_t(\pi_{\mathrm{ref}}).
\]

They measure distributional change, predictive degradation for a fixed predictor, and the deployed
policy's excess cost over a specified fallback or challenger. The third quantity is the decision
target: a named reference policy can make the comparison more identifiable than regret against an
unknown Bayes-optimal policy. Distribution change alone does not imply predictive degradation, and
predictive degradation alone does not establish harm under the deployed decision rule.

For the first paper, the monitoring null is

\[
H_0:\quad
\mathbb{E}\!\left[c(\pi_t(X_t),Y_t)-c(\pi_{\mathrm{ref}}(X_t),Y_t)
\mid \mathcal{F}_{t-1}\right]\leq\epsilon.
\]

The proposed contribution is an anytime-valid procedure for monitoring this conditional excess
cost and controlling erroneous escalation under explicit assumptions. An e-process by itself does
not establish validity. Any theorem and implementation must state and justify the feedback and label
availability process, predictable policy and reference-policy selection, dependence assumptions,
and any adaptive label-sampling mechanism. These conditions are part of the method and its
evaluation protocol, not follow-up details. The current baselines do not yet establish this guarantee.

The learner receives only features available at prediction time and labels after their recorded
availability time. Synthetic regime labels and generating parameters stay evaluator-side. Missing
or unknown real-world timing is not inferred. Real-source results must therefore use the task's
documented retrospective or offline protocol when a valid online replay clock is unavailable.

The paper protocols distinguish diagnostic evidence from confirmatory results. Small seed counts
are smoke or validation runs; selected final comparisons should use paired seeds and the larger
replication counts specified by the protocol. Imposed synthetic costs are research controls, not
application-grounded utilities. Current baselines do not establish anytime-valid alarm control,
conditional conformal coverage under arbitrary shift, causal drift attribution, or universal
benefits from adaptation.

For version-control conventions and contribution checks, see [CONTRIBUTING.md](CONTRIBUTING.md).
