# Exploratory CRSP exchange-stratified monitor replay

The frozen train-only policy was replayed on 7,621,543 test observations, 7,350 PERMNOs, and 1,507 dates. The exact same-date exchange code `primaryexch` defines six predeclared operational strata.

## Exchange support and paired costs

| exchange   |   events |   observed_dates |   mean_daily_paired_cost |   event_weighted_paired_cost |   positive_next_20_date_harm_prevalence |
|:-----------|---------:|-----------------:|-------------------------:|-----------------------------:|----------------------------------------:|
| A          |   319507 |             1507 |                 -0.00078 |                     -0.00077 |                                 0.26854 |
| B          |     1828 |             1507 |                  0.00010 |                      0.00130 |                                 0.41349 |
| I          |        0 |                0 |                nan       |                    nan       |                               nan       |
| N          |  2619313 |             1507 |                 -0.00031 |                     -0.00031 |                                 0.42619 |
| Q          |  4680895 |             1507 |                 -0.00036 |                     -0.00032 |                                 0.44021 |
| R          |        0 |                0 |                nan       |                    nan       |                               nan       |

## Monitor comparison

| method                      | exchange_mixture_first_crossing_date   |   exchange_mixture_crossing_fraction |   exchange_mixture_max_log_e | first_bonferroni_subgroup_crossing   |   subgroup_log_e_threshold_alpha_over_6 |   pooled_auroc_next_20_date_harm |   pooled_average_precision_next_20_date_harm |   pooled_positive_harm_windows |   updates_per_exchange | interpretation                                                |
|:----------------------------|:---------------------------------------|-------------------------------------:|-----------------------------:|:-------------------------------------|----------------------------------------:|---------------------------------:|---------------------------------------------:|-------------------------------:|-----------------------:|:--------------------------------------------------------------|
| fixed_stake_mixture         |                                        |                               0.0000 |                       0.0311 | False                                |                                  4.7875 |                           0.5043 |                                       0.3712 |                           2318 |                   1507 | exploratory retrospective replay; no CRSP error-control claim |
| uniform_eight_start_mixture |                                        |                               0.0000 |                       0.3845 | False                                |                                  4.7875 |                           0.5082 |                                       0.4091 |                           2318 |                   1507 | exploratory retrospective replay; no CRSP error-control claim |

The two candidates are the established fixed five-stake bounded-mean e-process and the established uniform eight-start mixture, each run within each exchange. The six per-exchange e-values are combined with fixed equal weights. An exchange-mixture crossing at `log(1/alpha)` is valid only for the intersection of all six exchange-specific nulls; the familywise subgroup threshold `log(6/alpha)` is also reported. Neither is a test of population-average harm.

All results are retrospective diagnostics on a test period already examined in previous CRSP analyses. Hindsight next-20-date labels are evaluator-only and overlapping. The WRDS close dates do not verify actual label publication times, temporal dependence is not modeled by these standard e-processes, and no CRSP false-alarm guarantee is claimed. Any figure should be separately produced with PaperBanana and validated against these saved metrics.

Protocol: `docs/crsp_exchange_stratified_replay_protocol.md`. Metrics, source hashes, environment details and checksums are saved under `outputs/crsp_exchange_stratified_replay/`.
