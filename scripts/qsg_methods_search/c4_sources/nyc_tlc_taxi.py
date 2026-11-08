"""NYC TLC yellow taxi trip records, Aug-Oct 2025 (official parquet): generous tip among card trips.

Label rationale (fixed before downloading): only card payments (payment_type == 1) record tips.
Public TLC reporting puts the share of card trips with any tip well above 0.8, so tip_amount > 0
would be too imbalanced; the label is instead tip_amount >= 20% of fare_amount (fare_amount > 0
required as the denominator), a natural "standard tip" threshold expected inside [0.2, 0.8].
Features are pickup-time only; dropoff location/time, fare, tip, distance, totals are never
features. Event time = tpep_pickup_datetime.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import requests

BASE = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{m}.parquet"
MONTHS = ["2025-08", "2025-09", "2025-10"]
WINDOW = ("2025-08-01T00:00:00", "2025-11-01T00:00:00")
K = 12  # keep every K-th card trip in pickup-time order, per month
META = {
    "name": "nyc_tlc_taxi",
    "url": BASE,
    "license": "NYC TLC Trip Record Data terms of use (public, published by NYC Taxi & "
    "Limousine Commission)",
    "publisher": "New York City Taxi and Limousine Commission",
    "task": "binary: tip >= 20% of fare for credit-card yellow taxi trips",
    "label": "payment_type == 1 and fare_amount > 0; y = tip_amount >= 0.2 * fare_amount",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": f"load(): per month, card trips sorted by pickup time, every {K}th row; "
    "then c4_build.N_MAX systematic if above 400k",
    "features_note": "pickup hour/dow/month, PULocationID, passenger_count, RatecodeID, "
    "VendorID: all known at pickup. Dropoff, fare, tip, distance not used as features.",
}
NUM = ["hour", "dow", "month", "passenger_count"]
CAT = ["PULocationID", "RatecodeID", "VendorID"]
COLS = [
    "VendorID",
    "tpep_pickup_datetime",
    "passenger_count",
    "RatecodeID",
    "PULocationID",
    "payment_type",
    "fare_amount",
    "tip_amount",
]


def fetch(raw: Path) -> None:
    for m in MONTHS:
        out = raw / f"yellow_tripdata_{m}.parquet"
        if out.exists():
            continue
        r = requests.get(BASE.format(m=m), timeout=1800)
        r.raise_for_status()
        out.write_bytes(r.content)
        (raw / f"{out.name}.receipt.json").write_text(
            json.dumps(
                {
                    "url": r.url,
                    "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "bytes": len(r.content),
                    "sha256": hashlib.sha256(r.content).hexdigest(),
                },
                indent=1,
            )
        )


def load(raw: Path) -> pd.DataFrame:
    parts = []
    lo, hi = pd.Timestamp(WINDOW[0]), pd.Timestamp(WINDOW[1])
    for m in MONTHS:
        d = pq.read_table(raw / f"yellow_tripdata_{m}.parquet", columns=COLS).to_pandas()
        d = d[(d["payment_type"] == 1) & (d["fare_amount"] > 0)]
        d = d[(d["tpep_pickup_datetime"] >= lo) & (d["tpep_pickup_datetime"] < hi)]
        d = d.sort_values("tpep_pickup_datetime", kind="stable").iloc[::K]
        ts = d["tpep_pickup_datetime"]
        parts.append(
            pd.DataFrame(
                {
                    "ts": ts,
                    "y": (d["tip_amount"] >= 0.2 * d["fare_amount"]).astype(int),
                    "hour": ts.dt.hour,
                    "dow": ts.dt.dayofweek,
                    "month": ts.dt.month,
                    "passenger_count": d["passenger_count"],
                    "PULocationID": d["PULocationID"].astype("Int64").astype(str),
                    "RatecodeID": d["RatecodeID"].astype("Int64").astype(str),
                    "VendorID": d["VendorID"].astype("Int64").astype(str),
                }
            )
        )
        del d
    return pd.concat(parts, ignore_index=True).dropna(subset=["ts"])
