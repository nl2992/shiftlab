"""B3+ baseline adapters: one event stream in, one result-dict schema out.

Every policy consumes the same ``(l0, l1, u)`` arrays and returns
``{"loss","queries","switches","rollbacks","t_prom"}``, each a ``(n,)`` array, exactly as
``b1_certified_switching`` produces them. The policy code for P0/P1/P2/P3b is the pinned b1 module
(commit 041bc26, ``run_policies(..., b2=True)`` and ``simple_out``); P6 is ``b3_real_data.run_p6``.
Nothing in b1 or b3_real_data is modified.

P1 is the hindsight reference (always deploys the challenger from t=0, one switch): it is a
non-deployable benchmark, not a competitor. ``VARIANT_META`` records this and the runner copies it
into every output row.

PCT is the lightweight cost-aware threshold comparator: P3b's pacer and evidence process, but a
promotion additionally requires the *point estimate* of the per-event advantage times the remaining
horizon to exceed ``cs``. It is a non-certified break-even rule, used to show that the B3+ gain is
not merely "any cost awareness".
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
B1_COMMIT = "041bc26"


def _load_b3():
    """Import b3_real_data (it pins and loads b1 at B1_COMMIT via its own git-source loader)."""
    name = "b3_real_data"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "b3_real_data.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_b3 = _load_b3()
if _b3.B1_COMMIT != B1_COMMIT:  # pragma: no cover - guards against an accidental re-pin
    raise RuntimeError(f"b3_real_data pins b1 at {_b3.B1_COMMIT}, expected {B1_COMMIT}")
b1 = _b3.b1
B1_RECORD = dict(_b3.B1_RECORD)  # {"commit","source","path","sha256"}
STREAM_DELAYS = {k: v["delay"] for k, v in _b3.STREAMS.items()}

BASELINES = ("P0", "P1", "P2", "P3b", "P6", "PCT")
VARIANT_META = {
    "P0": {"role": "frozen incumbent, never switches", "deployable": True},
    "P1": {"role": "HINDSIGHT reference: challenger from t=0; not a deployable policy", "deployable": False},
    "P2": {"role": "uniform-query cost-null alarm", "deployable": True},
    "P3b": {"role": "certified switching reference (b1 Cert kind P3b)", "deployable": True},
    "P6": {"role": "fixed-sample paired batch test (b3_real_data.run_p6)", "deployable": True},
    "PCT": {"role": "P3b + point-estimate break-even gate (non-certified comparator)", "deployable": True},
}


class PctCert(b1.Cert):
    """P3b with an extra promotion gate: mu_hat * (T - 1 - t) > cs (point estimate, no LCB).

    mu_hat is the discounted mean of the released IPW paired increments (per-event advantage of the
    challenger over the incumbent) on the current segment. Rollback is the unchanged mirrored test.
    """

    def __init__(self, n, budget, cs, p):
        super().__init__(n, budget, cs, "P3b", p)

    def step(self, t, l0t, l1t, dis, u, ndis):  # noqa: PLR0914 - mirrors b1.Cert.step
        p = self.p
        self.loss += np.where(self.dep == 0, l0t, l1t)
        slot = t % p.delay
        rate = (ndis + p.prior_rate * p.prior_w) / (t + p.prior_w)
        q = np.clip(self.rem / np.maximum(rate * (p.T - t), 1e-9), p.pmin, 1.0)
        q = np.where(self.rem > 0, q, 0.0)
        ask = dis & (u < q)
        x = np.where(ask, (l0t - l1t) / np.where(q > 0, q, 1.0), 0.0)
        self.rem = self.rem - ask
        self.queries += ask
        cap = q / 2
        lam = np.clip(b1.bet_from_stats(self.s1, self.s2, self.cnt, p, kelly=False), 0, cap)
        s = t - p.delay
        sgn = np.where(self.dep == 0, 1.0, -1.0)
        if s >= 0:
            xo, lo = self.xbuf[slot], self.lbuf[slot]
            live = s >= self.seg
            y = sgn * xo
            self.logw += np.where(live, np.log1p(lo * y), 0.0)
            self.s1 = np.where(live, p.gamma * self.s1 + y, self.s1)
            self.s2 = np.where(live, p.gamma * self.s2 + y * y, self.s2)
            self.cnt = np.where(live, p.gamma * self.cnt + 1.0, self.cnt)
        self.xbuf[slot], self.lbuf[slot] = x, lam
        cand = self.logw >= self.thr
        mu = np.where(self.cnt > 0, self.s1 / np.maximum(self.cnt, 1e-12), 0.0)
        gate = mu * (p.T - 1 - t) > self.cs
        cand = cand & ((self.dep == 1) | gate)
        promo = cand & (self.dep == 0)
        self.t_prom = np.where(promo & np.isnan(self.t_prom), t + 1, self.t_prom)
        self.rollbacks += cand & (self.dep == 1)
        self.switches += cand
        self.dep = np.where(cand, 1 - self.dep, self.dep).astype(np.int8)
        self.seg = np.where(cand, t + 1, self.seg)
        self.logw = np.where(cand, 0.0, self.logw)
        for name in ("s1", "s2", "cnt"):
            setattr(self, name, np.where(cand, 0.0, getattr(self, name)))


def _expand(l0, l1, u):
    """Broadcast 1-D event losses to (T, n) int8 matching u's seeds."""
    n = u.shape[1]
    a0 = np.asarray(l0, dtype=np.int8)
    a1 = np.asarray(l1, dtype=np.int8)
    if a0.ndim == 1:
        a0 = np.repeat(a0[:, None], n, axis=1)
    if a1.ndim == 1:
        a1 = np.repeat(a1[:, None], n, axis=1)
    return a0, a1


