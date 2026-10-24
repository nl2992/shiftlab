# Matched-path support-bound development grid

- Streams per scenario/schedule/bound cell: 60
- Horizon: 2400; delay: 12; pathwise label cap: 480.
- Generation device: cuda; event-order sequential replay: CPU NumPy.
- All query probabilities are precommitted by schedule and stream phase. Fixed/eventwise bound arms shared identical requested labels and processed event prefixes in every cell.
- The constant-q identity check passed: q=0.20 has identical fixed and eventwise bounds and stream decisions.
- This 60-stream development grid does not calibrate false alarms. Null counts are diagnostic only.
- No figure was generated; the frozen protocol requires PaperBanana for visuals, and these results are adequately represented by tables and Parquet.

## Cell summaries

| scenario                                  | schedule      | bound_mode   |   streams |   false_escalations |   detection_rate |   onset_reach_rate |   mean_labels |   mean_processed_events |   mean_event_delay |   mean_wall_delay |   mean_expected_exposure |
|:------------------------------------------|:--------------|:-------------|----------:|--------------------:|-----------------:|-------------------:|--------------:|------------------------:|-------------------:|------------------:|-------------------------:|
| markov_volatility_exact_marginal_null     | constant_q20  | eventwise    |        60 |                   2 |           0.0000 |           nan      |      472.0500 |               2355.0833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | constant_q20  | fixed        |        60 |                   2 |           0.0000 |           nan      |      472.0500 |               2355.0833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | periodic_q035 | eventwise    |        60 |                   2 |           0.0000 |           nan      |      473.7500 |               2364.0500 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | periodic_q035 | fixed        |        60 |                   0 |           0.0000 |           nan      |      473.7500 |               2364.0500 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | periodic_q055 | eventwise    |        60 |                   1 |           0.0000 |           nan      |      474.6833 |               2368.1000 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | periodic_q055 | fixed        |        60 |                   0 |           0.0000 |           nan      |      474.6833 |               2368.1000 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | periodic_q080 | eventwise    |        60 |                   1 |           0.0000 |           nan      |      475.8000 |               2375.9833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_exact_marginal_null     | periodic_q080 | fixed        |        60 |                   0 |           0.0000 |           nan      |      475.8000 |               2375.9833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_harm_d0.04              | constant_q20  | eventwise    |        60 |                   2 |           0.0000 |             1.0000 |      472.0500 |               2355.0833 |           nan      |          nan      |                  44.3960 |
| markov_volatility_harm_d0.04              | constant_q20  | fixed        |        60 |                   2 |           0.0000 |             1.0000 |      472.0500 |               2355.0833 |           nan      |          nan      |                  44.3960 |
| markov_volatility_harm_d0.04              | periodic_q035 | eventwise    |        60 |                   1 |           0.0167 |             1.0000 |      473.7500 |               2364.0500 |           959.0000 |          971.0000 |                  45.3564 |
| markov_volatility_harm_d0.04              | periodic_q035 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      473.7500 |               2364.0500 |           nan      |          nan      |                  46.2156 |
| markov_volatility_harm_d0.04              | periodic_q055 | eventwise    |        60 |                   1 |           0.0000 |             1.0000 |      474.6833 |               2368.1000 |           nan      |          nan      |                  45.6036 |
| markov_volatility_harm_d0.04              | periodic_q055 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      474.6833 |               2368.1000 |           nan      |          nan      |                  46.3738 |
| markov_volatility_harm_d0.04              | periodic_q080 | eventwise    |        60 |                   1 |           0.0000 |             1.0000 |      475.8000 |               2375.9833 |           nan      |          nan      |                  45.9013 |
| markov_volatility_harm_d0.04              | periodic_q080 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      475.8000 |               2375.9833 |           nan      |          nan      |                  46.6996 |
| markov_volatility_harm_d0.20              | constant_q20  | eventwise    |        60 |                   2 |           0.0167 |             1.0000 |      472.0500 |               2355.0833 |           355.0000 |          367.0000 |                 218.9800 |
| markov_volatility_harm_d0.20              | constant_q20  | fixed        |        60 |                   2 |           0.0167 |             1.0000 |      472.0500 |               2355.0833 |           355.0000 |          367.0000 |                 218.9800 |
| markov_volatility_harm_d0.20              | periodic_q035 | eventwise    |        60 |                   1 |           0.0167 |             1.0000 |      473.7500 |               2364.0500 |           748.0000 |          760.0000 |                 226.0933 |
| markov_volatility_harm_d0.20              | periodic_q035 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      473.7500 |               2364.0500 |           nan      |          nan      |                 231.0778 |
| markov_volatility_harm_d0.20              | periodic_q055 | eventwise    |        60 |                   1 |           0.0333 |             1.0000 |      474.6833 |               2368.1000 |           884.5000 |          896.5000 |                 225.9800 |
| markov_volatility_harm_d0.20              | periodic_q055 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      474.6833 |               2368.1000 |           nan      |          nan      |                 231.8689 |
| markov_volatility_harm_d0.20              | periodic_q080 | eventwise    |        60 |                   1 |           0.0167 |             1.0000 |      475.8000 |               2375.9833 |           995.0000 |         1007.0000 |                 228.7800 |
| markov_volatility_harm_d0.20              | periodic_q080 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      475.8000 |               2375.9833 |           nan      |          nan      |                 233.4978 |
| markov_volatility_harm_d0.40              | constant_q20  | eventwise    |        60 |                   2 |           0.0333 |             1.0000 |      472.0500 |               2355.0833 |           665.5000 |          677.5000 |                 437.2844 |
| markov_volatility_harm_d0.40              | constant_q20  | fixed        |        60 |                   2 |           0.0333 |             1.0000 |      472.0500 |               2355.0833 |           665.5000 |          677.5000 |                 437.2844 |
| markov_volatility_harm_d0.40              | periodic_q035 | eventwise    |        60 |                   1 |           0.0667 |             1.0000 |      473.7500 |               2364.0500 |           926.0000 |          938.0000 |                 447.8800 |
| markov_volatility_harm_d0.40              | periodic_q035 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      473.7500 |               2364.0500 |           nan      |          nan      |                 462.1556 |
| markov_volatility_harm_d0.40              | periodic_q055 | eventwise    |        60 |                   1 |           0.0500 |             1.0000 |      474.6833 |               2368.1000 |           444.6667 |          456.6667 |                 441.0800 |
| markov_volatility_harm_d0.40              | periodic_q055 | fixed        |        60 |                   0 |           0.0167 |             1.0000 |      474.6833 |               2368.1000 |          1107.0000 |         1119.0000 |                 463.0400 |
| markov_volatility_harm_d0.40              | periodic_q080 | eventwise    |        60 |                   1 |           0.0667 |             1.0000 |      475.8000 |               2375.9833 |           820.7500 |          832.7500 |                 448.5689 |
| markov_volatility_harm_d0.40              | periodic_q080 | fixed        |        60 |                   0 |           0.0000 |             1.0000 |      475.8000 |               2375.9833 |           nan      |          nan      |                 466.9956 |
| markov_volatility_harm_d0.60              | constant_q20  | eventwise    |        60 |                   2 |           0.2167 |             1.0000 |      472.0500 |               2355.0833 |           806.7692 |          818.7692 |                 621.0200 |
| markov_volatility_harm_d0.60              | constant_q20  | fixed        |        60 |                   2 |           0.2167 |             1.0000 |      472.0500 |               2355.0833 |           806.7692 |          818.7692 |                 621.0200 |
| markov_volatility_harm_d0.60              | periodic_q035 | eventwise    |        60 |                   1 |           0.2167 |             1.0000 |      473.7500 |               2364.0500 |           782.8462 |          794.8462 |                 632.2000 |
| markov_volatility_harm_d0.60              | periodic_q035 | fixed        |        60 |                   0 |           0.0333 |             1.0000 |      473.7500 |               2364.0500 |           830.0000 |          841.0000 |                 687.7533 |
| markov_volatility_harm_d0.60              | periodic_q055 | eventwise    |        60 |                   1 |           0.1667 |             1.0000 |      474.6833 |               2368.1000 |           781.3000 |          793.3000 |                 642.2067 |
| markov_volatility_harm_d0.60              | periodic_q055 | fixed        |        60 |                   0 |           0.0500 |             1.0000 |      474.6833 |               2368.1000 |           969.0000 |          981.0000 |                 688.4400 |
| markov_volatility_harm_d0.60              | periodic_q080 | eventwise    |        60 |                   1 |           0.2500 |             1.0000 |      475.8000 |               2375.9833 |           896.2667 |          908.2667 |                 645.5067 |
| markov_volatility_harm_d0.60              | periodic_q080 | fixed        |        60 |                   0 |           0.0333 |             1.0000 |      475.8000 |               2375.9833 |           973.5000 |          985.5000 |                 696.3333 |
| markov_volatility_strict_negative_control | constant_q20  | eventwise    |        60 |                   2 |           0.0000 |           nan      |      472.0500 |               2355.0833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | constant_q20  | fixed        |        60 |                   2 |           0.0000 |           nan      |      472.0500 |               2355.0833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | periodic_q035 | eventwise    |        60 |                   1 |           0.0000 |           nan      |      473.7500 |               2364.0500 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | periodic_q035 | fixed        |        60 |                   0 |           0.0000 |           nan      |      473.7500 |               2364.0500 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | periodic_q055 | eventwise    |        60 |                   1 |           0.0000 |           nan      |      474.6833 |               2368.1000 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | periodic_q055 | fixed        |        60 |                   0 |           0.0000 |           nan      |      474.6833 |               2368.1000 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | periodic_q080 | eventwise    |        60 |                   1 |           0.0000 |           nan      |      475.8000 |               2375.9833 |           nan      |          nan      |                   0.0000 |
| markov_volatility_strict_negative_control | periodic_q080 | fixed        |        60 |                   0 |           0.0000 |           nan      |      475.8000 |               2375.9833 |           nan      |          nan      |                   0.0000 |

