# Eventwise-scout temporal-context null calibration results

**Status:** passed for the registered 16-cell calibration family. This is finite synthetic
false-promotion evidence, not a power result, deployment guarantee, or novelty claim.

## Calibration result

The CUDA run used 1,000 fresh streams in each of 16 cells (seed block 20275000–20275999), crossing
four deterministic prevalence schedules, two proxy-error rates, and 20%/40% hard label caps. There
were 56 false promotions among 16,000 streams (0.35% overall). Every cell passed the simultaneous
one-sided exact Clopper–Pearson gate at familywise alpha 0.05; the largest observed cell rate was
1.10%, and the largest simultaneous upper limit was 2.3475%, below 5%. All evaluator-defined null
checks, positive propensity checks, and hard-cap checks passed; there were no cap violations.

The maximum upper limit occurred for high-first recurrence, zero proxy error, and the 40% cap: 11
promotions in 1,000 streams, with simultaneous upper limit 2.3475%. The 16 individual cell counts
and limits are in the generated calibration report and Parquet summary.

## Interpretation and limits

This supports the registered eventwise scout's false-promotion gate under the exact event-conditional
Bernoulli null, the four deterministic schedule family, fixed split and candidate set, uniform
randomized query process, immediate complete labels, and specified decision costs. Passing the
calibration permits a separately frozen, disjoint positive-signal confirmation on these temporal
schedules. It does not itself show that the scout detects harm, nor does it cover delayed or
selectively observed labels, adaptive propensities, other dependence structures, unregistered
prevalence paths, or real-world utility.

## Reproduction and artifacts

The frozen design and command are in
[`scout_context_policy_eventwise_temporal_null_protocol.md`](scout_context_policy_eventwise_temporal_null_protocol.md).
Stream records, cell counts and limits, the generated report, and checksummed manifest are in
[`outputs/scout_context_policy_eventwise_temporal_null_1000/`](../outputs/scout_context_policy_eventwise_temporal_null_1000/).
No figure was generated; any future research visual must use PaperBanana.
