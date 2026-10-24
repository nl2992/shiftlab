# Independent confirmation: history-predictable query bound

This registered CUDA/CPU confirmation used 4,000 paired streams per scenario, a 2400-event horizon, alpha 0.05, and a 20% hard label cap. The seed block begins at 27104027 and is disjoint from the development block ending at 27104026.

The sole primary harm estimand is the stream-paired, equal-weight mean detection-rate difference for the four registered doses (delta 0.04, 0.20, 0.40, 0.60), comparing q_min=0.05 history-predictable against q_min=0.05 fixed-bound evidence-directed querying. Retention requires the two-sided 95% paired-bootstrap lower limit to exceed +2 percentage points, the two-sided 95% upper limit for the label-count difference to be no greater than zero, and every simultaneous calibration upper limit below 5%.

The exact one-sided null limits use Bonferroni alpha 0.05/6 across the two nonpositive-mean controls and three arms. A strict negative control has an expected paired-cost contrast of -0.20 after event 1200. These Monte Carlo limits check this simulator and implementation; the mathematical guarantee still depends on the stated conditional-mean null and predictable q.

## Calibration

| scenario                       | arm                            |   streams |   false_escalations |   false_rate |   simultaneous_one_sided_95_upper |   per_cell_alpha | passes_5pct_upper_limit   |   mean_labels |   mean_events_processed |
|:-------------------------------|:-------------------------------|----------:|--------------------:|-------------:|----------------------------------:|-----------------:|:--------------------------|--------------:|------------------------:|
| mixed_sign_exact_marginal_null | evidence_qmin_0.05_fixed       |      4000 |                   1 |       0.0003 |                            0.0017 |           0.0083 | True                      |      297.1190 |               2399.8088 |
| mixed_sign_exact_marginal_null | evidence_qmin_0.05_predictable |      4000 |                  68 |       0.0170 |                            0.0225 |           0.0083 | True                      |      167.1560 |               2369.1820 |
| mixed_sign_exact_marginal_null | uniform_q020                   |      4000 |                  61 |       0.0152 |                            0.0205 |           0.0083 | True                      |      467.3290 |               2335.9662 |
| strict_negative_control        | evidence_qmin_0.05_fixed       |      4000 |                   0 |       0.0000 |                            0.0012 |           0.0083 | True                      |      285.9697 |               2399.9255 |
| strict_negative_control        | evidence_qmin_0.05_predictable |      4000 |                  59 |       0.0147 |                            0.0200 |           0.0083 | True                      |      161.7217 |               2370.3102 |
| strict_negative_control        | uniform_q020                   |      4000 |                  55 |       0.0138 |                            0.0188 |           0.0083 | True                      |      467.4880 |               2336.7387 |

## Harm dose response

| scenario                   |   harm_effect |   fixed_detection_rate |   predictable_detection_rate |   paired_detection_difference |   paired_detection_ci95_low |   paired_detection_ci95_high |   fixed_pre_onset_escalation_rate |   predictable_pre_onset_escalation_rate |   paired_label_difference |   paired_label_ci95_low |   paired_label_ci95_high |   paired_exposure_cost_difference |   paired_exposure_cost_ci95_low |   paired_exposure_cost_ci95_high |
|:---------------------------|--------------:|-----------------------:|-----------------------------:|------------------------------:|----------------------------:|-----------------------------:|----------------------------------:|----------------------------------------:|--------------------------:|------------------------:|-------------------------:|----------------------------------:|--------------------------------:|---------------------------------:|
| high_cost_local_harm_d0.04 |        0.0400 |                 0.0008 |                       0.0030 |                        0.0022 |                      0.0005 |                       0.0043 |                            0.0000 |                                  0.0143 |                 -131.1267 |               -134.0255 |                -128.1731 |                           -0.7480 |                         -0.9402 |                          -0.5783 |
| high_cost_local_harm_d0.20 |        0.2000 |                 0.0047 |                       0.0158 |                        0.0110 |                      0.0073 |                       0.0150 |                            0.0000 |                                  0.0143 |                 -134.6455 |               -137.7335 |                -131.6037 |                           -4.8513 |                         -5.8513 |                          -3.8960 |
| high_cost_local_harm_d0.40 |        0.4000 |                 0.0187 |                       0.0615 |                        0.0428 |                      0.0352 |                       0.0505 |                            0.0000 |                                  0.0143 |                 -137.1460 |               -140.2753 |                -133.9825 |                          -16.6771 |                        -19.0975 |                         -14.3247 |
| high_cost_local_harm_d0.60 |        0.6000 |                 0.0628 |                       0.1648 |                        0.1020 |                      0.0900 |                       0.1143 |                            0.0000 |                                  0.0143 |                 -138.9143 |               -142.0329 |                -135.7927 |                          -46.6319 |                        -51.0062 |                         -42.3157 |

Dose-level paired 95% bootstrap intervals are descriptive secondary analyses and are not adjusted across doses.

## Primary result

- Equal-weight paired detection difference: 0.0395 (95% paired-bootstrap CI (0.0346875, 0.04425)).
- Paired label difference: -135.46 (95% paired-bootstrap CI (-138.37811875, -132.52164531250003)).
- Paired evaluator exposure-cost difference: -17.23 (95% paired-bootstrap CI (-19.063627625, -15.496215562500002)).
- Calibration gate: True; overall retention rule: True.

Evaluator exposure assumes the system mitigates immediately after escalation. It is a synthetic expected-cost accounting quantity, not observed real-world harm prevented. Dose-specific comparisons are secondary and should not be used to override a failed primary result.

This confirmation tests only independent synthetic events, immediate randomized label feedback, a frozen current/reference action pair, and a history-only propensity. It does not validate serial dependence, delayed or informative feedback, policy adaptation, repeated-candidate selection, or interventions that alter outcomes. A passing result would support this registered benchmark only and would not establish novelty or universal superiority.

No figure was generated: PaperBanana was unavailable in this environment, and project guidance requires it for research visuals.

Reproduce with:

```powershell
uv run python scripts/confirm_history_predictable_query_bounds.py --streams 4000 --seed 27104027 --device cuda --output outputs/history_predictable_bound_confirmation
```
