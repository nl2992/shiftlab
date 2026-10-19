"""Fixed ISD station panels; source quality, accumulation periods and unknown release times retained."""

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from ..chronological_splits import assign_splits
from .common import save_source, utc_seconds
from .download import download

FEATURES = [
    "temperature_C",
    "dewpoint_C",
    "sea_level_pressure_hPa",
    "wind_speed_m_s",
    "visibility_m",
    "precipitation_depth_mm",
    "precipitation_period_hours",
]
BAD_QUALITY = {"2", "3", "6", "7"}


def decode_fields(original):
    """Decode documented tuple positions; absent fields stay missing, never zero filled."""

    def part(column, position):
        values = original.get(column, pd.Series("", index=original.index)).astype("string")
        return values.str.split(",").str[position]

    def numeric(column, position, sentinel, scale=1, quality_position=None):
        raw = pd.to_numeric(part(column, position), errors="coerce")
        result = raw.mask(raw.abs() == sentinel) / scale
        if quality_position is not None:
            quality = part(column, quality_position)
            result = result.mask(quality.isna() | quality.isin(BAD_QUALITY))
        return result.to_numpy(dtype=float, na_value=np.nan)

    temperature = numeric("TMP", 0, 9999, 10, 1)
    dewpoint = numeric("DEW", 0, 9999, 10, 1)
    pressure = numeric("SLP", 0, 99999, 10, 1)
    wind = numeric("WND", 3, 9999, 10, 4)
    visibility = numeric("VIS", 0, 999999, quality_position=1)
    depth = numeric("AA1", 1, 9999, 10, 3)
    period = numeric("AA1", 0, 99)
    # Inaccurate, accumulating, deleted, missing or incomplete totals are not full amounts.
    invalid = part("AA1", 2).isin({"1", "3", "5", "6", "7", "8", "I", "J"}).to_numpy()
    depth = np.where(invalid | ~np.isfinite(period), np.nan, depth)
    return np.column_stack([temperature, dewpoint, pressure, wind, visibility, depth, period])


def station_rows(original, station, year):
    from .adapters import standardize

    if not {"DATE", "STATION", "TMP", "DEW"}.issubset(original):
        raise ValueError("NOAA station file lacks required source fields")
    if not original.STATION.astype(str).eq(station).all():
        raise ValueError("NOAA station file contains a different station")
    dates = pd.to_datetime(original.DATE, utc=True, errors="raise")
    if dates.isna().any() or not dates.dt.year.eq(year).all():
        raise ValueError("NOAA date missing or outside requested year")
    order = np.argsort(utc_seconds(dates), kind="stable")
    original = original.iloc[order].reset_index(drop=True)
    times = utc_seconds(original.DATE)
    X = decode_fields(original)
    # Simultaneous reports cannot supply a future target. Select the first report at
    # the next strictly later observed time; no fabricated within-time chronology.
    next_index = np.searchsorted(times, times, side="right")
    keep = next_index < len(original)
    current, following = np.flatnonzero(keep), next_index[keep]
    if len(current) < 4:
        raise ValueError("NOAA station needs at least four usable forecast origins")
    records = original.to_dict("records")
    frame = standardize(
        X[current],
        X[following, 0],
        station,
        f"noaa-{station}-{year}",
        event_time=times[current],
        metadata=[
            json.dumps(
                {
                    "source": records[i],
                    "target_source": {"DATE": records[j]["DATE"], "TMP": records[j]["TMP"]},
                    "next_event_time": records[j]["DATE"],
                    "horizon_seconds": float(times[j] - times[i]),
                    "task": "next strictly later recorded observation temperature",
                    "release_latency": "unknown",
                    "quality_policy": "mask suspect/error codes 2,3,6,7",
                },
                allow_nan=False,
            )
            for i, j in zip(current, following)
        ],
    )
    frame["label_event_time"] = times[following]
    return frame


def acquire(config, root):
    root = Path(root)
    year = int(config.get("year", 2023))
    stations = config.get("stations", [str(config.get("station", "74486094789"))])
    if (
        not isinstance(stations, list)
        or not 1 <= len(stations) <= 5
        or len(set(stations)) != len(stations)
        or any(not isinstance(s, str) or not re.fullmatch(r"[A-Z0-9]\d{10}", s) for s in stations)
        or not 1901 <= year <= 2100
    ):
        raise ValueError("Require 1–5 unique ISD station IDs and a valid year")
    frames, paths = [], []
    for station in stations:
        path = download(
            f"https://noaa-global-hourly-pds.s3.amazonaws.com/{year}/{station}.csv",
            root / "raw/noaa" / f"{year}-{station}-s3.csv",
            max_bytes=int(config.get("max_download_bytes", 25_000_000)),
        )
        paths.append(path)
        original = pd.read_csv(path, dtype=str, keep_default_na=False)
        frames.append(station_rows(original, station, year))
    frame = (
        pd.concat(frames, ignore_index=True)
        .sort_values("event_time", kind="stable")
        .reset_index(drop=True)
    )
    frame["split"] = assign_splits(frame.event_time)
    # Even for retrospective evaluation, don't use a train/calibration target across
    # the next partition's event boundary. Real label availability is still unknown.
    partitions = ["train", "validation", "calibration", "test"]
    for i, split in enumerate(partitions[:-1]):
        later = frame.loc[frame.split.isin(partitions[i + 1 :]), "event_time"]
        if len(later):
            frame.loc[(frame.split == split) & (frame.label_event_time >= later.min()), "split"] = (
                "unassigned"
            )
    return save_source(
        "noaa",
        config,
        root,
        [(frame, None)],
        paths,
        FEATURES,
        [
            "Unknown release latency; all prediction/feature/label availability times remain unknown.",
            "Irregular next-observation forecasting, not a strict hourly horizon; simultaneous reports skip to the next later time.",
            "Sentinels and suspect/error quality codes masked; source strings, target temperature flag and precipitation conditions retained.",
            "AA1 depth covers its accompanying accumulation period; trace/estimated flags retained, no hourly rate or forward filling inferred.",
            "Shared panel event-time splits with outcome-boundary purging are retrospective, not evidence of online availability.",
        ],
    )
