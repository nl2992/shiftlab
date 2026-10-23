# DIVE initial evidence-acquisition comparison

Generated from 30 paired evaluation seeds for each of 6 scenarios. Resolved device: `cuda`.

## Implemented variants

- `full_feedback`: all monitor-period labels; direct paired-cost e-process.
- `uniform_direct`: uniform Bernoulli queries and direct inverse-propensity paired-cost estimates.
- `uniform_proxy`: uniform queries with prediction-powered correction.
- `pprm_reliance_analogue`: uniform queries with a predictable historical plug-in scalar for proxy reliance. This is not the full PPRM algorithm or its confidence-sequence construction.
- `uncertainty_proxy`: entropy-based query propensities calibrated on the pre-monitor validation slice.
- `variance_proxy`: query scores proportional to the square root of a held-out model for proxy residual second moments.
- `decision_value_proxy`: a heuristic that increases sampling near the harm margin when proxy residual uncertainty is high.

All fitted proxies and query multipliers use only the pre-monitor training/validation rows. Proxy refits use queried outcomes only after they arrive. Query outcomes are immediate in this first experiment. This monitor benchmark takes no action after alarms; candidate promotion is evaluated in a separate forward-time experiment.

## Preliminary results

These are descriptive paired-stream Monte Carlo results, not confirmatory inference. `rmse_stream_mean` is computed across independent seeds. False-escalation proportions have only 30 stream replicates per cell. The change-aware mixture is reported in the Parquet artifact; this report's table summarizes the single-start process.

Independent seeds are the inferential units. False-escalation intervals use Wilson's method over all population-null control streams and pre-onset alternative streams; detection intervals use only streams with evaluator-known harm onsets. Finite-stream oracle excursions within population-null controls are recorded separately. Labels and expected harm use t intervals across seeds; stream-mean RMSE uses a deterministic percentile bootstrap over seeds. Nondetections remain in the detection denominator and are not discarded from the Parquet data.

