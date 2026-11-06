# Wild-Time HuffPost chronological transfer result

**Disposition:** adverse single-source application case study; the frozen PFA-SR transfer gate
failed against both primary comparators. PFA-SR is published prior art; this is not a new-method
claim.

## Frozen setup and eligibility

- Data: Wild-Time HuffPost / News Category Dataset v2, pinned dataset revision
  `khalidalt/HuffPost@01020533529fc1cda0af7d99231eb96e7837f883`; archive SHA-256 is in the
  pretest and opening manifests. Raw data and model weights remain local.
- Historical model windows: incumbent 2012–2013, challenger 2014–2016, validation 2017; test
  window 2018-01-01 through 2018-05-25 inclusive. Frozen class set is the official 11-class
  Wild-Time HuffPost mapping. Models use title-only `HashingVectorizer` plus `SGDClassifier`.
- Corrected validation order is timestamp then original JSONL line ID. The validation gate passed:
  8,786 events; 6,953 disagreements; incumbent-minus-challenger overall error advantage 0.404621;
  conditional disagreement advantage 0.511290; block advantages `[0.419939, 0.374872, 0.419057]`.
- The test opening retained 3,877 usable rows and budget `B=200`. Labels are not source-timestamped
  at annotation release; the replay imposes midnight UTC +24 hours. Same-day requests happen before
  labels due at that midnight are delivered. Policy constructor pacing uses the validation median
  articles per day as an integer event-delay proxy; actual `observe` availability follows the
  timestamp-aware queue.
- Costs: 0.05 per label; 5 per deployment switch; alpha 0.05. Methods share the ordered rows,
  predictions, horizon, budget, simulated availability and costs. Paired intervals use 2,000
  moving-block bootstrap resamples over 7-calendar-day blocks, seed `2026110641`.

## Policy outcomes

| Policy | Net cost | Prediction loss | Labels / label cost | Switches / switch cost | Promotion / rollback | Promotion time |
|---|---:|---:|---:|---:|---:|---|
| PFA-SR, adaptive-range host | 3,163.00 | 3,153 | 200 / 10.00 | 0 / 0 | 0 / 0 | none |
| Matched-host RMM | 2,039.00 | 2,024 | 200 / 10.00 | 1 / 5.00 | 1 / 0 | event 1,498; 2018-02-23 |
| Xu acquisition-only adapter | 1,454.00 | 1,439 | 200 / 10.00 | 1 / 5.00 | 1 / 0 | event 254; 2018-01-11 |
| E_rb, adaptive-range host | 2,039.00 | 2,024 | 200 / 10.00 | 1 / 5.00 | 1 / 0 | event 1,498; 2018-02-23 |
| E_swcert | 1,627.95 | 1,613 | 199 / 9.95 | 1 / 5.00 | 1 / 0 | event 624; 2018-01-25 |
| Never-switch | 3,153.00 | 3,153 | 0 / 0 | 0 / 0 | 0 / 0 | none |

## Primary contrasts

| Contrast: PFA-SR minus comparator | Difference / 1,000 events | 95% time-block interval | Frozen gate |
|---|---:|---:|---|
| Same-host RMM | +289.91 | `[+193.64,+391.18]` | **FAIL** |
| Xu acquisition-only | +440.80 | `[+394.19,+486.84]` | **FAIL** |

The primary gate required at least 5 units saved per 1,000 events and a two-sided 95% interval
below zero against each comparator. PFA-SR instead incurred a clearly higher cost against both.
RMM and E_rb produced identical traces because E_rb never had a promotion followed by a reversal
to monitor on this stream.

## Interpretation and limits

This is a reproducible chronological replay showing late-improvement blindness for PFA-SR in one
validation-selected HuffPost source under scarce labels. The label-release clock is simulated, dates
have day-level granularity, and there is one source cluster. The time-block interval measures
within-source temporal uncertainty; there is no cross-source interval and no causal deployment
claim. Serial dependence means the iid conditional-null guarantee is not established here.

The one-opening runner persisted predictions and trace hashes but not per-event traces or daily
paired cost/count sufficient statistics. An independent analyst therefore cannot recalculate the
bootstrap endpoints from the committed aggregate files. Do not reopen this test window to repair
that limitation.

## Reproduction and provenance

- Frozen code/source/runtime manifest: `code_freeze.json`.
- Ordered candidate/final row registries and durable opening records:
  `TEST_OPENING_STARTED.json`, `TEST_OPENED.json`.
- Validation-only gate and model manifest: `source_eligibility.json`, `pretest_manifest.json`.
- Summary JSON: `transfer_results.json`; prediction and trace hashes:
  `prediction_stream_sha256.json`.
- Runner: `scripts/sota_sprint/run_huffpost_transfer.py`.
- Review: independent protocol-control review before opening and independent aggregate-result
  review after opening are recorded in `docs/scoped_method_research_2026-11-06/INDEPENDENT_REVIEW.md`.
