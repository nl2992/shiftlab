"""Sethi Algorithm 1 on the lazy-resample chain: size at the null boundary and power vs the oracle ceiling (gate_b_oracle.json)."""

import json
from pathlib import Path

import numpy as np

from shiftlab.dep import sethi

T, R0, ALPHA, S, EVERY = 2000, 0.3, 0.05, 1000, 10
rng = np.random.default_rng(5)


def run(delta, pi):
    cur = (rng.random(S) < pi).astype(int)
    prev = cur.copy()
    n = np.zeros((S, 2, 2))
    stopped = np.full(S, T)
    for t in range(1, T):
        sw = rng.random(S) < delta
        cur = np.where(sw, (rng.random(S) < pi).astype(int), cur)
        np.add.at(n, (np.arange(S), prev, cur), 1)
        prev = cur
        if t % EVERY == 0:
            L = sethi.statistic(n[:, 0, 0], n[:, 0, 1], n[:, 1, 0], n[:, 1, 1], R0)
            beta = sethi.threshold(n[:, 0].sum(1), n[:, 1].sum(1), ALPHA)
            stopped = np.where((L >= beta) & (stopped == T), t, stopped)
    return float((stopped < T).mean())


oracle = json.loads(Path("outputs/dep_sprint/gate_b_oracle.json").read_text())
out = {}
for tdelta in (1, 20, 100, 500):
    d = tdelta / T
    size = run(d, R0)
    row = {"size_at_boundary": size}
    for eps in (0.05, 0.1):
        row[f"power_eps={eps}"] = run(d, R0 + eps)
        row[f"oracle_power_eps={eps}"] = oracle[f"eps={eps},T*delta={tdelta}"]["oracle_power"]
    out[f"T*delta={tdelta}"] = row
    print(tdelta, row, flush=True)
Path("outputs/dep_sprint/sethi_vs_oracle.json").write_text(json.dumps(out, indent=1))
