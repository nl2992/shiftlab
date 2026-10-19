"""Small, inspectable real adapters. Unknown release times remain null."""

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_svmlight_file

from ..catalogue import SOURCES
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
    if dataset in {"eia", "fred", "monash", "wilds", "criteo", "noaa", "opsd", "folktables"}:
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
    elif dataset == "binance":
        from .binance import prepare as prepare_binance

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
        frame, names = prepare_binance(original, symbol, month, interval)
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
