# History-predictable PPI bound calibration and localized-harm benchmark

## Locked setup

This GPU/CPU synthetic benchmark used 2,000 paired streams per condition, a 2400-event horizon, alpha 0.05, and a hard cap of 480 labels. The null has exactly zero aggregate expected paired cost contrast and variance 13: the low- and high-cost strata have expected contrasts -0.12 and +0.12. At event 1200, only the high-cost outcome law changes. The registered post-onset aggregate expected-cost effects are (0.04, 0.2, 0.4, 0.6); the high-stratum probability is derived from each effect before outcome generation.

The learner receives an empirical two-stratum proxy fit on 512 independent pre-monitor examples per stream. Query probabilities use prior process wealth and prior spend only. The fixed-bound process uses `B=M(2/q_min-1)`. Its paired comparator uses `B_t=M(2/q_t-1)` with the policy's current propensity, which is predictable because it is a function of prior wealth and spend. Both use the same stakes, alpha, hard label cap, and common random numbers. No oracle truth enters the learner or query policy.

The exact mixture-bound argument is standard: under the conditional-mean null, predictable q makes B_t history-predictable; the PPI estimate has the paired-cost contrast as its conditional mean and satisfies `|H_t|≤B_t`; therefore each nonnegative betting factor has conditional expectation at most one. This experiment checks code behavior and finite Monte Carlo calibration for the registered independent-stream DGP. It does not establish validity under dependence, delayed or informative labels, policy changes, or candidate selection, and it does not support a novelty claim.

## Null calibration

|Query arm|q floor|Bound|False escalations / streams|Rate|Wilson 95% interval|Mean labels|Mean events|
|---|---:|---|---:|---:|---:|---:|---:|
| evidence_qmin_0.05_fixed | 0.05 | fixed | 2/2000 | 0.100% | [0.027%, 0.364%] | 296.5 | 2399.6 |
| evidence_qmin_0.05_predictable | 0.05 | predictable | 26/2000 | 1.300% | [0.889%, 1.898%] | 169.8 | 2376.8 |
| evidence_qmin_0.10_fixed | 0.10 | fixed | 23/2000 | 1.150% | [0.768%, 1.720%] | 354.7 | 2362.5 |
| evidence_qmin_0.10_predictable | 0.10 | predictable | 32/2000 | 1.600% | [1.136%, 2.250%] | 284.0 | 2367.9 |
| evidence_qmin_0.15_fixed | 0.15 | fixed | 24/2000 | 1.200% | [0.808%, 1.779%] | 425.4 | 2263.7 |
| evidence_qmin_0.15_predictable | 0.15 | predictable | 28/2000 | 1.400% | [0.970%, 2.016%] | 391.2 | 2343.1 |
| uniform_q020 | 0.20 | fixed | 39/2000 | 1.950% | [1.430%, 2.655%] | 465.6 | 2328.7 |

## Localized-harm detection

