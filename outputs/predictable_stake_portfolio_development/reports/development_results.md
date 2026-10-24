# Predictable stake portfolio development screen

- Streams per scenario and eta: 60; horizon: 2400; delay: 12.
- Query schedule: `periodic_q080` (`q_low=0.05`, `q_high=0.8`, 2/10 high slots); hard cap: 480 labels.
- Generation device: cuda; sequential delayed-feedback replay: CPU NumPy.
- Candidate eta grid: `[0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]`; eta=1 matches the fixed equal-weight stake mixture algebraically and numerically to 1e-12.
- All candidates share identical query, label, event-prefix, and budget paths. Null cells are descriptive (60 streams), not calibration.
- No figure was generated; the project requires PaperBanana for visuals and none is available in this session.

## Cell summaries

| scenario                                  |    eta |   streams |   false_escalations |   detection_rate |   onset_reach_rate |   mean_labels |   mean_processed_events |   mean_event_delay |   mean_wall_delay |   mean_expected_exposure |
|:------------------------------------------|-------:|----------:|--------------------:|-----------------:|-------------------:|--------------:|------------------------:|-------------------:|------------------:|-------------------------:|
| markov_volatility_exact_marginal_null     | 0.0000 |        60 |                   2 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | 0.2500 |        60 |                   2 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | 0.5000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | 0.7500 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | 1.0000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | 1.5000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | 2.0000 |        60 |                   0 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_harm_d0.04              | 0.0000 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |            22.0000 |           34.0000 |                  45.3316 |
| markov_volatility_harm_d0.04              | 0.2500 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           442.0000 |          454.0000 |                  45.5978 |
| markov_volatility_harm_d0.04              | 0.5000 |        60 |                   1 |           0.0000 |             1.0000 |      473.7167 |               2365.3333 |           nan      |          nan      |                  46.1018 |
| markov_volatility_harm_d0.04              | 0.7500 |        60 |                   1 |           0.0000 |             1.0000 |      473.7167 |               2365.3333 |           nan      |          nan      |                  46.1018 |
| markov_volatility_harm_d0.04              | 1.0000 |        60 |                   1 |           0.0000 |             1.0000 |      473.7167 |               2365.3333 |           nan      |          nan      |                  46.1018 |
| markov_volatility_harm_d0.04              | 1.5000 |        60 |                   1 |           0.0000 |             1.0000 |      473.7167 |               2365.3333 |           nan      |          nan      |                  46.1018 |
| markov_volatility_harm_d0.04              | 2.0000 |        60 |                   0 |           0.0000 |             1.0000 |      473.7167 |               2365.3333 |           nan      |          nan      |                  46.9964 |
| markov_volatility_harm_d0.20              | 0.0000 |        60 |                   1 |           0.0333 |             1.0000 |      473.7167 |               2365.3333 |           321.0000 |          333.0000 |                 224.9511 |
| markov_volatility_harm_d0.20              | 0.2500 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           442.0000 |          454.0000 |                 227.9889 |
| markov_volatility_harm_d0.20              | 0.5000 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           443.0000 |          455.0000 |                 227.9933 |
| markov_volatility_harm_d0.20              | 0.7500 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           443.0000 |          455.0000 |                 227.9933 |
| markov_volatility_harm_d0.20              | 1.0000 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           882.0000 |          894.0000 |                 229.4400 |
| markov_volatility_harm_d0.20              | 1.5000 |        60 |                   1 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           932.0000 |          944.0000 |                 229.5889 |
| markov_volatility_harm_d0.20              | 2.0000 |        60 |                   0 |           0.0167 |             1.0000 |      473.7167 |               2365.3333 |           973.0000 |          985.0000 |                 234.1622 |
| markov_volatility_harm_d0.40              | 0.0000 |        60 |                   1 |           0.1167 |             1.0000 |      473.7167 |               2365.3333 |           637.5714 |          648.2857 |                 436.0222 |
| markov_volatility_harm_d0.40              | 0.2500 |        60 |                   1 |           0.0667 |             1.0000 |      473.7167 |               2365.3333 |           655.5000 |          667.5000 |                 446.8178 |
| markov_volatility_harm_d0.40              | 0.5000 |        60 |                   1 |           0.0667 |             1.0000 |      473.7167 |               2365.3333 |           671.5000 |          682.7500 |                 447.2089 |
| markov_volatility_harm_d0.40              | 0.7500 |        60 |                   1 |           0.0667 |             1.0000 |      473.7167 |               2365.3333 |           673.0000 |          685.0000 |                 447.2622 |
| markov_volatility_harm_d0.40              | 1.0000 |        60 |                   1 |           0.0667 |             1.0000 |      473.7167 |               2365.3333 |           675.0000 |          687.0000 |                 447.3333 |
| markov_volatility_harm_d0.40              | 1.5000 |        60 |                   1 |           0.0667 |             1.0000 |      473.7167 |               2365.3333 |           692.7500 |          704.7500 |                 447.8622 |
| markov_volatility_harm_d0.40              | 2.0000 |        60 |                   0 |           0.0833 |             1.0000 |      473.7167 |               2365.3333 |           767.8000 |          779.8000 |                 455.5378 |
| markov_volatility_harm_d0.60              | 0.0000 |        60 |                   1 |           0.2833 |             1.0000 |      473.7167 |               2365.3333 |           702.8235 |          714.5294 |                 608.3267 |
| markov_volatility_harm_d0.60              | 0.2500 |        60 |                   1 |           0.2000 |             1.0000 |      473.7167 |               2365.3333 |           776.3333 |          788.3333 |                 642.1400 |
| markov_volatility_harm_d0.60              | 0.5000 |        60 |                   1 |           0.1667 |             1.0000 |      473.7167 |               2365.3333 |           709.2000 |          721.2000 |                 644.1600 |
| markov_volatility_harm_d0.60              | 0.7500 |        60 |                   1 |           0.1667 |             1.0000 |      473.7167 |               2365.3333 |           709.6000 |          721.6000 |                 644.1867 |
| markov_volatility_harm_d0.60              | 1.0000 |        60 |                   1 |           0.1667 |             1.0000 |      473.7167 |               2365.3333 |           708.6000 |          720.6000 |                 644.0333 |
| markov_volatility_harm_d0.60              | 1.5000 |        60 |                   1 |           0.1667 |             1.0000 |      473.7167 |               2365.3333 |           710.9000 |          722.9000 |                 644.3333 |
| markov_volatility_harm_d0.60              | 2.0000 |        60 |                   0 |           0.1833 |             1.0000 |      473.7167 |               2365.3333 |           730.0000 |          742.0000 |                 654.4400 |
| markov_volatility_strict_negative_control | 0.0000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | 0.2500 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | 0.5000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | 0.7500 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | 1.0000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | 1.5000 |        60 |                   1 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | 2.0000 |        60 |                   0 |           0.0000 |           nan      |      473.7167 |               2365.3333 |           nan      |          nan      |                   0.0000 |

