"""Exploratory known-zero/disagreement query deletion on exposed real periods."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.exhaustive_evaluation.run_real_paired_development import build_stream
from shiftlab.sota_search.paired_control import PairedConfig, paired_screen

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
OUT = ROOT / "outputs/exhaustive_evaluation/known_zero_baseline"


def main():
    registration = DOC / "known_zero_baseline_registration.json"
    resultfile = DOC / "known_zero_baseline_results.json"
    if registration.exists():
        raise FileExistsError("retain existing exploratory check")
    selection = json.loads((DOC / "tuned_ftl_confirmation_registration.json").read_text())[
        "configs"
    ]
    configs = [PairedConfig(**{k: v for k, v in c.items() if k != "id"}) for c in selection]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "exposed real development; not confirmation",
        "reason": "do not pay to label a known-zero paired loss when frozen actions agree",
        "candidates": selection,
        "variants": ["original", "skip_known_zero"],
        "paths": 16,
        "seed_base": 202624000,
        "kwargs": {
            "frac": 0.2,
            "delay": 5,
            "alpha": 0.05,
            "margin": 0.01,
            "query_cost": 0.001,
            "switch_cost": 1,
        },
        "guard": "only direct paired control; do not remove labels needed for an absolute-risk alarm",
        "theory": "common-outcome equal actions imply equal cost; no outcome needed for zero gain; no new novelty claim",
        "sources": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in [
                "scripts/exhaustive_evaluation/check_known_zero_baseline.py",
                "scripts/exhaustive_evaluation/run_real_paired_development.py",
                "src/shiftlab/sota_search/paired_control.py",
            ]
        },
    }
    registration.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for j, meta in enumerate(json.loads((DOC / "real_data_manifest.json").read_text())):
        s, parity = build_stream(meta, paths=reg["paths"])
        name = meta["dataset"]
        _S, T = s["loss"].shape
        for skip in (False, True):
            value = paired_screen(
                s,
                configs,
                budget=int(0.2 * T),
                seed=reg["seed_base"] + j,
                skip_known_zero=skip,
                **reg["kwargs"],
            )
            np.savez_compressed(OUT / f"{name}_skip{int(skip)}.npz", **value)
            for i, c in enumerate(selection):
                rows.append(
                    {
                        "dataset": name,
                        "id": c["id"],
                        "skip_known_zero": skip,
                        "labels": float(value["labels"][i].mean()),
                        "promotion_rate": float(np.mean(value["first"][i] < T)),
                        "delta_vs_incumbent": float(value["delta_vs_incumbent"][i].mean()),
                        "total_cost": float(value["total_cost"][i].mean()),
                        "frozen_models_reproduced": parity["frozen_model_costs_reproduced"],
                    }
                )
        print(name, "original and known-zero controls evaluated", flush=True)
    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    resultfile.write_text(
        json.dumps({"status": "completed", "rows": rows}, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
