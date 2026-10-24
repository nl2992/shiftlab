# Independent intervention confirmation results

**Status:** Utility confirmation and separate null-calibration replication completed. Both use
the development-selected design `q=0.80`, 40% label cap, label price 0.01, and promotion and
rollback costs 0.05. No parameters were changed between blocks.

## Utility confirmation

The independent 2,000-seed confirmation compared four policies on five controls and six
reversal profiles. Promotion-plus-rollback improved expected net utility over promotion-only
by **5.51** averaged equally over the six reversal profiles; the paired seed-cluster 95%
interval was **[5.32, 5.69]**. Its difference from continue was **52.94** [52.75, 53.13].
All 88,000 policy-stream records respected the 640-label cap. The metric Parquet SHA-256 is
`c7e632b71bd051940e070d45a18e480195b89c864a5bcf4c22a148920872570f`; see the [manifest](../outputs/intervention_confirmation/manifest.json).

The aggregate improvement does not mean the policy prevents every harmful promotion. When
harm began after only 10% of deployment, rollback occurred on 292/2,000 streams for -0.10
harm (14.6% detection) and 1,934/2,000 for -0.20 harm (96.7%); expected net utility remained
-51.70 and -60.87, respectively. Later reversals kept substantial positive net utility because
the candidate benefited for longer before the reversal.

Promotion-only and promotion-plus-rollback had the same promotion-null errors: 25/2,000
(1.25%) with zero gain in both phases and 22/2,000 (1.10%) when gain appeared only after the
shadow period. Their nine-cell simultaneous upper bounds were 2.03% and 1.84%. The selected
zero-deployment-gain rollback null produced 35/2,000 errors (1.75%) and an upper bound of
2.64%, slightly above the predeclared 2.5% empirical criterion. The 2,000-stream block does
not clear that calibration gate.

## Separate 10,000-stream calibration replication

To improve calibration precision without changing the selected policy, a fixed 10,000-stream
replication was run on five fresh non-harmful controls. It has its own seed block and exact
Bonferroni intervals over the same nine phase-specific cells. No metrics were pooled with the
2,000-stream block.

| Calibration cell | Events | Rate | Simultaneous one-sided 95% upper limit |
| --- | ---: | ---: | ---: |
| Promotion null, zero gain in both phases | 116/10,000 | 1.16% | 1.46% |
| Promotion null, benefit begins only after shadow | 128/10,000 | 1.28% | 1.59% |
| Rollback null, selected strong shadow benefit then zero deployment gain | 132/10,000 | 1.32% | 1.64% |
| Rollback null, zero gain in both phases | 0/10,000 | 0.00% | 0.05% |
| Rollback null, persistent positive deployment benefit | 1/10,000 | 0.01% | 0.07% |
| Rollback null, future-only deployment benefit | 0/10,000 | 0.00% | 0.05% |
| Rollback null, weak positive deployment benefit | 6/10,000 | 0.06% | 0.15% |

All nine cells, including the duplicate promotion rows for the combined policy, have
familywise upper limits below 2.5%; the largest is **1.64%**. This independent replication
supports calibration of the frozen policy under the simulator's stated assumptions. The
earlier 2,000-stream calibration miss remains visible and separate, rather than being pooled
away.

The replication metrics SHA-256 is
`0d0897e114f2ec007e629847cdd56c6aa2711a9d30963f28cbaacc88f05829ae`. See its [calibration table](../outputs/intervention_calibration_replication/error_calibration.csv),
[Parquet metrics](../outputs/intervention_calibration_replication/metrics.parquet), and
[manifest](../outputs/intervention_calibration_replication/manifest.json).

## Scope

The result supports a cost-aware two-stage intervention reference policy in a bounded,
independent Bernoulli paired-cost simulation. It does not establish type-I control for delayed
or selectively observed labels, serial dependence, estimated propensities, adaptive candidate
search, or real-world counterfactual decision costs. The fixed-stake mixture is established
e-process machinery; this is not a novelty claim. No figure was generated; any later research
visual must use PaperBanana under the repository guidance.
