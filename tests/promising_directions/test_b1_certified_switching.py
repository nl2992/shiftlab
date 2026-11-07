from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts/promising_directions/b1_certified_switching.py"
)
spec = importlib.util.spec_from_file_location("b1_certified_switching", SCRIPT)
b1 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b1
spec.loader.exec_module(b1)

SMALL = b1.Params(T=400, tau=120)


def stream(world, p, n=300, seed=3):
    return b1.make_stream(world, p, n, seed, 0)


def swap_after(s, s0):
    """Swap which model is wrong at disagreements for events >= s0 (agreement pattern kept)."""
    l0, l1 = s["l0"].copy(), s["l1"].copy()
    l0[s0:], l1[s0:] = s["l1"][s0:], s["l0"][s0:]
    return l0, l1


def test_joint_law_matches_marginals_and_disagreement():
    for e0, e1 in b1.REGIMES.values():
        both, p10, p01, p00 = b1.joint_probs(e0, e1)
        assert math.isclose(both + p10, e0) and math.isclose(both + p01, e1)
        assert math.isclose(p10 + p01, b1.DELTA) and math.isclose(both + p10 + p01 + p00, 1)
    p = b1.Params()
    s = b1.make_stream("W1", p, 4000, 5, 0)
    pre, post = slice(0, p.tau), slice(p.tau, p.T)
    assert abs(s["l0"][pre].mean() - 0.10) < 0.01 and abs(s["l1"][pre].mean() - 0.20) < 0.01
    assert abs(s["l0"][post].mean() - 0.30) < 0.01 and abs(s["l1"][post].mean() - 0.12) < 0.01
    assert abs((s["l0"] != s["l1"]).mean() - 0.25) < 0.005


def test_hard_budget_never_exceeded():
    p = replace(SMALL, pmin=0.05)
    for world in ("W1", "W3", "W4"):
        s = stream(world, p)
        for budget in (7, 25, 60):
            res = b1.run_policies(s["l0"], s["l1"], s["u"], budget, (5,), p)
            for out in (res["P2"], res["P3"], res["P4"][5], res["P4w"][5]):
                assert out["queries"].max() <= budget
            # the budget is actually binding for the certified policy, so the check is not vacuous
            assert res["P3"]["queries"].max() == budget


def test_label_for_event_s_used_only_at_s_plus_d():
    p = SMALL
    s = stream("W1", p)
    s0 = 200
    l0b, l1b = swap_after(s, s0)
    a = b1.run_policies(s["l0"], s["l1"], s["u"], 60, (5,), p, trace=True)["_p3_obj"].tr
    c = b1.run_policies(l0b, l1b, s["u"], 60, (5,), p, trace=True)["_p3_obj"].tr
    d = p.delay
    # queries and bets issued at t <= s0 + d use only events <= s0 - 1
    assert np.array_equal(a["ask"], c["ask"])
    assert np.array_equal(a["lam"][: s0 + d + 1], c["lam"][: s0 + d + 1])
    assert np.array_equal(a["dep"][: s0 + d + 1], c["dep"][: s0 + d + 1])
    assert np.array_equal(a["logw"][: s0 + d], c["logw"][: s0 + d])
    assert not np.array_equal(a["logw"][s0 + d :], c["logw"][s0 + d :])


def test_bets_frozen_at_issue_time_and_wealth_is_released_product():
    p = replace(SMALL, alpha=1e-12)  # never promotes, so the wealth is one plain product
    s = stream("W1", p)
    tr = b1.run_policies(s["l0"], s["l1"], s["u"], 60, (5,), p, trace=True)["_p3_obj"].tr
    assert tr["lam"].min() >= 0 and tr["lam"].max() <= p.pmin / 2 + 1e-12
    logs = np.log1p(tr["lam"] * tr["x"])
    d = p.delay
    for t in (d - 1, d, 57, 199, p.T - 1):
        expect = logs[: t - d + 1].sum(0) if t >= d else np.zeros(logs.shape[1])
        assert np.allclose(tr["logw"][t], expect)
    # the bet of a late event is a function of earlier released data only (not of its own label)
    l0b, l1b = swap_after(s, p.T - 1)
    tr2 = b1.run_policies(l0b, l1b, s["u"], 60, (5,), p, trace=True)["_p3_obj"].tr
    assert np.array_equal(tr["lam"], tr2["lam"])