| Scenario | Method | False escalation (95% Wilson) | Detection on harmful streams (95% Wilson) | Delay among detected | Labels/stream (95% t CI) | Realized label spend/stream (95% t CI) | Stream-mean RMSE (95% bootstrap) | Proxy RMSE | Predictive Brier | Expected harm (95% t CI) | Oracle regret | Net cost vs ref (95% t CI) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| benign_nuisance | decision_value_proxy | 0.00 [0.00,0.11] | — | — | 321.6 [303.6,339.6] | 3.2 [3.0,3.4] | 0.0494 [0.0363,0.0632] | 0.9101 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 197.56 [192.26,202.86] |
| benign_nuisance | full_feedback | 0.03 [0.01,0.17] | — | — | 2400.0 [2400.0,2400.0] | 24.0 [24.0,24.0] | 0.0000 [0.0000,0.0000] | 0.9966 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 218.35 [213.00,223.70] |
| benign_nuisance | pprm_reliance_analogue | 0.00 [0.00,0.11] | — | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0465 [0.0302,0.0615] | 0.8731 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.73 [191.38,202.08] |
| benign_nuisance | uncertainty_proxy | 0.00 [0.00,0.11] | — | — | 233.9 [227.1,240.8] | 2.3 [2.3,2.4] | 0.0505 [0.0385,0.0631] | 0.9071 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.69 [191.32,202.05] |
| benign_nuisance | uniform_direct | 0.00 [0.00,0.11] | — | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0465 [0.0305,0.0622] | 0.8721 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.73 [191.38,202.08] |
| benign_nuisance | uniform_proxy | 0.00 [0.00,0.11] | — | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0490 [0.0336,0.0657] | 0.9004 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.73 [191.38,202.08] |
| benign_nuisance | variance_proxy | 0.00 [0.00,0.11] | — | — | 352.6 [334.9,370.3] | 3.5 [3.3,3.7] | 0.0428 [0.0295,0.0552] | 0.8954 | 0.0802 | 0.0810 [0.0787,0.0832] | 0.0810 | 197.87 [192.52,203.23] |
| boundary_local_harm | decision_value_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 245.3 [238.5,252.2] | 2.5 [2.4,2.5] | 0.1066 [0.0869,0.1244] | 1.2409 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 676.22 [658.17,694.27] |
| boundary_local_harm | full_feedback | 0.00 [0.00,0.11] | 1.00 [0.89,1.00] | 356 | 2400.0 [2400.0,2400.0] | 24.0 [24.0,24.0] | 0.0000 [0.0000,0.0000] | 1.2463 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 697.76 [679.71,715.82] |
| boundary_local_harm | pprm_reliance_analogue | 0.00 [0.00,0.11] | 0.17 [0.07,0.34] | 1358 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0724 [0.0568,0.0868] | 1.2304 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 676.15 [658.09,694.21] |
| boundary_local_harm | uncertainty_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 236.1 [229.3,242.9] | 2.4 [2.3,2.4] | 0.0531 [0.0421,0.0633] | 1.2363 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 676.13 [658.05,694.20] |
| boundary_local_harm | uniform_direct | 0.00 [0.00,0.11] | 0.47 [0.30,0.64] | 1120 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0728 [0.0571,0.0869] | 1.2296 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 676.15 [658.09,694.21] |
| boundary_local_harm | uniform_proxy | 0.00 [0.00,0.11] | 0.17 [0.07,0.34] | 1304 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0739 [0.0571,0.0888] | 1.2397 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 676.15 [658.09,694.21] |
| boundary_local_harm | variance_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 242.4 [237.0,247.8] | 2.4 [2.4,2.5] | 0.0880 [0.0691,0.1043] | 1.2399 | 0.0644 | 0.2807 [0.2732,0.2883] | 0.3125 | 676.19 [658.13,694.25] |
| harmful_adaptation | decision_value_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 247.4 [241.2,253.5] | 2.5 [2.4,2.5] | 0.0604 [0.0431,0.0765] | 0.7827 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 657.24 [651.22,663.26] |
| harmful_adaptation | full_feedback | 0.00 [0.00,0.11] | 1.00 [0.89,1.00] | 367 | 2400.0 [2400.0,2400.0] | 24.0 [24.0,24.0] | 0.0000 [0.0000,0.0000] | 0.8078 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 678.77 [672.75,684.78] |
| harmful_adaptation | pprm_reliance_analogue | 0.00 [0.00,0.11] | 0.03 [0.01,0.17] | 1205 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0494 [0.0380,0.0595] | 0.7819 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 657.15 [651.13,663.17] |
| harmful_adaptation | uncertainty_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 236.1 [229.3,242.9] | 2.4 [2.3,2.4] | 0.0455 [0.0311,0.0605] | 0.7885 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 657.13 [651.11,663.15] |
| harmful_adaptation | uniform_direct | 0.00 [0.00,0.11] | 0.60 [0.42,0.75] | 1110 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0495 [0.0384,0.0606] | 0.7838 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 657.15 [651.13,663.17] |
| harmful_adaptation | uniform_proxy | 0.00 [0.00,0.11] | 0.07 [0.02,0.21] | 1534 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0478 [0.0375,0.0576] | 0.7820 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 657.15 [651.13,663.17] |
| harmful_adaptation | variance_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 242.4 [237.0,247.8] | 2.4 [2.4,2.5] | 0.0593 [0.0449,0.0729] | 0.7817 | 0.0577 | 0.2728 [0.2703,0.2753] | 0.2728 | 657.19 [651.16,663.22] |
| recurring_regimes | decision_value_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 240.1 [232.3,247.8] | 2.4 [2.3,2.5] | 0.1019 [0.0785,0.1232] | 1.2398 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 667.80 [650.75,684.85] |
| recurring_regimes | full_feedback | 0.00 [0.00,0.11] | 1.00 [0.89,1.00] | 147 | 2400.0 [2400.0,2400.0] | 24.0 [24.0,24.0] | 0.0000 [0.0000,0.0000] | 1.2442 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 689.40 [672.35,706.45] |
| recurring_regimes | pprm_reliance_analogue | 0.00 [0.00,0.11] | 0.13 [0.05,0.30] | 2263 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0858 [0.0677,0.1043] | 1.2286 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 667.78 [650.73,684.84] |
| recurring_regimes | uncertainty_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 236.1 [229.3,242.9] | 2.4 [2.3,2.4] | 0.0552 [0.0430,0.0671] | 1.2379 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 667.76 [650.70,684.82] |
| recurring_regimes | uniform_direct | 0.00 [0.00,0.11] | 0.50 [0.33,0.67] | 2001 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0860 [0.0684,0.1031] | 1.2281 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 667.78 [650.73,684.84] |
| recurring_regimes | uniform_proxy | 0.00 [0.00,0.11] | 0.13 [0.05,0.30] | 2279 | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0874 [0.0689,0.1050] | 1.2389 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 667.78 [650.73,684.84] |
| recurring_regimes | variance_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 242.4 [237.0,247.8] | 2.4 [2.4,2.5] | 0.0911 [0.0742,0.1058] | 1.2388 | 0.0642 | 0.2772 [0.2701,0.2844] | 0.3089 | 667.82 [650.76,684.89] |
| residual_variance | decision_value_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 246.8 [240.4,253.3] | 2.5 [2.4,2.5] | 0.0749 [0.0580,0.0920] | 0.9653 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 279.72 [272.97,286.47] |
| residual_variance | full_feedback | 0.00 [0.00,0.11] | 0.07 [0.02,0.21] | 868 | 2400.0 [2400.0,2400.0] | 24.0 [24.0,24.0] | 0.0000 [0.0000,0.0000] | 0.9659 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 301.25 [294.49,308.00] |
| residual_variance | pprm_reliance_analogue | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0519 [0.0370,0.0653] | 0.9485 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 279.63 [272.86,286.40] |
| residual_variance | uncertainty_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 236.1 [229.3,242.9] | 2.4 [2.3,2.4] | 0.0400 [0.0316,0.0480] | 0.9664 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 279.61 [272.83,286.39] |
| residual_variance | uniform_direct | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0522 [0.0390,0.0653] | 0.9478 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 279.63 [272.86,286.40] |
| residual_variance | uniform_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0550 [0.0401,0.0696] | 0.9637 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 279.63 [272.86,286.40] |
| residual_variance | variance_proxy | 0.00 [0.00,0.11] | 0.00 [0.00,0.11] | — | 242.4 [237.0,247.8] | 2.4 [2.4,2.5] | 0.0621 [0.0450,0.0790] | 0.9638 | 0.0991 | 0.1155 [0.1127,0.1183] | 0.1569 | 279.67 [272.91,286.44] |
| stationary | decision_value_proxy | 0.00 [0.00,0.11] | — | — | 248.0 [241.6,254.4] | 2.5 [2.4,2.5] | 0.0646 [0.0482,0.0806] | 0.8900 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.83 [191.49,202.16] |
| stationary | full_feedback | 0.03 [0.01,0.17] | — | — | 2400.0 [2400.0,2400.0] | 24.0 [24.0,24.0] | 0.0000 [0.0000,0.0000] | 0.8911 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 218.35 [213.00,223.70] |
| stationary | pprm_reliance_analogue | 0.00 [0.00,0.11] | — | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0465 [0.0306,0.0619] | 0.8726 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.73 [191.38,202.08] |
| stationary | uncertainty_proxy | 0.00 [0.00,0.11] | — | — | 236.1 [229.3,242.9] | 2.4 [2.3,2.4] | 0.0353 [0.0293,0.0410] | 0.8920 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.71 [191.34,202.07] |
| stationary | uniform_direct | 0.00 [0.00,0.11] | — | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0465 [0.0302,0.0622] | 0.8721 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.73 [191.38,202.08] |
| stationary | uniform_proxy | 0.00 [0.00,0.11] | — | — | 238.4 [232.9,243.8] | 2.4 [2.3,2.4] | 0.0497 [0.0340,0.0655] | 0.8885 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.73 [191.38,202.08] |
| stationary | variance_proxy | 0.00 [0.00,0.11] | — | — | 242.4 [237.0,247.8] | 2.4 [2.4,2.5] | 0.0602 [0.0374,0.0826] | 0.8887 | 0.0577 | 0.0810 [0.0787,0.0832] | 0.0810 | 196.77 [191.41,202.13] |

