# Decision-local betting-bound calibration

This CUDA/CPU simulation compares fixed global and predictable decision-local bounds over 2000 independent streams in each cell, horizon 600, and query caps 10%, 20%, and 30%. It uses a single frozen candidate against a fixed reference, so alpha is 0.05 without a candidate-family correction.

Each event reveals a cost stratum before label acquisition. Both policies choose different actions. Conditional on either stratum, the outcome probability 0.50 makes the paired cost gain have mean zero; this is a nondegenerate pointwise null. Costs are 1 in the low stratum and 1, 2, or 5 in the high stratum. Under alternatives, the outcome probability is 0.53 or 0.56 in both strata, producing positive conditional benefit. The queried-label indicator is Bernoulli with the displayed rate until the pathwise cap is reached; monitoring stops at that point.

The global direct-IPW bound is max_cost/q. The local bound is the revealed event cost divided by q. Because the bound is predictable from information available before the current outcome and the null holds conditional on that information, each bounded betting factor has conditional expectation at most one. If only the history-conditional average null held, this data-dependent scaling would not in general preserve the sign of the expected betting increment. This experiment tests one candidate and independent streams; it is not a familywise-calibration claim for repeated promotion.

## Results

| High cost | Query cap | Outcome probability | Bound | Crossed / streams (95% Wilson CI) | Mean labels / cap | Mean events processed |
|---:|---:|---:|---|---:|---:|---:|
| 1 | 10% | 0.50 | global | 35/2000 (0.013, 0.024) | 57.1 / 60 | 569.8 |
| 1 | 10% | 0.50 | decision_local | 35/2000 (0.013, 0.024) | 57.1 / 60 | 569.8 |
| 1 | 10% | 0.53 | global | 65/2000 (0.026, 0.041) | 57.1 / 60 | 571.6 |
| 1 | 10% | 0.53 | decision_local | 65/2000 (0.026, 0.041) | 57.1 / 60 | 571.6 |
| 1 | 10% | 0.56 | global | 124/2000 (0.052, 0.073) | 57.0 / 60 | 572.0 |
| 1 | 10% | 0.56 | decision_local | 124/2000 (0.052, 0.073) | 57.0 / 60 | 572.0 |
| 1 | 20% | 0.50 | global | 33/2000 (0.012, 0.023) | 115.8 / 120 | 581.3 |
| 1 | 20% | 0.50 | decision_local | 33/2000 (0.012, 0.023) | 115.8 / 120 | 581.3 |
| 1 | 20% | 0.53 | global | 119/2000 (0.050, 0.071) | 116.2 / 120 | 580.9 |
| 1 | 20% | 0.53 | decision_local | 119/2000 (0.050, 0.071) | 116.2 / 120 | 580.9 |
| 1 | 20% | 0.56 | global | 263/2000 (0.117, 0.147) | 116.3 / 120 | 579.3 |
| 1 | 20% | 0.56 | decision_local | 263/2000 (0.117, 0.147) | 116.3 / 120 | 579.3 |
| 1 | 30% | 0.50 | global | 37/2000 (0.013, 0.025) | 175.3 / 180 | 585.4 |
| 1 | 30% | 0.50 | decision_local | 37/2000 (0.013, 0.025) | 175.3 / 180 | 585.4 |
| 1 | 30% | 0.53 | global | 120/2000 (0.050, 0.071) | 175.1 / 180 | 585.7 |
| 1 | 30% | 0.53 | decision_local | 120/2000 (0.050, 0.071) | 175.1 / 180 | 585.7 |
| 1 | 30% | 0.56 | global | 418/2000 (0.192, 0.227) | 175.5 / 180 | 584.7 |
| 1 | 30% | 0.56 | decision_local | 418/2000 (0.192, 0.227) | 175.5 / 180 | 584.7 |
| 2 | 10% | 0.50 | global | 22/2000 (0.007, 0.017) | 56.9 / 60 | 571.7 |
| 2 | 10% | 0.50 | decision_local | 24/2000 (0.008, 0.018) | 56.9 / 60 | 571.7 |
| 2 | 10% | 0.53 | global | 62/2000 (0.024, 0.040) | 57.0 / 60 | 571.4 |
| 2 | 10% | 0.53 | decision_local | 72/2000 (0.029, 0.045) | 57.0 / 60 | 571.4 |
| 2 | 10% | 0.56 | global | 111/2000 (0.046, 0.066) | 57.2 / 60 | 569.7 |
| 2 | 10% | 0.56 | decision_local | 129/2000 (0.055, 0.076) | 57.2 / 60 | 569.7 |
| 2 | 20% | 0.50 | global | 34/2000 (0.012, 0.024) | 115.8 / 120 | 580.9 |
| 2 | 20% | 0.50 | decision_local | 44/2000 (0.016, 0.029) | 115.8 / 120 | 580.9 |
| 2 | 20% | 0.53 | global | 89/2000 (0.036, 0.054) | 115.9 / 120 | 580.4 |
| 2 | 20% | 0.53 | decision_local | 103/2000 (0.043, 0.062) | 115.9 / 120 | 580.4 |
| 2 | 20% | 0.56 | global | 253/2000 (0.113, 0.142) | 116.2 / 120 | 579.5 |
| 2 | 20% | 0.56 | decision_local | 279/2000 (0.125, 0.155) | 116.2 / 120 | 579.5 |
| 2 | 30% | 0.50 | global | 36/2000 (0.013, 0.025) | 175.6 / 180 | 585.3 |
| 2 | 30% | 0.50 | decision_local | 37/2000 (0.013, 0.025) | 175.6 / 180 | 585.3 |
| 2 | 30% | 0.53 | global | 125/2000 (0.053, 0.074) | 175.5 / 180 | 585.3 |
| 2 | 30% | 0.53 | decision_local | 128/2000 (0.054, 0.076) | 175.5 / 180 | 585.3 |
| 2 | 30% | 0.56 | global | 384/2000 (0.175, 0.210) | 175.7 / 180 | 584.3 |
| 2 | 30% | 0.56 | decision_local | 432/2000 (0.199, 0.235) | 175.7 / 180 | 584.3 |
| 5 | 10% | 0.50 | global | 29/2000 (0.010, 0.021) | 57.0 / 60 | 571.4 |
| 5 | 10% | 0.50 | decision_local | 34/2000 (0.012, 0.024) | 57.0 / 60 | 571.4 |
| 5 | 10% | 0.53 | global | 57/2000 (0.022, 0.037) | 57.2 / 60 | 569.7 |
| 5 | 10% | 0.53 | decision_local | 57/2000 (0.022, 0.037) | 57.2 / 60 | 569.7 |
| 5 | 10% | 0.56 | global | 97/2000 (0.040, 0.059) | 56.9 / 60 | 572.1 |
| 5 | 10% | 0.56 | decision_local | 147/2000 (0.063, 0.086) | 56.9 / 60 | 572.1 |
| 5 | 20% | 0.50 | global | 27/2000 (0.009, 0.020) | 115.9 / 120 | 580.4 |
| 5 | 20% | 0.50 | decision_local | 44/2000 (0.016, 0.029) | 115.9 / 120 | 580.4 |
| 5 | 20% | 0.53 | global | 78/2000 (0.031, 0.048) | 116.2 / 120 | 579.5 |
| 5 | 20% | 0.53 | decision_local | 116/2000 (0.049, 0.069) | 116.2 / 120 | 579.5 |
| 5 | 20% | 0.56 | global | 209/2000 (0.092, 0.119) | 116.1 / 120 | 580.8 |
| 5 | 20% | 0.56 | decision_local | 278/2000 (0.125, 0.155) | 116.1 / 120 | 580.8 |
| 5 | 30% | 0.50 | global | 46/2000 (0.017, 0.031) | 175.5 / 180 | 585.3 |
| 5 | 30% | 0.50 | decision_local | 37/2000 (0.013, 0.025) | 175.5 / 180 | 585.3 |
| 5 | 30% | 0.53 | global | 124/2000 (0.052, 0.073) | 175.7 / 180 | 584.3 |
| 5 | 30% | 0.53 | decision_local | 163/2000 (0.070, 0.094) | 175.7 / 180 | 584.3 |
| 5 | 30% | 0.56 | global | 280/2000 (0.125, 0.156) | 175.6 / 180 | 585.0 |
| 5 | 30% | 0.56 | decision_local | 415/2000 (0.190, 0.226) | 175.6 / 180 | 585.0 |

