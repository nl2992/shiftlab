"""Q3 / S10: cost-aware intervention environment (synthetic only).

Two pre-trained models exist: the source model M_src (initially deployed) and a challenger M_shift trained
offline on the shifted regime. The label law is a logistic model with regime-dependent weights. At every
step the deployed model takes a cost-sensitive decision and pays its decision loss. Policies may query labels
(cost per label, resolved after ``delay`` steps), recalibrate / retrain the deployed model toward the current
regime, promote (swap to the other model) or roll back.

Action costs are paid in loss units: query cost c_q * KQ per label, other costs c * KC per action, where the
mandated grid values are multiplied by KQ=10 and KC=100 (documented design choice: costs are then comparable
to the harm accumulated over the horizon). Trajectories do not depend on costs for cost-blind policies, so cost
grids are applied post hoc from action counts; the cost-gated policy is re-run per cost setting.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from shiftlab.sota_search import generators as g

KQ, KC = 10.0, 100.0
T_DEFAULT = 1000
W0 = g.W_SRC.copy()
DW = np.array([-2.0, 2.0, 0.0, 0.0])
W1 = W0 + DW
WMID = W0 + 0.5 * DW
REG_W = {0: W0, 1: W1, 2: WMID}
ALPHA = 0.05
R0_BRIER, R0_COST = 0.1608, 0.4085
SD_COST = 1.45
RETRAIN_LAG, RETRAIN_NOISE, RECAL_NOISE, RECAL_STEP = (
    25,
    0.3,
    0.47,
    0.6,
)  # noise = 1.5 / sqrt(labels in the refit window): 25 (retrain) and 10 (recalibrate) labels at a 10% label rate


@dataclass(frozen=True)
class Scenario:
    name: str
    sched: str  # 'perm' | 'temp' | 'reversal' | 'tied' | 'none'
    delay: int = 5
    T: int = T_DEFAULT
    t0: int = 300


def regime_path(sc: Scenario) -> np.ndarray:
    T, t0 = sc.T, sc.t0
    t = np.arange(T)
    if sc.sched == "perm":
        return (t >= t0).astype(int)
    if sc.sched == "temp":
        return ((t >= t0) & (t < t0 + 120)).astype(int)
    if sc.sched == "reversal":
        return ((t >= t0) & (t < t0 + 250)).astype(int)
    if (
        sc.sched == "tied"
    ):  # alternates between the source regime and a regime where both models are equally off
        return np.where(((t - t0) // 60) % 2 == 0, 2, 0) * (t >= t0)
    return np.zeros(T, dtype=int)


SCENARIOS = [
    Scenario("perm_beneficial", "perm"),
    Scenario("temp_beneficial", "temp"),
    Scenario("reversal", "reversal"),
    Scenario("near_tied_flip", "tied"),
    Scenario("harmful_incumbent_delay50", "perm", delay=50),
    Scenario("no_worthwhile", "none"),
]


@lru_cache(maxsize=16)
def exp_cost_table() -> np.ndarray:
    """E[decision cost] of M_src (row 0) and M_shift (row 1) under each regime (columns 0,1,2), by Monte Carlo."""
    rng = np.random.default_rng(2468)
    n = 400_000
    out = np.zeros((2, 3))
    x = rng.standard_normal((n, g.D))
    u = rng.random(n)
    for r in range(3):
        y = (u < g.sigmoid(x @ REG_W[r])).astype(float)
        for m, wm in enumerate((W0, W1)):
            out[m, r] = g.decision_cost((g.sigmoid(x @ wm) >= g.TAU).astype(float), y).mean()
    return out


def make(sc: Scenario, S: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    T = sc.T
    x = rng.standard_normal((S, T, g.D))
    rp = regime_path(sc)
    wt = np.stack([REG_W[r] for r in rp])  # (T, D)
    y = (rng.random((S, T)) < g.sigmoid(np.einsum("std,td->st", x, wt))).astype(float)
    return {
        "x": x,
        "y": y,
        "rp": rp,
        "wt": wt,
        "scenario": sc,
        "U": rng.random((S, T)),
        "noise": rng.standard_normal((S, T // 20 + 2, g.D)),
    }


class OnlineHG:
    """Per-seed online HG e-process (Brier risk, discounted Kelly bet, decision-cost gate), restartable."""

    def __init__(self, S, frac, delay, gamma=0.99, gate_w=100):
        self.S, self.frac, self.delay, self.gamma, self.gg = S, frac, delay, gamma, 1 - 1 / gate_w
        self.reset(np.ones(S, bool))
        self.buf = {}

    def reset(self, m):
        z = lambda a: np.where(m, 0.0, a)
        for k in ("c1", "c2", "cn", "g1", "gn", "logw"):
            setattr(self, k, z(getattr(self, k, np.zeros(self.S))))

    def absorb(self, t, m):
        """Labels that arrive at time t (stored in buf) update the moment states; ``m`` restricts to live seeds."""
        for key, arrs in list(self.buf.items()):
            if key <= t - 1:
                X, Xc, wl = arrs
                self.c1 = self.gamma * self.c1 + X
                self.c2 = self.gamma * self.c2 + X * X
                self.cn = self.gamma * self.cn + 1
                self.g1 = self.gg * self.g1 + Xc
                self.gn = self.gg * self.gn + 1
                self.logw = self.logw + wl
                del self.buf[key]

    def step(self, t, p, brier, cost, Q, live):
        q = self.frac
        prox_b, act = p * (1 - p), (p >= g.TAU).astype(float)
        prox_c = act * (1 - p) * g.FP_COST + (1 - act) * p * g.FN_COST
        X = prox_b + (Q / q) * (brier - prox_b) - R0_BRIER
        Xc = prox_c + (Q / q) * (cost - prox_c) - R0_COST
        mean, second = self.c1 / (self.cn + 1), self.c2 / (self.cn + 1)
        lam = np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0)
        lam = np.minimum(lam, 0.5 / (0.25 * (1 / q - 1) + R0_BRIER))
        lam = lam * ((self.g1 / (self.gn + 1)) > 0)
        wl = np.log1p(lam * X)
        a = t + self.delay
        old = self.buf.get(a)
        new = (X * live, Xc * live, wl * live)
        self.buf[a] = new if old is None else tuple(o + n for o, n in zip(old, new, strict=True))
        # absorb everything that arrived strictly before t happens at the start of the next call
        return self.logw >= np.log(1 / ALPHA)


def run_policy(
    st: dict,
    policy: str,
    frac: float = 0.10,
    costs: dict | None = None,
    ph_thr: float = 12.0,
    seed: int = 0,
) -> dict:
    t0_ = time.perf_counter()
    sc: Scenario = st["scenario"]
    S, T, D = st["x"].shape
    delay = sc.delay
    ctab = exp_cost_table()
    wd = np.tile(W0, (S, 1))  # deployed weights
    other = np.tile(W1, (S, 1))  # the other pre-trained model (challenger / previous)
    dep_id = np.zeros(S, dtype=int)  # 0 = M_src, 1 = M_shift, 2 = custom (retrained/recalibrated)
    oth_id = np.ones(S, dtype=int)
    n_q, n_sw, n_rb, n_rt, n_rc, n_false = (np.zeros(S) for _ in range(6))
    loss_tot = np.zeros(S)
    loss_star = np.zeros(S)
    swap_t = np.full(S, -10_000)
    retrain_ready = np.full(S, -1)
    retrain_w = np.zeros((S, D))
    prev_dep_was_other = np.zeros(S, dtype=bool)
    np.full(S, np.nan)
    ph_m, ph_min, ph_peak = np.zeros(S), np.zeros(S), np.zeros(S)
    hg = OnlineHG(S, frac, delay) if policy in ("hg_switch",) else None
    ev_c1, ev_c2, ev_n, ev_log = (np.zeros(S) for _ in range(4))
    ev_buf: dict = {}
    ph_buf: dict = {}
    persist = np.zeros(S)
    np.zeros(S)
    np.zeros(S)
    pdis = np.full(S, 0.3)
    np.arange(S)
    for t in range(T):
        reg = st["rp"][t]
        wstar = st["wt"][t]
        x, y = st["x"][:, t], st["y"][:, t]
        p_d = g.sigmoid(np.einsum("sd,sd->s", x, wd))
        p_o = g.sigmoid(np.einsum("sd,sd->s", x, other))
        p_star = g.sigmoid(x @ wstar)
        act_d, act_o, act_s = (p_d >= g.TAU) * 1.0, (p_o >= g.TAU) * 1.0, (p_star >= g.TAU) * 1.0
        l_d, l_o, l_s = (g.decision_cost(a, y) for a in (act_d, act_o, act_s))
        loss_tot += l_d
        loss_star += l_s
        Q = (st["U"][:, t] < frac) if policy != "frozen" else np.zeros(S, bool)
        q_eff = frac
        if policy in ("cert_switch", "cert_gated"):
            # disagreement-focused querying: the paired increment is identically 0 when the two models act alike
            dis = act_d != act_o
            q_eff = np.minimum(1.0, frac / np.maximum(pdis, 0.05))
            Q = dis & (st["U"][:, t] < q_eff)
            pdis = 0.99 * pdis + 0.01 * dis
        n_q += Q
        # ---------- label arrivals (strictly before t)
        arrive_ph = ph_buf.pop(t - 1, None)
        if policy in ("ph_switch", "hysteresis"):
            if arrive_ph is not None:
                m_, upd = arrive_ph
                ph_m = np.where(upd, ph_m + (m_ - R0_COST) / SD_COST - 0.05, ph_m)
                ph_min = np.minimum(ph_min, ph_m)
            ph_buf[t + delay] = (l_d * Q, Q.copy())
        alarm = np.zeros(S, bool)
        if policy in ("ph_switch", "hysteresis"):
            alarm = (ph_m - ph_min) >= ph_thr
            ph_peak = np.maximum(ph_peak, ph_m - ph_min)
        if policy == "hg_switch":
            hg.absorb(t, np.ones(S, bool))
            alarm = hg.step(t, p_d, (p_d - y) ** 2, l_d, Q * 1.0, 1.0)
        if policy in ("cert_switch", "cert_gated", "cert_uniform"):
            # evidence that the other model is better: d = l_d - l_o (positive favours the other)
            arr = ev_buf.pop(t - 1, None)
            if arr is not None:
                Xa, wla = arr
                ev_c1 = 0.99 * ev_c1 + Xa
                ev_c2 = 0.99 * ev_c2 + Xa * Xa
                ev_n = 0.99 * ev_n + 1
                ev_log = ev_log + wla
            if policy == "cert_uniform":
                q_eff = frac
            X = (Q / q_eff) * (l_d - l_o)
            mean, sec = ev_c1 / (ev_n + 1), ev_c2 / (ev_n + 1)
            # cap uses the inclusion probability on disagreement events (a function of the past only)
            lam = np.minimum(
                np.where(sec > 0, np.maximum(mean, 0) / np.maximum(sec, 1e-12), 0.0),
                0.5 * np.minimum(q_eff, 1.0) / g.FN_COST,
            )
            ev_buf[t + delay] = (X, np.log1p(lam * X))
            alarm = ev_log >= np.log(1 / ALPHA)
            if policy == "cert_gated" and costs is not None:
                remaining = T - t
                est_gain = (
                    np.maximum(mean, 0) * remaining
                )  # IPW mean of d is the per-step gain of swapping
                alarm &= est_gain > KC * max(costs["switch"], costs["rollback"]) * 1.0 + 1e-9
        # ---------- actions
        swapped = np.zeros(S, bool)
        if policy in ("ph_switch", "hg_switch", "cert_switch", "cert_gated", "cert_uniform"):
            swapped = alarm & (t - swap_t > 0)
        elif policy == "hysteresis":
            persist = np.where(alarm, persist + 1, 0)
            swapped = (persist >= 20) & (t - swap_t > 150)
        if swapped.any():
            wd_new = np.where(swapped[:, None], other, wd)
            other_new = np.where(swapped[:, None], wd, other)
            was_other_prev = swapped & prev_dep_was_other
            # roll back when swapping to the model that was deployed before the last swap
            n_rb += was_other_prev
            n_sw += swapped & ~was_other_prev
            prev_dep_was_other = np.where(swapped, ~prev_dep_was_other, prev_dep_was_other)
            # false promotion: the model swapped to is not truly better in the current regime
            ce_d = np.where(dep_id == 0, ctab[0, reg], ctab[1, reg])
            ce_o = np.where(oth_id == 0, ctab[0, reg], ctab[1, reg])
            n_false += swapped & (ce_o >= ce_d - 0.01)
            dep_id, oth_id = np.where(swapped, oth_id, dep_id), np.where(swapped, dep_id, oth_id)
            wd, other = wd_new, other_new
            swap_t = np.where(swapped, t, swap_t)
            ph_m[swapped] = 0.0
            ph_min[swapped] = 0.0
            if hg is not None:
                hg.reset(swapped)
            ev_c1[swapped] = ev_c2[swapped] = ev_n[swapped] = ev_log[swapped] = 0.0
            persist[swapped] = 0
        if policy == "periodic_retrain" and t >= 250 and t % 250 == 0:
            retrain_ready = np.full(S, t + RETRAIN_LAG)
            retrain_w = wstar[None, :] + RETRAIN_NOISE * st["noise"][:, t // 20 + 1]
            n_rt += 1
        if policy == "rolling_recal" and t >= 100 and t % 100 == 0:
            wd = wd + RECAL_STEP * (wstar[None, :] + RECAL_NOISE * st["noise"][:, t // 20 + 1] - wd)
            dep_id = np.full(S, 2)
            n_rc += 1
        if policy == "periodic_retrain":
            ready = retrain_ready == t
            if ready.any():
                wd = np.where(ready[:, None], retrain_w, wd)
                dep_id = np.where(ready, 2, dep_id)
        # recovery time bookkeeping: first time after the first harmful regime step the deployed loss is near the best
        # (measured on realised loss differences, averaged later)
    wall = time.perf_counter() - t0_
    return {
        "loss": loss_tot,
        "loss_star": loss_star,
        "n_q": n_q,
        "n_sw": n_sw,
        "n_rb": n_rb,
        "n_rt": n_rt,
        "n_rc": n_rc,
        "n_false": n_false,
        "runtime_s": wall,
        "ph_peak": ph_peak,
    }


def total_cost(res: dict, c: dict, policy: str) -> np.ndarray:
    return (
        res["loss"]
        + KQ * c["query"] * res["n_q"]
        + KC * c["switch"] * res["n_sw"]
        + KC * c["rollback"] * res["n_rb"]
        + KC * c["retrain"] * res["n_rt"]
        + KC * 0.25 * c["retrain"] * res["n_rc"]
    )


POLICIES = (
    "frozen",
    "periodic_retrain",
    "rolling_recal",
    "ph_switch",
    "hg_switch",
    "cert_uniform",
    "cert_switch",
    "hysteresis",
    "cert_gated",
)
