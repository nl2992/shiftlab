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

The delayed-feedback study separately tests event-order monitoring when labels arrive late. Its
2,000-seed null calibration found false-escalation estimates from 0% to 1.50% across the registered
stationary and benign-variance controls. In the disjoint primary alternative confirmation, the
fixed eight-start e-process mixture detected late, weaker harm in 933/2,000 streams, compared with
100/2,000 for the same-family full-stream betting process (paired exact McNemar `p=5.37e-245`).
An independently seeded 2,000-stream replication found 895/2,000 versus 100/2,000, with paired exact
McNemar `p=8.89e-229`. Across both blocks, descriptive detection was 45.70% versus 5.00%. This is
evidence for these fixed synthetic conditions, not a general superiority or novelty claim. A
separate 12-cell confirmation grid (2,000 paired streams per cell) found a positive restart-mixture
detection gain in every tested cell, ranging from 1.2 to 68.4 percentage points. All 12 exact paired
tests remained significant after Holm correction (largest adjusted p=3.03e-6); these results remain
specific to the registered independent synthetic settings. See the
[calibration and confirmation protocol](docs/delayed_null_calibration_protocol.md), [calibration
metrics](outputs/delayed_null_calibration_2000/), [first confirmation](outputs/delayed_feedback_confirmation_2000/),
the [replication](outputs/delayed_feedback_replication_2000/), and the
[12-cell grid](outputs/delayed_feedback_grid_confirmation_2000/).
No figure is included for this study because its protocol requires PaperBanana and that tool was not
available when the results were generated.

A separate delayed-feedback validation now combines the history-predictable query process with a
two-state Markov volatility regime whose paired-cost conditional mean is zero in each latent state.
At a fixed 12-event outcome-independent delay, an independent 2,000-stream-per-cell null calibration
passed the registered 5% simultaneous upper-limit gate (largest exact upper limit 2.11%). In a
disjoint 2,000-stream-per-dose confirmation, the predictable-bound system improved equal-weight
detection by 6.03 percentage points (paired 95% bootstrap interval [5.33, 6.75]) and used about 130
fewer labels per stream (interval [-134, -126]) than the same history-only query system with a fixed
bound. The gain was concentrated at stronger harms; the system had 31/2,000 pre-onset alarms per
dose block, all counted as nondetections. This validates the complete monitor-query system only for
the registered Markov DGP, frozen action pair, full-history conditional-mean null, and complete
delay-12 feedback; it does not isolate the bound's effect or establish a new algorithm. Protocol,
results, per-stream Parquet, and manifests are in
[`docs/delayed_markov_bound_confirmation_results.md`](docs/delayed_markov_bound_confirmation_results.md)
and [`outputs/delayed_markov_predictable_confirmation_2000/`](outputs/delayed_markov_predictable_confirmation_2000/).
No figure was made because PaperBanana was unavailable; this result is adequately represented by
tables and machine-readable stream metrics.

A matched-path ablation then held the propensity sequence, queried labels, and processed prefix fixed
while varying only the support bound. Constant `q=0.20` produced identical outcomes under the fixed
and eventwise bounds, as expected. For three periodic schedules with the same 0.20 mean query rate,
the eventwise-bound system improved exploratory macro detection by 4.58–7.50 percentage points over
the conservative fixed bound; all paired intervals were positive on this 60-stream development
block. These null cells are too small to calibrate false alarms, and schedule selection remains
exploratory. See the [protocol and results](docs/matched_path_bound_ablation_results.md) and
[stream-level metrics](outputs/matched_path_bound_ablation_60/).

An independent calibration and disjoint confirmation then tested the frozen `q∈{0.05,0.80}`
periodic schedule. All four simultaneous 95% null upper limits were at most 3.29%, below the
registered 5% gate. With query paths held identical, eventwise bounds improved mean detection by
5.41 points (paired 95% interval [4.59, 6.25]) and used exactly the same labels as the fixed bound.
The effect was concentrated at harm effects 0.40 and 0.60, while the weakest dose remained difficult.
This isolates a simulator-specific range effect; it does not establish a new betting algorithm or
external validity. See the [confirmation report](docs/matched_path_bound_confirmation_results.md)
and the [calibration and confirmation artifacts](outputs/matched_path_bound_confirmation_2000/).

A separate predictable stake-portfolio screen compared equal per-event rebalancing with the fixed
mixture on identical delayed-feedback paths. In the 60-seed development block, equal rebalancing
increased macro detection from 6.25% to 11.25% (+5.00 points; paired bootstrap 95% interval
[+2.50, +7.92]). Its fresh 2,000-stream-per-cell null calibration did not clear the frozen
simultaneous 5% upper-limit gate: the exact-null upper limit was 5.54% for equal rebalancing.
Therefore the disjoint harm confirmation was not run; the development power result is exploratory
only. The selected `eta=0` rule uses uniform weights at each event and is not history-adaptive.
This is a standard predictable betting construction, with no novelty claim. See the
[protocol and decision](docs/predictable_stake_portfolio_results.md),
[development artifacts](outputs/predictable_stake_portfolio_development/), and
[null calibration](outputs/predictable_stake_portfolio_calibration_2000/).

The separate Paper 3 DIVE benchmark has 1,260 CUDA-generated rows (30 paired seeds, six scenarios,
seven monitoring/query variants). The corrected null audit counts every alarm on stationary and
benign-nuisance population-null streams as a false escalation, even when that particular finite
covariate path has an oracle average above the margin. The full-feedback single-start monitor
alarmed on 1/30 streams in each control; each sparse method had 0/30 alarms, with wide Wilson
intervals that include the nominal 5% rate. Under boundary-local harm, full feedback detected 30/30
streams and uniform direct inverse-propensity monitoring detected 14/30; the proxy-corrected and
adaptive-query variants detected fewer in this pilot. These results do not show an adaptive-query
advantage. The complete table, control audit, and Parquet seed rows are in
[`outputs/reports/method_comparison.md`](outputs/reports/method_comparison.md) and
[`outputs/metrics/method_comparison.parquet`](outputs/metrics/method_comparison.parquet).

The extended Paper 3 query-allocation comparison also covers boundary-local harm, residual-variance
shift, recurring regimes, and deliberately harmful adaptation. Its locked protocol is in
[`docs/hard_budget_extended_scenarios_protocol.md`](docs/hard_budget_extended_scenarios_protocol.md),
and the 60-seed CUDA results (1,200 method-stream rows), paired bootstrap summaries, and figure are
in `outputs/hard_budget_extended_scenarios_60/`. In this exploratory block, all per-stream hard
budgets were respected and no false escalations occurred, while harmful-stream detection ranged
from 0/60 to 8/60 depending on scenario and query policy. The low rates are descriptive and do not
establish a method ranking or a false-alarm guarantee. See the [Paper 3 research log](papers/paper3_cost_aware_adaptation/research_log.md)
for the interpretation and per-scenario paired RMSE intervals. The control scenarios' population
paired excess costs were independently integrated and verified below the 0.10 harm margin; a
finite-stream oracle flag above the margin is a path-specific diagnostic, not a population-null
failure. See the [population harm validation](outputs/reports/dive_population_harm_validation.md)
and reproduce it with `uv run python scripts/validate_dive_population_harm.py`.