The null rows (outcome probability 0.50) are the calibration check; alternatives are power diagnostics. Wilson intervals describe Monte Carlo uncertainty and do not replace the betting-process proof. Results are reported for every registered cell without selecting a best cost ratio or query cap.

Reproduce with `uv run python scripts/calibrate_decision_local_bounds.py --streams 2000 --horizon 600 --seed 26102026 --device cuda --output outputs/decision_local_bound_calibration`.

## Paired bound-mode contrasts

Each row compares both bound modes on the same generated streams. Intervals are paired t intervals over independent streams and are unadjusted across all 27 cells.

| High cost | Query cap | Outcome probability | Global crossings | Local crossings | Paired difference (95% CI) |
|---:|---:|---:|---:|---:|---:|
| 1 | 10% | 0.50 | 35/2000 | 35/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 10% | 0.53 | 65/2000 | 65/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 10% | 0.56 | 124/2000 | 124/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 20% | 0.50 | 33/2000 | 33/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 20% | 0.53 | 119/2000 | 119/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 20% | 0.56 | 263/2000 | 263/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 30% | 0.50 | 37/2000 | 37/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 30% | 0.53 | 120/2000 | 120/2000 | 0.0000 [0.0000, 0.0000] |
| 1 | 30% | 0.56 | 418/2000 | 418/2000 | 0.0000 [0.0000, 0.0000] |
| 2 | 10% | 0.50 | 22/2000 | 24/2000 | 0.0010 [-0.0036, 0.0056] |
| 2 | 10% | 0.53 | 62/2000 | 72/2000 | 0.0050 [-0.0010, 0.0110] |
| 2 | 10% | 0.56 | 111/2000 | 129/2000 | 0.0090 [0.0001, 0.0179] |
| 2 | 20% | 0.50 | 34/2000 | 44/2000 | 0.0050 [-0.0007, 0.0107] |
| 2 | 20% | 0.53 | 89/2000 | 103/2000 | 0.0070 [-0.0003, 0.0143] |
| 2 | 20% | 0.56 | 253/2000 | 279/2000 | 0.0130 [0.0020, 0.0240] |
| 2 | 30% | 0.50 | 36/2000 | 37/2000 | 0.0005 [-0.0046, 0.0056] |
| 2 | 30% | 0.53 | 125/2000 | 128/2000 | 0.0015 [-0.0068, 0.0098] |
| 2 | 30% | 0.56 | 384/2000 | 432/2000 | 0.0240 [0.0114, 0.0366] |
| 5 | 10% | 0.50 | 29/2000 | 34/2000 | 0.0025 [-0.0033, 0.0083] |
| 5 | 10% | 0.53 | 57/2000 | 57/2000 | 0.0000 [-0.0080, 0.0080] |
| 5 | 10% | 0.56 | 97/2000 | 147/2000 | 0.0250 [0.0141, 0.0359] |
| 5 | 20% | 0.50 | 27/2000 | 44/2000 | 0.0085 [0.0021, 0.0149] |
| 5 | 20% | 0.53 | 78/2000 | 116/2000 | 0.0190 [0.0090, 0.0290] |
| 5 | 20% | 0.56 | 209/2000 | 278/2000 | 0.0345 [0.0200, 0.0490] |
| 5 | 30% | 0.50 | 46/2000 | 37/2000 | -0.0045 [-0.0112, 0.0022] |
| 5 | 30% | 0.53 | 124/2000 | 163/2000 | 0.0195 [0.0076, 0.0314] |
| 5 | 30% | 0.56 | 280/2000 | 415/2000 | 0.0675 [0.0516, 0.0834] |

The pointwise-null rows assess type-I behavior under the stronger conditional null. Alternatives assess power; these exploratory intervals are descriptive and do not establish uniform superiority or account for selecting a favorable cell.
