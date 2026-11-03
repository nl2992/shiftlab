# Failure Atlas v2 synthetic discovery tables

Source: `outputs/failure_atlas_v2/discovery_synth/records.jsonl` (all policies except DISCERN) and
`discovery_synth_fix/records.jsonl` (DISCERN after the PrPl-EB fidelity fix, plus the ported Gong-Zhang, Qiu
and Ryabchenko adaptations), 100 paired streams per regime, seed base 2026110301, v2 contract.
`regE` = net cost minus the cost of the expected-cost-optimal path computed from the true G_t (evaluator-only,
not a feasible policy). `regH` = net minus the hindsight DP optimum on realised losses (a lower bound no policy can reach).
Families: C = methods with an anytime false-promotion guarantee; U = no such guarantee.

## F0_better

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| model_selector_causal | U2 pool active selection | 326.5 ± 1.9 | 1.00 | 1.84 | 200 | 108 | 22.5 | 23.7 |
| economic_replacement | control | 329.0 ± 1.7 | 1.00 | 1.00 | 200 | 248 | 25.0 | 26.2 |
| model_picker_adapter | U1 online-Bayes | 329.2 ± 2.7 | 1.00 | 2.86 | 80 | 112 | 25.2 | 26.5 |
| qiu_delayed_movement | U7 dyn-regret OCO | 329.4 ± 2.1 | 1.00 | 1.38 | 200 | 202 | 25.4 | 26.7 |
| variance_min_ipw | U5 active risk est. | 330.5 ± 2.1 | 1.00 | 2.40 | 194 | 114 | 26.5 | 27.8 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 330.9 ± 2.3 | 1.00 | 2.38 | 200 | 132 | 27.0 | 28.2 |
| cams_adapter | U4 expert advice | 331.0 ± 2.2 | 1.00 | 2.52 | 190 | 110 | 27.0 | 28.3 |
| online_llm_picker | U3 bandit selection | 333.9 ± 3.1 | 1.00 | 3.78 | 81 | 107 | 30.0 | 31.2 |
| ryabchenko_capacity | U8 capacity sched. | 353.3 ± 5.2 | 0.82 | 1.31 | 129 | 0 | 49.4 | 50.6 |
| SMCS+retain-incumbent | C3 e-elimination | 377.9 ± 4.1 | 0.76 | 0.76 | 200 | 664 | 74.0 | 75.2 |
| xu_acquisition_only | C4 active-testing betting | 378.4 ± 3.2 | 0.92 | 0.92 | 195 | 890 | 74.5 | 75.7 |
| P7s_settled | C5 ours-prior (B3+) | 385.2 ± 3.4 | 0.75 | 0.75 | 161 | 993 | 81.3 | 82.5 |
| CONTROL_never_switch | control | 418.9 ± 1.9 | 0.00 | 0.00 | 0 | nan | 114.9 | 116.2 |
| gated_deployment | C1 anytime-CS | 426.0 ± 2.3 | 0.06 | 0.06 | 195 | 1252 | 122.1 | 123.3 |
| discern_style | C2 DISCERN CS | 428.9 ± 1.9 | 0.00 | 0.00 | 200 | nan | 124.9 | 126.1 |

## F0_null

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| CONTROL_never_switch | control | 359.6 ± 1.8 | 0.00 | 0.00 | 0 | nan | 0.0 | 16.9 |
| xu_acquisition_only | C4 active-testing betting | 369.4 ± 1.8 | 0.00 | 0.00 | 195 | nan | 9.8 | 26.7 |
| SMCS+retain-incumbent | C3 e-elimination | 369.5 ± 1.8 | 0.01 | 0.01 | 200 | 302 | 9.9 | 26.8 |
| P7s_settled | C5 ours-prior (B3+) | 369.6 ± 1.8 | 0.00 | 0.00 | 199 | nan | 9.9 | 26.8 |
| discern_style | C2 DISCERN CS | 369.6 ± 1.8 | 0.00 | 0.00 | 200 | nan | 10.0 | 26.9 |
| gated_deployment | C1 anytime-CS | 369.6 ± 1.8 | 0.00 | 0.00 | 200 | nan | 10.0 | 26.9 |
| ryabchenko_capacity | U8 capacity sched. | 375.6 ± 2.6 | 0.64 | 1.71 | 128 | 0 | 15.9 | 32.8 |
| economic_replacement | control | 375.6 ± 1.9 | 0.83 | 0.83 | 200 | 268 | 16.0 | 32.9 |
| qiu_delayed_movement | U7 dyn-regret OCO | 392.3 ± 2.2 | 0.99 | 4.51 | 200 | 202 | 32.6 | 49.5 |
| model_selector_causal | U2 pool active selection | 397.9 ± 2.9 | 0.95 | 5.53 | 200 | 122 | 38.3 | 55.2 |
| model_picker_adapter | U1 online-Bayes | 400.4 ± 3.4 | 0.96 | 7.00 | 96 | 130 | 40.8 | 57.7 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 403.8 ± 2.4 | 1.00 | 6.65 | 200 | 146 | 44.2 | 61.1 |
| online_llm_picker | U3 bandit selection | 412.9 ± 3.9 | 0.98 | 9.37 | 96 | 112 | 53.3 | 70.2 |
| variance_min_ipw | U5 active risk est. | 423.5 ± 5.0 | 0.95 | 10.62 | 196 | 123 | 63.9 | 80.8 |
| cams_adapter | U4 expert advice | 424.0 ± 5.1 | 0.96 | 10.67 | 194 | 109 | 64.3 | 81.2 |

