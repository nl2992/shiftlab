"""Stage 5 recovery policies (docs/paper1_eqsdp/15_STAGE3_FAILURE_TRACE_AND_RECOVERY.md, section 3).

New code only. Everything subclasses ``Stage2Policy`` (arm R evidence, Beta posterior on discounted
counts, unchanged switching rule); the frozen Stage 1-3 behaviour is not edited.

Information rule: a policy sees ``event`` (event_id, t, horizon, model_predictions), the remaining
budget, released feedback (event_id, t_requested, t_released, model_losses) and the declared
contract (T, B, c_s, c_q, delay). It never reads ``feedback.label``, ``feedback.extra``,
``feedback.query_probability`` or ``event.context`` (tested with attribute-guarded proxies).

Arms
----
``Stage5R1``       evidence-insurance floor: C1 reachability suppression (``p_cross``), but (i) when
                   the gate says skip, the label is bought anyway so that the unconditional query
                   rate on that disagreement event is ``min(q, f)`` (absolute floor f) and (ii) a
                   disagreement event is force-bought when more than ``G`` events have passed since
                   the last purchase (any time before the cutoff).
``Stage5Calendar`` control for R1: a uniform purchase schedule of ``m`` labels at disagreement events
                   between t=0 and the cutoff, ignoring the pacer and the evidence.
``Stage5R2``       one-label economic EVSI with a change hazard. A grid Bayesian filter over the
                   disagreement-outcome parameter p (41 midpoints, uniform prior) with a persistence/
                   hazard mixture (per event, with prob. hz, p is redrawn from the prior) is updated
                   from released labels only. At an offered draw the policy evaluates the one-step
                   preposterior of a label released at t+delay, integrating the outcomes of the
                   ``pending`` (requested, unreleased) labels as uncertain futures:
                       J(info) = r * H' * E_post[regret of the deployed decision] + c_s * 1[switch],
                   H' = T - (t + delay), r the prediction-only disagreement rate, with the decision
                   after the info given by arm R's own rule (gamma-quantile payback > c_s) applied to
                   the filter posterior. Modes: ``evsi`` (R2: query iff c_q + lambda_t < EVSI),
                   ``tail`` (R3: query iff EVSI condition OR CVaR_0.95(J_skip - J_query) >= tau),
                   ``tail_only`` (ablation: query iff CVaR_0.95 >= tau), ``entropy`` (control: query
                   iff the entropy of the filter posterior exceeds ``theta``).
                   lambda_t = lambda0 * min(max(E_left / v_rem - 1, 0), 10) as in C1.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulator import QueryRequest
from stage2_policies import Stage2Policy

# C1 suppression parameters inherited from the frozen Stage 2 candidate (rho0, s, h); evidence is
# arm R (lam .98, gamma .3). bw = 0 as in the frozen candidate.
C1_PARAMS = {"rho0": 0.0079, "s": 0.7779, "h": 12, "bw": 0.0, "gs": 0.0}
GRID_N = 41
CVAR_LEVEL = 0.95


class Stage5Base(Stage2Policy):
    """Arm R with a re-implemented ``request_labels`` that passes the propensity ``q`` to the keep
    hook and supports a forced-purchase rule. With the hooks inactive it equals ``Stage2Policy``."""

    def __init__(self, *a, cutoff=None, gap=None, **kw):
        kw["stop_h"] = None if cutoff is None else int(cutoff)
        super().__init__(*a, **kw)
        self.gap = None if gap is None else int(gap)
        self.last_buy = 0

    def _open(self, t):
        return self.stop_h is None or t + self.delay <= self.T - self.stop_h

    def keep_q(self, event, remaining_budget, q) -> bool:  # pragma: no cover - overridden
        return True

    def request_labels(self, event, remaining_budget):
        self.rem = int(remaining_budget)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, self.virtual_remaining(remaining_budget), dis)
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            return QueryRequest(requested=False)
        q = min(1.0, q * self.mf)
        take = False
        if q > 0.0:
            take = bool(self.rng.random() < q)
            if take and not self._keep(event, remaining_budget, q):
                take = False
                self.skipped += 1
        forced = (
            not take
            and self.gap is not None
            and self._open(event.t)
            and event.t - self.last_buy >= self.gap
        )
        if forced:
            take, q = True, 1.0
        if take:
            self.last_buy = event.t
        self.pending += int(take)
        return QueryRequest(requested=take, probability=q if take else 0.0)

    def _keep(self, event, remaining_budget, q) -> bool:
        if not self._open(event.t):
            self.undo += 1  # cutoff skips are not debited from the pacer view
            return False
        return self.keep_q(event, remaining_budget, q)


# ---------------------------------------------------------------------------------------------
# R1: evidence-insurance floor
# ---------------------------------------------------------------------------------------------
class Stage5R1(Stage5Base):
    def __init__(self, *a, f=0.2, **kw):
        for k, v in C1_PARAMS.items():
            kw.setdefault(k, v)
        super().__init__(*a, **kw)
        self.f = float(f)

    def keep_q(self, event, remaining_budget, q):
        pc = self.p_cross(event.t)
        vrem = max(self.virtual_remaining(remaining_budget), 1.0)
        e_left = self._rate() * (self.T - event.t)
        pressure = min(max(e_left / vrem - 1.0, 0.0), 10.0)
        if pc >= self.rho0 * (1.0 + self.s * pressure):
            return True
        return bool(self.rng.random() < min(1.0, self.f / q))


class Stage5Calendar(Stage5Base):
    """Uniform schedule of ``m`` purchases at disagreement events in [0, T - cutoff - delay]."""

    def __init__(self, *a, m=30, **kw):
        kw["rho0"] = 0.0
        super().__init__(*a, **kw)
        span = self.T - (self.stop_h or 0) - self.delay + 1
        self.m = int(m)
        self.sched = [int((j + 0.5) * span / self.m) for j in range(self.m)] if self.m else []
        self.j = 0

    def request_labels(self, event, remaining_budget):
        self.rem = int(remaining_budget)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        self.acq.note_event(dis)
        if not dis or remaining_budget <= 0 or self.j >= self.m or not self._open(event.t):
            return QueryRequest(requested=False)
        if event.t < self.sched[self.j]:
            return QueryRequest(requested=False)
        while self.j < self.m and self.sched[self.j] <= event.t:
            self.j += 1
        self.pending += 1
        self.last_buy = event.t
        return QueryRequest(requested=True, probability=1.0)


# ---------------------------------------------------------------------------------------------
# R2 / R3 and controls: hazard filter + one-step preposterior
# ---------------------------------------------------------------------------------------------
class HazardFilter:
    """Grid Bayes filter for p = P(challenger correct | disagreement) with redraw hazard ``hz``."""

    def __init__(self, hz, n=GRID_N):
        self.hz = float(hz)
        self.p = (np.arange(n) + 0.5) / n
        self.logp, self.log1p = np.log(self.p), np.log1p(-self.p)
        self.prior = np.full(n, 1.0 / n)
        self.w = self.prior.copy()
        self.tau = 0

    def at(self, t):
        keep = (1.0 - self.hz) ** max(t - self.tau, 0)
        return keep * self.w + (1.0 - keep) * self.prior

    def update(self, z, t):
        w = self.at(t) * (self.p if z else 1.0 - self.p)
        self.w = w / w.sum()
        self.tau = max(self.tau, t)


def _binom_logpmf(m, logp, log1p):
    s = np.arange(m + 1)
    lc = gammaln(m + 1) - gammaln(s + 1) - gammaln(m - s + 1)
    return lc[None, :] + s[None, :] * logp[:, None] + (m - s)[None, :] * log1p[:, None]


def preposterior(w, filt, pending, deployed, gamma, cs, rate, hp, rule="mean"):
    """One-step preposterior of a label released at t+delay with ``pending`` other labels also in
    flight. Returns (EVSI, CVaR_0.95 of J_skip - J_query), both exact enumerations on the grid."""
    p, n = filt.p, len(filt.p)
    P = int(pending)
    bp = np.exp(_binom_logpmf(P, filt.logp, filt.log1p))  # n x (P+1)
    bq_log = _binom_logpmf(P + 1, filt.logp, filt.log1p)  # n x (P+2)
    wsk = w[:, None] * bp
    wq = w[:, None] * np.exp(bq_log)
    scale = rate * hp

    def decide(joint):
        mass = joint.sum(axis=0)
        post = joint / np.where(mass > 1e-300, mass, 1.0)[None, :]
        if rule == "mean":  # Bayes rule on posterior expected loss differences
            q = (post * p[:, None]).sum(axis=0)
        else:  # arm R's gamma-quantile payback rule applied to the filter posterior
            cdf = np.cumsum(post, axis=0)
            lev = gamma if deployed == 0 else 1.0 - gamma
            q = p[np.minimum((cdf >= lev - 1e-12).argmax(axis=0), n - 1)]
        gain = (2.0 * q - 1.0) * scale if deployed == 0 else (1.0 - 2.0 * q) * scale
        return np.where(gain > cs, 1 - deployed, deployed)

    d_sk, d_q = decide(wsk), decide(wq)
    reg0, reg1 = np.maximum(2 * p - 1, 0.0) * scale, np.maximum(1 - 2 * p, 0.0) * scale

    def cost(d):  # n x len(d): cost of landing on decision d[k] when the true parameter is p[j]
        return (
            np.where(d[None, :] == 0, reg0[:, None], reg1[:, None]) + cs * (d != deployed)[None, :]
        )

    c_sk = cost(d_sk)  # n x (P+1)
    c_q = cost(d_q)  # n x (P+2)
    # atoms (j, s, z): weight w_j Bin(s; P, p_j) Bern(z; p_j)
    w1 = wsk * p[:, None]
    w0 = wsk * (1.0 - p)[:, None]
    delta0 = c_sk - c_q[:, :-1]  # z = 0 -> outcome count s
    delta1 = c_sk - c_q[:, 1:]  # z = 1 -> outcome count s + 1
    evsi = float((w0 * delta0).sum() + (w1 * delta1).sum())
    d_all = np.concatenate([delta0.ravel(), delta1.ravel()])
    w_all = np.concatenate([w0.ravel(), w1.ravel()])
    order = np.argsort(-d_all)
    cw = np.cumsum(w_all[order])
    tail = 1.0 - CVAR_LEVEL
    k = int(np.searchsorted(cw, tail))
    ws = w_all[order][: k + 1].copy()
    ws[-1] -= max(cw[k] - tail, 0.0) if k < len(cw) else 0.0
    cvar = float((ws * d_all[order][: k + 1]).sum() / tail)
    return evsi, cvar


class Stage5R2(Stage5Base):
    def __init__(self, *a, mode="evsi", hz=5e-4, lam0=0.0, tau=1.0, theta=2.5, rule="mean", **kw):
        kw["rho0"] = 0.0
        super().__init__(*a, **kw)
        self.rule = rule
        assert mode in ("evsi", "tail", "tail_only", "entropy")
        self.mode, self.lam0, self.tau, self.theta = mode, float(lam0), float(tau), float(theta)
        self.filt = HazardFilter(hz)

    def observe(self, feedback):
        fbs = sorted(feedback, key=lambda f: f.event_id)
        super().observe(feedback)
        for fb in fbs:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d != 0:
                self.filt.update(d > 0, fb.t_requested)

    def keep_q(self, event, remaining_budget, q):
        t = event.t
        w = self.filt.at(t)
        if self.mode == "entropy":
            return bool(-(w * np.log(w)).sum() > self.theta)
        hp = self.T - (t + self.delay)
        if hp <= 0:
            return False
        evsi, cvar = preposterior(
            w,
            self.filt,
            self.pending,
            self.deployed,
            self.gamma,
            self.cs,
            self._rate(),
            hp,
            self.rule,
        )
        if self.mode == "tail_only":
            return bool(cvar >= self.tau)
        vrem = max(self.virtual_remaining(remaining_budget), 1.0)
        e_left = self._rate() * (self.T - t)
        pressure = min(max(e_left / vrem - 1.0, 0.0), 10.0)
        ok = evsi > self.cq + self.lam0 * pressure
        if self.mode == "tail":
            ok = ok or cvar >= self.tau
        return bool(ok)


def evsi_k(w, filt, pending, k, deployed, gamma, cs, rate, hp, rule="mean"):
    """EVSI of a bundle of ``k`` new labels (all released at t+delay) with ``pending`` others in
    flight; k = 1 equals ``preposterior``'s EVSI. Exact enumeration on the grid."""
    p, n = filt.p, len(filt.p)
    P = int(pending)
    bp = np.exp(_binom_logpmf(P, filt.logp, filt.log1p))  # n x (P+1)
    bk = np.exp(_binom_logpmf(k, filt.logp, filt.log1p))  # n x (k+1)
    bt = np.exp(_binom_logpmf(P + k, filt.logp, filt.log1p))  # n x (P+k+1)
    scale = rate * hp

    def decide(joint):
        mass = joint.sum(axis=0)
        post = joint / np.where(mass > 1e-300, mass, 1.0)[None, :]
        if rule == "mean":
            q = (post * p[:, None]).sum(axis=0)
        else:
            cdf = np.cumsum(post, axis=0)
            lev = gamma if deployed == 0 else 1.0 - gamma
            q = p[np.minimum((cdf >= lev - 1e-12).argmax(axis=0), n - 1)]
        gain = (2.0 * q - 1.0) * scale if deployed == 0 else (1.0 - 2.0 * q) * scale
        return np.where(gain > cs, 1 - deployed, deployed)

    reg0, reg1 = np.maximum(2 * p - 1, 0.0) * scale, np.maximum(1 - 2 * p, 0.0) * scale

    def cost(d):
        return (
            np.where(d[None, :] == 0, reg0[:, None], reg1[:, None]) + cs * (d != deployed)[None, :]
        )

    wsk = w[:, None] * bp
    c_sk, c_t = cost(decide(wsk)), cost(decide(w[:, None] * bt))
    return float(
        sum((wsk * bk[:, z : z + 1] * (c_sk - c_t[:, z : z + P + 1])).sum() for z in range(k + 1))
    )


