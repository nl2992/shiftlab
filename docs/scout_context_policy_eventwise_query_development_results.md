# Predictable-query eventwise scout development results

**Status:** completed exploratory development, 2026-10-25. This is not null calibration,
independent confirmation, or evidence of a literature gap.

## Design and integrity

The frozen CUDA experiment used 60 matched seed clusters across 36 context-prevalence,
persistence, signal, and proxy-error profiles; two realized label caps; three feature-based query
policies; and four promotion rules. The output contains all 51,840 expected stream-method rows
and 864 profile/cap/method cells. Keys are unique, all three query policies and four rules are
present, propensities remain within registered support, and no realized label cap is exceeded.
The logged eventwise support bound agrees with `5 * mean(1/q_t) + kappa` within `2.5e-14`.
The manifest records the protocol, source, and output hashes. No figure was planned or generated.

## Development findings

Across the 48 positive-signal profile/cap cells, the eventwise-bound scout's evaluator-known
expected postpromotion net gain exceeded the minimum-propensity-bound scout by 5.448 under
uniform queries (seed-cluster descriptive 95% interval [3.731, 7.403]) and by 6.729 under both
variance and decision-value queries (intervals [4.669, 9.034] and [4.661, 9.015]). These
comparisons process the same number of queried labels within each query policy. They indicate
that the less conservative eventwise bound can improve the scout's synthetic-grid utility under
this registered design; they do not establish a safety or calibration guarantee beyond the stated
conditional null and immediate-feedback assumptions.

Within the eventwise-bound rule, variance-weighted queries exceeded uniform by 2.130 expected
net-gain units (descriptive interval [0.722, 3.590]). Mean labels queried differed by only 0.266
(interval [-0.767, 1.260]); the mean process bound increased by 1.288. Decision-value queries
had the same contrasts to rounding.

**The grid did not distinguish variance from decision-value acquisition.** For all 17,280
matched stream-method rows in each policy, their query counts, propensities, eventwise bounds,
promotion decisions, and expected postpromotion utility were exactly equal. This is a property of
the realized score paths in this DGP, not proof that the policy definitions are generally
equivalent. The next query-policy design should first verify on a frozen diagnostic DGP that the
pre-monitor score paths differ materially, then freeze a revised grid before running it.

There were no promotions in any of the 1,440 zero-signal streams per query-policy/rule cell.
These zero-event counts are only development diagnostics, not calibration. Any candidate promoted
from this screen needs fresh null calibration and disjoint confirmation. The current predictable
propensity e-process uses the standard bounded-betting argument with a time-varying support bound;
it is not a new theorem. Delayed or outcome-dependent labels, feedback-dependent query propensities,
and violations of the event-conditional null remain outside the demonstrated scope.

## Reproduction and artifacts

The registered run command is in [`scout_context_policy_eventwise_query_development_protocol.md`](scout_context_policy_eventwise_query_development_protocol.md).
The detailed generated report, stream-level Parquet metrics, cell summaries, contrast and null
summary CSVs, environment metadata, and checksums are stored in
[`outputs/scout_context_policy_eventwise_query_development_60/`](../outputs/scout_context_policy_eventwise_query_development_60/).
