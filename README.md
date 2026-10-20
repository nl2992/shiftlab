# ShiftLab

A CPU-runnable research platform for decision-relevant drift, adaptive conformal prediction,
and cost-aware adaptation. This is the first implementation deliverable, not a novelty claim.
Existing starter entry points remain available under `experiments/`; they are legacy illustrative
experiments and are excluded from the new benchmark reports.

## Data acquisition and generation

The versioned data framework, exact CLI commands, CUDA setup, acquired datasets and limitations
are documented in [docs/data_phase1.md](docs/data_phase1.md). See [data/reports/experiment_readiness.md](data/reports/experiment_readiness.md)
for per-version readiness, [data/reports/dataset_paper_suitability.md](data/reports/dataset_paper_suitability.md)
for the source-level paper matrix, and [data/reports/data_quality_report.md](data/reports/data_quality_report.md)
for actual checks. The full requirement status is maintained in [docs/phase1_completion_audit.md](docs/phase1_completion_audit.md);
it remains in progress while source-specific and statistical gaps are addressed.
The executed stationary-control evidence is in [data/reports/stationary_control_validation.json](data/reports/stationary_control_validation.json).

## Install and run

Python 3.11+ and uv are required. From this repository:

```bash
uv sync --extra dev --extra data-sources
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run python scripts/validate_environment.py
uv run python scripts/run_diagnostics.py --config configs/experiments/diagnostics.yaml
uv run python scripts/run_baselines.py --paper 1
uv run python scripts/run_baselines.py --paper 2
uv run python scripts/run_baselines.py --paper 3
uv run python scripts/run_first_deliverable.py
uv run python scripts/aggregate_results.py
```

`uv sync --all-extras` also installs optional PyTorch, WILDS and MLflow dependencies. Neural model training
and tracking integration remain deferred. The data framework supports CUDA generation; the original
Ridge benchmark still rejects non-CPU devices. The default installation requires neither optional dependency.
No dataset is downloaded at installation or in CI. `shiftlab --config ... --paper 2` is the CLI.

## Implemented benchmark

`src/shiftlab/core/config.py` strictly validates YAML, including chronological boundaries.
`synthetic.py` produces four shared-seed regression controls. `streaming.py` sends immutable
observations and arrived feedback to a learner, while the evaluator retains targets, regimes
and generating parameters. Zero-delay feedback arrives after that time's prediction; delay d
arrives after prediction at t+d. Labels still pending at the horizon never update the learner.
Calibration labels are historical, available at initialization. Missingness is independent MCAR.
Initial train and calibration blocks are disjoint and end before the configured intervention time.

Ridge is shared across tracks. KS uses Bonferroni correction across features at each window check.
Standardized one-sided CUSUM monitors squared prediction error and asymmetric decision loss.
Paper 1 compares these alarms on a frozen predictor. Paper 2 compares fixed split-conformal
intervals and rolling residual quantiles. Paper 3 compares frozen, periodic, and error-CUSUM
triggered retraining with a shared maximum number of full fits and per-fit resource cost.
No partial updates or calibration-only adaptation are silently substituted.

Every run writes a unique `outputs/<UTC>-<uuid>/` folder containing an atomic status manifest,
validated config and SHA256 hash, dependency versions, Git revision (null before a first commit),
actual DGP arrays, event logs, numeric Ridge checkpoints, prediction traces, metrics, and PNG/PDF
figures. Numerical results are deterministic; wall-clock times and identifiers are not.
Checkpoints use `np.load(path)`; prediction is `X @ saved['coef'] + saved['intercept']`.
Failed runs retain a failed manifest. Large local artifacts are ignored by Git.

## Scientific limits

KS assumes independent observations; this DGP is iid within each regime. Repeated KS tests and
resetting CUSUM do not provide anytime-valid control. Thresholds are fixed, not matched to a
common false-alarm budget. False-alarm counts and first post-change delay are reported separately;
a missing delay is a censored nondetection, not zero. No-shift streams have no true change.
Benign means the population target mechanism ignores the shifted feature; finite-sample Ridge
can still assign it a nonzero coefficient. These are deliberately diagnostic controls.

The policy acts at predicted response zero with false-negative cost 5 and false-positive cost 1.
Reported regret is conditional expected decision regret against the known Gaussian Bayes policy
(probability threshold 1/6), not adaptation-controller regret. This fixed action threshold is not
Bayes optimal even before shift; compare changes as well as absolute regret. Paper 3's objective
is test squared-error sum plus configured cost per retrain; measured times are separate. Equal
intervention caps do not imply matched wall-clock compute. No dynamic adaptation oracle exists yet.

Split conformal uses ceil((m+1)(1-alpha)) with an infinity atom for insufficient calibration size.
Rolling coverage is empirical, not a guarantee under nonstationarity. Regime coverage is an
evaluator diagnostic. Recovery times, ACI, weighted conformal, MMD, classifier tests, River,
ruptures, dependent bootstrap, temporal/classification models and real-data acquisition remain
unimplemented. The legacy function name `weighted_conformal_quantile` means ordinary unweighted
split conformal, retained for compatibility. No weighted validity is claimed.

Three seeds provide smoke evidence only. Aggregate bootstrap intervals resample independent
stream seeds, not time points; they are unstable with so few seeds. Do not tune on these held-out
streams and then present them as confirmatory evidence. See `docs/implementation_status.md` and
paper protocols for deferred research work.

## Version control

Use `main` for shared integration and short-lived `paper1/`, `paper2/`, `paper3/` or `shared/` branches.
See [CONTRIBUTING.md](CONTRIBUTING.md) for hooks, review, reproducibility tags and remote setup.
