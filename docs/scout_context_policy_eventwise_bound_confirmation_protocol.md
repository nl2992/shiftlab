# Eventwise-propensity scout confirmation under abrupt context drift

**Status:** frozen 2026-10-25 after the development screen and independent eventwise-bound null calibration. This confirmation evaluates the eventwise-bound scout on a seed block disjoint from both. It is a synthetic benchmark result, not a novelty test or a general deployment guarantee.

## Confirmatory question and endpoint

Does the eventwise-propensity-bound scout improve evaluator-known postpromotion net decision utility over pooled rank and nested-volume selection on the registered positive-signal context-drift grid?

The primary endpoint is `expected_postpromotion_net_gain`, which uses evaluator-only expected decision costs on events after the certification decision, including the registered switching charge. It is averaged equally over the 24 prevalence × signal × proxy-error × label-cap cells. The learner and certification process do not receive evaluator truth.

The two primary contrasts are eventwise scout minus pooled rank and eventwise scout minus nested-volume. Resample seed IDs as clusters, preserving each seed's matched outcomes across all 24 cells, using 10,000 percentile-bootstrap draws. Report the one-sided 97.5% lower bootstrap limit for each contrast; the two lower limits use Bonferroni allocation for an approximate simultaneous 95% familywise assessment. Call the candidate better on this grid only if both lower limits exceed zero. Also report two-sided 95% seed-cluster percentile intervals. The comparison to the minimum-propensity scout is a prespecified mechanism contrast and is reported with its own two-sided 95% interval, without being part of the primary success gate.

Bootstrap coverage is approximate and relies on independent seed clusters; it is not an exact finite-sample guarantee. The separate null calibration supplies finite-sample Clopper–Pearson limits for the registered null family. Neither result covers unregistered feedback or dependence processes.

## Frozen design

- 600 independent seed clusters, 20270000–20270599. This block is disjoint from the 60-seed development block and the 1,000-seed-per-cell eventwise null calibration.
- The 24 matched cells cross pre/post context prevalence (0.10→0.90, 0.50→0.50, 0.90→0.10), signal strength (0.05, 0.10), proxy error (0, 0.25), and realized label cap (20%, 40%).
- Compare eventwise scout, minimum-propensity scout, pooled rank, and nested-volume on each stream. Use the registered uniform-query design, direct-IPW estimator, fixed-mixture certification, FN cost 5, FP cost 1, switching charge 0.05, context/candidate split, alpha 0.05, `n=3,200`, and `d=16`.
- Require all 57,600 method-cell-seed rows, unique `(cell, budget, seed, method)` keys, positive propensities, verified evaluator truth, and no realized-cap violations. Save cellwise promotion, harmful-promotion, expected and realized utility, labels, and processed-event metrics along with the matched primary contrasts, manifest, protocol hash, and artifact checksums.
- Seed-specific generators make streams independent of execution order. Six workers are used on the registered host, with CUDA generation and one native numerical-library thread per worker. Preserve sorted seed order in output.
- No method or threshold changes are allowed after the protocol is frozen. No figure is planned; use PaperBanana for any future research visual.

Passing the primary gate supports an advantage over the two prespecified baselines on this simulator grid. It does not establish a universal improvement, an application-level utility gain, or algorithmic novelty. If either lower limit is at most zero, retain the eventwise scout as a calibrated but unselected comparator.

## Reproduction

```powershell
uv run shiftlab-dive-scout-drift-confirm `
  --seeds 600 --seed-offset 20270000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_bound_confirmation_protocol.md `
  --output outputs/scout_context_policy_eventwise_bound_confirmation_600
```
