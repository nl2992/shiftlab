"""Gong-Zhang, Qiu et al. and Ryabchenko et al. adaptations on the common simulator.

Ports of the Failure Atlas v1 R6 adaptations (``src/shiftlab/dive/atlas_r6_baselines.py``) to the
``Policy`` interface. The decision arithmetic is unchanged; the differences are recorded here:

* ADAPTER: the v1 harness exposed only the paired difference; the simulator exposes predictions,
  so querying is gated on disagreement (an agreement label carries no paired information), with
  the shared ``PacedDisagreementAcquisition`` rate. Every other competitor in the suite gates the
  same way, so this removes a handicap rather than adds an advantage.
* ``x = l1 - l0`` (v1 ``D``: action 1 minus action 0), importance weighted by the frozen issue
  propensity carried in ``ReleasedFeedback``.

These are adaptations, not reproductions: the source guarantees (regret bounds) do not transfer.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (SOTA, SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import QueryRequest


def _sigmoid(z):
    return 1.0 / (1.0 + math.exp(-z)) if z >= 0 else math.exp(z) / (1.0 + math.exp(z))


class _Paced:
    def __init__(self, T, budget, delay, cs, rng, name):
        self.T, self.B, self.d, self.cs, self.rng, self.name = T, budget, delay, cs, rng, name
        self.acq = PacedDisagreementAcquisition(T, budget)
        self.act = 0
        self.t = 0

    def predict(self, event):
        self.t = event.t
        self._decide(event.t)
        return self.act

    def _decide(self, t):
        pass

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


class GongZhangPaidObsPolicy(_Paced):
    """Discounted IW benefit estimate; switch when remaining-horizon gain exceeds ``c_s``."""

    def __init__(self, T, budget, delay, cs, rng, name="gong_zhang_paid_obs"):
        super().__init__(T, budget, delay, cs, rng, name)
        self.gamma = 1.0 - 1.0 / max(delay + 1, T / 5.0)
        self.num: list[tuple[int, float]] = []

    def observe(self, feedback):
        for fb in feedback:
            x = float(fb.model_losses[1]) - float(fb.model_losses[0])
            self.num.append((fb.event_id, -x / fb.query_probability))

    def _decide(self, t):
        if len(self.num) < 3:
            return
        g = self.gamma
        s_hat = sum(v * g ** (t - ev) for ev, v in self.num)
        last = t - self.d
        den = (1.0 - g**last) / (1.0 - g) if last > 0 else 1.0
        gain_left = (self.T - t) * s_hat / den
        if self.act == 0 and gain_left > self.cs:
            self.act = 1
        elif self.act == 1 and -gain_left > self.cs:
            self.act = 0


class QiuDelayedMovementPolicy(_Paced):
    """Blocked fixed-share Hedge on IW loss differences (delayed movement-cost reduction)."""

    def __init__(self, T, budget, delay, cs, rng, name="qiu_delayed_movement"):
        super().__init__(T, budget, delay, cs, rng, name)
        self.L = max(delay + 1, math.ceil(T / 20))
        n_blocks = math.ceil(T / self.L)
        k_sw = max(1.0, math.sqrt(n_blocks))
        self.eta = 3.0 * math.sqrt(k_sw / n_blocks) / self.L
        self.share = min(0.5, k_sw / n_blocks)
        self.z, self.buf = 0.0, 0.0

    def observe(self, feedback):
        for fb in feedback:
            x = float(fb.model_losses[1]) - float(fb.model_losses[0])
            self.buf += x / fb.query_probability

    def _decide(self, t):
        if t % self.L == 0 and t > 0:
            self.z = float(np.clip(self.z - self.eta * self.buf, -30, 30))
            self.buf = 0.0
            p = (1.0 - self.share) * _sigmoid(self.z) + self.share / 2.0
            self.z = math.log(p / (1.0 - p))
            self.act = int(p > 0.5)


class RyabchenkoCapacityPolicy(_Paced):
    """One random representative query per block of ``ceil(T/B)``; delayed Hedge on scores.

    ADAPTER: the representative is the first disagreement at or after a uniformly drawn round of
    the block (an agreement label is uninformative), with the frozen probability 1 reported.
    """

    def __init__(self, T, budget, delay, cs, rng, name="ryabchenko_capacity"):
        super().__init__(T, budget, delay, cs, rng, name)
        self.b = max(1, math.ceil(T / max(budget, 1)))
        n_blocks = math.ceil(T / self.b)
        self.u = float(rng.random())
        self.eta = math.sqrt(8.0 * math.log(2.0) / n_blocks) / math.sqrt(
            1.0 + math.ceil(delay / self.b)
        )
        self.score, self.ready = 0.0, 0.0
        self.target, self.done = -1, True

    def observe(self, feedback):
        for fb in feedback:
            self.ready += float(fb.model_losses[0]) - float(fb.model_losses[1])

    def _decide(self, t):
        if t % self.b == 0:
            self.score += self.ready
            self.ready = 0.0
            self.act = int(self.u < _sigmoid(self.eta * self.score))
            self.target = t + int(self.rng.integers(min(self.b, self.T - t)))
            self.done = False

    def request_labels(self, event, remaining_budget):
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        if self.done or remaining_budget <= 0 or event.t < self.target or not dis:
            return QueryRequest(requested=False)
        self.done = True
        return QueryRequest(requested=True, probability=1.0)


def _mk(cls):
    return lambda T, budget, cs, cq, alpha, delay, r, _c=cls: _c(
        T, budget, delay, cs, r(_c.__name__)
    )


EXTRA = {
    "gong_zhang_paid_obs": _mk(GongZhangPaidObsPolicy),
    "qiu_delayed_movement": _mk(QiuDelayedMovementPolicy),
    "ryabchenko_capacity": _mk(RyabchenkoCapacityPolicy),
}
