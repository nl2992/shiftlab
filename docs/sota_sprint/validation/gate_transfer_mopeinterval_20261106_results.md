# Deploy-gate transfer (Amendment 4) — MOPE interval-correction sensitivity

MOPE-affected policy arms are replaced by corrected same-seed replays; unaffected arms retain their registered records. This is a code-correction sensitivity, not an independent confirmation.

| gated host | vs native host, all regimes | Holm-significant best-certified comparisons | iid-null safe | null rates | real fresh vs best certified (improved/K) |
|---|---:|---:|---|---|---|
| D1 (model_picker_adapter) | +4.9 [+3.1,+6.7] | 0 | True | V_null 0.016, V_null_dep_r5 0.055, V_null_dep_r8 0.233, V_worse 0.001 | appliances +14.3 (1/6); beijing_pm25 -14.6 (11/14); bike_hour -1.2 (4/6); household_power +3.8 (9/20); metro +0.6 (6/16) |
| D2 (cams_adapter) | -1.8 [-3.6,+0.0] | 2 | True | V_null 0.014, V_null_dep_r5 0.045, V_null_dep_r8 0.226, V_worse 0.000 | appliances +1.4 (3/6); beijing_pm25 -33.2 (13/14); bike_hour -6.1 (5/6); household_power -2.8 (11/20); metro -2.7 (14/16) |
| D6-D1params:ms (model_selector_causal) | +7.4 [+5.8,+9.0] | 2 | True | V_null 0.016, V_null_dep_r5 0.049, V_null_dep_r8 0.197, V_worse 0.000 | appliances +29.2 (2/6); beijing_pm25 -6.3 (10/14); bike_hour -6.2 (4/6); household_power +2.4 (9/20); metro -1.3 (11/16) |