The betting-scale sensitivity experiment compares the existing five-stake e-process with a fixed
13-stake geometric mixture on matched harmful-shift streams and stationary/benign controls. The
broader equal-weight mixture detected fewer harmful streams in this block, so it is retained as a
negative grid-search result rather than promoted as an improved method. The bounded-mean guarantee
is the same for both mixtures under the documented assumptions. See the
[multiscale betting protocol](docs/multiscale_betting_protocol.md) and its paired output reports.

A follow-up protected mixture retained 90% prior weight on the baseline stakes and put 10% on
smaller bets. It also detected fewer harmful streams than the baseline in a fresh matched block
(32/1,200 versus 39/1,200); the seven discordant outcomes all favored the baseline. The paired
seed-cluster analysis is reproducible with `scripts/analyze_betting_mixture.py`; see the
[protected-mixture protocol](docs/protected_multiscale_betting_protocol.md) and
`outputs/hard_budget_protected_multiscale_60/` for the metrics, report, figure, and manifest.

The current full initial run is documented in
[`data/reports/decision_harm_phase2/20261023T0230Z-final-30seed/baseline_report.md`](data/reports/decision_harm_phase2/20261023T0230Z-final-30seed/baseline_report.md).

### DIVE: evidence-efficient decision-harm monitoring

The first DIVE implementation compares full feedback, uniform direct and prediction-powered
estimates, a clearly labeled PPRM-style adaptive-reliance analogue, and uncertainty-,
residual-variance-, decision-value-, and expected-evidence-growth-guided label acquisition. It
uses paired deployed-minus-reference costs, prequential prediction-powered corrections, bounded
mean e-processes, and a fixed mixture over prespecified start times. The implementation and
assumptions are described in [`docs/methods_and_assumptions.md`](docs/methods_and_assumptions.md);
the closest prior work and current novelty boundary are in
[`references/closest_competitors.md`](references/closest_competitors.md). Open proof targets are in
[`docs/theory_targets.md`](docs/theory_targets.md).

The hard-budget runner now also includes a development adaptation of robust active statistical
inference: it selects a path between residual-variance and uniform querying using a validation-only
minimax variance score. On 30 CUDA seeds in each of three scenarios, it reduced stream-mean RMSE
relative to uniform in the benign-nuisance cell, but did not improve uniformly across scenarios or
increase harm detections (all allocation variants detected 0/30 boundary-local harms). This is an
exploratory comparator with an uncalibrated radius setting, not a sequential guarantee or novelty
claim. See the [development results](docs/robust_active_inference_development_results.md) and
machine-readable [Parquet output](outputs/robust_active_inference_development/metrics/hard_budget_comparison.parquet).

A separate six-value L2-radius development grid (30 new seeds per scenario) found a narrow macro
RMSE minimum at radius fraction 0.50, nearly tied with 0.25; neither choice increased harm
detection, which remained 0/30 for every allocation. The radius is not promoted as a default.
See the [frozen radius protocol](docs/robust_active_inference_radius_grid_protocol.md), [results](docs/robust_active_inference_radius_development_results.md), and
[seed-level metrics](outputs/robust_active_inference_radius_development/metrics/hard_budget_comparison.parquet).

The paired acquisition-budget frontier evaluates seven policies at 10%, 20%, and 25% hard
label-dollar caps over 60 common-seed streams in four scenarios. Every method respected its cap;
all methods detected 0/60 reachable harmful streams at every cap, while exact and robust
mixture-growth allocation reduced stream-mean estimation RMSE against uniform. This separates
estimation accuracy from sequential decision-harm power; zero detections in 60 streams do not
establish either useful power or 5% calibration. The 30% endpoint proved infeasible under the
fixed propensity and tariff bounds, so the protocol replaced it with the highest checked-feasible
25% level before generating those results. See the [screening protocol](docs/budget_frontier_protocol.md),
[measured findings](docs/budget_frontier_results.md), [full report](outputs/budget_frontier_60/reports/budget_frontier.md),
[metrics](outputs/budget_frontier_60/metrics/budget_frontier.parquet), [figure](outputs/budget_frontier_60/figures/budget_frontier.png),
and [manifest](outputs/budget_frontier_60/reports/manifest.json).

A follow-up horizon grid keeps the total realized label-dollar cap at **$720** while exposing the same 4,000-event stream for 1,000, 1,800, or 2,600 monitoring events. Across 30 seeds per cell, the fixed eventwise mixture detected 29/30 early-boundary harms at the longest horizon, but only 4/30 late-boundary harms; predictable variance was statistically indistinguishable after Holm adjustment. PM-EB and the 10% block-PPI mixture recorded zero detections across the harmful cells. Controls had 0/30 alarms, which is too small for calibration. The block method remains a comparator, and these development results do not establish a universal winner. See the [frozen protocol](docs/fixed_dollar_horizon_grid_protocol.md), [full report](outputs/fixed_dollar_horizon_grid_development/analysis/fixed_dollar_horizon_results.md), [paired contrasts](outputs/fixed_dollar_horizon_grid_development/analysis/paired_detection_contrasts.csv), [figure](outputs/fixed_dollar_horizon_grid_development/analysis/fixed_dollar_horizon_detection.png), and [analysis manifest](outputs/fixed_dollar_horizon_grid_development/analysis/analysis_manifest.json). Reproduce with `uv run python scripts/run_fixed_dollar_horizon_grid.py --seeds 30 --seed-offset 56100000 --budget-dollars 720 --device cuda`, followed by `uv run python scripts/analyze_fixed_dollar_horizon_grid.py`.

An equal four-start e-process mixture was then tested on a disjoint 30-seed block under the same $720 cap and horizons. It detected **0/30** late-boundary harms at 2,600 events versus **1/30** for the full-stream mixture, while early-boundary detections fell from 29/30 to 22/30 and recurring-regime detections from 13/30 to 6/30. The adaptation cell was 23/30 versus 22/30, an inconclusive one-stream difference. This is evidence against advancing the equal four-start construction as the lead monitor in these settings; zero alarms in 30 null-control streams do not establish 5% calibration. The construction is mathematically standard and remains a comparator. See the [protocol](docs/started_mixture_horizon_protocol.md), [results](outputs/started_mixture_horizon_development/analysis/started_mixture_results.md), [paired contrasts](outputs/started_mixture_horizon_development/analysis/paired_start_mixture_contrasts.csv), [figure](outputs/started_mixture_horizon_development/analysis/started_mixture_detection.png), and [manifest](outputs/started_mixture_horizon_development/analysis/analysis_manifest.json). Reproduce with `uv run python scripts/run_started_mixture_horizon_grid.py --seeds 30 --seed-offset 57100000 --budget-dollars 720 --device cuda`, followed by `uv run python scripts/analyze_started_mixture_horizon_grid.py`.

