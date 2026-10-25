# Fitted context-nested promotion development grid

This frozen CUDA grid used 30 matched seeds in each of 27 cells (`n=3200`, `d=16`), with uniform direct-IPW monitoring and common 20%/40% hard label caps. It compares pooled candidate-rank alpha with equal-context and validation-volume nested allocations. The exact DGP and analysis were frozen in [the protocol](../../../docs/contextual_budgeted_promotion_grid_protocol.md).

The monitor/evaluator assumptions are unchanged from the fitted-controller benchmark. The context signal is applied from the monitor boundary; latent group membership is evaluator-only, and the learner's context rule uses the independently misclassified proxy feature. No figure was generated.

## Primary macro contrasts

The primary summary equally averages the 18 positive-signal prevalence/error cells at the 40% cap. The two primary contrasts use 97.5% intervals for simultaneous coverage. The +1 cumulative utility margin is the existing development gate; this exploratory grid does not select a confirmation winner.

| Contrast | Mean paired future net gain | 97.5% bootstrap interval | Settings |
|---|---:|---:|---:|
| rank_context_volume_minus_rank | 0.014 | [-1.938, 1.998] | 18 |
| rank_context_volume_minus_rank_context_equal | 0.410 | [-0.773, 1.744] | 18 |

## 40% cap results by signal strength

| Signal delta | Allocation | Promotion rate | Mean future net gain | Future harmful rate | Mean labels / cap | Processed monitor fraction |
|---:|---|---:|---:|---:|---:|---:|
| 0.00 | rank | 0.000 | 0.000 | 0.000 | 631.6 / 640 | 0.984 |
| 0.00 | rank_context_equal | 0.000 | 0.000 | 0.000 | 631.6 / 640 | 0.984 |
| 0.00 | rank_context_volume | 0.000 | 0.000 | 0.000 | 631.6 / 640 | 0.984 |
| 0.05 | rank | 0.000 | 0.000 | 0.000 | 631.6 / 640 | 0.984 |
| 0.05 | rank_context_equal | 0.000 | 0.000 | 0.000 | 631.6 / 640 | 0.984 |
| 0.05 | rank_context_volume | 0.000 | 0.000 | 0.000 | 631.6 / 640 | 0.984 |
| 0.10 | rank | 0.078 | 10.012 | 0.000 | 631.6 / 640 | 0.984 |
| 0.10 | rank_context_equal | 0.059 | 9.220 | 0.000 | 631.6 / 640 | 0.984 |
| 0.10 | rank_context_volume | 0.070 | 10.039 | 0.000 | 631.6 / 640 | 0.984 |

## Cellwise diagnostic

Nested volume exceeded pooled-rank mean net gain in 1/18 positive-signal cells at the 40% cap. The largest registered-cell contrast was `context_p90_delta100_error00`: nested volume minus rank-only was 23.16 [4.96, 44.33] cumulative units, with promotion rates 0.333 versus 0.233. This cell was identified after examining the development grid; its interval is unadjusted and is not confirmation evidence. The two-way macro comparison remains the registered primary analysis.

The complete parameter-cell summaries, paired cell contrasts, and seed-level metrics are stored in Parquet. Cellwise intervals are descriptive and unadjusted across the factorial; the macro contrast averages only the registered positive-signal settings. The zero-signal cells are nondegenerate pointwise net-benefit nulls because both actions have equal expected cost before switching cost.

## Reproduction

`uv run shiftlab-dive-budgeted-context-grid develop --seeds 30 --seed-offset 20261025 --n 3200 --d 16 --device cuda --output outputs/context_budgeted_promotion_grid_30`

This is a development screen. Any method retained for a performance claim needs a new independent null calibration and a disjoint confirmation run. No novelty claim follows from weighted Bonferroni composition.
