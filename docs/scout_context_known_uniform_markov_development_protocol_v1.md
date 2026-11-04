# Contextual target scout with exact uniform propensity: Markov development v1

**Frozen:** 2026-11-04, before execution. **Status:** exploratory development only. This protocol
tests whether contextual scout selection helps after all methods use the known uniform query
propensity in their support bounds. It does not test novelty, SOTA performance, or Markov-null
calibration.

## Question

With a uniform query probability equal to each label-budget rate, does the context-specific scout
improve expected postpromotion utility over pooled-rank and nested context-volume selection when
every arm uses the same exact propensity floor? The prior confirmations used a generic floor at half
the actual uniform probability, which confounded their eventwise contrast with support-bound
tightness. This run corrects that comparison and uses new seeds.

## Frozen design

- 60 matched seed clusters, `21,510,000–21,510,059`. A scan of current output manifests found no
  overlapping seed range.
- 108 cells: stationary context prevalence `{0.10, 0.50, 0.90}` × Markov persistence
  `{0.0, 0.50, 0.80}` × signal `{0, 0.05, 0.10}` × proxy error `{0, 0.25}` × label cap `{0.20, 0.40}`.
- Four matched methods: pooled rank, nested context-volume, minimum-bound contextual scout, and
  eventwise-bound contextual scout. Both global and eventwise support bounds use the exact known
  uniform propensity `q_min = q_t = budget_rate`; all methods use the same query uniforms and labels.
- Keep direct IPW, fixed-mixture betting, FN cost 5, FP cost 1, switching charge 0.05, alpha 0.05,
  `n=3,200`, `d=16`, and the existing independent scout/certification split.
- Primary descriptive endpoint: equally weighted expected postpromotion net decision gain over
  the 72 positive-signal cells, paired by seed cluster. Report eventwise-minus-pooled-rank and
  eventwise-minus-nested-volume, overall, by signal, and by persistence. Also report
  eventwise-minus-minimum-bound as an implementation-equivalence check; it should be zero up to
  numerical summation tolerance when the support bounds and paths coincide.
- Save all 25,920 method-cell-seed rows and complete manifests/checksums. Require unique complete
  keys, positive propensities, finite evaluator utility, and no hard-cap violations.

## Interpretation and advance rule

All contrasts and bootstrap intervals are exploratory. Zero-signal rows are diagnostic only and do
not calibrate false-promotion rates under Markov context. A positive contrast can motivate a
separate null-calibration and source-matched prior-art study; it cannot establish an algorithmic
novelty or SOTA claim. Do not reuse these seeds for tuning followed by confirmation. If
eventwise-minus-minimum-bound is materially nonzero, stop interpretation and audit the implementation
before drawing conclusions.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-development `
  --seeds 60 --seed-offset 21510000 --n 3200 --d 16 --device cuda --workers 6 `
  --exact-uniform-propensity-floor `
  --protocol docs/scout_context_known_uniform_markov_development_protocol_v1.md `
  --output outputs/scout_context_known_uniform_markov_development_v1
```