A fresh-seed monitor diagnostic compared the fixed gate with predictable variance and PM-EB using
identical sampled labels and globally bounded increments. All three had 0/30 detections in both
harmful scenarios under all three query policies, with all onsets reached; 0/30 null escalations
has a 11.4% Wilson upper endpoint and cannot establish 5% calibration. See the
[protocol](docs/monitor_power_diagnostic_protocol.md), [measured findings](docs/monitor_power_diagnostic_results.md),
[full metrics](outputs/monitor_power_diagnostic_30/metrics/hard_budget_comparison.parquet),
[monitor summary](outputs/monitor_power_diagnostic_30/metrics/monitor_comparison.csv), and
[figure](outputs/monitor_power_diagnostic_30/figures/monitor_power_comparison.png). A paired
uniform-query sensitivity then changed only the global bound from 198.9 (`q_min=.05`) to 45.9
(`q_min=.20`): fixed-mixture and predictable-variance monitors detected 19–20/30 harmful streams,
with zero alarms in either 30-stream null control. Query counts, spend, and horizon were identical.
This implicates bound width as a power bottleneck, but the 0/30 null result has an 11.4% Wilson
upper endpoint and does not establish 5% calibration. See the [paired results](docs/monitor_bound_sensitivity_results.md),
[machine-readable paired metrics](outputs/monitor_bound_sensitivity_qmin020/metrics/paired_qmin_sensitivity.csv),
and [full paired report](outputs/monitor_bound_sensitivity_qmin020/reports/paired_qmin_sensitivity.md).
The next calibration run is pre-specified for 2,000 streams in each of two null controls at
`q_min=.20`; its seed block, endpoints, and interpretation rules are recorded in the
[calibration protocol](docs/null_calibration_qmin020_protocol.md).
That run has now completed: fixed-mixture, predictable-variance, and PM-EB each had 0/2,000
false escalations in both controls. For the four pre-specified fixed-mixture/predictable-variance
cells, the Bonferroni simultaneous one-sided 95% exact upper limit is 0.00219, under the registered
synthetic assumptions. See the [calibration report](outputs/null_calibration_qmin020_2000/reports/null_calibration_results.md),
[CSV metrics](outputs/null_calibration_qmin020_2000/metrics/null_calibration.csv),
[stream metrics](outputs/null_calibration_qmin020_2000/metrics/hard_budget_comparison.parquet),
and [figure](outputs/null_calibration_qmin020_2000/figures/null_calibration.png). A disjoint
200-stream-per-alternative confirmation then found fixed-mixture detection rates of 72.5% for
boundary-local harm and 65.5% for recurring regimes, with every onset reached. Predictable
variance reached 62.5% and 63.0%; PM-EB reached 4.5% and 5.0%. Fixed mixture had a paired advantage
over variance for boundary-local harm after Holm adjustment, while the recurring-regime difference
was inconclusive. See the [frozen confirmation protocol](docs/harm_confirmation_qmin020_protocol.md),
[report](outputs/harm_confirmation_qmin020_200/reports/harm_confirmation_results.md),
[paired metrics](outputs/harm_confirmation_qmin020_200/metrics/harm_confirmation_paired_tests.csv),
and [stream metrics](outputs/harm_confirmation_qmin020_200/metrics/hard_budget_comparison.parquet).
The completed 36-cell CUDA development grid varies harm severity, abrupt onset, and horizon across
1,080 stream-cell observations (30 paired seeds per cell). All streams had material harm, every
harm onset was reached before budget stopping, and all realized label-dollar caps were respected.
Across cells, mean detection rates were 0.500 for fixed mixture, 0.435 for predictable variance,
and 0.100 for PM-EB in boundary-local harm; rates were 0.441, 0.426, and 0.093 respectively for
recurring regimes. In the central boundary-local setting (`n=3200`, severity 1.5), fixed-mixture
detection was 0.83, 0.63, and 0.20 as onset moved from 35% to 50% to 65% of the stream; it was
0.27, 0.63, and 0.77 as severity increased from 0.75 to 1.5 to 2.25, and 0.43, 0.63, and 0.80
as horizon increased from 2,400 to 4,000 events. The horizon comparison also increases the total
dollar budget at a fixed 20% budget rate, so it combines more observation time with more resources.
This 30-seed alternative-only development screen has no false-alarm controls; the separate null
calibration above addresses only its registered simulator assumptions. These results support
fixed mixture as a useful baseline in the tested settings, not a novel method or universal ranking.
See the [frozen protocol](docs/harm_power_grid_protocol.md), [measured findings](outputs/harm_power_grid_30/reports/harm_power_grid_results.md),
[full monitor table](outputs/harm_power_grid_30/reports/harm_power_grid.md), [Parquet stream metrics](outputs/harm_power_grid_30/metrics/harm_power_grid.parquet),
[cell summaries](outputs/harm_power_grid_30/metrics/harm_power_grid_summary.csv), [paired contrasts](outputs/harm_power_grid_30/metrics/harm_power_grid_paired_tests.csv),
[trend summary](outputs/harm_power_grid_30/metrics/harm_power_grid_trends.csv), [figure](outputs/harm_power_grid_30/figures/harm_power_grid.png),
and [run manifest](outputs/harm_power_grid_30/reports/manifest.json). Reproduce with
`uv run python scripts/run_harm_power_grid.py --seeds 30 --device cuda --output outputs/harm_power_grid_30`;
regenerate the report and figure with `uv run python scripts/analyze_harm_power_grid.py`.

The repeated-candidate hard-budget benchmark extends this work to sparse feedback. It freezes a
13-candidate family and validation-based ranking before monitoring, then compares direct
inverse-propensity with prediction-powered monitoring under 10% and 20% pathwise label caps. Across
60 CUDA seeds in seven synthetic scenarios, the exact-copy candidate family produced no
certificates. At the 20% cap, direct IPW certified candidates in the boundary-local and recurring
regime alternatives (18–28% depending on query policy), while prediction-powered monitoring
certified none. No estimator/query combination promoted at the 10% cap. The paired intervals
suggest validation-rank alpha spending outperformed equal and validation-power allocation in
several alternatives, but are unadjusted across the comparison grid. Decision-value querying did
not consistently outperform uniform querying. This is a power and budget diagnostic, not a
confirmed superiority or novelty result. See the [benchmark report](outputs/budgeted_promotion_grid_ipw/reports/budgeted_promotion_grid.md),
[stream metrics](outputs/budgeted_promotion_grid_ipw/metrics/budgeted_promotion_streams.parquet),
[paired contrasts](outputs/budgeted_promotion_grid_ipw/metrics/budgeted_promotion_paired_contrasts.parquet),
[plot](outputs/budgeted_promotion_grid_ipw/figures/budgeted_promotion_grid.png), and
[manifest](outputs/budgeted_promotion_grid_ipw/reports/manifest.json). Reproduce with
`uv run shiftlab-dive-budgeted-promotion --seeds 60 --seed-offset 24102026 --n 3200 --device cuda
--output outputs/budgeted_promotion_grid_ipw`.

