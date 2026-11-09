"""Stage 1 candidate policies (docs/paper1_eqsdp/10_JOINTBAYES_PLAN.md, 12_STAGE1_RESULTS.md).

All classes subclass the frozen ``EQSD`` (scripts/qsg_methods_search/eqs_d.py), which is not edited.
The base ``Stage1Base`` re-implements ``request_labels`` with the *same* arithmetic and random draws
as ``EQSD(stake=False)`` plus two hooks (a virtual-budget view for the pacer and a post-draw gate),
so with the hooks inactive it equals arm R ``EQSDp_l0.98_g0.3`` exactly (tested).

Information rule: a policy sees only ``event`` (t, horizon, model predictions), the budget remaining,
released feedback (paired model losses of purchased labels, at their release time), and the declared
contract (T, B, c_s, delay). Evaluator fields never reach these classes.

Candidates (each sits on arm R's evidence: discounted counts ``n, k`` and Beta(k+1, n-k+1)):

C1  ``Stage1C1``  decision-reachability label gating plus a budget shadow price.
C2  ``Stage1C2``  persistent-advantage hazard mixture plus reversal option value (can only delay).
C5  ``Stage1C5``  horizon-dependent early adoption with a worse-than-incumbent cap, plus
                  conservative reversal.

Controls: ``Stage1C1Thin`` (uniform thinning), ``Stage1C1Stop`` (hard end-of-horizon label stop),
``s1c2ctl`` (arm R with a raised additive hurdle), ``s1c5ctl`` (arm R with a fixed larger gamma).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta as _beta
from scipy.stats import betabinom as _bb

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/qsg_methods_search",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from eqs_d import EQSD
from hurdles import WaldLCB
from simulator import QueryRequest

LAM, GAM = 0.98, 0.3  # arm R
CQ = 0.05


class Stage1Base(EQSD):
    """Arm R with two inert hooks. ``keep`` / ``virtual_remaining`` default to arm R behaviour."""

    def __init__(self, horizon, budget, switch_cost, *, rng, delay, name, cq=CQ, **kw):
        kw.setdefault("lam", LAM)
        kw.setdefault("gamma", GAM)
        super().__init__(horizon, budget, switch_cost, rng=rng, stake=False, name=name, **kw)
        self.delay, self.cq = int(delay), float(cq)
        self.skipped = 0  # labels the gate refused after the draw said "buy"
        self.rem = int(budget)  # last seen real remaining budget

    # hooks ---------------------------------------------------------------------------------
    def virtual_remaining(self, remaining_budget):
        return remaining_budget

    def keep(self, event, remaining_budget) -> bool:
        return True

    # ----------------------------------------------------------------------------------------
    def request_labels(self, event, remaining_budget):
        self.rem = int(remaining_budget)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, self.virtual_remaining(remaining_budget), dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        q = min(1.0, q * self.mf)
        if q <= 0.0:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        if take and not self.keep(event, remaining_budget):
            take = False
            self.skipped += 1
        self.pending += int(take)
        return QueryRequest(requested=take, probability=q if take else 0.0)


# ---------------------------------------------------------------------------------------------
# C1: decision-reachability gating + budget shadow price
# ---------------------------------------------------------------------------------------------
class Stage1C1(Stage1Base):
    """Skip a purchase the draw approved when it cannot plausibly change the next decision.

    L = pending + 1 + h labels (in-flight ones are *simulated*, never treated as observed). With
    the discounted counts updated by L labels (equal-weight approximation of the discount weights)
    find the least number ``o*`` of "opposite" outcomes (challenger correct when on model 0,
    incumbent correct when on model 1) after which arm R's own switch test passes at the release
    time t+delay. P(cross) = Beta-binomial tail P(O >= o*) under the current posterior predictive.
    A label is skipped when P(cross) < rho_eff, with the shadow price

        rho_eff = rho0 * (1 + s * min(pressure, 10)),   pressure = max(0, E_left / v_rem - 1),

    E_left the expected remaining disagreements and v_rem the virtual remaining budget. A skipped
    label is bought anyway with probability ``floor`` (prevents lock-in). Skipped draws are debited
    from the pacer's budget view with weight ``kappa`` (so the pacer does not just catch up).
    The end-of-horizon stop is implicit: if no outcome can pay back c_s, P(cross) = 0.
    """

    def __init__(self, *a, rho0=0.03, s=1.0, h=6, floor=0.1, kappa=1.0, **kw):
        super().__init__(*a, **kw)
        self.rho0, self.s, self.h = float(rho0), float(s), int(h)
        self.floor, self.kappa = float(floor), float(kappa)

    def virtual_remaining(self, remaining_budget):
        if remaining_budget <= 0:
            return remaining_budget
        return max(remaining_budget - self.kappa * self.skipped, 1.0)

    def _gain(self, n2, k2, tt, rate):
        lev = self.gamma if self.deployed == 0 else 1.0 - self.gamma
        p = float(_beta.ppf(lev, k2 + 1.0, n2 - k2 + 1.0))
        adv = (2 * p - 1) if self.deployed == 0 else (1 - 2 * p)
        return adv * rate * (self.T - tt)

    def p_cross(self, t):
        L = self.pending + 1 + self.h
        lam = self.lam
        geo = (1.0 - lam**L) / (1.0 - lam)
        w = geo / L
        n_dec, k_dec = lam**L * self.n, lam**L * self.k
        n2 = n_dec + L * w
        tt = t + self.delay
        rate = self._rate()
        if self.T - tt <= 0 or rate * (self.T - tt) <= self.cs:
            return 0.0

        def reach_gain(o):
            ones = o if self.deployed == 0 else L - o
            return self._gain(n2, k_dec + ones * w, tt, rate)

        if reach_gain(L) <= self.cs:
            return 0.0
        if reach_gain(0) > self.cs:
            return 1.0
        lo, hi = 0, L  # gain(lo) <= cs < gain(hi)
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (lo, mid) if reach_gain(mid) > self.cs else (mid, hi)
        a, b = (self.k + 1.0, self.n - self.k + 1.0)
        if self.deployed == 1:
            a, b = b, a
        return float(_bb.sf(hi - 1, L, a, b))

    def keep(self, event, remaining_budget):
        pc = self.p_cross(event.t)
        vrem = max(self.virtual_remaining(remaining_budget), 1.0)
        e_left = self._rate() * (self.T - event.t)
        pressure = min(max(e_left / vrem - 1.0, 0.0), 10.0)
        rho = self.rho0 * (1.0 + self.s * pressure)
        if pc >= rho:
            return True
        return bool(self.rng.random() < self.floor)


class Stage1C1Thin(Stage1Base):
    """Control (i): uniform thinning at keep-probability ``keep_p``, same pacer debit as C1."""

    def __init__(self, *a, keep_p=0.7, kappa=1.0, **kw):
        super().__init__(*a, **kw)
        self.keep_p, self.kappa = float(keep_p), float(kappa)

    def virtual_remaining(self, remaining_budget):
        if remaining_budget <= 0:
            return remaining_budget
        return max(remaining_budget - self.kappa * self.skipped, 1.0)

    def keep(self, event, remaining_budget):
        return bool(self.rng.random() < self.keep_p)


class Stage1C1Stop(Stage1Base):
    """Control (ii): hard end-of-horizon stop. No purchase once the label would arrive within
    ``stop_h`` events of the end (t + delay > T - stop_h)."""

    def __init__(self, *a, stop_h=300, **kw):
        super().__init__(*a, **kw)
        self.stop_h = int(stop_h)

    def keep(self, event, remaining_budget):
        return event.t + self.delay <= self.T - self.stop_h


class Stage1WaldStop(Stage1Base):
    """Supplementary: the reference ``wald_l0.97_g0.2`` (normal-approximation lower bound, same
    evidence and switching rule) with the same hard end-of-horizon label stop. stop_h very negative
    makes it inert, i.e. equal to the reference. Tests whether the fee cut alone transfers."""

    _q = WaldLCB._q

    def __init__(self, *a, stop_h=300, **kw):
        kw.setdefault("lam", 0.97)
        kw.setdefault("gamma", 0.2)
        super().__init__(*a, **kw)
        self.stop_h = int(stop_h)

    def keep(self, event, remaining_budget):
        return event.t + self.delay <= self.T - self.stop_h


# ---------------------------------------------------------------------------------------------
# C2: persistent-advantage belief + reversal option value
# ---------------------------------------------------------------------------------------------
class Stage1C2(Stage1Base):
    """Execute arm R's proposed switch only if the posterior value of switching now beats waiting.

    Model: the advantage a = (2p-1) per disagreement (sign flipped for a reversal) persists until an
    event-wise hazard ``hz`` ends it, after which the destination model is assumed worse and a
    reversal costs c_s plus a wrong-model loss ``omega * c_s``. For horizon H:
        G(a, H) = a * r * E[min(tau,H)] - cs - P(tau<H) * (1 + omega) * cs,
        E[min(tau,H)] = (1-(1-hz)^H)/hz,  P(tau<H) = 1-(1-hz)^H.
    V_now = E_post[G(a, H)]. V_wait = (1-hz)^w * E[max(0, G(a~, H-w))] where a~ comes from a
    preposterior update with the labels expected to arrive in w events (Monte Carlo, ``ndraw``
    posterior draws). Switch iff V_now > 0 and V_now >= V_wait. Applies to promotions and reversals.
    """

    def __init__(self, *a, mc_rng, hz=1 / 1000, w=100, omega=0.5, ndraw=64, **kw):
        super().__init__(*a, **kw)
        self.mc, self.hz, self.w, self.omega, self.ndraw = mc_rng, float(hz), int(w), omega, ndraw
        self.n_eval = self.n_defer = 0

    def _G(self, adv, rate, H):
        H = np.maximum(H, 0.0)
        surv = (1.0 - self.hz) ** H
        e_tau = (1.0 - surv) / self.hz
        return adv * rate * e_tau - self.cs - (1.0 - surv) * (1.0 + self.omega) * self.cs

    def approve(self, t):
        self.n_eval += 1
        rate = self._rate()
        H = self.T - t
        p = self.mc.beta(self.k + 1.0, self.n - self.k + 1.0, self.ndraw)
        sgn = 1.0 if self.deployed == 0 else -1.0  # advantage of the model we would move to
        v_now = float(self._G(sgn * (2 * p - 1), rate, H).mean())
        if v_now <= 0:
            return False
        lab_rate = min(rate, self.rem / max(self.T - t, 1)) if self.rem > 0 else 0.0
        n_w = lab_rate * self.w
        if n_w < 1.0:
            return True
        nb = round(n_w)
        s = self.mc.binomial(nb, p)
        lam_nb = self.lam**nb
        wbar = (1.0 - lam_nb) / ((1.0 - self.lam) * nb)
        n2 = lam_nb * self.n + nb * wbar
        k2 = lam_nb * self.k + s * wbar
        pm = (k2 + 1.0) / (n2 + 2.0)
        g_wait = self._G(sgn * (2 * pm - 1), rate, H - self.w)
        v_wait = float((1.0 - self.hz) ** self.w * np.maximum(g_wait, 0.0).mean())
        ok = v_now >= v_wait
        self.n_defer += int(not ok)
        return ok

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + float(d > 0)
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs and self.approve(fb.t_released):
                self.deployed = 1 - self.deployed


# ---------------------------------------------------------------------------------------------
# C5: risk-aware early adoption + conservative reversal
# ---------------------------------------------------------------------------------------------
class Stage1C5(Stage1Base):
    """Promote at a horizon-dependent quantile level, reverse only on strong evidence.

    Promotion (on model 0): level g_t = gamma + (g_early - gamma) * (T-t)/T, i.e. arm R's gamma at
    the end and ``g_early`` at t=0; switch iff (2 Q(g_t) - 1) r (T-t) > cs AND the posterior
    probability that the challenger is worse, P(p <= 1/2), is at most ``cap``.
    Reversal (on model 1): arm R's rule with the more extreme level ``g_rev`` (g_rev=gamma is arm R).
    """

    def __init__(self, *a, g_early=0.45, cap=0.2, g_rev=0.1, **kw):
        super().__init__(*a, **kw)
        self.g_early, self.cap, self.g_rev = float(g_early), float(cap), float(g_rev)

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + float(d > 0)
            self.t = fb.t_released
            if self.deployed == 0:
                g_t = self.gamma + (self.g_early - self.gamma) * (self.T - self.t) / self.T
                if self._gain_away(g_t) > self.cs:
                    pw = float(_beta.cdf(0.5, self.k + 1.0, self.n - self.k + 1.0))
                    if pw <= self.cap:
                        self.deployed = 1
            elif self._gain_away(self.g_rev) > self.cs:
                self.deployed = 0


# ---------------------------------------------------------------------------------------------
# registry (name parsing; names are fixed grids so build_suite can enumerate them)
# ---------------------------------------------------------------------------------------------
C1_GRID = [
    (rho0, s, h) for rho0 in (0.01, 0.03, 0.1) for s in (0.0, 1.0) for h in (0, 6)
]  # 12 configs
C1_THIN = (0.9, 0.8, 0.7, 0.6, 0.5, 0.4)
C1_STOP = (100, 200, 300, 400, 500, 700)
# Control grids extended after the first C1 run showed they could not reach C1's label count
# (documented deviation in 12_STAGE1_RESULTS.md): matching the label count requires them.
WALD_STOP = (0, 300, 700, 1100, 1300, 1500)
C1_THIN_EXT = (0.3, 0.25, 0.2, 0.15, 0.1, 0.05)
C1_STOP_EXT = (900, 1100, 1300, 1500, 1600, 1700, 1750)
C2_GRID = [(hz, w, om) for hz in (500, 1000, 2000) for w in (50, 150) for om in (0.0, 0.5)]  # 12
C2_MARGINS = (1, 2, 3, 4, 6, 8, 12, 16)
C5_GRID = [(ge, cap, gr) for ge in (0.4, 0.5) for cap in (0.15, 0.3) for gr in (0.3, 0.15, 0.05)]
C5_CTL = (0.35, 0.4, 0.45, 0.5, 0.55, 0.6)


def c1_name(rho0, s, h):
    return f"s1c1_r{rho0}_s{s:g}_h{h}"


def c2_name(hz, w, om):
    return f"s1c2_hz{hz}_w{w}_o{om}"


def c5_name(ge, cap, gr):
    return f"s1c5_ge{ge}_c{cap}_gr{gr}"


def _make(cls, name, **kw):
    def f(T, B, cs, cq, alpha, delay, r):
        extra = {"mc_rng": r("S1MC")} if cls is Stage1C2 else {}
        return cls(T, B, cs, rng=r("EQSD"), delay=delay, name=name, cq=cq, **extra, **kw)

    return f


def registry_entries() -> dict:
    """name -> factory (T, B, cs, cq, alpha, delay, r). Every policy draws labels from the same
    named stream as arm R (``r("EQSD")``), so purchases are paired by common random numbers."""
    reg = {"s1base": _make(Stage1Base, "s1base")}
    for rho0, s, h in C1_GRID:
        reg[c1_name(rho0, s, h)] = _make(Stage1C1, c1_name(rho0, s, h), rho0=rho0, s=s, h=h)
    reg["s1c1_r0_s0_h0"] = _make(Stage1C1, "s1c1_r0_s0_h0", rho0=0.0, s=0.0, h=0, floor=0.0)
    for kp in C1_THIN + C1_THIN_EXT:
        reg[f"s1c1thin_k{kp}"] = _make(Stage1C1Thin, f"s1c1thin_k{kp}", keep_p=kp)
    for sh in C1_STOP + C1_STOP_EXT:
        reg[f"s1c1stop_H{sh}"] = _make(Stage1C1Stop, f"s1c1stop_H{sh}", stop_h=sh)
    reg["s1wald_inert"] = _make(Stage1WaldStop, "s1wald_inert", stop_h=-(10**6))
    for sh in WALD_STOP:
        reg[f"s1wald_stop_H{sh}"] = _make(Stage1WaldStop, f"s1wald_stop_H{sh}", stop_h=sh)
    for hz, w, om in C2_GRID:
        reg[c2_name(hz, w, om)] = _make(Stage1C2, c2_name(hz, w, om), hz=1.0 / hz, w=w, omega=om)
    for m in C2_MARGINS:
        reg[f"s1c2ctl_m{m}"] = _make(Stage1Base, f"s1c2ctl_m{m}", margin=float(m))
    for ge, cap, gr in C5_GRID:
        reg[c5_name(ge, cap, gr)] = _make(
            Stage1C5, c5_name(ge, cap, gr), g_early=ge, cap=cap, g_rev=gr
        )
    reg["s1c5_degenerate"] = _make(Stage1C5, "s1c5_degenerate", g_early=GAM, cap=1.0, g_rev=GAM)
    for g in C5_CTL:
        reg[f"s1c5ctl_g{g}"] = _make(Stage1Base, f"s1c5ctl_g{g}", gamma=g)
    return reg


def grid_names(cand: str) -> dict:
    """Names of one candidate's grid and control grid (for the runner and analysis)."""
    if cand == "c1":
        return {
            "grid": [c1_name(*g) for g in C1_GRID],
            "control_a": [f"s1c1thin_k{k}" for k in C1_THIN + C1_THIN_EXT],
            "control_b": [f"s1c1stop_H{h}" for h in C1_STOP + C1_STOP_EXT],
            "ext": [f"s1c1thin_k{k}" for k in C1_THIN_EXT]
            + [f"s1c1stop_H{h}" for h in C1_STOP_EXT]
            + ["s1wald_inert", *[f"s1wald_stop_H{h}" for h in WALD_STOP]],
            "check": ["s1base", "s1c1_r0_s0_h0"],
        }
    if cand == "c2":
        return {
            "grid": [c2_name(*g) for g in C2_GRID],
            "control_a": [f"s1c2ctl_m{m}" for m in C2_MARGINS],
            "control_b": [],
            "check": ["s1base"],
        }
    if cand == "c5":
        return {
            "grid": [c5_name(*g) for g in C5_GRID],
            "control_a": [f"s1c5ctl_g{g}" for g in C5_CTL],
            "control_b": [],
            "check": ["s1base", "s1c5_degenerate"],
        }
    raise ValueError(cand)
