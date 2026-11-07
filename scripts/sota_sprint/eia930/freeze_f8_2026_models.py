"""Fit and freeze only the 2021 EIA-930 challenger models for 2026 confirmation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_2026_confirmation_20261107"
DATA_DIR = ROOT / "data/raw/eia930_f8_2026_confirmation_20261107/models"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_all_balancing_authorities import FEATURES, TRAIN_START, load_all, sha256

BA_LIST = ["AZPS", "BANC", "EPE", "ERCO", "FMPP", "FPC", "MISO", "NEVP", "NYIS", "SWPP", "TIDC"]
DEV_START = pd.Timestamp("2022-01-01T00:00:00Z")
IDX_END = pd.Timestamp("2024-01-01T00:00:00Z")


def fit_one(ba: str, series: dict[str, pd.Series]):
    idx = pd.date_range(TRAIN_START, IDX_END - pd.Timedelta(hours=1), freq="h")
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
    if len(train) < 1000 or train.label.nunique() != 2:
        raise RuntimeError(f"insufficient training data for {ba}: n={len(train)}")
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
    return model, cutoff, len(train)


def main() -> None:
    freeze_path = PILOT / "MODEL_FREEZE.json"
    if freeze_path.exists():
        raise SystemExit("model freeze already exists; refusing to overwrite")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = load_all()
    if set(BA_LIST) - set(data):
        raise RuntimeError("one or more registered BAs are missing from 2021-2023 sources")
    models = {}
    for ba in BA_LIST:
        model, cutoff, ntrain = fit_one(ba, data[ba])
        path = DATA_DIR / f"{ba}.joblib"
        joblib.dump(model, path, compress=3)
        models[ba] = {
            "artifact": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "train_events": ntrain,
            "threshold_mw": cutoff,
        }
    src_manifest = json.loads(
        (
            ROOT
            / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
        ).read_text()
    )
    result = {
        "protocol": "eia930_f8_2026_confirmation_20261107/PROTOCOL_V2.md",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "model_code_sha256": sha256(Path(__file__)),
        "feature_code_sha256": sha256(
            Path(__file__).resolve().parent / "profile_all_balancing_authorities.py"
        ),
        "training_source_sha256": src_manifest["raw_file_sha256"],
        "training_year": 2021,
        "validation_period_metrics_not_recomputed": True,
        "sklearn_version": sklearn.__version__,
        "models": models,
    }
    freeze_path.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {"models_frozen": len(models), "period": 2021, "validation_or_test_metrics": False},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