## F0_worse

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| CONTROL_never_switch | control | 297.9 ± 1.5 | 0.00 | 0.00 | 0 | nan | 0.0 | 0.2 |
| P7s_settled | C5 ours-prior (B3+) | 307.2 ± 1.6 | 0.00 | 0.00 | 186 | nan | 9.3 | 9.5 |
| xu_acquisition_only | C4 active-testing betting | 307.7 ± 1.5 | 0.00 | 0.00 | 196 | nan | 9.8 | 10.0 |
| gated_deployment | C1 anytime-CS | 307.8 ± 1.5 | 0.00 | 0.00 | 198 | nan | 9.9 | 10.1 |
| discern_style | C2 DISCERN CS | 307.9 ± 1.5 | 0.00 | 0.00 | 200 | nan | 10.0 | 10.2 |
| SMCS+retain-incumbent | C3 e-elimination | 307.9 ± 1.5 | 0.00 | 0.00 | 200 | nan | 10.0 | 10.2 |
| qiu_delayed_movement | U7 dyn-regret OCO | 315.9 ± 1.9 | 0.38 | 0.82 | 200 | 202 | 18.0 | 18.3 |
| model_selector_causal | U2 pool active selection | 316.3 ± 1.9 | 0.45 | 1.18 | 200 | 120 | 18.4 | 18.6 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 320.3 ± 2.1 | 0.55 | 1.92 | 200 | 139 | 22.4 | 22.7 |
| cams_adapter | U4 expert advice | 321.0 ± 2.1 | 0.60 | 2.14 | 188 | 110 | 23.1 | 23.3 |
| variance_min_ipw | U5 active risk est. | 322.2 ± 2.2 | 0.61 | 2.36 | 194 | 118 | 24.3 | 24.5 |
| model_picker_adapter | U1 online-Bayes | 324.2 ± 2.9 | 0.66 | 2.96 | 78 | 128 | 26.3 | 26.5 |
| online_llm_picker | U3 bandit selection | 325.2 ± 3.0 | 0.72 | 3.36 | 79 | 116 | 27.3 | 27.6 |
| economic_replacement | control | 327.7 ± 4.5 | 0.19 | 0.19 | 200 | 256 | 29.8 | 30.0 |
| ryabchenko_capacity | U8 capacity sched. | 349.9 ± 5.3 | 0.53 | 2.04 | 129 | 0 | 52.0 | 52.2 |

## F1_late_1200

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| qiu_delayed_movement | U7 dyn-regret OCO | 347.9 ± 2.2 | 1.00 | 2.32 | 200 | 1162 | 49.2 | 51.4 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 358.0 ± 2.9 | 0.99 | 4.26 | 200 | 171 | 59.3 | 61.5 |
| P7s_settled | C5 ours-prior (B3+) | 369.1 ± 2.0 | 0.77 | 0.77 | 192 | 1766 | 70.4 | 72.6 |
| economic_replacement | control | 369.6 ± 2.1 | 0.36 | 0.36 | 200 | 262 | 71.0 | 73.2 |
| ryabchenko_capacity | U8 capacity sched. | 370.4 ± 2.1 | 0.59 | 1.28 | 127 | 0 | 71.7 | 73.9 |
| CONTROL_never_switch | control | 373.1 ± 1.6 | 0.00 | 0.00 | 0 | nan | 74.4 | 76.6 |
| model_selector_causal | U2 pool active selection | 382.2 ± 2.1 | 0.93 | 3.31 | 200 | 131 | 83.5 | 85.7 |
| xu_acquisition_only | C4 active-testing betting | 382.5 ± 1.6 | 0.11 | 0.11 | 195 | 1946 | 83.8 | 86.0 |
| SMCS+retain-incumbent | C3 e-elimination | 383.1 ± 1.6 | 0.00 | 0.00 | 200 | nan | 84.4 | 86.6 |
| discern_style | C2 DISCERN CS | 383.1 ± 1.6 | 0.00 | 0.00 | 200 | nan | 84.4 | 86.6 |
| gated_deployment | C1 anytime-CS | 383.1 ± 1.6 | 0.00 | 0.00 | 200 | nan | 84.4 | 86.6 |
| online_llm_picker | U3 bandit selection | 384.4 ± 3.6 | 0.89 | 5.54 | 86 | 119 | 85.7 | 87.9 |
| model_picker_adapter | U1 online-Bayes | 385.0 ± 2.9 | 0.91 | 4.52 | 90 | 131 | 86.3 | 88.5 |
| cams_adapter | U4 expert advice | 387.8 ± 2.8 | 0.95 | 5.43 | 193 | 121 | 89.1 | 91.3 |
| variance_min_ipw | U5 active risk est. | 391.7 ± 2.7 | 0.92 | 5.25 | 194 | 120 | 93.0 | 95.2 |

## F1_late_400

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| economic_replacement | control | 335.3 ± 2.4 | 0.99 | 0.99 | 200 | 654 | 33.8 | 36.4 |
| qiu_delayed_movement | U7 dyn-regret OCO | 338.5 ± 2.0 | 1.00 | 2.15 | 200 | 556 | 37.0 | 39.6 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 347.1 ± 2.3 | 1.00 | 4.10 | 200 | 194 | 45.6 | 48.2 |
| model_selector_causal | U2 pool active selection | 349.6 ± 2.4 | 1.00 | 3.18 | 200 | 176 | 48.1 | 50.7 |
| model_picker_adapter | U1 online-Bayes | 355.5 ± 3.8 | 1.00 | 4.64 | 88 | 162 | 54.0 | 56.6 |
| ryabchenko_capacity | U8 capacity sched. | 361.6 ± 4.4 | 0.79 | 1.70 | 128 | 0 | 60.1 | 62.7 |
| online_llm_picker | U3 bandit selection | 363.0 ± 3.4 | 1.00 | 6.17 | 85 | 136 | 61.5 | 64.1 |
| variance_min_ipw | U5 active risk est. | 363.4 ± 3.3 | 1.00 | 5.94 | 195 | 140 | 61.9 | 64.5 |
| cams_adapter | U4 expert advice | 365.8 ± 3.4 | 1.00 | 6.28 | 191 | 123 | 64.3 | 66.9 |
| P7s_settled | C5 ours-prior (B3+) | 373.7 ± 2.9 | 0.88 | 0.88 | 168 | 1201 | 72.2 | 74.8 |
| xu_acquisition_only | C4 active-testing betting | 391.2 ± 2.4 | 0.78 | 0.78 | 196 | 1446 | 89.7 | 92.3 |
| CONTROL_never_switch | control | 407.6 ± 1.9 | 0.00 | 0.00 | 0 | nan | 106.2 | 108.8 |
| SMCS+retain-incumbent | C3 e-elimination | 409.3 ± 2.3 | 0.27 | 0.27 | 200 | 1509 | 107.8 | 110.4 |
| discern_style | C2 DISCERN CS | 417.6 ± 1.9 | 0.00 | 0.00 | 200 | nan | 116.1 | 118.7 |
| gated_deployment | C1 anytime-CS | 417.6 ± 1.9 | 0.00 | 0.00 | 200 | nan | 116.1 | 118.7 |

