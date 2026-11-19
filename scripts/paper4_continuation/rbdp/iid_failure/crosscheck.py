"""Cross-checks run before the main study. Usage: PYTHONPATH=src python crosscheck.py  (writes results/crosscheck.json)."""
from __future__ import annotations

import itertools
import json
import os
import random
import subprocess
import sys
from fractions import Fraction as F

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
from iidlib import (Chain, GatePolicy, Post, calibrate_p1, calibrate_p2, calibrate_p3, calibrate_p4, cost, risks)  # noqa: E402
from runner import run_setting, solver_policy  # noqa: E402

OUT = os.path.join(ROOT, "docs/paper4_continuation/rbdp/iid_failure/results")
os.makedirs(OUT, exist_ok=True)


def brute_force_causal(pol, ch, kmax=18):
    """Max over all 2^K deterministic nulls (p in {0, 1/2} at every query node, as a function of the FULL history)
    of the exact promotion probability. Independent of the Lemma-A recursion: explicit history tree, vectorised."""
    T = ch.T
    nodes = []  # history tuples at which the policy queries with positive probability

    def walk(h, t, n, s):
        if t > T:
            return
        pi, kap = pol.act(t, n, s)
        if pi >= 1:
            return
        if kap > 0:
            nodes.append(h)
        if kap < 1:
            walk(h + ("n",), t + 1, n, pol.step(s, t, n, "n"))
        if kap > 0:
            for y in (0, 1):
                walk(h + (y,), t + 1, n - 1, pol.step(s, t, n, y))

    walk((), 1, ch.B, pol.s0)
    K = len(nodes)
    if K > kmax:
        return None, K
    idx = {h: i for i, h in enumerate(nodes)}
    grid = np.array(list(itertools.product((0.0, 0.5), repeat=K))).T if K else np.zeros((0, 1))

    def prob(h, t, n, s):
        if t > T:
            return np.zeros(grid.shape[1])
        pi, kap = pol.act(t, n, s)
        if pi >= 1:
            return np.ones(grid.shape[1])
        val = np.zeros(grid.shape[1])
        if kap < 1:
            val = val + (1 - kap) * prob(h + ("n",), t + 1, n, pol.step(s, t, n, "n"))
        if kap > 0:
            p = grid[idx[h]]
            val = val + kap * ((1 - p) * prob(h + (0,), t + 1, n - 1, pol.step(s, t, n, 0))
                               + p * prob(h + (1,), t + 1, n - 1, pol.step(s, t, n, 1)))
        return pi + (1 - pi) * val

    allp = prob((), 1, ch.B, pol.s0)
    # random continuous nulls must not exceed
    return float(allp.max()), K


def check_a():
    cells = [
        dict(t01=0.75, t10=0.75, e0=0.1, T=4, B=2, alpha=0.1),
        dict(t01=0.9, t10=0.6, e0=0.2, T=5, B=2, alpha=0.05),
        dict(t01=0.6, t10=0.9, e0=0.1, T=5, B=1, alpha=0.1),
        dict(t01=0.25, t10=0.1, e0=0.1, T=4, B=2, alpha=0.1),
        dict(t01=0.9, t10=0.9, e0=0.2, T=3, B=2, alpha=0.05),
    ]
    out = []
    for c in cells:
        ch = Chain(c["t01"], c["t10"], c["e0"], 1 - c["e0"], c["t01"] / (c["t01"] + c["t10"]), c["T"], c["B"])
        for cal in (calibrate_p1, calibrate_p2, calibrate_p3, calibrate_p4):
            pol = cal(ch, c["alpha"])
            ri, rc = risks(pol, ch)
            bf, K = brute_force_causal(pol, ch)
            out.append(dict(cell=c, policy=pol.name, param=pol.param(), K_query_nodes=K, risk_iid=ri,
                            evaluator_causal=rc, brute_force_max=bf,
                            abs_diff=None if bf is None else abs(bf - rc), ok=None if bf is None else bool(abs(bf - rc) < 1e-12)))
    return out


def check_gate():
    """Float gate DP vs the repo's exact Fraction planner (EProcessGatedPlanner.solve_gated), small rational cells."""
    out = []
    for (t01, t10, e0, T, B) in [("3/4", "3/4", "1/10", 5, 2), ("9/10", "3/5", "1/5", 6, 3), ("1/4", "1/10", "1/10", 5, 2)]:
        ch = Chain(float(F(t01)), float(F(t10)), float(F(e0)), 1 - float(F(e0)),
                   float(F(t01) / (F(t01) + F(t10))), T, B)
        post = Post(ch)
        for m in range(1, B + 1):
            th = 2 ** m
            g = GatePolicy(ch, post, th)
            code = (
                "import sys,json;sys.path.insert(0,%r);from fractions import Fraction as F;"
                "from gamma_lib import make;from shiftlab.dive.eprocess_gated_planner import EProcessGatedPlanner;"
                "cfg,model=make(%d,%d,1,F(%r),F(%r),F(%r),1-F(%r),F(%r)/(F(%r)+F(%r)),F(1,100),F(0),F(1,10));"
                "cost,_=EProcessGatedPlanner(cfg,model,stake=F(1),threshold=F(%d)).solve_gated();print('@@'+str(float(cost)))"
            ) % (os.path.join(ROOT, "scripts/paper4_continuation/theory_C"), T, B, t01, t10, e0, e0, t01, t01, t10, th)
            p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT,
                               env=dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src")), timeout=600)
            ref = next((float(l[2:]) for l in p.stdout.splitlines() if l.startswith("@@")), None)
            out.append(dict(cell=dict(t01=t01, t10=t10, e0=e0, T=T, B=B), th=th, mine=g.cost_gate, planner=ref,
                            abs_diff=None if ref is None else abs(ref - g.cost_gate),
                            err=None if ref is not None else p.stderr[-300:]))
    return out


