"""Reduced exact dynamic program for budgeted, delayed, reversible model switching.

See docs/paper1_scale25/THEORETICAL_ANALYSIS.md for the model, the Bellman recursion and the
status of every claim (what is exact, what is numerical, what is only a sanity check).

Model (stationary case, exact up to floating point)
  * Two frozen predictors; every step is a *disagreement event* (the only events carrying
    paired information), so a step is one unit of decision time.
  * p = P(challenger correct | disagreement) is drawn once from a prior and fixed. Deploying the
    incumbent (index 0) costs 1[challenger correct] on a step, deploying the challenger costs
    1[incumbent correct].
  * Released labels are the only evidence: a bought label of step s is released at the start of
    step s + d, and reveals the outcome of step s. Evidence is the pair (k, n): k challenger wins in
    n released labels. Pending outcomes need not be tracked (exchangeability: the next released
    outcome is Bernoulli(posterior mean) given the released labels), only WHEN labels are due:
    a d-bit queue marks the steps at which a purchase is in flight.
  * Hard budget B (labels bought, whether or not released); price cq per label; switching cost cs
    per change of deployment; at every step the policy may change the deployment (after the
    release at that step) and then buy the step's label.
  * Cost = sum of expected step losses + cq * labels + cs * switches, minimised in expectation
    over the prior. Value is exact: backward induction over (dep, k, n, queue).

State size: 2 x (B+1)^2 x 2^d, one layer in memory. The expected loss of a step uses the posterior
mean given RELEASED labels only (the decision-time information), which is exact because the step
loss is linear in the Bernoulli outcome and the outcome is independent of the policy's information
given p; averaging over the posterior of p at decision time is therefore the correct conditional
expectation.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
from scipy.stats import beta as _beta
from scipy.stats import norm as _norm

ROOT = Path(__file__).resolve().parents[3]
S60 = ROOT / "scripts/paper1_eqsdp/search60"
if str(S60) not in sys.path:
    sys.path.insert(0, str(S60))
if str(S60.parent) not in sys.path:
    sys.path.insert(0, str(S60.parent))


@dataclass(frozen=True)
class Inst:
    T: int = 160
    B: int = 24
    d: int = 6
    cs: float = 5.0
    cq: float = 0.05
    prior: tuple = ("beta", 1.0, 1.0)  # ("beta", a, b) or ("points", (p1, p2, ...), (w1, w2, ...))
    name: str = ""

    def means(self) -> np.ndarray:
        """Posterior mean of p given (k, n): array (B+2, B+2) indexed [k, n]."""
        K = self.B + 2
        k = np.arange(K)[:, None].astype(float)
        n = np.arange(K)[None, :].astype(float)
        if self.prior[0] == "beta":
            a, b = self.prior[1], self.prior[2]
            return (k + a) / (n + a + b)
        ps, ws = np.array(self.prior[1], float), np.array(self.prior[2], float)
        ll = (
            np.log(ws)[None, None, :]
            + k[..., None] * np.log(ps)
            + (n - k)[..., None] * np.log1p(-ps)
        )
        ll -= ll.max(-1, keepdims=True)
        w = np.exp(ll)
        w /= w.sum(-1, keepdims=True)
        return (w * ps).sum(-1)

    def prior_sample(self, rng, size):
        if self.prior[0] == "beta":
            return rng.beta(self.prior[1], self.prior[2], size)
        return rng.choice(
            np.array(self.prior[1]), size=size, p=np.array(self.prior[2]) / sum(self.prior[2])
        )

    def oracle_cost(self) -> float:
        """E[ T * min(p, 1-p) + cs * 1{best is the challenger} ] with p known and no labels."""
        rng = np.random.default_rng(0)
        p = self.prior_sample(rng, 400_000)
        return float(np.mean(self.T * np.minimum(p, 1 - p) + self.cs * (p > 0.5)))


def _popcount(n: int) -> np.ndarray:
    x = np.arange(1 << n) if n > 0 else np.zeros(1, int)
    return np.array([i.bit_count() for i in x])


class Layout:
    """Index helpers shared by the solver and the evaluator."""

    def __init__(self, inst: Inst):
        self.I = inst
        d, B = inst.d, inst.B
        self.Q = 1 << d
        self.QR = 1 << (d - 1)
        self.K = B + 2  # k and n axes padded by one
        self.m = inst.means()
        self.pop_r = _popcount(d - 1)
        self.qr = np.arange(self.QR)
        self.i0 = self.qr << 1
        self.i1 = self.i0 | 1
        q = np.arange(self.Q)
        self.oldest = (q >> (d - 1)) & 1
        self.qr_of_q = q & (self.QR - 1)
        n = np.arange(self.K)
        # remaining budget after release when n labels are released and pop_r are in flight
        self.brem = B - n[:, None] - self.pop_r[None, :]  # (K, QR)

    def release(self, W: np.ndarray) -> np.ndarray:
        """Expectation over the label released at the start of the step.

        W[dep, k, n, qr, aux] is the value after release. Returns V[dep, k, n, q, aux].
        """
        Kx = self.K
        m = self.m[:, :, None, None]  # (K, K, 1, 1) [k, n]
        Wk1 = np.zeros_like(W)
        Wk1[:, :-1, :-1] = W[:, 1:, 1:]  # outcome 1: (k+1, n+1)
        Wk0 = np.zeros_like(W)
        Wk0[:, :, :-1] = W[:, :, 1:]  # outcome 0: (k, n+1)
        Wrel = m[None] * Wk1 + (1 - m[None]) * Wk0  # (2, K, K, QR, A)
        out = np.empty(W.shape[:3] + (self.Q,) + W.shape[4:])
        for q in range(self.Q):
            out[:, :, :, q] = (
                Wrel[:, :, :, self.qr_of_q[q]] if self.oldest[q] else W[:, :, :, self.qr_of_q[q]]
            )
        del Kx
        return out


def solve_optimal(inst: Inst, want_policy: bool = False, hook=None):
    """Backward induction. Returns V0 (value at (dep 0, k 0, n 0, empty queue)) and optionally policies."""
    L = Layout(inst)
    T, d, cs, cq = inst.T, inst.d, inst.cs, inst.cq
    K = L.K
    Lm = np.stack([L.m, 1 - L.m])  # (2, K, K) expected step loss by deployed model
    V = np.zeros((2, K, K, L.Q, 1))
    pol = {}
    for t in range(T - 1, -1, -1):
        c0 = V[:, :, :, L.i0, 0]  # (2, K, K, QR)
        c1 = V[:, :, :, L.i1, 0] + cq
        feas = (L.brem >= 1) & (t + d <= T - 1)  # (K, QR)
        buy = feas[None, None] & (c1 < c0)
        cont = np.where(buy, c1, c0)
        if hook is not None:
            hook(t, c0, c1, feas)
        G = Lm[..., None] + cont  # (2, K, K, QR)
        W = np.minimum(G, cs + G[::-1])
        V = L.release(W[..., None])
        if want_policy:
            sw = (cs + G[::-1]) < G  # switch from dep to the other model
            pol[t] = {"buy": buy, "switch": sw}
    return float(V[0, 0, 0, 0, 0]), (pol if want_policy else None)


# ----------------------------------------------------------------------------------- controllers
@dataclass
class Ctrl:
    """Reduced counterparts of the panel's decision rules (stationary, lambda = 1, rate known = 1)."""

    kind: str = (
        "beta"  # "beta" (EQSDp quantile) or "wald" (normal lower bound on the same posterior)
    )
    gamma: float = 0.3
    cutoff_H: int | None = None  # no purchase when t + d > T - H
    e48: dict | None = None  # {"disc":.5,"look":int,"hazard":.002}
    f60: dict | None = None  # {"bundle":2,"horizon":int,"hazard":.002}
    p_min: float = 0.05
    name: str = ""
    rate_mode: str = (
        "known"  # "known": r = 1 (every step is a disagreement); "estimated": (t+5)/(t+20)
    )


