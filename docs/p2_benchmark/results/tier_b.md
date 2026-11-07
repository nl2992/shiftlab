# P2 Tier B gate (H8): registered analysis output

- two-tier admitted: [['gated_adaptive_range+front', 356.36604166666666], ['choe_ramdas_eb+front', 357.36650000000003], ['SMCS+retain-incumbent', 365.3548333333333], ['choe_ramdas_eb', 373.36983333333336], ['xu_acquisition_only', 374.44812500000006], ['gated_deployment+QCE', 376.2065], ['gated_adaptive_range', 392.2908333333333], ['discern_design_floor', 393.24108333333334], ['A5b', 395.22858333333335], ['D5', 396.61033333333336], ['gated_deployment', 417.88325000000003], ['discern_style', 429.81325]]
- single gate admitted: [['discern_style', 429.81325]]
- H8a: {'n_pass_tier_a': 16, 'of': 16}
- H8b: {"QSG": {"mean": 7.466, "lb99": 2.92594, "pass": true}, "SMCS+retain-incumbent": {"mean": 1.578, "lb99": -1.53004, "pass": false}, "pass": false}
- H8c: {"P_star": "gated_adaptive_range", "S_star": "discern_style", "diff_mean": -37.522416666666665, "ci99": [-41.31619625, -33.943069583333326], "i_two_tier_admits": true, "ii_single_rejects": true, "iii_ub_below_minus5": true, "pass": true}
- H8d: agree 10/16; observed ['A5b', 'D5', 'SMCS+retain-incumbent', 'choe_ramdas_eb', 'choe_ramdas_eb+front', 'discern_design_floor', 'discern_style', 'gated_adaptive_range', 'gated_adaptive_range+front', 'gated_deployment', 'gated_deployment+QCE', 'xu_acquisition_only']

| policy | class | Tier A | Tier B | worst null | worst UB95 | single | J alt |
|---|---|---|---|---|---:|---|---:|
| D2 | V1 | True | False | F5_dep_null_r95 | 9.01 | False | 342.4 |
| QSG | V1 | True | False | F5_dep_null_r95 | 10.78 | False | 345.7 |
| gated_deployment+QCE+front | V1 | True | False | F5_dep_null_r95 | 5.29 | False | 356.1 |
| gated_adaptive_range+front | V1 | True | True | F5_dep_null_r95 | 4.20 | False | 356.4 |
| choe_ramdas_eb+front | V1 | True | True | F5_dep_null_r95 | 4.80 | False | 357.4 |
| rmm:gated_deployment+RMM | V1 | True | False | F5_dep_null_r95 | 6.62 | False | 361.4 |
| SMCS+retain-incumbent | V1 | True | True | F5_dep_null_r95 | 3.96 | False | 365.4 |
| choe_ramdas_eb | V1 | True | True | WP2_o2_null | 2.83 | False | 373.4 |
| xu_acquisition_only | V1 | True | True | F5_dep_null_r95 | 3.96 | False | 374.4 |
| gated_deployment+QCE | V1 | True | True | F5_dep_null_r95 | 3.56 | False | 376.2 |
| gated_adaptive_range | V1 | True | True | F5_dep_null_r95 | 2.36 | False | 392.3 |
| discern_design_floor | V1 | True | True | F5_dep_null_r95 | 1.79 | False | 393.2 |
| A5b | V2 | True | True | WP2_hs_null | 1.87 | False | 395.2 |
| D5 | V2 | True | True | WP2_sm_null | 1.76 | False | 396.6 |
| gated_deployment | V1 | True | True | WP2_o2_null | 1.09 | False | 417.9 |
| discern_style | V1 | True | True | F5_dep_null_r8 | 0.00 | True | 429.8 |
