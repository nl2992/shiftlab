"""Simulator adapter for B3+ P7s ("settled" acquisition): ``P7sPolicy``.

``P7sPolicy`` owns a real ``b3_plus_policy.CertPlus(n=1, ...)`` configured as
``PlusParams(variant="P7s", acq_shape="settled", r_max=1.0, r_floor=0.25, settled_floor=0.0,
use_hopeless=True)`` and drives ``CertPlus.step`` itself. The issue rule (pacer, certified
bounds, hopeless/settled gate), the frozen bets, the margin-grid e-processes, the delayed release
and the promotion/rollback decision are all CertPlus's own arithmetic. Nothing of it is copied.

What is re-implemented (nothing else): (1) the split of one ``step`` call across the simulator's
predict / request_labels / observe callbacks, and (2) the supply of the paired loss increment.

Why ``step`` can be called from ``request_labels``
--------------------------------------------------
``CertPlus.step(t, ...)`` does, in this order: *issue* (q_t, lam_t from state released through
event t-delay-1), store x_t and the bets in the delay buffer, *release* event t-delay, *decide*
(effective for event t+1). The issue block never reads the buffer; only the release block reads
slot ``t % delay``, which holds the label of event t-delay. So the adapter calls ``step(t)`` in
``request_labels(t)`` with dummy losses (zeros) and, immediately before, overwrites the buffered
increment of event t-delay with the one built from the label the simulator released through
``observe``. Event t's own losses never enter: at issue time ``step`` is given zeros, and the
buffered increment for event t is dummy until its own label is released at t+delay.

Information-flow order: EXACTLY CertPlus's
------------------------------------------
Simulator order at event t is observe (release of event t-delay) -> predict -> request_labels.
A naive port would let the released label t-delay inform q_t and the deployment of event t,
one event EARLIER than CertPlus. This adapter does not: the released item is only stashed in
``observe``. ``predict(t)`` returns the model decided at the end of CertPlus step t-1 (which had
released event t-1-delay), and q_t is computed inside ``step(t)`` before event t-delay is
released. The adapter is therefore numerically identical to CertPlus, and strictly no less
restrictive than it (the policy merely holds one label unused for part of an event). The
discrepancy that would otherwise exist is thus removed, not tolerated.

Other adaptation points
-----------------------
* Disagreement ``dis`` is "the two models' predictions differ" (label-free, from ``Event``).
  CertPlus uses ``l0 != l1``; the two coincide for binary labels and 0/1 loss, which is the
  setting P7s was built for. For multiclass labels they can differ and this adapter uses the
  prediction-level definition (the only one available at issue time).
* The simulator's budget is authoritative. Before each ``step`` the internal remaining-budget
  counter is set to ``remaining_budget``, so the pacer uses exactly the simulator's number; the
  adapter adds no cap of its own (CertPlus already returns q = 0 when it is zero).
* Randomness: one uniform per event, drawn from the supplied ``rng`` whether or not the models
  disagree, matching ``b3_real_data.episode_u`` (one draw per event).
* The increment x_s = (loss_0 - loss_1) / q_s uses the issue-time ``query_probability`` carried
  by ``ReleasedFeedback`` (frozen); the frozen bets travel in ``extra`` and are checked to equal
  the internal ones at release.
* Models: index 0 is the incumbent, index 1 the challenger; other indices are ignored.
* Unlike the vectorised class, the adapter keeps a ``trace=True`` CertPlus (T x 1 arrays) to read
  back q_t and the bets; this only records, it does not alter the arithmetic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import numpy as np

_PD = Path(__file__).resolve().parents[2]
_SOTA = _PD / "sota"
for _p in (_PD, _SOTA):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from b3_plus_policy import CertPlus, PlusParams, b1
from simulator import Event, QueryRequest, ReleasedFeedback

_TRACE_KEYS = ("dep", "ask", "x", "lam", "logw", "q", "gap", "lcb", "ucb", "r")
_ARRAY_FIELDS = (
    "dep", "rem", "seg", "logw", "s1", "s2", "cnt", "pst", "xbuf", "lbuf", "lubuf", "queries",
    "switches", "rollbacks", "t_prom", "loss", "q_sum", "min_factor", "min_grid_factor", "lbw",
    "ubw",
)  # fmt: skip


def _enc(a: np.ndarray) -> dict:
    return {"dtype": str(a.dtype), "shape": list(a.shape), "data": a.ravel().tolist()}


def _dec(d: dict) -> np.ndarray:
    return np.array(d["data"], dtype=d["dtype"]).reshape(d["shape"])


def p7s_plus_params() -> PlusParams:
    return PlusParams(
        variant="P7s",
        acq_shape="settled",
        r_max=1.0,
        r_floor=0.25,
        settled_floor=0.0,
        use_hopeless=True,
    )


class P7sPolicy:
    """B3+ P7s as a scalar simulator policy (model 0 = incumbent, model 1 = challenger)."""

    def __init__(
        self,
        horizon: int,
        budget: int,
        delay: int,
        switch_cost: float,
        label_price: float,
        *,
        rng: np.random.Generator,
        params: b1.Params | None = None,
        name: str = "P7s_settled",
        q_adjust: Callable[[int, float], float] | None = None,
    ):
        if delay < 1:
            raise ValueError("delay must be >= 1")
        self.name = name
        self.horizon, self.budget, self.delay = int(horizon), int(budget), int(delay)
        self.rng = rng
        self.q_adjust = q_adjust
        self.p = params or b1.Params(T=self.horizon, delay=self.delay, cq=label_price)
        if self.p.T != self.horizon or self.p.delay != self.delay or self.p.cq != label_price:
            raise ValueError("params.T / delay / cq must match horizon / delay / label_price")
        self.cp = CertPlus(
            1, self.budget, float(switch_cost), float(label_price), self.p, p7s_plus_params(),
            trace=True,
        )  # fmt: skip
        self._stash: list[ReleasedFeedback] = []
        self._ndis = 0
        self._next_t = 0

    # ------------------------------------------------------------------ protocol
    def predict(self, event: Event) -> int:
        return int(self.cp.dep[0])  # decided at the end of CertPlus step t-1

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        # Held, not applied: CertPlus issues q_t BEFORE releasing event t-delay (see docstring).
        self._stash.extend(feedback)

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        t, cp = event.t, self.cp
        if t != self._next_t or event.horizon != self.horizon:
            raise ValueError("events must arrive in order t = 0, 1, ... with the declared horizon")
        # Stage the released label of event t-delay in the buffer slot step(t) will release.
        for fb in self._stash:
            if fb.t_requested != t - self.delay:
                raise ValueError(f"released event {fb.t_requested} at t={t}, delay {self.delay}")
            slot = fb.t_requested % self.delay
            lam, lu = cp.lbuf[slot, 0], cp.lubuf[slot, 0]
            if fb.extra.get("lam") != lam or fb.extra.get("lam_dn") != lu:
                raise ValueError("frozen bets in feedback differ from the issue-time bets")
            q = fb.query_probability
            cp.xbuf[slot, 0] = (float(fb.model_losses[0]) - float(fb.model_losses[1])) / q
        self._stash = []
        cp.rem[0] = int(remaining_budget)  # the simulator's budget is authoritative
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        u = float(self.rng.random())
        # Dummy (zero) losses: nothing about event t's label or losses reaches CertPlus now.
        adjust = None
        if self.q_adjust is not None:
            adjust = lambda step_t, q: np.array([self.q_adjust(step_t, float(q[0]))])
        cp.step(
            t, np.zeros(1), np.zeros(1), np.array([dis]), np.array([u]),
            np.array([self._ndis]), q_adjust=adjust,
        )
        self._ndis += int(dis)
        self._next_t = t + 1
        q = float(cp.tr["q"][t, 0])
        ask = bool(cp.tr["ask"][t, 0])
        return QueryRequest(
            requested=ask,
            probability=q,
            extra={"lam": float(cp.tr["lam"][t, 0]), "lam_dn": float(cp.lubuf[t % self.delay, 0])},
        )

    def decision_state(self) -> str:
        return f"dep={int(self.cp.dep[0])}"

    # -------------------------------------------------------------- introspection
    @property
    def issued_q(self) -> np.ndarray:
        """q_t issued so far (0 where the budget was exhausted)."""
        return self.cp.tr["q"][: self._next_t, 0].copy()

    # ---------------------------------------------------------------------- state
    def state_dict(self) -> dict:
        cp = self.cp
        return {
            "arrays": {
                k: _enc(getattr(cp, k)) for k in _ARRAY_FIELDS if getattr(cp, k) is not None
            },
            "trace": {k: _enc(v) for k, v in cp.tr.items()},
            "stash": [
                {
                    "event_id": f.event_id,
                    "t_requested": f.t_requested,
                    "t_released": f.t_released,
                    "label": f.label,
                    "model_losses": f.model_losses.tolist(),
                    "query_probability": f.query_probability,
                    "extra": dict(f.extra),
                }
                for f in self._stash
            ],
            "ndis": self._ndis,
            "next_t": self._next_t,
            "rng": self.rng.bit_generator.state,
        }

    def load_state_dict(self, s: dict) -> None:
        cp = self.cp
        for k, v in s["arrays"].items():
            setattr(cp, k, _dec(v))
        cp.tr = {k: _dec(v) for k, v in s["trace"].items()}
        self._stash = [
            ReleasedFeedback(
                event_id=int(f["event_id"]), t_requested=int(f["t_requested"]),
                t_released=int(f["t_released"]), label=int(f["label"]),
                model_losses=np.array(f["model_losses"], dtype=np.int8),
                query_probability=float(f["query_probability"]), extra=dict(f["extra"]),
            )
            for f in s["stash"]
        ]  # fmt: skip
        self._ndis, self._next_t = int(s["ndis"]), int(s["next_t"])
        self.rng.bit_generator.state = s["rng"]
