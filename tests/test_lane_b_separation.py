from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from shiftlab.dive.eprocess import PredictableBoundMeanEProcess

_PATH = Path(__file__).resolve().parents[1] / "scripts" / "lane_b" / "separation_check.py"
_SPEC = importlib.util.spec_from_file_location("lane_b_separation_check", _PATH)
sc = importlib.util.module_from_spec(_SPEC)
import sys

sys.modules[_SPEC.name] = sc
_SPEC.loader.exec_module(sc)

ALL_RULES = [
    sc.Config("fixed", q=0.5),
    sc.Config("burst", b=10, q_sparse=0.5),
    sc.Config("paced"),
    sc.Config("r1"),
    sc.Config("r2", h=10.0),
]


def _world(n: int, seed0: int = 7_000, rho: float = 0.05):
    d, uz, ug = sc.draw_world(seed0 + np.arange(n), rho)
    mu = np.broadcast_to(sc.mean_path("N"), (n, sc.T))
    return d, uz, ug, mu


@pytest.mark.parametrize("delay", [0, 20])
@pytest.mark.parametrize("cfg", ALL_RULES, ids=lambda c: c.label())
def test_q_predictable_wrt_label_values(cfg, delay):
    """Changing Z at events >= t0 must not change q at times <= t0 + delay."""
    n = 24
    d, uz, ug, mu = _world(n)
    t0 = sc.S0 + 40
    mu2 = np.array(mu)
    mu2[:, t0:] = 0.9 * np.where(np.arange(sc.T - t0) % 2 == 0, 1.0, -1.0)  # different Z law
    uz2 = np.array(uz)
    uz2[:, t0:] = 1.0 - uz2[:, t0:]
    kw = {"budget": 40, "delay": delay, "variant": "B_disagree_only", "record": True}
    a = sc.simulate(cfg, d, uz, ug, mu, **kw)
    b = sc.simulate(cfg, d, uz2, ug, mu2, **kw)
    cut = t0 + delay + 1  # event s label arrives at s + delay; usable only at t > s + delay
    assert np.array_equal(a["q"][:, :cut], b["q"][:, :cut])
    assert np.array_equal(a["req"][:, :cut], b["req"][:, :cut])


@pytest.mark.parametrize("delay", [0, 20])
@pytest.mark.parametrize("cfg", ALL_RULES, ids=lambda c: c.label())
def test_hard_cap_including_pending_labels(cfg, delay):
    n = 24
    d, uz, ug, mu = _world(n, seed0=8_000, rho=0.2)
    for budget in (5, 40):
        out = sc.simulate(
            cfg,
            d,
            uz,
            ug,
            mu,
            budget=budget,
            delay=delay,
            variant="A_agree_in_eprocess",
            record=True,
        )
        assert out["req"].sum(axis=1).max() <= budget
        assert out["cum"].max() <= budget
        # charged at request: with delay 20 the cap binds before earlier labels have arrived
        assert np.all(out["q"][out["cum"] >= budget][:, -1] == 0)


def test_delay_does_not_let_responsive_rule_overspend_burst():
    d, uz, ug, mu = _world(30)
    out = sc.simulate(
        sc.Config("r1"),
        d,
        uz,
        ug,
        mu,
        budget=1000,
        delay=20,
        variant="B_disagree_only",
        record=True,
    )
    # with delay the SPRT stop is seen late, so r1 spends more in the burst than at d = 0
    out0 = sc.simulate(
        sc.Config("r1"), d, uz, ug, mu, budget=1000, delay=0, variant="B_disagree_only", record=True
    )
    burst = slice(sc.S0, sc.S0 + sc.L)
    assert out["req"][:, burst].sum() >= out0["req"][:, burst].sum()


def test_row_eprocess_matches_class():
    """The vectorised wealth update equals PredictableBoundMeanEProcess on the same increments."""
    rng = np.random.default_rng(0)
    proc = PredictableBoundMeanEProcess(alpha=0.05)
    logw = np.zeros(len(sc.STAKES))
    for _ in range(200):
        q = rng.choice([0.25, 0.5, 1.0])
        z = rng.choice([-1.0, 1.0])
        g = rng.random() < q
        v = (z / q if g else 0.0) - sc.EPS
        bound = sc.C / q + sc.EPS
        proc.update(v, bound=bound)
        logw += np.log1p(sc.STAKES * (v / bound))
        mx = logw.max()
        mine = mx + np.log(np.exp(logw - mx).sum()) - np.log(len(sc.STAKES))
        assert mine == pytest.approx(proc.log_e_value, abs=1e-9)


@pytest.mark.parametrize("variant", ["A_agree_in_eprocess", "B_disagree_only"])
def test_null_control_false_alarm_rate(variant):
    n = 400
    d, uz, ug = sc.draw_world(9_000 + np.arange(n), 0.05)
    mu = np.broadcast_to(sc.mean_path("null"), (n, sc.T))
    for cfg in (sc.Config("fixed", q=1.0), sc.Config("r1"), sc.Config("r2", h=3.0)):
        out = sc.simulate(cfg, d, uz, ug, mu, budget=120, delay=0, variant=variant)
        for ai, alpha in enumerate(sc.ALPHAS):
            k = int(np.sum(out["alarm"][:, ai] < sc.T))
            # exact 99.9% one-sided upper bound must still sit below 2 * alpha + slack
            assert sc.clopper_pearson_upper(k, n, 0.999) < max(4 * alpha, 0.12)


def test_clopper_pearson_upper_basic():
    assert sc.clopper_pearson_upper(0, 1000) == pytest.approx(1 - 0.05 ** (1 / 1000), rel=1e-6)
    assert sc.clopper_pearson_upper(1000, 1000) == 1.0
