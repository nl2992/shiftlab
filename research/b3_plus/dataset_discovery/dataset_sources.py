"""Dataset loaders for B3+ screening.

Every loader returns a :class:`RawStream` in *file order* together with whatever genuine
timestamp / ordinal-time columns exist. Ordering decisions are NOT made here (see
``validate_stream.py``); this module only reads files. Downloads go to
``_raw/<dataset_id>/`` (git-ignored). river loaders download on demand into
``$RIVER_DATA``; we point ``RIVER_DATA`` at the per-dataset raw directory so every file is
cached and hashable. OpenML datasets are fetched by numeric id.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "_raw"


@dataclass
class RawStream:
    """A dataset in file order. ``X`` is a DataFrame (numeric/categorical) or a scipy CSR matrix."""

    dataset_id: str
    X: object
    y: np.ndarray  # raw labels (any dtype), file order
    time: np.ndarray | None = None  # genuine timestamp (numeric), file order, else None
    time_name: str | None = None
    ordinal: pd.DataFrame | None = None  # genuine ordinal-time columns (e.g. sessionIndex, rep)
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.y)


def raw_dir(dataset_id: str) -> Path:
    d = RAW / dataset_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


def hash_dir(d: Path) -> dict[str, dict]:
    """sha256 + size of every cached file below ``d`` (relative path -> record)."""
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and not p.name.endswith(".log") and p.name != ".gitignore":
            out[p.relative_to(d).as_posix()] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    return out


# --------------------------------------------------------------------------- river downloads
RIVER_CLASSES = {
    "insects_abrupt_balanced": ("Insects", {"variant": "abrupt_balanced"}),
    "insects_abrupt_imbalanced": ("Insects", {"variant": "abrupt_imbalanced"}),
    "insects_gradual_balanced": ("Insects", {"variant": "gradual_balanced"}),
    "insects_gradual_imbalanced": ("Insects", {"variant": "gradual_imbalanced"}),
    "insects_incremental_balanced": ("Insects", {"variant": "incremental_balanced"}),
    "insects_incremental_abrupt_balanced": ("Insects", {"variant": "incremental_abrupt_balanced"}),
    "insects_incremental_reoccurring_balanced": (
        "Insects",
        {"variant": "incremental_reoccurring_balanced"},
    ),
    "trec07": ("TREC07", {}),
    "keystroke": ("Keystroke", {}),
    "creditcard": ("CreditCard", {}),
    "beth": ("BETH", {}),
    "http": ("HTTP", {}),
    "smtp": ("SMTP", {}),
    "malicious_url": ("MaliciousURL", {}),
    "sms_spam": ("SMSSpam", {}),
    "river_phishing": ("Phishing", {}),
    "river_elec2": ("Elec2", {}),
}


def river_dataset(dataset_id: str):
    from river import datasets

    cls, kw = RIVER_CLASSES[dataset_id]
    os.environ["RIVER_DATA"] = str(raw_dir(dataset_id))
    return getattr(datasets, cls)(**kw)


def river_declared_size(dataset_id: str) -> int | None:
    return getattr(river_dataset(dataset_id), "size", None)


def download_river(dataset_id: str) -> Path:
    ds = river_dataset(dataset_id)
    if hasattr(ds, "download"):
        ds.download(verbose=False)
    return Path(ds.path)


# --------------------------------------------------------------------------- direct https downloads
DIRECT = {
    "uci_occupancy": {
        "url": "https://archive.ics.uci.edu/static/public/357/occupancy+detection.zip",
        "filename": "occupancy_detection.zip",
    },
}


def download_direct(dataset_id: str) -> Path:
    spec = DIRECT[dataset_id]
    dest = raw_dir(dataset_id) / spec["filename"]
    if not dest.exists():
        with urllib.request.urlopen(spec["url"], timeout=120) as r:  # noqa: S310 - fixed https host
            data = r.read()
        if not zipfile.is_zipfile(io.BytesIO(data)):
            raise RuntimeError(f"{spec['url']} did not return a zip archive")
        dest.write_bytes(data)
    return dest


# --------------------------------------------------------------------------- OpenML
def openml_find(name: str) -> list[dict]:
    """Search OpenML by dataset name (active datasets only); returns did, name, version, rows."""
    url = f"https://www.openml.org/api/v1/json/data/list/data_name/{name}/status/active"
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 - fixed https host
        d = json.load(r)
    out = []
    for e in d.get("data", {}).get("dataset", []):
        q = {x["name"]: x["value"] for x in e.get("quality", [])}
        out.append(
            {
                "did": int(e["did"]),
                "name": e["name"],
                "version": int(e["version"]),
                "rows": q.get("NumberOfInstances"),
                "features": q.get("NumberOfFeatures"),
            }
        )
    return out


def download_openml(dataset_id: str, did: int) -> Path:
    from sklearn.datasets import fetch_openml

    d = raw_dir(dataset_id)
    fetch_openml(data_id=did, data_home=str(d), as_frame=True, parser="auto", cache=True)
    return d


def _openml_frame(dataset_id: str, did: int):
    from sklearn.datasets import fetch_openml

    b = fetch_openml(
        data_id=did, data_home=str(raw_dir(dataset_id)), as_frame=True, parser="auto", cache=True
    )
    return b.frame, b.target_names, b


# --------------------------------------------------------------------------- readers
def _read_insects(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    cols = [f"f{i}" for i in range(1, 34)] + ["class"]
    df = pd.read_csv(p, header=None, names=cols)
    y = df.pop("class").to_numpy()
    return RawStream(dataset_id, df, y, meta={"file_order": True})


def _read_trec07(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    df = pd.read_csv(p)
    return _trec_from_frame(dataset_id, df)


def _trec_from_frame(dataset_id: str, df: pd.DataFrame) -> RawStream:
    y = (df["y"].astype(str).str.lower().isin({"1", "spam", "true"})).to_numpy().astype(int)
    t = pd.to_datetime(df["date"], errors="coerce", utc=True)
    text = (
        df["sender"].fillna("").astype(str)
        + " "
        + df["subject"].fillna("").astype(str)
        + " "
        + df["body"].fillna("").astype(str).str.slice(0, 5000)
    )
    tt = (t - pd.Timestamp("1970-01-01", tz="UTC")).dt.total_seconds().to_numpy(dtype=float)
    return RawStream(
        dataset_id,
        text.to_numpy(dtype=object),
        y,
        time=tt,
        time_name="date",
        meta={"kind": "text", "n_unparsed_dates": int(t.isna().sum())},
    )


def _read_keystroke(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    df = pd.read_csv(p)
    ordinal = df[["sessionIndex", "rep"]].copy()
    y = df["subject"].to_numpy()
    X = df.drop(columns=["subject", "sessionIndex", "rep"])
    return RawStream(dataset_id, X, y, ordinal=ordinal, meta={"subject_major_file": True})


def _read_creditcard(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    df = pd.read_csv(p)
    y = df.pop("Class").to_numpy()
    t = df["Time"].to_numpy(dtype=float)
    return RawStream(dataset_id, df, y, time=t, time_name="Time")


def _read_kdd_subset(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    df = pd.read_csv(p)
    ycol = df.columns[-1] if "y" not in df.columns else "y"
    y = df.pop(ycol).to_numpy()
    return RawStream(dataset_id, df, y, meta={"columns": list(df.columns)})


def _read_openml(dataset_id: str, did: int, opts: dict | None = None) -> RawStream:
    opts = opts or {}
    frame, targets, bunch = _openml_frame(dataset_id, did)
    tgt = targets[0]
    y = frame[tgt].to_numpy()
    X = frame.drop(columns=targets).reset_index(drop=True)
    t, meta = None, {"openml_did": did, "target": tgt}
    if opts.get("time_col"):
        t = X[opts["time_col"]].astype(float).to_numpy()
    if opts.get("corroboration_col"):
        meta["time_corroboration"] = X[opts["corroboration_col"]].astype(float).to_numpy()
    X = X.drop(columns=opts.get("drop_cols", []))
    return RawStream(dataset_id, X, y, time=t, time_name=opts.get("time_col"), meta=meta)


def _read_occupancy(dataset_id: str) -> RawStream:
    z = zipfile.ZipFile(raw_dir(dataset_id) / DIRECT[dataset_id]["filename"])
    parts = []
    for name in ("datatraining.txt", "datatest.txt", "datatest2.txt"):  # file order, NOT time order
        d = pd.read_csv(io.BytesIO(z.read(name)), index_col=0)
        d["source_file"] = name
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    t = pd.to_datetime(df["date"])
    tt = (t - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy(dtype=float)
    y = df["Occupancy"].to_numpy()
    X = df.drop(columns=["date", "Occupancy", "source_file"])
    return RawStream(dataset_id, X, y, time=tt, time_name="date",
                     meta={"files_concatenated_in_this_order": ["datatraining", "datatest", "datatest2"]})


def _read_sms(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    df = pd.read_csv(p, sep="\t", header=None, names=["y", "text"], quoting=3)
    return RawStream(dataset_id, df["text"].to_numpy(dtype=object), df["y"].to_numpy(),
                     meta={"kind": "text"})


def _read_phishing(dataset_id: str) -> RawStream:
    p = Path(river_dataset(dataset_id).path)
    df = pd.read_csv(p)
    y = df.pop("is_phishing").to_numpy()
    return RawStream(dataset_id, df, y)


READERS = {
    "trec07": _read_trec07,
    "keystroke": _read_keystroke,
    "creditcard": _read_creditcard,
    "http": _read_kdd_subset,
    "smtp": _read_kdd_subset,
    "sms_spam": _read_sms,
    "uci_occupancy": _read_occupancy,
    "river_phishing": _read_phishing,
}
for _k in RIVER_CLASSES:
    if _k.startswith("insects_"):
        READERS[_k] = _read_insects


def load(dataset_id: str, openml_did: int | None = None, opts: dict | None = None) -> RawStream:
    """Load a cached dataset (call ``download_datasets`` first)."""
    if openml_did is not None:
        return _read_openml(dataset_id, openml_did, opts)
    if dataset_id in READERS:
        return READERS[dataset_id](dataset_id)
    raise KeyError(f"no loader registered for {dataset_id}")
