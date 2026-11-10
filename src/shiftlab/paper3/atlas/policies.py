"""Atlas policies: alarm-driven switchers (CUSUM, Page-Hinkley, e-detector, Wald-economic) and
evidence-gated switchers (thinned-iid, Markov-skeleton, C1 gap-aware Markov) with a shared rollback.

All use the shared budget-paced disagreement acquisition (ported controls.PacedDisagreementAcquisition)
unless stated. Labels: IN_HOUSE_HEURISTIC (alarm switchers, Wald-economic), DOCUMENTED_ADAPTER for
the gating wrappers; C1/C3 are candidate repairs (this workstream). Hyper-parameters are fixed,
registered, UNTUNED defaults (see C_ATLAS_PROTOCOL.md) so every method gets the same (zero) tuning budget.
Evidence uses label-clock outcomes (queried disagreements, x=1 iff challenger right), no IPW.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from .controls import PacedDisagreementAcquisition
from .sim import Event, QueryRequest


# ------------------------------------------------------------------ acquisition
class SpacedAcquisition:
    """C3: spacing-aware acquisition. Eligible only if gap since last query >= gmin and pending < pcap.
    Per-eligible-disagreement propensity spends the remaining budget over the expected number of
    eligible slots (T-t)/(gmin + 1/rate)."""

    def __init__(self, horizon, budget, gmin, pcap, prior_rate=0.25, prior_w=20.0):
        self.T, self.B, self.gmin, self.pcap = int(horizon), int(budget), int(gmin), int(pcap)
        self.prior_rate, self.prior_w = prior_rate, prior_w
        self.n_disagree = 0
        self.last_q = -(10**9)
        self.pending = 0

    def propensity(self, t, remaining, disagree):
        if (
            not disagree
            or remaining <= 0
            or t - self.last_q < self.gmin
            or self.pending >= self.pcap
        ):
            return 0.0
        rate = (self.n_disagree + self.prior_rate * self.prior_w) / (t + self.prior_w)
        slots = max((self.T - t) / (self.gmin + 1.0 / max(rate, 1e-9)), 1e-9)
        return float(min(max(remaining / slots, 0.05), 1.0))

    def note_event(self, disagree):
        self.n_disagree += int(disagree)


# ------------------------------------------------------------------ evidence
class MarkovBetEvidence:
    """Betting e-process on label-clock signs x in {0,1} (1 = challenger right on a queried disagreement).

    Null family H0(rho_max): sign chain with per-event persistence rho in [0, rho_max], marginal
    pi <= 1/2. For a gap g since the previous USED query the g-step predictive satisfies
        P(x=1 | prev=1) <= (1 + rho_max^g)/2 ,   P(x=1 | prev=0) <= 1/2 .
    With m_t that bound and a predictable bet lam_t in [0, cap/m_t], E_t = prod(1 + lam_t (x_t - m_t))
    is a test supermartingale for every member of H0 (conditioning on the used history; query times
    are chosen from released information and independent randomisation, not from the unrevealed sign).
    mode:
      'gapaware' (C1)   : actual gaps, as above.
      'skeleton'        : same bound with one homogeneous nominal gap g_nom (v1 'markov_lr' analogue).
      'thinned'         : use only queries >= thin_gap after the last used one; m=1/2 (iid, no
                          dependence correction; the gap-10 betting baseline).
      'iid'             : m=1/2 on every query (what a dependence-unaware gate does).
    """

    def __init__(self, mode, rho_max=0.95, g_nom=10.0, thin_gap=10, cap=0.8):
        self.mode, self.rho_max, self.g_nom, self.thin_gap, self.cap = (
            mode,
            rho_max,
            g_nom,
            thin_gap,
            cap,
        )
        self.reset()

    def reset(self):
        self.log_e = 0.0
        self.last_x = None
        self.last_t = None
        self.n = 0
        self.sy = 0.0
        self.sy2 = 0.0

    def bound(self, t):
        if self.mode in ("thinned", "iid") or self.last_x is None:
            return 0.5
        g = self.g_nom if self.mode == "skeleton" else max(t - self.last_t, 1)
        return 0.5 * (1.0 + self.rho_max**g) if self.last_x == 1 else 0.5

    def update(self, t, x):
        if self.mode == "thinned" and self.last_t is not None and t - self.last_t < self.thin_gap:
            return
        m = self.bound(t)
        ybar = self.sy / (self.n + 10.0)
        s2 = (self.sy2 + 0.25 * 10.0) / (self.n + 10.0)
        lam = min(max(ybar / (s2 + ybar * ybar), 0.0), self.cap, 0.9 / m)
        y = x - m
        self.log_e += math.log1p(lam * y)
        self.sy += y
        self.sy2 += y * y
        self.n += 1
        self.last_x, self.last_t = x, t


class EDetector:
    """Mixture-over-starts, mixture-over-bet e-detector on D in {-1,+1}: mean_lam sum_s prod (1+lam*sign*D_k).
    sign=+1 detects improvement, sign=-1 detects harm. Alarm at 1/alpha. Shiryaev-Roberts mixture form
    (same as the RMM detector); iid null only."""

    def __init__(self, sign, alpha, lams=(0.15, 0.3, 0.5)):
        self.sign, self.lams = sign, np.array(lams)
        self.thr = 1.0 / alpha
        self.R = np.zeros(len(lams))

    def update(self, d):
        self.R = (1.0 + self.R) * (1.0 + self.lams * self.sign * d)
        return float(self.R.mean()) >= self.thr


class CusumLLR:
    def __init__(self, sign, h, p1=0.65):
        self.sign, self.h = sign, h
        p1 = p1 if sign > 0 else 1 - p1
        self.a, self.b = math.log(p1 / 0.5), math.log((1 - p1) / 0.5)
        self.s = 0.0

    def update(self, d):
        self.s = max(0.0, self.s + (self.a if d > 0 else self.b))
        return self.s >= self.h


class PageHinkley:
    """Classical Page-Hinkley for an increase in the mean of x = sign*D: m += x - xbar - delta; alarm if m - min(m) > lam."""

    def __init__(self, sign, delta=0.1, lam=6.0):
        self.sign, self.delta, self.lam = sign, delta, lam
        self.m = self.mmin = self.sx = 0.0
        self.n = 0

    def update(self, d):
        x = self.sign * d
        self.n += 1
        self.sx += x
        self.m += x - self.sx / self.n - self.delta
        self.mmin = min(self.mmin, self.m)
        return (self.m - self.mmin) >= self.lam


class WaldEcon:
    """Wald SPRT (p0=.5 vs p1=.65) with an economic gate: promote if LLR >= log(1/alpha) AND
    est. payback gain_hat*(T-t) > k. Rollback: reverse SPRT (p=.35 vs .5) crossing log(1/alpha)."""

    def __init__(self, sign, alpha, horizon, k):
        self.sign, self.thr, self.T, self.k = sign, math.log(1 / alpha), horizon, k
        p1 = 0.65 if sign > 0 else 0.35
        self.a, self.b = math.log(p1 / 0.5), math.log((1 - p1) / 0.5)
        self.llr = 0.0
        self.n = 0
        self.nfav = 0

    def update(self, d, t=0, dis_rate=0.2):
        self.llr += self.a if d > 0 else self.b
        self.llr = max(self.llr, -self.thr)  # lower Wald boundary reflects (restart)
        self.n += 1
        self.nfav += int(d > 0)
        if self.llr < self.thr:
            return False
        if self.sign > 0:
            gain = (2 * self.nfav / self.n - 1) * dis_rate
            return gain * (self.T - t) > self.k
        return True


# ------------------------------------------------------------------ policies
class _Base:
    def __init__(self, name, horizon, budget, rng, acq=None):
        self.name = name
        self.T = horizon
        self.rng = rng
        self.acq = acq if acq is not None else PacedDisagreementAcquisition(horizon, budget)
        self.deployed = 0
        self.t = 0
        self.n_pending = 0

    def predict(self, event: Event) -> int:
        self.t = event.t
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        if isinstance(self.acq, SpacedAcquisition):
            self.acq.pending = self.n_pending
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0:
            return QueryRequest(False)
        take = bool(self.rng.random() < q)
        if take:
            self.n_pending += 1
            if isinstance(self.acq, SpacedAcquisition):
                self.acq.last_q = event.t
        return QueryRequest(take, q)


class AlarmSwitcher(_Base):
    """kind in cusum|page_hinkley|edetector|wald_econ. Promote on up-alarm, roll back on a mirrored
    down-alarm; detectors reset after a switch. Consumes labels in release order."""

    def __init__(
        self, kind, horizon, budget, switch_cost, rng, alpha=0.05, h=4.0, name_override=None
    ):
        super().__init__(name_override or kind, horizon, budget, rng)
        self.kind, self.alpha, self.h, self.k = kind, alpha, h, switch_cost
        self._mk()

    def _det(self, sign):
        if self.kind == "cusum":
            return CusumLLR(sign, self.h)
        if self.kind == "page_hinkley":
            return PageHinkley(sign)
        if self.kind == "edetector":
            return EDetector(sign, self.alpha)
        if self.kind == "wald_econ":
            return WaldEcon(sign, self.alpha, self.T, self.k)
        raise ValueError(self.kind)

    def _mk(self):
        self.det = self._det(+1 if self.deployed == 0 else -1)

    def observe(self, fb):
        for f in fb:
            self.n_pending -= 1
            d = int(f.model_losses[0]) - int(f.model_losses[1])
            if d == 0:
                continue
            if self.kind == "wald_econ" and self.det.sign > 0:
                fire = self.det.update(d, self.t, self.acq.n_disagree / max(self.t, 1))
            else:
                fire = self.det.update(d)
            if fire:
                self.deployed = 1 - self.deployed
                self._mk()


class GatedSwitcher(_Base):
    """Promote when a Markov/iid betting gate crosses 2^ep/alpha (alpha spending alpha/2^ep over
    restarts); roll back with the shared down e-detector (alpha_rb). Labels are consumed in QUERY
    order, blocking on the earliest unresolved query, so bets are predictable in query order under any
    delay. On a switch, queries in flight are dropped and the gate restarts."""

    def __init__(
        self,
        name,
        horizon,
        budget,
        rng,
        mode,
        alpha=0.05,
        rho_max=0.95,
        acq=None,
        g_nom=None,
        alpha_rb=0.05,
        max_episodes=4,
    ):
        super().__init__(name, horizon, budget, rng, acq)
        self.alpha, self.alpha_rb, self.max_ep = alpha, alpha_rb, max_episodes
        self.ev = MarkovBetEvidence(mode, rho_max, g_nom if g_nom else horizon / max(budget, 1))
        self.ep = 1
        self.queue: deque = deque()
        self.pend: dict[int, list] = {}
        self.down = None
        self.n_promotions = 0

    def request_labels(self, event, remaining_budget):
        r = super().request_labels(event, remaining_budget)
        if r.requested:
            rec = [event.t, False, 0, 0]
            self.queue.append(rec)
            self.pend[event.t] = rec
        return r

    def observe(self, fb):
        for f in fb:
            rec = self.pend.pop(f.event_id, None)
            if rec is None:
                continue
            self.n_pending -= 1
            d = int(f.model_losses[0]) - int(f.model_losses[1])
            rec[1], rec[2], rec[3] = True, int(d > 0), d
        while self.queue and self.queue[0][1]:
            t0, _, x, d = self.queue.popleft()
            if self.deployed == 0:
                if self.ep > self.max_ep:
                    continue
                self.ev.update(t0, x)
                if self.ev.log_e >= math.log(2.0**self.ep / self.alpha):
                    self._switch(1)
                    break
            else:
                if self.down.update(d):
                    self._switch(0)
                    break

    def _switch(self, to):
        self.deployed = to
        self.pend.clear()
        self.queue.clear()
        self.n_pending = 0
        self.ev.reset()
        if to == 1:
            self.n_promotions += 1
            self.down = EDetector(-1, self.alpha_rb)
        else:
            self.ep += 1
