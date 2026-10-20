"""EIA v2 balancing-authority hourly data with explicit unknown historical release latency."""

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from ..chronological_splits import retrospective_event_splits
from ..provenance import sha256
from .api import reject_secrets, required_key, snapshot_pages
from .common import numeric_rows, save_source, utc_seconds
from .download import download

ENDPOINT = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
BULK_MANIFEST = "https://api.eia.gov/bulk/manifest.txt"
BULK_EBA = "https://www.eia.gov/opendata/bulk/EBA.zip"


def _retrospective_splits_if_feasible(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep tiny fixtures unassigned; real event-time panels receive purged splits."""
    if frame.event_time.nunique() < 4:
        return frame
    return retrospective_event_splits(frame)


def _bulk_records(archive_path: Path, respondents, types, start, end, max_records):
    """Stream selected UTC hourly EBA series from the official bulk archive."""
    lower_time = pd.Timestamp(start)
    upper_time = pd.Timestamp(end)
    lower_time = (
        lower_time.tz_localize("UTC") if lower_time.tzinfo is None else lower_time.tz_convert("UTC")
    )
    upper_time = (
        upper_time.tz_localize("UTC") if upper_time.tzinfo is None else upper_time.tz_convert("UTC")
    )
    if upper_time < lower_time:
        raise ValueError("EIA EBA end time must not precede start time")
    lower = lower_time.strftime("%Y%m%dT%H")
    upper = upper_time.strftime("%Y%m%dT%H")
    wanted = {
        f"EBA.{respondent}-ALL.{kind}.H": (respondent, kind)
        for respondent in respondents
        for kind in types
    }
    found = set()
    records = []
    with zipfile.ZipFile(archive_path) as archive:
        members = [name for name in archive.namelist() if Path(name).name == "EBA.txt"]
        if len(members) != 1:
            raise ValueError("Official EIA EBA archive must contain exactly one EBA.txt file")
        with archive.open(members[0]) as source:
            for line_number, line in enumerate(source, start=1):
                try:
                    payload = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        f"Malformed EIA EBA JSON record at line {line_number}"
                    ) from exc
                series_id = payload.get("series_id")
                if series_id not in wanted:
                    continue
                respondent, kind = wanted[series_id]
                if payload.get("f") != "H" or not series_id.endswith(".H"):
                    raise ValueError(f"Expected UTC hourly data for {series_id}")
                found.add(series_id)
                for period, raw_value in payload.get("data", []):
                    if lower <= period <= upper and raw_value is not None:
                        if len(records) >= max_records:
                            raise ValueError(
                                "EIA bulk extraction exceeds max_records; narrow the configured date window"
                            )
                        records.append(
                            {
                                "period": period,
                                "respondent": respondent,
                                "type": kind,
                                "value": raw_value,
                                "units": payload.get("units"),
                            }
                        )
    missing = sorted(set(wanted) - found)
    if missing:
        raise ValueError(f"EIA EBA bulk archive lacks requested series: {missing}")
    return records


def _acquire_bulk(config: dict, root: Path):
    """Acquire EBA data without an API key under an explicit compressed-byte budget."""
    dataset = config.get("bulk_dataset")
    if dataset != "EBA":
        raise ValueError("Supported EIA bulk_dataset is 'EBA'")
    if "max_download_bytes" not in config:
        raise ValueError("EIA bulk acquisition requires an explicit max_download_bytes")
    respondents = list(config.get("respondents", ["NYIS"]))
    kinds = list(config.get("types", ["D", "DF", "NG", "TI"]))
    start = config.get("start", "2023-01-01T00")
    end = config.get("end", "2023-01-03T23")
    max_records = int(config.get("max_records", 20000))
    if max_records < 1:
        raise ValueError("max_records must be positive")
    archive_path = download(
        BULK_EBA,
        root / "raw/eia/EBA.zip",
        max_bytes=int(config["max_download_bytes"]),
    )
    manifest_path = download(
        BULK_MANIFEST,
        root / "raw/eia/manifest.txt",
        max_bytes=int(config.get("manifest_max_bytes", 2_000_000)),
    )
    records = _bulk_records(archive_path, respondents, kinds, start, end, max_records)
    if not records:
        raise ValueError("EIA EBA bulk query returned no observations in the configured range")
    original = pd.DataFrame(records)
    original["period"] = pd.to_datetime(original.period, format="%Y%m%dT%H", utc=True)
    original["value"] = pd.to_numeric(original.value, errors="coerce")
    units_by_series = {}
    for (respondent, kind), rows in original.groupby(["respondent", "type"]):
        units = sorted(set(rows.units.dropna().astype(str)))
        if len(units) != 1:
            raise ValueError(f"EIA EBA series has ambiguous units: {respondent} {kind}")
        units_by_series[f"{respondent}:{kind}"] = units[0]
    if original.duplicated(["period", "respondent", "type"]).any():
        raise ValueError("EIA EBA contains duplicate respondent/type/period observations")
    wide = original.pivot(index=["respondent", "period"], columns="type", values="value")
    columns = list(config.get("types", ["D", "DF", "NG", "TI"]))
    target = config.get("target", "D")
    if target not in wide.columns:
        raise ValueError(f"EIA target {target} absent from this bulk response")
    frames = []
    horizon = int(config.get("horizon", 1))
    if horizon < 1:
        raise ValueError("horizon must be positive")
    for respondent, group in wide.groupby(level="respondent"):
        group = group.droplevel("respondent").sort_index().reindex(columns=columns)
        if len(group) <= horizon:
            continue
        times = utc_seconds(group.index)
        valid = np.r_[
            np.isclose(times[horizon:] - times[:-horizon], 3600 * horizon),
            np.zeros(horizon, dtype=bool),
        ]
        indices = np.flatnonzero(valid)
        values = group.to_numpy(float)
        metadata = [
            json.dumps(
                {
                    "period": group.index[i],
                    "respondent": respondent,
                    "horizon_hours": horizon,
                    "original_rows": records_for(original, respondent, group.index[i]),
                    "availability": "unknown; historical measurements/forecasts may be revised",
                    "source_representation": "official EIA EBA bulk series, UTC hourly",
                },
                default=str,
            )
            for i in indices
        ]
        frame = numeric_rows(
            values[indices],
            group[target].to_numpy()[indices + horizon],
            f"eia-{respondent}",
            str(respondent),
            metadata,
        )
        frame["event_time"] = times[indices]
        frame["label_event_time"] = times[indices + horizon]
        frame = _retrospective_splits_if_feasible(frame)
        frames.append((frame, None))
    return save_source(
        "eia",
        {**config, "acquisition_mode": "official_bulk_EBA"},
        root,
        frames,
        [archive_path, manifest_path],
        columns,
        [
            "Downloaded the official EIA bulk EBA archive; hourly event time is not publication time.",
            "No real-time feature/label availability is inferred; historical measurements and forecasts may be revised.",
            "The configured date window is extracted from a full compressed publisher archive under a strict byte budget.",
        ],
        extra={
            "source_url": BULK_EBA,
            "source_manifest_url": BULK_MANIFEST,
            "bulk_dataset_id": "EBA",
            "series_units": units_by_series,
            "license": "EIA U.S. government data; public-domain EIA content with EIA attribution; verify any series-specific third-party restrictions",
            "bulk_manifest_sha256": sha256(manifest_path),
        },
    )


def acquire(config: dict, root: Path):
    reject_secrets(config)
    if config.get("bulk_dataset"):
        return _acquire_bulk(config, root)
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
        frame = _retrospective_splits_if_feasible(frame)
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
