"""Label-clock evidence (LCE): an attachable correction for IPW-weighted anytime certificates.

Weakness addressed
------------------
Gated deployment, DISCERN and P7s certify the sign of the per-EVENT gain G = E[l0 - l1] from
Horvitz-Thompson increments w_t A_t D_t with w_t = L_t / q_t, consumed on the event clock. Under a
budget the pacer sets q_t < 1, so increments range over [-1/p_min, 1/p_min]; the anytime bounds
must cover that range, and bets are restricted accordingly. The deployment rule needs only the SIGN
of G, and G = rho * m with rho = P(A_t = 1) > 0, m = E[D | A = 1], so the sign is the sign of m.

Decision rule
-------------
Consume ONLY queried disagreements, in event order, each with weight one: X_n = D_{tau_n} in
{-1, +1}, where tau_n is the n-th queried disagreement. Run the base method's own confidence
sequence / e-process on X_n with range 1 instead of 1/p_min.

Validity (conditional null). Let F_t be the full history and suppose
H0: E[D_t | F_{t-1}, A_t = 1] <= 0 for every t (the challenger is never better on disagreements).
The query coin L_t ~ Bernoulli(q_t) uses q_t measurable w.r.t. (F_{t-1}, A_t) and independent
randomness, so E[D_t | F_{t-1}, A_t = 1, L_t = 1] <= 0. By optional sampling at the stopping times
tau_n, (X_n) has conditional means <= 0 given the label-indexed history, so any wealth
prod (1 + lambda_n X_n) with predictable lambda_n in [0, 1) is a nonnegative supermartingale and
Ville's inequality bounds P(ever certify | H0) <= alpha. Delay is handled exactly as in the base
adapters: label n is consumed only after labels 1..n-1 are, and its bet uses only those.

What this does NOT cover: the time-averaged null "sum_t G_t <= 0" when G_t changes sign (the
label clock weights periods by query intensity), and stationary-but-dependent nulls in which past
D_t predict future D_t (then the conditional null itself is false; see regime F5).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from certificate_stops import (  # noqa: E402
    DiscernStyleStop,
    GatedDeploymentStop,
    MopeCS,
    PrPlEBCS,
    _Rec,
)
from simulator import Event, QueryRequest  # noqa: E402


class _LabelClockMixin:
    """Queue only queried disagreements; resolve each with weight one."""

    front_load = False

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if self.stopped or self.exhausted:
            return QueryRequest(requested=False)
        self._on_event_start(event)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        if self.front_load and dis and remaining_budget > 0:
            q = 1.0
        self.acq.note_event(dis)
        if not dis or q <= 0.0:
            if dis and remaining_budget <= 0:
                self.exhausted = True
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        if take:
            rec = _Rec(event.t, False, 1.0, 0)
            self._queue.append(rec)
            self._pending[event.t] = rec
        return QueryRequest(requested=take, probability=q)

    def observe(self, feedback):
        if self.stopped:
            return
        for fb in feedback:
            rec = self._pending.pop(fb.event_id, None)
            if rec is None:
                continue
            rec.w = 1.0  # label clock: no inverse-propensity weight
            rec.d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            rec.resolved = True
        self._flush()


class _FrontLoadMixin:
    """Ablation: the base (IPW, event-clock) method with q = 1 on every disagreement."""

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        orig = self.acq.propensity

        def pinned(t, remaining, disagree):
            return 1.0 if (disagree and remaining > 0) else 0.0

        self.acq.propensity = pinned
        try:
            return super().request_labels(event, remaining_budget)
        finally:
            self.acq.propensity = orig


class GatedLCE(_LabelClockMixin, GatedDeploymentStop):
    def __init__(self, *a, front_load=False, **k):
        super().__init__(*a, **k)
        self.cs = MopeCS(self.alpha, 2.0)  # every weight is 1 <= wmax
        self.front_load = front_load


class DiscernLCE(_LabelClockMixin, DiscernStyleStop):
    def __init__(self, *a, front_load=False, **k):
        super().__init__(*a, **k)
        self.c = 1.0  # increments are D in {-1, +1}
        self.cs1 = PrPlEBCS(self.alpha, self.cs1.lam_max)
        self.front_load = front_load


class GatedFrontLoad(_FrontLoadMixin, GatedDeploymentStop):
    pass


class DiscernFrontLoad(_FrontLoadMixin, DiscernStyleStop):
    pass


FACTORIES = {
    "gated_LCE": lambda T, B, cs, cq, a, d, r: GatedLCE(T, B, a, rng=r("gated_deployment")),
    "gated_LCE_front": lambda T, B, cs, cq, a, d, r: GatedLCE(
        T, B, a, rng=r("gated_deployment"), front_load=True),
    "gated_frontload_ipw": lambda T, B, cs, cq, a, d, r: GatedFrontLoad(
        T, B, a, rng=r("gated_deployment")),
    "discern_LCE": lambda T, B, cs, cq, a, d, r: DiscernLCE(T, B, a, 0.0, rng=r("discern_style")),
    "discern_LCE_front": lambda T, B, cs, cq, a, d, r: DiscernLCE(
        T, B, a, 0.0, rng=r("discern_style"), front_load=True),
    "discern_frontload_ipw": lambda T, B, cs, cq, a, d, r: DiscernFrontLoad(
        T, B, a, 0.0, rng=r("discern_style")),
}

__all__ = ["FACTORIES", "GatedLCE", "DiscernLCE", "np"]
