# Intervention sensitivity grid results

**Run:** 60 development seeds per cell, 220 cells, six reversal profiles and four controls.
Generated on the RTX 4060 Laptop GPU. This is a development grid; the top setting was selected
on these seeds and its intervals are not confirmatory.

The grid crossed query propensity (0.25, 0.50, 0.80), hard cap (20%, 40%), label price
(0, 0.01), three promotion/rollback cost pairs, and six combinations of reversal onset and
severity. The controls ran at the frozen reference setting. All 52,800 policy-stream rows
respected their hard caps. The metrics Parquet hash is
`0f61edd81955a7a567ab03d4ab96b80cc0de1f005a06e1d96e12be193bf44667`; see the [manifest](../outputs/intervention_sensitivity_development/manifest.json)
for source hashes and environment details.

## Development ranking at the reference label price

For the reference promotion and rollback costs (0.05 each), macro expected net utility over
the six reversal profiles changed with label propensity and budget as follows. Promotion-plus-
rollback utility is averaged equally over the six profiles and 60 streams per profile. The
paired interval is a seed-cluster bootstrap interval used for development ranking only.

| Query rate | Label cap | Promotion-only utility | Promotion + rollback utility | Paired gain | Development 95% interval |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.25 | 20% | 47.43 | 48.65 | +1.22 | [0.11, 2.41] |
| 0.25 | 40% | 47.43 | 48.65 | +1.22 | [0.11, 2.51] |
| 0.50 | 20% | 47.43 | 50.84 | +3.41 | [1.71, 5.07] |
| 0.50 | 40% | 47.43 | 51.99 | +4.55 | [3.10, 5.89] |
| 0.80 | 20% | 47.43 | 47.18 | -0.25 | [-1.60, 1.21] |
| 0.80 | 40% | 47.43 | 53.48 | +6.05 | [4.96, 7.14] |

At query rate 0.80, the 20% cap constrained the post-promotion evidence enough that rollback
did not improve net utility. With the 40% cap, it produced the largest development gain at
label price 0.01. Its mean was 601.9 labels of the 640-label cap across reversal streams and
it rolled back 18.3% of promoted streams. At label price zero, the highest-ranked design was
also query rate 0.80 and 40% cap; its macro utility was 59.50 and its gain over promotion-only
was 11.55. That zero-price result is an economic sensitivity point, not the selected design.

The selected setting is `q=0.80`, cap 40%, label price 0.01, and costs (0.05, 0.05). It was
chosen from the reference-price rows and frozen before independent confirmation. The grid is
not a universal recommendation: under q=0.80 and a 20% cap, label spending and evidence
starvation offset rollback value. Details are in the [protocol](intervention_sensitivity_protocol.md),
[macro ranking](../outputs/intervention_sensitivity_development/reversal_macro_ranking.csv),
[cell contrasts](../outputs/intervention_sensitivity_development/paired_utility_contrasts.csv),
[metrics](../outputs/intervention_sensitivity_development/metrics.parquet), and
[manifest](../outputs/intervention_sensitivity_development/manifest.json).

## Confirmation and calibration status

The independent 2,000-seed confirmation selected the same design. Promotion-plus-rollback
exceeded promotion-only by 5.51 expected utility units averaged over the six reversal profiles
(95% paired seed-cluster interval [5.32, 5.69]). The hard label cap was respected. However,
the selected zero-deployment-gain rollback null produced 35 rollbacks in 2,000 streams (1.75%);
its nine-cell simultaneous exact upper limit was 2.64%, slightly above the predeclared 2.5%
empirical gate. That block therefore does not by itself clear the calibration criterion.

A separate, frozen 10,000-seed calibration replication used new seeds and no parameter changes.
All nine phase-specific cells had simultaneous upper limits below 2.5%. Under the difficult
zero-deployment-gain null after strong shadow benefit, 132/10,000 streams rolled back (1.32%),
with a familywise upper limit of 1.64%. The false promotion rates were 1.16% under zero gain in
both phases and 1.28% when benefit appeared only after shadow evaluation; their upper limits
were 1.46% and 1.59%, respectively. This replication supports calibration for the frozen
simulator and design. The original 2,000-stream result remains reported separately; the two
blocks are not pooled.

The six-profile macro utility result passes its predeclared independent utility criterion,
and the separate larger calibration replication passes its error-limit criterion. This is
evidence for this bounded, independent Bernoulli simulation only. It is not a causal result on
real data, a guarantee under dependent or delayed feedback, or a novelty claim. The policy
still loses heavily when severe harm begins early: in confirmation, the 10%-onset / -0.10
profile yielded -51.70 utility with 14.6% rollback, while the 10%-onset / -0.20 profile yielded
-60.87 utility despite 96.7% rollback. Mitigation does not erase accumulated harm.
