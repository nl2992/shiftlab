"""Exact evaluator and the standard IID-calibrated promotion policies (see docs/.../iid_failure/PROTOCOL.md).

Cost model = the RB-DP solver's (src/shiftlab/paper4/risk_budget_dp_fast.py): step cost pos(beta) = P(Y_t=1 | beta)
before promotion, c per query, k per switch; after promotion the solver's own greedy-on-grid-J continuation
(evaluated on exact beliefs), reached through ``Post.P(t, n, beta)`` = cost of promoting at t with n queries left.
Delay d = 1: a label queried at t is seen before the decision at t+1.

A policy is a small object with
    s0                      initial (hashable) policy state
    act(t, n, s)  -> (pi, kappa)   promote prob; if not promoting, query prob (0 when n == 0)
    step(s, t, n, ev)       next state after 'n' (no query) or label 0 / 1
Risk recursion = PROOFS.md Lemma A (m = max(a,(a+b)/2) causal; (a+b)/2 IID), memoised on (t, n, s).
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np

sys.setrecursionlimit(20000)
EPS = 1e-10  # tie tolerance on thresholds
RD = 13  # rounding digits for belief states


@dataclass(frozen=True)
class Chain:
    t01: float
    t10: float
    e0: float
    e1: float
    prior1: float
    T: int
    B: int
    c: float = 0.01
    k: float = 0.0

    def prop(self, b):
        return self.t01 * (1.0 - b) + (1.0 - self.t10) * b

    def pos(self, b):
        return self.e0 + (self.e1 - self.e0) * b

    def beta1(self):
        return round(self.prop(self.prior1), RD)

    def branches(self, b):
        """(p0, p1, belief at next decision after label 0, after label 1, belief after no query)."""
        pos = self.pos(b)
        b1 = self.prop(b * self.e1 / pos)
        b0 = self.prop(b * (1.0 - self.e1) / (1.0 - pos))
        return 1.0 - pos, pos, round(b0, RD), round(b1, RD), round(self.prop(b), RD)

    def C0(self):
        b, tot = self.beta1(), 0.0
        for _ in range(self.T):
            tot += self.pos(b)
            b = self.prop(b)
        return tot


class Post:
    """Cost of promoting now, from the solver's post-promotion tables (exact evaluation on exact beliefs)."""

    def __init__(self, ch: Chain):
        from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, _Evaluator, _Solver

        cfg = RBDPConfig(T=ch.T, B=ch.B, t01=ch.t01, t10=ch.t10, e0=ch.e0, e1=ch.e1, prior1=ch.prior1,
                         c=ch.c, k=ch.k, alpha=0.1, n_beta=201, w_step_div=1, mode="causal")
        self.s = _Solver(cfg)
        self.s._build_post()
        self.ev = _Evaluator(self.s)
        self.ch = ch
        self.cache = {}

    def P(self, t, n, b):
        key = (t, n, round(b, RD))
        if key not in self.cache:
            from shiftlab.paper4.risk_budget_dp_fast import _Maps

            mp = _Maps(self.s, np.array([b]))
            _, pq = self.s._promote_cost(n, mp, self.s.J[t + 1])
            self.cache[key] = self.ev._promote_exact(t, n, {"mp": mp, "pq": bool(pq[0])})
        return self.cache[key]


