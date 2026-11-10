"""Workstream A policy adapters (A0, A1, A3, A5; A2/A4 compose these). PolicyView-only."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

from ..contracts import Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec
from .belief import HZ_FINE, P_FINE, BeliefCore
from .valuefn import build_tables, flip_prob, greedy_q, rho_level, voi

LABELS = {
    "A0": "IN_HOUSE_HEURISTIC (online belief-state MPC; textbook controlled-POMDP baseline)",
    "A1": "IN_HOUSE_HEURISTIC (queue-aware one-step VOI over belief-grid value tables)",
    "A2": "IN_HOUSE_HEURISTIC (A1 behind core e-process Gate)",
    "A3": "IN_HOUSE_HEURISTIC (Lagrangian dual-price controller)",
    "A4": "IN_HOUSE_HEURISTIC (learned continuation value, train-seed fitted, behind Gate)",
    "A5": "IN_HOUSE_HEURISTIC (ranking-reversal lookahead)",
}


class _JointBase(PolicyAdapter):
    """Shared state: belief core, pending-queue bookkeeping (own request times)."""

    def __init__(
        self,
        known: dict | None = None,
        n_models: int = 18,
        rho_mult: float = 1.0,
        fine: bool = False,
        persist: float = 0.0,
        pi0: float = 0.5,
    ):
        self.known, self.n_models, self.rho_mult = known, n_models, rho_mult
        self.core = (
            BeliefCore(known, HZ_FINE, P_FINE, persist, pi0)
            if fine
            else BeliefCore(known, persist=persist, pi0=pi0)
        )

    def reset(self, spec: ProblemSpec, rng: np.random.Generator) -> None:
        self.spec, self.rng = spec, rng
        self.T, self.B, self.k, self.c_q = spec.T, spec.B, spec.costs.k, spec.costs.c_q
        self.core.reset(spec)
        self._reset()

    def _reset(self):
        pass

    def _rho(self, view: PolicyView, d: int) -> float:
        rem = view.labels_remaining
        if rem <= 0:
            return 0.0
        left = max(self.T - view.t - d, 1)
        return float(min(self.core.r_hat(), rem / left) * self.rho_mult)

    def _tabs(self, idx, rho, k):
        rl = rho_level(min(rho, 0.6))
        return [build_tables(self.core.model(int(h)), self.T, k, rl) for h in idx]

    def _finish(self, view, a, q) -> Paper3Decision:
        if q:
            self.core.note_query(view.t)
        return Paper3Decision(int(a), int(q))

    def _can_query(self, view, d) -> bool:
        informative = view.event.disagree if self.known is None else True
        return bool(informative) and view.labels_remaining > 0 and view.t + d <= self.T


# ======================================================================================
# A1: queue-aware VOI (+ ablations)
# ======================================================================================
class QVOI(_JointBase):
    def __init__(
        self,
        lam_q=0.0,
        sw_margin=0.0,
        rho_mult=1.0,
        n_models=18,
        use_delay=True,
        persist=0.0,
        pi0=0.5,
        use_cont=True,
        use_switch_pen=True,
        known=None,
        name="A1",
        ns=(1, 2, 3, 5, 8, 12, 20),
        voi_mult=1.0,
        acq="voi",
    ):
        super().__init__(known, n_models, rho_mult, persist=persist, pi0=pi0)
        self.ns = tuple(ns)
        self.voi_mult = voi_mult
        self.acq = acq  # "voi" | "paced" (paced = attribution ablation: Wald-style spending)
        self.lam_q, self.sw_margin = lam_q, sw_margin
        self.use_delay, self.use_cont, self.use_switch_pen = use_delay, use_cont, use_switch_pen
        self.name = name

    def act(self, view: PolicyView) -> Paper3Decision:
        core = self.core
        core.ingest(view)
        t = view.t
        d = core.d_hat() if self.use_delay else 1
        rho = self._rho(view, d)
        idx, ws = core.top(self.n_models)
        pis = core.pi_at(t)[idx]
        tabs = self._tabs(idx, rho, self.k)
        a, _ = greedy_q([q for _, q in tabs], ws, t, pis, view.prev_action, self.k, self.sw_margin)
        q = 0
        if self.acq == "paced":
            if self._can_query(view, d):
                left = max(core.r_hat() * (self.T - t), 1e-9)
                pr = min(max(view.labels_remaining / left, 0.05), 1.0)
                q = int(self.rng.random() < pr)
        elif self._can_query(view, d):
            m_pend = len(core.pending) if self.use_delay else 0
            ktab = self.k if self.use_switch_pen else 0.0
            vtabs = tabs if self.use_switch_pen else self._tabs(idx, rho, ktab)
            gain = 0.0
            for h, w, pi, (V, _) in zip(idx, ws, pis, vtabs, strict=True):
                gain += w * voi(
                    core.model(int(h)),
                    V,
                    t,
                    t + d,
                    a,
                    float(pi),
                    m_pend,
                    self.T,
                    use_pending=self.use_delay,
                    myopic=not self.use_cont,
                    k=ktab,
                    ns=self.ns,
                    rem=view.labels_remaining,
                )
            q = int(self.voi_mult * gain > self.c_q + self.lam_q)
        return self._finish(view, a, q)


# ======================================================================================
# A5: ranking-reversal lookahead
# ======================================================================================
class RankReversal(_JointBase):
    def __init__(
        self,
        eps_flip=0.05,
        h_min=5,
        sw_margin=0.0,
        rho_mult=1.0,
        n_models=18,
        known=None,
        n_batch=8,
        persist=0.0,
        pi0=0.5,
    ):
        super().__init__(known, n_models, rho_mult, persist=persist, pi0=pi0)
        self.eps_flip, self.h_min, self.sw_margin, self.name = eps_flip, h_min, sw_margin, "A5"
        self.n_batch = n_batch

    def act(self, view: PolicyView) -> Paper3Decision:
        core = self.core
        core.ingest(view)
        t, d = view.t, core.d_hat()
        rho = self._rho(view, d)
        idx, ws = core.top(self.n_models)
        pis = core.pi_at(t)[idx]
        tabs = self._tabs(idx, rho, self.k)
        a, _ = greedy_q([q for _, q in tabs], ws, t, pis, view.prev_action, self.k, self.sw_margin)
        q = 0
        if self._can_query(view, d) and self.T - (t + d) >= self.h_min:
            m_pend = len(core.pending)
            pf = 0.0
            for h, w, pi, (_, Q) in zip(idx, ws, pis, tabs, strict=True):
                pf += w * flip_prob(
                    core.model(int(h)),
                    Q,
                    t,
                    t + d,
                    a,
                    float(pi),
                    m_pend,
                    self.T,
                    self.k,
                    n_batch=min(self.n_batch, max(view.labels_remaining, 1)),
                )
            q = int(pf >= self.eps_flip)
        return self._finish(view, a, q)


# ======================================================================================
# A3: Lagrangian dual-price controller
# ======================================================================================
class DualPrice(_JointBase):
    def __init__(
        self,
        lam_q=0.0,
        lam_sw=0.0,
        kappa=1.0,
        eta=0.0,
        front=0.3,
        rho_mult=1.0,
        n_models=18,
        known=None,
        name="A3",
        persist=0.0,
        pi0=0.5,
    ):
        super().__init__(known, n_models, rho_mult, persist=persist, pi0=pi0)
        self.lam_q0, self.lam_sw, self.kappa, self.eta, self.front = (
            lam_q,
            lam_sw,
            kappa,
            eta,
            front,
        )
        self.name = name

    def _reset(self):
        self.lam_q = self.lam_q0

    def _evpi(self, view, d) -> float:
        c = self.core
        t, dep = view.t, view.prev_action
        n = self.T - t + 1
        w, pi = c.weights(), c.pi_at(t)
        if c.known is None:
            gL, gH = c.r_hat() * (2 * c.pL - 1), c.r_hat() * (2 * c.pH - 1)
        else:
            m = c.model(0)
            gL, gH = np.array([m.gain[0]]), np.array([m.gain[1]])
        lam = c.lam
        neff = (1 - lam**n) / np.maximum(1 - lam, 1e-9)
        B = n * (gL + (gH - gL) * c.pinf) + (gH - gL) * (pi - c.pinf) * neff
        var_in = ((gH - gL) * neff) ** 2 * pi * (1 - pi)
        mean = float(np.sum(w * B))
        var = float(np.sum(w * var_in) + np.sum(w * (B - mean) ** 2))
        sd = math.sqrt(max(var, 1e-12))
        m = (mean if dep == 0 else -mean) - self.k - self.lam_sw
        evpi = sd * norm.pdf(m / sd) - abs(m) * norm.cdf(-abs(m) / sd)
        avail = max(self.T - t - d, 0) / max(self.T - t, 1)
        return self.kappa * evpi * avail

    def act(self, view: PolicyView) -> Paper3Decision:
        core = self.core
        core.ingest(view)
        t, d = view.t, core.d_hat()
        rho = self._rho(view, d)
        idx, ws = core.top(self.n_models)
        pis = core.pi_at(t)[idx]
        tabs = self._tabs(idx, rho, self.k)
        a, _ = greedy_q([q for _, q in tabs], ws, t, pis, view.prev_action, self.k, self.lam_sw)
        spent = (self.B - view.labels_remaining) / max(self.B, 1)
        frac = t / max(self.T - d, 1)
        if self.eta > 0:  # dynamic dual: raise price when ahead of the pacing path
            self.lam_q = max(0.0, self.lam_q + self.eta * (spent - frac))
        q = 0
        cap_ok = spent <= self.front + (1 - self.front) * min(frac, 1.0) + 1e-9  # reservation
        if self._can_query(view, d) and cap_ok:
            q = int(self._evpi(view, d) > self.c_q + self.lam_q)
        return self._finish(view, a, q)


# ======================================================================================
# A0: online belief-state MPC (Monte-Carlo rollouts with queue, delay and budget in the sim)
# ======================================================================================
class BeliefMPC(_JointBase):
    def __init__(
        self,
        N=64,
        Hmax=120,
        qmargin=0.0,
        amargin=0.0,
        base_margin=0.0,
        rho_mult=1.0,
        known=None,
        name="A0",
        persist=0.0,
        pi0=0.5,
    ):
        super().__init__(known, 1, rho_mult, fine=True, persist=persist, pi0=pi0)
        self.N, self.Hmax, self.qmargin = N, Hmax, qmargin
        self.amargin, self.base_margin, self.name = amargin, base_margin, name

    def _reset(self):
        self.cur_a = 0

    @staticmethod
    def _benefit(pi, n, gL, gH, lam, pinf):
        neff = (1 - lam**n) / np.maximum(1 - lam, 1e-9)
        return n * (gL + (gH - gL) * pinf) + (gH - gL) * (pi - pinf) * neff

    def act(self, view: PolicyView) -> Paper3Decision:
        core = self.core
        core.ingest(view)
        t, d, dep = view.t, core.d_hat(), view.prev_action
        canq = self._can_query(view, d)
        if not (canq or core.new_obs or t == 1):
            return self._finish(view, self.cur_a, 0)
        a, q = self._plan(view, d, dep, canq)
        self.cur_a = a
        return self._finish(view, a, q)

    @staticmethod
    def _draw(Pst, u):
        c = np.cumsum(Pst, axis=1)
        return np.minimum((u[:, None] > c).sum(1), Pst.shape[1] - 1)

    def _plan(self, view, d, dep, canq):
        core, T, N, k, cq = self.core, self.T, self.N, self.k, self.c_q
        rng, t = self.rng, view.t
        H = max(1, min(T - t, self.Hmax))
        w = core.weights()
        pi_t = core.pi_at(t)
        hs = rng.choice(len(w), size=N, p=w)
        s = (rng.random(N) < pi_t[hs]).astype(int)
        a_, b_ = core.a[hs], core.b[hs]
        lam, pinf = 1 - a_ - b_, core.pinf[hs]
        PL, PH = core.PL[hs], core.PH[hs]  # (N,O)
        zexp_L, zexp_H = PL @ core.Zo, PH @ core.Zo
        r = core.r_hat()
        gL, gH = r * zexp_L, r * zexp_H
        O = core.O
        D = max(d, 1)
        cands = [(0, 0), (1, 0), (0, 1), (1, 1)]
        C = len(cands)
        ca = np.array([c[0] for c in cands])[:, None]
        cqq = np.array([c[1] for c in cands])[:, None]
        noise = rng.random((H + 1, 4, N))
        buf = -np.ones((C, N, D), int)

        def put(mask, tau, s_now, u):
            o = self._draw(np.where(s_now[:, None] == 1, PH, PL), u)
            ok = mask & (tau + d <= T)
            sl = tau % D
            buf[:, :, sl] = np.where(ok, o[None, :], buf[:, :, sl])

        Pst = np.where(s[:, None] == 1, PH, PL)
        for u_req in core.pending:  # in-flight queries: outcome drawn from the current state
            A = u_req + d
            if t < A <= T:
                buf[:, :, A % D] = self._draw(Pst, noise[0, 3])[None, :]
        pi = np.tile(pi_t[hs], (C, 1))
        rem = np.full((C, N), view.labels_remaining)
        cost = np.zeros((C, N))
        aprev = np.full((C, N), dep)
        flag0 = 1.0 if (view.event.disagree or core.known is not None) else 0.0
        zs = np.where(s == 1, zexp_H, zexp_L)
        # ---- root round t: forced candidate
        a_now = np.broadcast_to(ca, (C, N))
        cost += k * (a_now != aprev) - a_now * flag0 * zs[None, :]
        qm = np.broadcast_to((cqq == 1) & (rem > 0), (C, N)) if canq else np.zeros((C, N), bool)
        cost += cq * qm
        rem = rem - qm
        put(qm, t, s, noise[0, 2])
        aprev = a_now.copy()
        for h in range(1, H + 1):
            tau = t + h
            u = noise[h]
            s = np.where(s == 0, (u[0] < a_).astype(int), (u[0] >= b_).astype(int))
            pi = pinf + (pi - pinf) * lam
            sl = tau % D
            arr = buf[:, :, sl].copy()
            buf[:, :, sl] = -1
            has = arr >= 0
            if has.any():
                oi = np.maximum(arr, 0)
                ph = np.take_along_axis(np.broadcast_to(PH, (C, N, O)), oi[..., None], 2)[..., 0]
                pl = np.take_along_axis(np.broadcast_to(PL, (C, N, O)), oi[..., None], 2)[..., 0]
                den = pi * ph + (1 - pi) * pl
                pi = np.where(has & (den > 1e-300), pi * ph / np.maximum(den, 1e-300), pi)
            n = T - tau + 1
            Bn = self._benefit(pi, n, gL[None], gH[None], lam[None], pinf[None])
            sw0 = (aprev == 0) & (Bn - k > self.base_margin)
            sw1 = (aprev == 1) & (-Bn - k > self.base_margin)
            a_now = np.where(sw0, 1, np.where(sw1, 0, aprev))
            f = np.ones(N, bool) if core.known is not None else (u[1] < r)
            zs = np.where(s == 1, zexp_H, zexp_L)
            cost += k * (a_now != aprev) - a_now * f[None, :] * zs[None, :]
            qm = f[None, :] & (rem > 0) & (tau + d <= T)
            cost += cq * qm
            rem = rem - qm
            put(qm, tau, s, u[2])
            aprev = a_now
        if t + H < T:  # truncated horizon: tail value of the final deployed action
            n = T - (t + H)
            Bn = self._benefit(pi, n, gL[None], gH[None], lam[None], pinf[None])
            cost += np.where(aprev == 1, -Bn, 0.0)
        adj = cost.mean(1)
        for i, (ai, qi) in enumerate(cands):
            if qi and not canq:
                adj[i] = np.inf
            if qi:
                adj[i] += self.qmargin
            if ai != dep:
                adj[i] += self.amargin
        return cands[int(np.argmin(adj))]
