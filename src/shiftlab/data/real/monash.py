"""Monash TSF acquisition preserving supplied attributes, missingness and official horizons."""

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np

from ..tasks import integer_parameter
from .common import numeric_rows, save_source
from .download import download

# Fixed record versions linked by https://forecastingdata.org/ (verified 2026-10-19).
DATASETS = {
    "m4_weekly": ("4656522", "m4_weekly_dataset.zip", "7578a670dbcdaaf519aa01b3836f64d5"),
    "m4_hourly": ("4656589", "m4_hourly_dataset.zip", "3983df90f60db0f4e1f4dc3fca8ef565"),
    "m4_daily": ("4656548", "m4_daily_dataset.zip", "a92adb385fe0aec3728e60bd6de29875"),
    "electricity_hourly": (
        "4656140",
        "electricity_hourly_dataset.zip",
        "18096614662b02640d265ad2a6a416bd",
    ),
    "weather": ("4654822", "weather_dataset.zip", "57155594af0883ccd5e63a5948976796"),
}


def read_tsf(handle):
    """Stream series records; validate declared attribute types without inventing dates."""
    attributes = []
    metadata = {}
    in_data = False
    for raw in handle:
        line = raw.decode("cp1252").strip() if isinstance(raw, bytes) else raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            parts = line.split()
            if parts[0].lower() == "@attribute":
                if len(parts) != 3 or parts[2] not in ["numeric", "string", "date"]:
                    raise ValueError("Unsupported TSF attribute declaration")
                attributes.append((parts[1], parts[2]))
            elif parts[0].lower() == "@data":
                if not attributes:
                    raise ValueError("TSF data have no attributes")
                in_data = True
            else:
                if len(parts) != 2:
                    raise ValueError("Malformed TSF metadata")
                metadata[parts[0][1:].lower()] = parts[1]
            continue
        if not in_data:
            raise ValueError("TSF observation before @data")
        fields = line.split(":", len(attributes))
        if len(fields) != len(attributes) + 1:
            raise ValueError("Malformed TSF row")
        record = {}
        for (name, kind), value in zip(attributes, fields):
            if kind == "numeric":
                record[name] = float(value)
            elif kind == "date":
                # Keep source calendar attributes rather than asserting availability or a timezone.
                datetime.strptime(value, "%Y-%m-%d %H-%M-%S")
                record[name] = value
            else:
                record[name] = value
        values = np.array(
            [np.nan if value == "?" else float(value) for value in fields[-1].split(",")]
        )
        if not len(values) or np.isinf(values).any():
            raise ValueError("Invalid TSF series")
        yield record, values, dict(metadata)


def tsf_chunks(handle, config):
    lookback = int(config.get("lookback", 8))
    if lookback < 1:
        raise ValueError("lookback must be positive")
    maximum = int(config.get("max_series", 20))
    if maximum < 1:
        raise ValueError("max_series must be positive")
    for index, (attributes, values, meta) in enumerate(read_tsf(handle)):
        if index >= maximum:
            break
        if "horizon" in meta:
            try:
                horizon = int(meta["horizon"])
            except (TypeError, ValueError) as exc:
                raise ValueError("TSF horizon must be a positive integer") from exc
            if str(horizon) != meta["horizon"] or horizon <= 0:
                raise ValueError("TSF horizon must be a positive integer")
        elif "forecast_horizon" in config:
            horizon = integer_parameter(config["forecast_horizon"], "forecast_horizon", minimum=1)
        else:
            raise ValueError("TSF lacks a forecast horizon; provide forecast_horizon explicitly")
        origin = len(values) - horizon
        if origin < lookback + 1:
            raise ValueError("Series too short for official horizon and lookback")
        series = str(attributes.get("series_name", f"series-{index}"))
        rows = []
        for outcome in range(lookback, origin):
            rows.append(
                (
                    values[outcome - lookback : outcome],
                    values[outcome],
                    "train",
                    outcome - 1,
                    outcome,
                    1,
                )
            )
        # Official holdout: every horizon shares a single forecast origin and identical training-only covariates.
        for step in range(1, horizon + 1):
            rows.append(
                (
                    values[origin - lookback : origin],
                    values[origin + step - 1],
                    "test",
                    origin - 1,
                    origin + step - 1,
                    step,
                )
            )
        frame = numeric_rows(
            np.stack([r[0] for r in rows]),
            [r[1] for r in rows],
            f"monash-{index}-{series}",
            config.get("dataset", "local_tsf"),
            [
                json.dumps(
                    {
                        "series_attributes": attributes,
                        "tsf_metadata": meta,
                        "origin_index": r[3],
                        "outcome_index": r[4],
                        "forecast_step": r[5],
                        "official_horizon": horizon,
                        "forecast_horizon_source": config.get(
                            "forecast_horizon_source", "TSF @horizon"
                        ),
                        "clock": "series-relative index; no individual release times inferred",
                    }
                )
                for r in rows
            ],
        )
        frame["entity_id"] = series
        frame["split"] = [r[2] for r in rows]
        # Expose ordinal positions separately from wall-clock/availability fields.
        frame["sequence_index"] = [r[4] for r in rows]
        yield frame, None


def acquire(config, root: Path):
    key = config.get("dataset", "m4_hourly")
    if "path" in config:
        path = Path(config["path"])
        if not config.get("license"):
            raise ValueError("Local TSF import requires explicit license")
    else:
        if key not in DATASETS:
            raise ValueError(f"Unsupported Monash dataset; choose {list(DATASETS)}")
        record, filename, md5 = DATASETS[key]
        path = download(
            f"https://zenodo.org/records/{record}/files/{filename}?download=1",
            root / "raw/monash" / record / filename,
            max_bytes=config.get("max_download_bytes", 250_000_000),
        )
        if md5:
            digest = hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
            if digest != md5:
                raise ValueError("Monash publisher MD5 mismatch")
    limits = [
        "Official final-horizon split preserved; holdout forecasts use one fixed training-only origin.",
        "TSF start dates are source attributes, not verified measurement/release dates. Within-series positions are not cross-entity wall-clock times.",
        "No exogenous covariates claimed unless present as source attributes; lag features are derived from the series only.",
        f"Only the first {config.get('max_series', 20)} series are selected deterministically; this is a documented subset, not the full competition.",
    ]
    if config.get("forecast_horizon_source"):
        limits.append(
            "TSF omits @horizon; configured horizon follows the cited Monash archive benchmark protocol: "
            f"{config['forecast_horizon_source']}"
        )
    extra = {
        "license": config.get(
            "license",
            "CC BY 4.0 per Zenodo record; retain original competition attribution and research-use guidance",
        )
    }
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            members = [name for name in archive.namelist() if name.endswith(".tsf")]
            if len(members) != 1:
                raise ValueError("Expected exactly one TSF file in archive")
            with archive.open(members[0]) as handle:
                return save_source(
                    "monash",
                    config,
                    root,
                    tsf_chunks(handle, config),
                    [path],
                    [f"lag_{lag}" for lag in range(int(config.get("lookback", 8)), 0, -1)],
                    limits,
                    extra=extra,
                )
    with path.open("rb") as handle:
        return save_source(
            "monash",
            config,
            root,
            tsf_chunks(handle, config),
            [path],
            [f"lag_{lag}" for lag in range(int(config.get("lookback", 8)), 0, -1)],
            limits,
            extra=extra,
        )