def rate_of(c: Ctrl, t: int) -> float:
    """Disagreement-rate estimate used by the panel's controllers (controls.py pacer prior 0.25 x 20)."""
    return 1.0 if c.rate_mode == "known" else (t + 5.0) / (t + 20.0)


def _adv(mu, dep):
    return (2 * mu - 1) if dep == 0 else (1 - 2 * mu)


@cache
def _quant(kind, gamma, dep, k, n):
    a, b = k + 1.0, n - k + 1.0
    mu = a / (a + b)
    if kind == "beta":
        return float(_beta.ppf(gamma if dep == 0 else 1 - gamma, a, b))
    z = _norm.ppf(1 - gamma)
    sd = math.sqrt(mu * (1 - mu) / (a + b + 1))
    return mu - z * sd if dep == 0 else mu + z * sd


def switch_table(inst: Inst, c: Ctrl, t: int, L: Layout) -> np.ndarray:
    """S[dep, k, n]: switch after the release at step t."""
    K = L.K
    S = np.zeros((2, K, K), bool)
    for n in range(inst.B + 1):
        for k in range(n + 1):
            mu = (k + 1.0) / (n + 2.0)
            for dep in (0, 1):
                q = _quant(c.kind, c.gamma, dep, k, n)
                fire = _adv(q, dep) * rate_of(c, t) * (inst.T - t) > inst.cs
                if fire and c.e48 is not None:
                    H = max(0, inst.T - t - c.e48["look"])
                    fire = c.e48["disc"] * _adv(mu, dep) * rate_of(c, t) * H > inst.cs
                S[dep, k, n] = fire
    return S


