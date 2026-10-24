# Residual-variance onset-prior screen: development protocol

## Research question

The previous matched test found that fixed start mixtures can improve monitoring of a post-burn-in residual-variance shift, while uniform starts beat a prior weighted further toward late starts. In this generator, the variance change occurs at event 1,200; monitoring begins at event 800, giving a planned 1,600-event monitor horizon and a known design onset fraction of 0.25. This development screen asks whether a fixed start prior centered near that design onset improves the tradeoff.

## Candidates and validity argument

All candidates are fixed convex mixtures of the existing bounded-mean e-process, with the same PPI increments, alpha, support bound, labels, and hard cost budget:

- Full-stream fixed mixture (reference).
- Beta(1,1) uniform, Beta(1,2) early, Beta(2,1) late, and Beta(2,2) center priors on eight equal-width start bins.
- Beta(4,12) prior centered at start fraction 0.25, specified from the public generator's event-1,200 change time and event-800 monitor start.

For any fixed component start and stake, the existing bounded-mean e-process remains valid under its stated eventwise conditional-mean null and predictable support. A fixed convex mixture of these components preserves that guarantee. Beta(4,12) is a design-informed candidate, not a novel theorem; its start weights are frozen before these development outcomes.

## Locked design and selection rule

- Severity: 1.5, 3.0, 4.5.
- Query rates: 0.40, 0.80, 1.00; q=1 is full feedback.
- 60 fresh seeds per severity/rate cell, seeds 31,302,026–31,302,085.
- n=2,400; d=16; same cost matrix, decision margin, generator, predictor, query coins, and realized dollar cap across monitors.
- CUDA generation; vectorized CPU recursions use the same mixture algebra as the reference implementation.
- Primary selection set: the six severity × query-rate cells at q=0.80 and q=1.00. Select the prior with the highest equal-cell macro detection rate; break ties by higher minimum detection rate averaged across severities. q=0.40 is a stress cell and is excluded from selection.
- Report the full per-cell rates and seed-paired detection contrasts against the full-stream and uniform-start references. This is an exploratory screen; its bootstrap intervals are descriptive and not multiplicity-adjusted.

Run:

```powershell
uv run python -m shiftlab.dive.residual_variance_prior_development --device cuda --seeds 60
```

The output folder is `outputs/residual_variance_prior_development/`, with per-stream metrics, grouped results, paired contrasts, selected-prior table, and a manifest. Results and interpretation are recorded in [residual_variance_prior_development_results.md](residual_variance_prior_development_results.md). No visual is generated. Use PaperBanana if a figure is later requested.

## Decision after this screen

Do not call the winning prior confirmatory. Freeze it only if the observed gain is large enough to justify a disjoint validation/calibration stage. The next stage must use fresh nondegenerate null streams and a separate alternative block; it must retain the full-stream and uniform-start controls. If the onset-focused prior does not improve over uniform across the primary cells, stop this tuning branch rather than searching additional shapes on the same seeds.
