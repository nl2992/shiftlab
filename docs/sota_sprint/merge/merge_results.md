# P1 x P2 merge (Amendment 6): **NOT MET** (primary M_LRMD_SUI)

## M_LRMD_SUI: HM1 validity FAIL; HM2 late benefit FAIL

Nulls (1000 seeds): V_null 0.016 (ub 0.026); V_null_dep_r5 0.013 (ub 0.022); V_null_dep_r8 0.006 (ub 0.013); V_worse 0.001 (ub 0.006); W_null_dep_r9 0.002 (ub 0.007); W_null_dep_r95 0.008 (ub 0.016)

Twin-null real (split bootstrap): appliances 0.097 [0.053,0.144]; beijing_pm25 0.023 [0.008,0.038]; bike_hour 0.100 [0.050,0.153]; household_power 0.049 [0.028,0.074]; metro 0.000 [0.000,0.000]

* V_late_600: vs A5b -16.4 [-21.9,-10.9]; vs best certified -5.8 [-10.5,-1.1] (xu_acquisition_only, Holm p=0.0178); retained fraction of iid-RMM gain 0.221
* W_late_1000: vs A5b -6.1 [-8.3,-3.9]; vs best certified -2.0 [-5.0,+1.1] (xu_acquisition_only, Holm p=0.105); retained fraction of iid-RMM gain 0.132
* stationary vs A5b / best certified: V_better_a +10.0 [+1.4,+18.6] / +12.9 [+3.8,+22.1]; V_better_b +5.9 [+2.6,+9.2] / +11.1 [+7.9,+14.3]; V_better_c +34.2 [+24.0,+44.5] / +33.4 [+22.3,+44.6]; V_near +1.8 [-2.2,+5.8] / +3.2 [-1.9,+8.3]
* reversal/recurrent vs A5b: V_reversal_1000 -0.5 [-6.6,+5.5]; W_reversal_700 -17.2 [-25.0,-9.3]; V_recurrent +8.6 [+4.5,+12.7]
* fresh real vs A5b / best certified (improved/K): appliances -50.4 / +206.9 (0/6); beijing_pm25 -6.7 / +67.8 (2/14); bike_hour -9.6 / +72.5 (0/6); household_power +4.4 / +70.7 (6/20); metro +35.5 / +134.3 (0/16)

## M_RMMSUI_A5b: HM1 validity FAIL; HM2 late benefit FAIL

Nulls (1000 seeds): V_null 0.006 (ub 0.013); V_null_dep_r5 0.004 (ub 0.010); V_null_dep_r8 0.005 (ub 0.012); V_worse 0.000 (ub 0.004); W_null_dep_r9 0.004 (ub 0.010); W_null_dep_r95 0.002 (ub 0.007)

Twin-null real (split bootstrap): appliances 0.056 [0.019,0.097]; beijing_pm25 0.019 [0.005,0.037]; bike_hour 0.083 [0.042,0.133]; household_power 0.035 [0.017,0.055]; metro 0.000 [0.000,0.000]

* V_late_600: vs A5b +0.6 [-0.2,+1.4]; vs best certified +11.2 [+5.9,+16.5] (xu_acquisition_only, Holm p=1); retained fraction of iid-RMM gain -0.429
* W_late_1000: vs A5b +0.0 [+0.0,+0.0]; vs best certified +4.2 [+2.2,+6.1] (xu_acquisition_only, Holm p=1); retained fraction of iid-RMM gain -0.278
* stationary vs A5b / best certified: V_better_a +0.0 [-0.1,+0.1] / +2.9 [-3.5,+9.3]; V_better_b -1.2 [-3.0,+0.7] / +4.0 [+2.1,+5.9]; V_better_c +0.0 [+0.0,+0.0] / -0.8 [-4.6,+3.0]; V_near +0.0 [-0.0,+0.0] / +1.4 [-3.7,+6.5]
* reversal/recurrent vs A5b: V_reversal_1000 +1.2 [-0.7,+3.1]; W_reversal_700 +2.9 [-1.6,+7.3]; V_recurrent -1.4 [-3.9,+1.1]
* fresh real vs A5b / best certified (improved/K): appliances -5.0 / +252.4 (0/6); beijing_pm25 -0.5 / +74.1 (2/14); bike_hour +3.7 / +85.8 (0/6); household_power +5.0 / +71.2 (3/20); metro -2.6 / +96.2 (0/16)

## M_RMMSUI_gar: HM1 validity FAIL; HM2 late benefit FAIL

Nulls (1000 seeds): V_null 0.006 (ub 0.013); V_null_dep_r5 0.001 (ub 0.006); V_null_dep_r8 0.004 (ub 0.010); V_worse 0.000 (ub 0.004); W_null_dep_r9 0.017 (ub 0.027); W_null_dep_r95 0.068 (ub 0.085)

Twin-null real (split bootstrap): appliances 0.256 [0.181,0.333]; beijing_pm25 0.065 [0.040,0.093]; bike_hour 0.100 [0.050,0.156]; household_power 0.092 [0.063,0.121]; metro 0.003 [0.000,0.009]

* V_late_600: vs A5b -7.2 [-11.6,-2.8]; vs best certified +3.4 [-1.4,+8.2] (xu_acquisition_only, Holm p=1); retained fraction of iid-RMM gain -0.131
* W_late_1000: vs A5b -0.8 [-1.7,+0.0]; vs best certified +3.3 [+1.2,+5.4] (xu_acquisition_only, Holm p=1); retained fraction of iid-RMM gain -0.221
* stationary vs A5b / best certified: V_better_a +12.1 [+3.6,+20.6] / +15.0 [+6.2,+23.8]; V_better_b +5.3 [+2.3,+8.2] / +10.4 [+8.0,+12.9]; V_better_c +35.7 [+25.9,+45.5] / +34.9 [+24.5,+45.4]; V_near +2.2 [-1.4,+5.8] / +3.6 [-1.6,+8.8]
* reversal/recurrent vs A5b: V_reversal_1000 +4.3 [-0.8,+9.3]; W_reversal_700 -12.5 [-20.4,-4.6]; V_recurrent +6.6 [+3.4,+9.8]
* fresh real vs A5b / best certified (improved/K): appliances -111.4 / +146.0 (0/6); beijing_pm25 -21.4 / +53.2 (2/14); bike_hour -20.4 / +61.7 (0/6); household_power -33.0 / +33.3 (5/20); metro -38.0 / +60.8 (0/16)

