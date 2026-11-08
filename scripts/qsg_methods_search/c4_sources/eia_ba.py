"""EIA-930 hourly balancing-authority demand vs day-ahead forecast (local EBA.zip bulk file).

BA choice rule (fixed before any modelling): exclude CISO and ERCO (already used elsewhere); among
the remaining BAs pick the one with the most hourly UTC timestamps having both D (demand) and DF
(day-ahead demand forecast) non-missing. Ties broken by BA code. The rule is evaluated in load().
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
ZIP = ROOT / "data/raw/eia/EBA.zip"
RECEIPT = ROOT / "data/raw/eia/EBA.zip.receipt.json"
EXCLUDE = {"CISO", "ERCO"}
PAT = re.compile(r'"series_id":\s*"EBA\.([A-Z0-9]+)-ALL\.(D|DF)\.H"')
META = {
    "name": "eia_ba",
    "url": "https://www.eia.gov/opendata/bulk/EBA.zip",
    "license": "U.S. EIA open data (public domain, U.S. government work)",
    "publisher": "U.S. Energy Information Administration, Form EIA-930",
    "task": "binary: realised hourly demand exceeds the day-ahead demand forecast (forecast-error sign)",
    "label": "D > DF (ties count as 0)",
    "delay": 24,
    "window": "full available history of the selected BA (UTC hours with D and DF both present)",
    "subsample_rule": "none expected (< c4_build.N_MAX)",
    "features_note": "UTC hour/day-of-week/month, day-ahead forecast level, forecast error D-DF "
    "at t-24 and t-48, mean error over t-24..t-47 (all >= 24h old; NaN across gaps). BA chosen by "
    "the data-availability rule in the module docstring.",
}
NUM = ["hour", "dow", "month", "forecast", "err_l24", "err_l48", "err_mean_24_47"]
CAT: list[str] = []


def fetch(raw: Path) -> None:
    """Verify the local bulk file against its receipt; copy nothing."""
    rec = json.loads(RECEIPT.read_text())
    h = hashlib.sha256()
    with open(ZIP, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    if h.hexdigest() != rec["sha256"]:
        raise RuntimeError(f"EBA.zip sha256 mismatch: {h.hexdigest()} != {rec['sha256']}")


def _scan() -> dict[str, dict[str, pd.Series]]:
    out: dict[str, dict[str, pd.Series]] = {}
    with zipfile.ZipFile(ZIP) as z, z.open("EBA.txt") as f:
        for line in f:
            m = PAT.search(line[:300].decode("utf8", "ignore"))
            if not m or m.group(1) in EXCLUDE:
                continue
            d = json.loads(line)
            rows = [(t, float(v)) for t, v in d["data"] if v is not None]
            s = pd.Series(
                {
                    pd.Timestamp(t[:4] + "-" + t[4:6] + "-" + t[6:8] + " " + t[9:11] + ":00"): v
                    for t, v in rows
                },
                dtype=float,
            ).sort_index()
            out.setdefault(m.group(1), {})[m.group(2)] = s
    return out


def load(raw: Path) -> pd.DataFrame:
    series = _scan()
    counts = {
        ba: len(v["D"].index.intersection(v["DF"].index))
        for ba, v in series.items()
        if "D" in v and "DF" in v
    }
    ba = min(counts, key=lambda k: (-counts[k], k))
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "selection.json").write_text(
        json.dumps(
            {
                "selected": ba,
                "excluded": sorted(EXCLUDE),
                "top10_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])[:10]),
            },
            indent=1,
        )
    )
    D, DF = series[ba]["D"], series[ba]["DF"]
    idx = pd.date_range(
        min(D.index.min(), DF.index.min()), max(D.index.max(), DF.index.max()), freq="h"
    )
    D, DF = D.reindex(idx), DF.reindex(idx)
    err = D - DF
    out = pd.DataFrame(
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
        }
    )
    return out.dropna(subset=["y"]).reset_index(drop=True)