def _price(inst, c, t, rem):
    t_end = (inst.T - c.cutoff_H - inst.d + 1) if c.cutoff_H is not None else inst.T - inst.d
    ahead = (inst.B - rem) / inst.B - min(1.0, t / max(1, t_end))
    return inst.cq * (1.0 + 20.0 * max(0.0, ahead)), t_end


def buy_table(inst: Inst, c: Ctrl, t: int, L: Layout):
    """(parent, force)[dep', k, n, qr, aux]: the parent's purchase probability and the F60 force flag."""
    from modules_E import surv, voi

    T, d, B = inst.T, inst.d, inst.B
    A = c.f60["bundle"] if c.f60 else 1
    K = L.K
    Pp = np.zeros((2, K, K, L.QR, A))
    Pf = np.zeros((2, K, K, L.QR, A))
    closed = c.cutoff_H is not None and t + d > T - c.cutoff_H
    if t + d > T - 1:
        return Pp, Pf
    for pend in range(d):
        qmask = L.pop_r == pend
        for n in range(B + 1 - pend):
            rem = B - n - pend
            if rem <= 0:
                continue
            paced = min(max(rem / max(rate_of(c, t) * (T - t), 1e-9), c.p_min), 1.0)
            price, t_end = _price(inst, c, t, rem)
            used = (B - rem) / B
            pace_ok = used <= 0.25 + 0.7 * min(1.0, t / max(1, t_end))
            for k in range(n + 1):
                a, b = k + 1.0, n - k + 1.0
                for dep in (0, 1):
                    veto = False
                    if c.e48 is not None:
                        H = T - t - d - c.e48["look"]
                        Hx = max(0.0, H) * surv(H, c.e48["hazard"])
                        veto = (
                            c.e48["disc"] * voi(a, b, pend, 1, dep, rate_of(c, t), Hx, inst.cs)
                            < price
                        )
                    Pp[dep, k, n][qmask] = 0.0 if (closed or veto) else paced
                    if c.f60 is not None and not closed and pace_ok:
                        bn, hz = c.f60["bundle"], c.f60["hazard"]
                        H = min(T - t - d, c.f60["horizon"])
                        fire = (
                            voi(a, b, pend, bn, dep, rate_of(c, t), H * surv(H, hz), inst.cs)
                            > bn * price
                        )
                        for aux in range(A):
                            if aux > 0 or fire:
                                Pf[dep, k, n][np.ix_(qmask, [aux])] = 1.0
    return Pp, Pf