## F1_late_800

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| qiu_delayed_movement | U7 dyn-regret OCO | 339.7 ± 2.0 | 1.00 | 2.02 | 200 | 1010 | 42.8 | 45.4 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 346.7 ± 2.4 | 1.00 | 4.12 | 200 | 176 | 49.8 | 52.4 |
| economic_replacement | control | 356.3 ± 2.8 | 0.73 | 0.73 | 200 | 1128 | 59.4 | 62.0 |
| model_picker_adapter | U1 online-Bayes | 364.6 ± 2.9 | 0.98 | 4.69 | 91 | 156 | 67.7 | 70.3 |
| ryabchenko_capacity | U8 capacity sched. | 366.6 ± 3.5 | 0.74 | 1.92 | 129 | 0 | 69.7 | 72.3 |
| model_selector_causal | U2 pool active selection | 366.8 ± 2.3 | 0.99 | 3.49 | 200 | 146 | 70.0 | 72.6 |
| P7s_settled | C5 ours-prior (B3+) | 371.0 ± 2.3 | 0.78 | 0.78 | 181 | 1520 | 74.1 | 76.7 |
| online_llm_picker | U3 bandit selection | 374.7 ± 3.5 | 0.94 | 5.71 | 85 | 115 | 77.9 | 80.5 |
| cams_adapter | U4 expert advice | 376.5 ± 2.8 | 1.00 | 5.68 | 192 | 138 | 79.6 | 82.2 |
| variance_min_ipw | U5 active risk est. | 380.1 ± 3.2 | 0.98 | 6.17 | 194 | 154 | 83.3 | 85.9 |
| CONTROL_never_switch | control | 387.9 ± 1.8 | 0.00 | 0.00 | 0 | nan | 91.1 | 93.7 |
| xu_acquisition_only | C4 active-testing betting | 390.1 ± 1.7 | 0.50 | 0.50 | 197 | 1728 | 93.2 | 95.8 |
| SMCS+retain-incumbent | C3 e-elimination | 397.9 ± 1.8 | 0.01 | 0.01 | 200 | 1920 | 101.0 | 103.6 |
| gated_deployment | C1 anytime-CS | 397.9 ± 1.8 | 0.00 | 0.00 | 200 | nan | 101.1 | 103.7 |
| discern_style | C2 DISCERN CS | 397.9 ± 1.8 | 0.00 | 0.00 | 200 | nan | 101.1 | 103.7 |

## F2_transient

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| qiu_delayed_movement | U7 dyn-regret OCO | 367.0 ± 2.0 | 1.00 | 2.77 | 200 | 505 | 57.9 | 62.9 |
| economic_replacement | control | 369.3 ± 2.1 | 1.00 | 1.00 | 200 | 504 | 60.2 | 65.2 |
| CONTROL_never_switch | control | 370.9 ± 1.7 | 0.00 | 0.00 | 0 | nan | 61.8 | 66.7 |
| ryabchenko_capacity | U8 capacity sched. | 375.7 ± 2.8 | 0.75 | 1.58 | 129 | 0 | 66.6 | 71.6 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 376.1 ± 2.3 | 1.00 | 4.45 | 200 | 186 | 67.1 | 72.0 |
| discern_style | C2 DISCERN CS | 380.8 ± 1.7 | 0.00 | 0.00 | 200 | nan | 71.8 | 76.7 |
| gated_deployment | C1 anytime-CS | 380.8 ± 1.7 | 0.00 | 0.00 | 200 | nan | 71.8 | 76.7 |
| model_selector_causal | U2 pool active selection | 382.8 ± 2.4 | 1.00 | 3.19 | 200 | 154 | 73.7 | 78.7 |
| model_picker_adapter | U1 online-Bayes | 384.4 ± 3.2 | 1.00 | 4.73 | 89 | 147 | 75.4 | 80.3 |
| online_llm_picker | U3 bandit selection | 387.9 ± 2.9 | 0.99 | 6.25 | 88 | 133 | 78.9 | 83.8 |
| cams_adapter | U4 expert advice | 390.8 ± 2.7 | 1.00 | 5.21 | 190 | 140 | 81.7 | 86.7 |
| SMCS+retain-incumbent | C3 e-elimination | 390.9 ± 2.3 | 0.43 | 0.43 | 200 | 1019 | 81.8 | 86.8 |
| P7s_settled | C5 ours-prior (B3+) | 395.2 ± 2.3 | 0.85 | 0.95 | 183 | 871 | 86.1 | 91.1 |
| variance_min_ipw | U5 active risk est. | 397.2 ± 3.2 | 1.00 | 5.84 | 196 | 120 | 88.1 | 93.0 |
| xu_acquisition_only | C4 active-testing betting | 399.0 ± 2.5 | 0.66 | 0.71 | 197 | 1016 | 89.9 | 94.8 |