def test_structural_zero_on_agreement():
    p = SMALL
    s = stream("W1", p)
    tr = b1.run_policies(s["l0"], s["l1"], s["u"], 80, (5,), p, trace=True)["_p3_obj"].tr
    agree = s["l0"] == s["l1"]
    assert not tr["ask"][agree].any()
    assert (tr["x"][agree] == 0).all()
    assert tr["ask"].any() and (tr["x"][~agree] != 0).any()


def test_exact_null_false_promotion_rate():
    n = 2000
    for pmin in (0.05, 0.5):  # the second setting uses 10x larger bets to make the check bite
        p = replace(SMALL, T=300, pmin=pmin)
        s = b1.make_stream("NULL", p, n, 11, 0)
        assert abs((s["l0"] - s["l1"]).mean()) < 0.01  # E[D] = 0
        res = b1.run_policies(s["l0"], s["l1"], s["u"], 90, (5,), p)
        rate = float(np.mean(~np.isnan(res["P3"]["t_prom"])))
        slack = 3 * math.sqrt(p.alpha * (1 - p.alpha) / n)
        assert rate <= p.alpha + slack, (pmin, rate)


def test_w3_reversal_timing_hidden_from_policies():
    p = b1.Params(T=2000)
    s = b1.make_stream("W3", p, 2000, 9, 2)
    assert abs(s["reversal"].mean() - 150) < 12 and s["reversal"].min() >= 1
    reg = s["regime"]
    assert (reg[: p.tau] == 0).all() and set(np.unique(reg)) == {0, 1, 3}
    # policies receive no regime information: run_policies has no regime argument, and the
    # oracle (evaluator side) is the only consumer of it
    code = b1.run_policies.__code__
    assert "regime" not in code.co_varnames[: code.co_argcount]
    shuffled = np.random.default_rng(0).permutation(reg.T).T
    small = replace(p, T=2000)
    a = b1.run_policies(s["l0"][:, :50], s["l1"][:, :50], s["u"][:, :50], 200, (5,), small)
    o1 = b1.oracle_out(reg[:, :50], s["l0"][:, :50], s["l1"][:, :50])
    o2 = b1.oracle_out(shuffled[:, :50], s["l0"][:, :50], s["l1"][:, :50])
    assert not np.array_equal(o1["loss"], o2["loss"])
    assert a["P3"]["queries"].max() <= 200
    assert (o1["switches"] == 2).mean() > 0.9  # switch at change and at reversal


def test_p3b_cap_respected_per_event():
    p = SMALL
    s = stream("W1", p)
    tr = b1.run_policies(s["l0"], s["l1"], s["u"], 60, (5,), p, trace=True, b2=True)["_p3b_obj"].tr
    assert tr["lam"].min() >= 0
    assert (tr["lam"] <= tr["q"] / 2 + 1e-12).all()
    assert (tr["q"][tr["ask"] > 0] >= p.pmin - 1e-12).all()
    # the cap is actually used above B1's p_min/2 somewhere, so the check is not vacuous
    assert (tr["lam"] > p.pmin / 2 + 1e-12).any()


def test_p3b_boundary_null_false_promotion_rate():
    n = 2500  # regime 4: E[D] = 0 exactly on the disagreement event
    p = replace(SMALL, T=300)
    s = b1.make_stream("NULL", p, n, 21, 0)
    assert abs((s["l0"] - s["l1"]).mean()) < 0.01
    res = b1.run_policies(s["l0"], s["l1"], s["u"], 90, (5,), p, b2=True)
    rate = float(np.mean(~np.isnan(res["P3b"]["t_prom"])))
    assert rate <= p.alpha + 3 * math.sqrt(p.alpha * (1 - p.alpha) / n), rate
