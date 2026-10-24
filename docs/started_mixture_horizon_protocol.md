# Prespecified start-time mixture monitor grid

**Status:** frozen before execution. This is a development benchmark for an established e-process construction, not a novel method or a confirmatory winner selection.

## Question and construction

Does allocating a fixed e-value mixture across prespecified monitor start times improve late-onset decision-harm detection at the same query labels and pathwise label-dollar cap? For each monitor horizon `H`, the four components start at offsets `{0, floor(H/4), floor(H/2), floor(3H/4)}`. A component remains at one until its registered start, then follows the same bounded-mean e-process and uses the same prediction-powered estimates as the full-stream baseline. The mixture has equal weights and the same overall alpha. Under the stated eventwise conditional-mean null, each delayed component remains a nonnegative supermartingale; their fixed convex mixture therefore retains the standard Ville bound. This validity argument depends on immediate labels, predictable propensities/proxies, and the registered common bounded increment. It does not cover delayed/selective feedback or establish intervention safety.

The start locations are fixed from `H` before each run and never selected using labels or evaluation outcomes. Earlier components give broad protection; later-start components discard some pre-onset evidence and may improve sensitivity to recent changes at the price of mixture dilution and reduced power for early changes.

## Frozen grid

- Common generated stream: `n=4000`, `d=16`, monitor starts at event 1,000; horizons 1,000, 1,800, and 2,600.
- 30 paired seeds, `57,100,000–57,100,029`, disjoint from the prior 56,100,000 development grid.
- Six cells: stationary and benign-nuisance controls; boundary-local harm with change fractions .35 and .65; recurring regimes; harmful adaptation.
- One eventwise uniform-proxy acquisition stream per seed/cell, with a fixed pathwise `$720` realized label-dollar cap, query target .20, propensity range `[.20,.80]`, alpha `.05`, and materiality margin `.10`.
- Comparators share the identical event-level corrected estimates and labels: full-stream fixed mixture, four-start equal mixture, predictable-variance e-process, and PM-EB.
- CUDA is requested for synthetic generation and model fitting. CPU fallback remains available.

## Analysis and limits

The primary descriptive comparison is paired detection (four-start mixture versus full-stream fixed mixture) in the boundary-late cells. All-harm denominators retain streams whose onset was not reached; reachability, delay among detections, false escalations on both controls, processed events, labels, and dollar spend are reported. Exact paired McNemar tests use Holm correction over all harm-cell/horizon comparisons. The 30-stream controls are a smoke test only: their intervals are too wide to establish 5% calibration. Any confirmatory claim requires independent, larger null calibration and a fresh alternative seed block sized from a predeclared paired-power target.

## Reproduction

```powershell
uv run python scripts/run_started_mixture_horizon_grid.py --seeds 30 --seed-offset 57100000 --budget-dollars 720 --device cuda
uv run python scripts/analyze_started_mixture_horizon_grid.py
```
