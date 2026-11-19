"""Check (a): Lemma A (d=1) and Lemma A_2 (DELAY2 §2, d=2) against brute-force enumeration of nulls.

A random behavioural learner policy (pi, kappa) is drawn on learner information sets of the pre-promotion
tree.  Nulls choose p at every query node as a function of the FULL history (all generated labels,
including a pending one when d=2).  We enumerate all 2^K deterministic nulls with p in {0, 1/2}
(vectorised, float64), take the max of the exact promotion probability, and compare with the
backward recursion R = pi + (1-pi)[(1-kappa) R_n + kappa max(R_0, (R_0+R_1)/2)] evaluated in Fractions.
Also: 20000 random continuous nulls p in [0, 1/2] (must not exceed the recursion), and the IID null.
"""
from __future__ import annotations

import itertools
import random
import sys
from fractions import Fraction as F

import numpy as np

VALS = [F(0), F(1, 4), F(1, 3), F(1, 2), F(2, 3), F(1), F(1, 10)]


def run(T: int, B: int, d: int, seed: int) -> dict:
    rng = random.Random(seed)

    # full history: tuple of steps, step = 'n' (no query) or 0/1 (queried label)
    def nq(full):
        return sum(1 for s in full if s != "n")

    def info(full):
        if d == 1 or not full or full[-1] == "n":
            return full
        return full[:-1] + ("q",)  # pending label hidden from learner

    pol: dict = {}

    def policy(full):
        key = info(full)
        if key not in pol:
            pi = rng.choice(VALS) if rng.random() < 0.8 else F(0)
            kappa = rng.choice(VALS) if nq(full) < B else F(0)
            pol[key] = (pi, kappa)
        return pol[key]

    # enumerate nodes (pre-promotion, t <= T)
    nodes = []

    def walk(full):
        if len(full) >= T:
            return
        nodes.append(full)
        walk(full + ("n",))
        if nq(full) < B:
            walk(full + (0,))
            walk(full + (1,))

    walk(())
    qnodes = [h for h in nodes if nq(h) < B and policy(h)[1] > 0]
    qidx = {h: i for i, h in enumerate(qnodes)}
    K = len(qnodes)

    # exact recursion (Lemma A / A_2)
    def R(full, mode):
        if len(full) >= T:
            return F(0)
        pi, kappa = policy(full)
        rn = R(full + ("n",), mode)
        rq = F(0)
        if kappa:
            r0, r1 = R(full + (0,), mode), R(full + (1,), mode)
            rq = max(r0, (r0 + r1) / 2) if mode == "causal" else (r0 + r1) / 2
        return pi + (1 - pi) * ((1 - kappa) * rn + kappa * rq)

    rec_c, rec_i = R((), "causal"), R((), "iid")

    # brute force: all 2^K deterministic nulls, vectorised
    def prob(full, P):
        if len(full) >= T:
            return 0.0
        pi, kappa = map(float, policy(full))
        val = (1 - kappa) * prob(full + ("n",), P)
        if kappa:
            p = P[qidx[full]]
            val = val + kappa * ((1 - p) * prob(full + (0,), P) + p * prob(full + (1,), P))
        return pi + (1 - pi) * val

    if K <= 20:
        grid = np.array(list(itertools.product((0.0, 0.5), repeat=K))).T if K else np.zeros((0, 1))
        allp = prob((), grid) if K else np.array([prob((), grid)])
        allp = np.atleast_1d(allp)
        brute = float(allp.max())
        arg = int(np.argmax(allp))
        # exact re-evaluation of the arg-max null
        pstar = {h: (F(1, 2) if grid[i, arg] else F(0)) for h, i in qidx.items()} if K else {}

        def prob_exact(full):
            if len(full) >= T:
                return F(0)
            pi, kappa = policy(full)
            val = (1 - kappa) * prob_exact(full + ("n",))
            if kappa:
                p = pstar[full]
                val += kappa * ((1 - p) * prob_exact(full + (0,)) + p * prob_exact(full + (1,)))
            return pi + (1 - pi) * val

        brute_exact = prob_exact(())
    else:
        brute, brute_exact = float("nan"), None
    # continuous nulls
    rs = np.random.default_rng(seed)
    cont = rs.uniform(0, 0.5, size=(K, 20000)) if K else np.zeros((0, 20000))
    cmax = float(np.max(np.atleast_1d(prob((), cont)))) if K else float(prob((), cont))
    iid = prob((), np.full((K, 1), 0.5)) if K else prob((), np.zeros((0, 1)))
    return {
        "T": T, "B": B, "d": d, "seed": seed, "K_null_infosets": K, "n_nulls": 2**K,
        "recursion_causal": rec_c, "brute_max": brute, "brute_argmax_exact": brute_exact,
        "exact_equal": brute_exact == rec_c, "cont_max": cmax,
        "cont_exceeds": cmax > float(rec_c) + 1e-12,
        "recursion_iid": rec_c if False else rec_i, "iid_null_prob": float(np.atleast_1d(iid)[0]),
    }


def plan_seeing_example():
    """T=2, B=1: query at t=1, promote at t=2 w.p. q_y after label y.  Behavioural (fresh coin at
    t=2) versus a pre-drawn plan that the null can see."""
    q0 = q1 = F(1, 2)
    behavioural = max(q0, (q0 + q1) / 2)
    plan = q0 * q1 * 1 + q0 * (1 - q1) * 1 + (1 - q0) * q1 * F(1, 2)
    return behavioural, plan


if __name__ == "__main__":
    out = []
    worst = 0.0
    for d in (1, 2):
        for (T, B) in [(2, 1), (3, 1), (3, 2), (4, 1), (4, 2), (5, 1)]:
            for s in range(8 if (T, B) != (4, 2) else 4):
                r = run(T, B, d, 1000 * T + 100 * B + 10 * d + s)
                out.append(r)
                gap = abs(r["brute_max"] - float(r["recursion_causal"]))
                worst = max(worst, gap)
                ok = r["exact_equal"] and not r["cont_exceeds"] and abs(
                    r["iid_null_prob"] - float(r["recursion_iid"])) < 1e-12
                print(f"d={d} T={T} B={B} seed={s} K={r['K_null_infosets']:2d} "
                      f"rec={float(r['recursion_causal']):.12f} brute={r['brute_max']:.12f} "
                      f"exact_eq={r['exact_equal']} cont_max={r['cont_max']:.6f} "
                      f"iid_ok={abs(r['iid_null_prob'] - float(r['recursion_iid'])) < 1e-12} {'OK' if ok else 'FAIL'}")
                sys.stdout.flush()
    print("runs", len(out), "all exact-equal:", all(r["exact_equal"] for r in out),
          "any continuous null exceeding recursion:", any(r["cont_exceeds"] for r in out),
          "max |brute-rec| (float):", worst)
    b, p = plan_seeing_example()
    print("plan-seeing example (q0=q1=1/2): behavioural risk", b, "plan-observing null risk", p)
