# C4 Amendment A2: sequential batches until 8 supporting datasets (registered 2026-11-08)

Committed **after** the batch-1 opening ([c4_results.md](c4_results.md), 5 of 9 supporting) and
**before** any batch-2 source is built. The user instructed on 2026-11-08 to keep adding
datasets until 8 support the claim.

## Unchanged

- Claim: arm B `EQSDp_l0.9_g0.2` (frozen since `10ba0237`) vs tuned Gong–Zhang-style
  `gongT_w100_m10`.
- Contract: B=200, c_q=.05, c_s=5, 10 policy seeds per episode.
- Builder recipe and gates: `c4_build.py`, ≥35 episodes, ≥3% disagreement.
- Source brief rules; coordinator leakage audit before registration.
- **Per-dataset criterion:** one-sided 95% episode-bootstrap upper bound of mean Δ < 0.
- One dataset per organisation; one per city is the sensitivity count.
- Batch-1 results are final and are never re-analysed or dropped.

## Batch procedure

1. Build candidate sources and audit them. Every eligible, audit-passing source of the batch
   is listed with its sealed hash in `c4_registration_batch<k>.json`, which is committed
   before that batch is opened.
2. A batch is opened once with `c4_confirm.py` (`C4_REG` pointing at the batch registration,
   batch-specific seed base) and analysed with the locked per-dataset rule.
3. The cumulative tally X/N counts all datasets opened in all batches.
4. **Stopping rule:** stop when the cumulative distinct-organisation supporters reach 8, or
   when no further eligible public source can be built within the brief.

## Multiplicity-aware reporting (new; required because stopping is outcome-dependent)

Continuing until 8 datasets pass a 5%-level test would eventually succeed even with no effect.
The paper therefore reports, for the final cumulative set:

- **X / N**, where N is every opened dataset in every batch.
- **The count test.** Under H0 (arm B no better than the comparator on any dataset), each
  dataset supports with probability ≤ .05, independently across sources. So
  P(X ≥ x | N) ≤ BinomialSF(x−1; N, .05). This bound holds at every N, so it is a valid
  sequential count test.
- **The sign test** over all N datasets on mean Δ.
- **The pooled secondary** (vs Qiu-style), as before.

The ≥8 target is the user's practical bar. The inferential statements are the tests above.

## Disclosure of outcome-informed source selection

The batch-2 candidate pool was chosen after batch-1 results were known: 311-type closure
streams supported most often there. That selection is reported as such. The per-batch
tallies and binomial tests are reported separately as well as cumulatively.

## Analysis

`scripts/qsg_methods_search/analyze_c4_batches.py`: applies the locked per-dataset rule to each
batch's records and prints the cumulative X/N, the binomial count bound, the sign test and the
pooled secondary.
