"""Q2 / S09 certification benchmark: structured subset of the mandated grid, per-seed records, explicit error evaluation."""

import itertools
import time
from multiprocessing import get_context

import numpy as np
import pandas as pd

from shiftlab.gap import q2

OUT = "outputs/gap_closure/e7_q2"


def jobs():
    J = []
    # core: K x gap x ranking at horizon 2000, delay 5, frac .10
    for K, gap, rk in itertools.product(
        (2, 5, 10),
        ("zero", "tiny", "moderate", "large"),
        ("stationary", "one_reversal", "recurrent"),
    ):
        if False:
            continue
        J.append((q2.Q2World(K=K, gap=gap, ranking=rk, T=2000), 0.10, 5, "core"))
    # label fraction sweep
    for f, gap, rk in itertools.product(
        (0.01, 0.05, 0.20), ("zero", "moderate"), ("stationary", "one_reversal")
    ):
        J.append((q2.Q2World(K=5, gap=gap, ranking=rk, T=2000), f, 5, "frac"))
    # delay sweep
    for dl, gap in itertools.product((0, 20), ("zero", "moderate")):
        J.append((q2.Q2World(K=5, gap=gap, ranking="stationary", T=2000), 0.10, dl, "delay"))
    # horizon sweep
    for T, gap in itertools.product((200, 500), ("zero", "moderate", "large")):
        J.append((q2.Q2World(K=5, gap=gap, ranking="stationary", T=T), 0.20, 5, "horizon"))
    return J


JOBS = jobs()


def work(i):
    w, f, dl, grp = JOBS[i]
    S = 300 if w.gap == "zero" else 120
    if w.K == 10:
        S = min(S, 100)
    st = q2.make(w, S, 90_000 + i)
    rows = []
    for m in q2.METHODS:
        res = q2.run(st, m, frac=f, delay=dl, qseed=i)
        sc = q2.score(res, st)
        rows.append(
            pd.DataFrame(
                {
                    "grp": grp,
                    "world": w.name,
                    "K": w.K,
                    "gap": w.gap,
                    "ranking": w.ranking,
                    "T": w.T,
                    "frac": f,
                    "delay": dl,
                    "method": m,
                    "seed": 90_000 + i * 1000 + np.arange(S),
                    "certified": sc["certified"],
                    "correct": sc["correct"],
                    "incorrect": sc["incorrect"],
                    "false_reject_any": sc["false_reject_any"],
                    "cert_t": sc["cert_t"],
                    "labels_at_cert": sc["labels_at_cert"],
                    "labels_total": res["labels_total"],
                    "n_elim": sc["n_elim"],
                    "runtime_s_per_seed": res["runtime_s"] / S,
                    "peak_rss_mb": res["peak_rss_mb"],
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


if __name__ == "__main__":
    import os

    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    with get_context("fork").Pool(4) as pool:
        parts = pool.map(work, range(len(JOBS)), chunksize=1)
    df = pd.concat(parts, ignore_index=True)
    df.to_parquet(f"{OUT}/perseed.parquet", index=False)
    print("rows", len(df), "worlds", len(JOBS), "seconds", round(time.time() - t0))
