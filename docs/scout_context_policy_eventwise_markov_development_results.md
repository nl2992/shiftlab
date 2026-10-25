# Eventwise target-scout development under persistent contexts

## Question and status

This exploratory CUDA development screen tested whether the eventwise-propensity-bound scout's
utility advantage persists when learner-visible contexts follow a stationary two-state Markov
process. It used the protocol frozen before execution in
[`scout_context_policy_eventwise_markov_development_protocol.md`](scout_context_policy_eventwise_markov_development_protocol.md).
It is development evidence only: the positive-signal contrasts are descriptive and the
zero-signal streams do not calibrate false-promotion error for this method and DGP.

## Design and integrity

The run used 60 matched seed clusters (20273000–20273059), 3,200 events, 16 features, CUDA
generation on an NVIDIA GeForce RTX 4060 Laptop GPU, and six worker processes. It crossed three
stationary context prevalences, three persistence values, three signal strengths, two proxy-error
rates, and two hard label caps. Four methods were evaluated on each shared stream: pooled rank,
nested context-volume rank, the minimum-propensity scout, and the eventwise-propensity-bound scout.

All 108 cells and all 25,920 method-cell-seed records are present with unique keys, positive
propensities, finite evaluator utility, and zero hard-cap violations. All methods used the same
query realization within each seed and cap. SHA-256 checksums for all four data/report artifacts
and 68 source files in the manifest were independently rechecked; there were no mismatches. The
run manifest records the environment, seeds, design, and frozen-protocol hash. The output contains
three Parquet files, a Markdown report, and the manifest; no figure was generated.

## Results

On the 72 positive-signal cells, the eventwise scout's equally weighted expected postpromotion net
gain exceeded:

| Paired contrast | Mean difference | Descriptive 95% seed-cluster bootstrap interval |
| --- | ---: | ---: |
| Eventwise − minimum-bound scout | +5.468 | [+4.090, +6.967] |
| Eventwise − pooled rank | +8.502 | [+6.244, +10.805] |
| Eventwise − nested context-volume | +8.080 | [+6.008, +10.274] |

These are exploratory intervals over the registered cells, not confirmatory or familywise
inference. The advantage was larger at signal 0.10 than 0.05: eventwise minus minimum-bound was
+9.525 (descriptive interval [+7.079, +12.164]) and +1.410 ([+0.672, +2.289]), respectively.
Against the minimum-bound scout, the differences were +3.883 at persistence 0, +6.103 at 0.5,
and +6.418 at 0.8; each descriptive interval excluded zero. Thus, in this design, the advantage
did not disappear as context persistence increased.

The eventwise scout promoted 291/6,480 streams overall, including 286 positive-signal promotions;
7 promotions had negative evaluator-known net utility. In the zero-signal controls it promoted
5/2,160 streams (all at the 40% cap). These five observations are diagnostics, not an estimate
that certifies the false-promotion rate. The other methods promoted 44/6,480 (rank), 50/6,480
(nested volume), and 115/6,480 (minimum-bound scout). All methods averaged 473.44 queried labels
per stream across the equally weighted caps.

## Interpretation and next gate

The positive-signal utility result supported continuing to test the eventwise scout under persistent
contexts. A fresh eventwise-specific Markov null calibration has since passed all 36 simultaneous
cellwise exact upper-limit gates using 1,000 streams per cell; the largest upper limit was 3.175%.
See [`scout_context_policy_eventwise_markov_null_results.md`](scout_context_policy_eventwise_markov_null_results.md).
This calibration now permits a disjoint positive-signal Markov confirmation under the same
registered design; it does not extend the error-control evidence to other feedback regimes.

The result still relies on uniform randomized querying, immediate feedback, the fixed split,
bounded paired costs, predictable scout selection, and the registered synthetic oracle. It does not
establish robustness to gradual or recurring context prevalence, delayed or selective labels,
adaptive query propensities, or real data. No algorithmic novelty claim follows. Full per-stream
metrics, cell summaries, contrasts, checksums, and environment are preserved in
[`outputs/scout_context_policy_eventwise_markov_development_60/`](../outputs/scout_context_policy_eventwise_markov_development_60/).
