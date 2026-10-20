"""Hourly and complete UTC-day OPSD tasks; original calendar offsets and source schema retained."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..chronological_splits import retrospective_event_splits
from ..tasks import finite_real_parameter
from .common import save_source, utc_seconds
from .download import download


def prepare(original, columns, target_column, frequency, domain, source_fields):
    from .adapters import standardize

    if frequency not in {"hourly", "daily"}:
        raise ValueError("OPSD frequency must be hourly or daily")
    if target_column not in columns or not columns or len(set(columns)) != len(columns):
        raise ValueError("Require unique feature columns including target_column")
    if len(original) < 10:
        raise ValueError("OPSD selected period empty/too small")
    dates = pd.to_datetime(original.utc_timestamp, utc=True, errors="raise")
    local = pd.to_datetime(original.cet_cest_timestamp, utc=True, errors="raise")
    if dates.isna().any() or not np.array_equal(utc_seconds(dates), utc_seconds(local)):
        raise ValueError("OPSD UTC/local representations disagree or contain missing dates")
    times = utc_seconds(dates)
    if not np.all(np.diff(times) == 3600) or np.any(times % 3600):
        raise ValueError("OPSD hourly calendar has gaps, duplicates or reversed times")
    values = original[columns].apply(pd.to_numeric, errors="raise").copy()
    values.index = pd.DatetimeIndex(dates)
    if frequency == "daily":
        counts = values.resample("D").count()
        row_counts = values.resample("D").size()
        means = values.resample("D").mean().mask(counts != 24)
        # Partial boundary days are excluded; full days with missing fields remain NaN.
        values = means.loc[row_counts == 24]
        duration = 86400
    else:
        duration = 3600
    if len(values) < 5:
        raise ValueError("OPSD task needs at least five complete time groups")
    times = utc_seconds(values.index)
    if not np.all(np.diff(times) == duration):
        raise ValueError("OPSD task calendar is not contiguous after aggregation")
    meta = []
    for stamp in values.index[:-1]:
        source = original.loc[(dates >= stamp) & (dates < stamp + pd.Timedelta(seconds=duration))]
        meta.append(
            json.dumps(
                {
                    "utc": source.utc_timestamp.tolist()[0],
                    "cet_cest": source.cet_cest_timestamp.tolist()[0],
                    "source_utc_timestamps": source.utc_timestamp.tolist(),
                    "source_cet_cest_timestamps": source.cet_cest_timestamp.tolist(),
                    "source_missing_counts": {c: int(source[c].isna().sum()) for c in columns},
                    "period_end_utc": (stamp + pd.Timedelta(seconds=duration)).isoformat(),
                    "aggregation": "UTC-day arithmetic mean, requires 24 nonmissing hourly values per field"
                    if frequency == "daily"
                    else "source hourly average",
                    "task": f"next {frequency} {target_column}",
                    "release_latency": "unknown",
                    "source_fields": source_fields,
                },
                allow_nan=False,
            )
        )
    frame = standardize(
        values.to_numpy(float)[:-1],
        values[target_column].to_numpy(float)[1:],
        domain,
        f"opsd-2020-10-06-{frequency}",
        event_time=times[:-1],
        metadata=meta,
    )
    # Target is an aggregate over the entire NEXT period, not a value known at its start.
    frame["label_event_time"] = times[1:] + duration
    return retrospective_event_splits(frame)


def acquire(config, root):
    min_fraction = finite_real_parameter(
        config.get("min_observed_fraction", 0), "min_observed_fraction"
    )
    if not 0 <= min_fraction <= 1:
        raise ValueError("min_observed_fraction must lie in [0,1]")
    root = Path(root)
    version = "2020-10-06"
    base = f"https://data.open-power-system-data.org/time_series/{version}/"
    raw = root / "raw/opsd" / version
    metadata = download(base + "datapackage.json", raw / "datapackage.json")
    path = download(base + "time_series_60min_singleindex.csv", raw / "hourly.csv")
    columns = config.get(
        "columns",
        [
            "DE_load_actual_entsoe_transparency",
            "DE_wind_generation_actual",
            "DE_solar_generation_actual",
        ],
    )
    original = pd.read_csv(path, usecols=["utc_timestamp", "cet_cest_timestamp", *columns])
    dates = pd.to_datetime(original.utc_timestamp, utc=True)
    start, end = (
        pd.to_datetime(config.get("start", "2018-01-01"), utc=True),
        pd.to_datetime(config.get("end", "2019-01-01"), utc=True),
    )
    if start >= end:
        raise ValueError("OPSD end must follow start")
    original = original.loc[(dates >= start) & (dates < end)].copy()
    package = json.loads(metadata.read_text())
    fields = {}
    for resource in package.get("resources", []):
        if resource.get("path") == "time_series_60min_singleindex.csv":
            fields = {
                f["name"]: f
                for f in resource.get("schema", {}).get("fields", [])
                if f["name"] in columns
            }
    if len(original) and (original[columns].notna().mean() < min_fraction).any():
        raise ValueError("OPSD selected fields lack required overlapping observed coverage")
    frequency = config.get("frequency", "hourly")
    frame = prepare(
        original,
        columns,
        config.get("target_column", columns[0]),
        frequency,
        config.get("domain", "DE"),
        fields,
    )
    names = columns if frequency == "hourly" else [f"{c}__UTC_daily_mean" for c in columns]
    return save_source(
        "opsd",
        config,
        root,
        [(frame, None)],
        [metadata, path],
        names,
        [
            "Historical source snapshot may contain revisions; release, feature and label availability remain unknown.",
            "Original UTC and CET/CEST strings retained; daily groups use UTC, not local civil days.",
            "Missing values are not filled; complete UTC-day means require all 24 hourly values per field.",
            "Wide regional feature columns retain distinct source definitions and units; prices are not operational utility.",
            "Next-period target event time is its interval end; boundary-crossing training/calibration outcomes are purged retrospectively.",
        ],
        artifacts={"source_datapackage.json": metadata},
    )