# ------------------------------------------------------------------------------ evaluator
def risks(pol, ch: Chain):
    """Exact (IID risk, causal worst-case risk) by Lemma A over the policy's state tree."""
    memo = {}
    T = ch.T

    def R(t, n, s):
        if t > T:
            return (0.0, 0.0)
        key = (t, n, s)
        hit = memo.get(key)
        if hit is not None:
            return hit
        pi, kap = pol.act(t, n, s)
        assert n > 0 or kap == 0
        ni = nc = 0.0
        if pi >= 1:
            memo[key] = (1.0, 1.0)
            return memo[key]
        if kap < 1:
            a = R(t + 1, n, pol.step(s, t, n, "n"))
            ni += (1 - kap) * a[0]
            nc += (1 - kap) * a[1]
        if kap > 0:
            r0 = R(t + 1, n - 1, pol.step(s, t, n, 0))
            r1 = R(t + 1, n - 1, pol.step(s, t, n, 1))
            ni += kap * 0.5 * (r0[0] + r1[0])
            nc += kap * max(r0[1], 0.5 * (r0[1] + r1[1]))
        out = (pi + (1 - pi) * ni, pi + (1 - pi) * nc)
        memo[key] = out
        return out

    return R(1, ch.B, pol.s0)


def cost(pol, ch: Chain, post: Post):
    """Expected cost under the alternative HMM, same accounting as the solver."""
    T, c = ch.T, ch.c
    memo = {}

    def C(t, n, s, b):
        if t > T:
            return 0.0
        key = (t, n, s, b)
        hit = memo.get(key)
        if hit is not None:
            return hit
        pi, kap = pol.act(t, n, s)
        val = 0.0
        if pi > 0:
            val += pi * post.P(t, n, b)
        if pi < 1:
            p0, p1, b0, b1, bn = ch.branches(b)
            rest = ch.pos(b)
            if kap < 1:
                rest += (1 - kap) * (C(t + 1, n, pol.step(s, t, n, "n"), bn) if t < T else 0.0)
            if kap > 0:
                rest += kap * c
                if t < T:
                    rest += kap * (p0 * C(t + 1, n - 1, pol.step(s, t, n, 0), b0)
                                   + p1 * C(t + 1, n - 1, pol.step(s, t, n, 1), b1))
            val += (1 - pi) * rest
        memo[key] = val
        return val

    return C(1, ch.B, pol.s0, ch.beta1())


def walk_states(pol, ch: Chain):
    """All (t, n, s) reachable ignoring promotion (superset of the reachable pre-promotion states)."""
    seen = set()
    stack = [(1, ch.B, pol.s0)]
    while stack:
        t, n, s = stack.pop()
        if t > ch.T or (t, n, s) in seen:
            continue
        seen.add((t, n, s))
        _, kap = pol.act(t, n, s)
        if kap < 1:
            stack.append((t + 1, n, pol.step(s, t, n, "n")))
        if kap > 0:
            for y in (0, 1):
                stack.append((t + 1, n - 1, pol.step(s, t, n, y)))
    return seen


# ------------------------------------------------------------------------------ policies
class P1Fixed:
    """Fixed-sample binomial test: query t = 1..B, promote at B+1 if ones >= kk (w.p. theta if ones == kk - 1)."""
    name = "P1_fixed_sample"
    s0 = 0

    def __init__(self, ch, kk, theta):
        self.ch, self.kk, self.theta = ch, kk, theta

    def act(self, t, n, s):
        B = self.ch.B
        if t <= B:
            return 0.0, 1.0
        if t == B + 1:
            if s >= self.kk:
                return 1.0, 0.0
            if s == self.kk - 1:
                return self.theta, 0.0
        return 0.0, 0.0

    def step(self, s, t, n, ev):
        return s + (1 if ev == 1 else 0)

    def param(self):
        return {"k": self.kk, "theta": self.theta}


def calibrate_p1(ch, alpha):
    B = ch.B
    pm = [math.comb(B, j) / 2 ** B for j in range(B + 1)]
    kk = next(k for k in range(0, B + 2) if sum(pm[k:]) <= alpha + 1e-15)
    tail = sum(pm[kk:])
    theta = 0.0 if abs(tail - alpha) < 1e-15 else (alpha - tail) / pm[kk - 1]
    return P1Fixed(ch, kk, theta)