|Scenario|Query arm|q floor|Bound|Detections / streams|Rate|Wilson 95% interval|Pre-onset escalations|Onsets reached|Mean delay if detected|Mean labels|Mean harm exposure events|Mean cumulative expected harm cost|
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_cost_local_harm_d0.04 | evidence_qmin_0.05_fixed | 0.05 | fixed | 3/2000 | 0.150% | [0.051%, 0.440%] | 0 | 2000/2000 | 889.0 | 299.0 | 1199.4 | 47.976 |
| high_cost_local_harm_d0.04 | evidence_qmin_0.05_predictable | 0.05 | predictable | 8/2000 | 0.400% | [0.203%, 0.787%] | 20 | 1980/2000 | 401.2 | 171.5 | 1184.6 | 47.382 |
| high_cost_local_harm_d0.04 | evidence_qmin_0.10_fixed | 0.10 | fixed | 21/2000 | 1.050% | [0.688%, 1.600%] | 6 | 1994/2000 | 479.3 | 355.9 | 1161.0 | 46.442 |
| high_cost_local_harm_d0.04 | evidence_qmin_0.10_predictable | 0.10 | predictable | 11/2000 | 0.550% | [0.307%, 0.982%] | 25 | 1975/2000 | 543.8 | 285.4 | 1175.7 | 47.029 |
| high_cost_local_harm_d0.04 | evidence_qmin_0.15_fixed | 0.15 | fixed | 10/2000 | 0.500% | [0.272%, 0.918%] | 17 | 1983/2000 | 302.5 | 425.8 | 1063.8 | 42.551 |
| high_cost_local_harm_d0.04 | evidence_qmin_0.15_predictable | 0.15 | predictable | 8/2000 | 0.400% | [0.203%, 0.787%] | 24 | 1976/2000 | 410.2 | 391.6 | 1151.2 | 46.048 |
| high_cost_local_harm_d0.04 | uniform_q020 | 0.20 | fixed | 8/2000 | 0.400% | [0.203%, 0.787%] | 35 | 1965/2000 | 702.9 | 465.5 | 1138.5 | 45.541 |
| high_cost_local_harm_d0.20 | evidence_qmin_0.05_fixed | 0.05 | fixed | 13/2000 | 0.650% | [0.380%, 1.109%] | 0 | 2000/2000 | 928.2 | 310.1 | 1198.2 | 239.631 |
| high_cost_local_harm_d0.20 | evidence_qmin_0.05_predictable | 0.05 | predictable | 44/2000 | 2.200% | [1.643%, 2.940%] | 20 | 1980/2000 | 676.5 | 179.9 | 1176.3 | 235.250 |
| high_cost_local_harm_d0.20 | evidence_qmin_0.10_fixed | 0.10 | fixed | 51/2000 | 2.550% | [1.945%, 3.337%] | 6 | 1994/2000 | 572.7 | 362.0 | 1150.1 | 230.027 |
| high_cost_local_harm_d0.20 | evidence_qmin_0.10_predictable | 0.10 | predictable | 32/2000 | 1.600% | [1.136%, 2.250%] | 25 | 1975/2000 | 667.7 | 292.7 | 1170.6 | 234.122 |
| high_cost_local_harm_d0.20 | evidence_qmin_0.15_fixed | 0.15 | fixed | 30/2000 | 1.500% | [1.053%, 2.133%] | 17 | 1983/2000 | 461.6 | 428.4 | 1053.7 | 210.733 |
| high_cost_local_harm_d0.20 | evidence_qmin_0.15_predictable | 0.15 | predictable | 25/2000 | 1.250% | [0.848%, 1.839%] | 24 | 1976/2000 | 604.6 | 395.0 | 1144.5 | 228.901 |
| high_cost_local_harm_d0.20 | uniform_q020 | 0.20 | fixed | 34/2000 | 1.700% | [1.219%, 2.366%] | 35 | 1965/2000 | 699.7 | 464.3 | 1132.8 | 226.556 |
| high_cost_local_harm_d0.40 | evidence_qmin_0.05_fixed | 0.05 | fixed | 40/2000 | 2.000% | [1.472%, 2.712%] | 0 | 2000/2000 | 894.9 | 323.7 | 1193.8 | 477.523 |
| high_cost_local_harm_d0.40 | evidence_qmin_0.05_predictable | 0.05 | predictable | 135/2000 | 6.750% | [5.731%, 7.935%] | 20 | 1980/2000 | 745.3 | 192.7 | 1157.1 | 462.854 |
| high_cost_local_harm_d0.40 | evidence_qmin_0.10_fixed | 0.10 | fixed | 143/2000 | 7.150% | [6.101%, 8.363%] | 6 | 1994/2000 | 679.2 | 370.7 | 1129.2 | 451.691 |
| high_cost_local_harm_d0.40 | evidence_qmin_0.10_predictable | 0.10 | predictable | 135/2000 | 6.750% | [5.731%, 7.935%] | 25 | 1975/2000 | 751.3 | 302.9 | 1149.2 | 459.667 |
| high_cost_local_harm_d0.40 | evidence_qmin_0.15_fixed | 0.15 | fixed | 91/2000 | 4.550% | [3.721%, 5.554%] | 17 | 1983/2000 | 538.5 | 432.8 | 1037.3 | 414.907 |
| high_cost_local_harm_d0.40 | evidence_qmin_0.15_predictable | 0.15 | predictable | 84/2000 | 4.200% | [3.405%, 5.170%] | 24 | 1976/2000 | 700.9 | 401.8 | 1129.6 | 451.840 |
| high_cost_local_harm_d0.40 | uniform_q020 | 0.20 | fixed | 131/2000 | 6.550% | [5.547%, 7.720%] | 35 | 1965/2000 | 757.0 | 460.5 | 1114.2 | 445.699 |
| high_cost_local_harm_d0.60 | evidence_qmin_0.05_fixed | 0.05 | fixed | 156/2000 | 7.800% | [6.704%, 9.058%] | 0 | 2000/2000 | 938.0 | 336.8 | 1179.5 | 707.706 |
| high_cost_local_harm_d0.60 | evidence_qmin_0.05_predictable | 0.05 | predictable | 362/2000 | 18.100% | [16.474%, 19.848%] | 20 | 1980/2000 | 735.2 | 202.7 | 1103.8 | 662.282 |
| high_cost_local_harm_d0.60 | evidence_qmin_0.10_fixed | 0.10 | fixed | 321/2000 | 16.050% | [14.507%, 17.724%] | 6 | 1994/2000 | 721.6 | 378.3 | 1093.7 | 656.200 |
| high_cost_local_harm_d0.60 | evidence_qmin_0.10_predictable | 0.10 | predictable | 361/2000 | 18.050% | [16.426%, 19.796%] | 25 | 1975/2000 | 745.1 | 310.5 | 1097.9 | 658.735 |
| high_cost_local_harm_d0.60 | evidence_qmin_0.15_fixed | 0.15 | fixed | 242/2000 | 12.100% | [10.743%, 13.602%] | 17 | 1983/2000 | 646.3 | 436.8 | 1010.6 | 606.370 |
| high_cost_local_harm_d0.60 | evidence_qmin_0.15_predictable | 0.15 | predictable | 312/2000 | 15.600% | [14.076%, 17.256%] | 24 | 1976/2000 | 756.4 | 405.0 | 1083.8 | 650.281 |
| high_cost_local_harm_d0.60 | uniform_q020 | 0.20 | fixed | 317/2000 | 15.850% | [14.315%, 17.516%] | 35 | 1965/2000 | 795.2 | 454.1 | 1082.3 | 649.378 |

