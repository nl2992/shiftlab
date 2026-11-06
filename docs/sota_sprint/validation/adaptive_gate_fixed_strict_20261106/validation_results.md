# SOTA sprint validation results (locked protocol + Amendments 1-2)

**STRICT PUBLISHED-CERTIFICATE POOL:** only the six ports in `bench.CERTIFIED_PUBLISHED` are ranked. They remain common-contract adapters, not author-native full deployments. Raw runs and registered results are unchanged. Comparator selection still uses the same evaluation seeds; these contrasts are descriptive and do not provide selection-adjusted confirmatory inference.

Raw: `outputs/sota_sprint/validation/`. Synthetic 100 seeds (base 2026110601); in-class nulls 1000 seeds (base 2026110602); out-of-class nulls 1000 seeds (base 2026110605, descriptive).

## Null promotion rate (1000 seeds; bold = point > .0936) and harm vs never-switch

| policy | V_null | V_worse | V_null_dep_r5 | V_null_dep_r8 | W_null_dep_r9 | W_null_dep_r95 | W_worse_dep_r8 | O_null_semimarkov | O_null_order2 |
|---|---|---|---|---|---|---|---|---|---|
| A1b | 0.005 (ub 0.012; harm +10.04) | 0.000 (ub 0.004; harm +10.00) | 0.004 (ub 0.010; harm +10.03) | 0.000 (ub 0.004; harm +10.00) | 0.001 (ub 0.006; harm +10.04) | 0.001 (ub 0.006; harm +9.99) | 0.001 (ub 0.006; harm +10.06) | 0.054 (ub 0.070; harm +9.15) | 0.021 (ub 0.032; harm +9.82) |
| A5b | 0.005 (ub 0.012; harm +10.04) | 0.000 (ub 0.004; harm +10.00) | 0.003 (ub 0.009; harm +10.03) | 0.000 (ub 0.004; harm +9.64) | 0.001 (ub 0.006; harm +7.11) | 0.001 (ub 0.006; harm +5.25) | 0.000 (ub 0.004; harm +9.41) | 0.048 (ub 0.063; harm +8.63) | 0.018 (ub 0.028; harm +8.36) |
| B2 | 0.012 (ub 0.021; harm +10.03) | 0.000 (ub 0.004; harm +10.00) | 0.029 (ub 0.041; harm +10.17) | **0.134** (ub 0.157; harm +10.93) | **0.367** (ub 0.397; harm +12.34) | **0.712** (ub 0.739; harm +19.95) | 0.025 (ub 0.037; harm +10.94) | **0.338** (ub 0.368; harm +5.56) | **0.330** (ub 0.360; harm +12.07) |
| B5 | 0.006 (ub 0.013; harm +8.43) | 0.000 (ub 0.004; harm +8.35) | 0.018 (ub 0.028; harm +8.54) | **0.099** (ub 0.119; harm +9.58) | **0.286** (ub 0.315; harm +11.03) | **0.622** (ub 0.651; harm +18.50) | 0.012 (ub 0.021; harm +8.77) | **0.262** (ub 0.290; harm +4.12) | **0.249** (ub 0.277; harm +11.22) |
| C2 | 0.001 (ub 0.006; harm +3.92) | 0.000 (ub 0.004; harm +1.93) | 0.012 (ub 0.021; harm +3.77) | 0.088 (ub 0.107; harm +4.55) | **0.181** (ub 0.206; harm +4.79) | **0.330** (ub 0.360; harm +5.44) | 0.014 (ub 0.023; harm +3.27) | **0.140** (ub 0.163; harm +2.04) | **0.216** (ub 0.243; harm +4.47) |
| C6 | 0.001 (ub 0.006; harm +2.79) | 0.000 (ub 0.004; harm +1.67) | 0.011 (ub 0.020; harm +2.67) | 0.085 (ub 0.104; harm +3.74) | **0.173** (ub 0.198; harm +4.27) | **0.322** (ub 0.352; harm +5.03) | 0.013 (ub 0.022; harm +2.84) | **0.126** (ub 0.148; harm +2.03) | **0.208** (ub 0.234; harm +3.71) |
| CONTROL_never_switch | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.001; harm +0.00) | 0.000 (ub 0.004; harm +0.00) | 0.000 (ub 0.004; harm +0.00) |
| D1 | 0.023 (ub 0.034; harm +9.23) | 0.001 (ub 0.006; harm +5.76) | 0.055 (ub 0.071; harm +8.84) | **0.235** (ub 0.262; harm +8.81) | **0.376** (ub 0.406; harm +8.55) | **0.534** (ub 0.565; harm +9.67) | 0.056 (ub 0.072; harm +8.84) | **0.331** (ub 0.361; harm +3.49) | **0.405** (ub 0.436; harm +7.75) |
| D2 | 0.016 (ub 0.026; harm +9.87) | 0.002 (ub 0.007; harm +9.90) | 0.046 (ub 0.061; harm +9.99) | **0.230** (ub 0.257; harm +10.54) | **0.445** (ub 0.476; harm +9.76) | **0.704** (ub 0.732; harm +9.97) | 0.042 (ub 0.056; harm +11.75) | **0.367** (ub 0.397; harm +4.44) | **0.443** (ub 0.474; harm +9.11) |
| QSG | 0.019 (ub 0.029; harm +10.08) | 0.000 (ub 0.004; harm +9.99) | 0.052 (ub 0.068; harm +10.16) | **0.292** (ub 0.321; harm +12.26) | **0.497** (ub 0.528; harm +15.64) | **0.696** (ub 0.724; harm +18.88) | 0.083 (ub 0.102; harm +13.89) | **0.389** (ub 0.420; harm +7.12) | **0.501** (ub 0.532; harm +13.97) |
| SMCS+retain-incumbent | 0.030 (ub 0.043; harm +10.15) | 0.000 (ub 0.004; harm +9.98) | 0.024 (ub 0.035; harm +10.08) | **0.097** (ub 0.117; harm +10.51) | **0.195** (ub 0.221; harm +11.74) | **0.350** (ub 0.380; harm +13.56) | 0.023 (ub 0.034; harm +11.34) | **0.198** (ub 0.224; harm +6.50) | **0.193** (ub 0.219; harm +11.47) |
| X_A5C | 0.005 (ub 0.012; harm +10.00) | 0.000 (ub 0.004; harm +8.55) | 0.003 (ub 0.009; harm +9.96) | 0.000 (ub 0.004; harm +9.59) | 0.001 (ub 0.006; harm +7.08) | 0.001 (ub 0.006; harm +5.25) | 0.000 (ub 0.004; harm +9.19) | 0.047 (ub 0.062; harm +8.25) | 0.018 (ub 0.028; harm +8.11) |
| choe_ramdas_eb | 0.004 (ub 0.010; harm +9.99) | 0.000 (ub 0.004; harm +8.85) | 0.006 (ub 0.013; harm +9.84) | 0.037 (ub 0.051; harm +9.93) | 0.082 (ub 0.101; harm +9.16) | **0.213** (ub 0.239; harm +9.47) | 0.002 (ub 0.007; harm +8.49) | **0.106** (ub 0.127; harm +6.86) | 0.083 (ub 0.102; harm +9.24) |
| choe_ramdas_eb+front | 0.004 (ub 0.010; harm +9.92) | 0.000 (ub 0.004; harm +9.04) | 0.011 (ub 0.020; harm +9.83) | **0.116** (ub 0.137; harm +9.84) | **0.211** (ub 0.237; harm +8.78) | **0.373** (ub 0.403; harm +6.99) | 0.017 (ub 0.027; harm +8.99) | **0.172** (ub 0.197; harm +5.82) | **0.245** (ub 0.273; harm +8.58) |
| discern_design_floor | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.48) | 0.001 (ub 0.006; harm +9.99) | 0.014 (ub 0.023; harm +9.84) | 0.034 (ub 0.047; harm +9.68) | **0.110** (ub 0.131; harm +9.89) | 0.000 (ub 0.004; harm +9.35) | 0.077 (ub 0.095; harm +7.63) | 0.043 (ub 0.057; harm +10.05) |
| discern_style | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.98) | 0.000 (ub 0.004; harm +9.98) | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.98) | 0.006 (ub 0.013; harm +9.87) | 0.000 (ub 0.004; harm +9.99) |
| gated_adaptive_range | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.68) | 0.000 (ub 0.004; harm +9.98) | 0.009 (ub 0.017; harm +9.97) | 0.022 (ub 0.033; harm +9.39) | **0.115** (ub 0.136; harm +9.98) | 0.001 (ub 0.006; harm +9.51) | 0.062 (ub 0.079; harm +6.78) | 0.031 (ub 0.044; harm +9.43) |
| gated_adaptive_range+front | 0.001 (ub 0.006; harm +9.98) | 0.000 (ub 0.004; harm +9.17) | 0.010 (ub 0.018; harm +9.92) | **0.106** (ub 0.127; harm +9.74) | **0.218** (ub 0.245; harm +9.00) | **0.386** (ub 0.417; harm +8.14) | 0.014 (ub 0.023; harm +8.92) | **0.171** (ub 0.196; harm +5.25) | **0.239** (ub 0.266; harm +8.88) |
| gated_adaptive_range+pace_tuned | 0.001 (ub 0.006; harm +9.98) | 0.000 (ub 0.004; harm +9.14) | 0.010 (ub 0.018; harm +9.92) | **0.105** (ub 0.126; harm +9.83) | **0.214** (ub 0.240; harm +8.87) | **0.385** (ub 0.415; harm +8.06) | 0.014 (ub 0.023; harm +8.91) |  |  |
| gated_deployment | 0.000 (ub 0.004; harm +9.99) | 0.000 (ub 0.004; harm +9.97) | 0.000 (ub 0.004; harm +9.98) | 0.001 (ub 0.006; harm +9.97) | 0.003 (ub 0.009; harm +9.98) | 0.010 (ub 0.018; harm +10.17) | 0.000 (ub 0.004; harm +9.89) | 0.013 (ub 0.022; harm +9.14) | 0.005 (ub 0.012; harm +9.72) |
| gated_deployment+QCE | 0.001 (ub 0.006; harm +10.01) | 0.000 (ub 0.004; harm +8.89) | 0.004 (ub 0.010; harm +9.93) | 0.031 (ub 0.044; harm +9.89) | 0.093 (ub 0.113; harm +9.14) | **0.232** (ub 0.259; harm +9.59) | 0.001 (ub 0.006; harm +8.65) | **0.123** (ub 0.145; harm +5.05) | 0.079 (ub 0.097; harm +9.39) |
| gated_deployment+QCE+front | 0.002 (ub 0.007; harm +10.02) | 0.000 (ub 0.004; harm +9.18) | 0.011 (ub 0.020; harm +9.94) | **0.114** (ub 0.135; harm +9.72) | **0.248** (ub 0.276; harm +8.83) | **0.423** (ub 0.454; harm +8.11) | 0.013 (ub 0.022; harm +8.84) | **0.174** (ub 0.199; harm +4.66) | **0.249** (ub 0.277; harm +8.11) |
| rmm:gated_deployment+RMM | 0.012 (ub 0.021; harm +10.03) | 0.000 (ub 0.004; harm +10.00) | 0.029 (ub 0.041; harm +10.19) | **0.134** (ub 0.157; harm +10.87) | **0.367** (ub 0.397; harm +12.27) | **0.712** (ub 0.739; harm +19.29) | 0.025 (ub 0.037; harm +10.97) |  |  |
| xu_acquisition_only | 0.014 (ub 0.023; harm +9.78) | 0.000 (ub 0.004; harm +9.79) | 0.031 (ub 0.044; harm +9.88) | 0.068 (ub 0.085; harm +10.38) | **0.117** (ub 0.138; harm +9.61) | **0.239** (ub 0.266; harm +13.41) | 0.006 (ub 0.013; harm +10.04) | **0.157** (ub 0.181; harm +6.95) | **0.114** (ub 0.135; harm +10.49) |