## F3_reversal_1200

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| qiu_delayed_movement | U7 dyn-regret OCO | 351.9 ± 1.9 | 1.00 | 2.18 | 200 | 202 | 62.1 | 64.1 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 352.1 ± 2.2 | 1.00 | 2.75 | 200 | 132 | 62.3 | 64.3 |
| online_llm_picker | U3 bandit selection | 365.9 ± 2.4 | 1.00 | 3.24 | 81 | 104 | 76.1 | 78.2 |
| model_picker_adapter | U1 online-Bayes | 367.8 ± 2.4 | 1.00 | 2.28 | 77 | 116 | 78.0 | 80.1 |
| model_selector_causal | U2 pool active selection | 369.6 ± 1.9 | 1.00 | 1.37 | 200 | 104 | 79.8 | 81.9 |
| cams_adapter | U4 expert advice | 372.2 ± 2.4 | 1.00 | 1.96 | 187 | 111 | 82.4 | 84.5 |
| ryabchenko_capacity | U8 capacity sched. | 372.6 ± 3.0 | 0.76 | 1.53 | 129 | 0 | 82.8 | 84.8 |
| CONTROL_never_switch | control | 376.1 ± 1.8 | 0.00 | 0.00 | 0 | nan | 86.3 | 88.3 |
| variance_min_ipw | U5 active risk est. | 378.1 ± 2.7 | 1.00 | 2.85 | 194 | 114 | 88.3 | 90.4 |
| economic_replacement | control | 379.0 ± 1.9 | 1.00 | 1.00 | 200 | 243 | 89.2 | 91.2 |
| discern_style | C2 DISCERN CS | 386.1 ± 1.8 | 0.00 | 0.00 | 200 | nan | 96.3 | 98.3 |
| gated_deployment | C1 anytime-CS | 390.7 ± 2.2 | 0.14 | 0.14 | 186 | 962 | 100.9 | 103.0 |
| SMCS+retain-incumbent | C3 e-elimination | 396.7 ± 2.9 | 0.90 | 0.90 | 200 | 434 | 106.9 | 108.9 |
| P7s_settled | C5 ours-prior (B3+) | 404.6 ± 2.5 | 0.89 | 1.18 | 189 | 578 | 114.8 | 116.8 |
| xu_acquisition_only | C4 active-testing betting | 410.0 ± 2.7 | 0.95 | 1.03 | 196 | 614 | 120.2 | 122.2 |

## F3_reversal_800

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| CONTROL_never_switch | control | 344.4 ± 1.8 | 0.00 | 0.00 | 0 | nan | 53.0 | 55.1 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 349.1 ± 2.3 | 1.00 | 2.97 | 200 | 136 | 57.8 | 59.9 |
| qiu_delayed_movement | U7 dyn-regret OCO | 350.4 ± 2.0 | 1.00 | 2.24 | 200 | 202 | 59.1 | 61.1 |
| discern_style | C2 DISCERN CS | 354.3 ± 1.8 | 0.00 | 0.00 | 200 | nan | 63.0 | 65.1 |
| gated_deployment | C1 anytime-CS | 360.6 ± 2.8 | 0.08 | 0.08 | 190 | 766 | 69.3 | 71.3 |
| ryabchenko_capacity | U8 capacity sched. | 378.0 ± 2.7 | 0.75 | 1.68 | 128 | 0 | 86.6 | 88.7 |
| online_llm_picker | U3 bandit selection | 378.0 ± 3.4 | 1.00 | 3.39 | 85 | 106 | 86.7 | 88.8 |
| model_picker_adapter | U1 online-Bayes | 384.6 ± 2.7 | 1.00 | 3.89 | 86 | 116 | 93.3 | 95.3 |
| model_selector_causal | U2 pool active selection | 385.5 ± 2.2 | 1.00 | 2.67 | 200 | 106 | 94.2 | 96.3 |
| cams_adapter | U4 expert advice | 389.4 ± 2.6 | 1.00 | 3.67 | 192 | 108 | 98.1 | 100.1 |
| variance_min_ipw | U5 active risk est. | 390.9 ± 2.6 | 1.00 | 3.66 | 193 | 114 | 99.6 | 101.7 |
| P7s_settled | C5 ours-prior (B3+) | 396.3 ± 3.8 | 0.70 | 1.25 | 194 | 547 | 105.0 | 107.1 |
| xu_acquisition_only | C4 active-testing betting | 402.4 ± 3.7 | 0.76 | 1.25 | 195 | 545 | 111.1 | 113.2 |
| SMCS+retain-incumbent | C3 e-elimination | 409.9 ± 3.7 | 0.81 | 0.81 | 200 | 397 | 118.6 | 120.7 |
| economic_replacement | control | 411.6 ± 1.8 | 1.00 | 1.00 | 200 | 250 | 120.2 | 122.3 |

## F4_recurrent

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| CONTROL_never_switch | control | 366.8 ± 1.9 | 0.00 | 0.00 | 0 | nan | 62.2 | 67.0 |
| discern_style | C2 DISCERN CS | 376.8 ± 1.9 | 0.00 | 0.00 | 200 | nan | 72.2 | 77.0 |
| gated_deployment | C1 anytime-CS | 377.3 ± 2.0 | 0.01 | 0.01 | 198 | 472 | 72.7 | 77.5 |
| ryabchenko_capacity | U8 capacity sched. | 380.7 ± 3.2 | 0.70 | 1.78 | 129 | 0 | 76.1 | 80.9 |
| SMCS+retain-incumbent | C3 e-elimination | 391.5 ± 2.0 | 0.67 | 0.67 | 200 | 337 | 86.9 | 91.7 |
| economic_replacement | control | 392.7 ± 1.6 | 1.00 | 1.00 | 200 | 252 | 88.1 | 92.9 |
| xu_acquisition_only | C4 active-testing betting | 393.1 ± 2.9 | 0.47 | 0.64 | 195 | 466 | 88.4 | 93.3 |
| online_llm_picker | U3 bandit selection | 394.3 ± 2.8 | 1.00 | 4.59 | 88 | 105 | 89.6 | 94.5 |
| model_selector_causal | U2 pool active selection | 395.2 ± 2.6 | 1.00 | 2.90 | 200 | 105 | 90.6 | 95.4 |
| model_picker_adapter | U1 online-Bayes | 398.7 ± 3.2 | 1.00 | 4.83 | 88 | 114 | 94.0 | 98.9 |
| P7s_settled | C5 ours-prior (B3+) | 399.2 ± 2.7 | 0.68 | 0.83 | 188 | 524 | 94.6 | 99.4 |
| cams_adapter | U4 expert advice | 402.9 ± 3.2 | 1.00 | 4.41 | 194 | 106 | 98.2 | 103.1 |
| qiu_delayed_movement | U7 dyn-regret OCO | 405.8 ± 2.1 | 1.00 | 3.83 | 200 | 202 | 101.2 | 106.0 |
| variance_min_ipw | U5 active risk est. | 408.7 ± 3.7 | 1.00 | 5.59 | 194 | 114 | 104.1 | 109.0 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 409.2 ± 2.3 | 1.00 | 4.12 | 200 | 132 | 104.6 | 109.4 |

