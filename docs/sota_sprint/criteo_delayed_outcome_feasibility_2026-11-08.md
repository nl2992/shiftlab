# Criteo delayed-outcome stream feasibility — 2026-11-08

**Disposition:** structurally usable as a chronological, derived-maturity benchmark; not a measured
label-ingestion trace, not a calibration dataset, and not evidence of a method or SOTA gain.

## Source and local artifact

The [Criteo Attribution dataset card](https://huggingface.co/datasets/criteo/criteo-attribution-dataset)
documents a 30-day sample of impression events sorted by impression timestamp, a binary conversion
indicator for conversions within 30 days, and a conversion timestamp (or `-1`). The card lists
CC BY-NC-SA 4.0. The publisher states that the price and cost-per-order fields are transformed,
not actual prices.

Downloaded artifact (ignored by Git):
`outputs/research_data/criteo_attribution_dataset.tsv.gz`, 653,015,824 bytes,
SHA-256 `94ac7a465564349bc7ba008602211d5990a3c53cc133abc0aadef61ea2391a98`.
The read-only audit runner is [`audit_criteo_attribution_candidate.py`](../../scripts/sota_sprint/audit_criteo_attribution_candidate.py);
its machine-readable output is `outputs/research_data/criteo_feasibility_audit.json` (also ignored).

## Full-file structural findings

- 16,468,027 rows; impression timestamps have zero file-order inversions and range from 0 to
  2,671,199 timestamp units.
- 806,196 rows have `conversion=1`; 15,661,831 have `conversion=0`.
- Every positive-row `conversion_timestamp` is after its impression and within 2,592,000 units
  (30 days); positive delay median is 323,536 units and p99 is 2,503,507 units.
- There are 435,810 distinct positive `conversion_id` values and 370,386 repeated positive-ID
  rows. A single conversion can therefore label multiple impression rows, so rowwise observations
  are dependent. A later evaluation must cluster by user and/or conversion and avoid splitting
  attributed copies of a conversion across train/evaluation partitions.
- The publisher card's headline “45K conversions” does not match the parsed positive impression
  rows (806,196), distinct positive `conversion_id`s (435,810), or distinct IDs among rows with
  `attribution=1` (236,331). These fields count different objects or the headline describes a
  narrower subset; the exact reconciliation is unresolved. Do not report any of these counts as the
  number of unique real-world conversion events without clarifying the schema against the publisher.
- 675 campaign IDs occur in the file.

The structural checks pass for a possible replay rule: reveal a positive at its recorded conversion
timestamp and reveal a negative only at `impression_timestamp + 2,592,000`. The latter is a derived
maturity convention from the 30-day outcome definition, not observed ingestion metadata. The replay
must disclose that distinction and cannot support a claim about production label latency.

## Research value and limits

This dataset offers a real chronological outcome stream for exploring paired fixed-model selection
under sparse delayed labels. It could strengthen the project’s external benchmark evidence if two
models are trained and frozen on a strictly earlier period and compared on later impression events.
It does not provide actual query-label prices or switching costs, and its transformed `cost`/`cpo`
fields must not be used as those prices. The repeated conversion IDs also make a per-row independent
label null implausible without an explicit user/conversion-level conditional model.

Next step, before any performance run: freeze target semantics (conversion vs attribution), a
chronological training/model-freeze/evaluation split with conversion-level leakage control, the
derived label-release convention, the paired predictive utility, and a matched source baseline.
Treat results as descriptive until the inferential assumptions can be justified under repeated
users, campaigns, and conversion dependence. The new model-switching comparator [*The Challenger*]
(https://arxiv.org/html/2512.18390) is prior art for economic replacement and oracle timing, though
its challenger is retrained as more full-feature samples arrive rather than monitored as one of two
fixed models.
