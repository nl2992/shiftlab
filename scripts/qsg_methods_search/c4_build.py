"""C4 shared builder: frozen chronological model pair, validation gates, sealed test losses.

One recipe for every source (docs/qsg_methods_search/c4_plan.md §3–4, Amendment A1). A source
module ``c4_sources/<name>.py`` provides:

    META = {"name", "url", "license", "publisher", "task", "label", "delay", "window",
            "subsample_rule", "features_note"}
    def fetch(raw_dir: Path) -> None          # download raw files (idempotent), write receipts
    def load(raw_dir: Path) -> pd.DataFrame    # columns: ts (sortable), y (0/1), features...
    NUM: list[str]; CAT: list[str]            # feature columns available at event time

The builder never prints, returns or records any statistic of the test window. It writes only
the sealed loss arrays, their content hash and the episode count. Validation-window gate
statistics are recorded.

Usage: python c4_build.py build <name> [--fetch]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
RAW = ROOT / "data/raw/c4"
SEALED = ROOT / "data/c4_sealed"
RECORDS = ROOT / "docs/qsg_methods_search/c4_builds"

FRACS = (0.2, 0.2, 0.1)  # train-old, train-new, validation; the remaining 50% is test
N_MAX = 400_000  # deterministic systematic subsample above this (chronology preserved)
T_EP = 2000
MIN_EPISODES = 35  # Amendment A1
GATES = {"min_disagreement": 0.03, "err_low": 0.02, "err_high": 0.5}


def subsample(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if len(df) <= N_MAX:
        return df, "none"
    idx = np.unique(np.linspace(0, len(df) - 1, N_MAX).round().astype(int))
    return df.iloc[idx].reset_index(drop=True), f"systematic {len(idx)} of {len(df)}"


def make_prep(num, cat):
    parts = []
    if num:
        parts.append(
            ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num)
        )
    if cat:
        parts.append(
            (
                "cat",
                make_pipeline(
                    SimpleImputer(strategy="constant", fill_value="NA"),
                    OneHotEncoder(
                        handle_unknown="infrequent_if_exist",
                        min_frequency=20,
                        max_categories=64,
                        sparse_output=False,
                    ),
                ),
                cat,
            )
        )
    return ColumnTransformer(parts)


def array_hash(*arrs) -> str:
    h = hashlib.sha256()
    for a in arrs:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


# Fresh-window rebuilds (docs/paper1_eqsdp/19_FRESH_CONFIRMATION_PROTOCOL.md): same recipe, overridden
# window; a few publishers split data by year, so the layer/file constant is patched explicitly.
FRESH_RAW = ROOT / "data/raw/c4_fresh"
FRESH_RECORDS = ROOT / "docs/paper1_eqsdp/fresh_builds"
FRESH_PATCH = {
    "dc_311": {
        "BASE": "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/"
        "FeatureServer/18/query",
        "FILE": "dc311_2025.csv",
    }
}


def _fmt_like(old: str, new: str) -> str:
    sep = "T" if "T" in old else " "
    return new.replace("T", sep).replace(" ", sep) if len(new) > 10 else f"{new}{sep}00:00:00"


def build(name: str, do_fetch: bool, window=None, tag=None) -> dict:
    mod = importlib.import_module(f"c4_sources.{name}")
    raw = RAW / name
    records, suffix = RECORDS, ""
    if window is not None:
        mod.WINDOW = (_fmt_like(mod.WINDOW[0], window[0]), _fmt_like(mod.WINDOW[1], window[1]))
        mod.META = {**mod.META, "window": mod.WINDOW}
        for k, v in FRESH_PATCH.get(name, {}).items():
            setattr(mod, k, v)
        if name in FRESH_PATCH:
            mod.META["url"] = mod.BASE
        raw = FRESH_RAW / name
        records, suffix = FRESH_RECORDS, f"__{tag}"
    raw.mkdir(parents=True, exist_ok=True)
    if do_fetch:
        mod.fetch(raw)
    df = mod.load(raw)
    for c in ("ts", "y"):
        if c not in df:
            raise ValueError(f"{name}: load() must return column {c!r}")
    df = df.sort_values("ts", kind="stable").reset_index(drop=True)
    df = df[df["y"].isin([0, 1])].reset_index(drop=True)
    n_raw = len(df)
    df, sub = subsample(df)
    n = len(df)
    a, b, c = (int(round(f * n)) for f in np.cumsum(FRACS))  # noqa: RUF046
    feats = list(mod.NUM) + list(mod.CAT)
    X, y = df[feats], df["y"].to_numpy().astype(int)

    m0 = Pipeline(
        [("prep", make_prep(mod.NUM, mod.CAT)), ("lr", LogisticRegression(max_iter=1000, C=1.0))]
    ).fit(X.iloc[:a], y[:a])
    m1 = Pipeline(
        [
            ("prep", make_prep(mod.NUM, mod.CAT)),
            ("hgb", HistGradientBoostingClassifier(random_state=0)),
        ]
    ).fit(X.iloc[a:b], y[a:b])

    # validation gates (recorded)
    p0, p1 = m0.predict(X.iloc[b:c]), m1.predict(X.iloc[b:c])
    yv = y[b:c]
    val = {
        "n": int(c - b),
        "disagreement": float((p0 != p1).mean()),
        "err_incumbent": float((p0 != yv).mean()),
        "err_challenger": float((p1 != yv).mean()),
        "base_rate_y1": float(yv.mean()),
    }
    k = (n - c) // T_EP
    gates = {
        "disagreement": val["disagreement"] >= GATES["min_disagreement"],
        "err_incumbent": GATES["err_low"] < val["err_incumbent"] < GATES["err_high"],
        "err_challenger": GATES["err_low"] < val["err_challenger"] < GATES["err_high"],
        "episodes": k >= MIN_EPISODES,
    }
    rec = {
        "name": name,
        "built_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "meta": mod.META,
        "num": list(mod.NUM),
        "cat": list(mod.CAT),
        "n_after_filter": n_raw,
        "subsample": sub,
        "n": n,
        "split": {"train_old": [0, a], "train_new": [a, b], "validation": [b, c], "test": [c, n]},
        "ts_bounds": {
            "train_old_start": str(df["ts"].iloc[0]),
            "test_start": str(df["ts"].iloc[c]),
            "end": str(df["ts"].iloc[-1]),
        },
        "validation": val,
        "gates": gates,
        "eligible": all(gates.values()),
        "episodes": int(k),
        "sklearn": sklearn.__version__,
        "numpy": np.__version__,
    }

    if rec["eligible"]:
        # sealed test losses: computed and written, never summarised
        Xt, yt = X.iloc[c : c + k * T_EP], y[c : c + k * T_EP]
        l0 = (m0.predict(Xt) != yt).astype(np.int8).reshape(k, T_EP)
        l1 = (m1.predict(Xt) != yt).astype(np.int8).reshape(k, T_EP)
        starts = (c + np.arange(k) * T_EP).astype(np.int64)
        SEALED.mkdir(parents=True, exist_ok=True)
        np.savez(
            SEALED / f"{name}{suffix}.npz",
            l0=l0,
            l1=l1,
            starts=starts,
            delay=np.int64(mod.META["delay"]),
        )
        rec["sealed"] = {
            "path": f"data/c4_sealed/{name}{suffix}.npz",
            "array_content_sha256": array_hash(l0, l1, starts),
        }
        del l0, l1
    records.mkdir(parents=True, exist_ok=True)
    (records / f"{name}.json").write_text(json.dumps(rec, indent=1, default=str) + "\n")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("name")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--window", nargs=2, metavar=("START", "END"))
    ap.add_argument("--tag", default="fresh")
    a = ap.parse_args()
    rec = build(a.name, a.fetch, a.window, a.tag)
    print(
        json.dumps(
            {k: rec[k] for k in ("name", "n", "validation", "gates", "eligible", "episodes")},
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
