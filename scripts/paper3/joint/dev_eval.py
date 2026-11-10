"""Dev-eval of tuned configs on the 30 dev-eval seeds x 24 regimes, checkpoint per regime.

usage: dev_eval.py --suite main|ablate|matched [--ref METHOD] [--workers 14]
"""

import argparse
import json
import os
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(__file__))
from common import OUT, ledger, log

from shiftlab.paper3.joint import harness as H

BASE = ["wald_paced", "wald_cut", "wald_any", "cusum", "page_hinkley", "gate_wald"]
MINE = ["A0", "A1", "A2", "A3", "A4", "A4_gate", "A5"]


def tuned(m):
    p = OUT / "tuning" / f"{m}.json"
    return json.loads(p.read_text())["best_spec"] if p.exists() else None


def specs_main():
    names, specs = ["never"], [{"kind": "never", "params": {}, "name": "never"}]
    for m in BASE + MINE:
        s = tuned(m)
        if s is not None:
            names.append(m)
            specs.append({**s, "name": m})
    return names, specs


def specs_ablate():
    names, specs = [], []

    def add(n, kind, params):
        names.append(n)
        specs.append({"kind": kind, "params": params, "name": n})

    a1 = tuned("A1")["params"]
    add("A1", "A1", a1)
    add("A1_no_delay", "A1", {**a1, "use_delay": False})
    add("A1_no_cont", "A1", {**a1, "use_cont": False})
    add("A1_no_switchpen", "A1", {**a1, "use_switch_pen": False})
    add("A1_no_batch", "A1", {**a1, "ns": (1,)})
    add("A1_paced_acq", "A1", {**a1, "acq": "paced"})
    a3 = tuned("A3")["params"]
    add("A3", "A3", a3)
    add("A3_static_duals", "A3", {**a3, "eta": 0.0})
    add("A3_no_switch_price", "A3", {**a3, "lam_sw": 0.0})
    return names, specs


def run_suite(tag, names, specs, rids, seed_list, B_by_regime=None, workers=14):
    d = OUT / tag
    d.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for rid in rids:
        f = d / f"{rid}.json"
        if f.exists():
            continue
        Bov = {rid: B_by_regime[rid]} if B_by_regime else None
        rows = H.run_batch(specs, [rid], seed_list, H.T_DEFAULT, workers, Bov)
        H.dump(f, {"names": names, "rows": rows})
        log(f"{tag}/{rid} done ({time.time() - t0:.0f}s)")
    return time.time() - t0


def load_rows(tag, rids):
    out = []
    for rid in rids:
        out += json.loads((OUT / tag / f"{rid}.json").read_text())["rows"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="main")
    ap.add_argument("--ref", default=None, help="matched: method whose label counts to match")
    ap.add_argument("--base", default=None, help="matched: baseline method to re-run")
    ap.add_argument("--workers", type=int, default=14)
    a = ap.parse_args()
    rids, sl = H.regime_ids(), H.seeds(H.EVAL_SEEDS)
    if a.suite == "main":
        names, specs = specs_main()
        wall = run_suite("dev_eval", names, specs, rids, sl, workers=a.workers)
        ledger(
            "dev_eval", {"methods": names, "seeds": [sl[0], sl[-1]], "T": H.T_DEFAULT}, None, wall
        )
    elif a.suite == "ablate":
        names, specs = specs_ablate()
        wall = run_suite("dev_ablate", names, specs, rids, sl, workers=a.workers)
        ledger("dev_ablate", {"methods": names, "seeds": [sl[0], sl[-1]]}, None, wall)
    elif a.suite == "matched":
        names, specs = specs_main()
        pid = names.index(a.ref)
        rows = load_rows("dev_eval", rids)
        nq = H.to_array(rows, len(names), rids, sl, "n_queries")[pid].mean(1)
        Bm = {r: max(1, round(float(q))) for r, q in zip(rids, nq, strict=True)}
        bp = names.index(a.base)
        wall = run_suite(
            f"dev_matched_{a.ref}_vs_{a.base}", [a.base], [specs[bp]], rids, sl, Bm, a.workers
        )
        H.dump(OUT / f"dev_matched_{a.ref}_vs_{a.base}" / "_B.json", Bm)
        ledger("dev_matched", {"ref": a.ref, "base": a.base, "B": Bm}, None, wall)


if __name__ == "__main__":
    main()
