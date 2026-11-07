"""Registered e-detector threshold-contract development comparison."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from shiftlab.sota_search.paired_control import PairedConfig, paired_screen, paired_world
from shiftlab.sota_search.paired_cusum import paired_cusum
from shiftlab.sota_search.paired_edetectors import paired_edetectors

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    regpath = DOC / "paired_edetectors_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing process/status before restart")
    sources = [
        "src/shiftlab/sota_search/paired_edetectors.py",
        "src/shiftlab/sota_search/paired_control.py",
        "src/shiftlab/sota_search/paired_references.py",
        "src/shiftlab/sota_search/paired_cusum.py",
        "src/shiftlab/sota_search/combination_screen.py",
        "scripts/exhaustive_evaluation/run_paired_edetectors.py",
    ]
    threshold = json.loads((DOC / "cusum_strict_thresholds.json").read_text())["thresholds"][2:]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "development operational threshold comparison, not new method or author-scale reproduction",
        "cases": [
            "harmful",
            "tie",
            "harmful_after_shift",
            "useful_initial",
            "useful",
            "late",
            "small",
            "reversal",
        ],
        "paths": 256,
        "horizon": 2000,
        "world_seed": 202666000,
        "query_seed": 202667000,
        "contract": "uniform frac.2 hard cap400 delay5 alpha.05 margin.01 query.001 switch1",
        "methods": "SR/CUSUM fixed stakes.2/.5/.8 and equal mixture; horizon H/alpha versus explicitly nonmatched ARL1/alpha",
        "primary": "horizon-safe operational net cost vs tuned FTL/CUSUM; all stake settings reported; ARL arms diagnostic only",
        "skip": "unreleased events use factor1 and open starts; pending requests charged; no inherited real-data guarantee",
        "cusum_thresholds": threshold,
        "sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    out = ROOT / "outputs/exhaustive_evaluation/paired_edetectors"
    out.mkdir(parents=True, exist_ok=True)
    statuspath = DOC / "paired_edetectors_status.json"
    status = {"status": "running", "completed": []}
    statuspath.write_text(json.dumps(status), encoding="utf-8")
    rows = []
    configs = [
        PairedConfig("direct", "uniform", 0.98, 0.75, r, "none", b)
        for r, b in [(False, "kelly"), (True, "ftl")]
    ]
    for j, kind in enumerate(reg["cases"]):
        s = paired_world(kind, paths=256, horizon=2000, seed=reg["world_seed"] + j)
        kw = {"seed": reg["query_seed"] + j}
        value = paired_edetectors(s, **kw)
        refs = [paired_screen(s, configs, **kw), paired_cusum(s, [0.05, 0.1], threshold, **kw)]
        merged = {
            k: np.concatenate([value[k]] + [r[k] for r in refs], axis=0)
            for k in ["first", "labels", "total_cost", "delta_vs_incumbent"]
        }
        assert np.all(merged["labels"] <= 400)
        np.savez_compressed(out / f"{kind}.npz", **merged)
        for i, name in enumerate(value["names"] + ["Kelly", "tuned_FTL", "CUSUM_.05", "CUSUM_.1"]):
            rows.append(
                {
                    "case": kind,
                    "method": name,
                    "promotion_rate": float((merged["first"][i] < 2000).mean()),
                    "total_cost": float(merged["total_cost"][i].mean()),
                    "delta_vs_incumbent": float(merged["delta_vs_incumbent"][i].mean()),
                    "labels": float(merged["labels"][i].mean()),
                }
            )
        status["completed"].append(kind)
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        print(kind, "complete", flush=True)
    (DOC / "paired_edetectors_results.json").write_text(
        json.dumps({"rows": rows}, indent=2), encoding="utf-8"
    )
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    main()
