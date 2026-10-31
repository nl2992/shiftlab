# Live verification data search and acquisition — 2026-10-31

Disposition: continue prospective data collection and timing audit. This is a successful acquisition smoke check, not a method result, statistical confirmation, or evidence of decision value.

## Repository finding

The Codex lane and main checkout both point to `https://github.com/nl2992/shiftlab.git`. `git worktree list` identifies the many local folders as checkouts of one shared repository. There are genuinely divergent research branches, including the separately preserved local/remote SOTA histories described in `../BRANCH_INVESTIGATION_2026-10-30.md` (relative to the workspace root, outside this checkout). This pull stays entirely in `research/codex-autoresearch`; no integration, reset, or experiment changes were made.

## Sources acquired

| Source | Saved now | Study role | Limitation |
|---|---|---|---|
| GB Carbon Intensity API | 90 days of national half-hourly forecast/reported-actual pairs, plus a forward snapshot | Forecast-error monitoring; possible flexible-load scheduling scenario | Reported actual is a system carbon-intensity estimate. Historical forecast retrieval does not establish the forecast vintage or original release time. No observed action costs or realized intervention value. |
| Open-Meteo GFS seamless and ECMWF IFS 0.25° | Seven days of hourly temperature, precipitation and wind forecasts at JFK, Chicago O'Hare and Phoenix airport coordinates | Two concrete forecast candidates, diverse climates, prospective target times | Grid forecasts differ from point observations; seamless GFS can combine resolutions. API response has no verified original issue timestamp. Current-day past hours must be excluded from prospective evaluation. |
| US National Weather Service | Hourly forecasts at each gridpoint, 500 recent observations each at KJFK/KORD/KPHX, point metadata | Third forecast comparator and observed temperature outcomes | Temperature observations contain missingness and quality flags; event time is not release time. NWS and other forecasts can share upstream models, so they are not independent replicates. |

Carbon API documentation: https://carbon-intensity.github.io/api-definitions/

Carbon terms (CC BY 4.0): https://github.com/carbon-intensity/terms/

Open-Meteo forecast documentation: https://open-meteo.com/en/docs

Open-Meteo terms (noncommercial free endpoint; data CC BY 4.0): https://open-meteo.com/en/terms

NWS API documentation: https://www.weather.gov/documentation/services-web-api

Additional useful source discovered but not acquired in this slice: Open-Meteo Previous Runs and Single Runs APIs. These support fixed lead offsets or individual initialized runs and are better candidates for a larger historical forecast-vintage benchmark than the seamless Historical Forecast API. Their initialization timestamps still do not establish actual public availability; audit ingestion and publication lag before claiming point-in-time replay. Documentation: https://open-meteo.com/en/docs/previous-runs-api and https://open-meteo.com/en/docs/historical-forecast-api. Do not substitute ERA5/reanalysis for station-observed outcomes.

## Local artifacts and validation

Successful snapshot: `data/raw/live_verification/20261031T204324016490Z/` (about 7 MB of source JSON).

- 20/20 requests succeeded and all 20 archived response SHA-256 hashes passed verification.
- 4,321 unique historical carbon intervals with nonmissing forecast and actual; inclusive API window boundaries were deduplicated and checked for conflicts. This is 90 days plus the preceding boundary interval.
- 1,476 temperature predictions across three sites and three candidates; 1,346 have target start times strictly after local capture completion.
- 1,500 weather observation records; 1,495 nonmissing temperatures. Original quality-control fields remain in raw responses and the temperature export.
- CSV exports: `temperature_predictions.csv`, `temperature_observations.csv`, `carbon_retrospective.csv`.
- `manifest.json` contains request URLs, request/capture timestamps, HTTP headers, response checksums, code revision and acquisition-script checksum. `verification.json` records the checks and counts. Raw files are excluded from Git by existing ignore rules.
- The first attempt used an incorrect carbon forward URL and received HTTP 400. That failed attempt is retained in `20261031T204309469839Z/manifest.json`. The endpoint was corrected to `/intensity/{from}/fw48h` and the complete run repeated successfully.

Reproduce from this checkout:

```powershell
python scripts/acquire_live_verification.py --history-days 90
python scripts/verify_live_verification.py data/raw/live_verification/20261031T204324016490Z
```

The second command verifies the saved snapshot. To verify a new pull, use its printed directory. For incremental prospective snapshots, use `--history-days 0`; this avoids downloading the historical carbon archive again. Each invocation writes a fresh directory and preserves earlier source responses.

## Proposed next experiment and eligibility gate

Start with hourly air temperature: GFS versus ECMWF, with NWS as an additional baseline. Both candidate losses can be calculated against the same station outcome; actions do not alter the weather. Fix the horizon (for example 24 hours), temperature units, station/grid mapping, station quality rules, permitted observation alignment tolerance, revision policy and missing-data policy before scoring. Existing CSVs deliberately contain all hours and flag future targets; they do not yet enforce a fixed lead horizon or join predictions to labels.

Use capture completion as a conservative availability time for forecasts and observations. Filter target times after forecast capture; freeze each selected prediction and candidate version before its future outcome. Match only subsequently captured observations, preserving revisions rather than overwriting them. Existing historical observations and carbon pairs are development data. Later pulls are required to supply outcomes for newly captured future predictions.

This supports real forecast-error evaluation. Decision losses require a declared application (for example a temperature threshold intervention), with costs clearly labeled as imposed scenarios. Label query budgets would be experimentally imposed on freely available measurements, not actual purchased-label costs. Switching and delay assumptions remain explicit experimental design choices. Serial dependence, stationarity and conditional-null assumptions require separate checks; better timestamps alone do not validate an e-process.

No confirmation sets were opened, no statistical comparison was run, and no recurring collection job was installed. A repeatable collector is ready; continuous live verification requires subsequent collection and a frozen evaluation protocol.
