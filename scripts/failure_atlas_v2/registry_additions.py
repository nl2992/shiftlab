"""Adapters for mandatory-registry entries 4, 11 and 13 (added 2026-11-03).

None of these papers ships code; each class is ported from the printed algorithm box and is an
ADAPTER to the two-frozen-model deployment contract, never "the published method".

* ``GongZhangPaidObs`` -- Gong & Zhang (ICML 2026), Algorithm 1 "Adversarial Contextual Algorithm
  with Paid Observations". Policy class Pi = {always-0, always-1} (loss streams carry no
  context). Weights w_t(pi) = exp(-eta_t sum_s lhat_s(pi)); q_t(a) = (1-gamma) w-share + gamma/|A|;
  per-action observation probability p_t(a) = min{1, sqrt(eta_t q_t(a) / c_t(a))}; IPW estimate
  lhat_t(a) = 1{a in O_t} l_t(a) / p_t(a). eta_t from Theorem 2.1 with constant cost c:
  eta_t = ((sum_{s<=t} sqrt(|A| c)) / ln|Pi|)^{-2/3} capped by sqrt(ln|Pi| / t); gamma = 1/T.
  ADAPTER: one label reveals BOTH models' losses, so O_t is all-or-nothing with probability
  max_a p_t(a), and both estimates use that probability. ADAPTER: deploy argmax q_t keeping the
  incumbent on ties (sampling a_t ~ q_t would pay the switch cost at random). ADAPTER: labels
  arrive after the delay and are applied with the issue-time probability; hard budget.
* ``QiuMovementOCO`` -- Qiu, Jacobsen, Esposito & Zhang (ICML 2026), Algorithms 1-3 (composite
  mirror descent with log regulariser, parameter-free grid, adaptive first-order reduction).
  ADAPTER: decision w in [0,1] = deployment weight on the challenger, linear loss
  f_t(w) = w * ghat_t with ghat_t an IPW estimate of l1 - l0, movement coefficient lambda = c_s.
  Equation (1) is solved in closed form on w >= 0 then clipped to [0,1]; the grid sum is clipped
  to [0,1]. Deployment = 1{w_t > 1/2}. The paper has no acquisition; the shared paced
  disagreement rule supplies labels. Gradients enter when released (delayed).
* ``DelayedFTRLCapacity`` -- Ryabchenko, Attias & Roy (2025), full-information Delayed FTRL with
  a capacity limit C on simultaneously tracked rounds (fixed delay: optimal C = Theta(1)).
  ADAPTER: Hedge over the two models on IPW losses, eta = sqrt(ln K / ((d+1) T)); a label is
  requested on a disagreement only while fewer than C are pending, paced by the budget.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback


class _Base:
    name = "base"

    def state_dict(self) -> dict:
        return {}

    def load_state_dict(self, s: dict) -> None:
        pass

    def decision_state(self) -> str:
        return f"dep={self.deployed}"


class GongZhangPaidObs(_Base):
    name = "gong_zhang_paid_obs"

    def __init__(self, horizon, budget, label_price, *, rng):
        self.T, self.c, self.rng = int(horizon), float(label_price), rng
        self.K, self.lnPi = 2, math.log(2.0)
        self.gamma = 1.0 / self.T
        self.lhat = np.zeros(2)
        self.deployed = 0
        self.t = 0

    def _eta(self, t: int) -> float:
        acc = t * math.sqrt(self.K * self.c)
        a = (acc / self.lnPi) ** (-2.0 / 3.0) if acc > 0 else float("inf")
        return min(a, math.sqrt(self.lnPi / max(t, 1)))

    def _q(self, t: int) -> np.ndarray:
        e = self._eta(t)
        z = -e * (self.lhat - self.lhat.min())
        w = np.exp(z)
        return (1 - self.gamma) * w / w.sum() + self.gamma / self.K

    def predict(self, event: Event) -> int:
        self.t = event.t + 1
        q = self._q(self.t)
        if q[1 - self.deployed] > q[self.deployed]:
            self.deployed = int(np.argmax(q))
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        if remaining_budget <= 0:
            return QueryRequest(requested=False)
        q = self._q(self.t)
        p = float(min(1.0, max(math.sqrt(self._eta(self.t) * qa / self.c) for qa in q)))
        take = bool(self.rng.random() < p)
        return QueryRequest(requested=take, probability=p)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            self.lhat += np.asarray(fb.model_losses[:2], float) / fb.query_probability


class QiuMovementOCO(_Base):
    name = "qiu_movement_oco"

    def __init__(self, horizon, budget, switch_cost, *, rng, p_min=0.05, eps=1.0):
        self.T, self.lam, self.rng = int(horizon), float(switch_cost), rng
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.L = 1.0 / p_min + self.lam  # L >= G + lambda_max (Theorem 3.1)
        n = math.ceil(math.log2(self.L * math.sqrt(self.T) / 1.0)) + 1
        self.etas = [min(2.0**i / (self.L * math.sqrt(self.T)), 1.0 / self.L) for i in range(n)]
        self.etas = sorted(set(self.etas))
        self.alpha = eps / self.T
        self.w = np.zeros(len(self.etas))  # one Algorithm-1 instance per eta (Algorithm 2)
        self.H = 0.0  # Algorithm 3 accumulator
        self.deployed = 0

    def _play(self) -> float:
        return float(min(max(self.w.sum(), 0.0), 1.0))

    def _alg1_step(self, g: float, lam_next: float) -> None:
        for i, eta in enumerate(self.etas):
            gamma = 1.0 / (eta * self.T)
            beta = abs(g) + lam_next
            wt = max(self.w[i], 0.0)
            grad_psi = math.log(wt / self.alpha + 1.0) / eta
            expo = eta * (grad_psi - g - (eta * beta * beta + gamma))
            nxt = self.alpha * (math.exp(min(expo, 50.0)) - 1.0)
            self.w[i] = min(max(nxt, 0.0), 1.0)

    def predict(self, event: Event) -> int:
        w = self._play()
        self.deployed = int(w > 0.5)
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            g = (int(fb.model_losses[1]) - int(fb.model_losses[0])) / fb.query_probability
            self.H += g  # Algorithm 3: accumulate until it outweighs the movement cost
            if abs(self.H) > self.lam:
                self._alg1_step(self.H, self.lam)
                self.H = 0.0


class DelayedFTRLCapacity(_Base):
    name = "delayed_ftrl_capacity"

    def __init__(self, horizon, budget, delay, *, rng, capacity=2, p_min=0.05):
        self.T, self.rng, self.C = int(horizon), rng, int(capacity)
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.eta = math.sqrt(math.log(2.0) / ((delay + 1) * self.T))
        self.lhat = np.zeros(2)
        self.pending = 0
        self.deployed = 0

    def predict(self, event: Event) -> int:
        z = -self.eta * (self.lhat - self.lhat.min())
        w = np.exp(z)
        w = w / w.sum()
        if w[1 - self.deployed] > w[self.deployed]:
            self.deployed = int(np.argmax(w))
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if q <= 0.0 or self.pending >= self.C:
            return QueryRequest(requested=False)
        take = bool(self.rng.random() < q)
        self.pending += int(take)
        return QueryRequest(requested=take, probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            self.pending -= 1
            self.lhat += np.asarray(fb.model_losses[:2], float) / fb.query_probability


FACTORIES = {
    "gong_zhang_paid_obs": lambda T, B, cs, cq, alpha, delay, r: GongZhangPaidObs(
        T, B, cq, rng=r("gong_zhang")
    ),
    "qiu_movement_oco": lambda T, B, cs, cq, alpha, delay, r: QiuMovementOCO(
        T, B, cs, rng=r("qiu")
    ),
    "delayed_ftrl_capacity": lambda T, B, cs, cq, alpha, delay, r: DelayedFTRLCapacity(
        T, B, delay, rng=r("ryabchenko")
    ),
}
