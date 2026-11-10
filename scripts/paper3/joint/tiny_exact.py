"""Tiny exact check: value gap of each method (given the TRUE model) to the exact DP optimum."""

import json
import os
import sys
import time
from fractions import Fraction as F
from multiprocessing import Pool

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from common import OUT, ledger, log

from shiftlab.paper3.baselines import AlwaysChallenger, Gate, NeverSwitch, WaldEconomic
from shiftlab.paper3.contracts import Costs, ProblemSpec
from shiftlab.paper3.joint.policies import QVOI, BeliefMPC, DualPrice, RankReversal
from shiftlab.paper3.oracle import EconomicOracle, HMMModel, OraclePolicy
from shiftlab.paper3.simulation import Tape, run_policy

# regime 0: challenger worse (m1 high); regime 1: challenger better (m1 low); incumbent m0=.5.
# (the core default HMM has an immediate-always optimum, which makes information worthless)
INSTANCES = [
    {"T": 8, "B": 2, "d": 1, "c_q": 0.03, "k": 0.6, "tr": 0.03, "m1": (0.9, 0.1)},
    {"T": 10, "B": 3, "d": 1, "c_q": 0.03, "k": 1.0, "tr": 0.05, "m1": (0.8, 0.1)},
    {"T": 12, "B": 3, "d": 2, "c_q": 0.03, "k": 1.0, "tr": 0.03, "m1": (0.8, 0.1)},
    {"T": 12, "B": 3, "d": 3, "c_q": 0.03, "k": 1.5, "tr": 0.03, "m1": (0.8, 0.1)},
]


def model_of(inst):
    tr = F(inst["tr"]).limit_denominator(1000)
    m1 = tuple(F(x).limit_denominator(100) for x in inst["m1"])
    return HMMModel(((1 - tr, tr), (tr, 1 - tr)), F(1, 2), (F(1, 2), F(1, 2)), m1)


def known_of(inst):
    return {
        "trans": [[1 - inst["tr"], inst["tr"]], [inst["tr"], 1 - inst["tr"]]],
        "m0": [0.5, 0.5],
        "m1": list(inst["m1"]),
        "prior1": 0.5,
    }


NT = int(os.environ.get("TINY_NT", 4000))  # noqa: PLW1508


def methods(kn):
    return {
        "never": lambda: NeverSwitch(),
        "always": lambda: AlwaysChallenger(),
        "wald_default": lambda: WaldEconomic(0.98, 0.3, "paced"),
        "A0_mpc(true model)": lambda: BeliefMPC(N=256, Hmax=40, known=kn),
        "A1_qvoi(true model)": lambda: QVOI(known=kn, n_models=1, ns=(1, 2, 3)),
        "A1_nobatch(true model)": lambda: QVOI(known=kn, n_models=1, ns=(1,), name="A1nb"),
        "A2_gate(A1)": lambda: Gate(QVOI(known=kn, n_models=1, ns=(1, 2, 3)), alpha=0.1, lam=0.25),
        "A3_dual(true model)": lambda: DualPrice(known=kn, n_models=1, kappa=1.0),
        "A5_flip(true model)": lambda: RankReversal(
            known=kn, n_models=1, n_batch=3, eps_flip=0.05, h_min=0
        ),
    }


_W = {}


def _chunk(args):
    inst, seeds = args
    T, B, d = inst["T"], inst["B"], inst["d"]
    spec = ProblemSpec(T=T, B=B, costs=Costs(inst["c_q"], inst["k"], 0.0, 0.0), delay_known=d)
    MODEL = model_of(inst)
    key = json.dumps(inst)
    if key not in _W:  # persistent per worker: the exact DP cache is reused across chunks
        orc = EconomicOracle(MODEL, T, B, d, inst["c_q"], inst["k"], num=float)
        pols = {"EXACT_DP": OraclePolicy(orc)}
        pols.update({n: f() for n, f in methods(known_of(inst)).items()})
        _W[key] = pols
    pols = _W[key]
    out = {n: [] for n in pols}
    for s in seeds:
        rng = np.random.default_rng([s, 99])
        ell = MODEL.sample_tape(T, rng)
        tape = Tape(ell, np.ones(T, bool), np.zeros((T, 1)), np.full(T, d))
        for n, p in pols.items():
            out[n].append(run_policy(p, tape, spec, int(s)).J)
    return out


def main():
    res = {}
    t0 = time.time()
    with Pool(14) as pool:
        for inst in INSTANCES:
            T, B, d = inst["T"], inst["B"], inst["d"]
            tt = time.time()
            exact = (
                EconomicOracle(
                    model_of(inst),
                    T,
                    B,
                    d,
                    F(inst["c_q"]).limit_denominator(1000),
                    F(inst["k"]).limit_denominator(1000),
                    num=float,
                )
                .solve()
                .value
            )
            seeds = np.arange(NT)
            chunks = [(inst, c) for c in np.array_split(seeds, 112)]
            parts = pool.map(_chunk, chunks)
            J = {n: np.concatenate([p[n] for p in parts]) for n in parts[0]}
            ref = J["EXACT_DP"]
            tab = {}
            for n, v in J.items():
                dlt = v - ref
                tab[n] = {
                    "J": float(v.mean()),
                    "gap": float(dlt.mean()),
                    "se": float(dlt.std(ddof=1) / np.sqrt(len(v))),
                    "gap_pct": float(100 * dlt.mean() / abs(ref.mean())),
                }
            res[json.dumps(inst)] = {
                "exact_value": float(exact),
                "mc_exact_policy": float(ref.mean()),
                "table": tab,
            }
            log(f"{inst} exact={float(exact):.4f} mc={ref.mean():.4f} ({time.time() - tt:.0f}s)")
            for n, r in tab.items():
                log(
                    f"   {n:26s} J={r['J']:.4f} gap={r['gap']:+.4f} +- {1.96 * r['se']:.4f} ({r['gap_pct']:+.1f}%)"
                )
    (OUT / "tiny_exact.json").write_text(json.dumps(res, indent=1))
    ledger("tiny_exact", {"instances": INSTANCES, "n_tapes": NT}, res, time.time() - t0)


if __name__ == "__main__":
    main()