## H0: Atlas v2 registered stop rule (vs tuned pacing only (Xu excluded from certificate-comparator selection))

* **A5b: FAIL**; safety rho .8/.95 True; CI<0 on 1/6: V_better_a -5.9 [-11.6,-0.2] vs gated_adaptive_range+pace_tuned; V_better_b +6.0 [+4.1,+7.9] vs gated_adaptive_range+pace_tuned; V_better_c +2.0 [-3.8,+7.8] vs gated_adaptive_range+pace_tuned; V_dep_better_r5 +34.5 [+27.4,+41.5] vs gated_adaptive_range+pace_tuned; V_near +0.4 [-2.4,+3.3] vs gated_adaptive_range+pace_tuned; V_bursty +1.4 [-2.4,+5.2] vs gated_adaptive_range+pace_tuned
* **A1b: FAIL**; safety rho .8/.95 True; CI<0 on 1/6: V_better_a -5.7 [-11.4,-0.0] vs gated_adaptive_range+pace_tuned; V_better_b +5.6 [+3.8,+7.3] vs gated_adaptive_range+pace_tuned; V_better_c +3.5 [-3.1,+10.0] vs gated_adaptive_range+pace_tuned; V_dep_better_r5 +30.9 [+24.0,+37.9] vs gated_adaptive_range+pace_tuned; V_near +0.4 [-2.4,+3.3] vs gated_adaptive_range+pace_tuned; V_bursty +1.4 [-2.4,+5.2] vs gated_adaptive_range+pace_tuned

