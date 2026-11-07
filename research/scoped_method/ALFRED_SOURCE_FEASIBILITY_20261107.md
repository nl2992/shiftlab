# ALFRED release-vintage source audit (2026-11-07)

**Status: metadata-only feasibility; no series observations or model outcomes opened.** This is a
source audit, not a real-data result or confirmation. It follows the prior ALFRED route note and
checks whether official release/vintage metadata can support a future point-in-time replay.

## Feasibility finding

ALFRED is a viable **candidate data system** for a chronological forecasting replay. Its official
documentation says it stores real-time periods for when historical values were available and
revised, and its series pages expose release-date histories. The output API supports observations
by vintage date and an “initial release only” output. ALFRED says new/revised observations are
typically loaded within one business day after source release. Its documentation also makes a
critical qualification: an actual source release date is used when available; otherwise ALFRED uses
provider dates or the date the series first appeared in FRED. The ALFRED website date is not itself
the exact release timestamp. Therefore a future protocol must verify each retained release against
the issuing agency's own release calendar and define actions as date-batched when historical time of
day is unavailable.

Official documentation checked:

- [ALFRED help: vintages and release-date determination](https://alfred.stlouisfed.org/help)
- [ALFRED API: vintage periods](https://fred.stlouisfed.org/docs/api/fred/alfred.html)
- [FRED observations API: output types and vintage dates](https://fred.stlouisfed.org/docs/api/fred/series_observations.html)

## Prospective series registry candidates

These are metadata-verified examples, not a frozen evaluation registry. No values, forecasts,
model pairs, or outcome slices were inspected in this audit.

| Series | Issuing source / release | Frequency and documented date history | Potential task | Main limitation |
|---|---|---|---|---|
| `UNRATE` | BLS, Employment Situation | Monthly; ALFRED page lists release-date history from 1960 | Predict next initial-release change using only vintages available at the current release | One national labor series; seasonal and population-control revisions require vintage-safe handling |
| `CPIAUCSL` | BLS, Consumer Price Index | Monthly; page lists release-date history from 1972 | Forecast next initial-release inflation direction or magnitude | ALFRED notes incomplete early vintage coverage; do not assume all early vintages exist |
| `INDPRO` | Federal Reserve Board, G.17 | Monthly; page lists release-date history from 1927 | Forecast next initial-release output change | National aggregate and structural revisions; verify old dates against official G.17 archives |
| `RSAFS` | U.S. Census Bureau, Advance Monthly Retail Sales | Monthly; page lists release dates from 2001 | Forecast next advance estimate and track subsequent revisions separately | Advance estimate is revised; use first release for the primary label and later values only as revision diagnostics |
| `HOUST` | Census Bureau / HUD, New Residential Construction | Monthly; page lists release dates from 1960 | Forecast next housing-starts estimate | Joint source and historical series-definition changes |
| `PCE` | BEA, Personal Income and Outlays | Monthly; page lists release dates from 1979 | Forecast next consumption estimate | Large revisions and national macro dependence; first-release target needed |

Official series pages: [UNRATE](https://alfred.stlouisfed.org/series?seid=UNRATE),
[CPIAUCSL](https://alfred.stlouisfed.org/series?seid=CPIAUCSL),
[INDPRO](https://alfred.stlouisfed.org/series?seid=INDPRO),
[RSAFS](https://alfred.stlouisfed.org/series?seid=RSAFS),
[HOUST](https://alfred.stlouisfed.org/series?seid=HOUST),
[PCE](https://alfred.stlouisfed.org/series?seid=PCE).

## Fit to the Failure Atlas task

These series provide a real, external chronology, historical vintages, and several source agencies.
A viable model pair could forecast the next release's direction from as-of-release predictors, using
fixed train cutoffs and rolling or frozen forecasts. The decision event would occur only after a
verified current release; the target label would be released at the next target publication. If
dates are available only at day granularity, all same-day publications must be treated as a single
batch so the replay cannot use one release before another release on the same date. Any difference
between source publication and ALFRED ingestion must be represented as an additional conservative
availability lag.

This source route does **not** yet meet the generalization requirement. The six series reflect one
interconnected U.S. macroeconomy, and multiple series from one agency are not independent deployment
domains. Uncertainty must cluster by issuing source and use calendar/time blocks for shared shocks;
with only a handful of source agencies, inferential precision will remain limited. A second
independent domain (for example, a separately governed electricity-market publication stream) would
need its own provenance audit before any multi-domain transfer claim.

## Next eligibility gate

The current synthetic method gates did not pass, so this audit does not authorize an outcome run.
If a distinct candidate later clears the synthetic and novelty gates, the smallest ALFRED eligibility
step is to freeze a short source registry, then verify a small set of release dates and vintage
values against BLS, the Federal Reserve, Census/HUD, and BEA source files without inspecting the
registered model-evaluation window. The registry must also settle data-use terms, download checksum,
first-release target definition, action/label batch order, training cutoffs, model-pair construction,
and a separate untouched chronological test period before that test is opened.
