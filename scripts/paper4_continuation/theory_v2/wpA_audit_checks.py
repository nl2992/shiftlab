"""WP A proof audit: independent exact B=1 premium formula (Theorem N1) and C3' checks.

Independent of theory_C/fu_b1_formula.py: the alternative model, the post-promotion
belief DP and the design gains are re-implemented here from the primitive model
(hidden-path enumeration, exact Fractions). Only gamma_cell (certified LP/FCG) is
imported, as the reference.

Usage (repo root):
  uv run --no-sync python scripts/paper4_continuation/theory_v2/wpA_audit_checks.py random  <out.json> <seed> <n>
  uv run --no-sync python scripts/paper4_continuation/theory_v2/wpA_audit_checks.py c3grid  <out.json> <T,..>
  uv run --no-sync python scripts/paper4_continuation/theory_v2/wpA_audit_checks.py cells   <out.json> <cells.json>
Outputs refuse to overwrite.
"""

from __future__ import annotations

import itertools
import json
import os
import random
import sys
import time
from fractions import Fraction as F
from functools import lru_cache

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "theory_C"))


class B1Model:
    """Exact B=1 design gains, re-derived from the primitive HMM."""

    def __init__(self, T, d, t01, t10, e0, e1, prior, c, k):
        self.T, self.d = T, d
        self.t01, self.t10, self.e = F(t01), F(t10), (F(e0), F(e1))
        self.c, self.k = F(c), F(k)
        prior = F(prior)
        # S_1 is one transition step from prior (matches RegimeModel.propagate(prior, 1)).
        p1 = prior * (1 - self.t10) + (1 - prior) * self.t01
        self.paths = []
        for s in itertools.product((0, 1), repeat=T):
            p = p1 if s[0] else 1 - p1
            for a, b in zip(s, s[1:]):
                if a == 0:
                    p *= self.t01 if b else 1 - self.t01
                else:
                    p *= self.t10 if b == 0 else 1 - self.t10
            if p:
                self.paths.append((s, p))
        self._q = {}
        self._cont = {}

    def q(self, t, obs):
        """P(Y_t = 1 | observed labels obs), obs a frozenset of (time, y); t is 1-based."""
        key = (t, obs)
        if key in self._q:
            return self._q[key]
        num = den = F(0)
        for s, p in self.paths:
            w = p
            for u, y in obs:
                eu = self.e[s[u - 1]]
                w *= eu if y else 1 - eu
            den += w
            num += w * self.e[s[t - 1]]
        val = num / den
        self._q[key] = val
        return val

    def py(self, u, y, obs):
        q = self.q(u, obs)
        return q if y else 1 - q

    def cont(self, t, prev, budget, pending, obs):
        """Min expected cost of steps t..T (post-promotion, any actions, optional query)."""
        if t > self.T:
            return F(0)
        key = (t, prev, budget, pending, obs)
        if key in self._cont:
            return self._cont[key]
        if pending is not None and pending + self.d == t:
            val = sum(
                self.py(pending, y, obs) * self.cont(t, prev, budget, None, obs | {(pending, y)})
                for y in (0, 1)
                if self.py(pending, y, obs)
            )
            self._cont[key] = val
            return val
        qt = self.q(t, obs)
        best = None
        for a in (0, 1):
            for qry in ((0, 1) if budget else (0,)):
                v = (qt if a == 0 else 1 - qt) + self.k * (a != prev) + self.c * qry
                v += self.cont(t + 1, a, budget - qry, t if qry else pending, obs)
                best = v if best is None or v < best else best
        self._cont[key] = best
        return best

    def gains(self):
        T, d = self.T, self.d
        E = frozenset()
        qm = [None] + [self.q(t, E) for t in range(1, T + 1)]
        C0 = sum(qm[1:])
        pre = lambda s: sum(qm[1:s])  # cost of action 0 on steps < s
        # unconditional promotion (risk 1 under every null)
        g_pre = None
        for s in range(1, T + 1):
            base = pre(s) + (1 - qm[s]) + self.k
            opts = [self.cont(s + 1, 1, 1, None, E), self.c + self.cont(s + 1, 1, 0, s, E)]
            v = C0 - (base + min(opts))
            g_pre = v if g_pre is None else max(g_pre, v)
            for tau in range(1, s):  # query earlier, promote before release
                if s < tau + d:
                    v = C0 - (pre(s) + self.c + (1 - qm[s]) + self.k + self.cont(s + 1, 1, 0, tau, E))
                    g_pre = max(g_pre, v)
        designs = {}
        for tau in range(1, T + 1):
            if tau + d > T:
                continue
            r = tau + d
            prefix = sum(qm[1:r]) + self.c
            P, W, N = {}, {}, {}
            for y in (0, 1):
                P[y] = self.py(tau, y, E)
                if not P[y]:
                    W[y] = N[y] = F(0)
                    continue
                ob = frozenset({(tau, y)})
                qy = [None] + [self.q(t, ob) for t in range(1, T + 1)]
                N[y] = sum(qy[r:])
                W[y] = min(
                    sum(qy[r:s]) + (1 - qy[s]) + self.k + self.cont(s + 1, 1, 0, None, ob)
                    for s in range(r, T + 1)
                )
            gz0 = C0 - (prefix + P[0] * W[0] + P[1] * N[1])
            gz1 = C0 - (prefix + P[0] * N[0] + P[1] * W[1])
            gb = C0 - (prefix + P[0] * W[0] + P[1] * W[1])
            designs[tau] = {"P1": P[1], "gz0": gz0, "gz1": gz1, "gboth": gb,
                            "G0": N[0] - W[0], "G1": N[1] - W[1]}
        return C0, g_pre, designs


