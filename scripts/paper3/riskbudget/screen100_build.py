"""Build the 100-stream F3 real-data screen (protocol 05G_F3_REAL_SCREEN100_PROTOCOL.md).

Construction is that of scripts/sota_sprint/fresh_real.py (incumbent LR on the first 15%,
challenger HGB and preprocessing on the first 30%, 2000-event episodes, at most 20 per stream).
Raw files are expected under data/raw/screen100/. Writes data/screen100_losses/<name>.npz and
stats.json, including an entry for every stream that could not be built.

    PYTHONPATH=src .venv/bin/python scripts/paper3/riskbudget/screen100_build.py
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import traceback
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "sota_sprint"))
from fresh_real import prep  # noqa: E402

RAW = ROOT / "data/raw/screen100"
OUT = ROOT / "data/screen100_losses"
T_EP, MAX_EPS = 2000, 20


def calendar(df: pd.DataFrame, ts: pd.Series) -> pd.DataFrame:
    df = df.copy()
    df["hour"], df["weekday"], df["month"] = ts.dt.hour.values, ts.dt.weekday.values, ts.dt.month.values
    return df


def chrono(df: pd.DataFrame, ts: pd.Series):
    order = np.argsort(ts.to_numpy(), kind="stable")
    return df.iloc[order].reset_index(drop=True), ts.iloc[order].reset_index(drop=True)


# ------------------------------------------------------------------ loaders
# Each returns (X, y_raw, kind, categorical cols); kind "binary" uses y_raw as the label,
# "median" thresholds y_raw at the training-period median.
def forex(name):
    d = pd.read_parquet(RAW / "openml" / f"{name}.pq")
    ts = pd.to_datetime(d.pop("Timestamp"))
    d, ts = chrono(d, ts)
    y = d.pop("Class").astype(str)
    y = (y == sorted(y.unique())[-1]).astype(int)
    return calendar(d.astype(float), ts), y, "binary", []


def air_multisite(station):
    p = next((RAW / "x501/PRSA_Data_20130301-20170228").glob(f"PRSA_Data_{station}_*.csv"))
    d = pd.read_csv(p)
    d = d[d["PM2.5"].notna()].reset_index(drop=True)
    ts = pd.to_datetime(d[["year", "month", "day", "hour"]])
    y = d.pop("PM2.5")
    d = d.drop(columns=["No", "year", "month", "day", "hour", "station", "PM10"])
    d["wd"] = d["wd"].fillna("NA").astype(str)
    num = [c for c in d.columns if c != "wd"]
    d[num] = d[num].ffill().bfill()
    return calendar(d, ts), y, "median", ["wd"]


def air_city(city):
    d = pd.read_csv(next((RAW / "x394").glob(f"{city}PM*.csv")))
    d = d[d["PM_US Post"].notna()].reset_index(drop=True)
    ts = pd.to_datetime(d[["year", "month", "day", "hour"]])
    y = d.pop("PM_US Post")
    d = d.drop(columns=[c for c in d.columns if c.startswith("PM_")] + ["No", "year", "month", "day", "hour"])
    d["cbwd"] = d["cbwd"].fillna("NA").astype(str)
    num = [c for c in d.columns if c != "cbwd"]
    d[num] = d[num].ffill().bfill().fillna(0)
    return calendar(d, ts), y, "median", ["cbwd"]


def seoul_bike(_):
    raw = zipfile.ZipFile(RAW / "uci_560.zip").read("SeoulBikeData.csv").decode("latin1")
    d = pd.read_csv(io.StringIO(raw))
    ts = pd.to_datetime(d.pop("Date"), format="%d/%m/%Y") + pd.to_timedelta(d.pop("Hour"), unit="h")
    d, ts = chrono(d, ts)
    y = d.pop("Rented Bike Count")
    return calendar(d, ts), y, "median", ["Seasons", "Holiday", "Functioning Day"]


def tetouan(zone):
    d = pd.read_csv(io.BytesIO(zipfile.ZipFile(RAW / "uci_849.zip").read("Tetuan City power consumption.csv")))
    d.columns = [" ".join(c.split()) for c in d.columns]
    ts = pd.to_datetime(d.pop("DateTime"), format="%m/%d/%Y %H:%M")
    d, ts = chrono(d, ts)
    zcols = [c for c in d.columns if c.startswith("Zone")]
    y = d[f"Zone {zone} Power Consumption"]
    d = d.drop(columns=zcols)  # other zones are contemporaneous components of city load
    return calendar(d, ts), y, "median", []


def air_quality(_):
    raw = zipfile.ZipFile(RAW / "uci_360.zip").read("AirQualityUCI.csv")
    d = pd.read_csv(io.BytesIO(raw), sep=";", decimal=",").dropna(axis=1, how="all").dropna(how="all")
    ts = pd.to_datetime(d.pop("Date") + " " + d.pop("Time"), format="%d/%m/%Y %H.%M.%S")
    d = d.replace(-200, np.nan)
    d = d[d["CO(GT)"].notna()].reset_index(drop=True)
    ts = ts[d.index] if len(ts) == len(d) else ts.loc[ts.index.isin(d.index)]
    d, ts = chrono(d, ts.reset_index(drop=True))
    y = d.pop("CO(GT)")
    d = d.drop(columns=["PT08.S1(CO)"])  # tin-oxide CO sensor: a measurement of the target
    d = d.ffill().bfill()
    return calendar(d, ts), y, "median", []


def openml_event(name):
    d = pd.read_parquet(RAW / "openml" / f"{name}.pq")
    idx = json.loads((RAW / "openml_index.json").read_text())[name]
    tgt = idx["target"]
    y = d.pop(tgt).astype(str)
    y = (y == sorted(y.unique())[-1]).astype(int)
    if name == "creditcard":
        ts = d["Time"]
    elif name == "BitcoinHeist_Ransomware":
        ts = d["day"]
    elif name == "Homesite_Quote_Conversion":
        ts = pd.to_datetime(d.pop("Original_Quote_Date"))
        d = d.drop(columns=["QuoteNumber"])
    else:  # BAF_base
        ts = d["month"]
    order = np.argsort(np.asarray(ts), kind="stable")
    d, y = d.iloc[order].reset_index(drop=True), y.iloc[order].reset_index(drop=True)
    cat = [c for c in d.columns if not pd.api.types.is_numeric_dtype(d[c])]
    for c in cat:
        d[c] = d[c].astype(str)
    num = [c for c in d.columns if c not in cat]
    d[num] = d[num].astype(float).fillna(d[num].astype(float).median())
    return d, y, "binary", cat


_LD = None


def electricity(client):
    global _LD
    if _LD is None:
        with zipfile.ZipFile(RAW / "uci_321.zip") as z:
            _LD = pd.read_csv(z.open("LD2011_2014.txt"), sep=";", decimal=",", index_col=0)
        _LD.index = pd.to_datetime(_LD.index)
    s = _LD[client]
    s = s.iloc[int(np.argmax(s.to_numpy() > 0)) :]
    d = pd.DataFrame({"lag96": s.shift(96), "lag672": s.shift(672)})
    d["y"] = s
    d = d.iloc[672:]
    ts = pd.Series(d.index)
    d = d.reset_index(drop=True)
    y = d.pop("y")
    return calendar(d, ts), y, "median", []


def electricity_clients(k=43, min_rows=30_000):
    global _LD
    electricity("MT_001")  # loads _LD
    out = []
    for c in _LD.columns:
        s = _LD[c].to_numpy()
        if (s > 0).any() and len(s) - int(np.argmax(s > 0)) - 672 >= min_rows:
            out.append(c)
        if len(out) == k:
            break
    return out


def pool():
    idx = json.loads((RAW / "openml_index.json").read_text())
    p = [("forex", n, forex, n, 24) for n in sorted(idx) if n.startswith("FOREX")]
    stations = sorted(f.name.split("_")[2] for f in (RAW / "x501/PRSA_Data_20130301-20170228").glob("*.csv"))
    p += [("air_multisite", f"air_{s}", air_multisite, s, 24) for s in stations]
    p += [("air_cities", f"pm_{c}", air_city, c, 24) for c in ("Chengdu", "Guangzhou", "Shanghai", "Shenyang")]
    p += [("seoul_bike", "seoul_bike", seoul_bike, None, 24)]
    p += [("tetouan", f"tetouan_z{z}", tetouan, z, 144) for z in (1, 2, 3)]
    p += [("air_quality", "air_quality_co", air_quality, None, 24)]
    p += [("openml_events", n, openml_event, n, 100) for n in ("creditcard", "BitcoinHeist_Ransomware", "Homesite_Quote_Conversion", "BAF_base")]
    p += [("electricity", f"elec_{c}", electricity, c, 96) for c in electricity_clients()]
    return p


def build(group, name, loader, arg, delay) -> dict:
    x, yraw, kind, cat = loader(arg)
    for c in cat:
        x[c] = x[c].astype(str)
    n = len(x)
    n15, n30 = int(0.15 * n), int(0.30 * n)
    if kind == "median":
        thr = float(np.median(yraw.to_numpy()[:n30]))
        y = (yraw.to_numpy() > thr).astype(int)
    else:
        thr, y = None, yraw.to_numpy().astype(int)
    k = min(MAX_EPS, (n - n30) // T_EP)
    if k < 1:
        raise ValueError(f"fewer than one episode (n={n})")
    if len(np.unique(y[:n15])) < 2:
        raise ValueError("incumbent training window has one class")
    f = prep(x.iloc[:n30], cat)
    m0 = LogisticRegression(max_iter=300, C=1.0).fit(f(x.iloc[:n15]), y[:n15])
    m1 = HistGradientBoostingClassifier(max_iter=100, max_depth=4, learning_rate=0.1, random_state=0).fit(
        f(x.iloc[:n30]), y[:n30]
    )
    starts = np.array([n30 + i * T_EP for i in range(k)], dtype=np.int64)
    end = n30 + k * T_EP
    xe = f(x.iloc[n30:end])
    l0 = (m0.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP)
    l1 = (m1.predict(xe) != y[n30:end]).astype(np.int8).reshape(k, T_EP)
    np.savez(OUT / f"{name}.npz", l0=l0, l1=l1, starts=starts)
    adv = (l0.astype(float) - l1).mean(axis=1)
    return {
        "name": name, "group": group, "status": "built", "delay": delay, "n_rows": n, "K": int(k),
        "label_kind": kind, "threshold": thr,
        "content_sha256": hashlib.sha256(l0.tobytes() + l1.tobytes() + starts.tobytes()).hexdigest(),
        "incumbent_err": float(l0.mean()), "challenger_err": float(l1.mean()),
        "disagreement": float((l0 != l1).mean()), "n_challenger_better": int((adv > 0).sum()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    stats = []
    for group, name, loader, arg, delay in pool():
        try:
            s = build(group, name, loader, arg, delay)
        except Exception as e:  # recorded, never silently dropped
            s = {"name": name, "group": group, "status": "unbuildable", "reason": repr(e)[:300],
                 "trace": traceback.format_exc()[-600:]}
        stats.append(s)
        print(f"{s['group']:14s} {name:34s} {s['status']:11s} "
              + (f"K={s['K']:2d} e0={s['incumbent_err']:.3f} e1={s['challenger_err']:.3f} dis={s['disagreement']:.3f}"
                 if s["status"] == "built" else s["reason"][:90]), flush=True)
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    print("pool", len(stats), "built", sum(s["status"] == "built" for s in stats))


if __name__ == "__main__":
    main()