def run_cost_threshold(l0, l1, u, budget, cs, cq, p) -> dict:
    """PCT. ``cq`` is accepted for a uniform signature; it does not enter the policy."""
    del cq
    a0, a1 = _expand(l0, l1, u)
    t_len, n = a0.shape
    dis_all = a0 != a1
    pol = PctCert(n, budget, cs, p)
    ndis = np.zeros(n)
    for t in range(t_len):
        pol.step(t, a0[t], a1[t], dis_all[t], u[t], ndis)
        ndis = ndis + dis_all[t]
    return b1.cert_out(pol)


def run_baselines(l0, l1, u, budget, cs, cq, p, names) -> dict[str, dict]:
    """Run the requested baselines on one shared stream.

    l0, l1: (T,) or (T, n) 0/1 losses; u: (T, n) shared query draws; p: b1.Params(T=...).
    cs and cq only affect PCT (cs); the other policies are cost-parameter-free by construction, and
    net cost is assembled by the caller as loss + cq * queries + cs * switches.
    """
    unknown = [x for x in names if x not in BASELINES]
    if unknown:
        raise ValueError(f"unknown baseline(s) {unknown}; known: {BASELINES}")
    a0, a1 = _expand(l0, l1, u)
    out: dict[str, dict] = {}
    if "P0" in names or "P1" in names:
        p0, p1 = b1.simple_out(a0, a1)
        if "P0" in names:
            out["P0"] = p0
        if "P1" in names:
            out["P1"] = p1
    if "P2" in names or "P3b" in names:
        res = b1.run_policies(a0, a1, u, budget, (), p, b2=True)
        if "P2" in names:
            out["P2"] = res["P2"]
        if "P3b" in names:
            out["P3b"] = res["P3b"]
    if "P6" in names:
        out["P6"] = _b3.run_p6(a0, a1, u, budget, p)
    if "PCT" in names:
        out["PCT"] = run_cost_threshold(a0, a1, u, budget, cs, cq, p)
    return {k: out[k] for k in names}
