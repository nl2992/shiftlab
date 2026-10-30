"""Registered development comparison of learned-query fixed-question adaptations."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from shiftlab.sota_search.learned_paired_rcps import learned_paired_rcps
from shiftlab.sota_search.paired_control import PairedConfig, paired_screen, paired_world
from shiftlab.sota_search.paired_cusum import paired_cusum

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main(profile="original"):
    if profile not in ("original", "range"):
        raise ValueError("unknown registered profile")
    ranged = profile == "range"
    prefix = "learned_rcps_range" if ranged else "learned_rcps_development"
    regpath = DOC / f"{prefix}_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing native process/status before rerun")
    variants = [
        {"id": f"{target}_{norm}", "variance_target": target, "normalization": norm, "floor": 0.05}
        for target in ["source", "residual"]
        for norm in ["source", "paper"]
    ]
    variants += [
        {
            "id": f"uniform_floor{floor}",
            "variance_target": "source",
            "normalization": "uniform",
            "floor": floor,
        }
        for floor in [0.05, 0.2]
    ]
    if ranged:
        base = variants
        variants = [
            {**v, "id": v["id"] + "_" + mode, "cap_mode": mode}
            for v in base[:4]
            for mode in ["global", "query", "predictor"]
        ]
        # Uniform query-bound modes alias the tight-floor control; avoid counting copies.
        variants += [
            {**base[4], "cap_mode": "global"},
            {**base[5], "cap_mode": "global"},
            {**base[5], "id": "uniform_predictor", "cap_mode": "predictor"},
        ]
    thresholds = json.loads((DOC / "cusum_strict_thresholds.json").read_text())["thresholds"]
    sources = [
        "src/shiftlab/sota_search/active_rcps_learning.py",
        "src/shiftlab/sota_search/learned_paired_rcps.py",
        "src/shiftlab/sota_search/paired_control.py",
        "src/shiftlab/sota_search/paired_cusum.py",
        "src/shiftlab/sota_search/paired_references.py",
        "src/shiftlab/sota_search/combination_screen.py",
        "scripts/exhaustive_evaluation/compare_learned_rcps.py",
    ]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "development baseline diagnostic, NOT confirmation or novel mechanism",
        "variants": variants,
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
        "paths_per_case": 128 if ranged else 256,
        "batch": 128,
        "horizon": 2000,
        "world_seed": 202658000 if ranged else 202654000,
        "query_seed": 202659000 if ranged else 202655000,
        "contract": "frac.2 cap400 delay5 alpha.05 margin.01 query.001 switch1; common query uniforms; models frozen",
        "paper_variant": "paper-payoff minimization with native dual cap and explicit normalization-parameter projection[-20,20]; residual target is saved issue-time residual squared",
        "adaptation": "fixed beta=.5; explicit cap modes; fresh released-history range computed before current covariates; source component parity, not full native-loop timing/grid or expected-budget claim",
        "primary": "all registered variants equal-weight persistent case net cost versus tuned FTL; no test-selected winner",
        "references": ["paired_Kelly", "tuned_FTL", "CUSUM_slack.05", "CUSUM_slack.1"],
        "cusum_thresholds": thresholds[2:],
        "cusum_threshold_source_sha256": hashlib.sha256(
            (DOC / "cusum_strict_thresholds.json").read_bytes()
        ).hexdigest(),
        "sources_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
    }
    regpath.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    statuspath = DOC / f"{prefix}_status.json"
    status = {"status": "running", "completed": []}
    statuspath.write_text(json.dumps(status), encoding="utf-8")
    out = ROOT / f"outputs/exhaustive_evaluation/{prefix}"
    out.mkdir(parents=True, exist_ok=True)
    configs = [
        PairedConfig("direct", "uniform", 0.98, 0.75, restart, "none", bet)
        for restart, bet in [(False, "kelly"), (True, "ftl")]
    ]
    rows = []
    for j, kind in enumerate(reg["cases"]):
        batches = []
        for b in range(reg["paths_per_case"] // reg["batch"]):
            offset = j * 100 + b
            stream = paired_world(kind, paths=128, horizon=2000, seed=reg["world_seed"] + offset)
            kw = {"seed": reg["query_seed"] + offset}
            entries = [
                learned_paired_rcps(stream, **{k: v for k, v in variant.items() if k != "id"}, **kw)
                for variant in variants
            ]
            betting = paired_screen(stream, configs, **kw)
            classical = paired_cusum(stream, [0.05, 0.1], reg["cusum_thresholds"], **kw)
            for value in [betting, classical]:
                entries.extend(
                    [
                        {
                            k: v[i]
                            for k, v in value.items()
                            if k in ["first", "labels", "total_cost", "delta_vs_incumbent"]
                        }
                        for i in range(2)
                    ]
                )
            result = {
                k: np.stack([e[k] for e in entries])
                for k in ["first", "labels", "total_cost", "delta_vs_incumbent"]
            }
            assert np.all(result["labels"] <= 400)
            np.savez_compressed(out / f"{kind}_{b:03d}.npz", **result)
            batches.append(result)
        merged = {k: np.concatenate([v[k] for v in batches], axis=1) for k in batches[0]}
        for i, name in enumerate([v["id"] for v in variants] + reg["references"]):
            rows.append(
                {
                    "case": kind,
                    "method": name,
                    "paths": reg["paths_per_case"],
                    "promotion_rate": float(np.mean(merged["first"][i] < 2000)),
                    "labels": float(merged["labels"][i].mean()),
                    "total_cost": float(merged["total_cost"][i].mean()),
                    "delta_vs_incumbent": float(merged["delta_vs_incumbent"][i].mean()),
                }
            )
        status["completed"].append(kind)
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        print(kind, "complete", flush=True)
    (DOC / f"{prefix}_results.json").write_text(
        json.dumps({"rows": rows}, indent=2), encoding="utf-8"
    )
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["original", "range"], default="original")
    main(parser.parse_args().profile)
