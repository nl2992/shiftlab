# Eventwise target-scout temporal-context development results

**Status:** exploratory development only. This run is not null calibration, confirmation, or a
novelty claim.

## Design and integrity

The frozen CUDA run used 60 matched seed clusters in each of 48 cells: four gradual/recurring
prevalence schedules, signals 0/0.05/0.10, proxy error 0/0.25, and hard label caps 20%/40%. The
seed block was 20274000–20274059. Four methods ran on each shared stream, giving 11,520
method-cell-seed rows. All rows were present and unique; propensity support was positive; all
utilities were finite; there were zero hard-cap violations. The evaluator confirmed nonpositive
expected net gain in all 16 zero-signal cells. Source and artifact hashes, the CUDA environment,
and row-level Parquet metrics are recorded in the output manifest.

## Development contrasts

Equal-cell paired mean differences in expected postpromotion net gain, eventwise minus comparator,
were:

| Comparator | Mean difference | Descriptive seed-cluster 95% interval |
| --- | ---: | ---: |
| Minimum-propensity scout | +3.829 | [2.729, 4.971] |
| Pooled candidate rank | +5.503 | [4.051, 7.052] |
| Nested context-volume allocation | +5.281 | [3.896, 6.756] |

These are exploratory intervals across the 32 positive-signal cells, not confirmatory or
multiplicity-adjusted evidence. The differences were concentrated at signal 0.10: averaged over
schedules, proxy errors, and caps, the eventwise-minus-rank contrast was +10.493 at 0.10 and +0.513
at 0.05. At 0.05 the contrast against rank was nearly zero for the high-first recurring profile
(+0.019). At 0.10 it was positive in each schedule, ranging from +5.016 on high-first recurrence
to +17.882 on low-first recurrence. This heterogeneity argues against a broad uniform-power claim.

The eventwise scout promoted 1/960 zero-signal streams, 12/960 streams at signal 0.05, and 100/960
streams at signal 0.10. One zero-signal promotion and four signal-0.10 promotions had nonpositive
evaluator-known realized future net utility. These are sparse development diagnostics, not a
false-promotion rate estimate. The mean number of queried labels was 474.63 per stream for each
method under this matched uniform-query design.

## Interpretation and next gate

The development screen supports spending computation on an independent temporal-schedule null
calibration: the average paired contrasts are positive, including in all four schedules at signal
0.10, and the generator's eventwise null and budget invariants held. It does not justify immediate
confirmation. The 0.05-signal gains are small, especially for high-first recurrence, and the
development null count cannot certify the promotion probability. The next step is a fresh
1,000-stream-per-cell calibration for the exact eventwise scout across all four schedules, two proxy
errors, and two label caps, with simultaneous exact one-sided Clopper–Pearson upper limits. Only if
every one of the 16 cells passes the registered 5% familywise gate should a disjoint positive-signal
confirmation proceed.

The result remains limited to the registered event-conditional Bernoulli simulator, deterministic
prevalence schedule, fixed candidate family and split, immediate complete labels, uniform query
process, and specified costs. It does not establish robustness to delayed/selective feedback,
adaptive propensities, real-world outcomes, or any general safe-adaptation guarantee. No figure was
generated; any future research visual must use PaperBanana.

## Reproduction and artifacts

The frozen design and command are in
[`scout_context_policy_eventwise_temporal_development_protocol.md`](scout_context_policy_eventwise_temporal_development_protocol.md).
The complete row-level data, cell summaries, contrasts, generated report, and manifest are in
[`outputs/scout_context_policy_eventwise_temporal_development_60/`](../outputs/scout_context_policy_eventwise_temporal_development_60/).
