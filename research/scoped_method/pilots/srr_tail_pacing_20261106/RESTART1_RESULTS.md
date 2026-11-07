# Restarted E-SR slower-pacing screen results

Candidate is an existing `k=0.5` acquisition configuration, not a new detector.

- Calibration null: 20/1000 promotions (2.000%); one-sided 95% Wilson upper 2.8682%; mean labels 197.78; mean net cost 369.90; records SHA-256 `6132e89f98f7e6db32e14c7ad99f7a404f57da08604b7e73b5748f918dc6b7b9`.
- Independent evaluation null: 20/1000 promotions (2.000%); one-sided 95% Wilson upper 2.8682%; mean labels 197.77; mean net cost 369.35; records SHA-256 `cb98f36d27d52a5322027f78d3ac541edddf540157977e8fb6aa98c378f3297a`.

## Candidate cost decomposition by regime

| Regime | Loss | Label expense | Switch expense | Net | Labels | Switches | Promoted | Rollbacks | Median promotion event |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `F0_better` | 375.96 | 9.91 | 4.30 | 390.17 | 198.18 | 0.86 | 86/100 | 0.00 | 1186.0 |
| `F1_late_800` | 351.46 | 9.89 | 4.70 | 366.05 | 197.76 | 0.94 | 94/100 | 0.00 | 1464.5 |
| `F3_reversal_1200` | 388.17 | 9.87 | 7.80 | 405.84 | 197.32 | 1.56 | 90/100 | 0.66 | 713.0 |
| `F3_reversal_800` | 366.42 | 9.88 | 6.25 | 382.55 | 197.70 | 1.25 | 63/100 | 0.62 | 660.0 |

## Paired net-cost contrasts

### `F0_better`


Paired candidate-minus-comparator net-cost differences, per 1,000 events, `F0_better`:
- `E_srrSR:gated_deployment`: +10.92 [+7.92, +13.92], n=100.
- `CONTROL_never_switch`: -14.52 [-17.47, -11.56], n=100.

### `F1_late_800`


Paired candidate-minus-comparator net-cost differences, per 1,000 events, `F1_late_800`:
- `E_srrSR:gated_deployment`: +1.69 [-0.51, +3.90], n=100.
- `PFA-SR:gated_deployment`: -16.18 [-18.24, -14.11], n=100.
- `rmm:gated_deployment+RMM`: -14.33 [-16.65, -12.01], n=100.
- `E_rb:gated_deployment`: -14.33 [-16.65, -12.01], n=100.
- `E_swcert`: -15.83 [-17.86, -13.80], n=100.
- `gated_adaptive_range+front`: -16.61 [-18.73, -14.49], n=100.
- `qiu_delayed_movement`: +12.49 [+10.77, +14.22], n=100.
- `gong_zhang_paid_obs`: +9.18 [+7.02, +11.34], n=100.
- `CONTROL_never_switch`: -11.62 [-13.74, -9.50], n=100.

### `F3_reversal_1200`


Paired candidate-minus-comparator net-cost differences, per 1,000 events, `F3_reversal_1200`:
- `E_srrSR:gated_deployment`: +3.25 [+0.32, +6.18], n=100.
- `CONTROL_never_switch`: +15.02 [+12.90, +17.14], n=100.

### `F3_reversal_800`


Paired candidate-minus-comparator net-cost differences, per 1,000 events, `F3_reversal_800`:
- `E_srrSR:gated_deployment`: -3.83 [-7.79, +0.13], n=100.
- `CONTROL_never_switch`: +20.04 [+17.26, +22.82], n=100.

## Interpretation and limitations

The primary `F1_late_800` contrast to default E-SR is +1.69 per 1,000 [−0.51,+3.90], so the candidate does not clear its savings gate. It also fails the adverse-reversal cost gates: on `F3_reversal_800` its excess cost is +20.04/1,000 [+17.26,+22.82] versus never-switch; on `F3_reversal_1200` it is +15.02/1,000 [+12.90,+17.14]. The raw runner records promotion time and rollback count but not rollback event time. Qiu and Gong are common-contract ports without the same safety guarantees as certificate/restart baselines. This is synthetic development evidence only.

Alternative records SHA-256: `2576b7c4faef66fd2bae23c036a0c2743f3c519782f6d43197cde5f8e1242db2`. Manifest git revision: `3fd8443c69a0e8de7e4478ad01c620920b927cfc`.
