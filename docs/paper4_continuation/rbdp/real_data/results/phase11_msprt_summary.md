# Phase 11 summary (PROTOCOL.md Addendum J): P8 mSPRT

## (1) Safety (exact worst-case adaptive risk)

settings: 528 (44 chains). Violation = risk_causal > alpha (1e-9 slack in the table; 1e-12 for the unit check).

| variant | violations at 1e-9 | violations at 1e-12 | max risk_causal / alpha | max risk_iid / alpha |
|---|---|---|---|---|
| P8 | 0 | 0 | 0.000000 | 0.000000 |
| P8c | 0 | 0 | 1.000000 | 1.000000 |

## (2) Panel cost versus P7 (RB-DP)

Delta = P8c cost - P7 cost; tie = |Delta| <= 1e-9 (absolute, as in tally_phase10_baselines.py); 'P7 cheaper' = Delta > 1e-9.

- P8c: P7 cheaper in 528, tied in 0, dearer in 0 of 528; max Delta 1.4467, min Delta 1.455e-02.
- P8: P7 cheaper in 528, tied in 0, dearer in 0 of 528; max Delta 2.3690, min Delta 3.971e-02.

Share of P7's value of information (C0 - cost) / (C0 - P7 cost), over settings with C0 - P7 cost > 1e-9:

| variant | n | median | q25 | q75 | min | max |
|---|---|---|---|---|---|---|
| P8c | 528 | 0.4509 | 0.1266 | 0.7109 | -0.9170 | 0.9671 |
| P8 | 528 | -0.1468 | -0.2876 | -0.0783 | -1.5641 | -0.0138 |

P8c: cheapest path member differs from the standard smallest-feasible-level calibration in 2 settings (max cost reduction 3.033e-04).

Per-chain (12 settings each): counts of P7 cheaper / tie / dearer vs P8c, median VOI share of P8c.

| chain | cheaper | tie | dearer | VOI P8c |
|---|---|---|---|---|
| A:atlas_v2/openml_ldpa | 12 | 0 | 0 | 0.575 |
| A:screen100/FOREX_audsgd-hour-Close | 12 | 0 | 0 | 0.203 |
| A:screen100/elec_MT_005 | 12 | 0 | 0 | 0.496 |
| A:screen100/elec_MT_010 | 12 | 0 | 0 | 0.541 |
| A:screen100/elec_MT_029 | 12 | 0 | 0 | 0.844 |
| A:screen100/pm_Shanghai | 12 | 0 | 0 | 0.889 |
| A:screen100/pm_Shenyang | 12 | 0 | 0 | 0.869 |
| A:screen100/tetouan_z1 | 12 | 0 | 0 | 0.933 |
| A:sprint_fresh/appliances | 12 | 0 | 0 | 0.877 |
| A:sprint_fresh/beijing_pm25 | 12 | 0 | 0 | 0.875 |
| B:covtype | 12 | 0 | 0 | 0.915 |
| Bext:electricity | 12 | 0 | 0 | 0.900 |
| D:geyser/Grand | 12 | 0 | 0 | -0.367 |
| D:geyser/Old_Faithful | 12 | 0 | 0 | -0.236 |
| E:lang/af | 12 | 0 | 0 | 0.542 |
| E:lang/br | 12 | 0 | 0 | 0.329 |
| E:lang/et/retry | 12 | 0 | 0 | 0.150 |
| E:lang/gl/retry | 12 | 0 | 0 | -0.024 |
| E:lang/ia/retry | 12 | 0 | 0 | 0.102 |
| F:faithful | 12 | 0 | 0 | 0.333 |
| F:geyser | 12 | 0 | 0 | -0.484 |
| L2:cy | 12 | 0 | 0 | 0.500 |
| L2:eo | 12 | 0 | 0 | 0.161 |
| L:ca | 12 | 0 | 0 | 0.136 |
| L:cs | 12 | 0 | 0 | 0.507 |
| L:hu | 12 | 0 | 0 | 0.270 |
| L:la | 12 | 0 | 0 | 0.174 |
| L:pl | 12 | 0 | 0 | 0.481 |
| L:ro | 12 | 0 | 0 | 0.509 |
| S2:P46804 | 12 | 0 | 0 | 0.257 |
| S3:P07916 | 12 | 0 | 0 | 0.617 |
| S3:P11547 | 12 | 0 | 0 | 0.662 |
| S:P04985 | 12 | 0 | 0 | 0.505 |
| S:P15502 | 12 | 0 | 0 | 0.718 |
| T:da | 12 | 0 | 0 | 0.520 |
| T:de | 12 | 0 | 0 | 0.559 |
| T:en | 12 | 0 | 0 | 0.496 |
| T:es | 12 | 0 | 0 | -0.025 |
| T:fi | 12 | 0 | 0 | -0.207 |
| T:fr | 12 | 0 | 0 | 0.307 |
| T:it | 12 | 0 | 0 | -0.039 |
| T:nl | 12 | 0 | 0 | 0.527 |
| T:pt | 12 | 0 | 0 | -0.531 |
| T:sv | 12 | 0 | 0 | 0.464 |

## (3) Replay (held-out windows; T = 32, B = 4, alpha = 0.1, c = 0.01, k = 0)

datasets: 100; windows: 9525

Pooled over windows (window bootstrap, 2000 resamples, seed 20261119). Difference is P7 - X (negative = P7 cheaper):

| policy | mean realised cost [95% CI] | P7 - X [95% CI] | promotion rate |
|---|---|---|---|
| P7 | 13.7991 [13.6602, 13.9312] | - | 0.289 |
| P8 | 18.0037 [17.8480, 18.1653] | -4.2046 [-4.3927, -4.0130] | 0.000 |
| P8c | 13.8379 [13.6982, 13.9738] | -0.0388 [-0.0973, 0.0196] | 0.280 |
| never | 17.9637 [17.8080, 18.1253] | -4.1646 [-4.3527, -3.9730] | 0.000 |

Datasets where P7's mean realised cost is below P8c: 60 of 100; tied (|diff| <= 1e-9): 0; P7 above P8c: 40.
Exact in-model causal risk / alpha of P8c over datasets: mean 0.959, max 1.000.

## (4) Does textbook P8 ever promote?

Maximum Lambda reachable (all B labels wins) = (2^(B+1) - 1)/(B+1): B=2: 2.3333, B=3: 3.7500, B=4: 6.2000; 1/alpha = 10 (alpha = 0.1) and 20 (alpha = 0.05).
Settings where max Lambda >= 1/alpha: 0 of 528. Settings with P8 causal risk > 0: 0.
P8 cost equals C0 + B*c (queries all B labels, never promotes) in 528 of 528 settings.
Replay (T = 32, B = 4, alpha = 0.1): textbook P8 exact cost mean over datasets 18.4315, max exact causal risk 0; realised promotion rate 0.000.