## F5_dep_better_r8

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| model_selector_causal | U2 pool active selection | 332.9 ± 2.7 | 1.00 | 2.12 | 200 | 108 | 26.9 | 36.3 |
| economic_replacement | control | 333.8 ± 2.1 | 1.00 | 1.00 | 200 | 260 | 27.8 | 37.3 |
| model_picker_adapter | U1 online-Bayes | 336.4 ± 3.3 | 1.00 | 3.00 | 77 | 117 | 30.4 | 39.8 |
| cams_adapter | U4 expert advice | 337.0 ± 3.4 | 1.00 | 2.96 | 186 | 109 | 31.0 | 40.4 |
| variance_min_ipw | U5 active risk est. | 339.1 ± 3.2 | 1.00 | 3.20 | 195 | 116 | 33.1 | 42.5 |
| qiu_delayed_movement | U7 dyn-regret OCO | 339.3 ± 3.2 | 1.00 | 1.92 | 200 | 202 | 33.3 | 42.7 |
| online_llm_picker | U3 bandit selection | 341.8 ± 3.8 | 1.00 | 3.93 | 79 | 107 | 35.9 | 45.3 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 341.9 ± 3.3 | 1.00 | 3.10 | 200 | 137 | 35.9 | 45.3 |
| ryabchenko_capacity | U8 capacity sched. | 347.7 ± 4.8 | 0.86 | 1.42 | 128 | 0 | 41.8 | 51.2 |
| SMCS+retain-incumbent | C3 e-elimination | 364.0 ± 4.0 | 0.82 | 0.82 | 200 | 398 | 58.1 | 67.5 |
| P7s_settled | C5 ours-prior (B3+) | 374.7 ± 3.6 | 0.76 | 0.76 | 153 | 630 | 68.7 | 78.1 |
| xu_acquisition_only | C4 active-testing betting | 376.7 ± 3.0 | 0.83 | 0.83 | 196 | 723 | 70.7 | 80.1 |
| CONTROL_never_switch | control | 417.9 ± 2.5 | 0.00 | 0.00 | 0 | nan | 111.9 | 121.3 |
| gated_deployment | C1 anytime-CS | 423.3 ± 2.7 | 0.15 | 0.15 | 191 | 1453 | 117.3 | 126.7 |
| discern_style | C2 DISCERN CS | 427.9 ± 2.5 | 0.00 | 0.00 | 200 | nan | 121.9 | 131.3 |

## F5_dep_null_r8

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| CONTROL_never_switch | control | 363.7 ± 2.1 | 0.00 | 0.00 | 0 | nan | 0.0 | 44.4 |
| economic_replacement | control | 372.8 ± 2.1 | 0.87 | 0.87 | 200 | 285 | 9.1 | 53.5 |
| gated_deployment | C1 anytime-CS | 373.6 ± 2.2 | 0.00 | 0.00 | 198 | nan | 9.9 | 54.3 |
| xu_acquisition_only | C4 active-testing betting | 373.6 ± 2.1 | 0.05 | 0.05 | 196 | 863 | 9.9 | 54.3 |
| discern_style | C2 DISCERN CS | 373.7 ± 2.1 | 0.00 | 0.00 | 200 | nan | 10.0 | 54.3 |
| SMCS+retain-incumbent | C3 e-elimination | 373.9 ± 2.1 | 0.08 | 0.08 | 200 | 360 | 10.3 | 54.6 |
| P7s_settled | C5 ours-prior (B3+) | 374.6 ± 2.1 | 0.12 | 0.12 | 196 | 780 | 10.9 | 55.3 |
| ryabchenko_capacity | U8 capacity sched. | 375.3 ± 3.0 | 0.69 | 1.86 | 128 | 0 | 11.6 | 55.9 |
| qiu_delayed_movement | U7 dyn-regret OCO | 392.2 ± 2.6 | 0.98 | 4.41 | 200 | 202 | 28.5 | 72.9 |
| model_picker_adapter | U1 online-Bayes | 393.0 ± 3.4 | 0.96 | 5.97 | 92 | 124 | 29.3 | 73.6 |
| model_selector_causal | U2 pool active selection | 400.6 ± 3.3 | 0.93 | 5.71 | 200 | 108 | 36.9 | 81.3 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 403.0 ± 2.9 | 1.00 | 6.58 | 200 | 147 | 39.3 | 83.7 |
| online_llm_picker | U3 bandit selection | 403.4 ± 3.6 | 0.96 | 7.42 | 92 | 108 | 39.7 | 84.1 |
| variance_min_ipw | U5 active risk est. | 409.8 ± 4.1 | 0.93 | 7.93 | 195 | 125 | 46.2 | 90.5 |
| cams_adapter | U4 expert advice | 412.7 ± 4.0 | 0.95 | 8.42 | 194 | 120 | 49.1 | 93.4 |

