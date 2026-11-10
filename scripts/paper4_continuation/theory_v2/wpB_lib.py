"""WP B: exact Lagrangian DP for the first-promotion game (pre-promotion plan + optimal continuation).

Lagrangian L_lam(pi) = C(pi) + lam * R_IID(pi). Solved by backward induction over the learner's
information histories (pure plans), for any two-state HMM; works with floats or Fractions.
Conventions follow src/shiftlab/dive/first_promotion_decomposition.py: a label queried at s is
visible from time s+d on; the promotion step pays 1-q + c*query + k, then the exact alternative-only
continuation (rollback / re-promotion allowed) from t+1 with old action 1.

State of the alternative world: unnormalised masses over (S_t, pending), pending = tuple of
(release_time, outcome). Null world: mass lam * 2^-(#released labels) (labels IID Ber(1/2)).
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction as F
from itertools import product


class Model:
    def __init__(self, T, B, d, t01, t10, e0, e1, prior1, c, k, exact=False):
        conv = F if exact else float
        self.T, self.B, self.d = T, B, d
        self.t01, self.t10, self.e0, self.e1 = conv(t01), conv(t10), conv(e0), conv(e1)
        self.prior1, self.c, self.k = conv(prior1), conv(c), conv(k)
        self.exact = exact
        self.one, self.zero, self.half = conv(1), conv(0), conv(1) / 2
        self._post = {}

    # ---------- alternative belief machinery ----------
    def em(self, s):
        return self.e1 if s else self.e0

    def root(self):
        # P(S_1 = 1) = propagate(prior1, 1), as in the repo game
        p = self.prior1 * (self.one - self.t10) + (self.one - self.prior1) * self.t01
        return {(0, ()): self.one - p, (1, ()): p} if p not in (0, 1) else {(int(p == 1), ()): self.one}

    def step(self, t, masses, query):
        """Apply query at t (label joins pending) and the transition to S_{t+1}."""
        out = defaultdict(lambda: self.zero)
        for (s, pend), m in masses.items():
            e = self.em(s)
            outs = ((0, self.one - e), (1, e)) if query else ((None, self.one),)
            for y, my in outs:
                p2 = pend + ((t + self.d, y),) if query else pend
                tr = ((0, self.one - self.t01), (1, self.t01)) if s == 0 else ((0, self.t10), (1, self.one - self.t10))
                for s2, mt in tr:
                    v = m * my * mt
                    if v:
                        out[(s2, p2)] += v
        return dict(out)

    def release(self, t, masses):
        """Split by the label released at time t (at most one per time). Returns [(y or None, masses)]."""
        due = any(pend and pend[0][0] <= t for (_, pend) in masses)
        if not due:
            return [(None, masses)]
        res = []
        for y in (0, 1):
            sub = {}
            for (s, pend), m in masses.items():
                if pend[0][1] == y:
                    sub[(s, pend[1:])] = sub.get((s, pend[1:]), self.zero) + m
            if sub:
                res.append((y, sub))
        return res

    def key(self, masses):
        tot = sum(masses.values())
        if self.exact:
            return tuple(sorted((k, v / tot) for k, v in masses.items()))
        return tuple(sorted((k, round(v / tot, 13)) for k, v in masses.items()))

    # ---------- alternative-only post-promotion DP (normalised beliefs) ----------
    def post_value(self, t, old, b, masses):
        """Optimal alternative cost from time t (after releases at t), per unit alternative mass."""
        tot = sum(masses.values())
        norm = {kk: v / tot for kk, v in masses.items()}
        kk = (t, old, b, self.key(norm))
        if kk in self._post:
            return self._post[kk]
        q = sum(m * self.em(s) for (s, _), m in norm.items())
        best = None
        for a in (0, 1):
            for qq in ((0, 1) if b else (0,)):
                v = (q if a == 0 else self.one - q) + self.c * qq + self.k * (a != old)
                if t < self.T:
                    nxt = self.step(t, norm, qq)
                    for _y, sub in self.release(t + 1, nxt):
                        w = sum(sub.values())
                        v += w * self.post_value(t + 1, a, b - qq, sub)
                if best is None or v < best:
                    best = v
        self._post[kk] = best
        return best

    def promote_value(self, t, b, masses, qq):
        """Alternative mass-weighted cost of promoting at t with query qq (masses unnormalised)."""
        tot = sum(masses.values())
        norm = {kk: v / tot for kk, v in masses.items()}
        q = sum(m * self.em(s) for (s, _), m in norm.items())
        v = self.one - q + self.c * qq + self.k
        if t < self.T:
            nxt = self.step(t, norm, qq)
            for _y, sub in self.release(t + 1, nxt):
                v += sum(sub.values()) * self.post_value(t + 1, 1, b - qq, sub)
        return tot * v


def solve(model, lam, tie="cont"):
    """Lagrangian DP. Returns (J, plan, info) with plan: info-key -> (a, q).

    info-key = (t, queries tuple, released tuple of (query_time, y)). tie in {cont, promote, minR, maxR};
    minR / maxR give the least / largest IID risk over ALL Lagrangian-optimal pure plans (exact mode).
    Also returns per-node (C, R) of the chosen plan: C alt cost, R null promotion prob.
    """
    T, B = model.T, model.B
    lam = F(lam) if model.exact else float(lam)
    plan = {}

    def rec(t, qs, rel, masses, nmass):
        # returns (J, Calt, Rnull_mass) for the subtree (mass-weighted)
        b = B - len(qs)
        options = []
        for a in (1, 0):
            for qq in ((0, 1) if b else (0,)):
                if a == 1:
                    calt = model.promote_value(t, b, masses, qq)
                    options.append((calt + nmass, calt, nmass, (1, qq)))
                    continue
                calt = sum(m * model.em(s) for (s, _), m in masses.items()) + model.c * qq * sum(masses.values())
                J, rn = calt, model.zero
                if t < T:
                    nxt = model.step(t, masses, qq)
                    qs2 = qs + ((t,) if qq else ())
                    for y, sub in model.release(t + 1, nxt):
                        rel2 = rel + (((t + 1 - model.d), y),) if y is not None else rel
                        nm = nmass / 2 if y is not None else nmass
                        j, c_, r_ = rec(t + 1, qs2, rel2, sub, nm)
                        J += j
                        calt += c_
                        rn += r_
                options.append((J, calt, rn, (0, qq)))
        tol = 0 if model.exact else 1e-12
        jmin = min(o[0] for o in options)
        cands = [o for o in options if o[0] <= jmin + tol * (1 + abs(jmin))]
        if tie == "cont":
            cands.sort(key=lambda o: (o[3][0], o[3][1]))  # prefer a=0, then no query
        elif tie == "minR":  # lexicographic: among optimal subplans, least null-promotion mass
            cands.sort(key=lambda o: (o[2], o[3]))
        elif tie == "maxR":
            cands.sort(key=lambda o: (-o[2], o[3]))
        else:
            cands.sort(key=lambda o: (-o[3][0], o[3][1]))
        best = cands[0]
        plan[(t, qs, rel)] = best[3]
        plan.setdefault("_ties", 0)
        if len(cands) > 1:
            plan["_ties"] += 1
        return best[0], best[1], best[2]

    J, C, Rn = rec(1, (), (), model.root(), lam)
    R = Rn / lam if lam else None
    return J, plan, {"C": C, "R": R}


def run_z(plan, model, z):
    """Promotion indicator of a deterministic plan when the j-th queried label is z[j]."""
    qs, rel, j = (), (), 0
    pend = []  # (release_time, query_time, y)
    for t in range(1, model.T + 1):
        for item in list(pend):
            if item[0] == t:
                rel = rel + ((item[1], item[2]),)
                pend.remove(item)
        a, q = plan[(t, qs, rel)]
        if a:
            return 1
        if q:
            pend.append((t + model.d, t, z[j]))
            qs = qs + (t,)
            j += 1
    return 0


def z_monotone(plan, model):
    B = min(model.B, model.T)
    g = {z: run_z(plan, model, z) for z in product((0, 1), repeat=B)}
    for z, v in g.items():
        for i in range(B):
            if z[i] == 0:
                z2 = z[:i] + (1,) + z[i + 1:]
                if v > g[z2]:
                    return False, (z, z2)
    return True, None


def risk_of(plan, model, causal=False):
    """IID risk (or causal sup risk via the endpoint recursion) of a deterministic plan."""
    def rec(t, qs, rel, pend):
        if t > model.T:
            return F(0)
        rel2 = rel
        pend2 = []
        for item in pend:
            if item[0] == t:
                rel2 = rel2 + ((item[1], item[2]),)
            else:
                pend2.append(item)
        # releases at t of unknown labels are handled by branching at query time
        a, q = plan[(t, qs, rel2)]
        if a:
            return F(1)
        if not q:
            return rec(t + 1, qs, rel2, pend2)
        v = [rec(t + 1, qs + (t,), rel2, pend2 + [(t + model.d, t, y)]) for y in (0, 1)]
        return max(v[0], (v[0] + v[1]) / 2) if causal else (v[0] + v[1]) / 2
    return rec(1, (), (), [])
