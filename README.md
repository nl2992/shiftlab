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

The current experimental tracks share a streaming learner and controlled data-generation system:

1. **Decision drift baselines** compare statistical alarms and measure prediction and decision loss.
2. **Conformal baselines** compare fixed and rolling residual calibration under shift and delayed
   feedback.
3. **Adaptation-cost baselines** compare frozen, periodic, and triggered retraining under stated
   update budgets and costs.

These are the names of existing implementation tracks, not claims that three new contributions have
been established. The governing research direction distinguishes decision harm from distributional
change and predictive degradation, and treats conformal prediction as a supporting module. See the
[research charter](docs/research_charter.md) for the candidate paper questions and evidence gates,
and [AGENTS.md](AGENTS.md) for implementation guidance.

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

## Decision-harm benchmark (Phases 0–2)

The explicit learner/evaluator message boundary, delayed-feedback ordering, query-propensity
recording, action/reference versions, and evaluator-only oracle schema are documented in the
[streaming decision contract](docs/streaming_decision_contract.md). The initial benchmark compares
feature RBF-MMD², predictive squared-error CUSUM, paired realized decision-cost CUSUM, and a bounded
full-feedback Hoeffding e-process across stationary, benign nuisance, localized harmful,
residual-variance, recurring-regime, and deliberately harmful-adaptation settings. This is a
reproducible baseline study, not a claim of a new method; see the [closest prior-work audit](docs/closest_prior_work.md).

Run the smoke version with `uv run shiftlab-decision-harm --quick`, or reproduce the configured
30-seed run with `uv run shiftlab-decision-harm --seeds 30 --calibration-seeds 60 --n 3200 --device auto`.
Auto selects CUDA only for the large synthetic-generation range supported by the committed host
benchmark (at least 200k observations, 64 features and 5k-row chunks); this small decision-harm
experiment therefore remains on CPU. Pass `--device cuda` to override that heuristic when CUDA is
available and you want to test that backend.
Outputs are written to a timestamped `data/reports/decision_harm_phase2/` directory and include
Parquet seed metrics and traces, calibration/seed/source hashes in a JSON manifest, three PNG
figures, and a baseline report. The quick run is an implementation check only. Empirical MMD/CUSUM
thresholds are calibrated on independent stationary runs at a fixed horizon; they are not universal
validity guarantees. The e-process example assumes predictable actions, complete paired outcomes,
bounded observed cost differences, known costs, and the conditional excess-cost null. Delayed or
selectively observed labels, adaptive queries, serial dependence, counterfactual policy value, and
real-world utility validity are not established by this benchmark.

The extended Paper 3 query-allocation comparison also covers boundary-local harm, residual-variance
shift, recurring regimes, and deliberately harmful adaptation. Its locked protocol is in
[`docs/hard_budget_extended_scenarios_protocol.md`](docs/hard_budget_extended_scenarios_protocol.md),
and the 60-seed CUDA results (1,200 method-stream rows), paired bootstrap summaries, and figure are
in `outputs/hard_budget_extended_scenarios_60/`. In this exploratory block, all per-stream hard
budgets were respected and no false escalations occurred, while harmful-stream detection ranged
from 0/60 to 8/60 depending on scenario and query policy. The low rates are descriptive and do not
establish a method ranking or a false-alarm guarantee. See the [Paper 3 research log](papers/paper3_cost_aware_adaptation/research_log.md)
for the interpretation and per-scenario paired RMSE intervals.

The betting-scale sensitivity experiment compares the existing five-stake e-process with a fixed
13-stake geometric mixture on matched harmful-shift streams and stationary/benign controls. The
broader equal-weight mixture detected fewer harmful streams in this block, so it is retained as a
negative grid-search result rather than promoted as an improved method. The bounded-mean guarantee
is the same for both mixtures under the documented assumptions. See the
[multiscale betting protocol](docs/multiscale_betting_protocol.md) and its paired output reports.

The current full initial run is documented in
[`data/reports/decision_harm_phase2/20261023T0230Z-final-30seed/baseline_report.md`](data/reports/decision_harm_phase2/20261023T0230Z-final-30seed/baseline_report.md).

### DIVE: evidence-efficient decision-harm monitoring

