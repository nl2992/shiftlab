"""Our contribution, reduced to its minimal contrast with the published alternative.

The narrowed claim (`SOTA_NARROWED_PROTOCOL.md`) is about the *stopping trigger* and nothing
else. So this policy is `GatedDeploymentStop` with **one method overridden**: the threshold at
which the confidence sequence is judged conclusive.

    certificate trigger (prior art):  stop when  g_lo > 0            or  g_hi < 0
    economic trigger  (ours):         stop when  g_lo > c_s/(T-t)    or  g_hi < c_s/(T-t)

Identical acquisition, identical confidence sequence, identical delay handling, identical budget
accounting, identical deployment mechanics. Any difference in net cost is attributable to the
threshold alone, which is what makes the comparison a test of the claim rather than of two
implementations.

**Why that threshold.** A switch costs `c_s` once and earns the per-event gain `G` for the
remaining `T - t` events, so switching is worth it exactly when `G * (T - t) > c_s`, i.e.
`G > c_s/(T-t)`. The certificate trigger asks whether `G > 0` -- whether the challenger is
*better* -- which is a different question from whether deploying it is *worth it*.

Two consequences, both predicted before running (protocol section 4):

* **Fewer switches.** Where `0 < G < c_s/(T-t)`, the certificate fires and switches; we do not.
* **Earlier stopping.** Where `g_hi < c_s/(T-t)` but `g_hi > 0`, the decision is economically
  settled although the certificate has not fired; we stop buying labels and it keeps paying.

The threshold rises as `T - t` shrinks, so late in an episode the bar for switching is higher.
That is the same economics as settled-decision acquisition, expressed as a stopping rule so it
can be compared like-for-like against the published certificate rules.
"""

from __future__ import annotations

import numpy as np

from certificate_stops import GatedDeploymentStop
from simulator import Event


class EconomicStop(GatedDeploymentStop):
    """Gated deployment with an economic threshold in place of zero.

    `switch_cost` and `horizon` are the simulator's own; nothing here is tuned per dataset.
    """

    deploy_verdicts = ("deploy",)

    def __init__(self, horizon: int, budget: int, alpha: float, switch_cost: float, *,
                 rng: np.random.Generator, p_min: float = 0.05,
                 name: str = "economic_stop"):  # fmt: skip
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name)
        if switch_cost < 0.0:
            raise ValueError("switch_cost must be >= 0")
        self.switch_cost = float(switch_cost)
        self.horizon = int(horizon)
        self._t = 0

    def _on_event_start(self, event: Event) -> None:
        self._t = int(event.t)
        super()._on_event_start(event)

    @property
    def threshold(self) -> float:
        """`c_s / (T - t)`: the per-event gain a switch must beat to repay itself.

        At the final event the remaining horizon is 1, so the bar is `c_s` itself; with a full
        horizon ahead it is `c_s/T`, close to the certificate trigger's 0. The economic and
        statistical triggers therefore agree early and diverge as the episode runs out.
        """
        remaining = max(self.horizon - self._t, 1)
        return self.switch_cost / remaining

    def _check(self) -> str:
        g_lo, g_hi = self.gain_bounds
        thr = self.threshold
        if g_lo > thr:  # switching repays its cost even on the pessimistic bound
            return "deploy"
        if g_hi < thr:  # even optimistically it cannot repay: the decision is settled
            return "keep"
        return ""

    def decision_state(self) -> str:
        g_lo, g_hi = self.gain_bounds
        return f"g=[{g_lo:.3f},{g_hi:.3f}];thr={self.threshold:.4f};dep={self.deployed}"

    def _extra_state(self) -> dict:
        return {**super()._extra_state(), "t": self._t}

    def _load_extra(self, s: dict) -> None:
        super()._load_extra(s)
        self._t = int(s.get("t", 0))
