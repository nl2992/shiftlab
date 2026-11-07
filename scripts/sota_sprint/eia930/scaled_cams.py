"""Single-threaded CAMS eta-scaling development ablations."""

from __future__ import annotations

from typing import Any

import cams as cams_module
from cams import CAMSDeploymentAdapter, _CAMSCore, stack_advice


class EtaScaledCore(_CAMSCore):
    def __init__(self, *args: Any, eta_scale: float, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.eta_scale = float(eta_scale)

    def _prepare(self, event):
        # The simulator is sequential. Temporarily scale only the author-core schedule call while
        # delegating the rest of CAMS's exact update/query implementation to the existing port.
        original = cams_module.learning_rate
        cams_module.learning_rate = lambda n_policies, t: self.eta_scale * original(n_policies, t)
        try:
            return super()._prepare(event)
        finally:
            cams_module.learning_rate = original


class EtaScaledCAMSAdapter(CAMSDeploymentAdapter):
    def __init__(self, *, eta_scale: float, rng: Any, name: str):
        advice = stack_advice(2, [])
        super().__init__(
            n_models=2,
            n_classes=2,
            advice_fn=advice,
            rng=rng,
            variant="CAMS",
            name=name,
        )
        self.core = EtaScaledCore(
            n_models=2,
            n_classes=2,
            advice_fn=advice,
            variant="CAMS",
            rng=rng,
            eta_scale=eta_scale,
        )


def _factory(scale: float, name: str):
    def create(T, B, cs, cq, alpha, delay, r):
        del T, B, cs, cq, alpha, delay
        return EtaScaledCAMSAdapter(eta_scale=scale, rng=r(name), name=name)

    return create


EXTRA = {
    "cams_eta_1p5": _factory(1.5, "cams_eta_1p5"),
    "cams_eta_2": _factory(2.0, "cams_eta_2"),
    "cams_eta_3": _factory(3.0, "cams_eta_3"),
}
