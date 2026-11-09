"""Native-endpoint variants of the gated-deployment comparators (2026-11-09).

Identical to ``gated_deployment`` / ``gated_adaptive_range`` (+front) except the CS endpoint is
computed as in the author code (n17s/mope@a4b8584b ``wealth_lb_2d``): exact log wealth on a
1000-point grid instead of the paper's quadratic lower bound. See docs/p2/_mope_native.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for sub in ("scripts/failure_atlas_v2_flq", "scripts/promising_directions/sota/competitors"):
    q = str(HERE.parents[1] / sub)
    if q not in sys.path:
        sys.path.insert(0, q)

from certificate_stops import GatedDeploymentStop, MopeCS
from strong_hosts import GatedAdaptiveRange


class GatedDeploymentNative(GatedDeploymentStop):
    def __init__(self, horizon, budget, alpha, *, rng, p_min=0.05, name="gated_deployment_native"):
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, name=name,
                         endpoint="exact_grid")  # fmt: skip


class GatedAdaptiveRangeNative(GatedAdaptiveRange):
    def __init__(self, horizon, budget, alpha, *, rng, p_min=0.05, front=False,
                 name="gated_adaptive_range_native"):  # fmt: skip
        super().__init__(horizon, budget, alpha, rng=rng, p_min=p_min, front=front, name=name)
        self.cs = MopeCS(alpha, 1.0 / self.p_min, "exact_grid")


EXTRA = {
    "gated_deployment_native": lambda T, B, cs, cq, a, d, r: GatedDeploymentNative(
        T, B, a, rng=r("gated_deployment")
    ),
    "gated_adaptive_range_native": lambda T, B, cs, cq, a, d, r: GatedAdaptiveRangeNative(
        T, B, a, rng=r("gated_deployment")
    ),
    "gated_adaptive_range_native+front": lambda T, B, cs, cq, a, d, r: GatedAdaptiveRangeNative(
        T, B, a, rng=r("gated_deployment"), front=True, name="gated_adaptive_range_native+front"
    ),
}
NULL_TESTED = {k: "V1" for k in EXTRA}