A mathematically grounded extension uses a candidate- and event-specific betting bound derived from
the two possible paired costs, visible covariates, known query propensity, and a frozen proxy. It is
valid under the stronger pointwise conditional harm null given current covariates; the history-only
null does not justify covariate-dependent scaling. A separate CUDA calibration with 2,000
nondegenerate null streams per cell observed false-escalation rates below 2.3% for both global and
local scales at a 5% threshold. In the cost-ratio-5, 30%-label alternative, the local bound crossed
415/2,000 times versus 280/2,000 globally (paired difference +6.75 points, 95% t interval +5.16 to
+8.34); across the 27 exploratory cells, results were mixed. This is an early signal under explicit
assumptions, not a general improvement claim. See the
[calibration report](outputs/decision_local_bound_calibration/reports/decision_local_bound_calibration.md),
[stream metrics](outputs/decision_local_bound_calibration/metrics/decision_local_bound_streams.parquet),
[paired contrasts](outputs/decision_local_bound_calibration/metrics/decision_local_bound_paired_contrasts.parquet),
and [manifest](outputs/decision_local_bound_calibration/reports/manifest.json).

That local scale did not carry over to the 13-candidate adaptation grid: it produced zero e-process
crossings across 15,120 stream-policy rows, despite shrinking the mean eventwise bound to 6.9% of
the fixed global scale. Also, the local test's pointwise conditional null is not the aggregate
mean-benefit null needed for safe candidate promotion; a crossing would only establish positive
conditional gain somewhere, not positive total expected net value. The [matched candidate-grid
report](outputs/budgeted_promotion_grid_local_bound/reports/budgeted_promotion_grid.md) records this
negative result. The method remains a diagnostic direction, not a promotion gate.

A mixed-sign aggregate-null CUDA calibration directly tests this limitation. Two equally likely strata have conditional gains of +0.12 and −0.12, so aggregate expected gain is exactly zero. Across 2,000 streams per cell, global-bound crossing rates were 1.2–2.1%; decision-local rates were 2.5–5.8%. This shows why local crossings cannot authorize aggregate promotion. Results and the reproduction command are in [the calibration report](outputs/mixed_mean_null_local_bound/reports/mixed_mean_null_calibration.md), with stream metrics and checksums beside it.


The shadow-promotion experiment evaluates a frozen logistic recalibration candidate and an
incumbent snapshot on fresh forward-time labels, applies candidate-index alpha spending, and
reports certification behavior in
[`outputs/promotion_experiment_corrected/figures/adaptation_promotion.png`](outputs/promotion_experiment_corrected/figures/adaptation_promotion.png),
[`outputs/promotion_experiment_corrected/metrics/promotion_comparison.parquet`](outputs/promotion_experiment_corrected/metrics/promotion_comparison.parquet),
and [`outputs/promotion_experiment_corrected/reports/promotion_comparison.md`](outputs/promotion_experiment_corrected/reports/promotion_comparison.md).
The earlier `outputs/metrics/promotion_comparison.parquet` predates the absorbing certificate fix
and is superseded. The one-step cost-aware controller is available in `shiftlab.dive.controller`;
its forecasts are supplied inputs and it is a heuristic without a utility guarantee. The
separate `CertifiedPromotionRollback` reference policy now connects two bounded-mean e-processes:
one certifies a frozen candidate on shadow feedback, and another can return to fallback on fresh
forward deployment feedback. Its CUDA development benchmark compares continue, unconditional
promotion, promotion-only, and promotion-plus-rollback under six scenarios and hard label caps.
The 2,000-seed run observed 1.0% false promotion under the zero-gain shadow null (simultaneous
exact upper bound 1.79% across the corrected 18-cell calibration family). Under early reversal,
rollback improved expected net utility by 3.07
units versus promotion-only (seed-bootstrap 95% interval 2.48–3.70), while the policy remained
far below continue in that scenario. Persistent-benefit monitoring reduced net utility by about
1.99 units through label costs, and shadow-only benefit exposed the gap between shadow and
deployment value. These are diagnostic simulation results, not a selected policy or novelty
claim. See the [protocol](docs/closed_loop_intervention_protocol.md), [results](docs/closed_loop_intervention_results.md),
[metrics](outputs/closed_loop_intervention/metrics.parquet), and [manifest](outputs/closed_loop_intervention/manifest.json).
Reproduce with `uv run python -m shiftlab.dive.closed_loop_intervention --device cuda --seeds 2000
--horizon 800 --bootstrap-replicates 10000 --output-dir outputs/closed_loop_intervention`.

The follow-up [sensitivity grid](docs/intervention_sensitivity_protocol.md) evaluated 216
reversal cells plus four controls. At the reference label price, the development-selected
setting was `q=0.80`, a 40% hard label cap, and promotion/rollback costs of 0.05; its macro
rollback gain over promotion-only was 6.05 utility units (development interval 4.96–7.14).
Fresh-seed confirmation estimated a gain of 5.51 (95% interval 5.32–5.69). Its first
2,000-stream zero-deployment rollback calibration had an upper limit of 2.64%, just above the
2.5% target. A separately reported 10,000-stream calibration replication passed the nine-cell
simultaneous gate (worst upper limit 1.64%) without changing the frozen policy. These results
apply to the stated independent Bernoulli simulation only. See the [development results](docs/intervention_sensitivity_results.md),
[confirmation results](docs/intervention_confirmation_results.md),
[confirmation protocol](docs/intervention_confirmation_protocol.md),
[calibration replication protocol](docs/intervention_calibration_replication_protocol.md),
[confirmation metrics](outputs/intervention_confirmation/metrics.parquet), and
[replication calibration table](outputs/intervention_calibration_replication/error_calibration.csv).

The initial CUDA benchmark is saved in `outputs/`. It contains 1,260 monitor rows (30 seeds × 6
scenarios × 7 methods) and 360 candidate-promotion rows. With 2,400 labels per stream, full-feedback
monitoring detected all harmful boundary-local, harmful-adaptation, and recurring-regime streams
(median delays 357, 367, and 147 events). At roughly 238 labels per stream, uniform direct monitoring
detected 14/30, 18/30, and 15/30 of those streams, with median delays of 1,120, 1,110, and 2,001
events. The prediction-powered and feature-guided acquisition variants detected few or none in these
conditions. There was one full-feedback false escalation in 30 streams in each of the stationary
and benign-nuisance controls; the 95% Wilson intervals are broad at this sample size. The
prespecified start-time mixture made no detections in
this run, so its practical sensitivity remains unresolved. These are synthetic descriptive results,
not evidence of real-world performance or superiority to faithfully reproduced published methods.

