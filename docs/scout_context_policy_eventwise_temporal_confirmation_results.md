# Eventwise-scout temporal-context confirmation results

**Status:** primary gate passed on the frozen registered grid. This is a synthetic benchmark
confirmation, not a novelty or deployment claim.

## Design and integrity

The CUDA confirmation used 600 matched seed clusters (20920000–20920599), 3,200 events and 16
features, across 32 positive-signal cells: four gradual/recurring context schedules, signal 0.05 or
0.10, proxy error 0 or 0.25, and 20% or 40% label cap. Four methods ran on each shared stream,
producing all 76,800 expected method-cell-seed rows. The null prerequisite was the committed,
passed 16-cell calibration at normalized manifest SHA-256
`1c81c4f6812d237d4a455ecdcf10fdfc8e824683e91139f04393b9243a5485e6`.

All keys were unique, every propensity was positive, every utility was finite, and no label cap was
exceeded. Each method queried an average of 472.06 labels per stream, as expected from the matched
uniform-query design.

## Primary result

The endpoint is evaluator-known expected postpromotion net decision gain, equally weighted over
cells and paired by seed cluster. The eventwise scout exceeded both frozen primary comparators:

| Contrast | Mean paired difference | 95% seed-cluster bootstrap interval | Approximate simultaneous one-sided lower limit |
| --- | ---: | ---: | ---: |
| Eventwise − pooled rank | +4.727 | [4.216, 5.266] | +4.216 |
| Eventwise − nested context-volume | +4.467 | [3.974, 4.976] | +3.974 |

Both one-sided 97.5% lower limits were positive, so the predeclared Bonferroni-adjusted primary
gate passed. Eventwise also exceeded the minimum-propensity scout by +3.485 (descriptive 95%
interval [3.090, 3.886]). Bootstrap coverage is approximate; these are not exact finite-sample
confidence guarantees.

The benefit varied by signal and schedule. The eventwise-minus-rank contrast averaged +0.650 at
signal 0.05 and +8.803 at 0.10. Averaged over both signals, the contrast was +2.031 for gradual
down, +6.212 for gradual up, +2.967 for high-first recurrence, and +7.696 for low-first recurrence.
This supports an average advantage on the registered grid, not uniform superiority at every harm
level or schedule.

## Promotion quality and limits

The eventwise scout promoted 1,018 of 19,200 method-streams and 62 of those promotions had
nonpositive evaluator-known realized future net utility. Across all four methods there were 90 such
harmful promotions; the other methods promoted 329 times combined. These outcomes show that positive
average expected net gain does not make every individual promotion beneficial. The calibration
controls false promotion under the specified null; it does not guarantee that each alternative
promotion is safe.

The result applies only to the registered event-conditional Bernoulli simulator, deterministic
prevalence schedules, fixed candidate family and split, immediate complete labels, uniform query
process, and FN/FP/switching costs. It does not cover delayed or selective labels, adaptive query
propensities, unregistered paths, other outcome dependence, or real-world utility. The method uses a
standard predictable bounded-factor argument in this setting; no novel algorithm or general safe
adaptation guarantee is established.

## Reproduction and artifacts

The frozen design and calibration prerequisite are in
[`scout_context_policy_eventwise_temporal_confirmation_protocol.md`](scout_context_policy_eventwise_temporal_confirmation_protocol.md).
The full stream and cell metrics, paired contrasts, generated report, and checksummed manifest are
in [`outputs/scout_context_policy_eventwise_temporal_confirmation_600/`](../outputs/scout_context_policy_eventwise_temporal_confirmation_600/).
No figure was generated; any future research visual must use PaperBanana.
