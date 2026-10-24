# Harm severity/onset/horizon grid: measured results

This CUDA development screen completed 1,080 stream-cell observations across 36 cells (30 paired seeds per cell). All 1,080 evaluator-classified streams had material harm, all 1,080 harm onsets were reached before budget stopping, and all respected the realized dollar cap. There were no missing cells or incomplete seed blocks.

## Main measured patterns

|Scenario|Monitor|Mean detection rate across cells|Median cell delay among detections|
|---|---|---:|---:|
|boundary_local_harm|fixed_mixture|0.500|1166.8|
|boundary_local_harm|predictable_variance|0.435|1240.0|
|boundary_local_harm|predictable_empirical_bernstein|0.100|1789.8|
|recurring_regimes|fixed_mixture|0.441|1559.0|
|recurring_regimes|predictable_variance|0.426|1974.0|
|recurring_regimes|predictable_empirical_bernstein|0.093|2638.5|

Empirical monotonicity counts for boundary-local harm (successes/conditioning slices): fixed_mixture: horizon 9/9, severity 9/9, earlier onset 9/9; predictable_variance: horizon 9/9, severity 9/9, earlier onset 9/9; predictable_empirical_bernstein: horizon 9/9, severity 9/9, earlier onset 9/9. Recurring-regime counts are fixed_mixture: horizon 3/3, severity 3/3; predictable_variance: horizon 3/3, severity 3/3; predictable_empirical_bernstein: horizon 3/3, severity 3/3. These are observed grid patterns, not population guarantees.

At the central boundary-local setting (`n=3200`, severity 1.50), fixed-mixture detection was 0.83 → 0.63 → 0.20 as onset fraction moved .35 → .50 → .65; it was 0.27 → 0.63 → 0.77 as severity moved .75 → 1.50 → 2.25; and 0.43 → 0.63 → 0.80 as n moved 2400 → 3200 → 4000. These rates use 30 streams per cell and each cell has its own Wilson interval in the main summary CSV.

For recurring regimes at severity 1.50, fixed-mixture rates were 0.10 → 0.57 → 0.83 across n=2400, 3200, 4000.

Across all cells, there were 57 fixed-only versus 0 variance-only detections, and 418 fixed-only versus 0 PM-EB-only detections. Because seed streams recur across the parameter cells, these pooled discordances are descriptive and are not treated as independent tests. Cellwise exact p-values in `harm_power_grid_paired_tests.csv` are exploratory and unadjusted.

## Interpretation and limits

The screen supports the earlier conclusion that fixed mixture is a strong baseline in these settings, while PM-EB is substantially more conservative. The fixed-mixture advantage over predictable variance is largest at earlier onsets and stronger harm; the two are closer in some high-severity/long-horizon cells. These patterns do not identify a new algorithm. The 20% dollar budget scales with the available horizon, so horizon trends combine more observation time with more total label dollars. They are not a fixed-total-cost causal comparison.

This is a 30-seed development grid, not a final confirmatory test. No false-alarm controls were included in this alternative-only screen; the independent null calibration is reported separately. The bounded e-process result remains conditional on the history-conditional mean null and valid propensity/increment bounds, and the experiment does not cover delayed feedback, serial dependence outside the registered generator, or real-world distribution shift.

## Reproduction and artifacts

Rebuild the grid using `docs/harm_power_grid_protocol.md` and run `uv run python scripts/analyze_harm_power_grid.py` for this summary. See the full 108-cell monitor table in `reports/harm_power_grid.md`, stream metrics in `metrics/harm_power_grid.parquet`, cellwise paired contrasts in `metrics/harm_power_grid_paired_tests.csv`, and the figure `figures/harm_power_grid.png`.