## Population-null control audit

Finite-stream oracle flags are shown separately from the population-null test result.

| Scenario | Method | Population-null alarms / streams | Finite-stream oracle flags / streams |
|---|---|---:|---:|
| benign_nuisance | decision_value_proxy | 0/30 | 1/30 |
| benign_nuisance | full_feedback | 1/30 | 1/30 |
| benign_nuisance | pprm_reliance_analogue | 0/30 | 1/30 |
| benign_nuisance | uncertainty_proxy | 0/30 | 1/30 |
| benign_nuisance | uniform_direct | 0/30 | 1/30 |
| benign_nuisance | uniform_proxy | 0/30 | 1/30 |
| benign_nuisance | variance_proxy | 0/30 | 1/30 |
| stationary | decision_value_proxy | 0/30 | 0/30 |
| stationary | full_feedback | 1/30 | 0/30 |
| stationary | pprm_reliance_analogue | 0/30 | 0/30 |
| stationary | uncertainty_proxy | 0/30 | 0/30 |
| stationary | uniform_direct | 0/30 | 0/30 |
| stationary | uniform_proxy | 0/30 | 0/30 |
| stationary | variance_proxy | 0/30 | 0/30 |

## Assumptions and limits

The proposed conditional null is that the mean of paired deployed-minus-reference cost, centered by epsilon=0.1, is nonpositive given prior information. Query indicators are Bernoulli with recorded predictable propensities; labels are immediate; costs are bounded; query probabilities are bounded below by the configured floor for proxy-corrected methods. The proxy is outcome-free at prediction time, and every online refit occurs only after queried feedback.

