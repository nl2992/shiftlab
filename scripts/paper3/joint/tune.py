"""Equal-budget random-search tuning on the tuning seeds (dev block, offset 0).

usage: tune.py METHOD [METHOD ...] --n 32 --workers 16
Every method gets the same n configs (config 0 = documented default), the same 6 tuning seeds x
24 regimes at T=300, the same objective (equal-weight mean over regimes of J / J_never), and the
configs tried + wall clock are recorded to outputs/paper3/joint/tuning/<method>.json.
"""

import argparse
import os
import sys
import time

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from common import OUT, ledger, log

from shiftlab.paper3.joint import harness as H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("methods", nargs="+")
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--T", type=int, default=H.T_DEFAULT)
    a = ap.parse_args()
    (OUT / "tuning").mkdir(parents=True, exist_ok=True)
    rids, sl = H.regime_ids(), H.seeds(H.TUNE_SEEDS)
    for m in a.methods:
        path = OUT / "tuning" / f"{m}.json"
        if path.exists():
            log(f"{m}: exists, skip")
            continue
        specs = H.sample_configs(m, a.n, a.seed)
        t0 = time.time()
        log(f"{m}: {len(specs)} configs x {len(rids)} regimes x {len(sl)} seeds")
        rows = H.run_batch(specs, rids, sl, a.T, a.workers, log=log)
        wall = time.time() - t0
        J = H.to_array(rows, len(specs), rids, sl, "J")
        Jn = H.to_array(rows, len(specs), rids, sl, "J_never")[0]
        sc = H.tuning_score(J, Jn)
        nq = H.to_array(rows, len(specs), rids, sl, "n_queries").mean((1, 2))
        best = int(np.argmin(sc))
        H.dump(
            path,
            {
                "method": m,
                "wall_clock_s": wall,
                "objective": "mean_regime(J/J_never)",
                "tune_seeds": sl,
                "T": a.T,
                "specs": specs,
                "scores": sc.tolist(),
                "mean_queries": nq.tolist(),
                "best": best,
                "best_spec": specs[best],
                "default_score": float(sc[0]),
                "cpu_s": float(sum(r["sec"] for r in rows)),
            },
        )
        log(f"{m}: best cfg {best} score {sc[best]:.4f} (default {sc[0]:.4f}); wall {wall:.0f}s")
        ledger(
            "tuning",
            {"method": m, "n_configs": len(specs), "seeds": sl, "T": a.T},
            {"best": best, "best_score": float(sc[best]), "default_score": float(sc[0])},
            wall,
        )


if __name__ == "__main__":
    main()
