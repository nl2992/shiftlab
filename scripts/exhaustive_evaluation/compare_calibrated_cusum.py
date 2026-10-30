"""Independent finite-horizon classical-baseline comparison, not a new method."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from scipy.stats import beta

from shiftlab.sota_search.paired_control import PairedConfig, paired_screen, paired_world
from shiftlab.sota_search.paired_cusum import paired_cusum

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"
NULLS = ["harmful", "tie", "harmful_after_shift"]
ALTS = ["useful_initial", "useful", "late", "small", "reversal"]


def main(profile="original"):
    if profile not in ("original", "strict"):
        raise ValueError("unknown registered experiment profile")
    strict = profile == "strict"
    prefix = "cusum_strict" if strict else "cusum_comparison"
    quantile = 0.975 if strict else 0.95
    world_seed = 202640000 if strict else 202630000
    query_seed = 202641000 if strict else 202631000
    regpath = DOC / f"{prefix}_registration.json"
    if regpath.exists():
        raise FileExistsError("inspect existing run before restarting")
    sources = [
        "src/shiftlab/sota_search/paired_cusum.py",
        "src/shiftlab/sota_search/paired_control.py",
        "src/shiftlab/sota_search/paired_references.py",
        "src/shiftlab/sota_search/combination_screen.py",
        "scripts/exhaustive_evaluation/compare_calibrated_cusum.py",
    ]
    reg = {
        "registered_utc": datetime.now(UTC).isoformat(),
        "stage": "independent synthetic operational comparison",
        "slacks": [0, 0.01, 0.05, 0.1],
        "nulls": NULLS,
        "alternatives": ALTS,
        "calibration_paths_per_null": 1000,
        "test_paths_per_null": 2000,
        "test_paths_per_alternative": 500,
        "horizon": 2000,
        "batch": 250,
        "world_seed_base": world_seed,
        "query_seed_base": query_seed,
        "calibration_quantile": quantile,
        "calibration": "per-slack threshold=max across null cases of order statistic ceil(quantile*(n+1)); strict crossing; no alternative tuning",
        "contract": "uniform Bernoulli .2 hard cap400; delay5; margin.01; query.001; switch1; no rollback",
        "primary": "per-method equal-case persistent alternative total cost; all four slacks reported, no post-test winner claim",
        "safety": "empirical finite-horizon null rates with simultaneous one-sided bounds over six methods times three nulls; no arbitrary-null guarantee for CUSUM",
        "screen": "all three null simultaneous upper bounds <=.06; practical gain >=10 percent against tuned comparator; report every slack separately",
        "sources": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
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
    null_maxima = []
    for j, kind in enumerate(NULLS):
        values = []
        for b in range(4):
            offset = j * 100 + b
            stream = paired_world(kind, paths=250, horizon=2000, seed=world_seed + offset)
            values.append(paired_cusum(stream, reg["slacks"], seed=query_seed + offset)["maximum"])
        values = np.concatenate(values, axis=1)
        null_maxima.append(np.sort(values, axis=1)[:, int(np.ceil(quantile * 1001)) - 1])
    thresholds = np.max(null_maxima, axis=0)
    threshold_file = (
        "cusum_strict_thresholds.json" if strict else "cusum_calibrated_thresholds.json"
    )
    (DOC / threshold_file).write_text(
        json.dumps(
            {"thresholds": thresholds.tolist(), "per_null": [v.tolist() for v in null_maxima]}
        ),
        encoding="utf-8",
    )
    rows = []
    for j, kind in enumerate(NULLS + ALTS):
        n = 2000 if kind in NULLS else 500
        values = []
        for b in range(n // 250):
            offset = 1000 + j * 100 + b
            stream = paired_world(kind, paths=250, horizon=2000, seed=world_seed + offset)
            classical = paired_cusum(stream, reg["slacks"], thresholds, seed=query_seed + offset)
            betting = paired_screen(stream, configs, seed=query_seed + offset)
            result = {
                k: np.concatenate([classical[k], betting[k]], axis=0)
                for k in ["first", "labels", "total_cost", "delta_vs_incumbent"]
            }
            np.savez_compressed(out / f"{kind}_{b:03d}.npz", **result)
            values.append(result)
        merged = {k: np.concatenate([v[k] for v in values], axis=1) for k in values[0]}
        for i, method in enumerate(
            [f"cusum_{s}" for s in reg["slacks"]] + ["paired_Kelly", "tuned_FTL"]
        ):
            count = int((merged["first"][i] < 2000).sum())
            rows.append(
                {
                    "case": kind,
                    "method": method,
                    "paths": n,
                    "promotions": count,
                    "promotion_rate": count / n,
                    "simultaneous_null_upper": float(beta.ppf(1 - 0.05 / 18, count + 1, n - count))
                    if kind in NULLS and count < n
                    else None,
                    "total_cost": float(merged["total_cost"][i].mean()),
                    "delta_vs_incumbent": float(merged["delta_vs_incumbent"][i].mean()),
                    "labels": float(merged["labels"][i].mean()),
                }
            )
        status["completed"].append(kind)
        statuspath.write_text(json.dumps(status), encoding="utf-8")
        print(kind, "complete", flush=True)
    (DOC / f"{prefix}_results.json").write_text(
        json.dumps({"thresholds": thresholds.tolist(), "rows": rows}, indent=2), encoding="utf-8"
    )
    status["status"] = "completed"
    statuspath.write_text(json.dumps(status), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["original", "strict"], default="original")
    main(parser.parse_args().profile)
