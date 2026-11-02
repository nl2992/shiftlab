from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/promising_directions/b3_plus_policy.py"
spec = importlib.util.spec_from_file_location("b3_plus_policy", SCRIPT)
b3p = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b3p
spec.loader.exec_module(b3p)
b1 = b3p.b1

CS, CQ = 5.0, 0.05
VARIANTS = b3p.VARIANTS
SMALL = b1.Params(T=400, tau=120)


def stream(world, p, n=60, seed=3):
    return b1.make_stream(world, p, n, seed, 0)


def regime_stream(rid, p, n, seed):
    rng = np.random.default_rng(seed)
    reg = np.full((p.T, n), rid, dtype=np.int8)
    l0, l1 = b1.draw_losses(reg, rng)
    return l0, l1, rng.random((p.T, n))


def run(l0, l1, u, budget, p, variants=VARIANTS, cs=CS, **kw):
    pls = [b3p.PlusParams(variant=v) for v in variants]
    return b3p.run_plus_policies(l0, l1, u, budget, cs, CQ, p, pls, return_objs=True, **kw)


def p3b(l0, l1, u, budget, p):
    return b1.run_policies(l0, l1, u, budget, (), p, trace=True, b2=True)


def test_pinned_b1_is_recorded():
    assert b3p.B1_RECORD["commit"] == "041bc26" and len(b3p.B1_RECORD["sha256"]) == 64
    assert hasattr(b1, "bet_from_stats") and hasattr(b1, "Params")


def test_output_keys_match_p3b():
    s = stream("W1", SMALL, n=8)
    out, _ = run(s["l0"], s["l1"], s["u"], 40, SMALL, ("P7",))
    ref = p3b(s["l0"], s["l1"], s["u"], 40, SMALL)["P3b"]
    assert set(ref) <= set(out["P7"])
    assert all(np.asarray(v).shape == (8,) for v in out["P7"].values())


def test_p4ref_reproduces_repository_p4():
    s = stream("W3", SMALL, n=20)
    out, _ = run(s["l0"], s["l1"], s["u"], 40, SMALL, ("P4ref",))
    ref = b1.run_policies(s["l0"], s["l1"], s["u"], 40, (CS,), SMALL)["P4"][CS]
    for key in ("loss", "queries", "switches", "rollbacks"):
        assert np.array_equal(out["P4ref"][key], ref[key])
    assert np.array_equal(out["P4ref"]["t_prom"], ref["t_prom"], equal_nan=True)


def test_pathwise_budget_invariance_all_variants():
    for world in ("W1", "W3", "W4"):
        s = stream(world, SMALL)
        for budget in (7, 25, 60):
            _, objs = run(s["l0"], s["l1"], s["u"], budget, SMALL)
            for name, o in objs.items():
                assert o.queries.max() <= budget, name
                assert o.rem.min() >= 0 and np.array_equal(o.queries + o.rem, np.full(60, budget))
    # not vacuous: the budget binds for a pacing variant
    _, objs = run(s["l0"], s["l1"], s["u"], 7, SMALL, ("P7a",))
    assert objs["P7a"].queries.max() == 7


def test_propensity_floor_on_every_queried_event():
    s = stream("W3", SMALL)
    _, objs = run(s["l0"], s["l1"], s["u"], 40, SMALL, trace=True)
    for name, o in objs.items():
        ask, q = o.tr["ask"].astype(bool), o.tr["q"]
        assert ask.any()
        assert (q[ask] >= SMALL.pmin - 1e-12).all() and (q <= 1).all(), name
        assert np.allclose(o.q_sum, np.where(ask, q, 0).sum(0)), name


def test_wealth_factors_nonnegative_under_adversarial_streams():
    p = b1.Params(T=300, tau=0)
    n, half = 20, 120
    rng = np.random.default_rng(0)
    u = rng.random((p.T, n))
    # challenger perfect, then maximally wrong: bets grow, then the worst sign arrives
    l0 = np.ones((p.T, n), dtype=np.int8)
    l1 = np.zeros((p.T, n), dtype=np.int8)
    l0[half:], l1[half:] = 0, 1
    for budget in (10, 60):
        _, objs = run(l0, l1, u, budget, p, trace=True)
        for name, o in objs.items():
            assert o.min_factor.min() > 0 and o.min_grid_factor.min() > 0, name
            assert o.tr["lam"].min() >= 0, name
            if name != "P4ref":  # cap tracks the propensity issued for the same event
                assert (o.tr["lam"] <= o.tr["q"] / 2 + 1e-12).all(), name
                assert o.min_factor.min() >= 0.5 - 1e-9, name
        # the cap actually binds somewhere (non-vacuous)
        o = objs["P7"]
        assert np.isclose(o.tr["lam"], o.tr["q"] / 2).any()