## H1 (Amendment 2): class-scoped reliability on the safety-cost Pareto frontier

### A5b: **FAIL**
* part 1 (Wilson ub <= .0936 on all in-class nulls): True {'V_null': True, 'V_worse': True, 'V_null_dep_r5': True, 'V_null_dep_r8': True, 'W_null_dep_r9': True, 'W_null_dep_r95': True, 'W_worse_dep_r8': True}
* part 2 (each certified comparator fails a null or is cost-dominated on >= 3/6): True
  * gated_deployment: fails []; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * gated_adaptive_range: fails ['W_null_dep_r95']; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_near', 'V_bursty'] -> ok
  * gated_adaptive_range+front: fails ['V_null_dep_r8', 'W_null_dep_r9', 'W_null_dep_r95']; dominated on [] -> ok
  * discern_style: fails []; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * discern_design_floor: fails ['W_null_dep_r95']; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_near', 'V_bursty'] -> ok
  * SMCS+retain-incumbent: fails ['V_null_dep_r8', 'W_null_dep_r9', 'W_null_dep_r95']; dominated on ['V_better_a', 'V_better_c'] -> ok
* part 3 NI (+5): 2/5 iid (2/6 incl. bursty): V_better_a -3.1 [-8.4,+2.2] vs gated_adaptive_range+front; V_better_b +6.0 [+4.0,+7.9] vs gated_adaptive_range+front; V_better_c +4.1 [-1.2,+9.4] vs gated_adaptive_range+front; V_near +1.4 [-2.7,+5.5] vs SMCS+retain-incumbent; W_delay600_better -4.3 [-7.3,-1.2] vs gated_adaptive_range+front; V_bursty +2.4 [-1.3,+6.2] vs gated_adaptive_range+front
* declared losses: V_bursty +2.4 [-1.3,+6.2]; V_dep_better_r5 +36.6 [+29.7,+43.6]; W_better_dep_r7 +56.0 [+47.4,+64.7]; W_better_dep_r9 +87.3 [+76.9,+97.7]; V_late_600 -2.9 [-7.5,+1.7]; W_late_1000 +0.3 [-0.0,+0.6]; V_reversal_1000 +41.1 [+35.8,+46.3]; W_reversal_700 +56.3 [+49.6,+63.1]; V_recurrent +5.4 [+2.6,+8.1]
### A1b: **FAIL**
* part 1 (Wilson ub <= .0936 on all in-class nulls): True {'V_null': True, 'V_worse': True, 'V_null_dep_r5': True, 'V_null_dep_r8': True, 'W_null_dep_r9': True, 'W_null_dep_r95': True, 'W_worse_dep_r8': True}
* part 2 (each certified comparator fails a null or is cost-dominated on >= 3/6): True
  * gated_deployment: fails []; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * gated_adaptive_range: fails ['W_null_dep_r95']; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * gated_adaptive_range+front: fails ['V_null_dep_r8', 'W_null_dep_r9', 'W_null_dep_r95']; dominated on [] -> ok
  * discern_style: fails []; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * discern_design_floor: fails ['W_null_dep_r95']; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_near', 'V_bursty'] -> ok
  * SMCS+retain-incumbent: fails ['V_null_dep_r8', 'W_null_dep_r9', 'W_null_dep_r95']; dominated on ['V_better_a', 'V_better_c'] -> ok
