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

The shadow-promotion experiment evaluates a frozen logistic recalibration candidate and an
incumbent snapshot on fresh forward-time labels, applies candidate-index alpha spending, and
reports certification behavior in
[`outputs/promotion_experiment_corrected/figures/adaptation_promotion.png`](outputs/promotion_experiment_corrected/figures/adaptation_promotion.png),
[`outputs/promotion_experiment_corrected/metrics/promotion_comparison.parquet`](outputs/promotion_experiment_corrected/metrics/promotion_comparison.parquet),
and [`outputs/promotion_experiment_corrected/reports/promotion_comparison.md`](outputs/promotion_experiment_corrected/reports/promotion_comparison.md).
The earlier `outputs/metrics/promotion_comparison.parquet` predates the absorbing certificate fix
and is superseded. The one-step cost-aware controller is available in `shiftlab.dive.controller`;
its forecasts are supplied inputs, and it is not yet integrated into a closed-loop intervention
benchmark.

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
