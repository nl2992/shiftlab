"""Phase 7 panel (C): iid_failure panel on the fitted chain of every positive dataset (Phases 4b-7).

Wrapper around iid_failure/run_study.py (imported unchanged) that (i) writes to results/phase7_baselines/ instead of the
iid_failure results directory, (ii) skips the shuffled-chain refits, (iii) drops the three built-in REAL chains (they are
included here through their Phase 4b/5 best stream). Usage: [PANEL_TS=16,32] run_phase7_baselines.py [--workers 6]
(default horizons 12,20 -> phase7_baselines/; other horizons -> phase7_baselines_T<..>/)
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RD = os.path.join(ROOT, "docs/paper4_continuation/rbdp/real_data/results")
TS = tuple(int(t) for t in os.environ.get("PANEL_TS", "12,20").split(","))
OUT = os.path.join(RD, "phase7_baselines" + ("" if TS == (12, 20) else "_T" + "_".join(map(str, TS))))
sys.path.insert(0, os.path.join(ROOT, "scripts/paper4_continuation/rbdp/iid_failure"))
sys.path.insert(0, os.path.join(ROOT, "src"))
import run_study  # noqa: E402


def collect():
    items = []
    for f in ("attempts_phase4b.jsonl", "attempts_phase5.jsonl", "attempts_phase6.jsonl", "attempts_phase7.jsonl"):
        p = os.path.join(RD, f)
        if not os.path.exists(p):
            continue
        for line in open(p):
            d = json.loads(line)
            if not d.get("positive") or d["id"] == "Y:noise_control":
                continue
            ss = [s for s in d["streams"] if s["positive"]]
            b = max(ss, key=lambda s: s["best_good_cell"]["rho_Gamma"])
            items.append({"id": d["id"], "solver_params": b["solver_params"], "orientation": b["orientation"],
                          "n": b["n"], "r1": b["r1"], "phase": f[9:-6]})
    return items


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    items = collect()
    json.dump(items, open(os.path.join(OUT, "extra_chains.json"), "w"), indent=1)
    print(len(items), "chains", flush=True)
    run_study.OUT = OUT
    run_study.TS = TS
    run_study.REAL = []
    run_study.fit_shuffles = lambda real: {}
    sys.argv = [sys.argv[0], "--real-only", "--extra-chains", os.path.join(OUT, "extra_chains.json")] + sys.argv[1:]
    run_study.main()
