# Eventwise-scout variance-query temporal null calibration results

**Status:** passed for the registered 16-cell synthetic calibration family on 2026-10-25. This is
false-promotion calibration evidence, not a power result, deployment guarantee, or novelty claim.

## Result

The CUDA run used 1,000 independent streams per cell (fresh seed block `21430000`–`21430999`) and
crossed four gradual/recurring context-prevalence schedules, two proxy-error rates, and two hard
label caps. The tested procedure used validation-fitted predictable variance-weighted queries and
the eventwise-propensity-bound scout. It recorded **92 false promotions among 16,000 streams**
(0.575% overall). All 16 cells passed the Bonferroni simultaneous one-sided exact Clopper–Pearson
gate; the largest observed cell rate was 0.70%, and the largest simultaneous upper limit was
**1.778%**, below 5%. Every evaluator-defined null check, positive propensity-support check, and
hard-cap check passed; there were no cap violations.

All 16,000 stream rows have unique profile/cap/seed/query/method keys. The output manifest records
the frozen protocol, the CUDA/runtime environment, and SHA-256 hashes for source and artifacts.
The per-cell counts and exact bounds are in the calibration report and Parquet summary under
[`outputs/scout_context_policy_eventwise_temporal_variance_null_1000/`](../outputs/scout_context_policy_eventwise_temporal_variance_null_1000/).

## Scope and next step

This supports the false-promotion gate only for the event-conditional Bernoulli null, four registered
deterministic schedules, fixed split and candidate set, validation-fitted variance query process,
immediate complete feedback, and specified decision costs. It does not validate power, delayed or
selective feedback, feedback-adaptive query probabilities, other outcome dependence, or real-world
utility. It permits a separately frozen positive-signal confirmation on disjoint seeds. Any
schedule-level primary comparisons should be frozen before that confirmation, given the marked
heterogeneity in the preceding development grid.

The exact design is in
[`scout_context_policy_eventwise_temporal_variance_null_protocol.md`](scout_context_policy_eventwise_temporal_variance_null_protocol.md).
