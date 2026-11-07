# H2 Round-5 post-development follow-up

## Synthetic 100-seed paired screen

ΔJ is H2 minus comparator; negative favors H2. Intervals are paired t intervals across simulator seeds.

| Regime | H2 J | Δ vs D2 [95% CI] | Δ vs A5b [95% CI] | H2 promotes | H2 labels |
|---|---:|---:|---:|---:|---:|
| F0_better | 361.2 | +7.6 [+4.0, +11.1] | -6.2 [-9.2, -3.3] | 0.860 | 128.0 |
| F0_null | 371.4 | +0.2 [-0.3, +0.6] | -0.1 [-0.2, +0.0] | 0.000 | 198.2 |
| F1_late_800 | 388.1 | -3.7 [-6.0, -1.4] | -11.8 [-15.5, -8.1] | 0.450 | 192.2 |
| F3_reversal_800 | 418.2 | +0.0 [-3.7, +3.7] | +0.6 [-3.9, +5.1] | 0.960 | 80.5 |
| F5_dep_better_r8 | 413.7 | +67.3 [+58.7, +76.0] | -4.4 [-9.4, +0.6] | 0.290 | 163.4 |
| F5_dep_null_r8 | 369.4 | +0.3 [-3.0, +3.6] | -1.0 [-1.4, -0.7] | 0.000 | 167.7 |
| F5_dep_null_r95 | 365.7 | -8.1 [-17.7, +1.5] | -0.6 [-0.8, -0.4] | 0.000 | 86.5 |
| F9_bursty_better | 367.3 | +11.9 [+7.3, +16.4] | -8.6 [-14.9, -2.3] | 0.770 | 146.8 |
| S_dep_better_r95 | 420.8 | +83.9 [+72.8, +95.1] | -1.8 [-3.8, +0.2] | 0.040 | 89.7 |

## Markov-null Monte Carlo screen

Wilson intervals are per fixed null regime; V2 scope is stationary first-order Markov only.

| Regime | Policy | Promotions / 1,000 | Rate [Wilson 95%] | Mean labels |
|---|---|---:|---:|---:|
| F0_null | A5b | 1/1000 | 0.001 [0.000, 0.006] | 200.0 |
| F0_null | D2 | 17/1000 | 0.017 [0.011, 0.027] | 196.6 |
| F0_null | H2 | 6/1000 | 0.006 [0.003, 0.013] | 198.1 |
| F0_null | H2-gateonly | 6/1000 | 0.006 [0.003, 0.013] | 198.5 |
| F0_null | H2-iid_space | 38/1000 | 0.038 [0.028, 0.052] | 192.8 |
| F5_dep_null_r8 | A5b | 2/1000 | 0.002 [0.001, 0.007] | 189.0 |
| F5_dep_null_r8 | D2 | 192/1000 | 0.192 [0.169, 0.218] | 174.7 |
| F5_dep_null_r8 | H2 | 7/1000 | 0.007 [0.003, 0.014] | 165.5 |
| F5_dep_null_r8 | H2-gateonly | 5/1000 | 0.005 [0.002, 0.012] | 198.2 |
| F5_dep_null_r8 | H2-iid_space | 182/1000 | 0.182 [0.159, 0.207] | 141.1 |
| F5_dep_null_r95 | A5b | 3/1000 | 0.003 [0.001, 0.009] | 96.9 |
| F5_dep_null_r95 | D2 | 660/1000 | 0.660 [0.630, 0.689] | 107.4 |
| F5_dep_null_r95 | H2 | 8/1000 | 0.008 [0.004, 0.016] | 84.0 |
| F5_dep_null_r95 | H2-gateonly | 9/1000 | 0.009 [0.005, 0.017] | 195.3 |
| F5_dep_null_r95 | H2-iid_space | 431/1000 | 0.431 [0.401, 0.462] | 58.5 |
| P_markov_null_r98 | A5b | 1/1000 | 0.001 [0.000, 0.006] | 77.2 |
| P_markov_null_r98 | D2 | 815/1000 | 0.815 [0.790, 0.838] | 80.1 |
| P_markov_null_r98 | H2 | 1/1000 | 0.001 [0.000, 0.006] | 62.9 |
| P_markov_null_r98 | H2-gateonly | 1/1000 | 0.001 [0.000, 0.006] | 193.5 |
| P_markov_null_r98 | H2-iid_space | 516/1000 | 0.516 [0.485, 0.547] | 42.4 |

## Real fixed-stream replay

Three paired policy seeds per episode; sources receive equal weight in the summary.

| Dataset | H2 J | D2 J | A5b J | Adaptive-range J | Never-switch J |
|---|---:|---:|---:|---:|---:|
| airlines | 781.9 | 781.2 | 784.0 | 781.1 | 776.8 |
| appliances | 769.9 | 575.1 | 831.4 | 574.8 | 821.8 |
| bank | 426.1 | 426.0 | 428.1 | 420.4 | 419.4 |
| beijing_pm25 | 651.4 | 547.5 | 656.8 | 598.9 | 664.6 |
| bike_hour | 342.7 | 254.4 | 344.8 | 265.6 | 552.8 |
| criteo | 697.0 | 696.6 | 699.4 | 699.1 | 693.9 |
| elec2 | 393.3 | 384.6 | 392.5 | 396.7 | 389.5 |
| household_power | 606.2 | 533.1 | 603.8 | 543.6 | 632.5 |
| metro | 180.0 | 120.1 | 221.4 | 126.2 | 719.9 |
| openml_ldpa | 562.4 | 444.8 | 540.8 | 461.1 | 663.0 |
| rialto | 180.7 | 84.2 | 186.0 | 90.9 | 202.1 |
| spam | 264.2 | 225.0 | 299.0 | 233.6 | 849.0 |
| uci_occupancy | 484.9 | 133.5 | 486.2 | 137.1 | 481.2 |
| weather | 461.3 | 459.2 | 466.0 | 468.8 | 504.0 |

Equal-dataset paired contrasts (H2 minus comparator), 14-source cluster bootstrap:

- vs D2: +81.2, 95% CI [+38.1, +136.1].
- vs A5b: -9.9, 95% CI [-21.5, -0.0].
- vs gated_adaptive_range+front: +71.7, 95% CI [+30.1, +126.4].
- vs CONTROL_never_switch: -112.0, 95% CI [-223.0, -23.9].

## Limitations

- Post-development, fixed simulator regimes and previously exposed sources; not independent confirmation.
- Real loss-stream results are descriptive and do not assign causal change labels.
- Wilson intervals quantify Monte Carlo uncertainty conditional on each fixed simulated regime.
