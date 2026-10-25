# Eventwise scout confirmation with variance-weighted queries

**Status:** confirmed on the registered synthetic grid, 2026-10-25. This result applies to the
frozen context-heterogeneity generator, immediate feedback, fixed split and specified predictable
query policies; it is not a real-data or deployment guarantee.

## Confirmatory findings

The CUDA run covered 48 positive-signal profile/cap cells and 600 matched seed clusters, yielding
all 230,400 expected method-cell-seed-query rows. The primary endpoint was evaluator-known
expected postpromotion net decision gain, equally weighted over cells and paired by seed. Under
variance-weighted querying, the eventwise scout exceeded pooled rank by 11.2436 units, with a
one-sided Bonferroni-adjusted seed-cluster bootstrap lower limit of 10.3412. It exceeded nested
context-volume by 10.7399, with lower limit 9.8610. Both preregistered primary lower limits were
positive, so the grid-level gate passed.

Secondary contrasts favored the variance-query eventwise scout over the minimum-propensity scout
by 7.2232 units (95% percentile interval [6.6430, 7.8158]) and over the uniform-query eventwise
scout by 1.2304 ([0.7192, 1.7501]). These do not replace the primary comparisons. There were 12
promotions with nonpositive evaluator-known future net utility across all method-query streams;
promotion safety is therefore not perfect even in this registered simulation. All caps and
propensity support checks passed, and the prerequisite 72-cell query-policy null calibration
passed with a largest simultaneous upper limit of 2.743%.

## Audit correction and limits

A post-run code audit found that the initial `variance_eventwise_minus_rank` contrast mistakenly
selected the eventwise rule for both sides. That produced an uninformative zero difference. The
registered comparison was corrected to use pooled rank on the baseline side, then all contrasts,
the report and manifest were recomputed from the saved stream-level metrics. The simulation,
seed block, protocol, candidate, baseline, endpoint and bootstrap procedure were unchanged; no
method was selected or tuned from the confirmation outcomes. The manifest preserves the original
simulation source hashes, current corrected analysis hashes and raw-stream hash.

The intervals use a seed-cluster percentile bootstrap and are approximate. The e-process is the
standard bounded-betting construction with predictable `B_t=C/q_t+kappa`, not a new validity
theorem. This confirmation does not establish validity with delayed or informative feedback,
query probabilities adapted to certification evidence, conditional-null misspecification, or
real-world utility. The variance and decision-value acquisition policies were identical in the
preceding development grid, so no claim distinguishes those two policies. No novelty claim follows.

The [frozen protocol](scout_context_eventwise_query_confirmation_protocol.md), row-level Parquet
metrics, cell metrics, corrected contrasts, report and hashes are preserved under
[`outputs/scout_context_eventwise_query_confirmation_600/`](../outputs/scout_context_eventwise_query_confirmation_600/).
No figure was planned or generated.