The first DIVE implementation compares full feedback, uniform direct and prediction-powered
estimates, a clearly labeled PPRM-style adaptive-reliance analogue, and uncertainty-,
residual-variance-, and decision-value-guided label acquisition. It
uses paired deployed-minus-reference costs, prequential prediction-powered corrections, bounded
mean e-processes, and a fixed mixture over prespecified start times. The implementation and
assumptions are described in [`docs/methods_and_assumptions.md`](docs/methods_and_assumptions.md);
the closest prior work and current novelty boundary are in
[`references/closest_competitors.md`](references/closest_competitors.md). Open proof targets are in
[`docs/theory_targets.md`](docs/theory_targets.md).

The shadow-promotion experiment evaluates a frozen logistic recalibration candidate and an
incumbent snapshot on fresh forward-time labels, applies candidate-index alpha spending, and
reports certification behavior in `outputs/figures/adaptation_promotion.png` and
`outputs/metrics/promotion_comparison.parquet`. The one-step cost-aware controller is available in
`shiftlab.dive.controller`; its forecasts are supplied inputs, and it is not yet integrated into a
closed-loop intervention benchmark.

The initial CUDA benchmark is saved in `outputs/`. It contains 1,260 monitor rows (30 seeds × 6
scenarios × 7 methods) and 360 candidate-promotion rows. With 2,400 labels per stream, full-feedback
monitoring detected all harmful boundary-local, harmful-adaptation, and recurring-regime streams
(median delays 357, 367, and 147 events). At roughly 238 labels per stream, uniform direct monitoring
detected 14/30, 18/30, and 15/30 of those streams, with median delays of 1,120, 1,110, and 2,001
events. The prediction-powered and feature-guided acquisition variants detected few or none in these
conditions. There was one full-feedback false escalation in 30 stationary streams; the 95% Wilson
interval is broad at this sample size. The prespecified start-time mixture made no detections in
this run, so its practical sensitivity remains unresolved. These are synthetic descriptive results,
not evidence of real-world performance or superiority to faithfully reproduced published methods.

The candidate test certified the exact incumbent-copy control in 0/150 streams where its
pointwise-null assumptions applied. The frozen recalibration candidate was certified in 30/30
boundary-local streams, 30/30 recurring-regime streams, and 30/30 harmful-adaptation streams. These
rates are exploratory; only the exact-copy control directly checks the stated null in this setup.
The evaluator labels material harm from finite-stream averages of oracle conditional costs. Seven
of 30 benign-nuisance streams crossed the 0.1 threshold even though the across-seed mean stayed
below it, so the borderline control classification is seed-sensitive.

The allocation search adds a validation-selected grid over expected query rates 5%, 10%, and 20%
and residual-variance score powers 0, 0.25, 0.5, 0.75, and 1. Score power 0.5 is the classical
Neyman allocation derived by minimizing the prediction-powered estimator's query-randomization
variance at a fixed expected budget. Hyperparameters are selected using fully labeled validation
residuals and evaluated on a separate forward monitor slice. This is a grounded tuning method, not
a novelty claim; realized labels can exceed or fall below the expected budget.

A follow-up rate-stabilized Neyman search shrinks that adaptive score toward uniform sampling. For
any deployment feature distribution, its expected query-rate deviation is bounded by a configured
tolerance `delta`, while all event propensities remain positive for sequential monitoring. This
controls expected budget drift under feature shift, though realized counts remain random. See
`outputs/reports/rate_stabilized_grid.md` for its paired 30-seed forward evaluation.

The current 30-seed allocation search is a useful negative result. Across 540 paired
scenario-seed-budget streams, validation-selected power (1.0 in 96.7% of groups and 0.75 in
3.3%) had **0.3055 higher stream RMSE** than fixed Neyman power 0.5 (paired 95% t interval
`[0.2288, 0.3823]`) and used **26.6 more labels** (`[20.0, 33.2]`). Material-stream detection
was zero for both. This shows that selecting an allocation by early validation residuals did not
generalize across the subsequent feature shifts; it is not evidence that increasing score power
helps.

