# DIVE initial evidence-acquisition comparison

Generated from 30 paired evaluation seeds for each of 3 scenarios. Resolved device: `cuda`.

## Implemented variants

- `full_feedback`: all monitor-period labels; direct paired-cost e-process.
- `uniform_direct`: uniform Bernoulli queries and direct inverse-propensity paired-cost estimates.
- `uniform_proxy`: uniform queries with prediction-powered correction.
- `pprm_reliance_analogue`: uniform queries with a predictable historical plug-in scalar for proxy reliance. This is not the full PPRM algorithm or its confidence-sequence construction.
- `uncertainty_proxy`: entropy-based query propensities calibrated on the pre-monitor validation slice.
- `variance_proxy`: query scores proportional to the square root of a held-out model for proxy residual second moments.
- `decision_value_proxy`: a heuristic that increases sampling near the harm margin when proxy residual uncertainty is high.
- `evidence_growth_proxy`: selects the predictable query propensity by maximizing a pre-monitor outcome model's stake-weighted expected log-wealth increment under the same expected label budget. The per-event objective is concave and solved through a dual budget multiplier. This is a model-based allocation rule, not an e-process validity result or a power-optimality claim.
- `evidence_growth_stabilized_proxy`: mixes evidence-growth propensities with uniform sampling at weight `0.025`. The expected query-rate drift under arbitrary feature shift is bounded by the configured tolerance `0.01`; this robustification may also remove most allocation adaptivity.

All fitted proxies and query multipliers use only the pre-monitor training/validation rows. Proxy refits for updating policies use queried outcomes only after they arrive; the expected-evidence policy freezes its decision-loss proxy over the monitor interval so the validation-calibrated objective does not change. Query outcomes are immediate in this first experiment. This monitor benchmark takes no action after alarms; candidate promotion is evaluated in a separate forward-time experiment.

## Preliminary results

These are descriptive paired-stream Monte Carlo results, not confirmatory inference. `rmse_stream_mean` is computed across independent seeds. False-escalation proportions have only 30 stream replicates per cell. The change-aware mixture is reported in the Parquet artifact; this report's table summarizes the single-start process.

Independent seeds are the inferential units. False-escalation intervals use Wilson's method over all population-null control streams and pre-onset alternative streams; detection intervals use only streams with evaluator-known harm onsets. Finite-stream oracle excursions within population-null controls are recorded separately. Labels and expected harm use t intervals across seeds; stream-mean RMSE uses a deterministic percentile bootstrap over seeds. Nondetections remain in the detection denominator and are not discarded from the Parquet data.

| Scenario | Method | False escalation (95% Wilson) | Detection on harmful streams (95% Wilson) | Delay among detected | Labels/stream (95% t CI) | Realized label spend/stream (95% t CI) | Stream-mean RMSE (95% bootstrap) | Proxy RMSE | Predictive Brier | Expected harm (95% t CI) | Oracle regret | Net cost vs ref (95% t CI) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| benign_nuisance | decision_value_proxy | 0.00 [0.00,0.11] | — | — | 349.6 [322.6,376.6] | 349.6 [322.6,376.6] | 0.0503 [0.0350,0.0641] | 0.8922 | 0.0726 | 0.0778 [0.0758,0.0799] | 0.0778 | 190.30 [185.41,195.18] |
| benign_nuisance | evidence_growth_stabilized_proxy | 0.00 [0.00,0.11] | — | — | 243.8 [238.3,249.4] | 243.8 [238.3,249.4] | 0.0543 [0.0431,0.0644] | 0.9401 | 0.0726 | 0.0778 [0.0758,0.0799] | 0.0778 | 189.24 [184.34,194.14] |
| benign_nuisance | uniform_proxy | 0.00 [0.00,0.11] | — | — | 241.6 [236.2,247.0] | 241.6 [236.2,247.0] | 0.0504 [0.0377,0.0627] | 0.8791 | 0.0726 | 0.0778 [0.0758,0.0799] | 0.0778 | 189.22 [184.32,194.11] |
| boundary_local_harm | decision_value_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 245.2 [239.0,251.4] | 245.2 [239.0,251.4] | 0.0894 [0.0612,0.1189] | 1.2180 | 0.0628 | 0.2691 [0.2627,0.2754] | 0.3026 | 648.19 [632.88,663.51] |
| boundary_local_harm | evidence_growth_stabilized_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 242.1 [236.7,247.5] | 242.1 [236.7,247.5] | 0.0696 [0.0542,0.0827] | 1.2217 | 0.0628 | 0.2691 [0.2627,0.2754] | 0.3026 | 648.16 [632.85,663.48] |
| boundary_local_harm | uniform_proxy | 0.00 [0.00,0.11] | 0.10 [0.03,0.26] | 1513 | 241.6 [236.2,247.0] | 241.6 [236.2,247.0] | 0.0727 [0.0568,0.0864] | 1.2161 | 0.0628 | 0.2691 [0.2627,0.2754] | 0.3026 | 648.16 [632.84,663.47] |
| stationary | decision_value_proxy | 0.00 [0.00,0.11] | — | — | 250.7 [244.6,256.8] | 250.7 [244.6,256.8] | 0.0666 [0.0423,0.0887] | 0.8699 | 0.0560 | 0.0778 [0.0758,0.0799] | 0.0778 | 189.31 [184.41,194.21] |
| stationary | evidence_growth_stabilized_proxy | 0.00 [0.00,0.11] | — | — | 242.1 [236.7,247.5] | 242.1 [236.7,247.5] | 0.0491 [0.0392,0.0586] | 0.8722 | 0.0560 | 0.0778 [0.0758,0.0799] | 0.0778 | 189.22 [184.32,194.12] |
| stationary | uniform_proxy | 0.00 [0.00,0.11] | — | — | 241.6 [236.2,247.0] | 241.6 [236.2,247.0] | 0.0493 [0.0359,0.0617] | 0.8686 | 0.0560 | 0.0778 [0.0758,0.0799] | 0.0778 | 189.22 [184.32,194.11] |

