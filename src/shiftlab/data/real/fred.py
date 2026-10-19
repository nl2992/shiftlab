"""FRED/ALFRED revision rows and conservative date-resolution release availability."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .api import reject_secrets, required_key, snapshot_pages
from .common import numeric_rows, save_source, utc_seconds

ENDPOINT = "https://api.stlouisfed.org/fred/series/observations"


def asof_vintage(records: pd.DataFrame, asof: str) -> pd.DataFrame:
    """Select only revisions whose real-time period includes asof; no future revisions."""
    date = str(pd.Timestamp(asof).date())
    eligible = records[(records.realtime_start <= date) & (records.realtime_end >= date)]
    return eligible.sort_values("realtime_start").drop_duplicates("date", keep="last")


def acquire(config: dict, root: Path):
    reject_secrets(config)
    key = required_key("FRED_API_KEY")
    frames, paths = [], []
    for series in config.get("series", ["UNRATE"]):
        params = {
            "series_id": series,
            "file_type": "json",
            "observation_start": config.get("start", "2022-01-01"),
            "observation_end": config.get("end", "2023-12-31"),
            "realtime_start": config.get("realtime_start", "1776-07-04"),
            "realtime_end": config.get("realtime_end", "9999-12-31"),
            "output_type": 1,
            "sort_order": "asc",
        }
        pages, receipt = snapshot_pages(
            ENDPOINT,
            params,
            key,
            root / "raw/fred",
            ("observations",),
            ("count",),
            page_size=1000,
            max_records=config.get("max_records", 20000),
            refresh=config.get("refresh", False),
        )
        paths.extend([*pages, receipt])
        records = [row for path in pages for row in json.loads(path.read_text())["observations"]]
        if not records:
            raise ValueError(f"FRED {series} returned no observations")
        original = (
            pd.DataFrame(records).sort_values(["date", "realtime_start"]).reset_index(drop=True)
        )
        if not {"date", "value", "realtime_start", "realtime_end"} <= set(original):
            raise ValueError("Missing FRED vintage fields")
        values = pd.to_numeric(original.value, errors="coerce").to_numpy()
        # This is a revision/event table, not a falsely lagged forecasting table.
        # Revisions are outcomes. asof_vintage is the only accessor for historical covariates.
        frame = numeric_rows(
            np.empty((len(original), 0)),
            values,
            f"fred-{series}",
            series,
            [
                json.dumps(
                    {
                        **row,
                        "series_id": series,
                        "kind": "revision_observation",
                        "release_resolution": "date",
                        "release_time_rule": "conservative end of realtime_start UTC day; exact release time unknown",
                    }
                )
                for row in original.to_dict("records")
            ],
        )
        frame["event_time"] = utc_seconds(original.date)
        frame["label_event_time"] = frame.event_time
        frame["label_available_time"] = utc_seconds(original.realtime_start) + 86400
        # Observation values cannot be available before their own event period.
        if (frame.label_available_time < frame.label_event_time).any():
            raise ValueError(
                "Forward-dated FRED observation requires explicit forecast-specific event semantics"
            )
        frames.append((frame, None))
    return save_source(
        "fred",
        config,
        root,
        frames,
        paths,
        [],
        [
            "Revision/event table, not a ready forecasting design. Use asof_vintage for feature construction.",
            "Release dates have no intraday timestamp; conservative end-of-day availability is an explicit derived assumption, not publisher ground truth.",
            "Series-specific copyright/redistribution terms still apply; final revised values are never assigned past availability.",
        ],
    )
