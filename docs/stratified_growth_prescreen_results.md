# WP2 G1: stop the stratified algorithm branch

The registered analytic screen failed. The candidate ties the equally equipped
known subgroup composition, so it cannot clear the required 1.5x gain over the
strongest applicable incumbent. Stop WP2 before the 588 development and 589
intersection-null calibration blocks. This is a successful negative screen.

The frozen [protocol](stratified_harm_monitor_development_protocol.md) and visible
pre-run scenario clarification govern this result. Command:
`uv run --no-sync python scripts/run_stratified_growth_prescreen.py`.
CPU runtime was 48.7709 seconds, starting 2026-10-27T14:30:05.125385Z at clean
HEAD `d0a350a08099deb04a51897216b956b3c417a695`. Seeds 58700000–58700019 supplied
only training/validation learner slices. No monitor, outcome coin or query coin
was simulated. All three working laws, three allocations, K={2,4,8} and four
budgets were retained: 19,440 arm rows. No working-law cell was infeasible.

The maximum absolute candidate/composition discrepancy was 4.4409e-16, below
1e-12. All 36 localised budget/K/allocation choices had positive pilot-pooled excess;
none passed the advancement rule. Candidate/strongest growth ratios ranged from
0.4030 to1.0000. Independent atom enumeration supplied the subgroup comparison.

For context, the largest candidate mean localised growth at each budget was:

| Budget | K | Allocation | Mean exact log growth / event | Candidate / strongest | Homogeneous / pooled gated HT |
|---|---:|---|---:|---:|---:|
| .02 | 2 | range limited | .007715 | 1.000 | 1.049 |
| .05 | 2 | range limited | .023239 | 1.000 | 1.260 |
| .10 | 2 | cap dominated | .049675 | 1.000 | 1.572 |
| .20 | 2 | cap dominated | .049737 | 1.000 | 1.573 |

Allocation ties are resolved only for displaying a row; every registered choice
is in the raw tables. These are exact expectations under imposed working laws,
averaged over 20 fitted pilot slices, not measured detection probabilities or
confirmed effects. The K=2 subgroup omits negative agreement factors from its
disagreement component. Its advantage over pooled gating changes the null from
pooled harm to per-stratum harm; it does not establish a superior pooled monitor.
Finite log(K/alpha) penalties and per-stake rates remain in the raw rows.

The output directory is `outputs/stratified_growth_prescreen_20/` (ignored).
Its manifest hashes all executed sources and outputs. Key SHA-256 receipts:

| Artifact | SHA-256 |
|---|---|
| decision.json | e5d5b3c252ba972047fe31f9708419a809ee38c498254b1e9e87a7ae8e465722 |
| rows.jsonl | 937c25e5e50bf0dd1c79790d6f1ca8be6be7e73d25aa8d1a849561900f228dc5 |
| stream_summary.csv | 4f7c9bcb7a25872071f7e7b47665229ce1fb0b882dbd5311732d188b9937dba6 |
| summary.csv | a755c04623c06023c179fdb5c5d62d74feeddaaa356296214c373971c32e55ca |

Focused formula/orientation tests passed 18; runner gate tests passed 4. The final
phase suite passed 1,794 tests with one skip in 971.76 seconds. An independent
artifact audit matched every registered seed, cell and output hash, found zero
spend-cap violations, and reproduced the decision and summary statistics. No
PaperBanana configuration is available; no figure was generated.
Next: finish WP1 and the separately frozen WP3 prescreen, then apply checkpoint B
if their exits are reached. This result alone does not complete the phase.