def n1_formula(m: B1Model, alpha):
    C0, g_pre, D = m.gains()
    alpha = F(alpha)
    cand_c = [F(0), g_pre]
    for v in D.values():
        cand_c += [2 * v["gz1"], v["gz0"], v["gboth"], v["gz0"] + v["gz1"]]
    r_c = max(cand_c)
    gz0max = max([v["gz0"] for v in D.values()], default=F(0))
    r_iid = max(r_c, 2 * gz0max)
    # condition W (corrections file): P1 G1 >= P0 G0 whenever G0 > 0 (best-s version)
    W_ok = all(
        not (v["G0"] > 0) or v["P1"] * v["G1"] >= (1 - v["P1"]) * v["G0"] for v in D.values()
    )
    return {
        "C0": C0, "g_pre": g_pre, "r_c": r_c, "r_iid": r_iid,
        "V_iid": C0 - alpha * r_iid, "V_causal": C0 - alpha * r_c,
        "Gamma": alpha * (r_iid - r_c), "W_bestS": W_ok,
        "designs": {t: {kk: str(vv) for kk, vv in v.items()} for t, v in D.items()},
    }


def certified(T, d, t01, t10, e0, e1, prior, c, k, alpha, force_fcg=False):
    from gamma_lib import gamma_cell
    return gamma_cell(T, 1, d, F(t01), F(t10), F(e0), F(e1), F(prior), F(c), F(k), F(alpha),
                      force_fcg=force_fcg)


def check_cell(T, d, t01, t10, e0, e1, prior, c, k, alpha, force_fcg=False):
    t0 = time.time()
    m = B1Model(T, d, t01, t10, e0, e1, prior, c, k)
    f = n1_formula(m, alpha)
    g = certified(T, d, t01, t10, e0, e1, prior, c, k, alpha, force_fcg)
    LI, UI = F(g["L_IID"]), F(g["U_IID"])
    LC, UC = F(g["L_causal"]), F(g["U_causal"])
    glo, ghi = F(g["Gamma_lo"]), F(g["Gamma_hi"])
    tol = F(1, 10**9)  # dual bounds are rationalised floats
    ok_iid = LI - tol <= f["V_iid"] <= UI + tol
    ok_c = LC - tol <= f["V_causal"] <= UC + tol
    ok_g = glo - tol <= f["Gamma"] <= ghi + tol
    return {
        "cell": dict(T=T, d=d, t01=str(F(t01)), t10=str(F(t10)), e0=str(F(e0)), e1=str(F(e1)),
                     prior=str(F(prior)), c=str(F(c)), k=str(F(k)), alpha=str(F(alpha))),
        "tp2": F(t01) + F(t10) <= 1,
        "formula": {kk: (str(vv) if isinstance(vv, F) else vv) for kk, vv in f.items()},
        "cert": {"L_IID": str(LI), "U_IID": str(UI), "L_causal": str(LC), "U_causal": str(UC),
                 "Gamma_lo": str(glo), "Gamma_hi": str(ghi), "src": g["V_causal_source"]},
        "ok_iid": ok_iid, "ok_causal": ok_c, "ok_gamma": ok_g,
        "Gamma_formula_f": float(f["Gamma"]), "W_bestS": f["W_bestS"],
        "secs": round(time.time() - t0, 2),
    }


def rand_frac(rng, lo, hi, den):
    while True:
        v = F(rng.randint(0, den), den)
        if lo < v < hi:
            return v


