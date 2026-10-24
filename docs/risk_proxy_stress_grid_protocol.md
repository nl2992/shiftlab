# Decision-risk proxy stress grid protocol

## Question and status

This development screen asks whether the training-only logistic decision-risk proxy remains
competitive with ridge regression, a validation-selected proxy, and prequential proxy-Hedge as the
amount of historical data, query rate, loss asymmetry, and shift severity vary. It follows the
previous development benchmark, where the logistic risk proxy was stronger than Hedge on average.
The grid does not introduce a new algorithm or test false-alarm calibration.

## Frozen grid

Run 12 shared seeds per cell, with 2,400 events per stream and CUDA generation when available.
Compare boundary-local harm, residual-variance shift, recurring regimes, and harmful adaptation.
For the first three scenarios, use severity values 0.75, 1.5, and 2.25. Harmful adaptation has a
single severity setting because its generator is severity-invariant. Cross each scenario setting
with two false-negative/false-positive cost regimes `(5,1)` and `(1,1)`, training fractions
`0.05`, `0.125`, and `0.25`, and Bernoulli query rates `0.10`, `0.20`, and `0.40`. This yields 180
cells and 2,160 generated streams. Each cell uses matched query uniforms and identical label/spend
paths across all six proxy methods.

With equal false-negative and false-positive costs, the deployed 0.5-threshold action and the
source cost-minimizing action coincide in the three classifier/boundary scenarios. Such cells have
no material harm and are excluded from conditional detection rates; they remain structural controls,
not nondegenerate null-calibration streams.

The validation slice is 12.5% of events. Training and validation are completed before monitoring.
The selected validation-best proxy is chosen using validation RMSE and frozen for the monitor. The
logistic model is trained only on the historical training slice; no evaluator probabilities or
change parameters enter its features or fitting data. Cost contrasts are computed from observed
policy actions, known cost matrix, and outcome labels.

## Comparisons and interpretation

For every cell, report detection, pre-onset false escalation, estimator RMSE, labels and spend,
processed events, and which proxy validation selected. Paired risk-model differences are reported
against ridge, validation-best, and Hedge with seed-cluster bootstrap intervals. Intervals are
descriptive and unadjusted across the grid. The within-cell seed count is a screening budget, not a
calibration sample size. The alternative-only grid cannot establish a false-escalation guarantee.

Retain the logistic proxy as a useful baseline if its detection and estimation performance remain
competitive across cost, severity, training, and query conditions. If performance is sharply
condition-dependent, model that dependence and design an independent study. Do not claim novelty
for a standard logistic conditional-risk model, and do not advance a new adaptive method from this
screen alone.

## Reproduction

```powershell
uv run shiftlab-dive-risk-proxy-stress --device cuda --seeds 12 --seed-offset 20402024 --n 2400 --output-dir outputs/risk_proxy_stress_grid
uv run shiftlab-dive-risk-proxy-stress-analyze --output-dir outputs/risk_proxy_stress_grid
```

The run writes a Parquet and CSV stream table, cell summaries, paired contrasts, source hashes, a
runtime manifest, and a text report. No plot is specified. If a research visual is added later, use
PaperBanana and verify its plotted values against these saved metrics.
