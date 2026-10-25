# Temporal context × query-policy development results

**Status:** exploratory development, completed 2026-10-25 on CUDA. These results do not authorize a
calibration, confirmation, safety, or novelty claim.

## Design and integrity

The frozen grid crossed four gradual/recurring context schedules, three context signal strengths,
two proxy-error levels, two label-budget rates, two predictable query policies, four allocation
methods, and 60 matched seed clusters (`21420000`–`21420059`). The RTX 4060 CUDA run produced all
23,040 expected stream-method rows and 384 cell-summary rows. Every row key was unique, query
propensities were positive, all realized label caps held, all outcomes were finite, and the
zero-signal expected-gain checks passed. Uniform and variance-weighted queries shared query
uniforms as registered. The run manifest records configuration, protocol/source/artifact hashes,
and the descriptive contrasts under
[`outputs/scout_context_temporal_query_development_60/`](../outputs/scout_context_temporal_query_development_60/).

## Main descriptive comparisons

Across the 32 positive-signal profile/cap cells, equally weighted and paired by seed, eventwise
scouting exceeded the minimum-propensity scout by **2.470** net-gain units under uniform querying
(seed-cluster 95% descriptive interval `[1.635, 3.373]`) and **4.385** under variance querying
(`[2.989, 5.932]`). It exceeded pooled rank by **4.313** under uniform (`[2.861, 5.923]`) and
**6.013** under variance (`[3.999, 8.290]`), and nested context-volume rank by **3.964** under
uniform (`[2.562, 5.498]`) and **5.637** under variance (`[3.745, 7.776]`).

The eventwise scout with variance-weighted queries exceeded its uniform-query counterpart by
**1.668** units, with a descriptive seed-cluster percentile interval `[0.426, 2.956]`. This pooled
comparison averages across schedules, signal levels, proxy errors, and caps. It is not a
confirmatory estimate.

| Context schedule | Signal | Variance minus uniform eventwise gain | Descriptive 95% seed-cluster interval |
| --- | ---: | ---: | ---: |
| Gradual down | 0.05 | +0.270 | [-0.016, 0.725] |
| Gradual down | 0.10 | +1.075 | [-0.523, 2.702] |
| Gradual up | 0.05 | +0.247 | [-0.819, 1.334] |
| Gradual up | 0.10 | +5.846 | [1.062, 11.235] |
| Recurring, high first | 0.05 | -0.225 | [-0.870, 0.329] |
| Recurring, high first | 0.10 | +0.842 | [-1.557, 3.229] |
| Recurring, low first | 0.05 | +1.189 | [0.001, 2.801] |
| Recurring, low first | 0.10 | +4.101 | [-0.865, 9.625] |

These schedule-level intervals are descriptive and were examined after seeing the grid; they have
no multiplicity adjustment. The weak and occasionally negative estimates at signal 0.05 and the
wide intervals at signal 0.10 show that the pooled advantage is not uniform across temporal
profiles. Proxy error attenuated the pooled variance-query advantage: the mean contrast was +2.867
and +2.677 at proxy error 0, versus +0.510 and +0.619 at error 0.25 for budget rates 0.20 and 0.40,
respectively.

## Interpretation and next decision

The result supports further study of variance-weighted evidence collection under temporal context
changes, but does not establish it as a robust winner. The earlier query-policy null calibration
covered a separately registered immediate-feedback Markov family, not these temporal schedules.
This run also relies on synthetic context prevalence and immediate feedback. It does not assess
delayed or informative labels, certification-history-adaptive querying, or real-world utility.

Before advancing variance querying, freeze an independent temporal null calibration for the exact
predictable variance-query policy and these temporal schedules. Then use a disjoint positive-signal
confirmation with prespecified schedule-level endpoints; keep the pooled result secondary because
the current schedule heterogeneity is material. Any validity statement must retain the
event-conditional null and feedback assumptions. The bounded-betting process remains standard
mathematics, and no novelty claim follows from this study.

The analysis protocol is [`scout_context_policy_eventwise_temporal_query_development_protocol.md`](scout_context_policy_eventwise_temporal_query_development_protocol.md).
