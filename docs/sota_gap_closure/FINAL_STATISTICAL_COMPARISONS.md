# Final statistical comparisons (frozen protocol; paired cluster bootstrap, 4,000 resamples; worlds weighted equally)
Primary power comparisons are Holm-adjusted together (family size 10); false-alarm and harm-before-alarm rows are secondary. Harm worlds: 15; null worlds: 6. A - B > 0 favours A for power, favours B for false alarm and harm-before-alarm.

| A | B | metric | diff (A-B) | ci_lo | ci_hi | p_raw | p_holm(power family) | effect>=threshold |
|---|---|---|---|---|---|---|---|---|
| HG@0.1 | pprm@0.1 | power | 0.029 | 0.012 | 0.046 | 0.001 | 0.004 | 0.000 |
| HG@0.1 | pprm@0.1 | fa | -0.005 | -0.011 | -0.000 | 0.030 |  | 0.000 |
| HG@0.1 | pprm@0.1 | harm_before | -20.608 | -29.694 | -11.802 | 0.000 |  |  |
| HG@0.1 | ph@0.1 | power | -0.066 | -0.240 | 0.079 | 0.455 | 1.000 | 1.000 |
| HG@0.1 | ph@0.1 | fa | -0.008 | -0.015 | -0.001 | 0.011 |  | 0.000 |
| HG@0.1 | ph@0.1 | harm_before | -17.525 | -33.233 | -2.071 | 0.025 |  |  |
| HG@0.1 | cusum@0.1 | power | 0.018 | -0.161 | 0.163 | 0.783 | 1.000 | 0.000 |
| HG@0.1 | cusum@0.1 | fa | -0.014 | -0.021 | -0.007 | 0.000 |  | 0.000 |
| HG@0.1 | cusum@0.1 | harm_before | -14.962 | -30.598 | -0.376 | 0.043 |  |  |
| HG_robustmix@0.1 | HG@0.1 | power | 0.018 | 0.001 | 0.033 | 0.044 | 0.267 | 0.000 |
| HG_robustmix@0.1 | HG@0.1 | fa | -0.004 | -0.009 | -0.001 | 0.008 |  | 0.000 |
| HG_robustmix@0.1 | HG@0.1 | harm_before | -6.961 | -10.727 | -3.390 | 0.001 |  |  |
| HG_F2lrv100@0.1 | HG@0.1 | power | -0.061 | -0.079 | -0.044 | 0.000 | 0.003 | 1.000 |
| HG_F2lrv100@0.1 | HG@0.1 | fa | -0.006 | -0.010 | -0.002 | 0.000 |  | 0.000 |
| HG_F2lrv100@0.1 | HG@0.1 | harm_before | 28.075 | 16.812 | 38.971 | 0.000 |  |  |
| HG@0.2 | pprm@0.2 | power | 0.052 | 0.020 | 0.090 | 0.000 | 0.003 | 1.000 |
| HG@0.2 | pprm@0.2 | fa | -0.009 | -0.019 | 0.000 | 0.059 |  | 0.000 |
| HG@0.2 | pprm@0.2 | harm_before | -24.215 | -33.546 | -15.217 | 0.000 |  |  |
| HG@0.2 | ph@0.2 | power | -0.110 | -0.247 | 0.005 | 0.065 | 0.323 | 1.000 |
| HG@0.2 | ph@0.2 | fa | 0.002 | -0.009 | 0.016 | 0.745 |  | 0.000 |
| HG@0.2 | ph@0.2 | harm_before | -23.365 | -42.801 | -5.022 | 0.011 |  |  |
| HG@0.2 | cusum@0.2 | power | -0.039 | -0.190 | 0.086 | 0.599 | 1.000 | 1.000 |
| HG@0.2 | cusum@0.2 | fa | -0.005 | -0.014 | 0.007 | 0.352 |  | 0.000 |
| HG@0.2 | cusum@0.2 | harm_before | -24.505 | -44.725 | -4.878 | 0.013 |  |  |
| HG_robustmix@0.2 | HG@0.2 | power | -0.004 | -0.025 | 0.014 | 0.699 | 1.000 | 0.000 |
| HG_robustmix@0.2 | HG@0.2 | fa | -0.004 | -0.014 | 0.002 | 0.314 |  | 0.000 |
| HG_robustmix@0.2 | HG@0.2 | harm_before | -4.544 | -7.048 | -2.082 | 0.001 |  |  |
| HG_F2lrv100@0.2 | HG@0.2 | power | -0.045 | -0.081 | -0.014 | 0.003 | 0.018 | 1.000 |
| HG_F2lrv100@0.2 | HG@0.2 | fa | -0.013 | -0.026 | -0.004 | 0.000 |  | 0.000 |
| HG_F2lrv100@0.2 | HG@0.2 | harm_before | 35.320 | 22.326 | 48.215 | 0.000 |  |  |

Practical thresholds: power 0.03, false alarm 0.02. Intervals reflect world and seed variability of the synthetic pools only; they say nothing about real data.