* part 3 NI (+5): 2/5 iid (2/6 incl. bursty): V_better_a -3.0 [-8.3,+2.4] vs gated_adaptive_range+front; V_better_b +5.5 [+3.8,+7.3] vs gated_adaptive_range+front; V_better_c +5.5 [-0.6,+11.7] vs gated_adaptive_range+front; V_near +1.4 [-2.7,+5.5] vs SMCS+retain-incumbent; W_delay600_better -4.3 [-7.3,-1.2] vs gated_adaptive_range+front; V_bursty +2.4 [-1.3,+6.2] vs gated_adaptive_range+front
* declared losses: V_bursty +2.4 [-1.3,+6.2]; V_dep_better_r5 +33.1 [+26.2,+40.0]; W_better_dep_r7 +66.7 [+57.0,+76.4]; W_better_dep_r9 +91.8 [+81.3,+102.3]; V_late_600 -3.7 [-8.6,+1.2]; W_late_1000 +0.3 [-0.0,+0.6]; V_reversal_1000 +42.0 [+36.8,+47.2]; W_reversal_700 +55.5 [+48.7,+62.3]; V_recurrent +5.5 [+2.5,+8.4]
### X_A5C: **FAIL**
* part 1 (Wilson ub <= .0936 on all in-class nulls): True {'V_null': True, 'V_worse': True, 'V_null_dep_r5': True, 'V_null_dep_r8': True, 'W_null_dep_r9': True, 'W_null_dep_r95': True, 'W_worse_dep_r8': True}
* part 2 (each certified comparator fails a null or is cost-dominated on >= 3/6): True
  * gated_deployment: fails []; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * gated_adaptive_range: fails ['W_null_dep_r95']; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_near', 'V_bursty'] -> ok
  * gated_adaptive_range+front: fails ['V_null_dep_r8', 'W_null_dep_r9', 'W_null_dep_r95']; dominated on [] -> ok
  * discern_style: fails []; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_dep_better_r5', 'V_near', 'V_bursty'] -> ok
  * discern_design_floor: fails ['W_null_dep_r95']; dominated on ['V_better_a', 'V_better_b', 'V_better_c', 'V_near', 'V_bursty'] -> ok
  * SMCS+retain-incumbent: fails ['V_null_dep_r8', 'W_null_dep_r9', 'W_null_dep_r95']; dominated on ['V_better_a', 'V_better_c'] -> ok