The rate-stabilized mixture's validation-selected setting had 0.0324 lower RMSE than uniform
sampling (`95% CI [-0.0568, -0.0079]`) at a cost of 5.9 additional labels (`[4.8, 7.0]`); material
harm detection was 0.174 versus 0.226. Against unmixed Neyman, it reduced RMSE by 0.1008
(`[-0.1491, -0.0526]`), used 22.3 fewer labels (`[-26.9, -17.7]`), and detected 0.174 versus 0
of material streams. These are paired descriptive results from shared seeds and scenarios, not
independent replications. The e-process detected no material streams in the original allocation
grid, and the mixture still detected only a minority; the fixed worst-case increment bound is too
conservative for a useful monitoring result in these runs. Each scenario-budget cell has 30 seeds,
so its detection intervals are wide. Treat the mixture as a hypothesis for a larger, independently
seeded follow-up, not a recommended method or a novelty claim.

An additional GPU experiment adds a known feature-dependent label tariff and compares the
classical cost-constrained `sqrt(vhat / label_cost)` allocation against uniform and residual-variance
querying on the same 30-seed streams. It reduced stream-estimation RMSE versus residual-variance
querying in five of six scenarios, but did not improve harm detection; uniform querying detected
some material streams where the cost-aware rule detected none. Against uniform querying, RMSE was
lower only in benign nuisance shift, where realized spend also rose substantially after the nuisance
shift. The result is a mixed estimator baseline and a negative monitoring result, not a new algorithm
claim. See [cost-aware findings](outputs/cost_aware/reports/cost_allocation_findings.md) and the
[full experiment report](outputs/cost_aware/reports/method_comparison.md).

The cost-neutral mixture was then evaluated on 30 paired seeds each for stationary, benign-nuisance,
and boundary-local harm, alongside uniform, variance-only, and cost-aware Neyman sampling. Its
expected-spend deviation satisfied the configured 0.05-per-event bound on every saved stream. Under
benign shift it spent about 369 per stream, compared with 495 for uniform and 640 for cost-aware
Neyman. It detected **0/30** boundary-harm streams, while uniform detected **5/30**. The stabilized
rule therefore controls expected spend under the specified bounded tariff, but shows no monitoring
power gain and loses estimation accuracy when its spend control reduces labels. See the [pilot
report](outputs/cost_stabilized_pilot_30/reports/cost_stability_results.md) and the full
[method comparison](outputs/cost_stabilized_pilot_30/reports/method_comparison.md).

The principal outputs are `outputs/reports/method_comparison.md`,
`outputs/reports/promotion_comparison.md`, `outputs/reports/allocation_grid.md`,
`outputs/reports/rate_stabilized_grid.md`, and the combined hash manifest at
`outputs/reports/manifest.json`; Parquet metrics are under `outputs/metrics/`. The figures
`shift_vs_harm.png`, `false_alarm_delay.png`, `label_efficiency.png`, `cumulative_net_regret.png`,
`cost_pareto.png`, `adaptation_promotion.png`, `allocation_grid.png`, and
`rate_stabilized_grid.png` are stored under
`outputs/figures/`.

