"""EXPLORATORY / EXPOSED: run the atlas method roster on the c4_sealed real loss streams.
No causal onsets exist, so alarm proxies are computed ex post from realised episode gain (analysis script).
Contract: T=2000, B=200, c_q=.05, k=5, alpha=.05; delay from the file. First N_EP episodes per stream.
"""

import glob
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from shiftlab.paper3.atlas import ledger
from shiftlab.paper3.atlas.runner import MAIN, REPAIR, build
from shiftlab.paper3.atlas.sim import preds_from_losses, run_episode

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT.parent / "shift-research-starter/data/c4_sealed"
OUT = ROOT / "outputs/paper3/atlas/real"
N_EP, B, PRICE, K = 30, 200, 0.05, 5.0
METHODS = MAIN + ["iid_gate", "edetector_cal", "cusum_cal"] + REPAIR
SB = 7500000


def job(path):
    name = Path(path).stem
    f = OUT / f"{name}.jsonl"
    if f.exists():
        return name, 0
    z = np.load(path)
    l0, l1, delay = z["l0"], z["l1"], int(z["delay"])
    rows = []
    for ep in range(min(N_EP, l0.shape[0])):
        L = np.stack([l0[ep], l1[ep]], 1)
        preds, labels = preds_from_losses(L, np.random.default_rng([SB, ep, 7]))
        delays = np.full(L.shape[0], max(delay, 1))
        D = L[:, 0].astype(int) - L[:, 1].astype(int)
        cp = {"budget": B, "switch_cost": K, "delay": max(delay, 1), "price": PRICE}
        for m in METHODS:
            out = run_episode(
                build(m, cp, SB, ep), preds, labels, delays, budget=B, price=PRICE, switch_cost=K
            )
            dep = out.dep.astype(int)
            assert (
                abs(
                    out.cost
                    - (
                        L[:, 0].sum()
                        + PRICE * out.n_queries
                        + K * out.n_switches
                        - D[dep == 1].sum()
                    )
                )
                < 1e-6
            )
            fp = int(np.argmax(dep == 1)) if (dep == 1).any() else -1
            rows.append(
                {
                    "stream": name,
                    "ep": ep,
                    "method": m,
                    "J": float(out.cost),
                    "sumD": int(D.sum()),
                    "n_q": out.n_queries,
                    "n_sw": out.n_switches,
                    "first_prom": fp,
                    "ever_prom": int(fp >= 0),
                    "delay": delay,
                }
            )
    f.write_text("\n".join(json.dumps(r) for r in rows))
    return name, len(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(DATA / "*.npz")))
    t = time.time()
    with ProcessPoolExecutor(14) as ex:
        for n, k in ex.map(job, files):
            print(n, k, round(time.time() - t), flush=True)
    ledger.append(
        "real_c4_exploratory_exposed",
        {"N_EP": N_EP, "B": B, "price": PRICE, "k": K, "methods": METHODS},
        f"episodes 0..{N_EP - 1} per stream, seed_base {SB}",
        "complete",
        str(OUT),
        "all c4 streams exposed by Papers 1/2",
    )