The candidate test certified the exact incumbent-copy control in 0/150 streams where its
pointwise-null assumptions applied. The frozen recalibration candidate was certified in 30/30
boundary-local streams, 30/30 recurring-regime streams, and 30/30 harmful-adaptation streams. These
rates are exploratory; only the exact-copy control directly checks the stated null in this setup.
Independent integration gives population excess cost 0.0793 for both stationary and
benign-nuisance controls, below the 0.10 material-harm margin. Finite-stream oracle excursions
remain recorded as diagnostics and do not redefine these population-null controls as alternatives.
Every alarm in either control counts as a false escalation.

The forward-time candidate-grid experiment (`shiftlab-dive-promotion-grid`) adds twelve frozen
logistic candidates and an exact incumbent-copy control, validation ranking, candidate-index alpha
spending, sequential certification, two fixed-horizon gates, and a later untouched deployment
slice. It compares never promoting, unconditional validation selection, Hoeffding and
empirical-Bernstein certification, and sequential certification. The empirical-Bernstein gate
assumes independent bounded monitoring outcomes, including deterministic non-identical regimes;
it tests average monitor-period benefit and does not cover serial dependence. It uses an established
bound, not a new theorem. The sequential certificate is absorbing and records the first threshold
crossing. Candidate rankings are frozen before shadow monitoring; final-slice outcomes measure
deployment reversals, not statistical type-I error. Reproduce the expanded 30-seed run with `uv run
shiftlab-dive-promotion-grid --seeds 30 --seed-offset 20381023 --n 3200 --d 16 --device cuda
--output outputs/promotion_grid_eb`. Rebuild seed-level intervals with
`uv run python scripts/analyze_promotion_grid.py`. See
[`docs/methods_and_assumptions.md`](docs/methods_and_assumptions.md) for the assumptions.

Expanded artifacts: [comparison report](outputs/promotion_grid_eb/reports/promotion_grid_comparison.md),
[seed-level uncertainty report](outputs/promotion_grid_eb/reports/strategy_uncertainty.md),
[candidate metrics](outputs/promotion_grid_eb/metrics/promotion_grid_candidates.parquet),
[strategy metrics](outputs/promotion_grid_eb/metrics/promotion_grid_strategies.parquet),
and [figure](outputs/promotion_grid_eb/figures/promotion_grid_outcomes.png). The previous
absorbing-certificate run without this gate remains in `outputs/promotion_grid_corrected/`.
Across the six scenarios, the exact-copy candidate certified in 0/180 tests (95% Wilson upper
bound 0.021). The empirical-Bernstein gate promoted in 30/30 boundary-local-harm and harmful-
adaptation streams, 29/30 recurring-regime streams, 1/30 residual-variance streams, and 0/30
stationary or benign-nuisance streams. Mean expected deployment net gains were 271.8 (95% seed-
level t interval 255.9–287.6), 279.1 (273.0–285.3), and 257.0 (233.5–280.4) in those three
harmful scenarios. It also declined 29/30 candidates under residual variance, where its mean gain
was only 3.4 (−3.5–10.2), and all candidates in benign nuisance, where mean gain was −24.3
(−80.6–32.0) for sequential certification and −65.8 (−148.5–16.9) for unconditional validation
selection. For benign nuisance, empirical Bernstein versus unconditional selection had paired mean
gain difference 65.8, with a wide 95% interval (−16.9–148.5). In stationary streams, it promoted
none while sequential certification promoted 21/30; this benchmark's incumbent is improvable even
without a shift, so intervention value and shift detection are distinct. The basic sequential test
also promoted in 15/30 benign-nuisance streams, while the empirical-Bernstein fixed-horizon gate
did not. The simpler Hoeffding gate had zero power in all six settings at these sample sizes.
Intervals are descriptive across 30 independent synthetic seeds and are not multiplicity-adjusted.
The generator produces independent events with deterministic regime schedules; these findings do
not establish calibration under serial dependence, delayed/adaptive feedback, or action-dependent
outcomes. Results support a benchmark-specific comparison, not a novelty or general-performance
claim. The original `outputs/promotion_grid/` results used a non-absorbing certification flag and
are superseded by the corrected runs.

The follow-up timing benchmark compares full-start and three-start sequential e-processes with
fixed-horizon empirical-Bernstein and Hoeffding gates on five benefit schedules, with 1,000
independent CUDA streams per schedule. Under no benefit, both sequential rules promoted 32/1,000
streams (3.2%, Wilson 95% CI 2.3–4.5%). For late persistent benefit, the three-start process
promoted 998/1,000 and achieved mean oracle future net gain 212.6 (95% seed-level t interval
211.5–213.8); the full-start process promoted 688/1,000 with gain 120.5 (115.4–125.7), and the
empirical-Bernstein gate promoted 520/1,000 with gain 74.9 (70.4–79.3). Under a benefit reversal,
the sequential rules promoted 997/1,000 and 996/1,000 candidates after the early positive phase,
but their mean oracle future net gains were −30.1 (−30.8 to −29.4) and −35.2 (−36.0 to −34.4).
This shows that a valid test of eventwise shadow improvement does not establish persistence of
future candidate value. The empirical-Bernstein gate promoted 1/1,000 under reversal, but paid the
latency of its fixed horizon. These are controlled synthetic results, not a new-method or universal
superiority claim. See [the timing report](outputs/promotion_timing_v6/reports/promotion_timing.md),
[metrics](outputs/promotion_timing_v6/metrics/promotion_timing_summary.parquet), and
[figure](outputs/promotion_timing_v6/figures/promotion_timing.png). Reproduce with
`uv run shiftlab-dive-promotion-timing --seeds 1000 --seed-offset 20401023 --n 3200 --device cuda
--output outputs/promotion_timing_v6`.

The follow-up [switching-cost and reversal grid](outputs/promotion_robustness_grid_corrected/reports/promotion_robustness_grid.md)
compares those gates with three two-phase persistence splits across six fixed schedules and four
one-time switching charges, using 1,000 paired CUDA streams per schedule. It finds no uniformly best
rule: persistence confirmation suppresses early long reversals, but an early split can still promote
before a later reversal, while later splits miss persistent or late-onset value. These are
descriptive synthetic comparisons with no multiplicity adjustment across grid cells. See the
[seed-level metrics](outputs/promotion_robustness_grid_corrected/metrics/promotion_robustness_summary.parquet),
[figure](outputs/promotion_robustness_grid_corrected/figures/promotion_robustness_grid.png), and
[`docs/methods_and_assumptions.md`](docs/methods_and_assumptions.md).