## F5_dep_null_r95

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| CONTROL_never_switch | control | 356.9 ± 3.3 | 0.00 | 0.00 | 0 | nan | 0.0 | 91.0 |
| P7s_settled | C5 ours-prior (B3+) | 366.0 ± 3.3 | 0.31 | 0.36 | 186 | 719 | 9.1 | 100.2 |
| discern_style | C2 DISCERN CS | 366.9 ± 3.3 | 0.00 | 0.00 | 200 | nan | 10.0 | 101.0 |
| gated_deployment | C1 anytime-CS | 367.1 ± 3.4 | 0.02 | 0.02 | 196 | 805 | 10.2 | 101.3 |
| SMCS+retain-incumbent | C3 e-elimination | 368.5 ± 3.5 | 0.34 | 0.34 | 200 | 418 | 11.6 | 102.7 |
| ryabchenko_capacity | U8 capacity sched. | 369.6 ± 3.7 | 0.65 | 1.56 | 130 | 0 | 12.7 | 103.8 |
| xu_acquisition_only | C4 active-testing betting | 370.0 ± 3.6 | 0.24 | 0.29 | 196 | 522 | 13.1 | 104.1 |
| economic_replacement | control | 375.2 ± 3.2 | 0.81 | 0.81 | 200 | 288 | 18.4 | 109.4 |
| online_llm_picker | U3 bandit selection | 384.0 ± 3.8 | 0.98 | 4.48 | 83 | 110 | 27.1 | 118.2 |
| model_picker_adapter | U1 online-Bayes | 384.4 ± 4.4 | 0.90 | 4.52 | 87 | 128 | 27.5 | 118.5 |
| variance_min_ipw | U5 active risk est. | 387.8 ± 4.0 | 0.94 | 4.45 | 194 | 122 | 31.0 | 122.0 |
| qiu_delayed_movement | U7 dyn-regret OCO | 387.9 ± 3.5 | 0.99 | 4.30 | 200 | 202 | 31.1 | 122.1 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 391.2 ± 4.0 | 0.99 | 5.43 | 200 | 147 | 34.3 | 125.3 |
| model_selector_causal | U2 pool active selection | 391.3 ± 4.1 | 0.96 | 4.56 | 200 | 110 | 34.4 | 125.5 |
| cams_adapter | U4 expert advice | 392.8 ± 4.4 | 0.92 | 5.11 | 191 | 116 | 35.9 | 127.0 |

## F6_delay400_better

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| online_llm_picker | U3 bandit selection | 343.3 ± 2.2 | 1.00 | 2.39 | 126 | 406 | 39.8 | 40.9 |
| model_selector_causal | U2 pool active selection | 343.6 ± 1.7 | 1.00 | 1.68 | 200 | 406 | 40.2 | 41.3 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 345.1 ± 1.8 | 1.00 | 1.70 | 200 | 438 | 41.6 | 42.7 |
| economic_replacement | control | 347.0 ± 1.7 | 1.00 | 1.00 | 200 | 556 | 43.6 | 44.7 |
| cams_adapter | U4 expert advice | 347.6 ± 2.1 | 1.00 | 2.48 | 190 | 406 | 44.2 | 45.3 |
| model_picker_adapter | U1 online-Bayes | 348.6 ± 3.0 | 1.00 | 2.75 | 86 | 424 | 45.2 | 46.3 |
| variance_min_ipw | U5 active risk est. | 349.3 ± 2.2 | 1.00 | 2.80 | 195 | 416 | 45.9 | 47.0 |
| qiu_delayed_movement | U7 dyn-regret OCO | 359.9 ± 2.0 | 1.00 | 1.02 | 200 | 802 | 56.4 | 57.5 |
| ryabchenko_capacity | U8 capacity sched. | 362.0 ± 5.6 | 0.70 | 1.32 | 128 | 0 | 58.6 | 59.7 |
| SMCS+retain-incumbent | C3 e-elimination | 387.9 ± 3.1 | 0.74 | 0.74 | 200 | 902 | 84.5 | 85.6 |
| xu_acquisition_only | C4 active-testing betting | 405.1 ± 2.5 | 0.71 | 0.71 | 196 | 1371 | 101.6 | 102.7 |
| P7s_settled | C5 ours-prior (B3+) | 409.7 ± 2.1 | 0.65 | 0.65 | 192 | 1409 | 106.3 | 107.4 |
| CONTROL_never_switch | control | 417.6 ± 2.0 | 0.00 | 0.00 | 0 | nan | 114.1 | 115.2 |
| gated_deployment | C1 anytime-CS | 425.6 ± 2.2 | 0.06 | 0.06 | 196 | 1384 | 122.2 | 123.3 |
| discern_style | C2 DISCERN CS | 427.6 ± 2.0 | 0.00 | 0.00 | 200 | nan | 124.1 | 125.2 |

## F6_delay400_late

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| economic_replacement | control | 368.8 ± 4.0 | 0.50 | 0.50 | 200 | 663 | 66.7 | 69.3 |
| ryabchenko_capacity | U8 capacity sched. | 374.8 ± 3.4 | 0.53 | 1.02 | 129 | 0 | 72.7 | 75.3 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 375.1 ± 2.4 | 0.95 | 2.96 | 200 | 461 | 73.1 | 75.6 |
| qiu_delayed_movement | U7 dyn-regret OCO | 378.7 ± 2.0 | 0.94 | 1.25 | 200 | 1604 | 76.6 | 79.2 |
| model_picker_adapter | U1 online-Bayes | 387.7 ± 2.9 | 0.94 | 4.36 | 96 | 450 | 85.6 | 88.2 |
| online_llm_picker | U3 bandit selection | 388.5 ± 2.9 | 0.97 | 4.72 | 140 | 413 | 86.4 | 89.0 |
| model_selector_causal | U2 pool active selection | 391.1 ± 2.4 | 0.95 | 3.84 | 200 | 421 | 89.1 | 91.6 |
| CONTROL_never_switch | control | 392.9 ± 1.6 | 0.00 | 0.00 | 0 | nan | 90.9 | 93.5 |
| variance_min_ipw | U5 active risk est. | 398.9 ± 3.0 | 0.96 | 5.56 | 195 | 439 | 96.9 | 99.4 |
| cams_adapter | U4 expert advice | 400.0 ± 2.7 | 0.97 | 5.41 | 193 | 415 | 98.0 | 100.6 |
| P7s_settled | C5 ours-prior (B3+) | 401.8 ± 1.5 | 0.24 | 0.24 | 199 | 1908 | 99.8 | 102.4 |
| xu_acquisition_only | C4 active-testing betting | 402.6 ± 1.6 | 0.02 | 0.02 | 196 | 1862 | 100.5 | 103.1 |
| discern_style | C2 DISCERN CS | 402.9 ± 1.6 | 0.00 | 0.00 | 200 | nan | 100.9 | 103.4 |
| SMCS+retain-incumbent | C3 e-elimination | 402.9 ± 1.6 | 0.00 | 0.00 | 200 | nan | 100.9 | 103.4 |
| gated_deployment | C1 anytime-CS | 402.9 ± 1.6 | 0.00 | 0.00 | 200 | nan | 100.9 | 103.4 |