* part 3 NI (+5): 2/5 iid (2/6 incl. bursty): V_better_a -3.1 [-8.4,+2.2] vs gated_adaptive_range+front; V_better_b +6.0 [+4.0,+7.9] vs gated_adaptive_range+front; V_better_c +4.1 [-1.2,+9.4] vs gated_adaptive_range+front; V_near +1.4 [-2.7,+5.5] vs SMCS+retain-incumbent; W_delay600_better -4.3 [-7.3,-1.2] vs gated_adaptive_range+front; V_bursty +2.4 [-1.3,+6.2] vs gated_adaptive_range+front
* declared losses: V_bursty +2.4 [-1.3,+6.2]; V_dep_better_r5 +36.6 [+29.7,+43.6]; W_better_dep_r7 +56.0 [+47.4,+64.7]; W_better_dep_r9 +87.3 [+76.9,+97.7]; V_late_600 -3.4 [-8.0,+1.2]; W_late_1000 -0.7 [-1.0,-0.3]; V_reversal_1000 +41.1 [+35.8,+46.3]; W_reversal_700 +56.3 [+49.6,+63.1]; V_recurrent +5.4 [+2.6,+8.1]

## H2 (cost superiority vs best certificate-policy comparator; Holm over 5 iid; requires Wilson-ub safety)