A two-phase persistence benchmark compares discovery fractions 25%, 50%, and 75%.
Each disjoint phase runs a level-0.05 e-process, and promotion requires both to cross. This is an
intersection-union test of the null that at least one phase has nonpositive conditional gain; the
conjunctive rule is valid at level 0.05 without splitting alpha between phases. In 1,000 CUDA
streams, a 50% discovery split reduced benefit-reversal promotions to 6/1,000 (0.6%, Wilson 95% CI
0.3–1.3%) from 997/1,000 for the full-start e-process. Mean oracle future net gain was still
negative (−0.372 [−0.669, −0.075]), while never promoting had zero gain. With persistent benefit,
the split promoted 974/1,000 and gained 155.95 [153.89, 158.02], below the full-start process's
255.73 [254.31, 257.15]. For late-onset benefit, the 75% discovery split promoted only 42/1,000,
versus 998/1,000 for the multi-start process. This established statistical construction reduces
harmful promotions but does not dominate on net utility and is not a novelty claim. See the
[full comparison](outputs/persistence_promotion_grid/reports/persistence_promotion_grid.md),
[Parquet metrics](outputs/persistence_promotion_grid/metrics/persistence_promotion_summary.parquet),
and [figure](outputs/persistence_promotion_grid/figures/persistence_promotion_grid.png). Reproduce
with `uv run shiftlab-dive-persistence-grid --seeds 1000 --seed-offset 20401023 --n 3200
--device cuda --discovery-fractions 0.25 0.5 0.75 --output outputs/persistence_promotion_grid`.

A second grid tests whether the fixed rank schedule spends the promotion error budget effectively.
It compares rank spending, equal allocation over the finite candidate set, and validation-power
weights for both sequential and empirical-Bernstein promotion. The validation-power rule uses an
independent pilot split, reserves 10% of the total level uniformly, and distributes the rest using
clipped positive validation z-scores. Conditional on validation, all candidate levels sum to at most
0.05, preserving the union-bound familywise guarantee. Independent-pilot weighted testing is prior
work; this benchmark asks whether that established idea improves decision value in this candidate
promotion setting. The final 30-seed CUDA comparison is in `outputs/promotion_grid_alpha_final/`. Under
boundary-local harm, the empirical-Bernstein rank allocation promoted 30/30 streams versus 25/30
for equal allocation and 27/30 for validation-power weighting. Its paired expected-gain advantage
over equal allocation was 42.5 (95% interval 0.2–84.9); its advantage over validation-power
weighting was 25.2 (−8.0–58.4). Under recurring regimes, the respective promotion counts were
30/30, 22/30, and 26/30; rank's paired gain advantage over equal allocation was 65.3 (14.5–116.1),
and over validation weighting was 37.9 (−1.9–77.7). All three promoted 30/30 in the harmful-
adaptation scenario. The sequential rank schedule promoted 20/30 stationary streams, compared
with 16/30 for equal and 18/30 for validation weighting; paired gain differences favoring rank
were uncertain (5.5, −2.4–13.3; and 2.5, −4.5–9.6). Exact-copy controls produced zero false
certificates under all five allocation-and-test combinations across 180 tests each. These are
descriptive intervals from 30 seeds without multiplicity adjustment. In this benchmark, rank-based
spending was strongest for the fixed-horizon gate when the best validation-ranked candidates were
also strong alternatives; validation weighting did not improve outcomes. This is a negative result
for the proposed weighting baseline, not a novel algorithm claim. See the [comparison report](outputs/promotion_grid_alpha_final/reports/promotion_grid_comparison.md), [paired uncertainty report](outputs/promotion_grid_alpha_final/reports/strategy_uncertainty.md), [candidate metrics](outputs/promotion_grid_alpha_final/metrics/promotion_grid_candidates.parquet), [strategy metrics](outputs/promotion_grid_alpha_final/metrics/promotion_grid_strategies.parquet), and [figure](outputs/promotion_grid_alpha_final/figures/promotion_grid_outcomes.png). Reproduce with `uv run shiftlab-dive-promotion-grid --seeds 30 --seed-offset 20381023 --n 3200 --d 16 --device cuda --output outputs/promotion_grid_alpha_final`.

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

An exploratory allocation maximizes a pre-monitor model's stake-weighted expected log-wealth
increment under an expected label budget. Its per-event objective is concave in query propensity,
and a dual multiplier solves the constrained allocation. This is optimal only for the estimated
surrogate, not detection power or the exact log-mixture e-value. On 30 fresh CUDA seeds, the raw
allocation's query rate rose from 10% on validation to 13.9% under benign nuisance shift; it
detected 0/30 boundary-harm streams versus 1/30 for uniform. A rate-stabilized version with
`delta=0.01` held the mean propensity near 10%, but detected 0/30 versus 3/30 for uniform on a
separate 30-seed block. It has not demonstrated a useful detection gain. Paired results are in
[`evidence-growth stabilized comparison`](outputs/evidence_growth_stabilized_replication_30/reports/evidence_growth_paired_comparison.md)
and [`raw evidence-growth comparison`](outputs/evidence_growth_replication_30/reports/evidence_growth_paired_comparison.md).

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
The subsequent [evidence-directed allocation screen](docs/evidence_directed_allocation_results.md)
tested a predictable propensity that rises with prior e-process evidence and tapers with remaining
budget. It respected all caps and reached all 30 boundary-harm onsets, but detected 0/30 harms,
compared with 0/30 for uniform; it used 230 versus 346 label dollars on average and its stream-mean
RMSE was higher by 0.0165 (paired 95% interval [-0.0011, 0.0323]). Its urgency signal stayed near
the propensity floor. Treat this as an inconclusive development result, not calibration; the next
step is a separately seeded grid of prespecified urgency curves. The [protocol](docs/evidence_directed_allocation_protocol.md)
and complete tabular outputs are checked in under `outputs/evidence_directed_allocation_30/`.
The fresh [nine-curve urgency grid](docs/evidence_urgency_curve_grid_results.md) then tested
activation offsets 0, 0.025 and 0.05 against concave, linear and convex evidence responses on
disjoint CUDA seeds. All nine curves and uniform detected 0/30 reached boundary harms at the 10%
cap; the nearest-to-uniform curve had no established RMSE or spend advantage. No curve is promoted.
Its [frozen protocol](docs/evidence_urgency_curve_grid_protocol.md) and hash-verified metrics are
under `outputs/evidence_urgency_curve_grid_30/`. A frozen fresh-seed comparison then raised the
cap to 20% and compared the near-uniform curve with uniform and cost-aware baselines, following
the prior design that showed nonzero detection power.
That fresh 20% comparison is now complete: uniform detected 6/60 boundary harms, the evidence
curve 4/60, variance 3/60, cost-aware Neyman 2/60, and cost-stabilized Neyman 5/60. All onsets were
reached; no method had a false escalation in 60 streams per null control. The evidence curve's
paired detection difference from uniform was -3.3 points (95% seed-bootstrap interval [-11.7,
5.0]), with no demonstrated accuracy benefit. It is not advanced. See the [protocol](docs/evidence_budget20_comparison_protocol.md),
[results](docs/evidence_budget20_comparison_results.md), and [run artifacts](outputs/evidence_budget20_comparison_60/).
The next step is to diagnose why the e-process accumulates weak signal before developing more
query-allocation variants.
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

