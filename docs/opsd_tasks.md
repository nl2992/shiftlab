# OPSD hourly and daily tasks

```powershell
python -m uv run python scripts/download_data.py --dataset opsd --config configs/data/public/opsd_hourly_panel.yaml --execute
python -m uv run python scripts/download_data.py --dataset opsd --config configs/data/public/opsd_daily.yaml --execute
python -m uv run python scripts/opsd_task_report.py --dataset-path <hourly-version> <daily-version>
```

The 2019 panel contains eight separate source columns: Germany load/wind/solar,
DE-LU day-ahead price, and Denmark DK_1 load/wind/solar/day-ahead price. Full column
names and publisher schema are retained; country load and bidding-zone price are not
represented as geographically identical measurements. Both tasks predict the next
period's German load using the preceding period's eight observations. Domain ID marks
the joint wide feature set. Other targets are configurable explicitly.

The coverage gate requires at least 90% observed hourly values for each selected
column. Austria's price series failed this gate with no observed 2019 values; it was
excluded explicitly. Missing values in the accepted series remain missing.

Hourly UTC timestamps must be contiguous and aligned; the original CET/CEST strings
must identify the same instants. Daily aggregation uses UTC midnight boundaries and
exactly 24 hourly records, independent of local daylight-saving day length. Each field
requires 24 nonmissing values to produce a daily mean. Partial boundary days are dropped;
missing hourly values are not filled or silently averaged over fewer records. Daily
power features are mean MW, not energy totals. Prices retain publisher units and negative
prices are valid. Original per-hour UTC/local representations, missing counts and field
definitions accompany each aggregate.

An aggregate target is complete only at the end of its period. Its `label_event_time`
therefore follows the next period's start by one hour or day. Historical fitting/calibration
partitions purge target events crossing the next partition boundary. Feature, prediction,
and outcome availability remain unknown: these event times do not assert publication
or real-time observability. Prices and source forecasts are historical snapshots and
are never treated as operational economic utility or vintage-correct future features.

Reference: [OPSD time series 2020-10-06](https://data.open-power-system-data.org/time_series/2020-10-06/).
The complete source datapackage is copied as a checksummed immutable artifact in each
version. Historical processed versions are retained; the earlier invalidated epoch-unit
version remains retired rather than silently rewritten.
