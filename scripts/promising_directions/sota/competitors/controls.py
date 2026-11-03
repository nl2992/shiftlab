"""Practical control policies for the SOTA comparison.

These are not published competitors. They are the deployable controls the brief requires, so that
any advantage we claim is measured against sensible simple rules and not only against research
methods.

**Every control shares one acquisition rule** (`PacedDisagreementAcquisition`), so that comparing
controls isolates the *switching decision*. That mirrors the instruction to keep acquisition fixed
when comparing inference components.

On naming discipline, which the brief is explicit about: the CUSUM and Shiryaev-Roberts policies
here **are** exact likelihood-ratio procedures, but only for the simple-vs-simple Bernoulli
hypotheses stated in `BernoulliPairedModel`, whose parameters are fixed on development data before
the locked window is read. They are not exact procedures for any other pair of hypotheses, and
calling an arbitrary cumulative statistic a likelihood-ratio test is precisely what we avoid here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from simulator import Event, QueryRequest, ReleasedFeedback  # noqa: F401


# --------------------------------------------------------------------------- acquisition
class PacedDisagreementAcquisition:
    """Budget-paced, disagreement-gated querying with a positive propensity floor.

    This is the acquisition every control shares. It is the same functional form as the P3b
    pacer: spend the remaining budget evenly over the expected remaining disagreement events,
    floored at `p_min` so every eligible event keeps positive propensity.
    """

    def __init__(self, horizon: int, budget: int, p_min: float = 0.05, prior_rate: float = 0.25,
                 prior_w: float = 20.0):
        self.T, self.B, self.p_min = int(horizon), int(budget), float(p_min)
        self.prior_rate, self.prior_w = float(prior_rate), float(prior_w)
        self.n_disagree = 0

    def propensity(self, t: int, remaining: int, disagree: bool) -> float:
        if not disagree or remaining <= 0:
            return 0.0
        rate = (self.n_disagree + self.prior_rate * self.prior_w) / (t + self.prior_w)
        expected_left = max(rate * (self.T - t), 1e-9)
        return float(min(max(remaining / expected_left, self.p_min), 1.0))

    def note_event(self, disagree: bool) -> None:
        self.n_disagree += int(disagree)


# --------------------------------------------------------------------------- observation model
@dataclass(frozen=True)
class BernoulliPairedModel:
    """The observation model the sequential tests are exact for.

    On a **queried disagreement** event exactly one model is wrong, so the paired difference
    `D = l0 - l1` takes values in {-1, +1}. Write `p = P(D = +1)`, the probability the challenger
    is the correct one given a disagreement. Then:

        H0: p = p0   (challenger no better; p0 <= 0.5)
        H1: p = p1   (challenger better;    p1 >  0.5)

    The log-likelihood ratio of a single observation is exactly

        +log(p1/p0)            if D = +1
        +log((1-p1)/(1-p0))    if D = -1

    `p0` and `p1` are **fixed on development data** before the locked window is read. The test is
    exact for this pair of simple hypotheses and for no others.
    """

    p0: float = 0.5
    p1: float = 0.65

    def __post_init__(self):
        if not 0.0 < self.p0 < 1.0 or not 0.0 < self.p1 < 1.0:
            raise ValueError("p0 and p1 must lie strictly inside (0, 1)")
        if self.p1 <= self.p0:
            raise ValueError("p1 must exceed p0 for the challenger-better alternative")

    def llr(self, d: int) -> float:
        if d > 0:
            return math.log(self.p1 / self.p0)
        return math.log((1.0 - self.p1) / (1.0 - self.p0))


class _SequentialControl:
    """Shared machinery: paced acquisition, deployment, and a statistic updated on release."""

    def __init__(self, horizon: int, budget: int, model: BernoulliPairedModel, threshold: float,
                 *, reset_on_switch: bool = True, name: str = "control"):
        self.name = name
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.model = model
        self.threshold = float(threshold)
        self.reset_on_switch = bool(reset_on_switch)
        self.deployed = 0
        self.stat = self._initial()
        self._last_q = 0.0

    def _initial(self) -> float:
        raise NotImplementedError

    def _update(self, stat: float, llr: float) -> float:
        raise NotImplementedError

    def predict(self, event: Event) -> int:
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        self._last_q = q
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self._rng_draw() < q), probability=q)

    def _rng_draw(self) -> float:
        return self.rng.random()

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue  # agreement carries no paired evidence
            self.stat = self._update(self.stat, self.model.llr(d))
            if self.deployed == 0 and self.stat >= self.threshold:
                self.deployed = 1
                if self.reset_on_switch:
                    self.stat = self._initial()

    def decision_state(self) -> str:
        return f"stat={self.stat:.3f};dep={self.deployed}"

    def state_dict(self) -> dict:
        return {"stat": self.stat, "deployed": self.deployed, "n_dis": self.acq.n_disagree}

    def load_state_dict(self, s: dict) -> None:
        self.stat, self.deployed = float(s["stat"]), int(s["deployed"])
        self.acq.n_disagree = int(s["n_dis"])


class PairedCUSUM(_SequentialControl):
    """Page's CUSUM on the paired LLR: `S_t = max(0, S_{t-1} + llr_t)`, switch when `S_t >= h`.

    Exact for the simple-vs-simple Bernoulli pair in `BernoulliPairedModel`; `h` and the reset
    policy are tuned on development data.
    """

    def __init__(self, horizon, budget, model, threshold, *, rng, **kw):
        self.rng = rng
        super().__init__(horizon, budget, model, threshold, name=kw.pop("name", "cusum"), **kw)

    def _initial(self) -> float:
        return 0.0

    def _update(self, stat: float, llr: float) -> float:
        return max(0.0, stat + llr)


class ShiryaevRoberts(_SequentialControl):
    """Shiryaev-Roberts: `R_t = (1 + R_{t-1}) * Lambda_t`, switch when `R_t >= A`.

    Carried in logs for numerical stability: `log R_t = log(1 + R_{t-1}) + llr_t`. Exact for the
    same simple-vs-simple pair; `A` tuned on development data.
    """

    def __init__(self, horizon, budget, model, threshold, *, rng, **kw):
        self.rng = rng
        super().__init__(horizon, budget, model, threshold, name=kw.pop("name", "shiryaev_roberts"),
                         **kw)

    def _initial(self) -> float:
        return -np.inf  # log R_0 = log 0

    def _update(self, stat: float, llr: float) -> float:
        prev = 0.0 if stat == -np.inf else stat
        return float(np.logaddexp(0.0, prev) + llr)


class EconomicReplacement:
    """Development-tuned economic rule: switch when the estimated payback exceeds the cost.

    Point-estimate rule, deliberately simple and deliberately **not** certified: with `phat` the
    observed fraction of queried disagreements favouring the challenger, the estimated per-event
    advantage is `delta = (2*phat - 1) * disagreement_rate`, and the rule switches when

        delta * (T - t) > switch_cost + margin

    `min_obs` and `margin` are fixed on development data. This is the comparator that asks whether
    our certified machinery earns its keep over a plain economic heuristic.
    """

    def __init__(self, horizon, budget, switch_cost, *, rng, min_obs: int = 15,
                 margin: float = 0.0, name: str = "economic_replacement"):
        self.name = name
        self.T, self.cs = int(horizon), float(switch_cost)
        self.acq = PacedDisagreementAcquisition(horizon, budget)
        self.rng = rng
        self.min_obs, self.margin = int(min_obs), float(margin)
        self.deployed = 0
        self.n_obs = 0
        self.n_fav = 0
        self.t = 0
        self._last_q = 0.0

    def predict(self, event: Event) -> int:
        self.t = event.t
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        self._last_q = q
        if q <= 0.0:
            return QueryRequest(requested=False)
        return QueryRequest(requested=bool(self.rng.random() < q), probability=q)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for fb in feedback:
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            self.n_obs += 1
            self.n_fav += int(d > 0)
        if self.deployed == 0 and self.n_obs >= self.min_obs:
            phat = self.n_fav / self.n_obs
            dis_rate = self.acq.n_disagree / max(self.t, 1)
            delta = (2.0 * phat - 1.0) * dis_rate
            if delta * (self.T - self.t) > self.cs + self.margin:
                self.deployed = 1

    def decision_state(self) -> str:
        return f"phat={self.n_fav}/{self.n_obs};dep={self.deployed}"

    def state_dict(self) -> dict:
        return {"n_obs": self.n_obs, "n_fav": self.n_fav, "deployed": self.deployed,
                "n_dis": self.acq.n_disagree}

    def load_state_dict(self, s: dict) -> None:
        self.n_obs, self.n_fav = int(s["n_obs"]), int(s["n_fav"])
        self.deployed, self.acq.n_disagree = int(s["deployed"]), int(s["n_dis"])


class FixedModel:
    """Deploy one model for the whole episode and never query.

    With `index` chosen on development data this is the "pick on dev, then freeze" control; with
    `index=0` it is never-switch.
    """

    def __init__(self, index: int = 0, name: str | None = None):
        self.index = int(index)
        self.name = name or f"fixed_model_{index}"

    def predict(self, event: Event) -> int:
        return self.index

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        return QueryRequest(requested=False)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        pass

    def decision_state(self) -> str:
        return f"fixed={self.index}"

    def state_dict(self) -> dict:
        return {"index": self.index}

    def load_state_dict(self, s: dict) -> None:
        self.index = int(s["index"])


class RetrospectiveOracle(FixedModel):
    """ORACLE REFERENCE, NOT DEPLOYABLE.

    Deploys whichever model has the lower realised loss over the episode, which requires knowing
    the future. It bounds what any policy could achieve with a single switch-free choice and must
    never be reported as a baseline.
    """

    def __init__(self, model_predictions: np.ndarray, labels: np.ndarray):
        losses = (model_predictions != labels[:, None]).mean(axis=0)
        super().__init__(index=int(np.argmin(losses)), name="ORACLE_retrospective_best")
        self.is_oracle = True