@pytest.mark.parametrize("variant", VARIANTS)
def test_issue_time_information_respects_delay(variant):
    p = SMALL
    s = stream("W1", p, n=20)
    s0, d = 200, p.delay
    l0b, l1b = s["l0"].copy(), s["l1"].copy()
    l0b[s0:], l1b[s0:] = s["l1"][s0:], s["l0"][s0:]  # swap losses, agreement pattern unchanged
    pl = [variant]
    _, a = run(s["l0"], s["l1"], s["u"], 60, p, pl, trace=True)
    _, c = run(l0b, l1b, s["u"], 60, p, pl, trace=True)
    ta, tc = a[variant].tr, c[variant].tr
    cut = s0 + d + 1  # q_t, lam_t at t <= s0 + d depend on labels of events <= s0 - 1 only
    for key in ("q", "lam", "ask", "dep", "gap", "lcb", "ucb", "r"):
        assert np.array_equal(ta[key][:cut], tc[key][:cut]), key
    assert not np.array_equal(ta["logw"][s0 + d :], tc["logw"][s0 + d :])
    assert not np.array_equal(ta["lam"][cut:], tc["lam"][cut:])


def test_equality_null_false_promotion_rate_is_small():
    # Empirical calibration check on an exact-null stream (E[D] = 0), NOT a proof of validity.
    p = b1.Params(T=500)
    l0, l1, u = regime_stream(4, p, 400, seed=11)
    out, _ = run(l0, l1, u, 100, p)
    for name, o in out.items():
        rate = float(np.mean(~np.isnan(o["t_prom"])))
        assert rate <= 0.15, (name, rate)


def test_large_persistent_advantage_promotes_and_p7_not_later_than_p4ref():
    p = b1.Params(T=2000, tau=0)
    s = stream("W1", p, n=40)
    out, _ = run(s["l0"], s["l1"], s["u"], 200, p, ("P7", "P4ref"))
    for name in ("P7", "P4ref"):
        assert (~np.isnan(out[name]["t_prom"])).mean() >= 0.95, name
    assert np.nanmean(out["P7"]["t_prom"]) <= np.nanmean(out["P4ref"]["t_prom"])


def test_horizon_sensitivity_p7_withholds_promotion_when_horizon_cannot_repay_cs():
    # Same evidence stream (challenger better by ~0.18/event), switch cost 100.
    # LCB <= 0.18, so a 300-event horizon yields at most ~54 < 100: switching cannot pay back.
    cs = 100.0
    p_long = b1.Params(T=3000, tau=0)
    s = b1.make_stream("W1", p_long, 40, 7, 0)
    short = slice(0, 300)
    p_short = b1.Params(T=300, tau=0)
    args = (s["l0"][short], s["l1"][short], s["u"][short], 300)
    base = b1.run_policies(*args[:3], 300, (), p_short, b2=True)["P3b"]
    p7, _ = run(*args[:3], 300, p_short, ("P7",), cs=cs)
    assert (~np.isnan(base["t_prom"])).mean() >= 0.9  # P3b promotes: it is horizon-blind
    assert np.isnan(p7["P7"]["t_prom"]).all()  # P7 does not: the horizon cannot repay cs
    # the same evidence with a long remaining horizon does promote, so the gate is the horizon
    long_out, _ = run(s["l0"], s["l1"], s["u"], 600, p_long, ("P7",), cs=cs)
    assert (~np.isnan(long_out["P7"]["t_prom"])).mean() >= 0.9


def test_hopeless_regime_saves_labels_relative_to_p3b():
    p = b1.Params(T=2000)
    l0, l1, u = regime_stream(3, p, 30, seed=5)  # challenger clearly worse: E[D] = -0.2
    ref = p3b(l0, l1, u, 200, p)["P3b"]
    out, _ = run(l0, l1, u, 200, p, ("P7",))
    assert out["P7"]["queries"].mean() < ref["queries"].mean()
    assert out["P7"]["queries"].max() <= 200
    assert np.isnan(out["P7"]["t_prom"]).all()


def test_ucb_bounds_true_mean_on_null_and_is_trivial_without_evidence():
    p = b1.Params(T=500)
    l0, l1, u = regime_stream(3, p, 20, seed=2)
    _, objs = run(l0, l1, u, 100, p, ("P7",), trace=True)
    ucb = objs["P7"].tr["ucb"]
    assert ucb[0].max() == b3p.UCB_TRIVIAL
    assert ucb[-1].min() <= 0.0  # E[D] = -0.2 < 0 is certified in some seeds
    assert (ucb[ucb < b3p.UCB_TRIVIAL] >= 0).all()
