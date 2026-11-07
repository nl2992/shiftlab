# R5 Round-5 focused follow-up protocol

Registered before the new seed block is run (2026-11-05). This is a post-development simulator sensitivity, not untouched real-data confirmation or a theorem test.

## Question and frozen comparison

Does the development-selected R5 operating point at nominal alpha 0.02 retain an empirical cost/risk trade-off on a new seed block, compared on common synthetic streams with D2, A5b, `gated_adaptive_range+front`, and `R:economic_stop`? The primary descriptive contrast is paired per-seed net cost (`R5 - comparator`) averaged over the six registered alternatives in `bench2.RISK_ALTS`. Secondary outcomes are promotion fraction on each of the four `bench2.RISK_NULLS`, pooled false promotion, and alternative cost by regime. Lower net cost is better. This follow-up does not change the selected alpha or select a new alpha after observing results.

The alpha 0.02 point was selected in the existing development Track-R curve for R15/R20/R25; it is evaluated here as a single frozen operating point. The R5 R10/R30 points and full frontier are not re-estimated in this follow-up.

## Data and execution

- Generator and regime definitions: `scripts/sota_sprint/bench2.py` (`RISK_NULLS`, `RISK_ALTS`) and the registered simulator implementation.
- 100 paired synthetic seeds per regime, seed base `2026110901`, distinct from existing R-family development/evaluation blocks and registered before execution.
- Contract alpha 0.02, budget/costs as recorded by `screen.py`; same stream is replayed by all five policies.
- No real-data claim: market/application utility and causal event truth are not available for this synthetic follow-up.
- Preserve raw records and manifest under `outputs/sprint2/round5/R5_eval100_a002/`; analyze without changing the protocol.

## Interpretation limits

This is a post-development robustness check on a new simulator seed block; it is not an independent research-team replication. Comparator choice and R5 selection occurred earlier in this sprint. The five-policy set is fixed for this run and does not constitute a comprehensive SOTA comparison. Empirical null proportions are descriptive rates with binomial uncertainty, not validity guarantees. No success threshold is used to relabel the candidate; report the observed estimates and uncertainty, including unfavorable results.
