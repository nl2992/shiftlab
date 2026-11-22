"""Phase 10 retry: datasets whose original fetch failed, re-run from alternative public sources with the unchanged
pipeline (run_phase10.promotion_losses / stream_from_losses) and evaluator (run_phase5). INSECTS is intentionally not retried.

Usage: PYTHONPATH=src .venv/bin/python scripts/paper4_continuation/rbdp/real_data/run_phase10_retry.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]  # keep run_phase10's argv parsing at defaults
import run_phase10 as r10  # noqa: E402

p5 = r10.p5
p5.OUT = r10.RES / "attempts_phase10_retry.jsonl"
p5.LOG = r10.RES / "phase10_retry.log"
DATA = r10.ROOT / "data/raw/real_chains/phase10"


def load_kdd_sklearn():
    import pandas as pd
    from sklearn.datasets import fetch_kddcup99

    d = fetch_kddcup99(subset=None, percent10=True, as_frame=True, shuffle=False, data_home=str(DATA / "sklearn_kdd"))
    df = d.frame.copy()
    for c in df.columns:  # bytes -> str
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: v.decode() if isinstance(v, bytes) else v)
    y = (df.iloc[:, -1] != "normal.").astype(int).to_numpy()
    X = df.iloc[:, :-1]
    cat = [c for c in X.columns if c in ("protocol_type", "service", "flag")]
    X = pd.get_dummies(X, columns=cat, dtype=float).astype(float).to_numpy()
    return X, y


def load_bike_openml():
    import pandas as pd
    from sklearn.datasets import fetch_openml

    df = fetch_openml(data_id=42712, as_frame=True, data_home=str(DATA / "openml"), parser="auto").frame.dropna()
    yv = df["count"].astype(float)
    df = df.assign(count=(yv > yv.median()).astype(int))
    return r10._tab_from_frame(df, "count")


def _with_retries(f, tries=4):
    import time

    def g():
        for i in range(tries):
            try:
                return f()
            except Exception:
                if i == tries - 1:
                    raise
                time.sleep(20 * (i + 1))
    return g


def load_sms_uci():
    """UCI id 228 SMS Spam Collection, published row order; fixed TF-IDF map capped at 500 features; target spam."""
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer

    df = pd.read_csv(DATA / "raw/sms/SMSSpamCollection", sep="\t", header=None, names=["y", "text"], quoting=3)
    X = TfidfVectorizer(max_features=500).fit_transform(df["text"]).toarray()
    return X, (df["y"] == "spam").astype(int).to_numpy()


def load_occupancy_uci():
    """UCI id 357 Occupancy Detection: the three published files concatenated in chronological (date) order."""
    import pandas as pd

    parts = [pd.read_csv(DATA / f"raw/occ/{f}", index_col=0, parse_dates=["date"]) for f in ("datatest.txt", "datatraining.txt", "datatest2.txt")]
    df = pd.concat(parts, ignore_index=True).sort_values("date", kind="stable")
    return df[["Temperature", "Humidity", "Light", "CO2", "HumidityRatio"]].to_numpy(float), df["Occupancy"].astype(int).to_numpy()


def load_openml_id(data_id, max_rows=200_000):
    """Same logic as run_phase10.load_openml_target but by OpenML data_id and with target_column=None (the frame keeps
    every column; the default target is read from the dataset details), so rows with a missing target are dropped by dropna."""
    def f():
        import pandas as pd
        from sklearn.datasets import fetch_openml

        d = fetch_openml(data_id=data_id, as_frame=True, data_home=str(DATA / "openml"), parser="auto", target_column=None)
        df = d.frame.iloc[:max_rows].dropna()
        tcol = d.details["default_target_attribute"].split(",")[0]
        yv = df[tcol]
        if pd.api.types.is_numeric_dtype(yv) and yv.nunique() > 20:
            df = df.assign(**{tcol: (yv > yv.median()).astype(int)})
        return r10._tab_from_frame(df, tcol)
    return _with_retries(f)


def _c(nm, data_id, note):
    return (f"C:{nm}", load_openml_id(data_id), f"OpenML data_id={data_id} ({note})", r10.CREASON[nm])


RETRY = [
    ("B:kdd99_10pct", load_kdd_sklearn, "sklearn.datasets.fetch_kddcup99(subset=None, percent10=True, shuffle=False)",
     r10.REASONS["B:kdd99_10pct"]),
    ("Bext:Bike_Sharing_Demand", load_bike_openml, "OpenML data_id=42712 (Bike_Sharing_Demand v2, hourly UCI bike sharing)",
     "demand; hourly bike rentals over two years (seasonal/yearly drift), target count above median"),
    ("Bext:SMSSpam", load_sms_uci, "UCI id 228 SMS Spam Collection (TF-IDF, 500 features, published order)", "text; spam filtering of SMS messages"),
    ("Bext:OnlineNewsPopularity", _with_retries(r10.load_openml_target("OnlineNewsPopularity")),
     "OpenML name=OnlineNewsPopularity v1 (data_id 4545), retried after HTTP 503", "news popularity over time"),
    ("Bext:adult", _with_retries(r10.load_openml_target("adult")), "OpenML name=adult v1 (data_id 179), retried after HTTP 503", "census"),
    ("Bext:occupancy", load_occupancy_uci, "UCI id 357 Occupancy Detection (3 files, chronological order)", "building sensors"),
    _c("road-safety", 42803, "road-safety v4"),
    _c("numerai28.6", 23517, "numerai28.6 v2"),
    _c("Amazon_employee_access", 43900, "amazon_employee_access v2"),
    _c("electricity-normalized", 43945, "electricity v2, 38474-row normalised variant; name 'electricity-normalized' does not exist on OpenML"),
    _c("kdd_el_nino-small", 563, "kdd_el_nino-small v1 fetched with target_column=None; rows with missing target dropped"),
]

if __name__ == "__main__":
    done = p5.done_ids()
    for cid, loader, source, reason in RETRY:
        if cid in done:
            continue
        fam = cid.split(":")[0]
        for c, meta, streams in r10._bench_family([(cid, loader)], fam):
            rec = {"id": c, **meta, "source": source, "retry_of": "fetch failed", "reason": reason}
            if streams is None:
                rec.setdefault("status", "fetch failed")
                rec["positive"] = False
            else:
                rec.update(p5.eval_streams(c, streams))
            p5.emit(rec)
            p5.log("DONE", c, rec.get("status"), "positive", rec.get("positive"))
