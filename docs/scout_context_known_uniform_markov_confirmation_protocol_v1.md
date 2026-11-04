# Exact-uniform contextual scout: Markov confirmation v1

**Frozen:** 2026-11-04 after the registered exact-floor development and null calibration. This is a
single disjoint confirmation of the contextual selection comparison. It is not a broad SOTA claim.

## Prerequisites

- The exact-floor exploratory development used seeds `21,510,000–21,510,059`; its eventwise-minus-
  minimum-bound utility contrast was exactly zero, while eventwise exceeded rank and nested-volume
  on the positive-signal grid. The full results are in
  `outputs/scout_context_known_uniform_markov_development_v1/`.
- The Markov null calibration passed on 36,000 streams, 1,000 per cell, with 95 total false
  promotions and zero cap violations. Every simultaneous one-sided Clopper–Pearson upper limit was
  at most 0.02051, below 0.05. The calibration manifest SHA-256 is
  `CA1C805F3F63632C13E6D6CA3D5A2B452EB7175AC14D265CFA900BA9D9B89642`.
- The calibration covers only the registered synthetic conditional-mean null, context process,
  uniform query rule, exact support floor, monitor, and stopping rule.

## Frozen comparison

- Use 600 matched seed clusters, `21,700,000–21,700,599`. A scan of current output manifests
  found no overlap with this block.
- Cross prevalence `{0.10, 0.50, 0.90}` × Markov persistence `{0.0, 0.50, 0.80}` × positive
  signal `{0.05, 0.10}` × proxy error `{0, 0.25}` × budget rate `{0.20, 0.40}`: 72 alternative
  cells, plus the required preregistered comparison arms per stream.
- Compare the contextual scout with pooled-rank and nested context-volume selection on matched
  streams. The minimum-bound and eventwise-bound scout arms both use `q_min=q_t=budget_rate`; their
  paired difference is an implementation-equivalence check, not a discovery contrast.
- Keep direct IPW, fixed-mixture betting, alpha 0.05, FN cost 5, FP cost 1, switching charge 0.05,
  `n=3,200`, `d=16`, and the existing independent scout/certification split. Use uniform querying
  and the exact known uniform propensity floor in every arm.
- Primary endpoint: evaluator-known expected postpromotion net decision gain, equally weighted
  over the 72 positive-signal cells and paired by seed cluster. The two primary contrasts are
  eventwise scout minus pooled rank and eventwise scout minus nested context-volume. Require both
  one-sided 97.5% seed-cluster bootstrap lower limits to exceed zero. The eventwise-minus-minimum
  scout contrast must be zero up to numerical tolerance; otherwise stop and audit.
- Require all expected rows, unique keys, positive propensities, no cap violations, and the exact
  passed calibration manifest hash above. Development and calibration seed blocks are prohibited
  for confirmation.

## Interpretation

A pass would establish a matched synthetic-context result for this registered grid, not novelty or
SOTA. Before describing an algorithmic contribution, compare the contextual selection procedure
with applicable source-faithful anytime-valid contextual-bandit/OPE methods under the same target,
null, query schedule, hard cap, alpha, and switching cost. A failure closes this candidate without
tuning on the confirmation block.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-eventwise-confirm `
  --seeds 600 --seed-offset 21700000 --n 3200 --d 16 --device cpu --workers 6 `
  --exact-uniform-propensity-floor `
  --null-calibration-manifest outputs/scout_context_known_uniform_markov_null_v1/reports/manifest.json `
  --protocol docs/scout_context_known_uniform_markov_confirmation_protocol_v1.md `
  --output outputs/scout_context_known_uniform_markov_confirmation_v1
```
