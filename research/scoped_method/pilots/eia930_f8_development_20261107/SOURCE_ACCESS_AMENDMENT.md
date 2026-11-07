# Source-access amendment

**Frozen before any EIA model-pair stream or method outcome was computed.** The initial API request
to the registered `region-data` route returned HTTP 429 while using public `DEMO_KEY`. The failure
occurred before data retrieval; `source_manifest.json`, derived predictions, and episode outcomes
were not created. No result or eligibility value was computed from the failed attempt.

The data-access route is changed to the official no-key six-month EIA-930 balance CSVs. The frozen
files are 2021 H1/H2 for threshold training and 2022 H1/H2 plus 2023 H1/H2 for development. The
three BA registry entries, `D`/`DF` variables, source-time limitations, feedback schedule, target
matching rules, cost contract, method panel, and analysis gate are unchanged. The train/development
calendar windows are updated accordingly in `PROTOCOL.md`.

The official files expose the UTC ending-hour timestamp, day-ahead forecast, actual demand, and an
EIA-imputed-demand field. The runner filters to the preselected BAs and those columns before retaining
observations, excludes populated imputed-demand rows, downloads atomically, and records original-file
hashes. This source route does not resolve the absence of historical point-in-time value vintages;
label availability remains simulated and the experiment remains a retrospective replay.

## Failed access attempt

- Command: `uv run python scripts/sota_sprint/eia930/run_f8_development.py`
- Response: `urllib.error.HTTPError: HTTP Error 429: Too Many Requests`
- Stage: first API data request, before any source rows were retained
- Outputs: no source data, predictions, policy traces, or episode results
- Preserved startup marker: `RUN_STARTED.json` contains the original protocol SHA-256 and start time
- New access route: `https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_<YEAR>_<Jan_Jun|Jul_Dec>.csv`

