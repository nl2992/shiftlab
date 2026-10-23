# Promotion timing benchmark

This generated benchmark compares two sequential e-processes, two fixed-horizon gates, and a no-promotion control over 1000 independent streams in each of five predeclared scenarios. Potential costs are Bernoulli and generated on `cuda`; the candidate is conceptually frozen before shadow monitoring. The first 800 events are a reserved pre-monitor construction prefix and are not used to fit or select a model in this focused test; shadow monitoring spans [800,2400); the untouched final slice is [2400,3200).

The full-start and three-start e-processes use the repository's fixed-stake bounded-mean mixture at alpha=0.05. The three starts are fixed at shadow fractions (0.0, 0.3333333333333333, 0.6666666666666666); their equally weighted mixture is Ville-valid under the pointwise conditional-mean null. The fixed-horizon Hoeffding gate is valid for average expected gain under independent bounded observations, including non-identically distributed streams. The empirical-Bernstein gate uses the independent, bounded, non-identically distributed version of Maurer and Pontil's bound (Theorem 11); it tests the average expected gain at this one prespecified horizon and is not anytime-valid. All methods use the same paired monitor outcomes and cost bound.

Potential benefit in the shadow is 0 for `no_benefit`, 0.22 for the first fifth only in `early_transient`, 0.22 for the first fifth then -0.04 for the remaining stream in `benefit_reversal`, 0.12 throughout `persistent_benefit`, and 0.18 in the final third only in `late_persistent`. The scenario schedule is evaluator-only. For the sequential gates, promotion begins on the event after a crossing; for the fixed-horizon gate, promotion begins after the shadow window. Outcomes after promotion are scored with simulator-known potential costs, and the one-time switching charge is 0.05. The synthetic setup assumes actions do not alter outcomes; results do not identify counterfactual policy values in performative settings.

## Results by scenario and rule

Independent seeds are the statistical units. Intervals are Wilson 95% intervals for promotion rates and t intervals over seed-level net gains. Non-crossings are right-censored at the shadow horizon in the restricted mean certificate time.

| Scenario | Method | Promote (95% CI) | Mean oracle future net gain (95% CI) | Harmful promotion | Mean certificate time |
|---|---|---:|---:|---:|---:|
| no_benefit | sequential_full_start | 0.032 [0.023, 0.045] | -0.002 [-0.002, -0.001] | 0.032 | 274.8 |
| no_benefit | sequential_multi_start_3 | 0.032 [0.023, 0.045] | -0.002 [-0.002, -0.001] | 0.032 | 649.9 |
| no_benefit | empirical_bernstein_fixed_horizon | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| no_benefit | hoeffding_fixed_horizon | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| no_benefit | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| early_transient | sequential_full_start | 1.000 [0.996, 1.000] | 53.079 [52.378, 53.781] | 0.000 | 77.5 |
| early_transient | sequential_multi_start_3 | 0.997 [0.991, 0.999] | 47.855 [47.057, 48.653] | 0.002 | 100.6 |
| early_transient | empirical_bernstein_fixed_horizon | 0.214 [0.190, 0.240] | -0.011 [-0.012, -0.009] | 0.214 | 1599.0 |
| early_transient | hoeffding_fixed_horizon | 0.171 [0.149, 0.196] | -0.009 [-0.010, -0.007] | 0.171 | 1599.0 |
| early_transient | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| benefit_reversal | sequential_full_start | 0.997 [0.991, 0.999] | -30.131 [-30.841, -29.420] | 0.997 | 78.0 |
| benefit_reversal | sequential_multi_start_3 | 0.996 [0.990, 0.998] | -35.223 [-36.008, -34.438] | 0.996 | 101.5 |
| benefit_reversal | empirical_bernstein_fixed_horizon | 0.001 [0.000, 0.006] | -0.032 [-0.095, 0.031] | 0.001 | 1599.0 |
| benefit_reversal | hoeffding_fixed_horizon | 0.001 [0.000, 0.006] | -0.032 [-0.095, 0.031] | 0.001 | 1599.0 |
| benefit_reversal | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| persistent_benefit | sequential_full_start | 1.000 [0.996, 1.000] | 255.727 [254.309, 257.145] | 0.000 | 267.5 |
| persistent_benefit | sequential_multi_start_3 | 1.000 [0.996, 1.000] | 246.142 [244.617, 247.667] | 0.000 | 347.4 |
| persistent_benefit | empirical_bernstein_fixed_horizon | 1.000 [0.996, 1.000] | 95.950 [95.950, 95.950] | 0.000 | 1599.0 |
| persistent_benefit | hoeffding_fixed_horizon | 0.999 [0.994, 1.000] | 95.854 [95.666, 96.042] | 0.000 | 1599.0 |
| persistent_benefit | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| late_persistent | sequential_full_start | 0.688 [0.659, 0.716] | 120.536 [115.364, 125.709] | 0.000 | 1398.9 |
| late_persistent | sequential_multi_start_3 | 0.998 [0.993, 0.999] | 212.645 [211.499, 213.791] | 0.000 | 1208.3 |
| late_persistent | empirical_bernstein_fixed_horizon | 0.520 [0.489, 0.551] | 74.854 [70.389, 79.319] | 0.000 | 1599.0 |
| late_persistent | hoeffding_fixed_horizon | 0.455 [0.424, 0.486] | 65.497 [61.047, 69.948] | 0.000 | 1599.0 |
| late_persistent | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |

A promotion on a transient shadow gain can be statistically valid for the historical shadow estimand and still have nonpositive future value. The `harmful promotion` column measures that decision mismatch; it is not a false-rejection rate for the e-process null. The no-benefit scenario is the pointwise-null calibration diagnostic. A finite Monte Carlo run is not itself the validity proof. Empirical-Bernstein bound: [Maurer and Pontil (2009), Theorem 11](https://www.cs.mcgill.ca/~colt2009/papers/012.pdf).

## Reproduction

`uv run shiftlab-dive-promotion-timing --seeds 1000 --seed-offset 20401023 --device cuda --output outputs/promotion_timing_v6`

Detailed seed-level outcomes, summary metrics, the figure, and a hash manifest are stored beside this report.