def check_cost_mc(n=200000, seed=7):
    """Monte Carlo of the alternative HMM for P3 (cost accounting incl. promotion cost from Post)."""
    ch = Chain(0.75, 0.75, 0.1, 0.9, 0.5, 8, 3)
    post = Post(ch)
    pol = calibrate_p3(ch, 0.1)
    exact = cost(pol, ch, post)
    rng = random.Random(seed)
    tot = 0.0
    sq = 0.0
    for _ in range(n):
        S = 1 if rng.random() < ch.prior1 else 0
        # state at t=1: S_1 evolves from S_0 ~ prior1
        S = (1 if rng.random() < ch.t01 else 0) if S == 0 else (0 if rng.random() < ch.t10 else 1)
        s, nq, b = pol.s0, ch.B, ch.beta1()
        cst = 0.0
        pend = None
        t = 1
        # sequential simulation with exact belief filter
        states = []
        # simulate the whole latent chain and labels first
        Ss, Ys = [S], []
        for tt in range(1, ch.T + 1):
            Ys.append(1 if rng.random() < (ch.e1 if Ss[-1] else ch.e0) else 0)
            if tt < ch.T:
                Ss.append((1 if rng.random() < ch.t01 else 0) if Ss[-1] == 0 else (0 if rng.random() < ch.t10 else 1))
        for t in range(1, ch.T + 1):
            pi, kap = pol.act(t, nq, s)
            if pi >= 1:  # deterministic promotion in the (theta<1 coin) -> handle coin
                pass
            u = rng.random()
            if u < pi:
                cst += post.P(t, nq, b)  # expectation of post-promotion cost (exact), not simulated
                break
            cst += Ys[t - 1]  # step cost: action 0 incurs loss 1 iff Y_t = 1
            if kap > 0 and nq > 0 and t < ch.T:
                cst += ch.c
                y = Ys[t - 1]
                s2 = pol.step(s, t, nq, y)
                b = s2
                s, nq = s2, nq - 1
            else:
                s = pol.step(s, t, nq, "n")
                b = s
        tot += cst
        sq += cst * cst
    mean = tot / n
    se = ((sq / n - mean * mean) / n) ** 0.5
    return dict(exact=exact, mc_mean=mean, mc_se=se, z=(mean - exact) / se, n=n)


def check_iid_vs_cost_order():
    """P5 (IID optimum) must have cost <= every IID-feasible policy 1-4 (all have IID risk alpha)."""
    out = []
    for (t01, t10, e0, T, B, a) in [(0.9, 0.9, 0.1, 12, 3, 0.1), (0.75, 0.6, 0.2, 12, 2, 0.05), (0.1, 0.25, 0.1, 12, 3, 0.1)]:
        ch = Chain(t01, t10, e0, 1 - e0, t01 / (t01 + t10), T, B)
        rows = {r["policy"]: r for r in run_setting(ch, a, {})}
        out.append(dict(cell=dict(t01=t01, t10=t10, e0=e0, T=T, B=B, alpha=a),
                        C5=rows["P5_iid_optimal_pomdp"]["cost"],
                        C1_4={k: rows[k]["cost"] for k in rows if k[:2] in ("P1", "P2", "P3", "P4")},
                        ok=all(rows["P5_iid_optimal_pomdp"]["cost"] <= rows[k]["cost"] + 1e-9 for k in rows if k[:2] in ("P1", "P2", "P3", "P4")),
                        C0_mine=rows["P1_fixed_sample"]["C0"], C0_solver=rows["P5_iid_optimal_pomdp"]["solver_C0"],
                        C7=rows["P7_rbdp_causal"]["cost"], risk7_causal=rows["P7_rbdp_causal"]["risk_causal"],
                        risk5_iid=rows["P5_iid_optimal_pomdp"]["risk_iid"], risk5_causal=rows["P5_iid_optimal_pomdp"]["risk_causal"]))
    return out


if __name__ == "__main__":
    res = {"a_bruteforce": check_a(), "gate_vs_planner": check_gate(), "cost_mc": check_cost_mc(),
           "p5_order_and_C0": check_iid_vs_cost_order()}
    json.dump(res, open(os.path.join(OUT, "crosscheck.json"), "w"), indent=1)
    for r in res["a_bruteforce"]:
        print(r["cell"], r["policy"], "K", r["K_query_nodes"], "eval", r["evaluator_causal"], "brute", r["brute_force_max"], r["ok"])
    for r in res["gate_vs_planner"]:
        print(r)
    print(res["cost_mc"])
    for r in res["p5_order_and_C0"]:
        print(r)
