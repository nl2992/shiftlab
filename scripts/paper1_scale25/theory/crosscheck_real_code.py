"""Cross-check: the reduced DP's evaluation of the beta-quantile controller vs the repository's own
EQSD class (scripts/qsg_methods_search/eqs_d.py) run in the repository simulator on streams drawn
from the reduced model (every step a disagreement, p ~ prior). lam = 1 so the evidence is (k, n).
Agreement within Monte Carlo error validates the DP's timing/queue/release semantics against the
real implementation (not the controllers' statistical properties).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search"))
import reduced_dp as R
from eqs_d import EQSD
from simulator import run_episode


def run(inst: R.Inst, gamma: float, n_ep: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    nets = []
    for e in range(n_ep):
        p = inst.prior_sample(rng, 1)[0]
        l0 = (rng.random(inst.T) < p).astype(int)  # incumbent wrong <=> challenger correct
        labels = rng.integers(0, 2, inst.T)
        preds = np.stack([labels ^ l0, labels ^ (1 - l0)], 1)
        pol = EQSD(
            inst.T,
            inst.B,
            inst.cs,
            rng=np.random.default_rng(rng.integers(1 << 31)),
            lam=1.0,
            gamma=gamma,
            stake=False,
        )
        r = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=inst.d,
            budget=inst.B,
            label_price=inst.cq,
            switch_cost=inst.cs,
            trace=False,
        )
        nets.append(r.net_cost)
    nets = np.array(nets)
    return nets.mean(), nets.std(ddof=1) / np.sqrt(n_ep)


if __name__ == "__main__":
    for inst in (R.Inst(T=60, B=8, d=3, cs=3.0), R.Inst(T=100, B=14, d=4, cs=5.0)):
        for g in (0.3, 0.1):
            ex = R.evaluate(inst, R.Ctrl(kind="beta", gamma=g, rate_mode="estimated"))
            mc, se = run(inst, g, 4000, seed=1)
            print(
                f"T={inst.T} B={inst.B} d={inst.d} cs={inst.cs} gamma={g}: DP {ex:.3f}  real-code MC {mc:.3f} +- {se:.3f}  z={(mc - ex) / se:+.2f}"
            )
