# Primary-paper audit: When to Retrain a Machine Learning Model

**Source:** Florence Regol, Leo Schwinn, Kyle Sprague, Mark Coates, and Thomas Markovich, “When to Retrain a Machine Learning Model,” ICML 2025, PMLR 267, pp. 51369–51404. [PMLR paper page](https://proceedings.mlr.press/v267/regol25a.html).  
**Audit date:** 2026-10-26.  
**Status:** primary-paper algorithm audit, independent implementation of the finite-horizon decision recursion, independently checked counterexample, and one exploratory retrospective EIA cost-frontier comparison; no author-code reproduction or independent confirmation.

## What UPF is and what it is not

UPF addresses a finite-horizon retraining-schedule problem. Its objective adds a bounded predictive-loss term for each future period to a fixed relative retraining cost. It forecasts the performance of currently available and not-yet-trained models using a low-data regression model over training time, evaluation time, time since training, and a feature-shift summary. The paper models future performance as independent Beta variables after converting a Gaussian mean/variance forecast to Beta parameters, then uses Monte Carlo quantiles of total cost to decide between retraining and keeping the incumbent. The reported configuration uses a 0.95 quantile and ElasticNetCV for the performance mean model.

This is a cost-sensitive intervention baseline, not an anytime-valid monitor, a paired decision-harm certificate, or a future-benefit guarantee. Its quantile decisions inherit the calibration and extrapolation quality of the performance forecaster; the primary paper does not provide an anytime false-escalation or false-promotion guarantee.

The official PMLR page links the paper PDF and OpenReview entry but does not expose an implementation link. Any local implementation must therefore be labelled an independent implementation and checked against the algorithm description; it cannot be called a code reproduction. The paper's principal real-data setting uses a sequence of timestamped classification datasets, with seven offline periods and eight online periods, and evaluates cost over a range of retraining-cost ratios.

## Independent check of Proposition 3.1

The final PMLR paper states the retraining-count bound

\[
r^* \le T - \sqrt{\alpha/L},
\]

under the condition that adjacent model indices differ in expected performance by at most \(L\). The following one-step instance satisfies the stated bounded-loss and adjacent-difference assumptions:

| Quantity | Value |
|---|---:|
| Horizon \(T\) | 1 |
| Initial model loss on period 1, \(pe_{0,1}\) | 1 |
| Model trained at period 1 loss on period 1, \(pe_{1,1}\) | 0 |
| Adjacent-difference bound \(L\) | 1 |
| Relative retraining cost \(\alpha\) | 0.25 |
| Cost without retraining | 1 |
| Cost with retraining | 0.25 |
| Optimal retraining count \(r^*\) | 1 |
| Claimed upper bound \(T-\sqrt{\alpha/L}\) | 0.5 |

The optimal schedule therefore violates the stated bound (`1 > 0.5`). The calculation is executable in [`scripts/audit_upf_retrain_count_bound.py`](../../scripts/audit_upf_retrain_count_bound.py) and covered by [`tests/test_upf_retrain_bound_audit.py`](../../tests/test_upf_retrain_bound_audit.py).

This counterexample applies to Proposition 3.1 as stated. It does **not** refute the separate UPF quantile decision rule or the paper's reported empirical comparisons. ShiftLab must not use Proposition 3.1 to prune retraining schedules or claim an upper bound on optimal retraining frequency. The algorithm remains a high-priority Q3 comparator; its decision rule can be evaluated independently of that proposition.

## Independent implementation status

`src/shiftlab/dive/upf_retraining.py` now implements the paper-described forecaster and cost recursion: ElasticNetCV mean fit, constant residual variance, moment conversion to Beta parameters, independent Beta performance draws, and backward Monte Carlo quantile comparison for each remaining-horizon state. `PerformanceObservation` records the loss maturity period, and `fit_available_performance_forecaster` filters observations to an explicit availability cutoff. The caller must refit after newly observed outcomes and provide only shift summaries available at decision time. The regression fit is CPU-side, matching the paper's small ElasticNetCV model; Torch performs Monte Carlo sampling and quantiles on CUDA when available. Unit tests cover availability filtering, feature construction, bounded parameter conversion, and retrain/keep decisions under low and high explicit costs. A CUDA smoke check passed on the NVIDIA GeForce RTX 4060 Laptop GPU.

This is an independent implementation from the published algorithm description, not an official-code reproduction: the PMLR entry exposes no code link, and no comparison to author outputs has been run. It is implementation progress only. The data adapter, finite-horizon cost-frontier experiment, published baselines, and real-data comparison remain open.

## ShiftLab benchmark status

The current EIA runner in `scripts/evaluate_eia_retraining_frontier.py` compares frozen, weekly, monthly, and recent-error-triggered Ridge policies on retrospective next-period regression. The error trigger is explicitly heuristic. It is not UPF: it does not forecast future performance distributions, recursively compare total-cost quantiles, or evaluate the published binary-classification objective. Existing Gas Sensor work uses ten coarse ordered batches, fewer than the paper's seven-offline/eight-online schedule; splitting inside a batch would invent timing not recorded by the source. Neither current run closes the published-baseline requirement.

The first bounded-loss EIA adaptation is complete. Protocol, exact execution snapshot, runner, manifest, Parquet period metrics and aggregate report are in `upf_eia_development_protocol.md` and `outputs/shiftguard_unified/real_data_development/upf_eia_frontier_v1/`. It compares UPF with never, always, periodic-2, periodic-4, a frozen error threshold and a full-information oracle on CISO and ERCO, under zero- and 168-hour assumed extra label delays. It used CUDA on an NVIDIA RTX 4060; the manifest verifies the protocol snapshot and records all data, source and output hashes. Results are mixed across domains and costs; UPF does not dominate the simple baselines. The full-information oracle is only a lower bound. This single exposed retrospective EIA series is an implementation/development check, not a paper-faithful classification reproduction, external confirmation, or evidence of operational utility. The comparison omits CARA and published drift-detector baselines, so the Q3 fidelity gate remains open.
