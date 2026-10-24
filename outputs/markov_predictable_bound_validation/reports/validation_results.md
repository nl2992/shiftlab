# Markov volatility validation of history-predictable query bounds

This CUDA synthetic validation used 4,000 streams per scenario, seed range 27108027–27112026, a 2,400-event horizon, alpha 0.05, and a 480-label hard cap. The persistent latent volatility state flips with probability 0.05 per event and is stationary with equal state probabilities.

The null preserves the conditional-mean assumption in each latent state, not only on average: state 0 has low/high context probabilities 0.5/0.5 and conditional cost contrasts -0.12/+0.12; state 1 has probabilities 0.75/0.25 and contrasts -0.10/+0.30. Each state therefore has exactly zero expected paired cost. The high-cost-event frequency and squared-cost variance persist in Markov regimes. Training proxies are estimated from a separate sample of the stationary regime mixture. The latent state and conditional probabilities are evaluator-only and never enter query or monitor inputs.

The strict-negative control has state-conditional post-onset mean contrasts -0.2667 and -0.1333, both nonpositive; its stationary average is -0.20. Each harm dose shifts the high-cost outcome probability by delta/3.75, giving stationary aggregate expected harm delta. The monitor's history-only query propensities preserve the marginal past-conditional null under the stated martingale construction.

Calibration family: two nonpositive controls crossed with three arms; exact one-sided Clopper-Pearson upper bounds use Bonferroni alpha 0.05/6. The primary harm contrast is the equal-weight four-dose paired detection difference. The same +2 percentage-point lower-bound threshold, no-extra-label upper-bound threshold, and simultaneous calibration gate as the independent confirmation are applied. Dose-level bootstrap intervals are secondary and unadjusted.

## Calibration

| scenario                                  | arm                            |   streams |   false_escalations |   false_rate |   simultaneous_one_sided_95_upper | passes_5pct_upper_limit   |   mean_labels |   mean_events_processed |
|:------------------------------------------|:-------------------------------|----------:|--------------------:|-------------:|----------------------------------:|:--------------------------|--------------:|------------------------:|
| markov_volatility_exact_marginal_null     | evidence_qmin_0.05_fixed       |      4000 |                   3 |       0.0008 |                            0.0026 | True                      |      304.8462 |               2399.8440 |
| markov_volatility_exact_marginal_null     | evidence_qmin_0.05_predictable |      4000 |                  62 |       0.0155 |                            0.0208 | True                      |      175.4625 |               2370.4145 |
| markov_volatility_exact_marginal_null     | uniform_q020                   |      4000 |                  74 |       0.0185 |                            0.0243 | True                      |      466.3505 |               2330.5720 |
| markov_volatility_strict_negative_control | evidence_qmin_0.05_fixed       |      4000 |                   0 |       0.0000 |                            0.0012 | True                      |      291.2627 |               2399.9747 |
| markov_volatility_strict_negative_control | evidence_qmin_0.05_predictable |      4000 |                  56 |       0.0140 |                            0.0191 | True                      |      168.9282 |               2371.6225 |
| markov_volatility_strict_negative_control | uniform_q020                   |      4000 |                  63 |       0.0158 |                            0.0211 | True                      |      466.6347 |               2332.0563 |

## Harm doses

| scenario                     |   harm_effect |   fixed_detection_rate |   predictable_detection_rate |   paired_detection_difference |   paired_detection_ci95_low |   paired_detection_ci95_high |   fixed_pre_onset_escalation_rate |   predictable_pre_onset_escalation_rate |   paired_label_difference |   paired_label_ci95_low |   paired_label_ci95_high |   paired_exposure_cost_difference |   paired_exposure_cost_ci95_low |   paired_exposure_cost_ci95_high |
|:-----------------------------|--------------:|-----------------------:|-----------------------------:|------------------------------:|----------------------------:|-----------------------------:|----------------------------------:|----------------------------------------:|--------------------------:|------------------------:|-------------------------:|----------------------------------:|--------------------------------:|---------------------------------:|
| markov_volatility_harm_d0.04 |        0.0400 |                 0.0010 |                       0.0032 |                        0.0022 |                      0.0005 |                       0.0040 |                            0.0000 |                                  0.0132 |                 -130.3913 |               -133.2758 |                -127.5192 |                           -0.7290 |                         -0.9159 |                          -0.5617 |
| markov_volatility_harm_d0.20 |        0.2000 |                 0.0035 |                       0.0155 |                        0.0120 |                      0.0080 |                       0.0160 |                            0.0000 |                                  0.0132 |                 -133.2330 |               -136.2133 |                -130.3035 |                           -4.5782 |                         -5.5595 |                          -3.6585 |
| markov_volatility_harm_d0.40 |        0.4000 |                 0.0147 |                       0.0700 |                        0.0553 |                      0.0478 |                       0.0633 |                            0.0000 |                                  0.0132 |                 -134.7303 |               -137.8441 |                -131.7417 |                          -18.0178 |                        -20.3773 |                         -15.7486 |
| markov_volatility_harm_d0.60 |        0.6000 |                 0.0698 |                       0.2265 |                        0.1568 |                      0.1440 |                       0.1698 |                            0.0000 |                                  0.0132 |                 -139.4305 |               -142.4628 |                -136.3836 |                          -61.5872 |                        -66.2317 |                         -56.9813 |

## Primary result

- Mean paired detection difference: 0.0566 (95% CI (0.051875, 0.0614375)).
- Mean paired label difference: -134.45 (95% CI (-137.29395625, -131.648171875)).
- Evaluator exposure-cost difference: -21.23 (95% CI (-23.099571007747205, -19.428932748491317)). This sums state-conditional expected paired costs along the evaluator-known latent path until the alarm or stopping time.
- Calibration gate: True; full retention rule: True.

This test is limited to the registered two-state Markov volatility process, immediate randomized feedback, a fixed action pair, and history-predictable q. It does not validate arbitrary serial dependence, delayed or informative labels, changing policies, or interventions. A pass supports the stated martingale-null case only; no novelty or universal robustness claim follows.

No figure was generated because PaperBanana was unavailable; project instructions require PaperBanana for research visuals.

Reproduce with:

```powershell
uv run python scripts/validate_markov_predictable_query_bounds.py --streams 4000 --seed 27108027 --device cuda --output outputs/markov_predictable_bound_validation
```
