# Eventwise scout null calibration with predictable query policies

**Status:** passed on 2026-10-25. This is independent false-promotion calibration under the
registered synthetic conditional null; it is not positive-signal confirmation or a real-data
guarantee.

The frozen CUDA run used 1,000 fresh seeds (`21210000–21210999`) in each of 72 simultaneous
cells: uniform or variance-based querying × three context prevalences × three Markov persistence
values × two proxy-error rates × two label caps. It produced all 72,000 expected stream rows with
unique keys. All evaluator-defined null flags and propensity-support checks passed, and there were
no hard-cap violations.

Across 36 cells per query policy, uniform querying produced 167 false promotions (0.464% overall)
and variance querying produced 206 (0.572% overall). The maximum cellwise observed rate was 1.2%
for uniform and 0.9% for variance. With Bonferroni simultaneous one-sided exact Clopper–Pearson
limits over all 72 cells, the maximum upper limit was 2.743% for uniform and 2.307% for variance;
all cells passed the registered 5% gate. The largest upper limit across the whole family was
2.743%.

This supports the eventwise bounded-betting monitor under the stated event-conditional null,
pre-monitor feature-based query probabilities, immediate feedback, Markov-context family, split,
and candidate-selection procedure. It does not establish power, net utility, validity with
feedback-dependent query rules or delayed/informative labels, or any novelty claim. A disjoint
positive-signal confirmation is required before making the selected eventwise-plus-variance
strategy claim. The variance and decision-value policies were identical in the preceding
development experiment; only variance is treated as a candidate policy here.

The [protocol](scout_context_eventwise_query_null_calibration_protocol.md), full
[stream and cell metrics](../outputs/scout_context_eventwise_query_null_calibration_1000/metrics/),
generated [calibration report](../outputs/scout_context_eventwise_query_null_calibration_1000/reports/eventwise_markov_null_calibration.md),
and [manifest](../outputs/scout_context_eventwise_query_null_calibration_1000/reports/manifest.json)
preserve the design, environment, source hashes, and artifact checksums. No figure was generated.
