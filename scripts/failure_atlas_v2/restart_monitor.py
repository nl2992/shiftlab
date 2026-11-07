"""Restart-Mixture Monitor (RMM): an attachable recovery wrapper for deployment policies.

Weakness addressed
------------------
Certificate methods (Gated deployment, DISCERN, SMCS) accumulate evidence over all history and
stop acquiring once a verdict fires; posterior/weight methods (Model Picker, CAMS, Gong-Zhang)
accumulate cumulative losses. Either way a change after early evidence is answered slowly or
never: a late improvement is diluted by the early regime, and a reversal after promotion is never
rolled back because nothing is being measured.

Decision rule
-------------
Let X_n = s_n * D_{tau_n} be the n-th queried disagreement outcome (label clock, no inverse
propensity weight), signed so that X_n = +1 means the NON-deployed model was right (s_n = +1 if
model 0 is deployed, -1 otherwise). For bet sizes lambda in a fixed grid Lambda and a fixed grid
of label start indices S (every ``gap`` labels), the detector is

    M_n = (1/|Lambda|) sum_{lambda in Lambda} sum_{s in S, s <= n} pi_s prod_{k=s}^{n} (1 + lambda X_k),

with pi_s = 1/|S|. On M_n >= 1/alpha_k the wrapper switches deployment and RESTARTS the base
policy on the remaining horizon and budget with the newly deployed model as its incumbent; the
detector is reset with alpha_{k+1}. Promotions (switching to the challenger, model 1) spend
alpha_det / 2^j on the j-th promotion alarm; rollbacks to model 0 use alpha_rb.

The wrapper also keeps acquiring after the base stops, with the same budget pacer the base uses,
so the detector always has labels; these labels are not shown to the base.

Validity. Under the uniform conditional null that the challenger is never better on
disagreements, each product from a start s is a nonnegative supermartingale (it is constant 1
before s), so V_n = M_n + sum_{s in S, s > n} pi_s is a nonnegative supermartingale with V_0 = 1
and Ville gives P(sup_n M_n >= 1/alpha) <= alpha. The base runs at alpha_base, so the total
probability of any challenger promotion under that null is at most alpha_base + alpha_det.
Delays: outcomes enter in event order, after release, exactly as in the base adapters.
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

from controls import PacedDisagreementAcquisition  # noqa: E402
from simulator import Event, QueryRequest, ReleasedFeedback  # noqa: E402


class HorizonWeightedPacer(PacedDisagreementAcquisition):
    """Spend density proportional to (T - t)^(k - 1): q_t = k * remaining / (rate * (T - t)).

    k = 1 is the shared uniform pacer; k = 2 spends in proportion to the remaining horizon, i.e.
    to the number of future events a decision made now will govern.
    """

    def __init__(self, horizon, budget, p_min=0.05, k: float = 2.0):
        super().__init__(horizon, budget, p_min=p_min)
        self.k = float(k)

    def propensity(self, t, remaining, disagree):
        if not disagree or remaining <= 0:
            return 0.0
        rate = (self.n_disagree + self.prior_rate * self.prior_w) / (t + self.prior_w)
        expected_left = max(rate * (self.T - t), 1e-9)
        return float(min(max(self.k * remaining / expected_left, self.p_min), 1.0))


class MixtureSRDetector:
    """Weighted Shiryaev-Roberts e-detector over a finite start grid; total prior mass one."""

    def __init__(self, alpha: float, max_labels: int, gap: int = 10,
                 lambdas: tuple[float, ...] = (0.15, 0.3, 0.5), single_start: bool = False,
                 w_first: float | None = None):
        self.alpha = float(alpha)
        self.gap = int(gap)
        self.n_starts = 1 if single_start else max(1, int(math.ceil(max_labels / self.gap)))
        # prior mass of each start; total one. w_first puts extra mass on the first start.
        if self.n_starts == 1:
            self.pis = [1.0]
        elif w_first is None:
            self.pis = [1.0 / self.n_starts] * self.n_starts
        else:
            rest = (1.0 - w_first) / (self.n_starts - 1)
            self.pis = [float(w_first)] + [rest] * (self.n_starts - 1)
        self.lams = np.asarray(lambdas, float)
        self.sr = np.zeros(len(self.lams))
        self.n = 0

    def update(self, x: int) -> bool:
        if self.n % self.gap == 0 and self.n // self.gap < self.n_starts:
            self.sr += self.pis[self.n // self.gap]  # a start enters before its first label
        self.sr *= 1.0 + self.lams * x
        self.n += 1
        return self.stat >= 1.0 / self.alpha

    @property
    def stat(self) -> float:
        return float(self.sr.mean())


class _View:
    """Present the stream to a restarted base with shifted time and permuted model indices."""

    def __init__(self, t0: int, horizon: int, swap: bool):
        self.t0, self.horizon, self.swap = t0, horizon, swap

    def event(self, ev: Event) -> Event:
        preds = ev.model_predictions[::-1].copy() if self.swap else ev.model_predictions
        return Event(event_id=ev.event_id, t=ev.t - self.t0, horizon=self.horizon,
                     model_predictions=preds, context=ev.context)

    def feedback(self, fb: ReleasedFeedback) -> ReleasedFeedback:
        ml = fb.model_losses[::-1].copy() if self.swap else fb.model_losses
        return ReleasedFeedback(event_id=fb.event_id, t_requested=fb.t_requested - self.t0,
                                t_released=fb.t_released - self.t0, label=fb.label,
                                model_losses=ml, query_probability=fb.query_probability,
                                extra=fb.extra)

    def model(self, k: int) -> int:
        return 1 - k if self.swap else k


class RestartMixtureMonitor:
    """Wrap any simulator Policy factory ``make(T, B, alpha, rng)`` with the RMM rule."""

    def __init__(self, make_base, horizon: int, budget: int, alpha: float, *, rng,
                 name: str, alpha_split: float = 0.5, alpha_rb: float | None = None,
                 gap: int = 10, keep_acquiring: bool = True, restart_base: bool = True,
                 p_min: float = 0.05, single_start: bool = False, pace_k: float = 1.0,
                 w_first: float | None = None):
        self.single_start = bool(single_start)
        self.w_first = w_first
        self.name = name
        self.make_base, self.T, self.B = make_base, int(horizon), int(budget)
        self.rng = rng
        self.alpha_base = alpha * (1.0 - alpha_split)
        self.alpha_det = alpha * alpha_split
        self.alpha_rb = alpha if alpha_rb is None else alpha_rb
        self.gap, self.keep, self.restart_base = int(gap), bool(keep_acquiring), bool(restart_base)
        self.acq = HorizonWeightedPacer(horizon, budget, p_min=p_min, k=pace_k)
        self.n_promotions = 0
        self.deployed = 0
        self.view = _View(0, self.T, False)
        self.base = make_base(self.T, self.B, self.alpha_base, rng)
        self.base_owned: set[int] = set()
        self.own: set[int] = set()
        self.queue: dict[int, int] = {}  # event id -> signed outcome, waiting for ordered entry
        self.order: list[int] = []
        self.det = self._new_detector()
        self.t = 0
        self.remaining = self.B
        self.n_alarms = 0
        self.override = False

    def _new_detector(self) -> MixtureSRDetector:
        if self.deployed == 0:  # next alarm would promote the challenger
            a = self.alpha_det / (2.0 ** self.n_promotions)
        else:
            a = self.alpha_rb
        return MixtureSRDetector(a, self.B, self.gap, single_start=self.single_start,
                                 w_first=self.w_first)

    # -- Policy protocol
    def predict(self, event: Event) -> int:
        self.t = event.t
        k = self.view.model(int(self.base.predict(self.view.event(event))))
        if self.override:
            return self.deployed
        if k != self.deployed:  # the base itself switched (under its own alpha_base)
            self.deployed = k
            self.det = self._new_detector()
            self.order, self.queue = [], {}
        return self.deployed

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        self.remaining = remaining_budget
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        req = self.base.request_labels(self.view.event(event), remaining_budget)
        q_own = self.acq.propensity(event.t, remaining_budget, dis)
        self.acq.note_event(dis)
        if req.requested:
            self.base_owned.add(event.t)
            if dis:
                self.order.append(event.t)
            return req
        if self.keep and dis and q_own > 0.0 and self.rng.random() < q_own:
            self.own.add(event.t)
            self.order.append(event.t)
            return QueryRequest(requested=True, probability=q_own)
        return QueryRequest(requested=False)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
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
        alarm = False
        while self.order and self.order[0] in self.queue:
            d = self.queue.pop(self.order.pop(0))
            x = d if self.deployed == 0 else -d
            if self.det.update(x):
                alarm = True
                break
        if alarm:
            self._switch()

    def _switch(self) -> None:
        self.n_alarms += 1
        new = 1 - self.deployed
        if new == 1:
            self.n_promotions += 1
        self.deployed = new
        if self.restart_base:
            h = self.T - (self.t + 1)
            self.view = _View(self.t + 1, max(h, 1), swap=(new == 1))
            self.base = self.make_base(max(h, 1), max(self.remaining, 0), self.alpha_base,
                                       self.rng)
            self.base_owned = set()
        else:
            self.override = True  # ablation: the stale base no longer controls deployment
        self.det = self._new_detector()
        self.order, self.queue = [], {}

    def decision_state(self) -> str:
        return f"dep={self.deployed};alarms={self.n_alarms}"

    def state_dict(self) -> dict:
        return {}

    def load_state_dict(self, s: dict) -> None:
        pass


def _factories():
    from cams import CAMSDeploymentAdapter, stack_advice
    from certificate_stops import DiscernStyleStop, GatedDeploymentStop
    from controls import FixedModel
    from model_picker import ModelPickerDeploymentAdapter
    from smcs import SMCSDeploymentPolicy

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from registry_additions import GongZhangPaidObs

    bases = {
        "gated_deployment": lambda T, B, a, r: GatedDeploymentStop(T, B, a, rng=r),
        "discern_style": lambda T, B, a, r: DiscernStyleStop(T, B, a, 0.0, rng=r),
        "SMCS+retain-incumbent": lambda T, B, a, r: SMCSDeploymentPolicy(2, r, alpha=a),
        "model_picker_adapter": lambda T, B, a, r: ModelPickerDeploymentAdapter(2, 2, r),
        "cams_adapter": lambda T, B, a, r: CAMSDeploymentAdapter(
            n_models=2, n_classes=2, advice_fn=stack_advice(2, []), rng=r),
        "gong_zhang_paid_obs": lambda T, B, a, r: GongZhangPaidObs(T, B, 0.05, rng=r),
        "detector_only": lambda T, B, a, r: FixedModel(0, name="fixed"),
    }
    out = {}
    for nm, mk in bases.items():
        seed_name = {"SMCS+retain-incumbent": "smcs", "model_picker_adapter": "model_picker",
                     "cams_adapter": "cams", "gong_zhang_paid_obs": "gong_zhang"}.get(nm, nm)
        out[f"{nm}+RMM"] = (lambda mk=mk, sn=seed_name: (
            lambda T, B, cs, cq, a, d, r: RestartMixtureMonitor(
                mk, T, B, a, rng=r(sn), name="")))()
        out[f"{nm}+RMM_single"] = (lambda mk=mk, sn=seed_name: (
            lambda T, B, cs, cq, a, d, r: RestartMixtureMonitor(
                mk, T, B, a, rng=r(sn), name="", single_start=True)))()
        out[f"{nm}+RMM_norestart"] = (lambda mk=mk, sn=seed_name: (
            lambda T, B, cs, cq, a, d, r: RestartMixtureMonitor(
                mk, T, B, a, rng=r(sn), name="", restart_base=False)))()
        out[f"{nm}+RMM_noacq"] = (lambda mk=mk, sn=seed_name: (
            lambda T, B, cs, cq, a, d, r: RestartMixtureMonitor(
                mk, T, B, a, rng=r(sn), name="", keep_acquiring=False)))()
    from controls import FixedModel as _Fixed

    def lrmd(**kw):
        return lambda T, B, cs, cq, a, d, r: RestartMixtureMonitor(
            lambda T_, B_, a_, r_: _Fixed(0, name="fixed"), T, B, a, rng=r("lrmd"), name="",
            alpha_split=1.0, **kw)

    out["LRMD"] = lrmd(pace_k=2.0)
    out["LRMD_k1"] = lrmd(pace_k=1.0)
    out["LRMD_k3"] = lrmd(pace_k=3.0)
    out["LRMD_single"] = lrmd(pace_k=2.0, single_start=True)
    out["LRMD_gap25"] = lrmd(pace_k=2.0, gap=25)
    out["LRMD_w50"] = lrmd(pace_k=2.0, w_first=0.5)
    out["LRMD_w50_k1"] = lrmd(pace_k=1.0, w_first=0.5)
    return out


FACTORIES = _factories()
