# Transfer tests (Amendments 3 and 4)

## HR, RMM transfer across 5 hosts: **FAIL** (3/5 hosts with CI<0 and iid-null safety)

| host | family Delta J (host+RMM - host) | iid nulls safe | rho .8 null | rho .95 null | reversal_1000 | reversal_700 |
|---|---|---|---|---|---|---|
| gated_deployment | -44.2 [-46.9,-41.4] | True | 0.151 | 0.683 | +32.3 | +29.6 |
| discern_style | -47.3 [-49.8,-44.8] | True | 0.156 | 0.660 | +34.0 | +33.1 |
| SMCS+retain-incumbent | -13.3 [-16.0,-10.6] | True | 0.156 | 0.701 | -9.6 | -20.3 |
| model_picker_adapter | +2.8 [-0.6,+6.1] | False | 0.952 | 0.953 | +1.4 | -0.0 |
| cams_adapter | -0.1 [-2.7,+2.6] | False | 0.942 | 0.968 | -11.4 | -6.2 |

HR2, best host+RMM = rmm:cams_adapter+RMM; family Delta vs: gated_adaptive_range+front -30.5 [-33.2,-27.7]; gated_deployment+QCE+front -30.4 [-33.2,-27.7]; xu_acquisition_only -36.5 [-39.4,-33.5]; discern_design_floor -54.7 [-57.5,-52.0]; P7s_settled -30.3 [-33.2,-27.3]; A5b -30.2 [-33.1,-27.4]; rmm:LRMD -20.5 [-23.1,-17.8]

Late-regime test vs best certified published (Holm): V_late_600 -24.7 [-31.4,-18.1] vs xu_acquisition_only (holm p=0); W_late_1000 -7.7 [-14.3,-1.1] vs xu_acquisition_only (holm p=0.0119)

Attribution (family mean): rmm:gated_deployment+RMM - rmm:gated_deployment+RMM_single: -2.5 [-4.4,-0.6]; rmm:discern_style+RMM - rmm:discern_style+RMM_single: -2.4 [-4.3,-0.4]; rmm:SMCS+retain-incumbent+RMM - rmm:SMCS+retain-incumbent+RMM_single: -5.5 [-7.1,-3.8]; rmm:gated_deployment+RMM - rmm:gated_deployment+RMM_noacq: -11.0 [-13.3,-8.7]; rmm:discern_style+RMM - rmm:discern_style+RMM_noacq: -8.0 [-10.1,-5.8]

## HD, deploy-gate transfer across 3 hosts: **FAIL**

| gated host | vs native host (all regimes) | Holm-sig vs best certified (of 5) | iid nulls safe | null rates | fresh real vs best certified (improved/K) |
|---|---|---|---|---|---|
| D1 (model_picker_adapter) | +4.9 [+3.1,+6.7] | 0 | True | V_null 0.016, V_null_dep_r5 0.055, V_null_dep_r8 0.233, V_worse 0.001 | appliances +14.3 (1/6); beijing_pm25 -14.6 (11/14); bike_hour -1.2 (4/6); household_power +3.8 (9/20); metro +0.6 (6/16) |
| D2 (cams_adapter) | -1.8 [-3.6,+0.0] | 2 | True | V_null 0.014, V_null_dep_r5 0.045, V_null_dep_r8 0.226, V_worse 0.000 | appliances +1.4 (3/6); beijing_pm25 -33.2 (13/14); bike_hour -6.1 (5/6); household_power -2.8 (11/20); metro -2.7 (14/16) |
| D6-D1params:ms (model_selector_causal) | +7.4 [+5.8,+9.0] | 2 | True | V_null 0.016, V_null_dep_r5 0.049, V_null_dep_r8 0.197, V_worse 0.000 | appliances +29.2 (2/6); beijing_pm25 -6.3 (10/14); bike_hour -6.2 (4/6); household_power +2.4 (9/20); metro -1.3 (11/16) |