class P2Sprt:
    """Count-based Wald SPRT, H1: IID Bernoulli(e1) vs H0: 1/2. Query every step until budget used;
    promote when LLR of released labels > tau (w.p. theta on a tie). Decisions only while new labels arrive
    (t <= B+1); the lower boundary is not used (it would only stop)."""
    name = "P2_count_sprt"
    s0 = 0

    def __init__(self, ch, tau, theta):
        self.ch, self.tau, self.theta = ch, tau, theta
        self.l1, self.l0 = math.log(2 * ch.e1), math.log(2 * (1 - ch.e1))

    def llr(self, n, s):
        m = self.ch.B - n
        return s * self.l1 + (m - s) * self.l0

    def act(self, t, n, s):
        B = self.ch.B
        if t > B + 1:
            return 0.0, 0.0
        z = self.llr(n, s)
        kap = 1.0 if n > 0 else 0.0
        if z > self.tau + EPS:
            return 1.0, kap
        if abs(z - self.tau) <= EPS:
            return self.theta, kap
        return 0.0, kap

    def step(self, s, t, n, ev):
        return s + (1 if ev == 1 else 0)

    def levels(self):
        B = self.ch.B
        return sorted({round(j * self.l1 + (m - j) * self.l0, 10) for m in range(B + 1) for j in range(m + 1)})

    def param(self):
        return {"tau_llr": self.tau, "theta": self.theta}


class P3Filter:
    """HMM-filter threshold: query every step until budget used; promote when beta_t > tau (w.p. theta on tie)."""
    name = "P3_hmm_filter"

    def __init__(self, ch, tau, theta):
        self.ch, self.tau, self.theta = ch, tau, theta
        self.s0 = ch.beta1()

    def _kap(self, t, n, s):
        return 1.0 if n > 0 else 0.0

    def act(self, t, n, s):
        kap = self._kap(t, n, s)
        if s > self.tau + EPS:
            return 1.0, kap
        if abs(s - self.tau) <= EPS:
            return self.theta, kap
        return 0.0, kap

    def step(self, s, t, n, ev):
        p0, p1, b0, b1, bn = self.ch.branches(s)
        return bn if ev == "n" else (b1 if ev == 1 else b0)

    def param(self):
        return {"tau_beta": self.tau, "theta": self.theta}


class P4Voi(P3Filter):
    """Myopic VOI design: query iff one-step VOI > c0 (c0 = 0.01) and budget left and t < T; promote iff beta > tau.
    VOI(beta) = V(prop(beta)) - sum_y P(y) V(beta_y'), V(b) = min(pos(b), 1 - pos(b)) (next-step stay/switch cost)."""
    name = "P4_myopic_voi"
    C_VOI = 0.01

    def _kap(self, t, n, s):
        if n == 0 or t >= self.ch.T:
            return 0.0
        ch = self.ch
        V = lambda b: min(ch.pos(b), 1.0 - ch.pos(b))  # noqa: E731
        p0, p1, b0, b1, bn = ch.branches(s)
        voi = V(ch.prop(s)) - (p0 * V(b0) + p1 * V(b1))
        return 1.0 if voi > self.C_VOI else 0.0


def calibrate_threshold(make, levels, ch, alpha):
    """Smallest level tau with IID risk(promote iff z > tau) <= alpha, then tie-randomise to hit alpha exactly."""
    lv = list(levels)
    rs = lambda i, th: risks(make(lv[i], th), ch)[0]  # noqa: E731
    lo, hi = 0, len(lv) - 1  # R_s(hi) = 0 <= alpha
    if rs(lo, 0.0) <= alpha + 1e-15:
        hi = lo
    else:
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if rs(mid, 0.0) <= alpha + 1e-15:
                hi = mid
            else:
                lo = mid
    i = hi
    r0 = rs(i, 0.0)
    if abs(r0 - alpha) < 1e-13 or r0 > alpha:
        return make(lv[i], 0.0)
    a, b = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (a + b)
        if rs(i, mid) <= alpha:
            a = mid
        else:
            b = mid
    return make(lv[i], a)