The estimator correction is unbiased under conditional Bernoulli sampling and positive known propensities, even when the proxy is misspecified. The e-process uses a fixed worst-case bound for each query design, preserving the stated unconditional conditional-mean null when query probabilities depend on current features. Empirical null crossing rates are diagnostics, not the validity proof. The variance and decision-value acquisition policies are heuristics; no optimality or novelty claim is made. Stationary and benign-nuisance streams are population-null controls, independently verified below epsilon. Their finite-stream oracle averages can cross epsilon by chance; those pathwise flags are retained as `sample_path_material_harm` and are not counted as true alternatives. Every monitor alarm on these population-null controls counts as a false escalation. For shifted alternatives, evaluator-known finite-regime oracle averages continue to define the sample-specific harm onset.

`cumulative_net_cost_vs_reference` adds an imposed label price of 0.01 per acquired label to evaluator-known expected excess decision cost. This is sensitivity-analysis bookkeeping, not a validated real-world label price. This monitoring experiment takes no action after an alarm, so it cannot establish controller value or reduced harm. Candidate certification is evaluated separately in `promotion_comparison.md`; the one-step controller is not yet integrated into a closed-loop intervention benchmark.

## Artifacts

`metrics/method_comparison.parquet` contains one row per seed, scenario, and method, including query propensities, e-process alarms, delay, proxy diagnostics, estimator error, MMD, predictive Brier loss, paired expected harm, synthetic oracle regret, and label-adjusted cost. Figures are generated from these rows.