## F7_near_better

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| economic_replacement | control | 354.5 ± 1.7 | 0.99 | 0.99 | 200 | 264 | 20.2 | 25.3 |
| qiu_delayed_movement | U7 dyn-regret OCO | 364.9 ± 2.4 | 1.00 | 2.51 | 199 | 202 | 30.6 | 35.7 |
| model_selector_causal | U2 pool active selection | 365.0 ± 2.6 | 1.00 | 3.34 | 200 | 114 | 30.7 | 35.8 |
| ryabchenko_capacity | U8 capacity sched. | 368.6 ± 3.0 | 0.76 | 1.95 | 129 | 0 | 34.3 | 39.4 |
| variance_min_ipw | U5 active risk est. | 371.0 ± 3.3 | 1.00 | 4.51 | 195 | 120 | 36.7 | 41.8 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 372.8 ± 2.9 | 1.00 | 4.43 | 200 | 140 | 38.5 | 43.6 |
| model_picker_adapter | U1 online-Bayes | 373.7 ± 3.9 | 1.00 | 5.12 | 90 | 123 | 39.3 | 44.5 |
| cams_adapter | U4 expert advice | 376.1 ± 3.9 | 1.00 | 5.49 | 192 | 112 | 41.7 | 46.9 |
| online_llm_picker | U3 bandit selection | 385.9 ± 4.1 | 0.99 | 7.10 | 89 | 109 | 51.5 | 56.7 |
| CONTROL_never_switch | control | 391.1 ± 1.7 | 0.00 | 0.00 | 0 | nan | 56.8 | 62.0 |
| SMCS+retain-incumbent | C3 e-elimination | 394.3 ± 2.1 | 0.14 | 0.14 | 200 | 456 | 60.0 | 65.1 |
| P7s_settled | C5 ours-prior (B3+) | 395.2 ± 1.9 | 0.30 | 0.30 | 189 | 1167 | 60.9 | 66.0 |
| xu_acquisition_only | C4 active-testing betting | 397.6 ± 1.9 | 0.27 | 0.27 | 197 | 1388 | 63.3 | 68.4 |
| discern_style | C2 DISCERN CS | 401.1 ± 1.7 | 0.00 | 0.00 | 200 | nan | 66.8 | 71.9 |
| gated_deployment | C1 anytime-CS | 401.1 ± 1.7 | 0.00 | 0.00 | 200 | nan | 66.8 | 71.9 |

## F7_near_tiny

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| economic_replacement | control | 369.5 ± 1.8 | 0.95 | 0.95 | 200 | 277 | 15.0 | 27.2 |
| CONTROL_never_switch | control | 374.0 ± 1.9 | 0.00 | 0.00 | 0 | nan | 19.5 | 31.7 |
| ryabchenko_capacity | U8 capacity sched. | 375.3 ± 2.8 | 0.58 | 1.58 | 129 | 0 | 20.9 | 33.1 |
| xu_acquisition_only | C4 active-testing betting | 383.1 ± 1.8 | 0.09 | 0.09 | 195 | 976 | 28.6 | 40.8 |
| P7s_settled | C5 ours-prior (B3+) | 383.4 ± 1.9 | 0.07 | 0.07 | 197 | 934 | 28.9 | 41.1 |
| SMCS+retain-incumbent | C3 e-elimination | 383.5 ± 1.9 | 0.03 | 0.03 | 200 | 440 | 29.0 | 41.2 |
| discern_style | C2 DISCERN CS | 384.0 ± 1.9 | 0.00 | 0.00 | 200 | nan | 29.5 | 41.7 |
| gated_deployment | C1 anytime-CS | 384.0 ± 1.9 | 0.00 | 0.00 | 200 | nan | 29.5 | 41.7 |
| qiu_delayed_movement | U7 dyn-regret OCO | 391.6 ± 2.2 | 1.00 | 4.27 | 200 | 202 | 37.1 | 49.3 |
| model_selector_causal | U2 pool active selection | 392.7 ± 3.3 | 0.98 | 5.00 | 200 | 120 | 38.2 | 50.4 |
| model_picker_adapter | U1 online-Bayes | 395.1 ± 3.9 | 0.98 | 6.62 | 93 | 129 | 40.6 | 52.8 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 403.9 ± 3.1 | 1.00 | 6.78 | 200 | 146 | 49.4 | 61.6 |
| online_llm_picker | U3 bandit selection | 408.9 ± 3.9 | 1.00 | 8.96 | 94 | 110 | 54.4 | 66.6 |
| variance_min_ipw | U5 active risk est. | 413.1 ± 4.3 | 1.00 | 9.18 | 195 | 116 | 58.6 | 70.8 |
| cams_adapter | U4 expert advice | 419.2 ± 4.6 | 1.00 | 10.44 | 193 | 112 | 64.7 | 76.9 |

## F8_rare_better

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| cams_adapter | U4 expert advice | 212.6 ± 1.4 | 1.00 | 1.04 | 30 | 146 | 5.9 | 6.1 |
| online_llm_picker | U3 bandit selection | 212.7 ± 1.5 | 1.00 | 1.10 | 37 | 134 | 6.0 | 6.2 |
| model_selector_causal | U2 pool active selection | 213.3 ± 1.4 | 1.00 | 1.02 | 60 | 134 | 6.6 | 6.7 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 214.8 ± 1.4 | 1.00 | 1.02 | 60 | 194 | 8.1 | 8.3 |
| qiu_delayed_movement | U7 dyn-regret OCO | 215.0 ± 1.4 | 1.00 | 1.02 | 60 | 202 | 8.3 | 8.4 |
| model_picker_adapter | U1 online-Bayes | 215.2 ± 1.5 | 1.00 | 1.06 | 14 | 236 | 8.5 | 8.7 |
| variance_min_ipw | U5 active risk est. | 216.3 ± 1.4 | 1.00 | 1.08 | 112 | 135 | 9.6 | 9.7 |
| SMCS+retain-incumbent | C3 e-elimination | 222.8 ± 1.4 | 1.00 | 1.00 | 60 | 479 | 16.1 | 16.3 |
| ryabchenko_capacity | U8 capacity sched. | 224.0 ± 2.1 | 0.76 | 0.86 | 30 | 0 | 17.2 | 17.4 |
| economic_replacement | control | 224.6 ± 1.4 | 1.00 | 1.00 | 60 | 588 | 17.9 | 18.1 |
| xu_acquisition_only | C4 active-testing betting | 228.8 ± 1.4 | 1.00 | 1.00 | 60 | 747 | 22.1 | 22.3 |
| gated_deployment | C1 anytime-CS | 230.7 ± 1.4 | 1.00 | 1.00 | 28 | 896 | 24.0 | 24.2 |
| P7s_settled | C5 ours-prior (B3+) | 236.2 ± 1.4 | 0.98 | 0.98 | 40 | 1048 | 29.5 | 29.7 |
| CONTROL_never_switch | control | 250.2 ± 1.6 | 0.00 | 0.00 | 0 | nan | 43.5 | 43.7 |
| discern_style | C2 DISCERN CS | 253.2 ± 1.6 | 0.00 | 0.00 | 60 | nan | 46.5 | 46.7 |

