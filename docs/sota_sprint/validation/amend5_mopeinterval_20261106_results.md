# Amendment 5, HC after MOPE interval correction (same-seed sensitivity): **PASS**

MOPE-affected policy arms are replaced by their corrected same-seed replays; unaffected arms retain their registered records.
Fresh seeds 2026110611 (100) / nulls 2026110612 (1000).

| host | (a) family vs host | (b) late vs registered comparator pool (Holm p) | (c) iid safe | reversal_1000 / reversal_700 / recurrent vs host | rho .8 / .95 null |
|---|---|---|---|---|---|
| gated_deployment | -41.4 [-43.8,-39.0] | V_late_600 -25.6 [-30.6,-20.6] vs xu_acquisition_only (Holm p=4.21e-16); W_late_1000 -18.9 [-23.1,-14.8] vs xu_acquisition_only (Holm p=6.62e-14) | True | +30.0 / +31.9 / +0.1 | 0.145 / 0.713 |
| discern_style | -47.2 [-49.8,-44.6] | V_late_600 -30.3 [-35.4,-25.3] vs xu_acquisition_only (Holm p=5.44e-20); W_late_1000 -14.6 [-18.9,-10.3] vs xu_acquisition_only (Holm p=8.38e-10) | True | +32.6 / +35.1 / +0.2 | 0.124 / 0.705 |
| SMCS+retain-incumbent | -14.5 [-17.1,-11.9] | V_late_600 -22.3 [-27.5,-17.1] vs xu_acquisition_only (Holm p=7.5e-13); W_late_1000 -18.5 [-23.3,-13.7] vs xu_acquisition_only (Holm p=2.6e-11) | True | -8.6 / -19.6 / +12.7 | 0.182 / 0.723 |
| gated_adaptive_range | -32.0 [-34.5,-29.6] | V_late_600 -24.0 [-29.2,-18.8] vs xu_acquisition_only (Holm p=3.51e-14); W_late_1000 -17.6 [-22.1,-13.0] vs xu_acquisition_only (Holm p=2.6e-11) | True | +3.0 / +18.1 / +6.2 | 0.139 / 0.705 |

## Strict published-certificate pool sensitivity

Only `bench.CERTIFIED_PUBLISHED` methods are eligible here; Xu acquisition and internal QCE/Choe–Ramdas ports are excluded. Holm adjustment covers all 8 host × late-regime contrasts, but not the same-sample selection of the lowest-mean comparator from this pool. Treat these as descriptive sensitivity results, not confirmatory SOTA evidence.

| host | regime | contrast vs strict-pool best | Holm p |
|---|---|---:|---:|
| gated_deployment | V_late_600 | -44.5 [-49.7,-39.4] vs discern_design_floor | 1.25e-30 |
| gated_deployment | W_late_1000 | -22.7 [-27.4,-18.0] vs gated_adaptive_range+front | 4.21e-15 |
| discern_style | V_late_600 | -49.3 [-54.0,-44.6] vs discern_design_floor | 1.08e-36 |
| discern_style | W_late_1000 | -18.4 [-22.7,-14.0] vs gated_adaptive_range+front | 2.86e-13 |
| SMCS+retain-incumbent | V_late_600 | -41.3 [-46.3,-36.3] vs discern_design_floor | 3.94e-29 |
| SMCS+retain-incumbent | W_late_1000 | -22.3 [-27.1,-17.4] vs gated_adaptive_range+front | 2e-14 |
| gated_adaptive_range | V_late_600 | -43.0 [-48.1,-37.8] vs discern_design_floor | 1.82e-29 |
| gated_adaptive_range | W_late_1000 | -21.3 [-26.2,-16.4] vs gated_adaptive_range+front | 1.66e-13 |
