"""Phase 10 baseline panel on the 4 new supporting datasets (B:covtype, Bext:electricity, D:geyser/Grand, D:geyser/Old_Faithful).

Reuses run_phase7_baselines (T in {16,32} panel, P1-P7) and run_phase9 (P3c, P4c, P5r) unchanged; only the chain list and the
output paths differ. Outputs: results/phase10_baselines/{extra_chains.json,settings.jsonl,...}, results/phase10_baselines_panel9.jsonl,
results/phase10_baselines.log.
Usage: PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python run_phase10_baselines.py [p7|p9] [--workers 6]
"""
import json
import os
import sys

os.environ["PANEL_TS"] = "16,32"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_phase7_baselines as b7  # noqa: E402

IDS = ["B:covtype", "Bext:electricity", "D:geyser/Grand", "D:geyser/Old_Faithful"]
FILES = ["attempts_phase10_shard1.jsonl", "attempts_phase10_shard2.jsonl", "attempts_phase10b.jsonl"]
OUT = os.path.join(b7.RD, "phase10_baselines")


def collect10():
    items = []
    for f in FILES:
        for line in open(os.path.join(b7.RD, f)):
            d = json.loads(line)
            if d["id"] in IDS and d.get("positive"):
                ss = [s for s in d["streams"] if s["positive"]]
                b = max(ss, key=lambda s: s["best_good_cell"]["rho_Gamma"])
                items.append({"id": d["id"], "solver_params": b["solver_params"], "orientation": b["orientation"],
                              "n": b["n"], "r1": b["r1"], "phase": "phase10"})
    assert sorted(i["id"] for i in items) == sorted(IDS), [i["id"] for i in items]
    return items


if __name__ == "__main__":
    stage = sys.argv[1]
    if stage == "p7":
        os.makedirs(OUT, exist_ok=True)
        json.dump(collect10(), open(os.path.join(OUT, "extra_chains.json"), "w"), indent=1)
        b7.run_study.OUT = OUT
        b7.run_study.TS = b7.TS
        b7.run_study.REAL = []
        b7.run_study.fit_shuffles = lambda real: {}
        sys.argv = [sys.argv[0], "--real-only", "--extra-chains", os.path.join(OUT, "extra_chains.json")] + sys.argv[2:]
        b7.run_study.main()
    else:
        import run_phase9 as p9
        from pathlib import Path
        p9.P7DIR = Path(OUT)
        p9.PANEL = Path(b7.RD) / "phase10_baselines_panel9.jsonl"
        p9.LOG = Path(b7.RD) / "phase10_baselines.log"
        w = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--workers=")), 4))
        p9.run_panel(w)
