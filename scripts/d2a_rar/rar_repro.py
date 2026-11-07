"""Reproduce a subset of RAR (arXiv:2611.02251v1) native-stream results on ELEC2-based streams.
Usage: python scripts/d2a_rar/rar_repro.py --seeds 5 --out results/d2a_rar/rar_repro.json
Checkpoints per (stream, seed) to the --out file; resumable."""

import argparse
import json
import os
import time

from shiftlab.sota.rar import (
    ADWINDetector,
    RARConfig,
    RiverHoeffdingTreeFactory,
    StepSizeQuality,
    run_stream,
    utility_at_rho,
)
from shiftlab.sota.rar.streams import load_elec2, semi_abrupt, semi_rollback_then_drift

COST_BLIND = ["no_response", "always_retrain", "binary", "alert_only", "rollback_only", "full_rar"]
ap = argparse.ArgumentParser()
ap.add_argument("--seeds", type=int, default=5)
ap.add_argument("--streams", default="elec2,semi_abrupt,semi_rb_drift")
ap.add_argument("--csv", default=os.path.expanduser("~/river_data/Elec2/electricity.csv"))
ap.add_argument("--out", default="results/d2a_rar/rar_repro.json")
ap.add_argument("--ca_rhos", default="1,10,100,1000")
a = ap.parse_args()

X0, y0, sha = load_elec2(a.csv)
res = {}
if os.path.exists(a.out):
    with open(a.out) as fh:
        res = json.load(fh)
res["_meta"] = {"elec2_sha256": sha, "n": len(y0), "fidelity": "PAPER_RECONSTRUCTION"}
for stream in a.streams.split(","):
    for seed in range(a.seeds):
        key = f"{stream}|{seed}"
        if key in res:
            continue
        if stream == "elec2":
            X, y, info = X0, y0, {}
        elif stream == "semi_abrupt":
            X, y, info = semi_abrupt(X0, y0, seed)
        else:
            X, y, info = semi_rollback_then_drift(X0, y0, seed)
        rec = {"info": info, "policies": {}}
        t0 = time.time()
        for mode in COST_BLIND:
            cfg = RARConfig(mode=mode, seed=seed)
            r = run_stream(
                X,
                y,
                cfg,
                RiverHoeffdingTreeFactory(),
                ADWINDetector(),
                quality=StepSizeQuality(cfg.q_window, cfg.q_ratio),
            )
            rec["policies"][mode] = {
                "n_correct": r["n_correct"],
                "n_eval": r["n_eval"],
                "counts": r["counts"],
                "U": {
                    str(rho): utility_at_rho(r, rho, cfg) for rho in (0.1, 0.5, 1, 5, 10, 100, 200)
                },
                "causes": [e.get("cause") for e in r["log"] if e["event"] == "action:rollback"],
            }
        for rho in map(float, a.ca_rhos.split(",")):
            cfg = RARConfig(mode="cost_aware_binary", seed=seed, rho=rho)
            r = run_stream(X, y, cfg, RiverHoeffdingTreeFactory(), ADWINDetector())
            rec["policies"][f"cost_aware_binary@{rho:g}"] = {
                "n_correct": r["n_correct"],
                "counts": r["counts"],
                "U": r["U"],
            }
            # Binary / Full RAR at same rho (re-priced exactly)
            for mode in ("binary", "full_rar", "no_response", "always_retrain"):
                rec["policies"][mode]["U"][str(rho)] = utility_at_rho(
                    {
                        "n_correct": rec["policies"][mode]["n_correct"],
                        "counts": rec["policies"][mode]["counts"],
                    },
                    rho,
                    cfg,
                )
        rec["secs"] = time.time() - t0
        res[key] = rec
        with open(a.out, "w") as fh:
            json.dump(res, fh)
        print(
            key,
            f"{rec['secs']:.0f}s",
            {
                m: round(v["U"]["1"], 1)
                for m, v in rec["policies"].items()
                if isinstance(v.get("U"), dict) and "1" in v["U"]
            },
            flush=True,
        )
