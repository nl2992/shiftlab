# Real-data validation

Fresh streams registered in aeb2d4f before any policy run (20 policy seeds, base 2026110604). Exposed streams are descriptive (10 seeds, base 2026110603). Unit = episode; consecutive windows, so CIs are optimistic.

## Fresh, never-used streams (external validation)

| dataset | K | candidate | vs best certified | vs host | vs best uncertified | improved/K (sign p) |
|---|---|---|---|---|---|---|
| appliances | 6 | A5b | +257.3 [+150.8,+363.9] (choe_ramdas_eb+front) |  | +232.6 (cams_adapter) | 0/6 (p=0.0312) |
| appliances | 6 | X_A5C | +257.3 [+150.8,+363.9] (choe_ramdas_eb+front) |  | +232.6 (cams_adapter) | 0/6 (p=0.0312) |
| appliances | 6 | D1 | +13.7 [+2.0,+25.4] (choe_ramdas_eb+front) | -11.1 [-46.2,+23.9] | -11.1 (cams_adapter) | 1/6 (p=0.219) |
| appliances | 6 | D2 | +1.2 [-1.7,+4.0] (choe_ramdas_eb+front) | -23.6 [-59.0,+11.8] | -23.6 (cams_adapter) | 3/6 (p=1) |
| appliances | 6 | C2 | +0.7 [-0.8,+2.2] (choe_ramdas_eb+front) | -0.1 [-0.2,+0.1] | -24.1 (cams_adapter) | 1/6 (p=0.625) |
| appliances | 6 | C6 | +0.7 [-0.8,+2.2] (choe_ramdas_eb+front) | -0.1 [-0.2,+0.1] | -24.1 (cams_adapter) | 1/6 (p=0.625) |
| appliances | 6 | B2 | +66.7 [+36.9,+96.6] (choe_ramdas_eb+front) | +5.2 [-3.0,+13.3] | +42.0 (cams_adapter) | 0/6 (p=0.0312) |
| appliances | 6 | B5 | +81.7 [+53.8,+109.6] (choe_ramdas_eb+front) | +20.1 [+6.8,+33.4] | +56.9 (cams_adapter) | 0/6 (p=0.0312) |
| beijing_pm25 | 14 | A5b | +76.3 [+25.5,+127.1] (SMCS+retain-incumbent) |  | +101.0 (model_picker_adapter) | 2/14 (p=0.0129) |
| beijing_pm25 | 14 | X_A5C | +76.3 [+25.5,+127.1] (SMCS+retain-incumbent) |  | +101.0 (model_picker_adapter) | 2/14 (p=0.0129) |
| beijing_pm25 | 14 | D1 | -15.3 [-34.8,+4.2] (SMCS+retain-incumbent) | +9.5 [-13.8,+32.7] | +9.5 (model_picker_adapter) | 11/14 (p=0.0574) |
| beijing_pm25 | 14 | D2 | -32.8 [-55.0,-10.6] (SMCS+retain-incumbent) | -9.9 [-20.2,+0.4] | -8.1 (model_picker_adapter) | 14/14 (p=0.000122) |
| beijing_pm25 | 14 | C2 | +16.8 [-25.8,+59.4] (SMCS+retain-incumbent) | -2.0 [-3.7,-0.4] | +41.6 (model_picker_adapter) | 7/14 (p=1) |
| beijing_pm25 | 14 | C6 | +16.2 [-26.3,+58.6] (SMCS+retain-incumbent) | -2.7 [-4.7,-0.7] | +40.9 (model_picker_adapter) | 7/14 (p=1) |
| beijing_pm25 | 14 | B2 | -14.3 [-29.3,+0.8] (SMCS+retain-incumbent) | -0.0 [-1.2,+1.1] | +10.5 (model_picker_adapter) | 10/14 (p=0.18) |
| beijing_pm25 | 14 | B5 | -8.6 [-20.9,+3.7] (SMCS+retain-incumbent) | +5.7 [-0.7,+12.1] | +16.2 (model_picker_adapter) | 8/14 (p=0.791) |
| bike_hour | 6 | A5b | +81.8 [+41.5,+122.0] (choe_ramdas_eb+front) |  | +94.8 (model_picker_adapter) | 0/6 (p=0.0312) |
| bike_hour | 6 | X_A5C | +81.8 [+41.5,+122.0] (choe_ramdas_eb+front) |  | +94.8 (model_picker_adapter) | 0/6 (p=0.0312) |
| bike_hour | 6 | D1 | -0.6 [-3.2,+2.0] (choe_ramdas_eb+front) | +12.4 [+7.2,+17.6] | +12.4 (model_picker_adapter) | 3/6 (p=1) |
| bike_hour | 6 | D2 | -5.9 [-11.2,-0.6] (choe_ramdas_eb+front) | +4.2 [-1.8,+10.2] | +7.1 (model_picker_adapter) | 5/6 (p=0.219) |
| bike_hour | 6 | C2 | +2.6 [+0.3,+5.0] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +15.6 (model_picker_adapter) | 0/6 (p=0.0625) |
| bike_hour | 6 | C6 | +2.6 [+0.3,+5.0] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +15.6 (model_picker_adapter) | 0/6 (p=0.0625) |
| bike_hour | 6 | B2 | +24.6 [+20.0,+29.2] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +37.6 (model_picker_adapter) | 0/6 (p=0.0312) |
| bike_hour | 6 | B5 | +29.8 [+24.2,+35.4] (choe_ramdas_eb+front) | +5.2 [+3.3,+7.2] | +42.8 (model_picker_adapter) | 0/6 (p=0.0312) |
| household_power | 20 | A5b | +61.2 [+13.9,+108.6] (choe_ramdas_eb+front) |  | +75.5 (model_picker_adapter) | 6/20 (p=0.332) |
| household_power | 20 | X_A5C | +61.2 [+13.9,+108.6] (choe_ramdas_eb+front) |  | +75.5 (model_picker_adapter) | 6/20 (p=0.332) |
| household_power | 20 | D1 | -1.2 [-7.2,+4.8] (choe_ramdas_eb+front) | +13.1 [-1.2,+27.3] | +13.1 (model_picker_adapter) | 11/20 (p=0.824) |
| household_power | 20 | D2 | -7.0 [-12.9,-1.1] (choe_ramdas_eb+front) | +0.5 [-15.2,+16.1] | +7.3 (model_picker_adapter) | 13/20 (p=0.167) |
| household_power | 20 | C2 | +3.0 [-25.9,+32.0] (choe_ramdas_eb+front) | +2.0 [-27.3,+31.3] | +17.3 (model_picker_adapter) | 8/20 (p=1) |
| household_power | 20 | C6 | +4.6 [-24.1,+33.2] (choe_ramdas_eb+front) | +3.5 [-25.5,+32.6] | +18.9 (model_picker_adapter) | 8/20 (p=1) |
| household_power | 20 | B2 | -3.0 [-20.4,+14.4] (choe_ramdas_eb+front) | -1.5 [-6.1,+3.0] | +11.3 (model_picker_adapter) | 7/20 (p=0.359) |
| household_power | 20 | B5 | -0.7 [-17.4,+15.9] (choe_ramdas_eb+front) | +0.7 [-5.3,+6.7] | +13.5 (model_picker_adapter) | 8/20 (p=0.503) |
| metro | 16 | A5b | +98.8 [+28.7,+168.8] (choe_ramdas_eb+front) |  | +111.3 (model_picker_adapter) | 0/16 (p=3.05e-05) |
| metro | 16 | X_A5C | +98.8 [+28.7,+168.8] (choe_ramdas_eb+front) |  | +111.3 (model_picker_adapter) | 0/16 (p=3.05e-05) |
| metro | 16 | D1 | +0.2 [-2.4,+2.9] (choe_ramdas_eb+front) | +12.8 [+11.6,+14.0] | +12.8 (model_picker_adapter) | 6/16 (p=0.454) |
| metro | 16 | D2 | -2.5 [-4.2,-0.9] (choe_ramdas_eb+front) | +2.9 [+1.4,+4.5] | +10.0 (model_picker_adapter) | 14/16 (p=0.00418) |
| metro | 16 | C2 | +3.5 [+1.4,+5.6] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +16.0 (model_picker_adapter) | 0/16 (p=0.000244) |
| metro | 16 | C6 | +3.5 [+1.4,+5.6] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +16.0 (model_picker_adapter) | 0/16 (p=0.000244) |
| metro | 16 | B2 | +30.0 [+27.5,+32.4] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +42.5 (model_picker_adapter) | 0/16 (p=3.05e-05) |
| metro | 16 | B5 | +34.7 [+32.1,+37.4] (choe_ramdas_eb+front) | +4.8 [+4.2,+5.4] | +47.3 (model_picker_adapter) | 0/16 (p=3.05e-05) |