The project now implements a mathematically valid baseline for this target: a fixed mixture of bounded
factors built from paired prediction-powered cost estimates, with query propensities and support bounds
chosen predictably from prior monitor history. Under the registered zero-margin eventwise
conditional-mean null (or after centering by a prespecified margin and enlarging the support bound),
a frozen current/reference action pair, positive randomized query propensities, complete outcomes
whenever queried, and the stated filtration, the bounded-factor supermartingale argument gives
anytime false-escalation control. This is standard e-process reasoning, not a novelty claim. Two independent 4,000-
stream CUDA studies passed their prespecified synthetic calibration and power gates: one under
independent events and one under a two-state Markov volatility process whose conditional mean is zero
in each state. In the Markov validation, the predictable-bound system improved four-dose mean detection
by 5.66 percentage points (95% paired-bootstrap CI +5.19 to +6.14) and used 134.45 fewer labels per
stream, while all simultaneous one-sided calibration upper limits were at most 2.43%. Full protocols,
results and manifests are in [the independent confirmation](docs/history_predictable_bound_confirmation_results.md)
and [the Markov validation](docs/markov_predictable_bound_validation_results.md). These findings apply
to the registered synthetic feedback models. A separate iid delayed-feedback calibration and
confirmation now supports this standard construction with a deterministic, outcome-independent
12-event label delay and event-order prefix updates. Its fresh null calibration passed the four-cell
family-wise gate; the disjoint four-dose confirmation improved macro detection by 3.14 percentage
points (95% paired-bootstrap CI +2.64 to +3.63) while using 131.25 fewer labels per stream. This
result does not extend to arbitrary serial dependence, informative or missing labels, adaptive policy
changes, repeated-candidate selection, or interventions that alter outcomes. See the
[delayed-feedback protocol](docs/delayed_history_predictable_bound_protocol.md),
[confirmation results](docs/delayed_history_predictable_confirmation_results.md), and
[confirmation artifacts](outputs/delayed_history_predictable_confirmation_2000/).

The learner receives only features available at prediction time and labels after their recorded
availability time. Synthetic regime labels and generating parameters stay evaluator-side. Missing
or unknown real-world timing is not inferred. Real-source results must therefore use the task's
documented retrospective or offline protocol when a valid online replay clock is unavailable.

The paper protocols distinguish diagnostic evidence from confirmatory results. Small seed counts
are smoke or validation runs; selected final comparisons should use paired seeds and the larger
replication counts specified by the protocol. Imposed synthetic costs are research controls, not
application-grounded utilities. The registered independent, Markov, and fixed-delay synthetic
studies establish alarm control only under their stated nulls, feedback rules, and predictable query
designs. They do not establish control under arbitrary feedback, serially dependent or informative
delayed labels, changing policies, conditional conformal coverage under arbitrary shift, causal drift
attribution, or universal benefits from adaptation.

For version-control conventions and contribution checks, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Feature-dependent intervention benchmark

The feature-dependent promotion/rollback integration connects the existing controller to the
versioned decision-stream contract and keeps evaluator-only cost truth out of replay. A fresh CUDA
grid covers stationary, nuisance-shift, boundary-harm, reversal, persistent-benefit, and
least-favourable rollback-null profiles. Independent 2,000-stream calibration passed all four
registered simultaneous error limits. On the disjoint harmful-reversal block, rollback improved
expected utility by 71.19 units over promotion-only, but remained 69.38 units worse than continuing
with the incumbent. The experiment supports a calibrated rollback mechanism under its stated
simulator assumptions; the end-to-end intervention policy fails the net-utility criterion. See
the [frozen protocol](docs/feature_intervention_protocol.md),
[confirmation protocol](docs/feature_intervention_confirmation_protocol.md),
[results and limitations](docs/feature_intervention_results.md), and synthetic artifacts under
`outputs/feature_intervention_*`.

A fresh 36-cell CUDA run compares the fixed-stake mixture at α and α/2, plug-in Kelly, published PM-EB, full-budget one-sided positive betting, and the canonical half-weighted hedged branch (2,000 streams per cell; seed 24102026). Every method stayed below 5% crossings in the mixed-sign zero-mean and strict negative-mean controls. On positive alternatives, full-budget positive betting averaged 12.14% crossings for broad gains and 7.22% when only the high-cost group benefited, versus 11.31% and 5.95% for the fixed mixture; its paired high-cost-only gain was +1.27 points (95% cellwise t interval +0.95 to +1.59), while the broad-gain interval included zero. The canonical half-weighted hedge performed essentially the same as a fixed mixture at the matched α/2 threshold. PM-EB remained more conservative and less powerful in this sparse-label setting. The full two-sided hedge is unsuitable as a decision-harm gate because its lower-tail branch can alarm inside the one-sided no-harm null. These are descriptive finite simulations, not a winner or novelty claim; this run is exploratory rather than preregistered. Code, paired Parquet results, checksums, [report](outputs/hedged_betting_comparison_final_24102026/reports/predictable_stake_calibration.md), and [plot](outputs/hedged_betting_comparison_final_24102026/figures/predictable_stake_calibration.png) are available. The earlier grids remain at `outputs/hedged_betting_comparison_v2_23102026/` and `outputs/predictable_betting_comparison/`.

The [regime-warning reliability grid](docs/regime_warning_grid_results.md) varies cue strength, MCAR missingness, false-warning threshold, and sensor cost across 500-seed CUDA streams. It contains 264,000 stream-policy rows and includes an evaluator-only matched-coverage reference. Because warning values are independent of event-level gains in this DGP, the cue adds no expected decision value beyond lowering coverage; positive sensing cost makes it strictly worse than the matched-exposure reference. Even at the strongest cue, the rule did not beat continuing with the incumbent under reversal. See the [protocol](docs/regime_warning_grid_protocol.md) and artifacts under `outputs/regime_warning_grid_500/`; this is an exploratory comparator result, not a novelty claim.

## Context-local promotion and rollback

ShiftLab now includes a contextual intervention benchmark that compares one global promotion/rollback gate with the same established bounded e-process composed across two visible context strata. The two-stage, two-stratum alpha allocation is Bonferroni composition; it is not claimed as a novel test. In a fresh 2,000-stream heterogeneous-reversal confirmation, stratified intervention exceeded the global gate by 30.53 utility units (paired 95% CI [29.54, 31.52]) and continuing by 13.00 ([11.51, 14.51]); all eight simultaneous null-calibration limits passed, every label cap held, and the safe context was retained in 1,999/2,000 streams. This result applies only to the registered balanced, visible-context simulator and is not a general superiority or novelty claim. The [protocol](docs/contextual_stratified_intervention_protocol.md), [results and limits](docs/contextual_stratified_intervention_results.md), and full outputs under `outputs/contextual_stratified_*` contain reproduction details, metrics, manifests, and hashes. Any research visual for this work must be made with PaperBanana and checked against the saved metrics; no visual was needed for the tabular results.