class Stage5R2Roll(Stage5R2):
    """R2-roll: short joint rollout. Query now iff some bundle size k <= kmax of labels (this one
    plus k-1 further labels bought at the next disagreement events and released together) has a
    positive net value, EVSI_k > k * (c_q + lambda_t). One label cannot flip the decision when the
    posterior is locked; a bundle can, which is the starvation mechanism of doc 15 section 2."""

    def __init__(self, *a, kmax=2, **kw):
        kw["mode"] = "evsi"
        super().__init__(*a, **kw)
        self.kmax = int(kmax)

    def keep_q(self, event, remaining_budget, q):
        t = event.t
        hp = self.T - (t + self.delay)
        if hp <= 0:
            return False
        w = self.filt.at(t)
        vrem = max(self.virtual_remaining(remaining_budget), 1.0)
        pressure = min(max(self._rate() * (self.T - t) / vrem - 1.0, 0.0), 10.0)
        price = self.cq + self.lam0 * pressure
        for k in range(1, self.kmax + 1):
            ev = evsi_k(
                w, self.filt, self.pending, k, self.deployed, self.gamma, self.cs,
                self._rate(), hp, self.rule,
            )  # fmt: skip
            if ev > k * price:
                return True
        return False


# ---------------------------------------------------------------------------------------------
# dynamic registry (kind + kwargs; filled in worker processes)
# ---------------------------------------------------------------------------------------------
KINDS = {"r1": Stage5R1, "cal": Stage5Calendar, "r2": Stage5R2, "r2roll": Stage5R2Roll}


def make_factory(spec: dict, name: str):
    spec = dict(spec)
    cls = KINDS[spec.pop("kind")]

    def f(T, B, cs, cq, alpha, delay, r):
        return cls(T, B, cs, rng=r("EQSD"), delay=delay, name=name, cq=cq, **spec)

    return f
