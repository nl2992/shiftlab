"""B3+ (P7) certified switching: break-even promotion and decision-value-aware acquisition.

Implements docs/promising_directions/B3_PLUS_METHOD.md as a sibling of ``b1.Cert``. b1 is loaded
from the pinned revision 041bc26 and is never modified. Development code; no claim of validity
beyond what the spec states (the margin-grid e-processes are nonnegative-wealth processes; the
economic criterion V_hat > 0 rests on an unestablished persistence assumption).
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
B1_PATH = ROOT / "scripts/promising_directions/b1_certified_switching.py"
B1_COMMIT = "041bc26"
VARIANTS = ("P7", "P7a", "P7b", "P7c", "P4ref")
UCB_TRIVIAL = 1.0  # |D| <= 1, so this is the bound when no margin null is rejected


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )


def load_b1():
    """Import b1_certified_switching as at commit 041bc26 (same approach as b3_real_data)."""
    rel = str(B1_PATH.relative_to(ROOT)).replace("\\", "/")
    unchanged = _git("diff", "--quiet", B1_COMMIT, "--", rel).returncode == 0
    path, how = B1_PATH, "worktree file (git diff --quiet 041bc26 is clean)"
    if not unchanged:
        src = _git("show", f"{B1_COMMIT}:{rel}")
        if src.returncode != 0:
            raise RuntimeError(f"cannot extract {rel} at {B1_COMMIT}")
        path = Path(tempfile.mkdtemp()) / "b1_certified_switching.py"
        path.write_text(src.stdout, encoding="utf-8")
        how = "extracted from 041bc26 via git show (worktree file differs)"
    name = "b1_pinned_for_b3plus"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    rec = {"commit": B1_COMMIT, "source": how, "path": str(path)}
    rec["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return mod, rec


b1, B1_RECORD = load_b1()


@dataclass(frozen=True)
class PlusParams:
    variant: str = "P7"  # one of VARIANTS
    r_floor: float = 0.25
    r_max: float = 2.0
    kappa: float = 1.0
    lb_step: float = (
        0.01  # margin grid (mirrors b1.Params defaults; these fields are authoritative)
    )
    lb_M: int = 31
    lb_offset: int = 150
    lb_K: int = 10
    persist_gamma: float = 0.97  # P7c only
    persist_min: float = 0.0  # P7c only


class CertPlus:
    """B3+ certified switching, vectorised over seeds like ``b1.Cert``.

    Per-event order is P3b's: issue (q_t, lam_t from information released before t - d), release
    (label of s = t - d enters evidence with its own frozen q_s, lam_s), decide (effective t + 1).

    LCB_t is b1's lower bound from the margin grid of nulls H0_m: E[D] <= m (wealth factor
    1 + lam (x - m), threshold log(K/alpha), value (count - 1) * step).
    UCB_t is its mirrored counterpart: nulls H0'_m: E[D] >= m for m in the same grid, wealth factor
    1 + lam_dn (m - x) with a margin-free frozen bet lam_dn = clip(max(-mu, 0)/(var + mu^2), 0,
    q/2). Because lam_dn does not depend on m, wealth is pathwise increasing in m, the rejected
    set is a suffix {m >= m*}, and a single threshold log(K/alpha) controls the family; UCB = m*
    (E[D] < m*), or UCB_TRIVIAL = 1 if nothing is rejected. SPEC DEVIATION: the spec describes the
    mirror as "negative margins (H0: E[D] >= -m)"; that grid can only certify E[D] < 0 and never a
    positive upper bound, so the equivalent suffix construction on the same non-negative grid is
    used. Both grids are only active while deployed on the incumbent, as in b1.Cert.
    """

    def __init__(self, n, budget, cs, cq, p, plus: PlusParams, trace=False):
        if plus.variant not in VARIANTS:
            raise ValueError(plus.variant)
        self.n, self.budget, self.cs, self.cq, self.p, self.plus = n, budget, cs, cq, p, plus
        v = plus.variant
        self.econ = v in ("P7", "P7a", "P7c")
        self.acq_dv = v in ("P7", "P7b", "P7c")
        self.persist = v == "P7c"
        self.is_p4 = v == "P4ref"
        self.dep = np.zeros(n, dtype=np.int8)
        self.rem = np.full(n, budget)
        self.seg = np.zeros(n, dtype=np.int64)
        self.logw = np.zeros(n)
        self.s1, self.s2, self.cnt = np.zeros(n), np.zeros(n), np.zeros(n)
        self.pst = np.zeros(n)
        self.xbuf, self.lbuf, self.lubuf = (np.zeros((p.delay, n)) for _ in range(3))
        self.queries = np.zeros(n, dtype=np.int64)
        self.switches = np.zeros(n, dtype=np.int64)
        self.rollbacks = np.zeros(n, dtype=np.int64)
        self.t_prom = np.full(n, np.nan)
        self.loss = np.zeros(n)
        self.q_sum = np.zeros(n)
        self.min_factor = np.full(n, np.inf)  # min of 1 + lam*y over released events
        self.min_grid_factor = np.full(n, np.inf)  # same over margin-grid factors
        self.k = 1 if self.is_p4 else plus.lb_K
        self.mgrid = np.arange(plus.lb_M) * plus.lb_step
        self.offs = np.arange(self.k) * plus.lb_offset
        self.lbw = np.zeros((n, self.k, plus.lb_M))
        self.ubw = np.zeros((n, self.k, plus.lb_M)) if self.acq_dv else None
        self.lb_thr = math.log(self.k / p.alpha)
        self.thr = math.log(1 / p.alpha)
        self.tr = (
            {
                k: np.zeros((p.T, n))
                for k in ("dep", "ask", "x", "lam", "logw", "q", "gap", "lcb", "ucb", "r")
            }
            if trace
            else None
        )

    # ------------------------------------------------------------------ bounds
    def lcb(self) -> np.ndarray:
        c = (self.lbw >= self.lb_thr).sum(2)
        return np.where(c > 0, (c - 1) * self.plus.lb_step, 0.0).max(1)

    def ucb(self) -> np.ndarray:
        c = (self.ubw >= self.lb_thr).sum(2)
        return np.where(c > 0, (self.plus.lb_M - c) * self.plus.lb_step, UCB_TRIVIAL).min(1)

    # --------------------------------------------------------------- trace views
    def _view(self, key):
        return None if self.tr is None else self.tr[key]

    gap_trace = property(lambda s: s._view("gap"))
    lcb_trace = property(lambda s: s._view("lcb"))
    q_trace = property(lambda s: s._view("q"))
    dep_trace = property(lambda s: s._view("dep"))

    @property
    def q_issued_mean(self) -> np.ndarray:
        return np.where(self.queries > 0, self.q_sum / np.maximum(self.queries, 1), np.nan)

    # --------------------------------------------------------------------- step
    def step(self, t, l0t, l1t, dis, u, ndis):
        p, pl, cs, cq = self.p, self.plus, self.cs, self.cq
        self.loss += np.where(self.dep == 0, l0t, l1t)
        dep_t = self.dep.copy()
        slot = t % p.delay
        # ---- issue: q_t and lam_t use only state released by t - delay - 1
        rate = (ndis + p.prior_rate * p.prior_w) / (t + p.prior_w)
        h_eff = p.T - t
        pace = self.rem / np.maximum(rate * h_eff, 1e-9)
        cq_future = cq * np.minimum(self.rem, rate * h_eff * p.pmin)
        lcb_i = ucb_i = gap = r = np.zeros(self.n)
        if self.acq_dv:
            lcb_i, ucb_i = self.lcb(), self.ucb()
            gap = cs + cq_future - lcb_i * h_eff
            decay = np.exp(-np.abs(gap) / (pl.kappa * max(cs, 1e-9)))
            r = np.where(
                ucb_i * h_eff < cs, pl.r_floor, np.clip(pl.r_max * decay, pl.r_floor, pl.r_max)
            )
            # SPEC DEVIATION: the grids are frozen while deployed on the challenger, so LCB/UCB
            # are undefined there; use the neutral pacer (r = 1) to keep rollback monitoring.
            r = np.where(self.dep == 1, 1.0, r)
            pace = r * pace
        q = np.clip(pace, p.pmin, 1.0)
        q = np.where(self.rem > 0, q, 0.0)
        ask = dis & (u < q)
        x = np.where(ask, (l0t - l1t) / np.where(q > 0, q, 1.0), 0.0)
        self.rem = self.rem - ask
        self.queries += ask
        self.q_sum += np.where(ask, q, 0.0)
        assert (self.rem >= 0).all() and (self.queries <= self.budget).all()
        cap = p.pmin / 2 if self.is_p4 else q / 2  # cap against THIS event's issued propensity
        lam = np.clip(b1.bet_from_stats(self.s1, self.s2, self.cnt, p, kelly=False), 0, cap)
        lu = np.zeros(self.n)
        if self.acq_dv:
            mu = self.s1 / (self.cnt + p.n0)
            var = (self.s2 + p.n0 * p.s2_prior) / (self.cnt + p.n0)
            lu = np.clip(np.maximum(-mu, 0.0) / (var + mu * mu), 0, cap)
        # ---- release: label of s = t - delay enters with the bets frozen at its issue time
        s = t - p.delay
        sgn = np.where(self.dep == 0, 1.0, -1.0)
        if s >= 0:
            xo, lo, luo = self.xbuf[slot], self.lbuf[slot], self.lubuf[slot]
            live = s >= self.seg
            y = sgn * xo
            self.logw += np.where(live, np.log1p(lo * y), 0.0)
            self.min_factor = np.minimum(self.min_factor, np.where(live, 1 + lo * y, np.inf))
            self.s1 = np.where(live, p.gamma * self.s1 + y, self.s1)
            self.s2 = np.where(live, p.gamma * self.s2 + y * y, self.s2)
            self.cnt = np.where(live, p.gamma * self.cnt + 1.0, self.cnt)
            self.pst = np.where(
                live, pl.persist_gamma * self.pst + (1 - pl.persist_gamma) * y, self.pst
            )
            act = (s >= self.seg[:, None] + self.offs[None, :]) & live[:, None]
            gate = act[:, :, None] & (self.dep == 0)[:, None, None]
            fac = 1 + lo[:, None, None] * (xo[:, None, None] - self.mgrid[None, None, :])
            self.lbw += np.where(gate, np.log(fac), 0.0)
            gmin = np.where(gate, fac, np.inf).min((1, 2))
            if self.acq_dv:
                facu = 1 + luo[:, None, None] * (self.mgrid[None, None, :] - xo[:, None, None])
                self.ubw += np.where(gate, np.log(facu), 0.0)
                gmin = np.minimum(gmin, np.where(gate, facu, np.inf).min((1, 2)))
            self.min_grid_factor = np.minimum(self.min_grid_factor, gmin)
        self.xbuf[slot], self.lbuf[slot], self.lubuf[slot] = x, lam, lu
        # ---- decide (effective from t + 1)
        cand_ev = self.logw >= self.thr
        lcb_d = self.lcb() if (self.econ or self.is_p4) else lcb_i
        if self.is_p4:
            ok = lcb_d * min(p.hazard_mean, p.T - 1 - t) > cs
        elif self.econ:
            ok = lcb_d * h_eff - cs - cq_future > 0
            if self.persist:
                ok = ok & ~(self.pst < pl.persist_min)
        else:
            ok = True
        # the economic gate guards promotion only; rollback is a safety action and is never gated
        cand = cand_ev & ((self.dep == 1) | ok)
        if self.tr is not None:
            for key, val in (
                ("dep", dep_t),
                ("ask", ask),
                ("x", x),
                ("lam", lam),
                ("q", q),
                ("gap", gap),
                ("lcb", lcb_i),
                ("ucb", ucb_i),
                ("r", r),
            ):
                self.tr[key][t] = val
            self.tr["logw"][t] = self.logw
        promo = cand & (self.dep == 0)
        self.t_prom = np.where(promo & np.isnan(self.t_prom), t + 1, self.t_prom)
        self.rollbacks += cand & (self.dep == 1)
        self.switches += cand
        self.dep = np.where(cand, 1 - self.dep, self.dep).astype(np.int8)
        self.seg = np.where(cand, t + 1, self.seg)
        self.logw = np.where(cand, 0.0, self.logw)
        for name in ("s1", "s2", "cnt", "pst"):
            setattr(self, name, np.where(cand, 0.0, getattr(self, name)))
        self.lbw[cand] = 0.0
        if self.ubw is not None:
            self.ubw[cand] = 0.0

    def out(self) -> dict:
        return {
            "loss": self.loss,
            "queries": self.queries,
            "switches": self.switches,
            "rollbacks": self.rollbacks,
            "t_prom": self.t_prom,
            "q_issued_mean": self.q_issued_mean,
        }


def run_plus_policies(l0, l1, u, budget, cs, cq, p, plus_list, trace=False, return_objs=False):
    """Run every PlusParams variant on identical streams. Keys mirror b1.run_policies' P3b output."""
    t_len, n = l0.shape
    dis_all = l0 != l1
    objs, names = [], []
    for i, pl in enumerate(plus_list):
        name = pl.variant if pl.variant not in names else f"{pl.variant}#{i}"
        names.append(name)
        objs.append(CertPlus(n, budget, cs, cq, p, pl, trace=trace))
    ndis = np.zeros(n)
    for t in range(t_len):
        for o in objs:
            o.step(t, l0[t], l1[t], dis_all[t], u[t], ndis)
        ndis = ndis + dis_all[t]
    out = {nm: o.out() for nm, o in zip(names, objs, strict=True)}
    return (out, dict(zip(names, objs, strict=True))) if return_objs else out
