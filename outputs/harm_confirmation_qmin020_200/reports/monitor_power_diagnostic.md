# Fresh-seed hard-budget monitor diagnostic

This is a development diagnostic following the completed budget frontier. It compares a fixed bounded-mean stake mixture with two existing predictable global-bound betting baselines: a smoothed variance-adaptive stake and predictable plug-in empirical Bernstein (PM-EB). Both comparator processes use the same prediction-powered estimate, global bound, query policy, labels, stopping rule, and alpha as the fixed mixture. Their stakes use only past evidence. These are established comparator algorithms, not novel contributions.

The run used 200 independent streams per scenario (seeds 53000000–53000199), n=3200, d=16, a 20% hard dollar cap, q_min=0.20, q_max=0.80, alpha=0.05, and the common global bound. For the selected registered scenarios, M=max(FN cost, FP cost)+margin=5.10, so the prediction-powered increment bound is M(2/q_min-1)=45.90. Requested device: `cuda`; resolved device: `NVIDIA GeForce RTX 4060 Laptop GPU`.

The primary outcomes are false escalation on stationary and benign-nuisance controls, harm detection and delay on boundary-local and recurring alternatives, onset reachability, and label spend/horizon. Report Wilson intervals and paired exact McNemar comparisons against the fixed mixture. This development grid is not a confirmation, and its small null cells cannot establish 5% calibration.

|Scenario|Query policy|Monitor|Detections / harmful|Reached / harmful|False escalations / null|Median delay given detection|Mean spend|Mean labels|Mean horizon|Paired discordants vs fixed (wins/losses)|McNemar p|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|uniform_proxy|fixed_mixture|145/200|200/200|n/a|1161.0|705.23|470.5|0.982|0/0|n/a|
|boundary_local_harm|uniform_proxy|predictable_variance|125/200|200/200|n/a|1164.0|705.23|470.5|0.982|0/20|0.000|
|boundary_local_harm|uniform_proxy|predictable_empirical_bernstein|9/200|200/200|n/a|1429.0|705.23|470.5|0.982|0/136|0.000|
|recurring_regimes|uniform_proxy|fixed_mixture|131/200|200/200|n/a|1922.0|705.23|470.5|0.982|0/0|n/a|
|recurring_regimes|uniform_proxy|predictable_variance|126/200|200/200|n/a|1938.0|705.23|470.5|0.982|0/5|0.062|
|recurring_regimes|uniform_proxy|predictable_empirical_bernstein|10/200|200/200|n/a|2242.0|705.23|470.5|0.982|0/121|0.000|

Detection and false-escalation confidence intervals are in `metrics/monitor_comparison.csv`. The event-level method metrics are in `metrics/hard_budget_comparison.parquet`.

Interpret the comparison under the history-conditional mean null and the globally bounded prediction-powered increments. Do not use current-covariate-specific normalization to claim aggregate-null validity. Any monitor that looks promising requires a separate 2,000-stream null calibration and an independently seeded confirmation with a nonzero expected detection rate.

![Monitor power comparison](../figures/monitor_power_comparison.png)

Reproduce with `uv run python scripts/diagnose_hard_budget_monitors.py --output outputs/harm_confirmation_qmin020_200 --seeds 200 --seed-offset 53000000 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.2 --device cuda`.