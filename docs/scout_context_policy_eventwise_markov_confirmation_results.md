# Eventwise-scout confirmation under persistent contexts

## Frozen question and prerequisite

The confirmation tested whether the eventwise-propensity-bound target scout improves expected
postpromotion net decision gain over pooled rank and nested context-volume selection on the frozen
stationary Markov-context alternatives. It used the design in
[`scout_context_policy_eventwise_markov_confirmation_protocol.md`](scout_context_policy_eventwise_markov_confirmation_protocol.md).
Before running, the implementation verified the independent eventwise Markov null calibration in
[`scout_context_policy_eventwise_markov_null_results.md`](scout_context_policy_eventwise_markov_null_results.md),
which passed all 36 simultaneous cellwise limits.

## Confirmation result

The CUDA run used 600 matched seed clusters (20910000–20910599), 3,200 events and 16 features,
across all 72 positive-signal prevalence × persistence × signal × proxy-error × budget cells. Four
methods were evaluated on shared streams, producing 172,800 method-cell-seed rows.

| Paired contrast | Mean expected-net-gain difference | Descriptive 95% seed-cluster bootstrap interval | Approx. familywise one-sided lower limit |
| --- | ---: | ---: | ---: |
| Eventwise − pooled rank | +10.5668 | [+9.7393, +11.4169] | +9.7393 |
| Eventwise − nested context-volume | +10.1697 | [+9.3472, +11.0016] | +9.3472 |
| Eventwise − minimum-bound scout (secondary) | +6.3994 | [+5.8941, +6.8970] | Not primary |

Both preregistered primary lower limits exceed zero, so the frozen grid-level confirmation gate
passed. Equal-cell mean expected postpromotion net gain was 13.0475 for eventwise scout, 6.6481
for minimum-bound scout, 2.8778 for nested context-volume, and 2.4807 for pooled rank. The paired
eventwise advantage remained positive in descriptive signal strata (eventwise minus rank +2.2528
at signal 0.05 and +18.8808 at 0.10) and persistence strata (eventwise minus rank +8.7463, +11.6586,
and +11.2954 at persistence 0, 0.5, and 0.8). These subgroup summaries were not separately tested.

Eventwise promoted 3,570/43,200 streams (8.26%); 11 promotions had nonpositive evaluator-known
future net utility. Pooled rank promoted 679, nested volume 714, and the minimum-bound scout 1,631;
none had a harmful promotion in this confirmation block. All methods averaged 472.79 queried labels
per stream across the equally weighted caps, with zero cap violations. Every propensity was
positive, all 172,800 keys were unique, and all expected records were present.

The paired seed-cluster percentile bootstrap supplies approximate uncertainty for these contrasts;
it is not an exact finite-sample guarantee. No cellwise inference was registered. The result supports
the eventwise scout on this frozen persistent-context synthetic grid, subject to its passed null
calibration and the feedback assumptions below. It is not a general superiority or novelty claim.

## Scope and next research step

The result depends on predictable candidate selection before certification, the registered
certification split, uniform randomized querying with known positive propensities, bounded paired
costs, immediate feedback, and the event-conditional cost null. The Markov process applies to the
learner-visible context; this does not establish validity for serially dependent outcomes, delayed or
selective labels, adaptive query propensities, gradual/recurring nonstationary prevalence, or real
application costs.

Retain the eventwise scout as a supported candidate for further synthetic stress tests. The next
grid should test gradual and recurring context-prevalence schedules, with a fresh null calibration
for every process that preserves the registered conditional null. Delayed feedback and adaptive
query selection need their own filtration and support arguments. Compare against established
sequential policy-selection and safe-adaptation methods before any novelty claim.

The frozen protocol, all three Parquet files, report, passed-calibration reference, environment, and
checksums are preserved in
[`outputs/scout_context_policy_eventwise_markov_confirmation_600/`](../outputs/scout_context_policy_eventwise_markov_confirmation_600/).
No figure was generated.
