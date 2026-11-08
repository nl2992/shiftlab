"""Tests for Gap-Mix+ (docs/methods_recovery/00_PREREG_GAPMIX_PLUS.md)."""

from __future__ import annotations

import dataclasses
import itertools

import numpy as np
import pytest

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver import gapmix_plus as gp


def cell(rho=0.8, d=10, b=0.1, rho_on=0.3, T=400):
    return fa.Family3CellSpec(
        rho=rho, onset=rho_on, duration=1.0, effect="strong", off_type="harmful",
        d=d, budget_frac=b, T=T,
    )  # fmt: skip


def run(c, sd, m):
    cfg, st = c.config(sd), fa.make_stream(c, sd)
    return fa.run_for(c, st, m, cfg), cfg, st


def test_rate_increases_with_gap():
    r = [gp.expected_gain(g, None, 0.55, 0.8) for g in (1, 2, 4, 10, 30)]
    assert all(b >= a - 1e-12 for a, b in itertools.pairwise(r)) and r[-1] > 3 * r[0]


def test_guard_trips_on_future_label():
    c = cell()
    cfg = c.config(1)
    m = gp.GapMixPlusMethod()
    m.start(cfg)
    with pytest.raises(gp.PredictabilityViolation):
        m.step(5, ((5, -1.0),))  # label queried at 5 cannot be released at 5 (d=10)


def test_queries_predictable_under_future_edit():
    """Altering D on rounds whose labels are not yet released cannot change earlier requests."""
    c = cell()
    cfg = c.config(3)
    st = fa.make_stream(c, 3)
    cut = 120
    D2 = st.D.copy()
    D2[cut:] = -D2[cut:]

    def qlog(D):
        m = gp.GapMixPlusMethod()
        m.start(cfg)
        pend, out = {}, []
        for t in range(1, cfg.T + 1):
            due = tuple(pend.pop(t, ()))
            _, q = m.step(t, due)
            if q:
                out.append(t)
                if t + cfg.d <= cfg.T:
                    pend.setdefault(t + cfg.d, []).append((t, float(D[t - 1])))
        return out

    q1, q2 = qlog(st.D), qlog(D2)
    horizon = cut + cfg.d  # first possible influence of rounds >= cut on a decision
    assert [t for t in q1 if t <= horizon] == [t for t in q2 if t <= horizon]


@pytest.mark.parametrize("mode", ["plus", "frozen", "pace"])
def test_budget_never_exceeded(mode):
    for d, b in ((1, 0.05), (10, 0.25)):
        c = cell(d=d, b=b)
        for sd in range(3):
            m = gp.GapMixPlusMethod(
                mode=mode, params=gp.GMParams(frac=0.3) if mode == "pace" else None
            )
            r, cfg, _ = run(c, sd, m)
            assert r.queries <= cfg.B and m.used == r.queries <= cfg.B


def test_ablation_4a_differs_only_in_evidence_terms():
    p = gp.GMParams(kappa=1.0, phi=1.0, omega=0.5)
    a = gp.GapMixPlusMethod(mode="plus", params=p)
    b = gp.GapMixPlusMethod(mode="frozen", params=p)
    assert a.gp == b.gp and a.evidence == b.evidence and a.rho_bar == b.rho_bar
    c = cell()
    cfg = c.config(4)
    st = fa.make_stream(c, 4)
    a.start(cfg)
    b.start(cfg)
    pend = {}
    seen = False
    for t in range(1, 200):
        due = tuple(pend.pop(t, ()))
        _, qa = a.step(t, due)
        _, qb = b.step(t, due)
        if qa and t + cfg.d <= cfg.T:
            pend.setdefault(t + cfg.d, []).append((t, float(st.D[t - 1])))
        if b.mode == "frozen":
            assert b.evidence_terms() == (0.0, None)
        ea, wa = a.evidence_terms()
        seen |= ea > 0 or wa is not None
        if qa != qb:  # decisions may differ only because the evidence terms differ
            break
    assert seen
    assert dataclasses.asdict(a.gp) == dataclasses.asdict(b.gp)


def test_null_monte_carlo_sanity():
    """Boundary-null streams (rho 0.5, T=400): false promotion stays low and the budget holds."""
    c = cell(rho=0.5, d=1, b=0.1).null_twin()
    fp = []
    for sd in range(40):
        m = gp.GapMixPlusMethod()
        r, cfg, _ = run(c, 7000 + sd, m)
        assert r.queries <= cfg.B
        fp.append(int((r.fp_regime or 0) > 0))
    assert np.mean(fp) <= 0.15
