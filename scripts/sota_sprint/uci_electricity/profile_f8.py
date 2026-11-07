"""Stream only the UCI 2011-2012 partition and screen for the frozen F8 profile."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/uci_electricity_f8_20261107"
ARCHIVE = ROOT / "data/raw/uci_electricity_f8_20261107/electricityloaddiagrams20112014.zip"
MEMBER = "LD2011_2014.txt"
N_CLIENTS = 370
TRAIN_ROWS = 365 * 96 - 1
DEV_ROWS = 366 * 96
DEV_END = TRAIN_ROWS + DEV_ROWS
LAGS = (1, 96, 672, 1344)
HGB = {
    "max_iter": 150,
    "learning_rate": 0.05,
    "max_leaf_nodes": 15,
    "l2_regularization": 1.0,
    "random_state": 1729,
}


def load_development_partition() -> tuple[list[str], np.ndarray, pd.DatetimeIndex]:
    """Read exactly 2011 and 2012 rows; never iterate into 2013-2014 data."""
    values = np.empty((DEV_END, N_CLIENTS), dtype=np.float32)
    timestamps: list[str] = []
    with zipfile.ZipFile(ARCHIVE) as archive, archive.open(MEMBER) as byte_stream:
        text_stream = (line.decode("utf-8").rstrip("\r\n") for line in byte_stream)
        reader = csv.reader(text_stream, delimiter=";")
        header = next(reader)
        if len(header) != N_CLIENTS + 1:
            raise ValueError(f"expected 1 timestamp + 370 clients, got {len(header)} columns")
        for row_id in range(DEV_END):
            row = next(reader)
            if len(row) != N_CLIENTS + 1:
                raise ValueError(f"row {row_id} has {len(row)} fields")
            timestamps.append(row[0])
            values[row_id] = np.fromiter(
                (float(value.replace(",", ".")) for value in row[1:]),
                dtype=np.float32,
                count=N_CLIENTS,
            )
    index = pd.DatetimeIndex(pd.to_datetime(timestamps, errors="raise"))
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError(
            "source timestamps are not strictly increasing in the development partition"
        )
    if index[0].year != 2011 or index[TRAIN_ROWS - 1].year != 2011:
        raise ValueError("the fixed 2011 training row boundary disagrees with source timestamps")
    if index[TRAIN_ROWS].year != 2012 or index[-1].year != 2012:
        raise ValueError("the fixed 2012 development row boundary disagrees with source timestamps")
    return header[1:], values, index


def features_for(
    series: np.ndarray, row_ids: np.ndarray, timestamps: pd.DatetimeIndex
) -> np.ndarray:
    """Features for row t use only the series through t-1."""
    n = len(series)
    csum = np.r_[0.0, np.cumsum(series, dtype=np.float64)]
    feat = [series[row_ids - lag] for lag in LAGS]
    left = row_ids - 96
    right = row_ids
    feat.append((csum[right] - csum[left]) / 96.0)
    rolling_max = (
        pd.Series(series)
        .shift(1)
        .rolling(96, min_periods=96)
        .max()
        .to_numpy(dtype=np.float32)[row_ids]
    )
    feat.append(rolling_max)
    dt = timestamps[row_ids]
    minute_of_day = dt.hour.to_numpy() * 60 + dt.minute.to_numpy()
    day_of_week = dt.dayofweek.to_numpy()
    day_of_year = dt.dayofyear.to_numpy()
    feat.extend(
        [
            np.sin(2 * np.pi * minute_of_day / 1440),
            np.cos(2 * np.pi * minute_of_day / 1440),
            np.sin(2 * np.pi * day_of_week / 7),
            np.cos(2 * np.pi * day_of_week / 7),
            np.sin(2 * np.pi * day_of_year / 366),
            np.cos(2 * np.pi * day_of_year / 366),
        ]
    )
    out = np.column_stack(feat).astype(np.float32, copy=False)
    if out.shape[0] != len(row_ids) or n <= int(row_ids[-1]):
        raise AssertionError("feature row mismatch")
    return out


def main() -> None:
    if not ARCHIVE.is_file():
        raise FileNotFoundError(f"source archive not found: {ARCHIVE}")
    if (PILOT / "DATASET_PROFILE.json").exists():
        raise SystemExit("profile exists; refusing to overwrite frozen outcome")
    names, values, timestamps = load_development_partition()
    started = monotonic()
    profiles: dict[str, dict] = {}
    for client_id, client_name in enumerate(names):
        if client_id % 25 == 0:
            print(
                f"profile client {client_id}/{len(names)}; elapsed {monotonic() - started:.0f}s",
                flush=True,
            )
        series = values[:, client_id]
        train_nonzero = (series[:TRAIN_ROWS] > 0).sum()
        if train_nonzero < 20_000:
            continue
        positive_train = series[:TRAIN_ROWS][series[:TRAIN_ROWS] > 0]
        threshold = float(np.quantile(positive_train, 0.90))
        first_nonzero = int(np.flatnonzero(series[:TRAIN_ROWS] > 0)[0])
        train_ids = np.arange(max(first_nonzero + max(LAGS), max(LAGS)), TRAIN_ROWS)
        dev_ids = np.arange(max(TRAIN_ROWS, first_nonzero + max(LAGS)), DEV_END)
        if not len(train_ids) or not len(dev_ids):
            continue
        x_train = features_for(series, train_ids, timestamps)
        y_train = (series[train_ids] >= threshold).astype(np.int8)
        if np.unique(y_train).size < 2:
            continue
        model = HistGradientBoostingClassifier(**HGB)
        with threadpool_limits(limits=1, user_api="openmp"):
            model.fit(
                x_train,
                y_train,
                sample_weight=compute_sample_weight("balanced", y_train),
            )
        x_dev = features_for(series, dev_ids, timestamps)
        y_dev = (series[dev_ids] >= threshold).astype(np.int8)
        incumbent = (series[dev_ids - 96] >= threshold).astype(np.int8)
        challenger = (model.predict(x_dev) >= 0.5).astype(np.int8)
        disagree = incumbent != challenger
        n_disagree = int(disagree.sum())
        disagreement_rate = float(disagree.mean())
        challenger_accuracy = (
            float((challenger[disagree] == y_dev[disagree]).mean()) if n_disagree else None
        )
        n_blocks = len(dev_ids) // 2000
        match = (
            0.01 <= disagreement_rate <= 0.05
            and challenger_accuracy is not None
            and challenger_accuracy >= 0.85
        )
        profiles[client_name] = {
            "train_nonzero_rows": int(train_nonzero),
            "train_rows": len(train_ids),
            "development_rows": len(dev_ids),
            "threshold_kw_p90_positive_2011": threshold,
            "disagreement_count_2012": n_disagree,
            "disagreement_rate_2012": disagreement_rate,
            "challenger_accuracy_on_disagreements_2012": challenger_accuracy,
            "nonoverlap_2000_event_blocks": int(n_blocks),
            "f8_profile_match": bool(match),
        }
    matches = [name for name, item in profiles.items() if item["f8_profile_match"]]
    source_digest = hashlib.sha256()
    with ARCHIVE.open("rb") as source_stream:
        for block in iter(lambda: source_stream.read(1024 * 1024), b""):
            source_digest.update(block)
    source_sha = source_digest.hexdigest()
    result = {
        "protocol": "research/scoped_method/pilots/uci_electricity_f8_20261107/PROTOCOL.md",
        "source": {
            "url": "https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip",
            "archive": "data/raw/uci_electricity_f8_20261107/electricityloaddiagrams20112014.zip",
            "retrieved_utc": datetime.now(UTC).isoformat(),
            "bytes": ARCHIVE.stat().st_size,
            "sha256": source_sha,
            "inner_member": MEMBER,
        },
        "partition": {
            "train": "2011 source rows only",
            "development": "2012 source rows only",
            "test": "2013-2014 not read by this program",
            "train_rows": TRAIN_ROWS,
            "development_rows": DEV_ROWS,
            "first_development_timestamp": timestamps[TRAIN_ROWS].isoformat(),
            "last_development_timestamp": timestamps[-1].isoformat(),
        },
        "candidate_rule": "2011 fit; 2012 F8 profile; require at least 20 matching clients",
        "eligible_clients": len(profiles),
        "matching_clients": len(matches),
        "matching_client_ids": matches,
        "profile_threshold_pass": len(matches) >= 20,
        "profiles": profiles,
        "interpretation": "profile screen only; no policy replay, 2013-2014 rows, or cost outcomes",
    }
    (PILOT / "DATASET_PROFILE.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "eligible_clients": result["eligible_clients"],
                "matching_clients": result["matching_clients"],
                "profile_threshold_pass": result["profile_threshold_pass"],
                "source": result["source"],
                "partition": result["partition"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
