"""Small, inspectable real adapters. Unknown release times remain null."""

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_svmlight_file

from ..catalogue import SOURCES
from ..chronological_splits import assign_splits
from ..provenance import sha256
from ..storage import save_dataset
from .download import download


def standardize(X, y, domain, name, event_time=None, metadata=None, split=None, weights=None):
    n = len(y)
    # Null timestamps are deliberate for coarse domains and unknown observability.
    return pd.DataFrame(
        {
            "sample_id": [f"{name}:{i}" for i in range(n)],
            "entity_id": name,
            "event_time": event_time if event_time is not None else [None] * n,
            "feature_available_time": [None] * n,
            "prediction_time": [None] * n,
            "label_event_time": [None] * n,
            "label_available_time": [None] * n,
            "features": list(np.asarray(X, dtype=float)),
            "target": np.asarray(y, dtype=float),
            "domain_id": domain,
            "regime_id": None,
            "decision_context": None,
            "sample_weight": np.ones(n) if weights is None else weights,
            "split": ["unassigned"] * n if split is None else split,
            "metadata": metadata
            if metadata is not None
            else json.dumps({"availability": "unknown"}),
        }
    )


def acquire(dataset: str, config: dict, root="data") -> Path:
    if dataset not in SOURCES:
        raise ValueError(f"Unknown dataset {dataset}")
    source = SOURCES[dataset]
    if not source["status"].startswith("implemented"):
        raise RuntimeError(f"{dataset}: {source['status']}; no substitute data will be downloaded")
    root = Path(root)
    if dataset in {"eia", "fred", "monash", "wilds", "criteo"}:
        from importlib import import_module

        return import_module(f"shiftlab.data.real.{dataset}").acquire(config, root)
    raw = root / "raw" / dataset
    paths = []
    names = []
    limits = [
        "No verified real changepoints.",
        source["timing"],
        "Decision utilities are research-imposed, not operational ground truth.",
    ]
    if dataset == "gas_sensor":
        path = download(
            "https://archive.ics.uci.edu/static/public/224/gas+sensor+array+drift+dataset.zip",
            raw / "uci-224.zip",
        )
        paths.append(path)
        frames = []
        with zipfile.ZipFile(path) as archive:
            for batch in range(1, 11):
                member = next(
                    n for n in archive.namelist() if n.lower().endswith(f"/batch{batch}.dat")
                )
                X, y = load_svmlight_file(
                    io.BytesIO(archive.read(member)), n_features=128, zero_based=False
                )
                frame = standardize(
                    X.toarray(),
                    y,
                    f"batch-{batch}",
                    f"gas-batch-{batch}",
                    metadata=json.dumps({"batch": batch, "within_batch_order": "unknown"}),
                    split=np.full(
                        len(y),
                        "train"
                        if batch <= 5
                        else "validation"
                        if batch == 6
                        else "calibration"
                        if batch == 7
                        else "test",
                    ),
                )
                frames.append(frame)
        frame = pd.concat(frames, ignore_index=True)
        names = [f"sensor_feature_{i}" for i in range(128)]
    elif dataset == "noaa":
        year, station = int(config.get("year", 2023)), str(config.get("station", "74486094789"))
        if len(station) != 11 or not station.isdigit() or not 1901 <= year <= 2100:
            raise ValueError("NOAA station must be 11 digits and year valid")
        path = download(
            f"https://noaa-global-hourly-pds.s3.amazonaws.com/{year}/{station}.csv",
            raw / f"{year}-{station}-s3.csv",
        )
        paths.append(path)
        original = pd.read_csv(path, dtype=str)
        # Retain every quality/sentinel string in metadata; decode temperature and dewpoint only.
        names = ["temperature_C", "dewpoint_C"]
        values = []
        for key in ["TMP", "DEW"]:
            numeric = pd.to_numeric(original[key].str.split(",").str[0], errors="coerce")
            numeric = (numeric / 10).mask(numeric.abs() == 9999)
            values.append(numeric.to_numpy())
        times = (
            pd.to_datetime(original.DATE, utc=True).astype("datetime64[ns, UTC]").astype("int64")
            / 1e9
        )
        order = np.argsort(times.to_numpy(), kind="stable")
        original = original.iloc[order].reset_index(drop=True)
        X = np.column_stack(values)[order]
        # Retrospective next-observation target; horizon is preserved, not assumed hourly.
        frame = standardize(
            X[:-1],
            X[1:, 0],
            station,
            f"noaa-{station}-{year}",
            event_time=times.to_numpy()[order][:-1],
            split=assign_splits(times.to_numpy()[order][:-1]),
            metadata=[
                json.dumps(
                    {
                        "source": row,
                        "next_event_time": str(original.DATE.iloc[i + 1]),
                        "task": "next recorded observation temperature",
                        "release_latency": "unknown",
                    }
                )
                for i, row in enumerate(original.iloc[:-1].to_dict("records"))
            ],
        )
        frame["label_event_time"] = times.to_numpy()[order][1:]
        limits.append(
            "Temperature/dewpoint sentinels decoded; other measurement and quality fields retained as raw metadata. Not a strict hourly forecast when records are irregular."
        )
    elif dataset == "opsd":
        version = "2020-10-06"
        base = f"https://data.open-power-system-data.org/time_series/{version}/"
        paths.append(download(base + "datapackage.json", raw / version / "datapackage.json"))
        path = download(base + "time_series_60min_singleindex.csv", raw / version / "hourly.csv")
        paths.append(path)
        columns = config.get(
            "columns",
            [
                "DE_load_actual_entsoe_transparency",
                "DE_wind_generation_actual",
                "DE_solar_generation_actual",
            ],
        )
        # A bounded historical subset; raw publisher version retained in full with checksum.
        original = pd.read_csv(path, usecols=["utc_timestamp", "cet_cest_timestamp", *columns])
        original = original.loc[
            (original.utc_timestamp >= config.get("start", "2018-01-01"))
            & (original.utc_timestamp < config.get("end", "2019-01-01"))
        ].copy()
        if len(original) < 10:
            raise ValueError("OPSD selected period empty/too small")
        times = (
            pd.to_datetime(original.utc_timestamp, utc=True)
            .astype("datetime64[ns, UTC]")
            .astype("int64")
            .to_numpy()
            / 1e9
        )
        X = original[columns].to_numpy(float)
        frame = standardize(
            X[:-1],
            X[1:, 0],
            "DE",
            f"opsd-{version}",
            event_time=times[:-1],
            split=assign_splits(times[:-1]),
            metadata=[
                json.dumps(
                    {
                        "utc": u,
                        "cet_cest": v,
                        "release_latency": "unknown",
                        "task": "next-hour load",
                    }
                )
                for u, v in zip(
                    original.utc_timestamp.iloc[:-1], original.cet_cest_timestamp.iloc[:-1]
                )
            ],
        )
        frame["label_event_time"] = times[1:]
        names = columns
        limits.append(
            "Historical snapshots may contain revisions; no real-time availability guarantee. Source missingness and local offsets retained without filling."
        )
    elif dataset == "binance":
        from .binance import calendar

        symbol, month = config.get("symbol", "BTCUSDT"), config.get("month", "2023-01")
        interval = config.get("interval", "1d")
        if symbol not in ["BTCUSDT", "ETHUSDT"] or len(month) != 7:
            raise ValueError("Supported symbols BTCUSDT/ETHUSDT, month YYYY-MM")
        if interval not in {"1d", "1h"}:
            raise ValueError("Supported intervals are 1d and 1h")
        import re

        if not re.fullmatch(r"\d{4}-\d{2}", month):
            raise ValueError("Month must be YYYY-MM")
        pd.Period(month, freq="M")
        stem = f"{symbol}-{month}" if interval == "1d" else f"{symbol}-{interval}-{month}"
        url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{month}.zip"
        checksum = download(url + ".CHECKSUM", raw / f"{stem}.CHECKSUM")
        paths.append(checksum)
        path = download(url, raw / f"{stem}.zip", expected_sha256=checksum.read_text().split()[0])
        paths.append(path)
        with zipfile.ZipFile(path) as archive:
            original = pd.read_csv(archive.open(archive.namelist()[0]), header=None)
        timestamps = pd.to_numeric(original[0]).to_numpy()
        divisor = calendar(month, interval, timestamps, pd.to_numeric(original[6]).to_numpy())
        close = pd.to_numeric(original[4]).to_numpy(float)
        X = original[[1, 2, 3, 4, 5]].to_numpy(float)
        frame = standardize(
            X[:-1],
            close[1:] / close[:-1] - 1,
            symbol,
            f"binance-{symbol}-{month}",
            event_time=timestamps[:-1] / divisor,
            split=assign_splits(timestamps[:-1]),
            metadata=[
                json.dumps(
                    {
                        "close_time_raw": int(v),
                        "timestamp_divisor": divisor,
                        "interval": interval,
                        "task": "next close return; all current OHLCV require bar close",
                    }
                )
                for v in original[6].iloc[:-1]
            ],
        )
        frame["label_event_time"] = pd.to_numeric(original[6]).to_numpy()[1:] / divisor
        names = ["open", "high", "low", "close", "volume"]
    elif dataset == "folktables":
        try:
            import folktables
        except ImportError as exc:
            raise RuntimeError(
                "Install uv sync --extra data-sources before Folktables acquisition"
            ) from exc
        tasks = config.get("tasks", ["ACSIncome"])
        if len(tasks) != 1:
            raise ValueError("Use one Folktables task per version; invoke separately for each task")
        states = config.get("states", ["NJ"])
        years = config.get("years", [2018])
        if not set(tasks) <= {
            "ACSIncome",
            "ACSEmployment",
            "ACSPublicCoverage",
            "ACSMobility",
            "ACSTravelTime",
        }:
            raise ValueError("Unknown Folktables task")
        frames = []
        for year in years:
            source_acs = folktables.ACSDataSource(
                survey_year=str(year), horizon="1-Year", survey="person", root_dir=str(raw)
            )
            for state in states:
                records = source_acs.get_data(states=[state], download=True)
                for task_name in tasks:
                    task = getattr(folktables, task_name)
                    task.df_to_pandas(records)[0]
                    X, y, group = task.df_to_numpy(records)
                    # Task preprocess determines retained indices; derive matching survey weights.
                    selected = task._preprocess(records)
                    weights = selected.PWGTP.to_numpy() if "PWGTP" in selected else np.ones(len(y))
                    frame = standardize(
                        X,
                        y.ravel(),
                        f"{state}-{year}",
                        f"acs-{task_name}-{state}-{year}",
                        weights=weights,
                        metadata=[
                            json.dumps(
                                {
                                    "survey_year": year,
                                    "state": state,
                                    "task": task_name,
                                    "demographic_group": int(g),
                                    "within_year_order": "unknown",
                                }
                            )
                            for g in group.ravel()
                        ],
                    )
                    frames.append(frame)
        frame = pd.concat(frames, ignore_index=True)
        paths = [p for p in raw.rglob("*") if p.is_file()]
        if len(tasks) > 1:
            raise ValueError("Use one task per version to retain a consistent feature schema")
        names = list(getattr(folktables, tasks[0]).features)
        limits.append(
            "Annual ACS microdata are unordered; no individual event/release times or sequential split assigned."
        )
    elif dataset == "licensed_local":
        path = Path(config["path"])
        if not config.get("license") or not config.get("feature_columns"):
            raise ValueError("Licensed import requires license and explicit feature_columns")
        original = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        names = config["feature_columns"]
        frame = standardize(
            original[names].to_numpy(),
            original[config["target_column"]],
            config.get("domain", "licensed"),
            "licensed",
        )
        for column in [
            "event_time",
            "feature_available_time",
            "prediction_time",
            "label_event_time",
            "label_available_time",
        ]:
            if column in config.get("time_columns", {}):
                frame[column] = (
                    pd.to_datetime(original[config["time_columns"][column]], utc=True)
                    .astype("datetime64[ns, UTC]")
                    .astype("int64")
                    / 1e9
                )
        frame["metadata"] = [json.dumps(row, default=str) for row in original.to_dict("records")]
        source = {**source, "license": config["license"]}
        paths = [path]
    else:
        raise RuntimeError(f"Adapter unavailable: {dataset}")
    provenance = {
        "publisher": source["publisher"],
        "source_url": source["url"],
        "citation": source["citation"],
        "license": source["license"],
        "permitted_use": "Research only; respect original source terms",
        "raw_checksums": {str(p): sha256(p) for p in paths},
        "retrieval_parameters": config,
        "limitations": limits,
        "feature_names": names,
    }
    return save_dataset(
        [(frame, None)],
        dataset,
        root,
        provenance,
        config,
        ground_truth="coarse_domains" if dataset in ["gas_sensor", "folktables"] else "none",
    )