## Previously exposed streams (descriptive only)

| dataset | K | candidate | vs best certified | vs host | vs best uncertified | improved/K (sign p) |
|---|---|---|---|---|---|---|
| airlines | 50 | A5b | +4.5 [+1.5,+7.5] (choe_ramdas_eb) |  | -3.0 (qiu_delayed_movement) | 5/50 (p=1.41e-07) |
| airlines | 50 | X_A5C | +2.9 [-0.1,+6.0] (choe_ramdas_eb) |  | -4.6 (qiu_delayed_movement) | 11/50 (p=0.00126) |
| airlines | 50 | D1 | -1.8 [-3.6,-0.0] (choe_ramdas_eb) | -12.2 [-17.2,-7.2] | -9.3 (qiu_delayed_movement) | 36/50 (p=0.0026) |
| airlines | 50 | D2 | +1.4 [-1.4,+4.1] (choe_ramdas_eb) | -14.9 [-21.5,-8.3] | -6.1 (qiu_delayed_movement) | 26/50 (p=0.775) |
| airlines | 50 | C2 | -2.9 [-5.7,-0.1] (choe_ramdas_eb) | -4.6 [-5.7,-3.5] | -10.4 (qiu_delayed_movement) | 42/50 (p=1.16e-06) |
| airlines | 50 | C6 | -2.5 [-5.9,+1.0] (choe_ramdas_eb) | -4.1 [-6.5,-1.7] | -10.0 (qiu_delayed_movement) | 42/50 (p=1.16e-06) |
| airlines | 50 | B2 | +1.9 [+0.9,+2.9] (choe_ramdas_eb) | -0.0 [-0.1,+0.0] | -5.6 (qiu_delayed_movement) | 5/50 (p=2.5e-07) |
| airlines | 50 | B5 | +0.9 [+0.0,+1.9] (choe_ramdas_eb) | -1.0 [-1.6,-0.4] | -6.5 (qiu_delayed_movement) | 26/50 (p=0.775) |
| bank | 8 | A5b | +7.9 [-2.0,+17.8] (choe_ramdas_eb+front) |  | +2.8 (model_selector_causal) | 0/8 (p=0.0312) |
| bank | 8 | X_A5C | +6.0 [-4.4,+16.4] (choe_ramdas_eb+front) |  | +0.9 (model_selector_causal) | 2/8 (p=1) |
| bank | 8 | D1 | +1.7 [-4.5,+8.0] (choe_ramdas_eb+front) | -15.3 [-29.2,-1.4] | -3.4 (model_selector_causal) | 6/8 (p=0.125) |
| bank | 8 | D2 | +5.7 [+0.1,+11.3] (choe_ramdas_eb+front) | -11.6 [-27.7,+4.5] | +0.5 (model_selector_causal) | 0/8 (p=0.0312) |
| bank | 8 | C2 | -1.6 [-3.0,-0.2] (choe_ramdas_eb+front) | -1.9 [-3.3,-0.4] | -6.8 (model_selector_causal) | 7/8 (p=0.0156) |
| bank | 8 | C6 | -1.6 [-3.0,-0.2] (choe_ramdas_eb+front) | -1.9 [-3.3,-0.4] | -6.8 (model_selector_causal) | 7/8 (p=0.0156) |
| bank | 8 | B2 | +7.9 [-2.0,+17.8] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +2.8 (model_selector_causal) | 0/8 (p=0.0312) |
| bank | 8 | B5 | +7.2 [-2.6,+16.9] (choe_ramdas_eb+front) | -0.8 [-1.2,-0.3] | +2.0 (model_selector_causal) | 1/8 (p=0.125) |
| criteo | 50 | A5b | +2.1 [+0.8,+3.4] (SMCS+retain-incumbent) |  | +11.5 (ryabchenko_capacity) | 4/50 (p=9.33e-09) |
| criteo | 50 | X_A5C | +2.1 [+0.8,+3.4] (SMCS+retain-incumbent) |  | +11.5 (ryabchenko_capacity) | 4/50 (p=9.33e-09) |
| criteo | 50 | D1 | -0.7 [-1.4,-0.1] (SMCS+retain-incumbent) | +5.2 [+1.9,+8.6] | +8.7 (ryabchenko_capacity) | 42/50 (p=1.16e-06) |
| criteo | 50 | D2 | -0.5 [-1.3,+0.3] (SMCS+retain-incumbent) | +2.8 [-1.9,+7.5] | +8.9 (ryabchenko_capacity) | 38/50 (p=0.000306) |
| criteo | 50 | C2 | -0.2 [-1.6,+1.2] (SMCS+retain-incumbent) | -2.1 [-2.6,-1.5] | +9.2 (ryabchenko_capacity) | 37/50 (p=0.000936) |
| criteo | 50 | C6 | -1.9 [-3.4,-0.5] (SMCS+retain-incumbent) | -3.8 [-4.4,-3.1] | +7.5 (ryabchenko_capacity) | 39/50 (p=9.02e-05) |
| criteo | 50 | B2 | +1.9 [+0.7,+3.2] (SMCS+retain-incumbent) | +0.0 [+0.0,+0.0] | +11.3 (ryabchenko_capacity) | 6/50 (p=9.43e-07) |
| criteo | 50 | B5 | +1.3 [+0.1,+2.5] (SMCS+retain-incumbent) | -0.6 [-0.9,-0.4] | +10.7 (ryabchenko_capacity) | 37/50 (p=0.000936) |
| elec2 | 4 | A5b | +0.1 [-8.3,+8.4] (SMCS+retain-incumbent) |  | -0.6 (ryabchenko_capacity) | 3/4 (p=0.625) |
| elec2 | 4 | X_A5C | +0.1 [-8.3,+8.4] (SMCS+retain-incumbent) |  | -0.6 (ryabchenko_capacity) | 3/4 (p=0.625) |
| elec2 | 4 | D1 | -4.5 [-5.7,-3.4] (SMCS+retain-incumbent) | -9.6 [-31.2,+12.1] | -5.2 (ryabchenko_capacity) | 4/4 (p=0.125) |
| elec2 | 4 | D2 | -9.0 [-18.2,+0.2] (SMCS+retain-incumbent) | -18.4 [-35.4,-1.5] | -9.7 (ryabchenko_capacity) | 4/4 (p=0.125) |
| elec2 | 4 | C2 | -2.0 [-8.5,+4.6] (SMCS+retain-incumbent) | -6.1 [-12.9,+0.6] | -2.7 (ryabchenko_capacity) | 3/4 (p=0.625) |
| elec2 | 4 | C6 | -1.9 [-10.1,+6.3] (SMCS+retain-incumbent) | -6.1 [-13.8,+1.6] | -2.6 (ryabchenko_capacity) | 3/4 (p=0.625) |
| elec2 | 4 | B2 | +2.6 [-3.6,+8.9] (SMCS+retain-incumbent) | +0.0 [+0.0,+0.0] | +1.9 (ryabchenko_capacity) | 1/4 (p=0.625) |
| elec2 | 4 | B5 | +2.3 [-4.1,+8.7] (SMCS+retain-incumbent) | -0.3 [-0.6,+0.0] | +1.6 (ryabchenko_capacity) | 2/4 (p=1) |
| openml_ldpa | 32 | A5b | +80.4 [+36.9,+124.0] (choe_ramdas_eb+front) |  | +109.6 (model_picker_adapter) | 5/32 (p=0.000192) |
| openml_ldpa | 32 | X_A5C | +81.7 [+38.6,+124.8] (choe_ramdas_eb+front) |  | +110.9 (model_picker_adapter) | 5/32 (p=0.000192) |
| openml_ldpa | 32 | D1 | -9.0 [-24.4,+6.4] (choe_ramdas_eb+front) | +20.2 [+14.3,+26.1] | +20.2 (model_picker_adapter) | 19/32 (p=0.377) |
| openml_ldpa | 32 | D2 | -14.4 [-30.8,+1.9] (choe_ramdas_eb+front) | +10.7 [+4.5,+16.9] | +14.8 (model_picker_adapter) | 26/32 (p=0.000535) |
| openml_ldpa | 32 | C2 | +7.8 [-2.1,+17.8] (choe_ramdas_eb+front) | +7.1 [-3.2,+17.3] | +37.0 (model_picker_adapter) | 9/32 (p=0.0614) |
| openml_ldpa | 32 | C6 | +17.4 [-3.2,+38.0] (choe_ramdas_eb+front) | +16.7 [-4.1,+37.4] | +46.6 (model_picker_adapter) | 9/32 (p=0.0614) |
| openml_ldpa | 32 | B2 | +6.4 [-15.5,+28.4] (choe_ramdas_eb+front) | +1.6 [-0.7,+3.9] | +35.6 (model_picker_adapter) | 9/32 (p=0.0201) |
| openml_ldpa | 32 | B5 | +10.6 [-12.4,+33.6] (choe_ramdas_eb+front) | +5.8 [+0.2,+11.4] | +39.8 (model_picker_adapter) | 8/32 (p=0.007) |
| rialto | 16 | A5b | +98.9 [+68.5,+129.3] (choe_ramdas_eb+front) |  | +112.8 (online_llm_picker) | 0/16 (p=3.05e-05) |
| rialto | 16 | X_A5C | +98.9 [+68.5,+129.3] (choe_ramdas_eb+front) |  | +112.8 (online_llm_picker) | 0/16 (p=3.05e-05) |
| rialto | 16 | D1 | +2.0 [+0.7,+3.3] (choe_ramdas_eb+front) | +14.0 [+13.1,+14.9] | +15.9 (online_llm_picker) | 2/16 (p=0.00418) |
| rialto | 16 | D2 | -2.5 [-3.3,-1.8] (choe_ramdas_eb+front) | +9.8 [+9.1,+10.5] | +11.4 (online_llm_picker) | 16/16 (p=3.05e-05) |
| rialto | 16 | C2 | +3.9 [+3.0,+4.7] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +17.8 (online_llm_picker) | 0/16 (p=3.05e-05) |
| rialto | 16 | C6 | +4.7 [+2.6,+6.8] (choe_ramdas_eb+front) | +0.9 [-0.8,+2.6] | +18.6 (online_llm_picker) | 0/16 (p=3.05e-05) |
| rialto | 16 | B2 | +10.9 [+10.2,+11.7] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +24.8 (online_llm_picker) | 0/16 (p=3.05e-05) |
| rialto | 16 | B5 | +10.8 [+10.1,+11.6] (choe_ramdas_eb+front) | -0.1 [-0.3,+0.1] | +24.8 (online_llm_picker) | 0/16 (p=3.05e-05) |
| spam | 1 | A5b | +65.4 [+nan,+nan] (gated_adaptive_range+front) |  | +94.6 (online_llm_picker) | 0/1 (p=1) |
| spam | 1 | X_A5C | +65.4 [+nan,+nan] (gated_adaptive_range+front) |  | +94.6 (online_llm_picker) | 0/1 (p=1) |
| spam | 1 | D1 | -4.3 [+nan,+nan] (gated_adaptive_range+front) | +20.9 [+nan,+nan] | +24.8 (online_llm_picker) | 1/1 (p=1) |
| spam | 1 | D2 | -11.8 [+nan,+nan] (gated_adaptive_range+front) | +9.8 [+nan,+nan] | +17.4 (online_llm_picker) | 1/1 (p=1) |
| spam | 1 | C2 | +0.0 [+nan,+nan] (gated_adaptive_range+front) | +0.0 [+nan,+nan] | +29.2 (online_llm_picker) | 0/1 (p=1) |
| spam | 1 | C6 | +0.0 [+nan,+nan] (gated_adaptive_range+front) | +0.0 [+nan,+nan] | +29.2 (online_llm_picker) | 0/1 (p=1) |
| spam | 1 | B2 | +16.0 [+nan,+nan] (gated_adaptive_range+front) | +0.0 [+nan,+nan] | +45.2 (online_llm_picker) | 0/1 (p=1) |
| spam | 1 | B5 | +25.9 [+nan,+nan] (gated_adaptive_range+front) | +9.9 [+nan,+nan] | +55.0 (online_llm_picker) | 0/1 (p=1) |
| uci_occupancy | 4 | A5b | +350.6 [-332.0,+1033.1] (choe_ramdas_eb+front) |  | +355.4 (model_picker_adapter) | 0/4 (p=0.25) |
| uci_occupancy | 4 | X_A5C | +350.6 [-332.0,+1033.1] (choe_ramdas_eb+front) |  | +355.4 (model_picker_adapter) | 0/4 (p=0.25) |
| uci_occupancy | 4 | D1 | +3.5 [-2.5,+9.6] (choe_ramdas_eb+front) | +8.4 [-7.1,+23.9] | +8.4 (model_picker_adapter) | 1/4 (p=0.625) |
| uci_occupancy | 4 | D2 | -1.0 [-6.3,+4.4] (choe_ramdas_eb+front) | +0.7 [-2.9,+4.4] | +3.9 (model_picker_adapter) | 3/4 (p=0.625) |
| uci_occupancy | 4 | C2 | +1.0 [-1.0,+3.0] (choe_ramdas_eb+front) | -0.5 [-1.5,+0.4] | +5.8 (model_picker_adapter) | 0/4 (p=1) |
| uci_occupancy | 4 | C6 | +1.0 [-1.0,+3.0] (choe_ramdas_eb+front) | -0.5 [-1.5,+0.4] | +5.8 (model_picker_adapter) | 0/4 (p=1) |
| uci_occupancy | 4 | B2 | +11.1 [-14.1,+36.3] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +15.9 (model_picker_adapter) | 1/4 (p=1) |
| uci_occupancy | 4 | B5 | +16.8 [-11.5,+45.0] (choe_ramdas_eb+front) | +5.7 [-0.8,+12.2] | +21.6 (model_picker_adapter) | 1/4 (p=1) |
| weather | 3 | A5b | +3.3 [-1.9,+8.5] (choe_ramdas_eb+front) |  | +25.7 (model_selector_causal) | 0/3 (p=0.5) |
| weather | 3 | X_A5C | +3.3 [-1.9,+8.5] (choe_ramdas_eb+front) |  | +25.7 (model_selector_causal) | 0/3 (p=0.5) |
| weather | 3 | D1 | -0.1 [-7.6,+7.3] (choe_ramdas_eb+front) | +13.7 [+4.1,+23.3] | +22.3 (model_selector_causal) | 2/3 (p=1) |
| weather | 3 | D2 | -3.1 [-4.9,-1.4] (choe_ramdas_eb+front) | +12.8 [+6.7,+18.9] | +19.3 (model_selector_causal) | 3/3 (p=0.25) |
| weather | 3 | C2 | +5.8 [-4.4,+16.0] (choe_ramdas_eb+front) | -0.2 [-0.7,+0.2] | +28.2 (model_selector_causal) | 1/3 (p=1) |
| weather | 3 | C6 | +3.6 [-9.8,+16.9] (choe_ramdas_eb+front) | -2.5 [-7.3,+2.4] | +26.0 (model_selector_causal) | 1/3 (p=1) |
| weather | 3 | B2 | +15.0 [-0.8,+30.8] (choe_ramdas_eb+front) | +0.0 [+0.0,+0.0] | +37.4 (model_selector_causal) | 0/3 (p=0.5) |
| weather | 3 | B5 | +18.2 [-1.4,+37.8] (choe_ramdas_eb+front) | +3.2 [-0.6,+7.1] | +40.6 (model_selector_causal) | 1/3 (p=1) |