The [contextual alpha-allocation robustness grid](docs/contextual_weighted_alpha_grid_results.md) adds volume-weighted and rare-protected Bonferroni allocation alongside equal per-context alpha. Across 324 CUDA factorial cells (200 seeds each), volume weighting had a modest average utility edge over equal allocation during heterogeneous reversal (+1.53 paired units) but the cellwise result was mixed; rare-protected weighting reduced mean utility under the event-weighted objective. Continuing was best under homogeneous harm, while the global gate was best when both contexts benefited. The development grid itself selected no general winner; its matched-method result then went to a frozen independent comparison.

In that independent confirmation, volume-weighted alpha improved mean realized utility over equal alpha by 1.484 units per 800-event stream (paired 95% CI [1.375, 1.597]) across the prespecified equal-weight prevalence/noise, cost, and budget factorial, exceeding the +1.0 practical margin. All 54 simultaneous calibration cells passed (largest exact upper bound 1.967%), and all label caps held. The effect varied by profile and is not a universal or application-level claim. The [calibration/confirmation protocol](docs/contextual_weighted_alpha_confirmation_protocol.md), [results](docs/contextual_weighted_alpha_confirmation_results.md), [calibration artifacts](outputs/contextual_weighted_alpha_calibration_2000/), and [confirmation artifacts](outputs/contextual_weighted_alpha_confirmation_2000/) preserve the assumptions and metrics. Any visuals must use PaperBanana.

The follow-up [nested candidate-by-context alpha study](docs/nested_candidate_context_alpha_results.md) isolates 13-candidate familywise spending under hard query caps. Its independent CUDA calibration passed all 108 simultaneous null cells (largest one-sided exact upper limit 1.035%). In the frozen specialist-context confirmation, nested volume allocation exceeded pooled rank-only and nested equal allocation by 2.952 [2.675, 3.235] and 2.510 [2.303, 2.720] realized utility units per 400-event deployment, respectively. The averages hide substantial cell variation, and the experiment uses synthetic utility processes rather than fitted models; it establishes no novelty or end-to-end classifier benefit. The [protocol](docs/nested_candidate_context_alpha_protocol.md) and checksummed artifacts under `outputs/nested_candidate_context_*` define the next integration task. Any research visual must use PaperBanana.

## Target-scout decision gate

The target-scout selector uses the first half of the target monitor to choose a context-specific policy map, freezes that map, and certifies it on fresh events with a bounded fixed-mixture e-process under the shared label cap. On the registered IID synthetic confirmation (600 streams per cell), its future net utility exceeded pooled-rank by 5.284 units (simultaneous 97.5% interval [4.301, 6.292]) and nested-volume by 4.182 ([3.282, 5.087]); no harmful promotion was observed. Its independent IID and stationary-Markov null calibrations both passed their simultaneous false-promotion gates.

An additional abrupt context-prevalence null calibration used 1,000 fresh streams in each of 24 cells: 10%→90%, stable 50%→50%, and 90%→10%, crossed with proxy noise, switching cost, and label cap. All cells passed the simultaneous 5% gate; there were 8 promotions total, no cap breaches, and the largest one-sided exact upper limit was 1.030%. At every event the conditional outcome probability remained at the decision threshold, so this study tests context-distribution drift under the null rather than power to detect harm. It does not establish performance under gradual drift, delayed/selective feedback, or positive-signal drift. See the [frozen protocol](docs/scout_context_policy_drift_null_protocol.md), [calibration report](outputs/scout_context_policy_drift_null_1000/reports/scout_context_drift_null_calibration.md), and [per-stream metrics](outputs/scout_context_policy_drift_null_1000/metrics/).

These finite simulator results complement the e-process argument only under their stated conditional-mean null, candidate-selection split, query support, and feedback assumptions. The selector and its application remain a tested research candidate, not a verified novel method or a general-purpose safe-adaptation guarantee. No figure was generated for the tabular calibration; use PaperBanana for future research visuals.

The first positive-signal drift development grid did not show a meaningful advantage: across 24 matched settings and 60 seeds per setting, the minimum-propensity scout promoted 2/1,440 streams, while rank and nested-volume promoted none. Its equal-cell expected-utility difference was +0.096 over each baseline with a descriptive 95% seed-cluster interval [0.000, 0.242]. Both scout promotions occurred in the 10%→90% shift, delta=0.05, 25% proxy-error, 40% budget cell. This sparse development result did not warrant independent confirmation. It identified a bound-efficiency opportunity: under the registered uniform-query design, q is known and predictable, so |I_t G_t/q|≤C/q gives eventwise support C/q+k instead of the previous C/q_min+k.

The eventwise-bound development grid compared that scout with the minimum-bound scout, pooled rank, and nested-volume across 24 matched settings and 60 seeds each. The eventwise scout promoted 7/1,440 streams (all had positive evaluator-known future net utility); the minimum-bound scout promoted 2/1,440, and rank and nested-volume promoted none. Eventwise scout's equal-cell utility contrast over the other two methods was +0.409 units (descriptive 95% interval [0.065, 0.863]); versus the minimum-bound scout it was +0.227 ([0.041, 0.472]). These are sparse development outcomes and do not establish a reliable power gain. The eventwise candidate now requires its independent 24-cell null calibration before any positive-signal confirmation. The [eventwise development report](outputs/scout_context_policy_eventwise_bound_development_60/reports/scout_context_drift_development.md), [stream metrics](outputs/scout_context_policy_eventwise_bound_development_60/metrics/), and [frozen protocol](docs/scout_context_policy_eventwise_bound_development_protocol.md) preserve the results. No figure was generated.

**Independent eventwise-bound null calibration passed:** 1,000 fresh streams in each of 24 cells (24,000 stream records) across the three abrupt prevalence profiles, proxy errors, switching charges, and label caps. There were 100 false promotions overall (0.42% of streams); the largest cell rate was 1.0%, and the largest simultaneous one-sided exact Clopper–Pearson upper limit was 2.28%, below the 5% familywise gate. All evaluator null checks, positive-propensity checks, and hard-cap checks passed. This supports the registered eventwise-bound gate under this zero-signal DGP and uniform-query process; it does not establish positive-signal power, validity for adaptive propensities, or robustness to delayed/selective feedback. The [frozen protocol](docs/scout_context_policy_eventwise_drift_null_protocol.md), [calibration report](outputs/scout_context_policy_eventwise_drift_null_1000/reports/scout_context_drift_null_calibration.md), [manifest](outputs/scout_context_policy_eventwise_drift_null_1000/reports/manifest.json), and [per-stream metrics](outputs/scout_context_policy_eventwise_drift_null_1000/metrics/) contain the complete reproducible record. No figure was generated.

The follow-up positive-signal comparison is now frozen in the [eventwise-bound confirmation protocol](docs/scout_context_policy_eventwise_bound_confirmation_protocol.md), using a disjoint 600-seed-per-cell block and matched comparisons against pooled rank and nested-volume. Its result is pending; the development block remains exploratory.