| candidate | safe | V_better_a | V_better_b | V_better_c | V_near | W_delay600_better | n sig | pass |
|---|---|---|---|---|---|---|---|---|
| A5b | True | -3.1 (p=0.509) | +6.0 (p=1) | +4.1 (p=1) | +1.4 (p=1) | -4.3 (p=0.0182) | 1 | False |
| A1b | True | -3.0 (p=0.563) | +5.5 (p=1) | +5.5 (p=1) | +1.4 (p=1) | -4.3 (p=0.0179) | 1 | False |
| D1 | False | -7.2 (p=0.0839) | -4.7 (p=3e-05) | +0.4 (p=1) | -5.1 (p=0.0839) | +8.4 (p=1) | 1 | False |
| D2 | False | -14.1 (p=0.00022) | -8.4 (p=0) | -10.6 (p=0.0051) | -6.5 (p=0.0147) | +0.2 (p=0.535) | 4 | False |
| C2 | False | +4.8 (p=1) | +0.4 (p=1) | +2.7 (p=1) | -0.1 (p=1) | +0.9 (p=1) | 0 | False |
| C6 | False | +7.5 (p=1) | +3.3 (p=1) | +10.6 (p=1) | -1.4 (p=1) | +1.3 (p=1) | 0 | False |
| X_A5C | True | -3.1 (p=0.509) | +6.0 (p=1) | +4.1 (p=1) | +1.4 (p=1) | -4.3 (p=0.0182) | 1 | False |
| B5 | False | +9.8 (p=1) | +15.3 (p=1) | +32.1 (p=1) | +0.2 (p=1) | +4.9 (p=1) | 0 | False |
| B2 | False | +5.9 (p=1) | +12.0 (p=1) | +22.4 (p=1) | +1.9 (p=1) | +5.8 (p=1) | 0 | False |

## H3 attribution (paired, 95% CI)

| contrast | mean [CI] |
|---|---|
| A5b-A1b@V_better_a | -0.2 [-0.5,+0.1] |
| A5b-A1b@V_better_b | +0.4 [-0.1,+0.9] |
| A5b-A1b@V_better_c | -1.4 [-4.0,+1.2] |
| A5b-A1b@V_near | +0.0 [-0.0,+0.0] |
| A5b-A1b@W_delay600_better | +0.0 [-0.0,+0.0] |
| A5b-A1b@V_bursty | +0.0 [+0.0,+0.0] |
| A5b-A1b@V_dep_better_r5 | +3.5 [-0.0,+7.1] |
| B2-host@V_reversal_1000 | -8.9 [-11.1,-6.6] |
| B2-host@W_reversal_700 | -8.4 [-10.9,-5.9] |
| B2-host@V_recurrent | +4.3 [+0.6,+8.1] |
| X_A5C-A5b@V_late_600 | -0.5 [-1.0,-0.0] |
| X_A5C-A5b@W_late_1000 | -0.9 [-1.4,-0.5] |
| B5-host@V_reversal_1000 | -12.0 [-17.3,-6.7] |
| B5-host@W_reversal_700 | -17.8 [-24.4,-11.2] |
| B5-host@V_recurrent | +2.7 [-3.4,+8.8] |
| D1-model_picker@V_null | -37.6 [-45.1,-30.1] |
| D2-cams@V_null | -59.6 [-68.3,-51.0] |
| D1-model_picker@V_null_dep_r8 | -33.9 [-41.5,-26.3] |
| D2-cams@V_null_dep_r8 | -46.6 [-56.2,-36.9] |
| C2-front@V_better_a | +4.8 [-0.1,+9.8] |
| C2-front@V_better_b | +0.4 [-0.3,+1.1] |
| C2-front@V_better_c | +2.7 [-2.4,+7.8] |
| C2-front@V_near | -1.4 [-3.1,+0.2] |
| C2-front@W_delay600_better | +0.9 [-0.5,+2.4] |

## All regimes: mean cost