def random_cells(seed, n):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        T = rng.choice([2, 3, 4, 5, 5, 6, 6])
        d = rng.choice([1, 1, 2, 2, 3])
        den = rng.choice([10, 20, 7, 12])
        t01 = F(rng.randint(0, den), den)
        t10 = F(rng.randint(0, den), den)
        e0 = rand_frac(rng, 0, F(1, 2), rng.choice([20, 10, 8, 100]))
        e1 = rand_frac(rng, F(1, 2), 1, rng.choice([20, 10, 8, 100]))
        prior = rng.choice([F(0), F(1), F(1, 2), F(1, 4), F(3, 4), F(rng.randint(0, 9), 9)])
        c = rng.choice([F(0), F(1, 100), F(1, 20), F(1, 10)])
        k = rng.choice([F(0), F(1, 50), F(1, 10), F(1, 4)])
        alpha = rng.choice([F(1, 20), F(1, 10), F(1, 4), F(1, 2)])
        out.append((T, d, t01, t10, e0, e1, prior, c, k, alpha))
    return out


def c3_closed(T, e, k, c, alpha):
    g = (1 - 2 * F(e)) ** 2
    return F(alpha) * min((g - F(k)) / 2 - F(c), g - 2 * F(k)), g


def save(path, payload):
    if os.path.exists(path):
        print(f"refusing to overwrite {path}", file=sys.stderr)
        sys.exit(2)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=1, default=str)
    print("wrote", path)


def main():
    mode, out = sys.argv[1], sys.argv[2]
    if os.path.exists(out):
        print(f"refusing to overwrite {out}", file=sys.stderr)
        sys.exit(2)
    rows = []
    if mode == "random":
        seed, n = int(sys.argv[3]), int(sys.argv[4])
        for cell in random_cells(seed, n):
            try:
                rows.append(check_cell(*cell))
            except Exception as exc:  # record, never hide
                rows.append({"cell": [str(x) for x in cell], "error": repr(exc)})
    elif mode == "c3grid":
        Ts = [int(x) for x in sys.argv[3].split(",")]
        for T in Ts:
            for e in (F(1, 20), F(1, 10), F(1, 4), F(3, 10)):
                for k in (F(0), F(1, 20), F(1, 10), F(1, 4)):
                    for c in (F(0), F(1, 100), F(1, 50)):
                        for a in (F(1, 20), F(1, 10), F(1, 4), F(1, 2)):
                            try:
                                r = check_cell(T, 1, 1, 1, e, 1 - e, F(1, 2), c, k, a)
                            except Exception as exc:
                                rows.append({"cell": [T, str(e), str(k), str(c), str(a)], "error": repr(exc)})
                                continue
                            cf, g = c3_closed(T, e, k, c, a)
                            hyp = g > 2 * k and c <= (g - k) / 2
                            r["c3_hyp"] = hyp
                            r["c3_closed"] = str(cf)
                            r["c3_ok"] = (F(r["cert"]["Gamma_lo"]) - F(1, 10**9) <= cf
                                          <= F(r["cert"]["Gamma_hi"]) + F(1, 10**9))
                            rows.append(r)
    elif mode == "cells":
        for cell in json.load(open(sys.argv[3])):
            cell = [F(x) if isinstance(x, str) else x for x in cell]
            force = bool(cell[10]) if len(cell) > 10 else False
            try:
                rows.append(check_cell(*cell[:10], force_fcg=force))
            except Exception as exc:
                rows.append({"cell": [str(x) for x in cell], "error": repr(exc)})
    ok = [r for r in rows if "error" not in r]
    summary = {
        "n": len(rows), "errors": len(rows) - len(ok),
        "ok_gamma": sum(r["ok_gamma"] for r in ok), "ok_iid": sum(r["ok_iid"] for r in ok),
        "ok_causal": sum(r["ok_causal"] for r in ok),
        "gamma_pos_formula": sum(r["Gamma_formula_f"] > 0 for r in ok),
        "gamma_pos_cert": sum(F(r["cert"]["Gamma_lo"]) > 0 for r in ok),
        "non_tp2": sum(not r["tp2"] for r in ok),
    }
    if mode == "c3grid":
        h = [r for r in ok if r.get("c3_hyp")]
        summary["c3_hyp"] = len(h)
        summary["c3_ok"] = sum(r["c3_ok"] for r in h)
        summary["c3_ok_outside_hyp"] = sum(r["c3_ok"] for r in ok if not r.get("c3_hyp"))
    print(json.dumps(summary))
    save(out, {"argv": sys.argv, "summary": summary, "rows": rows})


if __name__ == "__main__":
    main()
