"""EIA-930 hourly demand vs day-ahead forecast, all balancing authorities pooled (local EBA.zip bulk file).

Event = one (balancing authority, UTC hour) with both D (demand) and DF (day-ahead forecast). Label y = 1 if
D > DF (ties 0): the forecast error sign, observed at the end of the hour. Features known at the start of the
hour: BA, UTC hour/dow/month, DF (the day-ahead forecast issued the day before), forecast error D-DF at t-24
and t-48, mean error over t-24..t-47, and the relative lag-24 error. Never D at t.
Pooling over BAs makes the stream ~70 events per hour, so the contract delay of 100 events is about one
hour, close to the 1-2 hour EIA-930 publication latency (documented, not tuned).

Window (protocol rule): DEV = hours 2024-07-01 .. 2025-06-30 UTC (last 12 months of the 2023-07..2025-07 span,
since the pooled count exceeds 400k per year); CONFIRM = 2025-07-01 .. 2026-06-30 UTC (the local bulk file ends
2026-10-20). parent_source_id eia_930 is shared with the single-BA recipe `eia_ba` (ineligible): one counts.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

MAIN = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
ZIP = MAIN / "data/raw/eia/EBA.zip"
RECEIPT = MAIN / "data/raw/eia/EBA.zip.receipt.json"
PAT = re.compile(r'"series_id":\s*"EBA\.([A-Z0-9]+)-ALL\.(D|DF)\.H"')
WINDOW = ("2024-07-01T00:00:00", "2025-07-01T00:00:00")
META = {
    "name": "eia930_pooled",
    "url": "https://www.eia.gov/opendata/bulk/EBA.zip",
    "license": "U.S. EIA open data (public domain, U.S. government work)",
    "publisher": "U.S. Energy Information Administration, Form EIA-930",
    "task": "binary: realised hourly demand exceeds the day-ahead forecast, pooled over balancing authorities",
    "label": "D > DF (ties 0)",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "BA, UTC hour/dow/month, DF, error at t-24 and t-48, mean error t-24..t-47, relative lag-24 error",
}
NUM = ["hour", "dow", "month", "forecast", "err_l24", "err_l48", "err_mean_24_47", "rel_err_l24"]
CAT = ["ba"]


def fetch(raw: Path) -> None:
    rec = json.loads(RECEIPT.read_text())
    h = hashlib.sha256()
    with open(ZIP, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    if h.hexdigest() != rec["sha256"]:
        raise RuntimeError("EBA.zip sha256 mismatch")
    (raw / "source_receipt.json").write_text(json.dumps({**rec, "verified_sha256": h.hexdigest()}, indent=1))


def load(raw: Path) -> pd.DataFrame:
    series: dict[str, dict[str, pd.Series]] = {}
    with zipfile.ZipFile(ZIP) as z, z.open("EBA.txt") as f:
        for line in f:
            m = PAT.search(line[:300].decode("utf8", "ignore"))
            if not m:
                continue
            d = json.loads(line)
            s = pd.Series(
                {
                    pd.Timestamp(t[:4] + "-" + t[4:6] + "-" + t[6:8] + " " + t[9:11] + ":00"): float(v)
                    for t, v in d["data"]
                    if v is not None
                },
                dtype=float,
            ).sort_index()
            series.setdefault(m.group(1), {})[m.group(2)] = s
    frames = []
    for ba, v in sorted(series.items()):
        if "D" not in v or "DF" not in v:
            continue
        D, DF = v["D"], v["DF"]
        idx = pd.date_range(min(D.index.min(), DF.index.min()), max(D.index.max(), DF.index.max()), freq="h")
        D, DF = D.reindex(idx), DF.reindex(idx)
        err = D - DF
        o = pd.DataFrame(
            {
                "ts": idx,
                "y": (D > DF).astype(float).where(D.notna() & DF.notna()),
                "hour": idx.hour,
                "dow": idx.dayofweek,
                "month": idx.month,
                "forecast": DF.values,
                "err_l24": err.shift(24).values,
                "err_l48": err.shift(48).values,
                "err_mean_24_47": err.shift(24).rolling(24, min_periods=12).mean().values,
                "ba": ba,
            }
        )
        o["rel_err_l24"] = o["err_l24"] / o["forecast"].replace(0, np.nan)
        o = o[(o["ts"] >= WINDOW[0]) & (o["ts"] < WINDOW[1])].dropna(subset=["y"])
        frames.append(o)
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["ts", "ba"], kind="stable").reset_index(drop=True)
