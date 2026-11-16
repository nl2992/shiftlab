"""Fast synthetic-only tests for the real-stream check plumbing (no real losses are read)."""

import numpy as np
import pytest

from shiftlab.paper3.riskbudget.real_streams import (
    BENEFICIAL,
    CONDITIONS,
    HARMFUL,
    HS,
    STREAMS,
    T,
    build_real_arms,
    corruption_rng,
    make_real_spec,
    make_real_tape,
    run_arm_row,
)


def synth(seed=0, harmful=False):
    r = np.random.default_rng(seed)
    l0 = (r.random(T) < 0.3).astype(np.int8)
    p_flip = 0.35 if harmful else 0.15
    l1 = np.where(r.random(T) < 0.25, (r.random(T) < (0.5 + (0.1 if harmful else -0.2))), l0)
    l1 = np.where(r.random(T) < p_flip, 1 - l0, l1).astype(np.int8)
    return l0, l1


def test_registry():
    assert len(STREAMS) == 14 and set(HARMFUL) | set(BENEFICIAL) == set(STREAMS)
    assert len(BENEFICIAL) == 12
    d = {k: v[1] for k, v in STREAMS.items()}
    assert d["spam"] == 50 and d["weather"] == 1 and d["elec2"] == 48 and d["airlines"] == 100
    assert d["metro"] == d["bike_hour"] == d["beijing_pm25"] == 24
    assert d["appliances"] == d["household_power"] == 144


def test_tapes():
    l0, l1 = synth()
    unfav = l0 < l1
    assert unfav.sum() > 50
    c = make_real_tape(l0, l1, 100, "clean", corruption_rng("x", 0, "clean"))
    assert (c.delay == 100).all() and (c.disagree == (l0 != l1)).all()
    assert c.ell.shape == (T, 2) and c.x.shape == (T, 2) and c.ell.dtype == float
    d = make_real_tape(l0, l1, 100, "dropout_adverse", corruption_rng("x", 0, "dropout_adverse"))
    never = d.delay == T + 1
    assert never.any() and not never[~unfav].any()
    assert (d.delay[~never] == 100).all()
    assert 0.5 < never.sum() / unfav.sum() < 0.7
    d2 = make_real_tape(l0, l1, 100, "dropout_adverse", corruption_rng("x", 0, "dropout_adverse"))
    assert (d.delay == d2.delay).all()
    d3 = make_real_tape(l0, l1, 100, "dropout_adverse", corruption_rng("x", 1, "dropout_adverse"))
    assert (d.delay != d3.delay).any()
    a = make_real_tape(l0, l1, 100, "delay_adverse", corruption_rng("x", 0, "delay_adverse"))
    assert (a.delay[unfav] == 500).all() and (a.delay[~unfav] == 100).all()
    assert (a.ell == c.ell).all() and (d.ell == c.ell).all()


def test_spec():
    s = make_real_spec(48, "clean")
    assert (s.T, s.B, s.costs.c_q, s.costs.k) == (2000, 200, 0.05, 5.0)
    assert s.delay_known == 48 and s.delay_kind == "fixed"
    for c in CONDITIONS[1:]:
        s = make_real_spec(48, c)
        assert s.delay_known is None and s.delay_kind == "informative"


def test_arms():
    arms = build_real_arms()
    names = [a["name"] for a in arms]
    assert len(set(names)) == len(names)
    base = ["never", "wald_cut", "cusum", "gate_wald", "cusum_rb_h4", "cusum_rb_h8"]
    assert names[:6] == base
    for h in HS:
        for tag in ("stoploss", "f3_pi1", "f3v2d"):
            a = arms[names.index(f"{tag}_h{h}")]
            assert a["R"] == 10 + h
    assert [n for n in names if "blind8" in n] == ["f3v2_blind8_h14"]
    assert arms[names.index("f3v2_blind8_h14")]["R"] == 24
    assert len(arms) == 6 + 15 + 1
    # frozen parameters unchanged
    w = arms[names.index("f3_pi1_h14")]["inner"]["params"]
    assert w["lam"] == pytest.approx(0.9320934923645325) and w["stop"] == 0.3


@pytest.mark.parametrize("cond", CONDITIONS)
def test_end_to_end(cond):
    arms = build_real_arms()
    for harmful in (False, True):
        l0, l1 = synth(1, harmful)
        tape = make_real_tape(l0, l1, 24, cond, corruption_rng("syn", 0, cond))
        spec = make_real_spec(24, cond)
        for arm in arms:
            row = run_arm_row(arm, tape, spec, 24, 60001)
            if arm["name"] == "never":
                assert row["sup_harm"] == 0 and row["J"] == l0.sum()
            if arm["name"].startswith("f3_pi1_h") or "blind8" in arm["name"]:
                assert row["sup_harm"] <= arm["R"] + 1e-9, (arm["name"], row)
