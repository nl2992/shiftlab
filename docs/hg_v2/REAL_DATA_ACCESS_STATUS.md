# Real-data access status (2026-10-30)
Anonymous HTTPS probes, one attempt each, both denied by the environment proxy (`CONNECT tunnel failed, response 403`):
- `d37ci6vzurychx.cloudfront.net` (NYC TLC trip-record parquet files)
- `archive.ics.uci.edu` (UCI Gas Sensor Array Drift)
Not retried. No real data was downloaded, no result was mocked. Citi Bike (`s3.amazonaws.com/tripdata`) and `data.binance.vision` were not probed because the same policy almost certainly applies.
**To proceed:** add the hosts above under Allowed domains in the environment's Network access settings (or choose a broader access level).
**Frozen candidate for the real-data phase:** H2c = `pp_cost_guided`, mode `guided_disc`, γ = .995, label rates {10%, 20%}, α = .05, delay = the dataset's documented/assumed completion delay. The protocol (event chronology, label availability, nominal-risk calibration period, harm definition, validation vs untouched periods, terms of use) must be written and committed before any download, per `docs/hg_v2/RESEARCH_CHARTER.md`.
