# Independent harm confirmation at q_min=.20

This pre-specified confirmation uses disjoint seeds `53000000–53000199`, 200 independent streams in each alternative, a 20% hard dollar cap, uniform querying, alpha=.05, epsilon=.10, and the common prediction-powered bound 45.9. Fixed mixture was primary; predictable variance was secondary; PM-EB was exploratory. All monitors received the same labels, increments, and stopping horizon.

|Scenario|Monitor|Detections / 200 (95% Wilson)|Onsets reached|Median delay given detection|Mean labels|Mean spend / budget|Cap violations|
|---|---|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|fixed_mixture|145/200 ([0.659, 0.782])|200/200|1161.0|470.54|705.23 / 719.35|0|
|boundary_local_harm|predictable_variance|125/200 ([0.556, 0.689])|200/200|1164.0|470.54|705.23 / 719.35|0|
|boundary_local_harm|predictable_empirical_bernstein|9/200 ([0.024, 0.083])|200/200|1429.0|470.54|705.23 / 719.35|0|
|recurring_regimes|fixed_mixture|131/200 ([0.587, 0.717])|200/200|1922.0|470.54|705.23 / 719.35|0|
|recurring_regimes|predictable_variance|126/200 ([0.561, 0.694])|200/200|1938.0|470.54|705.23 / 719.35|0|
|recurring_regimes|predictable_empirical_bernstein|10/200 ([0.027, 0.090])|200/200|2242.0|470.54|705.23 / 719.35|0|

## Paired comparison

|Scenario|Fixed-mixture-only detections|Comparator-only detections|Comparator|Exact McNemar p|Holm-adjusted p (four tests)|
|---|---:|---:|---|---:|---:|
|boundary_local_harm|20|0|predictable_variance|1.907e-06|3.815e-06|
|boundary_local_harm|136|0|predictable_empirical_bernstein|2.296e-41|9.184e-41|
|recurring_regimes|5|0|predictable_variance|0.0625|0.0625|
|recurring_regimes|121|0|predictable_empirical_bernstein|7.523e-37|2.257e-36|

## Interpretation

Fixed mixture detected 145/200 (72.5%) boundary-local harms and 131/200 (65.5%) recurring-regime harms. Every onset was reached; no result is censored by missing the predeclared onset. Its median delay among detections was 1,161 and 1,922 events, respectively.

The paired evidence favors fixed mixture over predictable variance in the boundary-local alternative (20 streams detected only by fixed mixture, none only by variance; Holm-adjusted exact p is shown above). In recurring regimes, the difference is smaller (5 fixed-only, 0 variance-only; adjusted evidence does not meet .05). PM-EB detected only 9/200 and 10/200, with fixed mixture winning nearly every discordant pair. These results support fixed mixture as the lead monitor for this specified design, not universal superiority or novelty. The two null controls independently had 0/2,000 escalations per monitor, but synthetic calibration does not validate assumptions on real delayed or dependent feedback.

## Reproduction

Run the stream simulation command in `docs/harm_confirmation_qmin020_protocol.md`, then `uv run python scripts/analyze_harm_confirmation.py`. Aggregate and stream metrics, paired tests, figures, and a manifest are stored in this output directory.
