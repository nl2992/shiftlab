# EIA-930 F8 2026 temporal confirmation

Tested all 11 BAs with 17 complete episodes and 25 methods over five paired policy seeds.

Primary fixed challenger minus CAMS: **-12.239** net-cost units per episode; hierarchical paired 95% interval [-21.231, -7.218]. Frozen CAMS gate pass: **True**.

Lowest-cost registered comparator by point mean: `online_llm_picker` (61.797). Candidate minus selected best comparator: -9.191; selection-aware bootstrap interval [-13.958, -4.555]. Gate pass: **True**.

## Method summary

| Method | Net | Predictive loss | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixed_challenger | 52.606 | 47.606 | 0.0 | 0.00 | 1.00 | 5.00 | 1.00 | 0.00 |
| online_llm_picker | 61.797 | 49.830 | 58.4 | 2.92 | 1.81 | 9.05 | 1.37 | 0.44 |
| model_picker_adapter | 62.044 | 51.945 | 27.1 | 1.36 | 1.75 | 8.74 | 1.34 | 0.41 |
| gong_zhang_paid_obs | 63.027 | 50.579 | 127.8 | 6.39 | 1.21 | 6.06 | 1.11 | 0.11 |
| cams_adapter | 64.845 | 49.979 | 65.8 | 3.29 | 2.32 | 11.58 | 1.60 | 0.71 |
| variance_min_ipw | 66.011 | 49.252 | 170.6 | 8.53 | 1.65 | 8.23 | 1.25 | 0.39 |
| model_selector_causal | 66.020 | 50.561 | 127.4 | 6.37 | 1.82 | 9.09 | 1.36 | 0.45 |
| qiu_delayed_movement | 68.429 | 54.476 | 127.2 | 6.36 | 1.52 | 7.59 | 1.19 | 0.33 |
| SMCS+retain-incumbent | 69.730 | 59.264 | 127.5 | 6.38 | 0.82 | 4.09 | 0.82 | 0.00 |
| economic_replacement | 69.845 | 59.018 | 127.4 | 6.37 | 0.89 | 4.45 | 0.89 | 0.00 |
| PFA-SR:gated_adaptive_range | 72.043 | 61.412 | 130.8 | 6.54 | 0.82 | 4.09 | 0.82 | 0.00 |
| PFA-SR:gated_deployment | 72.078 | 61.442 | 130.9 | 6.54 | 0.82 | 4.09 | 0.82 | 0.00 |
| gated_adaptive_range+front | 72.352 | 66.167 | 41.9 | 2.09 | 0.82 | 4.09 | 0.82 | 0.00 |
| xu_acquisition_only | 73.491 | 63.191 | 123.3 | 6.16 | 0.83 | 4.14 | 0.83 | 0.00 |
| gated_adaptive_range | 76.299 | 70.048 | 43.2 | 2.16 | 0.82 | 4.09 | 0.82 | 0.00 |
| E_srr:gated_deployment | 76.302 | 65.661 | 131.0 | 6.55 | 0.82 | 4.09 | 0.82 | 0.00 |
| gated_deployment | 77.451 | 71.167 | 43.9 | 2.19 | 0.82 | 4.09 | 0.82 | 0.00 |
| E_rb:gated_adaptive_range+front | 77.575 | 66.848 | 132.7 | 6.64 | 0.82 | 4.09 | 0.82 | 0.00 |
| rmm:gated_deployment+RMM | 77.936 | 67.297 | 131.0 | 6.55 | 0.82 | 4.09 | 0.82 | 0.00 |
| E_rb:gated_deployment | 77.936 | 67.297 | 131.0 | 6.55 | 0.82 | 4.09 | 0.82 | 0.00 |
| rmm:gated_adaptive_range+RMM | 78.009 | 67.373 | 130.9 | 6.55 | 0.82 | 4.09 | 0.82 | 0.00 |
| E_rb:gated_adaptive_range | 78.351 | 67.627 | 130.8 | 6.54 | 0.84 | 4.18 | 0.82 | 0.02 |
| E_srrSR:gated_deployment | 78.453 | 67.815 | 130.9 | 6.55 | 0.82 | 4.09 | 0.82 | 0.00 |
| CONTROL_never_switch | 135.652 | 135.652 | 0.0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| fixed_incumbent | 135.652 | 135.652 | 0.0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## BA-level results

| BA | Candidate net | CAMS net | Best published panel method | Candidate labels | Candidate switches |
|---|---:|---:|---|---:|---:|
| AZPS | 75.00 | 89.39 | online_llm_picker: 97.29 | 0.0 | 1.0 |
| BANC | 46.00 | 53.84 | online_llm_picker: 53.21 | 0.0 | 1.0 |
| EPE | 32.00 | 39.04 | online_llm_picker: 34.25 | 0.0 | 1.0 |
| ERCO | 61.67 | 75.11 | online_llm_picker: 70.24 | 0.0 | 1.0 |
| FMPP | 134.50 | 178.07 | online_llm_picker: 162.88 | 0.0 | 1.0 |
| FPC | 29.50 | 34.17 | online_llm_picker: 34.67 | 0.0 | 1.0 |
| MISO | 47.00 | 51.47 | online_llm_picker: 51.61 | 0.0 | 1.0 |
| NEVP | 63.00 | 74.24 | online_llm_picker: 75.15 | 0.0 | 1.0 |
| NYIS | 39.00 | 44.97 | online_llm_picker: 42.34 | 0.0 | 1.0 |
| SWPP | 27.00 | 42.42 | online_llm_picker: 29.50 | 0.0 | 1.0 |
| TIDC | 24.00 | 30.57 | online_llm_picker: 28.63 | 0.0 | 1.0 |

## Integrity and limitations

All 2,125 policy-episode records passed the pathwise label cap and cost identity check; maximum residual 0. Source/feature chronology and simulated delay details are in `PROTOCOL_V2.md` and `PREFLIGHT.json`.

This is one provider and a single partial year. EIA values are revised, label release at one hour is simulated, and costs are hypothetical. Seventeen complete episodes were available, with one to three per BA. This cannot establish cross-provider generalization. Four episode-level fixed-challenger rows were exposed by tail commands during run monitoring; no design, policy or protocol choice changed after those peeks.