def calibrate_p2(ch, alpha):
    proto = P2Sprt(ch, 0.0, 0.0)
    return calibrate_threshold(lambda tau, th: P2Sprt(ch, tau, th), proto.levels(), ch, alpha)


def _belief_levels(cls, ch):
    pol = cls(ch, 2.0, 0.0)
    return sorted({round(s, 10) for (_, _, s) in walk_states(pol, ch)})


def calibrate_p3(ch, alpha):
    return calibrate_threshold(lambda tau, th: P3Filter(ch, tau, th), _belief_levels(P3Filter, ch), ch, alpha)


def calibrate_p4(ch, alpha):
    return calibrate_threshold(lambda tau, th: P4Voi(ch, tau, th), _belief_levels(P4Voi, ch), ch, alpha)


# ------------------------------------------------------------------------------ e-process gate (policy 6)
class GatePolicy:
    """Cost-optimal controller subject to the fixed-bet e-process gate (stake 1: label 1 doubles wealth, label 0
    zeroes it; capped at th; promotion allowed only at wealth th). Float re-implementation of
    shiftlab.dive.eprocess_gated_planner.EProcessGatedPlanner.solve_gated (checked against it in crosscheck.py)."""
    name = "P6_eprocess_gate"

    def __init__(self, ch: Chain, post: Post, th: int):
        self.ch, self.post, self.th = ch, post, th
        self.s0 = (ch.beta1(), 1)
        self.dec = {}
        self.val = {}
        self.cost_gate = self._G(1, ch.B, ch.beta1(), 1)

    def _upd(self, w, y):
        if w >= self.th:
            return self.th
        return min(self.th, 2 * w) if y == 1 else 0

    def _G(self, t, n, b, w):
        if t > self.ch.T:
            return 0.0
        key = (t, n, b, w)
        if key in self.val:
            return self.val[key]
        ch = self.ch
        p0, p1, b0, b1, bn = ch.branches(b)
        best, choice = None, None
        for q in ((0, 1) if (n > 0 and t < ch.T) else (0,)):
            v = ch.pos(b) + ch.c * q
            if t < ch.T:
                if q:
                    v += p0 * self._G(t + 1, n - 1, b0, self._upd(w, 0)) + p1 * self._G(t + 1, n - 1, b1, self._upd(w, 1))
                else:
                    v += self._G(t + 1, n, bn, w)
            if best is None or v < best:
                best, choice = v, (0, q)
        if w >= self.th:
            v = self.post.P(t, n, b)
            if v < best:
                best, choice = v, (1, 0)
        self.val[key] = best
        self.dec[key] = choice
        return best

    def act(self, t, n, s):
        b, w = s
        a, q = self.dec[(t, n, b, w)]
        return (1.0, 0.0) if a else (0.0, float(q))

    def step(self, s, t, n, ev):
        b, w = s
        p0, p1, b0, b1, bn = self.ch.branches(b)
        if ev == "n":
            return (bn, w)
        return (b1, self._upd(w, 1)) if ev == 1 else (b0, self._upd(w, 0))


def policy6(ch, post, alpha):
    """Best (lowest repaired cost) of th in {2,4,..,2^B}; activation a = min(1, alpha*th) mixes with never-promote."""
    best = None
    C0 = ch.C0()
    for m in range(1, ch.B + 1):
        th = 2 ** m
        g = GatePolicy(ch, post, th)
        ri, rc = risks(g, ch)
        act = min(1.0, alpha * th)
        cg = cost(g, ch, post)
        rec = dict(th=th, activation=act, risk_iid=act * ri, risk_causal=act * rc, ville_bound=act / th,
                   cost=act * cg + (1 - act) * C0, cost_gate_unrepaired=cg)
        if best is None or rec["cost"] < best["cost"]:
            best = rec
    return best
