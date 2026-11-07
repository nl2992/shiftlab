"""P1 x P2 merge: restart monitoring (RMM) on dependence-robust evidence (A5b's gap-indexed Markov SUI).

RMM-SUI keeps RMM's architecture (host certificate + restart detector + continued acquisition + switch
on alarm, alpha split host/detector, promotion alarms at alpha_det / 2^j) and changes two things:

1. Host: A5b (fam_a.FamA with SUI evidence and adaptive density), valid under the stationary
   first-order Markov sign null for any rho, instead of an iid-valid certificate.
2. Detector: fam_a.MarkovSUI (started mixture with gap-indexed null upper bound) instead of the
   iid Shiryaev-Roberts mixture, thresholded at 1 / alpha_k.

Validity bookkeeping (why it differs from RMM): the Markov conditional bound for an outcome is valid only
when it conditions on the MOST RECENT observed outcome. So the detector (a) receives every queried
disagreement outcome in event order, none dropped at a switch, and (b) carries the last observed
outcome and its event id across detector restarts. The host is never restarted (RMM's restart had no
measurable effect in the Atlas v2 ablation); after a detector alarm the monitor overrides deployment.
Under the null class every detector is a test supermartingale with respect to the filtration of
observed outcomes and predictable query decisions, so P(first false promotion) <= alpha_host +
alpha_det = alpha. Not covered: non-Markov dependence, time-varying p_t.
"""

from __future__ import annotations

import sys

import fam_a
from controls import FixedModel

_RMM = sys.modules["atlas_v2_restart_monitor"]  # loaded by registry._rmm()


class SUIDetector:
    def __init__(self, alpha: float):
        self.alpha = float(alpha)
        self.sui = fam_a.MarkovSUI(**fam_a._B)

    def update_at(self, hit: int, gap: int, prev) -> bool:
        return self.sui.update(hit, gap, prev) >= 1.0 / self.alpha


class RMMSUI(_RMM.RestartMixtureMonitor):
    def __init__(self, make_base, horizon, budget, alpha, *, rng, name="", **kw):
        self.last = None  # (z, event id) of the most recent observed disagreement, any segment
        super().__init__(
            make_base, horizon, budget, alpha, rng=rng, name=name, restart_base=False, **kw
        )

    def _new_detector(self):
        a = self.alpha_det / (2.0**self.n_promotions) if self.deployed == 0 else self.alpha_rb
        return SUIDetector(a)

    def predict(self, event):
        self.t = event.t
        k = self.view.model(int(self.base.predict(self.view.event(event))))
        if self.override:
            return self.deployed
        if k != self.deployed:  # the host switched under its own alpha: new detector, keep context
            self.deployed = k
            self.det = self._new_detector()
        return self.deployed

    def observe(self, feedback):
        to_base = []
        for fb in feedback:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if fb.event_id in self.base_owned:
                self.base_owned.discard(fb.event_id)
                to_base.append(self.view.feedback(fb))
            else:
                self.own.discard(fb.event_id)
            if d != 0:
                self.queue[fb.event_id] = d
        if to_base:
            self.base.observe(to_base)
        while self.order and self.order[0] in self.queue:
            e = self.order.pop(0)
            z = int(self.queue.pop(e) > 0)  # 1: challenger (model 1) right
            hit = z if self.deployed == 0 else 1 - z  # tested direction: the non-deployed model
            prev, gap = None, 0
            if self.last is not None:
                prev = self.last[0] if self.deployed == 0 else 1 - self.last[0]
                gap = e - self.last[1]
            self.last = (z, e)
            if self.det.update_at(hit, gap, prev):
                self._switch_keep()

    def _switch_keep(self):
        self.n_alarms += 1
        new = 1 - self.deployed
        if new == 1:
            self.n_promotions += 1
        self.deployed = new
        self.override = True
        self.det = self._new_detector()


def _a5b(T, B, a, r):
    return fam_a.FamA(
        T,
        B,
        a,
        rng=r,
        name="A5b-host",
        evidence="sui",
        density="adaptive",
        rho_sig=2.0,
        sui_kw=fam_a._B,
    )


def _gar(T, B, a, r):
    from strong_hosts import GatedAdaptiveRange

    return GatedAdaptiveRange(T, B, a, rng=r)


EXTRA = {
    # merged method: dependence-robust host + dependence-robust restart detector
    "M_RMMSUI_A5b": lambda T, B, cs, cq, a, d, r: RMMSUI(_a5b, T, B, a, rng=r("QSG")),
    # ablation: iid-valid host (strong gated re-port) with the SUI detector (isolates the host leak)
    "M_RMMSUI_gar": lambda T, B, cs, cq, a, d, r: RMMSUI(
        _gar, T, B, a, rng=r("gated_adaptive_range")
    ),
    # standalone: detector only on a fixed incumbent, all alpha to the detector (LRMD analogue)
    "M_LRMD_SUI": lambda T, B, cs, cq, a, d, r: RMMSUI(
        lambda T_, B_, a_, r_: FixedModel(0, name="fixed"), T, B, a, rng=r("lrmd"), alpha_split=1.0
    ),
}
