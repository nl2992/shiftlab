# Failure Atlas v2: fresh-seed synthetic validation

Seed base 2026110399, 13 registered regimes x 100 paired streams, v2 contract. Analysis registered in protocol Amendments 1-2 before rows were read. Certified = promotion <= 0.0936 on every null (V_null, V_worse, V_null_dep_r5, V_null_dep_r8).

## Certification check (promotion rate on the validation nulls)

| policy | V_null | V_worse | V_null_dep_r5 | V_null_dep_r8 | certified |
|---|---|---|---|---|---|
| CONTROL_never_switch | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| discern+front_only | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| discern_design_floor | 0.00 | 0.00 | 0.00 | 0.01 | yes |
| discern_design_floor+front | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| discern_style | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| discern_style+QCE | 0.00 | 0.00 | 0.01 | 0.03 | yes |
| gated_adaptive_range | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| gated_deployment | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| gated_deployment+QCE | 0.00 | 0.00 | 0.01 | 0.04 | yes |
| xu_acquisition_only | 0.00 | 0.00 | 0.03 | 0.06 | yes |
| xu_acquisition_only+QCE | 0.00 | 0.00 | 0.03 | 0.05 | yes |
| P7s_settled | 0.03 | 0.00 | 0.08 | 0.12 | NO |
| QSG | 0.01 | 0.00 | 0.03 | 0.32 | NO |
| QSG-r25 | 0.01 | 0.00 | 0.03 | 0.32 | NO |
| SMCS+QCE | 0.03 | 0.00 | 0.01 | 0.11 | NO |
| SMCS+QCE+front | 0.01 | 0.00 | 0.02 | 0.23 | NO |
| SMCS+QCE+front_v0front | 0.01 | 0.00 | 0.02 | 0.23 | NO |
| SMCS+front_only | 0.03 | 0.00 | 0.04 | 0.23 | NO |
| SMCS+front_only_v0front | 0.03 | 0.00 | 0.04 | 0.23 | NO |
| SMCS+retain-incumbent | 0.05 | 0.00 | 0.03 | 0.13 | NO |
| cams_adapter | 0.97 | 0.74 | 0.95 | 0.97 | NO |
| discern_style+QCE+front | 0.00 | 0.00 | 0.01 | 0.13 | NO |
| economic_replacement | 0.92 | 0.39 | 0.83 | 0.78 | NO |
| gated+front_only | 0.00 | 0.00 | 0.02 | 0.13 | NO |
| gated_adaptive_range+front | 0.00 | 0.00 | 0.02 | 0.13 | NO |
| gated_deployment+QCE+front | 0.00 | 0.00 | 0.02 | 0.16 | NO |
| gong_zhang_paid_obs | 0.99 | 0.71 | 1.00 | 0.99 | NO |
| model_picker_adapter | 0.93 | 0.73 | 0.95 | 0.96 | NO |
| model_selector_causal | 0.99 | 0.65 | 0.95 | 0.94 | NO |
| online_llm_picker | 0.97 | 0.87 | 0.98 | 0.97 | NO |
| qiu_delayed_movement | 0.98 | 0.51 | 1.00 | 1.00 | NO |
| ryabchenko_capacity | 0.63 | 0.53 | 0.56 | 0.68 | NO |
| variance_min_ipw | 0.98 | 0.70 | 0.96 | 0.93 | NO |
| xu+front_only | 0.00 | 0.00 | 0.04 | 0.13 | NO |
| xu_acquisition_only+QCE+front | 0.00 | 0.00 | 0.04 | 0.13 | NO |

## Primary: repaired minus host, stationary alternatives (paired, 100 streams)