## F9_bursty_better

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| model_selector_causal | U2 pool active selection | 333.7 ± 3.2 | 1.00 | 1.76 | 185 | 146 | 28.7 | 29.8 |
| model_picker_adapter | U1 online-Bayes | 333.7 ± 3.8 | 1.00 | 2.18 | 76 | 150 | 28.7 | 29.9 |
| online_llm_picker | U3 bandit selection | 334.1 ± 3.3 | 1.00 | 2.63 | 95 | 132 | 29.1 | 30.2 |
| cams_adapter | U4 expert advice | 334.9 ± 3.1 | 1.00 | 2.24 | 175 | 134 | 29.8 | 31.0 |
| qiu_delayed_movement | U7 dyn-regret OCO | 335.8 ± 3.2 | 1.00 | 1.12 | 189 | 202 | 30.7 | 31.9 |
| economic_replacement | control | 336.5 ± 3.1 | 1.00 | 1.00 | 189 | 323 | 31.5 | 32.6 |
| variance_min_ipw | U5 active risk est. | 337.9 ± 3.4 | 1.00 | 2.58 | 184 | 149 | 32.8 | 34.0 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 338.9 ± 4.0 | 1.00 | 2.42 | 189 | 158 | 33.8 | 35.0 |
| ryabchenko_capacity | U8 capacity sched. | 355.7 ± 6.0 | 0.68 | 1.01 | 47 | 0 | 50.6 | 51.8 |
| SMCS+retain-incumbent | C3 e-elimination | 375.3 ± 5.2 | 0.76 | 0.76 | 189 | 634 | 70.2 | 71.4 |
| xu_acquisition_only | C4 active-testing betting | 383.8 ± 4.5 | 0.88 | 0.88 | 187 | 970 | 78.8 | 79.9 |
| P7s_settled | C5 ours-prior (B3+) | 390.2 ± 4.9 | 0.79 | 0.79 | 163 | 956 | 85.1 | 86.3 |
| gated_deployment | C1 anytime-CS | 414.6 ± 6.4 | 0.26 | 0.26 | 168 | 944 | 109.6 | 110.7 |
| CONTROL_never_switch | control | 419.6 ± 5.5 | 0.00 | 0.00 | 0 | nan | 114.5 | 115.7 |
| discern_style | C2 DISCERN CS | 429.0 ± 5.6 | 0.00 | 0.00 | 189 | nan | 124.0 | 125.1 |

## F9_highdis_better

| policy | family | net (±se) | promote | switches | labels | 1st deploy (med) | regE | regH |
|---|---|---|---|---|---|---|---|---|
| economic_replacement | control | 557.2 ± 2.7 | 0.98 | 0.98 | 200 | 234 | 33.5 | 41.2 |
| cams_adapter | U4 expert advice | 571.2 ± 4.1 | 1.00 | 5.24 | 200 | 102 | 47.5 | 55.2 |
| model_selector_causal | U2 pool active selection | 572.6 ± 5.0 | 1.00 | 3.35 | 200 | 102 | 48.9 | 56.6 |
| model_picker_adapter | U1 online-Bayes | 573.7 ± 5.4 | 1.00 | 5.37 | 160 | 106 | 50.0 | 57.8 |
| qiu_delayed_movement | U7 dyn-regret OCO | 575.8 ± 2.9 | 1.00 | 2.62 | 200 | 202 | 52.1 | 59.8 |
| variance_min_ipw | U5 active risk est. | 587.7 ± 5.1 | 1.00 | 6.69 | 196 | 114 | 64.0 | 71.8 |
| online_llm_picker | U3 bandit selection | 592.4 ± 5.8 | 1.00 | 8.14 | 155 | 102 | 68.7 | 76.4 |
| gong_zhang_paid_obs | U6 paid-obs bandit | 595.4 ± 4.7 | 1.00 | 7.57 | 200 | 122 | 71.7 | 79.5 |
| ryabchenko_capacity | U8 capacity sched. | 598.2 ± 7.4 | 0.80 | 1.94 | 180 | 0 | 74.5 | 82.2 |
| P7s_settled | C5 ours-prior (B3+) | 659.3 ± 4.6 | 0.35 | 0.35 | 192 | 836 | 135.6 | 143.4 |
| xu_acquisition_only | C4 active-testing betting | 663.0 ± 4.7 | 0.35 | 0.35 | 194 | 883 | 139.3 | 147.0 |
| SMCS+retain-incumbent | C3 e-elimination | 677.4 ± 4.0 | 0.12 | 0.12 | 200 | 392 | 153.7 | 161.4 |
| CONTROL_never_switch | control | 680.3 ± 2.2 | 0.00 | 0.00 | 0 | nan | 156.6 | 164.3 |
| discern_style | C2 DISCERN CS | 690.3 ± 2.2 | 0.00 | 0.00 | 200 | nan | 166.6 | 174.3 |
| gated_deployment | C1 anytime-CS | 690.3 ± 2.2 | 0.00 | 0.00 | 200 | nan | 166.6 | 174.3 |
