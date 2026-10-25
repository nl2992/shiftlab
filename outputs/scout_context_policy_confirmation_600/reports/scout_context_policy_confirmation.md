# Target-scout contextual policy independent confirmation

Status: **passed**. Device: cuda; seeds per cell: 600; seed block: 20264000–20264599.

The registered grid has 18 positive-signal prevalence × signal × proxy-error cells, the common 40% hard cap, and three methods on matched seeds and query uniforms. The primary endpoint is evaluator-known cumulative future net decision gain. The two contrasts equally weight all 18 cells and resample matched seed IDs as blocks.

| Contrast | Mean paired difference | Simultaneous 97.5% interval | Practical margin |
|---|---:|---:|---:|
| scout_context_policy_minus_rank | 5.284 | [4.301, 6.292] | 1.0 |
| scout_context_policy_minus_rank_context_volume | 4.182 | [3.282, 5.087] | 1.0 |

The performance gate passes only when both lower limits exceed +1.0 and all hard caps hold. Cellwise metrics are descriptive. Claims are limited to this IID synthetic family, known positive uniform propensities, bounded paired costs, frozen candidate family, learner-visible contexts and registered budget. The independent null calibration does not extend to serial dependence, delayed/selective labels, context drift, or real applications. No novelty claim follows.

Frozen protocol: docs/scout_context_policy_confirmation_protocol.md (SHA-256 55f6f9f23f55a313232f49d7da2a6a77ef9dfb3c1f59cf39ee88541ad74d6c31). No figure was generated.
