"""EIA v2 balancing-authority hourly data with explicit unknown historical release latency."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .api import reject_secrets, required_key, snapshot_pages
from .common import numeric_rows, save_source, utc_seconds

ENDPOINT = "https://api.eia.gov/v2/electricity/rto/region-data/data/"


def acquire(config: dict, root: Path):
    reject_secrets(config)
    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "start": config.get("start", "2023-01-01T00"),
        "end": config.get("end", "2023-01-03T23"),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }
    for i, ba in enumerate(config.get("respondents", ["NYIS"])):
        params[f"facets[respondent][{i}]"] = ba
    for i, kind in enumerate(config.get("types", ["D", "DF", "NG", "TI"])):
        params[f"facets[type][{i}]"] = kind
    pages, receipt = snapshot_pages(
        ENDPOINT,
        params,
        required_key("EIA_API_KEY"),
        root / "raw/eia",
        ("response", "data"),
        ("response", "total"),
        max_records=config.get("max_records", 20000),
        refresh=config.get("refresh", False),
    )
    records = [row for path in pages for row in json.loads(path.read_text())["response"]["data"]]
    if not records:
        raise ValueError("EIA query returned no observations")
    original = pd.DataFrame(records)
    original["value"] = pd.to_numeric(original.value, errors="coerce")
    if original.duplicated(["period", "respondent", "type"]).any():
        raise ValueError("EIA contains ambiguous duplicate respondent/type/period observations")
    wide = original.pivot(
        index=["respondent", "period"], columns="type", values="value"
    ).sort_index()
    columns = list(config.get("types", ["D", "DF", "NG", "TI"]))
    target = config.get("target", "D")
    if target not in wide.columns:
        raise ValueError(f"EIA target {target} absent from this response")
    frames = []
    horizon = int(config.get("horizon", 1))
    if horizon < 1:
        raise ValueError("horizon must be positive")
    for ba, group in wide.groupby(level="respondent"):
        group = group.droplevel("respondent").reindex(columns=columns)
        if len(group) <= horizon:
            continue
        times = utc_seconds(group.index)
        # Missing calendar intervals remain explicit; never shift across a gap as a claimed fixed horizon.
        valid = np.r_[
            np.isclose(times[horizon:] - times[:-horizon], 3600 * horizon),
            np.zeros(horizon, dtype=bool),
        ]
        index = np.flatnonzero(valid)
        values = group.to_numpy(float)
        metadata = [
            json.dumps(
                {
                    "period": group.index[i],
                    "respondent": ba,
                    "horizon_hours": horizon,
                    "original_rows": records_for(original, ba, group.index[i]),
                    "availability": "unknown; historical measurements/forecasts may be revised",
                }
            )
            for i in index
        ]
        frame = numeric_rows(
            values[index], group[target].to_numpy()[index + horizon], f"eia-{ba}", str(ba), metadata
        )
        frame["event_time"] = times[index]
        frame["label_event_time"] = times[index + horizon]
        frames.append((frame, None))
    return save_source(
        "eia",
        config,
        root,
        frames,
        [*pages, receipt],
        columns,
        [
            "Hourly event time is not publication time; no real-time feature/label availability inferred.",
            "API receipts retain original-byte hashes; stored JSON removes credential echoes. Demand/forecast/generation/interchange types preserve source units.",
        ],
    )


def records_for(original, respondent, period):
    subset = original[(original.respondent == respondent) & (original.period == period)]
    return json.loads(subset.to_json(orient="records"))
