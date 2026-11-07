"""Frozen 2021-fit EIA-930 model-pair profile screen (no policy outcomes)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_ml_challenger_20261107"
SOURCE_PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_development_20261107"
sys.path.insert(0, str(ROOT / "scripts/sota_sprint/eia930"))
from run_f8_development import BAS, retrieve

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


def contiguous_chunks(mask: pd.Series, hours_per_chunk: int = 2000) -> tuple[int, int]:
    selected = mask[mask].index.sort_values()
    if selected.empty:
        return 0, 0
    gaps = selected.to_series().diff().ne(pd.Timedelta(hours=1))
    group_ids = gaps.cumsum().to_numpy()
    chunks = episodes = 0
    for group_id in np.unique(group_ids):
        n = int((group_ids == group_id).sum())
        episodes += 1
        chunks += n // hours_per_chunk
    return chunks, episodes


def main() -> None:
    if (PILOT / "DATASET_PROFILE.json").exists():
        raise SystemExit("profile exists; refusing to overwrite frozen development outcome")
    data = retrieve()
    profile = {}
    for ba in BAS:
        actual, forecast, imputed = data[ba]["D"], data[ba]["DF"], data[ba]["imputed"]
        idx = pd.date_range(TRAIN_START, DEV_END - pd.Timedelta(hours=1), freq="h")
        frame = pd.DataFrame(index=idx)
        frame["actual"] = actual.reindex(idx)
        frame["forecast"] = forecast.reindex(idx)
        frame["imputed"] = imputed.reindex(idx)
        for lag in (1, 24, 168, 336):
            frame[f"lag{lag}"] = frame.actual.shift(lag)
        prior = frame.actual.shift(1).rolling(24, min_periods=24)
        frame["mean24"] = prior.mean()
        frame["max24"] = prior.max()
        hours = idx.hour.to_numpy()
        weekdays = idx.dayofweek.to_numpy()
        years = idx.dayofyear.to_numpy()
        frame["hour_sin"], frame["hour_cos"] = (
            np.sin(2 * np.pi * hours / 24),
            np.cos(2 * np.pi * hours / 24),
        )
        frame["weekday_sin"], frame["weekday_cos"] = (
            np.sin(2 * np.pi * weekdays / 7),
            np.cos(2 * np.pi * weekdays / 7),
        )
        frame["year_sin"], frame["year_cos"] = (
            np.sin(2 * np.pi * years / 365.25),
            np.cos(2 * np.pi * years / 365.25),
        )
        train_year = (frame.index >= TRAIN_START) & (frame.index < DEV_START)
        cutoff = float(frame.loc[train_year, "actual"].dropna().quantile(0.90))
        frame["label"] = (frame.actual >= cutoff).astype("float")
        eligible = frame[FEATURES + ["actual", "forecast", "lag24", "label"]].notna().all(axis=1)
        eligible &= frame["imputed"].isna()
        for col in ("actual", "forecast", "lag24"):
            eligible &= frame[col] > 0
        train = frame.loc[eligible & train_year]
        dev = frame.loc[eligible & (frame.index >= DEV_START) & (frame.index < DEV_END)]
        if train.empty or dev.empty or train.label.nunique() < 2:
            raise RuntimeError(f"insufficient eligible train/dev rows for {ba}")
        model = HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            random_state=1729,
        )
        weights = compute_sample_weight("balanced", train.label.astype(int))
        model.fit(train[FEATURES], train.label.astype(int), sample_weight=weights)
        threshold_label = (dev.actual.to_numpy() >= cutoff).astype(np.int8)
        incumbent = (dev.lag24.to_numpy() >= cutoff).astype(np.int8)
        challenger = (model.predict_proba(dev[FEATURES])[:, 1] >= 0.5).astype(np.int8)
        disagree = incumbent != challenger
        freq = float(disagree.mean())
        conditional = (
            float((challenger[disagree] == threshold_label[disagree]).mean())
            if disagree.any()
            else None
        )
        eligible_mask = pd.Series(True, index=dev.index)
        complete_episodes, contiguous_runs = contiguous_chunks(eligible_mask)
        profile[ba] = {
            "eligible_events": len(dev),
            "disagreement_frequency": freq,
            "challenger_correct_on_disagreements": conditional,
            "complete_2000_hour_episodes": complete_episodes,
            "contiguous_runs": contiguous_runs,
            "cutoff_mw_train_2021_p90": cutoff,
            "train_events": len(train),
        }
    matches = [
        ba
        for ba, row in profile.items()
        if 0.01 <= row["disagreement_frequency"] <= 0.05
        and row["challenger_correct_on_disagreements"] is not None
        and row["challenger_correct_on_disagreements"] >= 0.85
    ]
    result = {
        "protocol": "eia930_f8_ml_challenger_20261107/PROTOCOL.md",
        "training_window": "2021-01-01/2022-01-01 UTC",
        "development_window": "2022-01-01/2024-01-01 UTC",
        "profiles": profile,
        "matching_bas": matches,
        "gate_pass": len(matches) >= 2,
        "interpretation": "Profile only; no policy outcomes, method costs, or confirmation data generated.",
    }
    (PILOT / "DATASET_PROFILE.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
