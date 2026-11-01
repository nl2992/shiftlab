"""Small registered development-only candidate-bank diagnostic, not confirmation."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scripts.exhaustive_evaluation.run_real_development import calendar_features

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def action_loss(probability, outcome):
    return np.where(probability >= 1 / 6, (1 - outcome) / 5, outcome)


def main():
    registration = DOC / "action_headroom_registration.json"
    if registration.exists():
        raise FileExistsError("Inspect existing registration/results before rerunning")
    manifests = json.loads((DOC / "real_data_manifest.json").read_text())
    source = Path(__file__)
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exposed development diagnostic, NOT confirmation",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "selection": "minimum calibration decision loss; fixed listed order breaks ties",
        "bank": [
            "logistic_C1",
            "logistic_C0.01",
            "logistic_C100",
            "hgb_7",
            "hgb_15",
            "positive",
            "negative",
        ],
        "cost": "FN=1 FP=0.2; decision threshold 1/6; no utility tuning",
        "boundary": "development parquet only; train-only fit/threshold; no refit on calibration",
        "primary": "selected challenger development cost relative to original logistic incumbent",
        "secondary": "per-month cost; oracle bank minimum is descriptive only",
        "inputs": {
            m["dataset"]: hashlib.sha256(
                (
                    ROOT
                    / f"outputs/exhaustive_evaluation/real_data/{m['dataset']}_development.parquet"
                ).read_bytes()
            ).hexdigest()
            for m in manifests
        },
    }
    registration.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    rows = []
    for meta in manifests:
        name, split = meta["dataset"], meta["split"]
        df = pd.read_parquet(
            ROOT / f"outputs/exhaustive_evaluation/real_data/{name}_development.parquet"
        )
        clock = pd.to_datetime(df.event_time)
        assert (clock < pd.Timestamp(split["development_end"])).all()
        target = "cnt" if name == "bike" else "pm2.5"
        df = df.loc[df[target].notna()].copy()
        clock = pd.to_datetime(df.event_time)
        train = (clock < pd.Timestamp(split["train_end"])).to_numpy()
        cal = (
            (clock >= pd.Timestamp(split["train_end"]))
            & (clock < pd.Timestamp(split["calibration_end"]))
        ).to_numpy()
        dev = (clock >= pd.Timestamp(split["calibration_end"])).to_numpy()
        assert train.any() and cal.any() and dev.any()
        y = (df[target].to_numpy() >= float(df.loc[train, target].median())).astype(int)
        features = calendar_features(clock)
        probabilities = []
        for c in (1, 0.01, 100):
            model = make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=500))
            model.fit(features[train], y[train])
            probabilities.append(model.predict_proba(features)[:, 1])
        for leaves in (7, 15):
            model = HistGradientBoostingClassifier(
                max_iter=100, max_leaf_nodes=leaves, l2_regularization=1, random_state=17
            )
            model.fit(features[train], y[train])
            probabilities.append(model.predict_proba(features)[:, 1])
        probabilities.extend([np.ones(len(y)), np.zeros(len(y))])
        losses = np.array([action_loss(p, y) for p in probabilities])
        # Exclude incumbent from candidate selection; identical decisions remain valid controls.
        selected = 1 + int(np.argmin(losses[1:, cal].sum(axis=1)))
        for i, tag in enumerate(reg["bank"]):
            row = {
                "dataset": name,
                "model": tag,
                "selected_on_calibration": i == selected,
                "calibration_cost": float(losses[i, cal].sum()),
                "development_cost": float(losses[i, dev].sum()),
                "development_delta_vs_incumbent": float((losses[i, dev] - losses[0, dev]).sum()),
                "development_rows": int(dev.sum()),
                "monthly_delta": {
                    str(month): float(
                        (losses[i] - losses[0])[
                            dev & (clock.dt.to_period("M") == month).to_numpy()
                        ].sum()
                    )
                    for month in clock[dev].dt.to_period("M").unique()
                },
            }
            rows.append(row)
    result = {"status": "completed", "stage": reg["stage"], "rows": rows}
    (DOC / "action_headroom_results.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps([r for r in rows if r["selected_on_calibration"]], indent=2))


if __name__ == "__main__":
    main()
