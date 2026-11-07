"""Frozen P7s / Model Picker acquisition overlay for the 2026-11-07 pilot."""

from __future__ import annotations

import numpy as np
from b3_plus_policy_adapter import P7sPolicy
from model_picker import eta_t, posterior, query_probability
from simulator import Event, QueryRequest, ReleasedFeedback


class P7sModelPickerOverlay(P7sPolicy):
    """P7s certificate/deployment with predictable Model Picker acquisition overlay."""

    def __init__(self, *args, settled_throttle: bool = True, **kwargs):
        self.mp_loss = np.zeros(2, dtype=float)
        self.mp_pending: list[ReleasedFeedback] = []
        self.settled_throttle = bool(settled_throttle)
        self._parts = {"p7s": 0.0, "mp": 0.0, "active": False}
        self.q_parts_trace: list[dict] = []
        super().__init__(*args, q_adjust=self._combine, **kwargs)

    def _combine(self, t: int, q_p7s: float) -> float:
        cp = self.cp
        active = bool((cp.dep[0] == 0) or (not self.settled_throttle) or (cp.pst[0] >= 0))
        preds = self._current_event.model_predictions
        q_mp = (
            query_probability(
                posterior(self.mp_loss, eta_t(2, t + 1)), preds, 1.0, 2, eta_t(2, t + 1)
            )
            if active
            else 0.0
        )
        q = 1.0 - (1.0 - q_p7s) * (1.0 - q_mp) if active else q_p7s
        if int(self.cp.rem[0]) <= 0:
            q = 0.0
        self._parts = {"p7s": float(q_p7s), "mp": float(q_mp), "active": active}
        return float(q)

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        self._current_event = event
        req = super().request_labels(event, remaining_budget)
        req.extra.update(
            {
                "q_p7s": self._parts["p7s"],
                "q_mp": self._parts["mp"],
                "overlay_active": self._parts["active"],
            }
        )
        self.q_parts_trace.append(
            {"t": event.t, **self._parts, "combined": float(self.cp.tr["q"][event.t, 0])}
        )
        # The feedback released at this event is applied only after the current issue decision,
        # matching CertPlus's issue-then-release filtration.
        for fb in self.mp_pending:
            if fb.query_probability <= 0:
                raise ValueError("overlay feedback has non-positive combined issue propensity")
            self.mp_loss += np.asarray(fb.model_losses, dtype=float) / fb.query_probability
        self.mp_pending.clear()
        return req

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        super().observe(feedback)
        self.mp_pending.extend(feedback)

    def state_dict(self) -> dict:
        state = super().state_dict()
        state["overlay"] = {
            "mp_loss": self.mp_loss.tolist(),
            "settled_throttle": self.settled_throttle,
            "q_parts_trace": list(self.q_parts_trace),
            "mp_pending": [
                {
                    "t_requested": f.t_requested,
                    "t_released": f.t_released,
                    "model_losses": f.model_losses.tolist(),
                    "query_probability": f.query_probability,
                }
                for f in self.mp_pending
            ],
        }
        return state

    def load_state_dict(self, state: dict) -> None:
        super().load_state_dict(state)
        overlay = state["overlay"]
        self.mp_loss = np.asarray(overlay["mp_loss"], dtype=float)
        self.settled_throttle = bool(overlay["settled_throttle"])
        self.q_parts_trace = list(overlay["q_parts_trace"])
        self.mp_pending = [
            ReleasedFeedback(
                event_id=f["t_requested"],
                t_requested=int(f["t_requested"]),
                t_released=int(f["t_released"]),
                label=0,
                model_losses=np.asarray(f["model_losses"], dtype=np.int8),
                query_probability=float(f["query_probability"]),
            )
            for f in overlay["mp_pending"]
        ]