def evaluate(inst: Inst, c: Ctrl):
    """Exact expected cost of controller ``c`` on the reduced model (policy evaluation)."""
    L = Layout(inst)
    T, cs, cq = inst.T, inst.cs, inst.cq
    K = L.K
    A = c.f60["bundle"] if c.f60 else 1
    Lm = np.stack([L.m, 1 - L.m])
    V = np.zeros((2, K, K, L.Q, A))
    aux_buy = (
        np.array([(a - 1) if a > 0 else (A - 1) for a in range(A)]) if A > 1 else np.zeros(1, int)
    )
    for t in range(T - 1, -1, -1):
        S = switch_table(inst, c, t, L)  # (2, K, K)
        Pp, Pf = buy_table(inst, c, t, L)  # (2, K, K, QR, A)
        c0 = V[:, :, :, L.i0, :]  # (2, K, K, QR, A) no purchase, aux unchanged
        c1p = V[:, :, :, L.i1, :] + cq  # parent purchase, aux unchanged
        c1f = V[:, :, :, L.i1, :][..., aux_buy] + cq  # forced purchase, packet counter advances
        cont = Pf * c1f + (1 - Pf) * (Pp * c1p + (1 - Pp) * c0)
        G = Lm[..., None, None] + cont  # (2, K, K, QR, A) value if deployed model = first axis
        # post-release switch: dep -> 1-dep if S[dep]; cost cs
        W = np.where(S[..., None, None], cs + G[::-1], G)
        V = L.release(W)
    return float(V[0, 0, 0, 0, 0])


# ----------------------------------------------------------------------------- Monte Carlo check
def simulate_table_policy(inst: Inst, c: Ctrl | None, n_ep: int, seed: int = 0):
    """Direct simulation of the reduced model under controller ``c`` (c=None -> the optimal policy).

    Independent of the backward recursion: draws p from the prior, plays steps, applies the same
    switch/buy tables. Used only to validate the exact recursion.
    """
    rng = np.random.default_rng(seed)
    L = Layout(inst)
    T, d = inst.T, inst.d
    A = c.f60["bundle"] if (c and c.f60) else 1
    if c is None:
        _, pol = solve_optimal(inst, want_policy=True)
    else:
        tabs = {t: (switch_table(inst, c, t, L), *buy_table(inst, c, t, L)) for t in range(T)}
    tot = np.zeros(n_ep)
    for e in range(n_ep):
        p = inst.prior_sample(rng, 1)[0]
        dep, k, n, aux = 0, 0, 0, 0
        queue: dict[int, int] = {}
        cost = 0.0
        for t in range(T):
            if t - d in queue:
                x = queue.pop(t - d)
                k, n = k + x, n + 1
            qr = 0
            for s_ in queue:
                qr |= 1 << (t - 1 - s_)
            if c is None:
                sw = pol[t]["switch"][dep, k, n, qr]
            else:
                sw = tabs[t][0][dep, k, n]
            if sw:
                dep, cost = 1 - dep, cost + inst.cs
            x_step = rng.random() < p  # challenger correct
            cost += float(x_step) if dep == 0 else float(not x_step)
            if c is None:
                buy = bool(pol[t]["buy"][dep, k, n, qr])
                forced = False
            else:
                pp_, pf_ = tabs[t][1][dep, k, n, qr, aux], tabs[t][2][dep, k, n, qr, aux]
                forced = pf_ > 0
                buy = forced or (rng.random() < pp_)
            if buy:
                cost += inst.cq
                queue[t] = int(x_step)
                if forced and A > 1:
                    aux = (aux - 1) if aux > 0 else (A - 1)
        tot[e] = cost
    return float(tot.mean()), float(tot.std(ddof=1) / math.sqrt(n_ep))
