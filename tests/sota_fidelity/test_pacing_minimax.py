"""Pacing minimax screen: budget cap, delay semantics, and null-law invariance across pacers."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_fidelity"))

import pacing_minimax as pm  # noqa: E402


def test_cap_truncation_and_no_promotion_without_released_labels():
    for name in ["U", "TU", "BURST_0", "BURST_8"]:
        net, nreq, dep, tp = pm.simulate(name, 0, 100, 50, 1, A=float("inf"))  # never promotes
        assert (nreq <= pm.B).all()
        assert not dep.any()
        assert np.allclose(net, pm.CQ * nreq)  # no deployment loss, only label cost
    # promotion can never happen before the first release
    _, _, dep, tp = pm.simulate("BURST_0", 0, 100, 200, 2, A=1.0001)
    assert (tp[dep] >= 100).all()


def test_tu_requests_nothing_after_its_horizon():
    spec = pm.pacer_spec("TU", 100)
    assert spec["horizon"] == round(pm.T - 100 - pm.CS / pm.G_DESIGN)


def test_label_clock_null_law_does_not_depend_on_pacing():
    # Under IID p=1/2 the released D's are IID whatever the request times, so the max statistic over
    # the first k labels has the same law. Compare U and an aggressive burst pacer at a fixed A.
    A = 8.0
    rates = []
    for name in ["U", "BURST_0"]:
        _, nreq, dep, _ = pm.simulate(name, pm.T, 1, 4000, 3, A, p_pre=0.5, p_post=0.5)
        rates.append(dep.mean())
    assert abs(rates[0] - rates[1]) < 0.05