## Paired eventwise-minus-fixed effects, macro-averaged over four harm doses

| schedule      | metric    | contrast              |   mean_difference |   bootstrap_95_low |   bootstrap_95_high |   streams |
|:--------------|:----------|:----------------------|------------------:|-------------------:|--------------------:|----------:|
| constant_q20  | detection | eventwise_minus_fixed |            0.0000 |             0.0000 |              0.0000 |        60 |
| constant_q20  | labels    | eventwise_minus_fixed |            0.0000 |             0.0000 |              0.0000 |        60 |
| constant_q20  | exposure  | eventwise_minus_fixed |            0.0000 |             0.0000 |              0.0000 |        60 |
| periodic_q035 | detection | eventwise_minus_fixed |            0.0708 |             0.0333 |              0.1125 |        60 |
| periodic_q035 | labels    | eventwise_minus_fixed |            0.0000 |             0.0000 |              0.0000 |        60 |
| periodic_q035 | exposure  | eventwise_minus_fixed |          -18.9181 |           -34.4269 |             -7.4858 |        60 |
| periodic_q055 | detection | eventwise_minus_fixed |            0.0458 |             0.0125 |              0.0875 |        60 |
| periodic_q055 | labels    | eventwise_minus_fixed |            0.0000 |             0.0000 |              0.0000 |        60 |
| periodic_q055 | exposure  | eventwise_minus_fixed |          -18.7131 |           -36.5015 |             -5.2533 |        60 |
| periodic_q080 | detection | eventwise_minus_fixed |            0.0750 |             0.0375 |              0.1167 |        60 |
| periodic_q080 | labels    | eventwise_minus_fixed |            0.0000 |             0.0000 |              0.0000 |        60 |
| periodic_q080 | exposure  | eventwise_minus_fixed |          -18.6923 |           -35.5010 |             -6.5480 |        60 |

## Interpretation limits

The bound contrast isolates bound choice under a fixed exogenous propensity path. The schedule contrast is a development screen and may change realized horizon at the hard label cap. No choice is confirmatory; any selected schedule needs fresh null calibration and a disjoint alternative block. This is a standard predictable bounded-factor construction and makes no novelty claim.
