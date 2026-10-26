# CRSP decision-policy retrospective pilot results

## Preliminary result

On the frozen 100-PERMNO training-selected sample, the model-based long-only policy had lower capped test cost than the same-date market-direction reference at all four imposed turnover charges. At 5 bps, paired candidate-minus-reference cost was -0.000558 per event (20-trading-date block 95% interval [-0.000912, -0.000202]); at 25 bps it was -0.000777 ([-0.001167, -0.000392]). Negative differences favor the candidate under this study's capped utility. The direction of the difference was negative in each test year from 2020 through 2025 at every cost setting.

Prediction quality did not show the same ranking: Ridge RMSE was 0.039943 versus 0.039786 for the training-mean predictor. The model policy therefore did not improve global squared-error prediction in this pilot, even though its thresholded actions had lower retrospective capped decision cost than the market-sign reference. This is a useful example of why predictive degradation and decision harm need separate endpoints.

| Turnover charge | Candidate minus reference mean cost | 95% date-block interval | Candidate long rate | Reference long rate |
| ---: | ---: | ---: | ---: | ---: |
| 0 bps | -0.000503 | [-0.000875, -0.000154] | 55.0% | 54.5% |
| 5 bps | -0.000558 | [-0.000912, -0.000202] | 55.0% | 54.5% |
| 10 bps | -0.000613 | [-0.000965, -0.000251] | 55.0% | 54.5% |
| 25 bps | -0.000777 | [-0.001167, -0.000392] | 55.0% | 54.5% |

## Sample and protocol

The study selected 100 PERMNOs uniformly from the train-split identifier set only, without requiring a security to appear in test. Of those 100, 30 had test-period observations, producing 166,753 training rows and 40,557 test events. The model used train-only imputation, scaling, and Ridge fitting on CUDA. The candidate went long when its next-observed-return prediction was positive; the reference went long when the same-date value-weighted market return was positive. Utility clipped next returns to [-10%, +10%] and charged entry, position changes, and test-end exits at 0/5/10/25 bps per turnover. The test span was 2020-01-02 to 2025-12-30.

The protocol and output hashes verify. The report contains only aggregate metrics; no CRSP observations or row-level costs were written into the result folder. Reproduction details are in the [frozen protocol](crsp_decision_policy_replay_protocol.md), source in `scripts/evaluate_crsp_policy_replay.py`, and aggregate files under `outputs/crsp_policy_replay_pilot_100/`.

## Limits and next experiment

This is a promising but very preliminary retrospective result, not trading evidence. The 100-name sample was selected from train identifiers and only 30 names reappeared in test; it is not a representative sample of the test universe. The confidence intervals block by date but do not include uncertainty from sampling PERMNOs. CRSP provides a retrospective daily-close clock, not verified release times. Returns are cross-sectionally and serially dependent, so these intervals do not establish the conditional-mean assumptions of the sequential monitor. The capped return utility and transaction costs are imposed sensitivity values; they are not an application or brokerage cost model. The report establishes no anytime-valid error rate, causal shift, deployment recommendation, or universal algorithm advantage.

The next useful study is a larger training-selected PERMNO cohort with security-cluster and date-block uncertainty, a fixed train/validation-only policy selection rule, and a preregistered comparison of the monitor candidates on the paired decision-cost stream. Keep all test outcomes evaluator-side until actions are frozen. Treat every sequential alarm as descriptive under the observed dependence unless a separate validity argument covers it.

No figure was generated. Any future figure must use PaperBanana and be validated against the saved aggregate metrics.