## Population-null control audit

Finite-stream oracle flags are shown separately from the population-null test result.

| Scenario | Method | Population-null alarms / streams | Finite-stream oracle flags / streams |
|---|---|---:|---:|
| benign_nuisance | decision_value_proxy | 0/30 | 0/30 |
| benign_nuisance | evidence_growth_stabilized_proxy | 0/30 | 0/30 |
| benign_nuisance | uniform_proxy | 0/30 | 0/30 |
| stationary | decision_value_proxy | 0/30 | 0/30 |
| stationary | evidence_growth_stabilized_proxy | 0/30 | 0/30 |
| stationary | uniform_proxy | 0/30 | 0/30 |

## Assumptions and limits

The proposed conditional null is that the mean of paired deployed-minus-reference cost, centered by epsilon=0.1, is nonpositive given prior information. Query indicators are Bernoulli with recorded predictable propensities; labels are immediate; costs are bounded; query probabilities are bounded below by the configured floor for proxy-corrected methods. The proxy is outcome-free at prediction time, and every online refit occurs only after queried feedback.
When heterogeneous label costs are enabled, the tariff is a known function of the last learner-visible feature and lies in [0.5, 2.5]. Sparse-query methods are matched to expected validation spend, while monitor-period realized spend can change under covariate shift. This is neither a fixed label-count budget nor a guaranteed spend cap. Cost-variance allocation is the classical clipped Neyman solution for estimator variance under known costs; its improvement in detection delay or decision utility is not established here.

The estimator correction is unbiased under conditional Bernoulli sampling and positive known propensities, even when the proxy is misspecified. The e-process uses a fixed worst-case bound for each query design, preserving the stated unconditional conditional-mean null when query probabilities depend on current features. Empirical null crossing rates are diagnostics, not the validity proof. The variance and decision-value acquisition policies are heuristics; no optimality or novelty claim is made.
Stationary and benign-nuisance streams are population-null controls, independently verified below epsilon. Their finite-stream oracle averages can cross epsilon by chance; those pathwise flags are retained as `sample_path_material_harm` and are not counted as true alternatives. Every monitor alarm on these population-null controls counts as a false escalation. For shifted alternatives, evaluator-known finite-regime oracle averages continue to define the sample-specific harm onset.

`cumulative_net_cost_vs_reference` adds an imposed label price of 0.01 per acquired label to evaluator-known expected excess decision cost. This is sensitivity-analysis bookkeeping, not a validated real-world label price. This monitoring experiment takes no action after an alarm, so it cannot establish controller value or reduced harm. Candidate certification is evaluated separately in `promotion_comparison.md`; the one-step controller is not yet integrated into a closed-loop intervention benchmark.

## Artifacts

`metrics/method_comparison.parquet` contains one row per seed, scenario, and method, including query propensities, e-process alarms, delay, proxy diagnostics, estimator error, MMD, predictive Brier loss, paired expected harm, synthetic oracle regret, and label-adjusted cost. Figures are generated from these rows.
