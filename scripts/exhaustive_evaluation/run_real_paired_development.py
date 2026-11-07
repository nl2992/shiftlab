"""Evaluate paired controls on exposed development periods, same frozen models.

Rebuilding predictors must exactly reproduce the prior recorded model costs.
No new model selection or reserved data. These periods are already exposed.
"""

import argparse
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
from shiftlab.sota_search.paired_control import paired_configurations, paired_screen
from shiftlab.sota_search.paired_references import paired_fixed_mixture, paired_paper_reference

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/real_paired_development"
REG = DOC / "real_paired_registration.json"
STATUS = DOC / "real_paired_status.json"
SOURCES = [
    "scripts/exhaustive_evaluation/run_real_paired_development.py",
    "src/shiftlab/sota_search/paired_control.py",
    "src/shiftlab/sota_search/paired_references.py",
    "src/shiftlab/sota_search/published_baselines.py",
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_stream(meta, *, paths):
    name = meta["dataset"]
    split = meta["split"]
    df = pd.read_parquet(
        ROOT / f"outputs/exhaustive_evaluation/real_data/{name}_development.parquet"
    )
    target = "cnt" if name == "bike" else "pm2.5"
    assert (pd.to_datetime(df.event_time) < pd.Timestamp(split["development_end"])).all()
    df = df.loc[df[target].notna()].copy()
    clock = pd.to_datetime(df.event_time)
    train = clock < pd.Timestamp(split["train_end"])
    (clock >= pd.Timestamp(split["train_end"])) & (clock < pd.Timestamp(split["calibration_end"]))
    dev = clock >= pd.Timestamp(split["calibration_end"])
    threshold = float(df.loc[train, target].median())
    y = (df[target].to_numpy() >= threshold).astype(int)
    X = calendar_features(clock)
    models = [
        make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=500)),
        HistGradientBoostingClassifier(
            max_iter=100, max_leaf_nodes=15, l2_regularization=1, random_state=17
        ),
    ]
    for model in models:
        model.fit(X[train], y[train])
    p, p1 = [model.predict_proba(X)[:, 1] for model in models]
    l0 = np.where(p >= 1 / 6, (1 - y) / 5, y)
    l1 = np.where(p1 >= 1 / 6, (1 - y) / 5, y)
    old = (
        pd.read_csv(ROOT / "outputs/exhaustive_evaluation/real_development/model_summary.csv")
        .set_index("dataset")
        .loc[name]
    )
    np.testing.assert_allclose(
        [l0[dev].sum(), l1[dev].sum(), threshold],
        [old.incumbent_cost, old.challenger_cost, old.threshold],
        rtol=0,
        atol=1e-10,
    )
    T = int(dev.sum())

    def rep(v):
        return np.broadcast_to(v, (paths, T)).copy()

    s = {
        "loss": rep(l0[dev]),
        "candidate_loss": rep(l1[dev]),
        "score": rep(p[dev]),
        "candidate_score": rep(p1[dev]),
        "disagree": rep((p[dev] >= 1 / 6) != (p1[dev] >= 1 / 6)),
        "proxy": rep(np.where(p[dev] >= 1 / 6, (1 - p[dev]) / 5, p[dev])),
        "proxy_max": 1 / 6,
        "r0": float(old.nominal_upper),
    }
    return s, {
        "dataset": name,
        "incumbent_cost": float(old.incumbent_cost),
        "challenger_cost": float(old.challenger_cost),
        "horizon": T,
        "frozen_model_costs_reproduced": True,
        "data_sha256": sha(
            ROOT / f"outputs/exhaustive_evaluation/real_data/{name}_development.parquet"
        ),
    }