| host -> repaired | V_better_a | V_better_b | V_better_c | V_dep_better_r5 | V_near | V_bursty | CI<0 count |
|---|---|---|---|---|---|---|---|
| gated_deployment -> gated_deployment+QCE+front | -41.5 [-49.9,-32.4] | -60.2 [-66.4,-53.2] | -123.9 [-133.5,-113.1] | -57.7 [-65.7,-49.3] | -6.6 [-10.3,-3.2] | -44.5 [-52.7,-36.0] | 6/6 |
| discern_style -> discern_style+QCE+front | -43.8 [-52.7,-34.5] | -89.2 [-94.2,-83.8] | -127.7 [-137.1,-117.4] | -58.7 [-67.4,-49.5] | -7.3 [-11.1,-3.8] | -47.0 [-54.9,-38.7] | 6/6 |
| SMCS+retain-incumbent -> SMCS+QCE+front | -20.8 [-28.4,-12.7] | -5.0 [-7.7,-2.3] | -45.5 [-56.9,-34.7] | -18.1 [-24.0,-12.2] | -1.2 [-5.1,+2.3] | -16.6 [-24.9,-8.4] | 5/6 |
| xu_acquisition_only -> xu_acquisition_only+QCE+front | -21.3 [-28.1,-14.4] | -9.9 [-12.5,-7.4] | -32.3 [-41.3,-23.6] | -16.1 [-21.1,-10.7] | -1.2 [-4.9,+2.4] | -21.4 [-27.6,-14.9] | 5/6 |
| gated_adaptive_range -> gated_adaptive_range+front | -34.7 [-43.2,-26.5] | -34.5 [-38.9,-29.7] | -93.3 [-104.6,-81.8] | -38.4 [-45.5,-31.3] | -6.2 [-9.8,-3.1] | -37.4 [-45.5,-29.4] | 6/6 |
| discern_design_floor -> discern_design_floor+front | +7.5 [+3.3,+11.9] | +0.4 [-2.5,+3.1] | +15.9 [+5.3,+26.5] | +4.8 [+0.7,+8.9] | +1.8 [+0.4,+3.7] | +6.5 [+1.9,+11.2] | 0/6 |

## Same comparisons on change regimes and nulls (secondary, reported in full)

| host -> repaired | V_late_600 | V_reversal_1000 | V_recurrent | V_null | V_worse | V_null_dep_r5 | V_null_dep_r8 |
|---|---|---|---|---|---|---|---|
| gated_deployment -> gated_deployment+QCE+front | -0.5 [-0.8,-0.2] | +35.6 [+29.4,+40.8] | -19.5 [-23.1,-16.0] | +0.0 [+0.0,+0.0] | -0.8 [-1.2,-0.5] | +0.2 [-0.0,+0.4] | -0.5 [-2.5,+1.7] |
| discern_style -> discern_style+QCE+front | -0.5 [-0.8,-0.2] | +33.0 [+28.5,+37.6] | -21.5 [-25.2,-17.6] | +0.0 [+0.0,+0.0] | -1.0 [-1.4,-0.6] | -0.1 [-0.2,+0.0] | -0.1 [-1.7,+1.8] |
| SMCS+retain-incumbent -> SMCS+QCE+front | +2.2 [-1.7,+6.0] | -0.3 [-5.1,+4.9] | -7.5 [-10.3,-5.0] | +0.3 [-0.5,+1.3] | +0.0 [+0.0,+0.0] | +0.1 [-0.3,+0.5] | +2.6 [-0.5,+5.9] |
| xu_acquisition_only -> xu_acquisition_only+QCE+front | +19.8 [+15.1,+24.5] | +0.1 [-4.8,+5.6] | -13.7 [-18.5,-9.4] | +0.2 [+0.1,+0.3] | +0.2 [+0.2,+0.3] | +0.5 [+0.2,+1.0] | +0.4 [-1.2,+2.1] |
| gated_adaptive_range -> gated_adaptive_range+front | +0.2 [-1.1,+1.5] | +7.5 [-0.6,+16.3] | -17.9 [-21.2,-14.7] | +0.0 [+0.0,+0.0] | -0.6 [-1.0,-0.2] | +0.1 [-0.1,+0.4] | -0.4 [-2.0,+1.5] |
| discern_design_floor -> discern_design_floor+front | +4.1 [+1.9,+6.6] | +15.5 [+8.7,+22.5] | +1.4 [-0.0,+2.9] | +0.0 [+0.0,+0.0] | +0.7 [+0.5,+1.0] | +0.0 [+0.0,+0.0] | +0.0 [-0.1,+0.1] |

## Secondary: our certified variants vs strongest certified published method

Published certified methods passing the criterion: gated_deployment, gated_adaptive_range, discern_style, discern_design_floor, xu_acquisition_only. Our variants passing: none. The strongest published method is chosen per regime on these same seeds (favours the comparator).

