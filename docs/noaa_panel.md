# NOAA fixed station panel

Acquire the selected 2023 JFK, Boston and Chicago O'Hare source files:

```powershell
python -m uv run python scripts/download_data.py --dataset noaa --config configs/data/public/noaa_panel.yaml --execute
python -m uv run python scripts/noaa_panel_report.py --dataset-path <returned-version-directory>
```

The implementation validates station identity and year, retains source records, decodes
seven numeric fields and masks missing sentinels and suspect/error quality flags. The
precipitation depth is paired with its accumulation period; it is not an inferred hourly
rate. Trace and estimated flags remain available in source metadata. Inaccurate or
incomplete precipitation amounts are masked. No field is forward filled.

The target is temperature at the next strictly later source time in the same station.
For simultaneous reports, the first record at that later time is selected in source
order. Its original temperature/quality string is retained. This is an irregular-horizon
retrospective forecasting task, with actual horizons recorded per row. Feature,
prediction and label availability remain unknown.

All stations use the same event-time split boundaries. Outcomes crossing fitting or
calibration boundaries are unassigned, including gaps that cross multiple partitions.
The quality report exports station identity, actual coverage, horizon ranges, missingness
and partition counts. This preserves domain differences without asserting real changepoints.

Authoritative format reference:
[NOAA ISD specification](https://www.ncei.noaa.gov/pub/data/noaa/isd-format-document.pdf).
Data come from NOAA's public Global Hourly S3 archive; immutable raw receipts and checksums
are retained locally. Old two-feature NOAA dataset versions are preserved as historical
versions rather than silently rewritten.
