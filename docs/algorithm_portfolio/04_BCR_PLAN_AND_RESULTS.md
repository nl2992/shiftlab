# Track A: BCR (Budgeted Challenger Racing)

Full ledger: branch `research/multimodel-bcr-2026-11-08`, `docs/multimodel_bcr/00–08`.
Code: `scripts/multimodel_bcr/` (envs, policies, runner, analysis).

- **Contract.** K=3 and K=5, T=2000, B=200, delay 100, c_q=.05, c_s=5. One purchased label
  reveals every model's loss; the simulator is unchanged.
- **Environments.** E1 persistent, E2 late, E3 reversal, E4 specialists under covariate drift,
  E5 ambiguous, E6 null/worse, plus K=5 variants.
- **Seeds.** 40 fresh development seeds (base 2026111101).
- **Configs.** 86, all tuned in-sample.

| Family (best config) | Net | Labels | Switches |
|---|---|---|---|
| K-Wald + disagreement pacing | **558.67** | 200 | 2.56 |
| K-Wald + Model-Picker acquisition | 559.42 | 96 | 2.67 |
| BCR (economic challenger set + decision-relevant acquisition) | 559.82 | 179 | 2.01 |
| K-Wald + uniform | 569.38 | 200 | 2.39 |
| never switch | 580.93 | 0 | 0 |
| Model Picker deployment adapter | 587.79 | 95 | 6.88 |

- **BCR vs the best K-Wald:** +1.15 [−1.37, +3.66].
- **Frontier check.** BCR is at best on the K-Wald frontier (−0.06), never inside it.
- **Per environment:** BCR wins on ambiguous (−6.9) and persistent (−4.0) environments. It loses
  on reversal (+20.5), specialists (+8.6) and late K=5 (+6.8): pruning a candidate delays
  recovery.

**Verdict: STOP (feasibility gate failed; directive §4.10 rules 1 and 3).** Candidates B and C
were not built separately. Ranking-sensitive acquisition is effectively tested by the
Model-Picker acquisition arm, which ties.

Kept findings (C1): selector churn without an economic hurdle; multiple-comparison churn growing
with K; a label-efficiency result (half the labels at equal cost).
