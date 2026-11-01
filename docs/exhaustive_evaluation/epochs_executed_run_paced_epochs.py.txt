"""Registered 504-composition development screen of pacing and fresh evidence."""

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from shiftlab.sota_search.paced_epochs import epoch_configurations, epoch_screen
from shiftlab.sota_search.paired_control import PairedConfig, paired_screen, paired_world
from shiftlab.sota_search.paired_cusum import paired_cusum

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    regpath = DOC / "paced_epochs_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing process/status before restarting")
    configs = epoch_configurations()
    assert len(configs) == 504
    sources = [
        "src/shiftlab/sota_search/paced_epochs.py",
        "src/shiftlab/sota_search/paired_control.py",
        "src/shiftlab/sota_search/paired_cusum.py",
        "src/shiftlab/sota_search/paired_references.py",
        "src/shiftlab/sota_search/combination_screen.py",
        "scripts/exhaustive_evaluation/run_paced_epochs.py",
    ]
    thresholds = json.loads((DOC / "cusum_strict_thresholds.json").read_text())["thresholds"][2:]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "development composition screen, NOT novelty or confirmation",
        "configurations": [asdict(c) for c in configs],
        "effective_count": 504,
        "excluded_aliases": "36 one-epoch quota settings equal remaining-budget pacing",
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
        "paths": 64,
        "horizon": 2000,
        "world_seed": 202662000,
        "query_seed": 202663000,
        "contract": "budget400 frac.2 delay5 margin.01 alpha.05 query.001 switch1; same economic eligibility; one promotion",
        "epochs": "deterministic equal-length tests; alpha/J each; discard pending labels from prior epoch evidence, charge all requests; gamma affects only bet learning",
        "primary": "all-case macro excess cost, with null promotion-rate diagnostics; rank only development, independently confirm any finalist",
        "practical_gate": "10 percent lower persistent cost than strongest eligible tuned comparator; no safety degradation; not inferred from64 paths",
        "references": ["Kelly", "tuned_FTL", "CUSUM_.05", "CUSUM_.1"],
        "cusum_thresholds": thresholds,
        "sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    statuspath = DOC / "paced_epochs_status.json"
    status = {"status": "running", "completed": []}
    statuspath.write_text(json.dumps(status), encoding="utf-8")
    out = ROOT / "outputs/exhaustive_evaluation/paced_epochs"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    parents = [
        PairedConfig("direct", "uniform", 0.98, 0.75, r, "none", b)
        for r, b in [(False, "kelly"), (True, "ftl")]
    ]
    for j, kind in enumerate(reg["cases"]):
        s = paired_world(kind, paths=64, horizon=2000, seed=reg["world_seed"] + j)
        kw = {"seed": reg["query_seed"] + j}
        result = epoch_screen(s, configs, **kw)
        refs = [paired_screen(s, parents, **kw), paired_cusum(s, [0.05, 0.1], thresholds, **kw)]
        merged = {
            k: np.concatenate([result[k]] + [r[k] for r in refs], axis=0)
            for k in ["first", "labels", "total_cost", "delta_vs_incumbent"]
        }
        assert np.all(merged["labels"] <= 400)
        np.savez_compressed(out / f"{kind}.npz", **merged)
        for i, name in enumerate([f"EP_{i:04d}" for i in range(504)] + reg["references"]):
            rows.append(
                {
                    "case": kind,
                    "id": name,
                    "promotion_rate": float((merged["first"][i] < 2000).mean()),
                    "labels": float(merged["labels"][i].mean()),
                    "total_cost": float(merged["total_cost"][i].mean()),
                    "delta_vs_incumbent": float(merged["delta_vs_incumbent"][i].mean()),
                }
            )
        status["completed"].append(kind)
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        print(kind, "504 configurations complete", flush=True)
    (DOC / "paced_epochs_results.json").write_text(
        json.dumps({"rows": rows}, indent=2), encoding="utf-8"
    )
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    main()
