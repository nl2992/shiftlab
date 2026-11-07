"""Frozen profile-only F8 screen over all BAs in EIA bulk files (2021--2023)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data/raw/eia930_f8_development_20261107"
SOURCE = ROOT / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_all_ba_development_20261107"
TRAIN_START = pd.Timestamp("2021-01-01T00:00:00Z")
DEV_START = pd.Timestamp("2022-01-01T00:00:00Z")
DEV_END = pd.Timestamp("2024-01-01T00:00:00Z")
FEATURES = [
    "forecast",
    "lag1",
    "lag24",
    "lag168",
    "lag336",
    "mean24",
    "max24",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "year_sin",
    "year_cos",
]
USECOLS = [
    "Balancing Authority",
    "UTC Time at End of Hour",
    "Demand Forecast (MW)",
    "Demand (MW)",
    "Demand (MW) (Imputed)",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_all() -> dict[str, dict[str, pd.Series]]:
    manifest = json.loads(SOURCE.read_text())
    by_ba: dict[str, dict[str, list[pd.DataFrame]]] = {}
    for relative, expected in manifest["raw_file_sha256"].items():
        path = ROOT / relative
        if sha256(path) != expected:
            raise RuntimeError(f"source checksum mismatch: {relative}")
        for chunk in pd.read_csv(path, usecols=USECOLS, dtype=str, chunksize=100_000):
            chunk["period"] = pd.to_datetime(
                chunk["UTC Time at End of Hour"],
                format="%m/%d/%Y %I:%M:%S %p",
                utc=True,
                errors="coerce",
            )
            chunk["actual"] = pd.to_numeric(chunk["Demand (MW)"], errors="coerce")
            chunk["forecast"] = pd.to_numeric(chunk["Demand Forecast (MW)"], errors="coerce")
            chunk["imputed"] = pd.to_numeric(chunk["Demand (MW) (Imputed)"], errors="coerce")
            for ba, group in chunk.dropna(subset=["period"]).groupby("Balancing Authority"):
                slot = by_ba.setdefault(str(ba), {key: [] for key in ("D", "DF", "imputed")})
                for key, col in (("D", "actual"), ("DF", "forecast"), ("imputed", "imputed")):
                    slot[key].append(group[["period", col]].rename(columns={col: key}))
    out = {}
    for ba, fields in by_ba.items():
        out[ba] = {}
        for key, frames in fields.items():
            frame = pd.concat(frames, ignore_index=True).drop_duplicates("period", keep="last")
            out[ba][key] = frame.set_index("period")[key].sort_index()
    return out


def complete_blocks(index: pd.DatetimeIndex, width: int = 2000) -> tuple[int, int]:
    if len(index) == 0:
        return 0, 0
    breaks = index.to_series().diff().ne(pd.Timedelta(hours=1)).cumsum().to_numpy()
    sizes = [int(np.sum(breaks == group)) for group in np.unique(breaks)]
    return sum(n // width for n in sizes), len(sizes)


def profile_ba(ba: str, series: dict[str, pd.Series]) -> dict:
    idx = pd.date_range(TRAIN_START, DEV_END - pd.Timedelta(hours=1), freq="h")
    frame = pd.DataFrame(index=idx)
    frame["actual"] = series["D"].reindex(idx)
    frame["forecast"] = series["DF"].reindex(idx)
    frame["imputed"] = series["imputed"].reindex(idx)
    for lag in (1, 24, 168, 336):
        frame[f"lag{lag}"] = frame.actual.shift(lag)
    prior = frame.actual.shift(1).rolling(24, min_periods=24)
    frame["mean24"], frame["max24"] = prior.mean(), prior.max()
    h, wd, doy = idx.hour.to_numpy(), idx.dayofweek.to_numpy(), idx.dayofyear.to_numpy()
    frame["hour_sin"], frame["hour_cos"] = np.sin(2 * np.pi * h / 24), np.cos(2 * np.pi * h / 24)
    frame["weekday_sin"], frame["weekday_cos"] = (
        np.sin(2 * np.pi * wd / 7),
        np.cos(2 * np.pi * wd / 7),
    )
    frame["year_sin"], frame["year_cos"] = (
        np.sin(2 * np.pi * doy / 365.25),
        np.cos(2 * np.pi * doy / 365.25),
    )
    train_time = (frame.index >= TRAIN_START) & (frame.index < DEV_START)
    cutoff = float(frame.loc[train_time, "actual"].dropna().quantile(0.90))
    frame["label"] = (frame.actual >= cutoff).astype(float)
    eligible = frame[FEATURES + ["actual", "lag24", "label"]].notna().all(axis=1)
    eligible &= frame.imputed.isna()
    eligible &= (frame.actual > 0) & (frame.forecast > 0) & (frame.lag24 > 0)
    train = frame.loc[eligible & train_time]
    dev = frame.loc[eligible & (frame.index >= DEV_START) & (frame.index < DEV_END)]
    if len(train) < 1000 or len(dev) < 2000 or train.label.nunique() < 2:
        return {
            "eligible_train_events": len(train),
            "eligible_dev_events": len(dev),
            "excluded": True,
        }
    model = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.05,
        max_leaf_nodes=15,
        l2_regularization=1.0,
        random_state=1729,
    )
    model.fit(
        train[FEATURES],
        train.label.astype(int),
        sample_weight=compute_sample_weight("balanced", train.label.astype(int)),
    )
    actual_label = (dev.actual.to_numpy() >= cutoff).astype(np.int8)
    incumbent = (dev.lag24.to_numpy() >= cutoff).astype(np.int8)
    challenger = (model.predict_proba(dev[FEATURES])[:, 1] >= 0.5).astype(np.int8)
    disagree = incumbent != challenger
    frequency = float(disagree.mean())
    accuracy = (
        float((challenger[disagree] == actual_label[disagree]).mean()) if disagree.any() else None
    )
    blocks, runs = complete_blocks(pd.DatetimeIndex(dev.index))
    matches = 0.01 <= frequency <= 0.05 and accuracy is not None and accuracy >= 0.85
    return {
        "eligible_train_events": len(train),
        "eligible_dev_events": len(dev),
        "disagreement_frequency": frequency,
        "challenger_correct_on_disagreements": accuracy,
        "complete_contiguous_2000_hour_blocks": blocks,
        "contiguous_runs": runs,
        "train_2021_p90_cutoff_mw": cutoff,
        "f8_profile_match": matches,
        "excluded": False,
    }


def main() -> None:
    output = PILOT / "DATASET_PROFILE.json"
    if output.exists():
        raise SystemExit("profile exists; refusing to overwrite development outcome")
    data = load_all()
    profiles = {ba: profile_ba(ba, data[ba]) for ba in sorted(data)}
    matching = [ba for ba, row in profiles.items() if row.get("f8_profile_match")]
    result = {
        "protocol": "eia930_f8_all_ba_development_20261107/PROTOCOL.md",
        "window": "fit=2021; development=2022-2023 UTC",
        "registered_ba_count": len(data),
        "profiles": profiles,
        "matching_bas": matching,
        "matching_ba_count": len(matching),
        "gate_pass": len(matching) >= 5,
        "interpretation": "Profile only; no algorithm or cost outcomes generated.",
    }
    PILOT.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "profiles"}, indent=2))
    print(
        json.dumps(
            {ba: row for ba, row in profiles.items() if row.get("f8_profile_match")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
