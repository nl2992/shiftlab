# Target-scout selected contextual policy development grid

This frozen grid used 30 matched seeds in each of 27 cells (`n=3200`, `d=16`), with uniform direct-IPW monitoring and common 20%/40% hard label caps. It compares pooled candidate-rank alpha, equal-context and validation-volume nested allocations, and one target-scout-selected composite policy tested at full alpha. The exact DGP and analysis were frozen in [the protocol](../../../docs/scout_selected_context_policy_protocol.md).

This run uses seed IDs 20261130–20261159, disjoint from the earlier nested-alpha, validation-composite, and target-scout development screens.

The monitor/evaluator assumptions are unchanged from the fitted-controller benchmark. The context signal is applied from the monitor boundary; latent group membership is evaluator-only, and the learner's context rule uses the independently misclassified proxy feature. No figure was generated.

## Primary macro contrasts

The primary summary equally averages the 18 positive-signal prevalence/error cells at the 40% cap. The two primary contrasts use 97.5% intervals for simultaneous coverage under the frozen independent seed block. The +1 cumulative utility margin is the existing development gate; this exploratory grid does not select a confirmation winner.

| Contrast | Mean paired future net gain | 97.5% bootstrap interval | Settings |
|---|---:|---:|---:|
| scout_context_policy_minus_rank | 4.898 | [1.542, 8.840] | 18 |
| scout_context_policy_minus_rank_context_volume | 4.359 | [0.893, 8.468] | 18 |

## 40% cap results by signal strength

| Signal delta | Allocation | Promotion rate | Mean future net gain | Future harmful rate | Mean labels / cap | Monitor fraction processed for test |
|---:|---|---:|---:|---:|---:|---:|
| 0.00 | rank | 0.000 | 0.000 | 0.000 | 631.8 / 640 | 0.986 |
| 0.00 | rank_context_equal | 0.000 | 0.000 | 0.000 | 631.8 / 640 | 0.986 |
| 0.00 | rank_context_volume | 0.000 | 0.000 | 0.000 | 631.8 / 640 | 0.986 |
| 0.00 | scout_context_policy | 0.000 | 0.000 | 0.000 | 631.8 / 640 | 0.486 |
| 0.05 | rank | 0.000 | 0.000 | 0.000 | 631.8 / 640 | 0.986 |
| 0.05 | rank_context_equal | 0.000 | 0.000 | 0.000 | 631.8 / 640 | 0.986 |
| 0.05 | rank_context_volume | 0.004 | 0.371 | 0.000 | 631.8 / 640 | 0.986 |
| 0.05 | scout_context_policy | 0.011 | 1.039 | 0.000 | 631.8 / 640 | 0.486 |
| 0.10 | rank | 0.041 | 5.476 | 0.000 | 631.8 / 640 | 0.986 |
| 0.10 | rank_context_equal | 0.033 | 5.823 | 0.000 | 631.8 / 640 | 0.986 |
| 0.10 | rank_context_volume | 0.037 | 6.183 | 0.000 | 631.8 / 640 | 0.986 |
| 0.10 | scout_context_policy | 0.081 | 14.231 | 0.000 | 631.8 / 640 | 0.486 |

## Cellwise diagnostic

scout_context_policy exceeded pooled-rank mean net gain in 5/18 positive-signal cells at the 40% cap. The largest registered-cell contrast was `context_p90_delta100_error00`: scout_context_policy minus rank-only was 50.47 [23.73, 80.20] cumulative units. This cell was identified after examining the development grid; its interval is unadjusted and is not confirmation evidence. The macro comparison remains the registered primary analysis.

The complete parameter-cell summaries, paired cell contrasts, and seed-level metrics are stored in Parquet. Cellwise intervals are descriptive and unadjusted across the factorial; the macro contrast averages only the registered positive-signal settings. The zero-signal cells are nondegenerate pointwise net-benefit nulls because both actions have equal expected cost before switching cost.

## Reproduction

`uv run shiftlab-dive-budgeted-context-grid scout-develop --seeds 30 --seed-offset 20261130 --n 3200 --d 16 --device cuda --protocol docs/scout_selected_context_policy_protocol.md --output outputs/scout_selected_context_policy_30`

This is a development screen. Any method retained for a performance claim needs a new independent null calibration and a disjoint confirmation run. No novelty claim follows from weighted Bonferroni composition.