| regime | strongest published (net) | best ours (net) | ours - published [95% CI] | best uncertified (net, promote on V_null) | never |
|---|---|---|---|---|---|
| V_better_a | xu_acquisition_only (433.9) | none | n/a | model_selector_causal (370.6, 0.99) | 458.7 |
| V_better_b | xu_acquisition_only (312.2) | none | n/a | model_selector_causal (281.3, 0.99) | 378.3 |
| V_better_c | xu_acquisition_only (473.0) | none | n/a | model_selector_causal (388.0, 0.99) | 536.1 |
| V_dep_better_r5 | xu_acquisition_only (381.0) | none | n/a | model_selector_causal (330.6, 0.99) | 419.0 |
| V_near | xu_acquisition_only (435.1) | none | n/a | model_selector_causal (403.3, 0.99) | 433.4 |
| V_bursty | xu_acquisition_only (406.3) | none | n/a | model_selector_causal (348.2, 0.99) | 427.5 |
| V_late_600 | xu_acquisition_only (390.8) | none | n/a | qiu_delayed_movement (336.7, 0.98) | 403.3 |
| V_reversal_1000 | discern_style (370.2) | none | n/a | gong_zhang_paid_obs (349.7, 0.99) | 360.2 |
| V_recurrent | gated_adaptive_range (395.2) | none | n/a | ryabchenko_capacity (372.1, 0.63) | 388.5 |
| V_null | xu_acquisition_only (412.1) | none | n/a | ryabchenko_capacity (421.4, 0.63) | 402.3 |
| V_worse | discern_design_floor (327.3) | none | n/a | qiu_delayed_movement (341.1, 0.98) | 318.1 |
| V_null_dep_r5 | xu_acquisition_only (367.4) | none | n/a | ryabchenko_capacity (376.3, 0.63) | 357.6 |
| V_null_dep_r8 | xu_acquisition_only (406.1) | none | n/a | ryabchenko_capacity (410.4, 0.63) | 396.4 |

## Net cost, all policies

