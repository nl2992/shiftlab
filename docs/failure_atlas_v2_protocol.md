# Failure Atlas v2 protocol: discover, repair, beat SOTA

Registered 2026-11-03 on branch `claude/failure-atlas-v2-sota-195428`, which merges
`research/atlas-local-checkpoint-2026-11-01` and `research/b3-generalisation-icml` without
modifying any v1 or SOTA-programme result. Result namespace: `outputs/failure_atlas_v2/`
(git-ignored raw records) and `docs/failure_atlas_v2_*` (committed summaries).

## Contract

Primary v2 contract: T=2000 events, hard label budget B=200, label price c_q=.05, switching cost
c_s=5, anytime level alpha=.05, 100 paired seeds per synthetic regime. Net cost
J = prediction loss + c_q * labels + c_s * switches. Every policy runs through the common
simulator `scripts/promising_directions/sota/simulator.py` (delayed release, frozen issue-time
propensities, pathwise budget enforcement). The v1 Atlas configurations and cycle-7 results are
untouched historical comparisons; this is a separately identified evaluation.

## Seeds and stages (locked before any development result is inspected)

| Stage | Seed base | Seeds | Data | Purpose |
|---|---|---|---|---|
| Discovery | 20261103 | 0-99 | 20 regimes F0-F9; 9 real streams, 20 replay seeds per episode | baseline failure atlas |
| Development | 20261103 | 100-199 | same regimes | build/ablate repairs |
| Validation | 20261104 | 5000-5099 | NEW neighbour regimes (below), never run before | confirm |
| Real validation | 20261104 | replay seeds 1000-1019 | 9 real streams | external relevance |

Validation regimes (`regimes.VALIDATION_REGIMES`, added before development results are read):
late improvement at 600/1000/1400 with p_after in {.65,.72}; transient [500,1200]; reversal at
1000; recurrent with period 400; stationary better p=.62 and p=.7; null p=.5; worse p=.4;
Markov null rho=.8; delay 50 and 250 variants of late-1000. Real streams are not fresh data:
they were exposed in B3 and in discovery here. Real-data results are therefore labelled
"replay on exposed streams" unless new streams are added.

## Comparators

Published registry (adapters named as in `SOTA_IMPLEMENTATION_VALIDATION.md`): Gated deployment
(MOPE CS), DISCERN-style, SMCS + retain-incumbent, Model Picker, Model Selector causal adapter,
Online LLM Picker, Xu acquisition-only, CAMS with constant policies, variance-min + streaming IPW,
and three adapters added on 2026-11-03 from the printed algorithm boxes: Gong & Zhang Alg. 1
(paid observations), Qiu et al. Alg. 1-3 (parameter-free movement-cost OCO), Ryabchenko et al.
delayed FTRL with capacity. Not run: Sawade calibrated, Xu prediction-assisted, CAMS contextual
(need features); The Challenger (learning-curve retraining setting; no frozen-model rule).
Controls: never-switch, development-tuned economic replacement, P7s (ours, prior).

Strongest-reading variants are added where our shared adapter may be weaker than the paper:
Gated and DISCERN with front-loaded acquisition (q=1 on every disagreement until the verdict).

## Primary comparison for a repair R attached to base A

1. Paired difference J(A+R) - J(A) per seed, averaged within regime, then over regimes in the
   declared family; percentile bootstrap over seeds (95%).
2. SOTA comparison: J(A+R) against the lowest-cost published comparator per regime, separately
   within the error-controlled class (methods with an anytime promotion guarantee: Gated,
   DISCERN, SMCS, and their strongest readings) and against all methods.
3. Safety: false-promotion frequency on validation nulls with Wilson 95% upper bound; a repair
   whose upper bound exceeds .10 on the independent null fails safety.
4. Stationary harm: on stationary validation regimes the mean paired increase must be below
   +2 cost units (0.1% of horizon) or the repair is reported as regime-specific only.

Success = (1) significant improvement for at least three bases on the declared family, (2) A+R
beats the best error-controlled published method on that family with paired CI below zero,
(3) safety and harm criteria pass. Anything else is reported as exploratory.