## Paired detection contrasts versus fixed eta=1

| metric                                  |   candidate_eta |   reference_eta |   mean_difference |   bootstrap_95_low |   bootstrap_95_high |   paired_seed_count |
|:----------------------------------------|----------------:|----------------:|------------------:|-------------------:|--------------------:|--------------------:|
| post_onset_detection                    |          0.0000 |          1.0000 |            0.0500 |             0.0250 |              0.0792 |                  60 |
| labels_queried                          |          0.0000 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| evaluator_cumulative_expected_harm_cost |          0.0000 |          1.0000 |          -13.0692 |           -20.0331 |             -6.7572 |                  60 |
| post_onset_detection                    |          0.2500 |          1.0000 |            0.0125 |             0.0000 |              0.0292 |                  60 |
| labels_queried                          |          0.2500 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| evaluator_cumulative_expected_harm_cost |          0.2500 |          1.0000 |           -1.0910 |            -2.8136 |             -0.0772 |                  60 |
| post_onset_detection                    |          0.5000 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| labels_queried                          |          0.5000 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| evaluator_cumulative_expected_harm_cost |          0.5000 |          1.0000 |           -0.3611 |            -1.2300 |              0.1283 |                  60 |
| post_onset_detection                    |          0.7500 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| labels_queried                          |          0.7500 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| evaluator_cumulative_expected_harm_cost |          0.7500 |          1.0000 |           -0.3411 |            -1.1900 |              0.1400 |                  60 |
| post_onset_detection                    |          1.5000 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| labels_queried                          |          1.5000 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| evaluator_cumulative_expected_harm_cost |          1.5000 |          1.0000 |            0.2444 |             0.0033 |              0.5822 |                  60 |
| post_onset_detection                    |          2.0000 |          1.0000 |            0.0083 |             0.0000 |              0.0250 |                  60 |
| labels_queried                          |          2.0000 |          1.0000 |            0.0000 |             0.0000 |              0.0000 |                  60 |
| evaluator_cumulative_expected_harm_cost |          2.0000 |          1.0000 |            6.0570 |             0.0167 |             17.0840 |                  60 |

## Frozen development nomination gate

Selected eta: `0.0`.

This is a development-only nomination; any candidate needs fresh calibration and disjoint confirmation.

## Interpretation

This is a development screen for a standard predictable convex portfolio of bounded betting factors. The supermartingale argument requires predictable weights and the registered event-time conditional-mean null. Any nonidentity candidate needs independent calibration and disjoint confirmation. No novelty claim is made.
