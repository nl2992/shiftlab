# Pilot decision and Failure Atlas update

**Disposition: `BENCHMARK_OR_CASE_STUDY_ONLY`.** This bounded development run does not support a
publishable repair claim. Close the Beta(2,1) prior lane; do not tune it or open real-data outcomes.

## Failure Atlas entry

Under `S_late_1500@B100` (T=2,000, 100-label cap, c_q=0.05, c_s=5, alpha=0.05), the published
gated certificate/adaptation panel did not promote to the improving challenger in any of 100 paired
streams. The never-switch reference remained cheaper on average (356.820 vs 361.782 for the best
mean panel policy and 361.797 for Beta2). P6 promoted in only 5/100 streams, at mean event 1937.6
among promotions, after spending essentially the full query budget (99.94 labels). This is a
reproducible late-improvement / scarce-budget blindness phenotype. Its economic significance is
limited: the realized late advantage leaves little horizon to repay query and switch costs, and this
experiment does not establish a safety-qualified economic opportunity.

The fixed Beta(2,1) start prior is a controlled intervention on the restart-weight allocation: it
changes no host, label acquisition rule, cost, threshold or simulator semantics relative to P6's
uniform prior. On the primary target, Beta2 differs from P6 uniform by -0.020 net-cost units (paired
95% bootstrap CI [-0.140, 0.100]) and from `gated_adaptive_range+front` by +0.015
([-0.318, 0.241]). It promoted in 5% of streams at an average event index 1937.6. This is consistent
with the weighting failing to overcome budget exhaustion and lack of time to amortize promotion;
it does not isolate the sole cause of the baseline failure.

## Gate results

- **Primary economic gate: FAIL.** Candidate-minus-strongest-mean published comparator was +0.015
  units, 95% paired bootstrap CI [-0.318, 0.241], versus the required <= -5 units and interval
  wholly below zero.
- **Mechanism/ablation: PARTIAL.** The prior intervention changed outcomes on the late-1200 and
  reversal cells, but the primary result is near-zero and the candidate was worse than several
  methods on delayed and ordinary-better cells. This does not identify a robust useful repair.
- **Null diagnostic:** 0/100 candidate promotions on `F5_dep_null_r8`; Wilson 95% interval
  [0.000%, 3.699%]. Descriptive only, not evidence of a formal guarantee.
- **Novelty: FAIL.** The Beta(2,1) weighted finite restart mixture is a conventional prior-weight
  choice. No independent original method contribution is established.
- **Real-world validation: FAIL / NOT RUN.** No new real data was opened for this lane. Prior exposed
  HuffPost results remain adverse and are not independent confirmation.

## Four contribution assessment

| Contribution | Status | Basis |
|---|---|---|
| Diagnosis | PARTIAL | Reproduced late promotion blindness in the frozen synthetic late/low-budget cell, but net economic headroom is not established. |
| Explanation | PARTIAL | Controlled prior ablation and time/budget measures support a budget-exhaustion explanation; they do not fully identify the mechanism. |
| Repair | FAIL | No practical advantage on the primary target, adverse cells remain, and the change is conventional rather than novel. |
| Validation | FAIL | No untouched independent real-world evidence for this candidate; real evaluation was correctly withheld. |

## Analysis limitation

The protocol froze the full comparator panel and the pairwise endpoint but did not name a single
published primary comparator in advance. The summary labels the lowest observed mean in the fixed
published panel as the strongest comparator. Since the candidate fails the margin against that
choice and does not show a five-unit advantage against any comparator, this does not change the
decision; the comparison remains development evidence, not confirmatory inference. The confidence
intervals are pointwise, not multiplicity-adjusted.

## Reproduction

The compressed episode records and runner manifest are stored beside this decision. From the repo
root, regenerate the summary with:

```sh
uv run python research/scoped_method/pilots/p6_beta2_bounded_development_20261107/analyze.py
```

The original run used the command and frozen seed/base/panel in `PROTOCOL.md`; its full manifest,
raw-record checksum, compressed-record checksum, and analysis checksum are recorded in
`RESULTS.md`. The smallest next step is to stop this candidate search and prepare the bounded,
honest benchmark/case-study manuscript package from the accumulated registered results.