Run `uv run shiftlab-dive --quick` for a small smoke benchmark or
`uv run shiftlab-dive --seeds 30 --n 3200 --device auto` for the initial paired-seed comparison.
Run `uv run shiftlab-dive --seeds 30 --n 3200 --device cuda --heterogeneous-label-costs --cost-stability-tolerance 0.05 --output outputs/cost_stabilized`
to compare cost-aware Neyman allocation against sparse-feedback baselines when label prices are
known at query time and vary with an observed feature. The cost-neutral mixture is included with a
worst-case expected-spend drift bound set by the tolerance. This synthetic stress test reports
realized label spend and does not claim a hard spend cap.
The focused pilot reported above used `--scenarios stationary benign_nuisance boundary_local_harm`
and `--methods uniform_proxy variance_proxy cost_variance_proxy cost_stabilized_proxy`; its exact
command and seed-level results are in `outputs/cost_stabilized_pilot_30/reports/`.
An exploratory paired-seed tolerance sweep at `delta` 0.01, 0.025, 0.05 and 0.1 is summarized in
`outputs/cost_tolerance_grid_exploratory/reports/tolerance_grid.md`; it reuses the first ten seeds
of the 30-seed runs at 0.01 and 0.05, so those subsets are not independent replications. All
expected-spend checks passed, but the ten-seed cells did not establish a harm-detection benefit.
Rebuild its summary, figure and hash manifest with `uv run python scripts/analyze_cost_tolerance_grid.py`.
For a common hard realized label-dollar cap, run
`uv run shiftlab-dive-hard-budget --seeds 30 --n 3200 --device cuda --output outputs/hard_budget_pilot_30`.
This compares five acquisition policies and stops monitoring before a new event if the remaining
balance cannot cover the known maximum tariff. The first 30-seed pilot respected the cap in all
450 rows; on boundary-local harm, uniform detected 4/30 while the four adaptive policies detected
0/30 under method-specific e-process bounds. A matched sensitivity rerun set every method to the
same `q_min=0.05` bound; then all methods detected 0/30 despite all 30 onsets being reached. The
4-versus-0 result is therefore sensitive to threshold conservatism and cannot be attributed to
allocation alone. See the [bound sensitivity report](outputs/hard_budget_pilot_30/reports/eprocess_bound_sensitivity.md).
The report includes paired seed intervals, budget censoring and assumptions. This is a synthetic
baseline result, not an intervention guarantee or a novelty claim.
We then locked a fresh 60-seed matched-bound study at a 20% target budget, common `q_min=0.10`,
and `q_max=0.80` so the cost-neutral propensity remains feasible over the declared tariff range.
All 900 method-stream rows stayed within the common hard cap; all 60 boundary-harm onsets were
reached, and there were no false escalations in 60 stationary or 60 benign-nuisance streams.
Cost-stabilized querying detected 12/60 boundary-harm streams versus 8/60 for uniform (paired
difference +0.067; 95% seed-bootstrap interval [0.000, 0.150]); this unadjusted interval touches
zero, so no advantage is established. Their RMSEs were 0.0548 and 0.0554 respectively (paired
difference -0.0006; 95% interval [-0.0082, 0.0068]); cost-stabilized used 518 labels versus 474 at
similar realized spend ($713 versus $712). See the [locked protocol](docs/hard_budget_matched_bound_protocol.md)
and [full analysis](outputs/hard_budget_matched_qmin_010_replication_60/reports/matched_bound_replication_analysis.md).
Reproduce with the command in the protocol; this is fresh-seed exploratory replication, not a
general allocation result.
The [paired power plan](outputs/hard_budget_matched_qmin_010_replication_60/reports/paired_detection_power_plan.md)
estimates 151 fresh seeds for 80% power against the easier zero-difference McNemar null under
pilot plug-in rates (219 with a four-comparison Bonferroni level). Those figures do not power the
registered +0.10 practical margin; the pilot estimate is +0.067, so that claim needs a separate
paired-risk-difference design.
Run `uv run shiftlab-dive-promotion --seeds 30 --n 3200 --device cuda` for the separate shadow
candidate experiment.
Run `uv run shiftlab-dive-grid --seeds 30 --n 3200 --device cuda` for the nested allocation search,
which writes `outputs/metrics/allocation_grid.parquet` and `outputs/reports/allocation_grid.md`.
Run `uv run shiftlab-dive-robust-grid --seeds 30 --n 3200 --device cuda` for the rate-stabilized
Neyman search and its bounded expected-rate-drift comparison.
Use `--device cuda` to force GPU generation when supported; automatic selection keeps this small
workload on CPU under the measured throughput heuristic. Metrics, plots, a report, and a manifest
are written under `outputs/metrics/`, `outputs/reports/`, and `outputs/figures/` by default; pass
`--output <directory>` to use another result root. This is an initial synthetic
comparison: it does not yet implement delayed-label inference, counterfactual policy evaluation,
or a label-budget controller. Prediction-powered monitoring and anytime-valid risk evidence
already have close prior work, so this benchmark makes no novelty claim.

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
  --config configs/data/synthetic/smoke.yaml --root data --device auto
uv run python scripts/validate_datasets.py --root data
uv run python scripts/build_data_report.py --root data
```

Acquisition commands default to a dry run. Network retrieval requires the explicit `--execute`
flag, and some sources require optional dependencies or credentials. See
[docs/data_phase1.md](docs/data_phase1.md) for exact commands, source constraints, and GPU guidance.

On a CUDA-capable host, install the optional CUDA PyTorch runtime with
`uv sync --extra dev --extra data-sources --extra neural`. Exercise benchmark-calibrated auto
selection with
`uv run --extra neural python scripts/generate_synthetic.py --config configs/data/synthetic/gpu_auto_smoke.yaml`;
the dataset manifest records the resolved backend. Explicit `--device cuda` and `--device cpu`
remain available for controlled comparisons.

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