| policy                        |   V_better_a |   V_better_b |   V_better_c |   V_bursty |   V_dep_better_r5 |   V_late_600 |   V_near |   V_null |   V_null_dep_r5 |   V_null_dep_r8 |   V_recurrent |   V_reversal_1000 |   V_worse |
|:------------------------------|-------------:|-------------:|-------------:|-----------:|------------------:|-------------:|---------:|---------:|----------------:|----------------:|--------------:|------------------:|----------:|
| CONTROL_never_switch          |        458.7 |        378.3 |        536.1 |      427.5 |             419   |        403.3 |    433.4 |    402.3 |           357.6 |           396.4 |         388.5 |             360.2 |     318.1 |
| P7s_settled                   |        435.4 |        310.4 |        470.1 |      406.4 |             384.4 |        373.3 |    438.8 |    412   |           368.2 |           406.7 |         393.4 |             406.9 |     327.8 |
| QSG                           |        408.2 |        297.2 |        408.1 |      381.5 |             358.4 |        399.1 |    432.7 |    412.5 |           367.8 |           411.2 |         382.9 |             403   |     328.1 |
| QSG-r25                       |        415.1 |        297.5 |        412.1 |      386.4 |             360.5 |        404.5 |    433.4 |    412.5 |           367.8 |           411.1 |         383.6 |             402.8 |     328.1 |
| SMCS+QCE                      |        438.2 |        311.4 |        459.8 |      401.6 |             384.2 |        400.9 |    438   |    412.5 |           367.5 |           407.2 |         388.1 |             414   |     328   |
| SMCS+QCE+front                |        414.7 |        299.7 |        410.6 |      384.2 |             362.2 |        411   |    435.2 |    412.5 |           367.7 |           409.7 |         376.9 |             408.1 |     328.1 |
| SMCS+QCE+front_v0front        |        414.7 |        299.7 |        410.6 |      384.2 |             362.2 |        411   |    435.2 |    412.5 |           367.7 |           409.7 |         376.9 |             408.1 |     328.1 |
| SMCS+front_only               |        424.6 |        298   |        418.3 |      395.5 |             365.1 |        413.3 |    435.3 |    412.2 |           367.7 |           409.1 |         373   |             401.8 |     328.1 |
| SMCS+front_only_v0front       |        424.6 |        298   |        418.3 |      395.5 |             365.1 |        413.3 |    435.3 |    412.2 |           367.7 |           409.1 |         373   |             401.8 |     328.1 |
| SMCS+retain-incumbent         |        435.5 |        304.7 |        456.1 |      400.8 |             380.3 |        408.9 |    436.4 |    412.2 |           367.6 |           407   |         384.4 |             408.4 |     328   |
| cams_adapter                  |        378   |        281.6 |        389.6 |      353.6 |             335.8 |        365.2 |    413.7 |    466.8 |           417.7 |           448.1 |         374.5 |             391.1 |     350.8 |
| discern+front_only            |        468.7 |        388.3 |        546.1 |      437.5 |             429   |        413.3 |    443.4 |    412.3 |           367.6 |           406.4 |         398.5 |             370.2 |     328.1 |
| discern_design_floor          |        453.9 |        344.5 |        487.2 |      426.1 |             408   |        409.3 |    441.5 |    412.3 |           367.5 |           406.4 |         396.3 |             409.6 |     327.3 |
| discern_design_floor+front    |        461.4 |        344.9 |        503.1 |      432.6 |             412.7 |        413.3 |    443.4 |    412.3 |           367.6 |           406.4 |         397.7 |             425.1 |     328.1 |
| discern_style                 |        468.7 |        388.2 |        546.1 |      437.3 |             429   |        413.3 |    443.4 |    412.3 |           367.5 |           406.4 |         398.5 |             370.2 |     328   |
| discern_style+QCE             |        443.2 |        310.8 |        470.2 |      413.5 |             390.5 |        409.8 |    440.5 |    412.3 |           367.3 |           405.8 |         388.7 |             411.7 |     326.4 |
| discern_style+QCE+front       |        424.9 |        299   |        418.4 |      390.3 |             370.3 |        412.8 |    436   |    412.3 |           367.5 |           406.3 |         377   |             403.2 |     327.1 |
| economic_replacement          |        371.6 |        287.8 |        395.2 |      346.8 |             334   |        336.7 |    391.6 |    417.2 |           377.2 |           410.9 |         365.2 |             397   |     358.3 |
| gated+front_only              |        427.8 |        299.8 |        421.3 |      391.1 |             367.8 |        412.2 |    436.6 |    412.3 |           367.7 |           406   |         377.4 |             408.3 |     327.2 |
| gated_adaptive_range          |        462.5 |        334.2 |        514.6 |      428.5 |             406.2 |        412   |    442.8 |    412.3 |           367.5 |           406.4 |         395.2 |             400.7 |     327.8 |
| gated_adaptive_range+front    |        427.8 |        299.8 |        421.3 |      391.1 |             367.8 |        412.2 |    436.6 |    412.3 |           367.7 |           406   |         377.4 |             408.3 |     327.2 |
| gated_deployment              |        468.7 |        360.7 |        545.3 |      436.8 |             426.5 |        413.3 |    443.4 |    412.3 |           367.5 |           406.4 |         397.7 |             373.5 |     328   |
| gated_deployment+QCE          |        446.6 |        318.1 |        479.4 |      414.8 |             389.4 |        406.5 |    441.7 |    412.3 |           367.6 |           406.3 |         391.3 |             416.3 |     327   |
| gated_deployment+QCE+front    |        427.3 |        300.6 |        421.3 |      392.3 |             368.8 |        412.8 |    436.8 |    412.3 |           367.7 |           405.9 |         378.2 |             409.1 |     327.2 |
| gong_zhang_paid_obs           |        377.8 |        283.6 |        392.5 |      354.6 |             338.3 |        345.5 |    416   |    450.1 |           399.6 |           445.3 |         385.4 |             349.7 |     350.7 |
| model_picker_adapter          |        381.9 |        281.6 |        391.4 |      353.4 |             333   |        361.6 |    411.9 |    450.8 |           398   |           445.3 |         377.6 |             384.3 |     349.6 |
| model_selector_causal         |        370.6 |        281.3 |        388   |      348.2 |             330.6 |        352.5 |    403.3 |    439.5 |           395.6 |           436.3 |         373.4 |             387.4 |     343.2 |
| online_llm_picker             |        381.7 |        284.9 |        390.2 |      355.9 |             341.6 |        357.3 |    420.9 |    455.1 |           407.5 |           440.3 |         377.5 |             376.3 |     361.5 |
| qiu_delayed_movement          |        374.7 |        282.3 |        399.8 |      349   |             335.7 |        336.7 |    407.6 |    435.3 |           392   |           433.6 |         384.1 |             351.2 |     341.1 |
| ryabchenko_capacity           |        397   |        300.6 |        431.7 |      377   |             357.7 |        358.2 |    411.2 |    421.4 |           376.3 |           410.4 |         372.1 |             385.5 |     364.3 |
| variance_min_ipw              |        380   |        282.7 |        394.1 |      355.3 |             339   |        368.3 |    423.8 |    464.7 |           417.2 |           446.2 |         382.7 |             392.2 |     354.5 |
| xu+front_only                 |        412.6 |        302.2 |        440.7 |      385   |             365   |        410.6 |    433.9 |    412.3 |           367.9 |           406.5 |         384   |             414.7 |     328.1 |
| xu_acquisition_only           |        433.9 |        312.2 |        473   |      406.3 |             381   |        390.8 |    435.1 |    412.1 |           367.4 |           406.1 |         397.8 |             414.6 |     327.9 |
| xu_acquisition_only+QCE       |        433.7 |        314.3 |        477.8 |      402.5 |             383.2 |        391.4 |    436.4 |    412.1 |           367.4 |           406.2 |         397.5 |             414.7 |     327.9 |
| xu_acquisition_only+QCE+front |        412.6 |        302.2 |        440.7 |      385   |             365   |        410.6 |    433.9 |    412.3 |           367.9 |           406.5 |         384   |             414.7 |     328.1 |
