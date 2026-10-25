# Eventwise-scout temporal variance-query confirmation results

**Status:** confirmed on the registered synthetic grid, 2026-10-25. This is a finite confirmation
under the frozen design, not a general safety or deployment guarantee and not an algorithmic
novelty claim.

## Confirmatory findings

The CUDA run used 600 matched seed clusters (`21440000`–`21440599`) across 32 positive-signal
profile/cap cells, with uniform and predictable variance-weighted query policies sharing query
randomness. It produced all **153,600** expected stream-method-query rows. The endpoint was
evaluator-known expected postpromotion net decision gain, equally weighted over the 32 cells and
paired by seed cluster.

Under variance-weighted querying, eventwise scouting exceeded pooled rank by **5.598** units, with
an approximate simultaneous one-sided lower limit of **5.008**. It exceeded nested
context-volume by **5.405**, with lower limit **4.815**. Both registered primary limits were
positive, so the grid-level gate passed. The secondary contrast against minimum-propensity
scouting was **+4.384** (descriptive 95% percentile interval `[3.929, 4.856]`).

Eventwise variance-query scouting exceeded its uniform-query counterpart by **+0.742** units
(descriptive 95% interval `[0.430, 1.055]`). This is materially smaller than the earlier
development estimate of +1.668, consistent with development selection and sampling variation. The
uniform-query eventwise scout also performed strongly against the rank baselines in this
confirmation (+4.856 versus pooled rank; +4.658 versus nested context-volume). The primary result
therefore supports the eventwise allocation rule over those rank baselines on this grid; the added
benefit from variance-weighted querying is positive but more modest.

| Context schedule | Signal | Variance minus uniform eventwise gain | Descriptive 95% seed-cluster interval |
| --- | ---: | ---: | ---: |
| Gradual down | 0.05 | +0.009 | [-0.144, 0.164] |
| Gradual down | 0.10 | +0.358 | [-0.136, 0.874] |
| Gradual up | 0.05 | +0.335 | [0.005, 0.687] |
| Gradual up | 0.10 | +1.639 | [0.263, 3.050] |
| Recurring, high first | 0.05 | -0.008 | [-0.117, 0.106] |
| Recurring, high first | 0.10 | +0.871 | [0.279, 1.475] |
| Recurring, low first | 0.05 | +0.286 | [-0.033, 0.614] |
| Recurring, low first | 0.10 | +2.442 | [1.009, 3.901] |

These schedule-by-signal intervals are secondary and descriptive, with no multiplicity adjustment.
They show that the variance-query advantage is near zero at signal 0.05 for two schedules and
larger at signal 0.10, especially for recurring-low-first. The pooled gain should not be read as a
uniform benefit across temporal regimes.

## Safety and integrity

All row keys were unique; every propensity was positive; outcomes were finite; and no realized hard
label cap was exceeded. The two query policies averaged 472.9 and 472.7 labels per stream,
respectively. There were **99 promotions with nonpositive evaluator-known future net utility**
across all method-query streams, including 82 under the eventwise rule. Thus positive expected
utility and calibrated false-promotion control do not make each individual promotion safe.

The independent variance-query temporal null calibration passed its 16-cell gate, with a maximum
simultaneous exact upper bound of 1.778%. This confirmation is limited to the specified
event-conditional null family and synthetic positive-signal alternatives, deterministic prevalence
schedules, fixed split/candidate set, validation-fitted predictable query process, immediate
complete feedback, and specified decision costs. Delayed or selective feedback, query probabilities
adapted to certification evidence, other dependence structures, and real-world utility remain
untested. The seed-cluster bootstrap bounds are approximate.

The frozen [protocol](scout_context_policy_eventwise_temporal_variance_confirmation_protocol.md),
row-level Parquet metrics, cell summaries, contrasts, generated report, and SHA-256 manifest are
preserved under
[`outputs/scout_context_policy_eventwise_temporal_variance_confirmation_600/`](../outputs/scout_context_policy_eventwise_temporal_variance_confirmation_600/).
The bounded-betting monitor remains a standard predictable betting construction, not a new
validity theorem. No figure was planned or generated; use PaperBanana for any future visual.