## Paired predictable-bound minus fixed-bound differences

|Scenario|q floor|Measure|Dynamic minus fixed|Paired bootstrap 95% interval|Positive / negative stream differences|
|---|---:|---|---:|---:|---:|
| high_cost_local_harm_d0.04 | 0.05 | post_onset_detection | +0.0025 | [-0.0005, +0.0060] | 8 / 3 |
| high_cost_local_harm_d0.04 | 0.05 | labels_queried | -127.4160 | [-131.4970, -123.3248] | 42 / 1957 |
| high_cost_local_harm_d0.04 | 0.05 | evaluator_cumulative_expected_harm_cost | -0.5934 | [-0.8286, -0.3754] | 5 / 33 |
| high_cost_local_harm_d0.04 | 0.10 | post_onset_detection | -0.0050 | [-0.0100, -0.0005] | 7 / 17 |
| high_cost_local_harm_d0.04 | 0.10 | labels_queried | -70.5225 | [-73.5536, -67.4905] | 60 / 1888 |
| high_cost_local_harm_d0.04 | 0.10 | evaluator_cumulative_expected_harm_cost | +0.5877 | [+0.3181, +0.8468] | 240 / 40 |
| high_cost_local_harm_d0.04 | 0.15 | post_onset_detection | -0.0010 | [-0.0050, +0.0025] | 6 / 8 |
| high_cost_local_harm_d0.04 | 0.15 | labels_queried | -34.2455 | [-36.4756, -32.0355] | 50 / 1707 |
| high_cost_local_harm_d0.04 | 0.15 | evaluator_cumulative_expected_harm_cost | +3.4970 | [+3.1462, +3.8514] | 640 / 41 |
| high_cost_local_harm_d0.20 | 0.05 | post_onset_detection | +0.0155 | [+0.0090, +0.0220] | 39 / 8 |
| high_cost_local_harm_d0.20 | 0.05 | labels_queried | -130.2780 | [-134.3378, -126.1065] | 52 / 1946 |
| high_cost_local_harm_d0.20 | 0.05 | evaluator_cumulative_expected_harm_cost | -4.3805 | [-5.6693, -3.1197] | 8 / 67 |
| high_cost_local_harm_d0.20 | 0.10 | post_onset_detection | -0.0095 | [-0.0170, -0.0025] | 17 / 36 |
| high_cost_local_harm_d0.20 | 0.10 | labels_queried | -69.3000 | [-72.5085, -66.2599] | 83 / 1864 |
| high_cost_local_harm_d0.20 | 0.10 | evaluator_cumulative_expected_harm_cost | +4.0948 | [+2.6938, +5.4728] | 299 / 49 |
| high_cost_local_harm_d0.20 | 0.15 | post_onset_detection | -0.0025 | [-0.0080, +0.0030] | 13 / 18 |
| high_cost_local_harm_d0.20 | 0.15 | labels_queried | -33.3740 | [-35.6141, -31.1458] | 61 / 1673 |
| high_cost_local_harm_d0.20 | 0.15 | evaluator_cumulative_expected_harm_cost | +18.1683 | [+16.3668, +20.0026] | 663 / 54 |
| high_cost_local_harm_d0.40 | 0.05 | post_onset_detection | +0.0475 | [+0.0365, +0.0585] | 112 / 17 |
| high_cost_local_harm_d0.40 | 0.05 | labels_queried | -131.0145 | [-135.2978, -126.7685] | 69 / 1924 |
| high_cost_local_harm_d0.40 | 0.05 | evaluator_cumulative_expected_harm_cost | -14.6690 | [-17.6560, -11.6849] | 20 / 154 |
| high_cost_local_harm_d0.40 | 0.10 | post_onset_detection | -0.0040 | [-0.0150, +0.0070] | 58 / 66 |
| high_cost_local_harm_d0.40 | 0.10 | labels_queried | -67.7650 | [-70.8436, -64.7558] | 118 / 1836 |
| high_cost_local_harm_d0.40 | 0.10 | evaluator_cumulative_expected_harm_cost | +7.9758 | [+4.8835, +11.1464] | 351 / 113 |
| high_cost_local_harm_d0.40 | 0.15 | post_onset_detection | -0.0035 | [-0.0120, +0.0050] | 34 / 41 |
| high_cost_local_harm_d0.40 | 0.15 | labels_queried | -30.9850 | [-33.3041, -28.8384] | 93 / 1628 |
| high_cost_local_harm_d0.40 | 0.15 | evaluator_cumulative_expected_harm_cost | +36.9334 | [+33.1017, +40.6367] | 709 / 83 |
| high_cost_local_harm_d0.60 | 0.05 | post_onset_detection | +0.1030 | [+0.0865, +0.1205] | 267 / 61 |
| high_cost_local_harm_d0.60 | 0.05 | labels_queried | -134.0970 | [-138.4973, -129.8484] | 72 / 1921 |
| high_cost_local_harm_d0.60 | 0.05 | evaluator_cumulative_expected_harm_cost | -45.4242 | [-51.4007, -39.5877] | 68 / 370 |
| high_cost_local_harm_d0.60 | 0.10 | post_onset_detection | +0.0200 | [+0.0035, +0.0360] | 159 / 119 |
| high_cost_local_harm_d0.60 | 0.10 | labels_queried | -67.7915 | [-70.8916, -64.7704] | 131 / 1827 |
| high_cost_local_harm_d0.60 | 0.10 | evaluator_cumulative_expected_harm_cost | +2.5350 | [-3.1206, +8.0800] | 397 / 286 |
| high_cost_local_harm_d0.60 | 0.15 | post_onset_detection | +0.0350 | [+0.0210, +0.0495] | 140 / 70 |
| high_cost_local_harm_d0.60 | 0.15 | labels_queried | -31.8025 | [-34.0822, -29.6039] | 139 / 1619 |
| high_cost_local_harm_d0.60 | 0.15 | evaluator_cumulative_expected_harm_cost | +43.9107 | [+37.9310, +50.0251] | 730 / 213 |

These are development-grid estimates from the locked seed block. Wilson intervals describe individual cells; the paired bootstrap resamples whole streams. They are unadjusted across floors and methods, so this block does not select a winning floor or establish a confirmatory advantage. A selected configuration needs an independent seed block and an explicit familywise error plan. Zero false escalations, if observed, are not proof of the 5% guarantee.

The study uses independent synthetic events and immediate randomized labels. It does not establish robustness to time dependence, informative label availability, delayed feedback, shifting policies, or deployment interventions. Query-policy comparisons are coupled through common random numbers but can follow different propensity and stopping paths. The harm exposure metric sums evaluator-known expected excess cost at the registered dose from onset through the alarm event, or through the last processed event if no alarm occurs; it is synthetic evaluator output only.

No figure is included because project guidance requires PaperBanana and no callable PaperBanana tool is available in this session. The validated summary tables and per-stream Parquet metrics are the reported outputs.

Reproduce with:

```powershell
uv run python scripts/calibrate_history_predictable_query_bounds.py --streams 2000 --horizon 2400 --seed 27102027 --device cuda --output outputs/history_predictable_bound_calibration_2000
uv run pytest tests/test_history_predictable_query_bounds.py -q
```