def register():
    if REG.exists():
        raise FileExistsError("registration exists")
    value = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exposed development replay, NOT confirmation",
        "datasets": json.loads((DOC / "real_data_manifest.json").read_text()),
        "config_count": 648,
        "paths": 16,
        "query_seed_base": 202616000,
        "frac": 0.2,
        "delay": 5,
        "alpha": 0.05,
        "margin": 0.01,
        "query_cost": 0.001,
        "switch_cost": 1,
        "primary": "total realized cost versus incumbent; harmful challenger rejection and query overhead",
        "models": "identical to prior registered real pilot; enforce exact cost/threshold parity",
        "safety": "no iid/conditional-null validity is inferred from serial real data",
        "exclusion": "reserved calibration/final files are not read",
        "sources_sha256": {p: sha(ROOT / p) for p in SOURCES},
    }
    REG.write_text(json.dumps(value, indent=2), encoding="utf-8")
    for p in SOURCES:
        (DOC / ("real_paired_executed_" + Path(p).name + ".txt")).write_bytes(
            (ROOT / p).read_bytes()
        )
    print("Registered exposed real development replay for 648 paired controls", flush=True)


def run():
    reg = json.loads(REG.read_text())
    assert all(sha(ROOT / p) == v for p, v in reg["sources_sha256"].items())
    if STATUS.exists():
        raise FileExistsError("inspect existing live/terminal run before restarting")
    OUT.mkdir(parents=True, exist_ok=True)
    status = {"status": "running", "registration_sha256": sha(REG), "completed": []}
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    rows = []
    modelrecords = []
    for j, meta in enumerate(reg["datasets"]):
        name = meta["dataset"]
        s, model = build_stream(meta, paths=reg["paths"])
        modelrecords.append(model)
        S, T = s["loss"].shape
        kw = {
            "frac": reg["frac"],
            "budget": int(reg["frac"] * T),
            "delay": reg["delay"],
            "seed": reg["query_seed_base"] + j,
            "alpha": reg["alpha"],
            "margin": reg["margin"],
            "query_cost": reg["query_cost"],
            "switch_cost": reg["switch_cost"],
        }
        result = paired_screen(s, paired_configurations(), **kw)
        np.savez_compressed(OUT / (name + "_grid.npz"), **result)
        entries = [(f"R3_{i:04d}", {k: v[i] for k, v in result.items()}) for i in range(648)]
        for tag, value in [
            ("existing_fixed_mixture_IPW", paired_fixed_mixture(s, **kw)),
            ("paired_PR_PM_EB", paired_paper_reference(s, method="pr", **kw)),
            ("paired_RCPS_FTL", paired_paper_reference(s, method="rcps", **kw)),
        ]:
            entries.append((tag, value))
            np.savez_compressed(OUT / (name + "_" + tag + ".npz"), **value)
        for tag, value in entries:
            for path in range(S):
                rows.append(
                    {
                        "dataset": name,
                        "id": tag,
                        "path": path,
                        "horizon": T,
                        "promoted": bool(value["first"][path] < T),
                        "promotion_time": int(value["first"][path]),
                        "labels": int(value["labels"][path]),
                        "decision_cost": float(value["decision_cost"][path]),
                        "total_cost": float(value["total_cost"][path]),
                        "delta_vs_incumbent": float(value["delta_vs_incumbent"][path]),
                    }
                )
        pd.DataFrame(rows).to_csv(OUT / "per_path_metrics.csv", index=False)
        pd.DataFrame(modelrecords).to_csv(OUT / "frozen_model_parity.csv", index=False)
        status["completed"].append(name)
        STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(
            name,
            "all paired controls and references completed; frozen model costs match",
            flush=True,
        )
    summary = (
        pd.DataFrame(rows)
        .groupby(["dataset", "id"], as_index=False)[
            ["promoted", "labels", "total_cost", "delta_vs_incumbent"]
        ]
        .mean()
    )
    summary.to_csv(OUT / "summary.csv", index=False)
    status.update(
        status="completed",
        finished_utc=datetime.now(UTC).isoformat(),
        summary_sha256=sha(OUT / "summary.csv"),
    )
    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["register", "run"])
    args = p.parse_args()
    register() if args.action == "register" else run()