| regime | best cert | best uncert | A5b | A1b | X_A5C | D1 | D2 | C2 | C6 | B2 | B5 | QSG | xu_acquisition_only | gated_adaptive_range+pace_tuned | gated_adaptive_range+front | choe_ramdas_eb+front | gated_deployment+QCE+front | SMCS+retain-incumbent | discern_style | CONTROL_never_switch |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V_better_a | gated_adaptive_range+front 430.9 | qiu_delayed_movement 373.4 | 427.8 | 427.9 | 427.8 | 423.7 | 416.8 | 435.7 | 438.4 | 436.8 | 440.7 | 415.4 | 437.0 | 433.6 | 430.9 | 428.4 | 433.0 | 440.7 | 467.1 | 457.1 |
| V_better_b | gated_adaptive_range+front 303.3 | model_picker_adapter 283.2 | 309.2 | 308.8 | 309.2 | 298.6 | 294.9 | 303.7 | 306.6 | 315.3 | 318.6 | 300.4 | 311.6 | 303.3 | 303.3 | 301.9 | 304.6 | 310.5 | 387.5 | 377.5 |
| V_better_c | gated_adaptive_range+front 421.5 | online_llm_picker 383.4 | 425.5 | 427.0 | 425.5 | 421.8 | 410.9 | 424.2 | 432.1 | 443.9 | 453.6 | 408.4 | 468.2 | 423.5 | 421.5 | 420.8 | 421.3 | 451.8 | 548.8 | 538.8 |
| V_bursty | gated_adaptive_range+front 401.3 | model_selector_causal 352.2 | 403.7 | 403.7 | 403.7 | 391.8 | 387.5 | 401.4 | 404.1 | 409.6 | 417.5 | 390.2 | 409.9 | 402.3 | 401.3 | 399.2 | 401.5 | 405.5 | 445.9 | 436.2 |
| V_dep_better_r5 | gated_adaptive_range+front 366.1 | model_selector_causal 328.6 | 402.8 | 399.2 | 402.8 | 354.3 | 353.3 | 371.1 | 372.9 | 373.7 | 381.5 | 352.7 | 376.4 | 368.3 | 366.1 | 365.6 | 367.4 | 376.4 | 423.5 | 413.5 |
| V_late_600 | SMCS+retain-incumbent 411.6 | qiu_delayed_movement 339.1 | 408.7 | 407.9 | 408.2 | 381.8 | 381.5 | 408.1 | 408.3 | 363.5 | 379.2 | 408.4 | 393.1 | 415.8 | 415.8 | 416.2 | 415.8 | 411.6 | 416.6 | 406.6 |
| V_near | SMCS+retain-incumbent 439.7 | model_selector_causal 401.7 | 441.0 | 441.0 | 441.0 | 434.6 | 433.1 | 439.6 | 438.3 | 441.6 | 439.8 | 433.2 | 441.3 | 440.6 | 441.0 | 439.8 | 440.8 | 439.7 | 447.8 | 437.8 |
| V_null | gated_deployment 413.1 | ryabchenko_capacity 422.0 | 413.2 | 413.2 | 413.2 | 412.2 | 412.7 | 407.0 | 405.9 | 413.4 | 411.6 | 413.1 | 412.9 | 413.1 | 413.1 | 413.1 | 413.1 | 413.1 | 413.1 | 403.1 |
| V_null_dep_r5 | gated_adaptive_range+front 371.1 | ryabchenko_capacity 382.7 | 370.9 | 370.9 | 370.8 | 370.6 | 370.8 | 365.2 | 364.1 | 372.1 | 369.9 | 371.4 | 371.3 | 371.1 | 371.1 | 370.8 | 370.6 | 372.5 | 371.4 | 361.4 |
| V_null_dep_r8 | gated_adaptive_range+front 407.1 | ryabchenko_capacity 411.6 | 408.8 | 409.1 | 408.7 | 407.1 | 406.5 | 402.0 | 401.6 | 408.7 | 407.3 | 406.8 | 408.0 | 407.2 | 407.1 | 405.8 | 406.2 | 409.1 | 409.1 | 399.1 |
| V_recurrent | gated_adaptive_range+front 380.6 | ryabchenko_capacity 372.9 | 385.9 | 386.0 | 385.9 | 378.0 | 375.5 | 379.9 | 380.3 | 406.4 | 404.8 | 383.1 | 397.9 | 380.6 | 380.6 | 378.8 | 380.5 | 384.7 | 397.2 | 387.2 |
| V_reversal_1000 | discern_style 370.1 | qiu_delayed_movement 350.9 | 411.1 | 412.1 | 411.1 | 409.2 | 405.6 | 408.8 | 407.6 | 397.1 | 393.9 | 405.1 | 410.6 | 408.4 | 408.5 | 407.0 | 409.1 | 412.2 | 370.1 | 360.1 |
| V_worse | gated_adaptive_range+front 330.1 | qiu_delayed_movement 343.6 | 330.9 | 330.9 | 329.1 | 326.4 | 330.6 | 322.8 | 322.5 | 330.9 | 329.2 | 330.9 | 330.6 | 330.0 | 330.1 | 329.9 | 330.0 | 330.9 | 330.8 | 320.9 |
| W_better_dep_r7 | gated_adaptive_range+front 369.4 | model_selector_causal 335.8 | 425.4 | 436.1 | 425.4 | 357.5 | 353.1 | 376.1 | 380.8 | 377.8 | 379.8 | 355.2 | 392.3 | 370.0 | 369.4 | 372.0 | 369.3 | 385.1 | 457.4 | 447.4 |
| W_better_dep_r9 | gated_adaptive_range+front 345.6 | model_selector_causal 321.1 | 432.9 | 437.3 | 432.9 | 334.3 | 327.4 | 355.2 | 360.4 | 348.6 | 353.4 | 328.5 | 366.7 | 344.3 | 345.6 | 347.6 | 343.1 | 354.9 | 442.4 | 432.4 |
| W_delay600_better | gated_adaptive_range+front 396.3 | online_llm_picker 355.9 | 392.0 | 392.0 | 392.0 | 404.7 | 396.5 | 397.2 | 397.6 | 402.1 | 401.2 | 382.5 | 419.1 | 395.7 | 396.3 | 394.9 | 396.8 | 399.3 | 425.2 | 415.2 |
| W_late_1000 | gated_adaptive_range+front 415.0 | qiu_delayed_movement 363.5 | 415.3 | 415.3 | 414.4 | 403.4 | 404.5 | 407.6 | 407.2 | 396.7 | 403.8 | 414.6 | 411.0 | 415.0 | 415.0 | 414.9 | 414.9 | 415.4 | 415.4 | 405.4 |
| W_null_dep_r9 | discern_design_floor 384.9 | ryabchenko_capacity 398.8 | 382.0 | 385.2 | 381.9 | 383.7 | 388.3 | 382.4 | 381.8 | 392.4 | 386.9 | 390.4 | 386.0 | 386.6 | 386.9 | 385.5 | 385.9 | 388.4 | 385.2 | 375.2 |
| W_null_dep_r95 | discern_design_floor 407.5 | ryabchenko_capacity 420.0 | 404.1 | 409.0 | 404.1 | 409.6 | 412.1 | 406.6 | 406.5 | 414.0 | 411.0 | 413.0 | 409.9 | 410.1 | 410.9 | 410.8 | 412.6 | 412.4 | 409.0 | 399.0 |
| W_reversal_700 | discern_style 348.4 | qiu_delayed_movement 352.5 | 404.7 | 403.8 | 404.7 | 412.4 | 413.4 | 407.9 | 406.7 | 379.8 | 370.4 | 404.7 | 388.8 | 410.2 | 410.2 | 406.7 | 408.9 | 399.2 | 348.4 | 338.4 |
| W_worse_dep_r8 | gated_adaptive_range 339.6 | ryabchenko_capacity 361.9 | 339.6 | 340.3 | 339.4 | 338.7 | 343.6 | 334.1 | 333.9 | 340.3 | 338.6 | 345.4 | 340.9 | 340.2 | 340.2 | 340.1 | 340.7 | 341.5 | 340.3 | 330.3 |
