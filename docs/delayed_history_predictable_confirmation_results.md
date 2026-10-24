# Delayed history-predictable bound: confirmation results

**Status:** independent, protocol-frozen confirmation; completed 2026-10-24. The estimator and betting construction are standard; this is not a novelty claim.

## Calibration gate

The candidate first passed a fresh four-cell null calibration on seed root `27504027`, with 2,000 streams per cell. Bonferroni-adjusted one-sided exact 95% upper limits were 0.637% and 0.319% for the fixed-bound arm under the exact-zero and strict-negative controls, and 3.054% and 2.231% for the eventwise-bound arm. Every limit was at most 5%, and all request-budget and eventwise support invariants passed.

## Independent harm confirmation

The confirmation used 2,000 paired streams per harm dose and arm (16,000 stream-arm rows total), seed root `27604027`, horizon 2,400, onset index 1,200, 12-event deterministic outcome-independent label delay, `q_min=0.05`, `q_max=0.80`, and a 480-label request cap. CUDA generated each scenario's random streams; a checksum-tested NumPy event-order replay performed the sequential update.

| Harm dose | Fixed detection | Eventwise detection | Paired difference (95% CI) | Eventwise onset reached | Mean label difference | Mean event-time delay if detected (fixed / eventwise) | Mean wall-time delay if detected (fixed / eventwise) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.04 | 0.30% | 0.10% | −0.20 pp [−0.45, 0.00] pp | 98.00% | −126.19 | 963.7 / 1,074.5 | 975.5 / 1,086.5 |
| 0.20 | 0.70% | 1.10% | +0.40 pp [−0.10, +0.95] pp | 97.95% | −129.06 | 888.2 / 754.5 | 900.2 / 766.5 |
| 0.40 | 2.35% | 5.25% | +2.90 pp [+1.95, +3.85] pp | 98.80% | −135.02 | 945.6 / 698.4 | 957.4 / 710.3 |
| 0.60 | 6.50% | 15.95% | +9.45 pp [+7.80, +11.15] pp | 98.40% | −134.74 | 986.1 / 778.5 | 997.9 / 790.4 |

The primary equal-weight macro detection gain was **+3.14 percentage points**, with paired stream-cluster 95% bootstrap interval **[+2.64, +3.63] points**. Mean label use fell by **131.25 labels per stream** (95% interval [−133.39, −129.14]); evaluator-known cumulative expected harm exposure fell by **15.94 cost units** (95% interval [−17.66, −14.25]). The independent calibration and all three frozen retention gates passed.

These results support the history-only eventwise-bound system over its fixed-bound comparator for this registered iid synthetic design with deterministic, outcome-independent 12-event delay. Benefit increased with harm dose; the eventwise arm had slightly lower onset reach and a small observed false-escalation rate on null controls (1.5%–2.2%). It is not universally superior. The experiment does not validate serial dependence, informative or missing feedback, adaptive action changes, or interventions that alter outcomes. The arrival-filtration argument depends on the iid process and outcome-independent fixed delay. A separate proof and experiment are required before extending the claim.

## Reproducibility artifacts

- Frozen selected-configuration calibration: [`delayed_history_predictable_selected_calibration_protocol.md`](delayed_history_predictable_selected_calibration_protocol.md), [`outputs/delayed_history_predictable_selected_calibration_2000/reports/calibration_results.md`](../outputs/delayed_history_predictable_selected_calibration_2000/reports/calibration_results.md)
- Frozen confirmation: [`delayed_history_predictable_confirmation_protocol.md`](delayed_history_predictable_confirmation_protocol.md)
- Runner: [`../scripts/confirm_delayed_history_predictable_bounds.py`](../scripts/confirm_delayed_history_predictable_bounds.py)
- Stream-level Parquet: [`../outputs/delayed_history_predictable_confirmation_2000/metrics/stream_metrics.parquet`](../outputs/delayed_history_predictable_confirmation_2000/metrics/stream_metrics.parquet)
- Dose results: [`../outputs/delayed_history_predictable_confirmation_2000/metrics/harm_dose_results.csv`](../outputs/delayed_history_predictable_confirmation_2000/metrics/harm_dose_results.csv)
- Operating characteristics: [`../outputs/delayed_history_predictable_confirmation_2000/metrics/operational_characteristics.csv`](../outputs/delayed_history_predictable_confirmation_2000/metrics/operational_characteristics.csv)
- Primary result and checksums: [`../outputs/delayed_history_predictable_confirmation_2000/reports/primary_result.json`](../outputs/delayed_history_predictable_confirmation_2000/reports/primary_result.json), [`../outputs/delayed_history_predictable_confirmation_2000/reports/manifest.json`](../outputs/delayed_history_predictable_confirmation_2000/reports/manifest.json)

No research figure was generated because PaperBanana is unavailable in the active environment.
