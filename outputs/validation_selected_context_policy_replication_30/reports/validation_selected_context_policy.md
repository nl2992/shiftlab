# Validation-selected contextual policy development grid

This frozen grid used 30 matched seeds in each of 27 cells (`n=3200`, `d=16`), with uniform direct-IPW monitoring and common 20%/40% hard label caps. It compares pooled candidate-rank alpha, equal-context and validation-volume nested allocations, and one validation-selected composite policy tested at full alpha. The exact DGP and analysis were frozen in [the protocol](../../../docs/validation_selected_context_policy_replication_protocol.md).

This run uses seed IDs 20261100–20261129, disjoint from the earlier nested-alpha and composite development screens.

The monitor/evaluator assumptions are unchanged from the fitted-controller benchmark. The context signal is applied from the monitor boundary; latent group membership is evaluator-only, and the learner's context rule uses the independently misclassified proxy feature. No figure was generated.

## Primary macro contrasts

The primary summary equally averages the 18 positive-signal prevalence/error cells at the 40% cap. The two primary contrasts use 97.5% intervals for simultaneous coverage under the frozen independent seed block. The +1 cumulative utility margin is the existing development gate; this exploratory grid does not select a confirmation winner.

| Contrast | Mean paired future net gain | 97.5% bootstrap interval | Settings |
|---|---:|---:|---:|
| validation_context_policy_minus_rank | -2.957 | [-6.417, -0.307] | 18 |
| validation_context_policy_minus_rank_context_volume | -4.002 | [-7.101, -1.359] | 18 |

## 40% cap results by signal strength

| Signal delta | Allocation | Promotion rate | Mean future net gain | Future harmful rate | Mean labels / cap | Processed monitor fraction |
|---:|---|---:|---:|---:|---:|---:|
| 0.00 | rank | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.00 | rank_context_equal | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.00 | rank_context_volume | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.00 | validation_context_policy | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.05 | rank | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.05 | rank_context_equal | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.05 | rank_context_volume | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.05 | validation_context_policy | 0.000 | 0.000 | 0.000 | 631.5 / 640 | 0.984 |
| 0.10 | rank | 0.048 | 6.782 | 0.000 | 631.5 / 640 | 0.984 |
| 0.10 | rank_context_equal | 0.041 | 7.163 | 0.000 | 631.5 / 640 | 0.984 |
| 0.10 | rank_context_volume | 0.056 | 8.873 | 0.000 | 631.5 / 640 | 0.984 |
| 0.10 | validation_context_policy | 0.015 | 0.868 | 0.000 | 631.5 / 640 | 0.984 |

## Cellwise diagnostic

validation_context_policy exceeded pooled-rank mean net gain in 0/18 positive-signal cells at the 40% cap. The largest registered-cell contrast was `context_p90_delta050_error10`: validation_context_policy minus rank-only was 0.00 [0.00, 0.00] cumulative units. This cell was identified after examining the development grid; its interval is unadjusted and is not confirmation evidence. The macro comparison remains the registered primary analysis.

The complete parameter-cell summaries, paired cell contrasts, and seed-level metrics are stored in Parquet. Cellwise intervals are descriptive and unadjusted across the factorial; the macro contrast averages only the registered positive-signal settings. The zero-signal cells are nondegenerate pointwise net-benefit nulls because both actions have equal expected cost before switching cost.

## Reproduction

`uv run shiftlab-dive-budgeted-context-grid policy-develop --seeds 30 --seed-offset 20261100 --n 3200 --d 16 --device cuda --output outputs/validation_selected_context_policy_replication_30`

This is a development screen. Any method retained for a performance claim needs a new independent null calibration and a disjoint confirmation run. No novelty claim follows from weighted Bonferroni composition.
