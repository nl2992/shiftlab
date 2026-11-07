"""Fresh real chronological loss streams for final external validation (SOTA sprint, Agent E).

Builds frozen incumbent/challenger loss pairs on five public UCI datasets never used before in
ShiftLab, mirroring scripts/promising_directions/b3_real_data.py::build_fetched:

* rows in chronological order, n rows;
* incumbent  = LogisticRegression(max_iter=300, C=1.0) fit on rows [0, 0.15n);
* challenger = HistGradientBoostingClassifier(max_iter=100, max_depth=4, lr=0.1, rs=0)
  fit on rows [0, 0.30n);
* label threshold (training-period median) and preprocessing (StandardScaler + OneHot) fit on
  rows [0, 0.30n) only;
* episodes: consecutive non-overlapping 2000-event windows from 0.30n, at most 20 per dataset;
* losses l = 1[pred != y] (int8).

This script fits models only. It never runs a ShiftLab policy or the screen runner.

    uv run python scripts/sota_sprint/fresh_real.py            # download (if absent) + build
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/sprint_fresh"
OUT = ROOT / "data/sprint_fresh_losses"
T_EP = 2000
MAX_EPS = 20

SOURCES = {
    "metro": (492, "metro+interstate+traffic+volume"),
    "beijing_pm25": (381, "beijing+pm2+5+data"),
    "bike_hour": (275, "bike+sharing+dataset"),
    "appliances": (374, "appliances+energy+prediction"),
    "household_power": (235, "individual+household+electric+power+consumption"),
}
# Registered label delay, in events: one day of natural time.
DELAYS = {
    "metro": 24,  # hourly
    "beijing_pm25": 24,  # hourly
    "bike_hour": 24,  # hourly
    "appliances": 144,  # 10-minute
    "household_power": 144,  # 10-minute means
}
LICENSE = "CC BY 4.0 (UCI Machine Learning Repository)"


def url(name: str) -> str:
    uid, slug = SOURCES[name]
    return f"https://archive.ics.uci.edu/static/public/{uid}/{slug}.zip"


def raw_zip(name: str) -> Path:
    p = RAW / f"uci_{SOURCES[name][0]}" / "raw.zip"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url(name), p)
    return p


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def member(name: str, fname: str) -> bytes:
    with zipfile.ZipFile(raw_zip(name)) as z:
        return z.read(fname)


def calendar(df: pd.DataFrame, ts: pd.Series) -> pd.DataFrame:
    df = df.copy()
    df["hour"], df["weekday"], df["month"] = ts.dt.hour, ts.dt.weekday, ts.dt.month
    return df


# ----------------------------------------------------------------------------- loaders
# Each returns (features DataFrame, raw target Series, timestamps), chronologically sorted.
def load_metro():
    df = pd.read_csv(
        io.BytesIO(gzip.decompress(member("metro", "Metro_Interstate_Traffic_Volume.csv.gz")))
    )
    ts = pd.to_datetime(df.pop("date_time"))
    order = np.argsort(ts.to_numpy(), kind="stable")
    df, ts = df.iloc[order].reset_index(drop=True), ts.iloc[order].reset_index(drop=True)
    y = df.pop("traffic_volume")
    df["holiday"] = df["holiday"].fillna("None").astype(str)
    return calendar(df, ts), y, ts


def load_beijing_pm25():
    df = pd.read_csv(io.BytesIO(member("beijing_pm25", "PRSA_data_2010.1.1-2014.12.31.csv")))
    df = df[df["pm2.5"].notna()].reset_index(drop=True)
    ts = pd.to_datetime(df[["year", "month", "day", "hour"]])
    y = df.pop("pm2.5")
    df = df.drop(columns=["No", "year", "month", "day", "hour"])
    return calendar(df, ts), y, ts


def load_bike_hour():
    df = pd.read_csv(io.BytesIO(member("bike_hour", "hour.csv")))
    ts = pd.to_datetime(df["dteday"]) + pd.to_timedelta(df["hr"], unit="h")
    y = df.pop("cnt")
    # casual + registered = cnt (leakage); yr is a trend index; calendar re-derived below.
    df = df.drop(
        columns=["instant", "dteday", "yr", "casual", "registered", "mnth", "hr", "weekday"]
    )
    return calendar(df, ts), y, ts


def load_appliances():
    df = pd.read_csv(io.BytesIO(member("appliances", "energydata_complete.csv")))
    ts = pd.to_datetime(df.pop("date"))
    y = df.pop("Appliances").astype(float)
    df = df.drop(columns=["rv1", "rv2"])  # documented random variables
    return calendar(df, ts), y, ts


def load_household_power():
    raw = member("household_power", "household_power_consumption.txt")
    df = pd.read_csv(io.BytesIO(raw), sep=";", na_values="?", low_memory=False)
    ts = pd.to_datetime(df.pop("Date") + " " + df.pop("Time"), format="%d/%m/%Y %H:%M:%S")
    df = df.set_index(ts).sort_index().astype(float)
    df = df.resample("10min").mean().dropna()  # 10-minute means; drop bins with no reading
    ts = pd.Series(df.index, name="ts").reset_index(drop=True)
    df = df.reset_index(drop=True)
    y = df.pop("Global_active_power")
    # Global_intensity ~ P/V and the three sub-meterings are contemporaneous components of the
    # target; drop as leakage. Keep reactive power, voltage and calendar.
    df = df.drop(columns=["Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3"])
    return calendar(df, ts), y, ts


LOADERS = {
    "metro": load_metro,
    "beijing_pm25": load_beijing_pm25,
    "bike_hour": load_bike_hour,
    "appliances": load_appliances,
    "household_power": load_household_power,
}
CATEGORICAL = {
    "metro": ["holiday", "weather_main", "weather_description"],
    "beijing_pm25": ["cbwd"],
}


def prep(xtr: pd.DataFrame, cat: list[str]):
    """Train-only preprocessing (as b3_real_data.prep)."""
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    num = [c for c in xtr.columns if c not in cat]
    sc = StandardScaler().fit(xtr[num])
    oh = (
        OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=False).fit(xtr[cat])
        if cat
        else None
    )

    def f(a):
        parts = [sc.transform(a[num])]
        if oh is not None:
            parts.append(oh.transform(a[cat]))
        return np.hstack(parts)

    return f


def build(name: str) -> dict:
    x, yraw, ts = LOADERS[name]()
    cat = CATEGORICAL.get(name, [])
    for c in cat:
        x[c] = x[c].astype(str)
    n = len(x)
    n15, n30 = int(0.15 * n), int(0.30 * n)
    thr = float(np.median(yraw.to_numpy()[:n30]))
    y = (yraw.to_numpy() > thr).astype(int)
    f = prep(x.iloc[:n30], cat)
    m0 = LogisticRegression(max_iter=300, C=1.0).fit(f(x.iloc[:n15]), y[:n15])
    m1 = HistGradientBoostingClassifier(
        max_iter=100, max_depth=4, learning_rate=0.1, random_state=0
    ).fit(f(x.iloc[:n30]), y[:n30])
    k = min(MAX_EPS, (n - n30) // T_EP)
    starts = np.array([n30 + i * T_EP for i in range(k)], dtype=np.int64)
    end = n30 + k * T_EP
    xe = f(x.iloc[n30:end])
    l0 = (m0.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP)
    l1 = (m1.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.npz"
    np.savez(out, l0=l0, l1=l1, starts=starts)
    content = hashlib.sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()).hexdigest()
    adv = (l0.astype(float) - l1).mean(axis=1)  # incumbent loss - challenger loss
    return {
        "dataset": name,
        "uci_id": SOURCES[name][0],
        "url": url(name),
        "license": LICENSE,
        "raw_sha256": sha256(raw_zip(name)),
        "npz": str(out.relative_to(ROOT)),
        "npz_sha256": sha256(out),
        "array_content_sha256": content,
        "n_rows": n,
        "time_span": [str(ts.iloc[0]), str(ts.iloc[-1])],
        "n_features_raw": int(x.shape[1]),
        "label_threshold_train_median": thr,
        "train_pos_rate": float(y[:n30].mean()),
        "eval_pos_rate": float(y[n30:end].mean()),
        "n15": n15,
        "n30": n30,
        "K": int(k),
        "eval_end": int(end),
        "delay_events": DELAYS[name],
        "incumbent_err": float(l0.mean()),
        "challenger_err": float(l1.mean()),
        "disagreement": float((l0 != l1).mean()),
        "mean_adv_per_episode": [round(float(a), 4) for a in adv],
        "n_challenger_better": int((adv > 0).sum()),
        "n_tied": int((adv == 0).sum()),
    }


def main() -> None:
    stats = [build(nm) for nm in LOADERS]
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    for s in stats:
        print(
            f"{s['dataset']:16s} n={s['n_rows']:6d} K={s['K']:2d} err0={s['incumbent_err']:.3f} "
            f"err1={s['challenger_err']:.3f} dis={s['disagreement']:.3f} "
            f"better={s['n_challenger_better']}/{s['K']}"
        )


if __name__ == "__main__":
    main()
