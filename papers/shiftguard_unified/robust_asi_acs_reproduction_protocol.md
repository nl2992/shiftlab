# Robust ASI on the paper's ACS regression task

**Status:** frozen reproduction protocol v1; this is a task-specific method reproduction, not a ShiftGuard sequential-monitor result.  
**Primary source:** Li, Zrnic, and Candès, [Robust Sampling for Active Statistical Inference, NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/file/6389470564214983604d1ac81631c2c5-Paper-Conference.pdf). The [authors' repository](https://github.com/lphLeo/Robust-Active-Statistical-Inference) contains the `census_data_analysis.ipynb` reference experiment. The paper/code were inspected; the implementation here is independent, and no author code is copied into this repository.

## Question and estimand

Reproduce the paper's California 2019 ACS PUMS task: estimate the age coefficient in the no-intercept least-squares regression of personal income `PINCP` on age `AGEP` and sex `SEX`, and compare uniform sampling, uncertainty-based active sampling, and robust active sampling. This is a fixed-horizon, model-assisted estimator benchmark. It says nothing about sequential alarm validity or intervention utility.

## Data and learner information

Use the locally acquired 2019 California person PUMS archive `data/raw/folktables/2019/1-Year/csv_pca.zip`, member `psam_p06.csv`, with its immutable download receipt. The exact source URL and archive digest are recorded in the run manifest. Select 20,000 records by one seeded uniform permutation, matching the authors' 20,000-record sample size. The base-model predictors are the paper's 17 fields: `AGEP`, `SCHL`, `MAR`, `DIS`, `ESP`, `CIT`, `MIG`, `MIL`, `ANC1P`, `NATIVITY`, `DEAR`, `DEYE`, `DREM`, `SEX`, `RAC1P`, `SOCP`, and `COW`; the paper treats `AGEP` and `SCHL` as numeric and the remaining fields as categorical. Missing predictors are represented by `-1` before categorical encoding. The target regression design contains only `AGEP` and `SEX`.

The evaluator uses all 20,000 selected incomes only to calculate the target coefficient and score completed sampling trials. The learner receives labels for a seeded 30% base-model training split, all 3% burn-in labels from the remaining 70%, and only the Bernoulli-queried labels from the final inference pool. No inference-pool label enters the fitted base model, residual-scale model, propensity selection, or robustness-radius cross-validation before it is queried. Survey weights are not used, matching the authors' notebook's unweighted OLS estimator; this is a sample-average benchmark rather than a population-representative ACS estimate.

## Frozen method settings

- Fit the base income predictor on the 30% labeled split using XGBoost absolute-error loss, learning rate 0.3, depth 7, and 2,000 boosting rounds, as in the authors' notebook. Use GPU histogram training when supported and record the actual device and package version.
- Draw 3% of the remaining records as a fully labeled burn-in sample. Fit the residual-scale predictor on burn-in covariates and absolute base-model residuals, using 200 XGBoost trees, learning rate 0.1, and depth 20.
- Estimate the OLS influence scale on the final inference pool as `abs(h.T @ x) * predicted_absolute_residual`, where `h` is the first column of the inverse design second-moment matrix. Preserve its relative scale: the authors' notebook uses this score without clipping it to `[0, 1]`, and clipping can collapse heterogeneous scores into a constant allocation. Propensity normalization, rather than score clipping, sets the expected query budget.
- Use the geometric path from residual-scale active allocation to uniform allocation. At every path point, normalize propensities to the exact expected-label budget, bound probabilities to `(0, 1]`, and use a fixed `1e-8` support floor. The floor and exact-budget normalization make the implementation numerically well-defined when the fitted residual scale is zero; they are recorded deviations from the authors' released notebook.
- Select the L2 robustness radius separately for each query budget by five-fold cross-validation on burn-in only. Use the paper-code candidate grid `[0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000, 5000, 10000]`; for each candidate, choose the geometric-path point minimizing the paper's L2 worst-case variance objective, then score its sandwich standard error using 200 Bernoulli trials per fold. In the objective, convert grid value `c` to Euclidean radius `c * sqrt(n_fold)`, which matches the paper code's `constraint_sum = c * sqrt(n)` convention.
- Evaluate budgets from 5% through 20% of the final inference pool at ten evenly spaced points. At each budget, use 500 Bernoulli sampling trials for uniform, active, and cross-validated robust active sampling, with shared query uniforms across methods. The fixed seed, random split, and per-stage seeds are recorded.
- Report estimation bias, RMSE, mean 90% sandwich interval width, empirical coverage, expected/realized labels, selected radius, and selected `rho`. The target 90% interval level follows the paper. These repeated sampling trials quantify Monte Carlo performance conditional on one sampled dataset; they are not independent datasets and do not validate finite-sample or sequential guarantees.

## Reproduction command

```powershell
uv run --with xgboost==3.4.1 python scripts/reproduce_robust_asi_acs.py `
  --data data/raw/folktables/2019/1-Year/csv_pca.zip `
  --output outputs/shiftguard_unified/sota_reproductions/robust_asi_acs_v2 `
  --device cuda
```

The run must fail on an unavailable requested CUDA device or invalid source receipt. It writes Parquet trial metrics, an aggregate CSV, a source/data manifest, the frozen protocol, and execution-source snapshots. No figure is required for this numerical reproduction.

## Limits and interpretation

This reproduces one paper task using the locally verified public ACS source and the method described in the paper. Model training uses the paper's XGBoost settings; exact random seeds are made reproducible here. The project implementation uses an exact expected-budget normalization and positive propensity floor to avoid clipping-induced budget mismatch and unsupported residual corrections. The authors' released notebook does not freeze its random split, and its final propensity clipping can alter expected spend; those implementation differences are explicit. The influence score itself is left unclipped to preserve the allocation information in the authors' task. This benchmark does not reproduce the paper's Pew or text-annotation tasks, does not validate the authors' reported values, and does not transfer the batch inference guarantee to DIVE, sequential monitoring, delayed feedback, or decision intervention.
