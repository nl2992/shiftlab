"""river Page-Hinkley (T1 detector) wrapped as a common-contract deployment adapter (T3).

Source
------
``river.drift.PageHinkley`` at the version pinned by ``pyproject.toml`` (optional extra ``drift``,
``river==0.26.1``). The detector is CALLED, not re-implemented, so the detector is **T1
author-native** (river is the reference implementation the check read:
``docs/sota_fidelity/checks/page_hinkley.md``; river defaults min_instances=30, delta=0.005,
threshold=50, alpha=0.9999). The Page (1954) / Hinkley (1971) papers were not read (unverifiable).
river is imported lazily so the default environment, without the extra, still imports this module;
constructing the adapter without river raises ``ImportError`` with the install hint
(``uv run --extra drift ...``).

T3 adapter (NOT a Page-Hinkley guarantee; the name is "river Page-Hinkley, common-contract adapter (T3)")
---------------------------------------------------------------------------------------------------
* Label clock: delivery order, one detector update per delivered label.
* Stream value ``z = loss(deployed) - loss(other)`` in {-1, 0, 1}; an upward shift means the
  non-deployed model became relatively better. The ``up``-mode detector acts: on its alarm the
  adapter switches deployment (promotion if incumbent deployed, rollback otherwise) and rebuilds a
  fresh detector. A second ``down``-mode detector (deployed model became relatively better) runs
  for diagnostics only and never acts; river's single ``mode="both"`` object does not expose the
  direction of an alarm through the public API, so two single-mode objects are used. The
  two-sided symmetric alternative is therefore the pair (up, down), not river's "both".
* Page-Hinkley detects a CHANGE of the stream mean relative to its own running mean since the last
  reset, not the sign of the mean. A challenger that is better from the first label produces a
  constant positive ``z`` and no alarm. This is the classical behaviour and it is kept: a faithful
  PH baseline is a change detector, not a harm or benefit test. ``prime_null=n0`` (default 0)
  optionally feeds ``n0`` zero-valued pseudo-observations (the null mean) after each reset so that
  the running mean starts at the null; this is a declared ShiftLab extension, off by default.
* Acquisition: shared ``PacedDisagreementAcquisition``, no IPW; labels requested at or before a
  switch event are dropped after the restart (same convention as the other adapters).
* No alpha, no error-rate calibration: the threshold is river's constant. ``alpha`` of the
  contract is accepted and ignored.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SOTA = Path(__file__).resolve().parents[1]
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from controls import PacedDisagreementAcquisition
from simulator import Event, QueryRequest, ReleasedFeedback


def river_available() -> bool:
    try:
        import river.drift  # noqa: F401
    except ImportError:
        return False
    return True


class RiverPageHinkleyDeploymentAdapter:
    def __init__(self, horizon: int, budget: int, *, rng: np.random.Generator,
                 min_instances: int = 30, delta: float = 0.005, threshold: float = 50.0,
                 forgetting: float = 0.9999, prime_null: int = 0, p_min: float = 0.05,
                 name: str = "river_page_hinkley_t3"):
        try:
            from river.drift import PageHinkley
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise ImportError("river is not installed; use `uv run --extra drift`") from exc
        self._PH = PageHinkley
        self.name = name
        self.kw = {"min_instances": min_instances, "delta": delta, "threshold": threshold,
                   "alpha": forgetting}
        self.prime_null = int(prime_null)
        self.rng = rng
        self.acq = PacedDisagreementAcquisition(horizon, budget, p_min=p_min)
        self.deployed = 0
        self.t = -1
        self.t_switch = -1
        self.n_switches = self.n_down_alarms = self.n_dropped_inflight = 0
        self._new_detectors()

    def _new_detectors(self) -> None:
        self.up = self._PH(mode="up", **self.kw)
        self.down = self._PH(mode="down", **self.kw)
        for _ in range(self.prime_null):
            self.up.update(0.0)
            self.down.update(0.0)

    def predict(self, event: Event) -> int:
        self.t = event.t
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
            if fb.t_requested <= self.t_switch:
                self.n_dropped_inflight += 1
                continue
            z = float(fb.model_losses[self.deployed]) - float(fb.model_losses[1 - self.deployed])
            self.down.update(z)
            if self.down.drift_detected:
                self.n_down_alarms += 1
            self.up.update(z)
            if self.up.drift_detected:
                self.deployed = 1 - self.deployed
                self.n_switches += 1
                self.t_switch = self.t
                self._new_detectors()

    def decision_state(self) -> str:
        return f"dep={self.deployed};sw={self.n_switches}"

    def state_dict(self) -> dict:
        return {}

    def load_state_dict(self, s: dict) -> None:
        pass
