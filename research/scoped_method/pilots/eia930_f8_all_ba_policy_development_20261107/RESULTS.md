# EIA-930 F8 policy development results

**Status:** completed development replay; not independent confirmation.

Rows: 6480; episodes: 81; BAs: 11; policy seeds per episode: 5.
Maximum absolute net-cost identity residual: 1.15e-14.

## Mean cost decomposition (equal weight per BA, episode and policy seed)

| Policy | Net | Predictive loss | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks | First promotion event |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cams_adapter | 29.83 | 22.57 | 36.30 | 1.81 | 1.09 | 5.44 | 0.95 | 0.14 | 359.6 |
| model_selector_causal | 30.67 | 22.18 | 72.48 | 3.62 | 0.97 | 4.86 | 0.88 | 0.09 | 327.2 |
| model_picker_adapter | 30.69 | 24.32 | 15.26 | 0.76 | 1.12 | 5.61 | 0.96 | 0.16 | 372.2 |
| gong_zhang_paid_obs | 31.18 | 23.54 | 72.15 | 3.61 | 0.81 | 4.03 | 0.80 | 0.01 | 348.6 |
| online_llm_picker | 31.28 | 23.11 | 43.28 | 2.16 | 1.20 | 6.01 | 1.00 | 0.20 | 344.8 |
| qiu_delayed_movement | 35.39 | 27.40 | 72.16 | 3.61 | 0.88 | 4.39 | 0.83 | 0.04 | 397.9 |
| variance_min_ipw | 35.57 | 22.46 | 158.11 | 7.91 | 1.04 | 5.21 | 0.92 | 0.12 | 330.4 |
| SMCS+retain-incumbent | 38.75 | 31.31 | 72.19 | 3.61 | 0.77 | 3.83 | 0.77 | 0.00 | 567.8 |
| economic_replacement | 39.14 | 32.13 | 72.23 | 3.61 | 0.68 | 3.41 | 0.68 | 0.00 | 438.5 |
| PFA-SR:gated_deployment | 40.40 | 33.00 | 74.14 | 3.71 | 0.74 | 3.69 | 0.74 | 0.00 | 610.5 |
| xu_acquisition_only | 40.99 | 33.80 | 69.94 | 3.50 | 0.74 | 3.70 | 0.74 | 0.00 | 630.7 |
| gated_adaptive_range | 44.24 | 39.66 | 23.10 | 1.15 | 0.69 | 3.43 | 0.69 | 0.00 | 764.9 |
| gated_deployment | 45.17 | 40.54 | 23.89 | 1.19 | 0.69 | 3.43 | 0.69 | 0.00 | 781.7 |
| E_rb:gated_deployment | 45.21 | 38.04 | 74.16 | 3.71 | 0.69 | 3.47 | 0.69 | 0.00 | 718.2 |
| rmm:gated_deployment+RMM | 45.21 | 38.04 | 74.16 | 3.71 | 0.69 | 3.47 | 0.69 | 0.00 | 718.2 |
| CONTROL_never_switch | 78.34 | 78.34 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | — |

## Frozen candidate contrasts

### PFA-SR minus `cams_adapter`

Equal-BA mean difference: **+10.57** (hierarchical BA-then-episode 95% interval [+7.93, +12.80]); BAs meeting ≥5-unit savings with their episode interval below zero: 0/11.

| BA | Episodes | Candidate − comparator | 95% episode-bootstrap interval |
|---|---:|---:|---:|
| AZPS | 8 | +8.88 | [+2.53, +15.24] |
| BANC | 7 | +9.14 | [+1.35, +15.98] |
| EPE | 8 | +8.04 | [+2.66, +13.18] |
| ERCO | 8 | +14.57 | [+13.48, +15.74] |
| FMPP | 6 | +11.41 | [+5.21, +16.39] |
| FPC | 8 | +14.12 | [+11.53, +16.64] |
| MISO | 7 | +13.16 | [+8.45, +16.53] |
| NEVP | 8 | +9.03 | [+3.85, +14.06] |
| NYIS | 8 | +12.49 | [+7.10, +17.12] |
| SWPP | 8 | +11.73 | [+7.93, +15.01] |
| TIDC | 5 | +3.70 | [-3.15, +11.74] |

### PFA-SR minus `rmm:gated_deployment+RMM`

Equal-BA mean difference: **-4.82** (hierarchical BA-then-episode 95% interval [-5.78, -3.72]); BAs meeting ≥5-unit savings with their episode interval below zero: 5/11.

| BA | Episodes | Candidate − comparator | 95% episode-bootstrap interval |
|---|---:|---:|---:|
| AZPS | 8 | -4.74 | [-7.33, -2.00] |
| BANC | 7 | -4.16 | [-7.25, -1.60] |
| EPE | 8 | -4.83 | [-7.46, -2.19] |
| ERCO | 8 | -6.30 | [-7.02, -5.47] |
| FMPP | 6 | -4.55 | [-8.38, -0.02] |
| FPC | 8 | -6.25 | [-7.47, -4.79] |
| MISO | 7 | -5.57 | [-7.77, -3.00] |
| NEVP | 8 | -3.08 | [-5.86, -0.30] |
| NYIS | 8 | -5.10 | [-7.33, -2.69] |
| SWPP | 8 | -5.70 | [-6.76, -4.00] |
| TIDC | 5 | -2.72 | [-5.52, +0.00] |

## Decision

Frozen development gate: **FAIL**.
The lowest-cost frozen panel baseline is `cams_adapter` at 29.83; candidate cost is 40.40 (difference +10.57).

This result is development evidence only. It does not validate real field utility, null error, source-level transfer, or a novel method claim.

## Limitations

- 2022-2023 is development data; BA selection used the same period's frozen profile screen.
- EIA history is revised and one-hour feedback release is simulated.
- All 11 BAs are correlated under one data provider; hierarchical intervals are not source-level uncertainty.
- PFA-SR is published prior art; no null guarantee is established for these serial streams.
- The cost contract is hypothetical Failure Atlas units, not calibrated electricity-market utility.
