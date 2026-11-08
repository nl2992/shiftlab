# C4: real data

## EQSDp (historical claim; registration preserved)

Claim: arm B `EQSDp_l0.9_g0.2` (frozen since `10ba0237`) vs the tuned Gong–Zhang-style adapter.
Records: `qsg_methods_search/c4_registration.json` (batch 1), `c4_amendment_A2.md`,
`c4_registration_batch2.json`, `c4_build_audit.md`, `c4_results.md`.

| Step | Outcome |
|---|---|
| Sources built | 27 public sources attempted. 11 failed eligibility gates (mostly <3% disagreement), 1 excluded by leakage audit (austin_animal), 3 not built (usage limit) |
| Batch 1 (K=9, opened once) | 5/9 supporting; registered rule NOT PASS |
| A2 (before batch 2) | Sequential batches; binomial count test; disclosure that batch 2 was selected after batch 1 |
| Batch 2 (K=7, opened once) | 4/7 supporting |
| **Cumulative** | **9/16 supporting (9 organisations, 9 cities): target reached** |
| Count test | P(X ≥ 9 \| N = 16, p = .05) = 1.6 × 10⁻⁸ |
| Sign test | 16/16 favour arm B, p = 1.5 × 10⁻⁵ |
| Effect size | pooled −3.38 per episode = **−0.75% of cost** (median −0.39%) |

**Caveats.**
- The supported family is mainly municipal 311 closure streams, plus crime clearance, collision
  injury and traffic citations.
- On 3 datasets never-switching beats arm B.
- Arm A (λ=.95) beats arm B on 16/16 (M5).
- The comparator is an adapter, not native Gong–Zhang.

## New algorithms

No new-algorithm track passed its gate (BCR, PAVE+; Gap-Mix+ pending), so no new-method C4
protocol has been created. Building K≥3-model real streams (BCR) was not started.
