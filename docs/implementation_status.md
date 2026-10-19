# Milestone audit

1. Runnable infrastructure: implemented strict YAML, editable package, uv lock, CLI, CI,
   atomic JSON manifests, failure status, unique runs, versions and config hashes. MLflow
   integration and broad static typing are deferred; mypy checks the configuration package.
2. Reliable benchmark: four DGP controls, online marginal KS and CUSUM, delayed/missing feedback,
   reproducibility and replicated detector tests. Other shifts and dependence are deferred.
3. Models: shared Ridge, full retraining, numeric checkpoints and timing. Classification,
   neural, temporal models, partial updates and GPU training are deferred.
4. Three tracks: decision-loss monitoring; fixed/rolling conformal; frozen/periodic/triggered
   retraining. Baseline extensions listed in README are explicitly unavailable.
5. Reports: actual 3-seed runs, traces, plots, CSV aggregation and stream bootstrap intervals.
   Matched false-alarm budgets, paired inferential contrasts, compute Pareto and dependence-aware
   resampling are deferred. This is an initial reproducibility check, not a paper-ready study.
6. Novel methods: intentionally not started.

Open questions: How should detector budgets be matched using separate calibration streams?
When does decision loss reveal harm more quickly than squared error? What recovery definition
is robust to noisy rolling coverage? Which budgeted adaptation oracle is scientifically fair?
No theorem or novelty has been established.
