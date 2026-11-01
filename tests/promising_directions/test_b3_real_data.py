from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/promising_directions/b3_real_data.py"
spec = importlib.util.spec_from_file_location("b3_real_data", SCRIPT)
b3 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b3
spec.loader.exec_module(b3)
b1 = b3.b1


def synthetic(rate_chal_better: float, n: int = 6, seed: int = 1):
    """Stream with 40% disagreements; on a disagreement the challenger is right w.p. given."""
    rng = np.random.default_rng(seed)
    dis = rng.random(b3.T_EP) < 0.4
    chal_right = rng.random(b3.T_EP) < rate_chal_better
    l0 = np.where(dis, chal_right, 0).astype(np.int8)  # incumbent wrong iff challenger right
    l1 = np.where(dis, ~chal_right, 0).astype(np.int8)
    u = rng.random((b3.T_EP, n))
    return l0, l1, u


def test_p6_binomial_threshold_is_exact_one_sided():
    assert b3.p6_reject(50, 50) and not b3.p6_reject(25, 50)
    assert b3.p6_reject(32, 50) and not b3.p6_reject(31, 50)
    assert binomtest(32, 50, 0.5, alternative="greater").pvalue <= 0.05
    assert binomtest(31, 50, 0.5, alternative="greater").pvalue > 0.05
    assert not b3.p6_reject(0, 0)


def test_p6_promotes_after_fifty_released_labels_and_never_rolls_back():
    l0, l1, u = synthetic(1.0)
    p = b1.Params(T=b3.T_EP, delay=7)
    out = b3.run_p6(l0[:, None].repeat(6, 1), l1[:, None].repeat(6, 1), u, 200, p)
    assert (out["switches"] == 1).all() and (out["rollbacks"] == 0).all()
    # issuing stops once the 50th label is released: at most 50 + labels in flight
    assert out["queries"].max() <= 50 + p.delay and out["queries"].min() >= 50
    assert (out["t_prom"] > p.delay).all()


def test_p6_does_not_promote_against_a_worse_challenger_and_respects_budget():
    l0, l1, u = synthetic(0.0)
    p = b1.Params(T=b3.T_EP, delay=3)
    out = b3.run_p6(l0[:, None].repeat(6, 1), l1[:, None].repeat(6, 1), u, 30, p)
    assert (out["switches"] == 0).all() and out["queries"].max() <= 30
    assert (out["loss"] == l0.sum()).all()


def test_adapter_matches_run_policies_and_seeds_are_independent_columns():
    l0, l1, u = synthetic(0.7, n=4)
    delay = 5
    res = b3.run_episode(l0, l1, u, 120, delay, base_err=0.1)
    p = b1.Params(T=b3.T_EP, delay=delay, base_err=0.1, eps=0.05)
    a0 = np.repeat(l0[:, None], 4, 1)
    a1 = np.repeat(l1[:, None], 4, 1)
    direct = b1.run_policies(a0, a1, u, 120, (5,), p, b2=True)
    for pol in ("P2", "P3b"):
        for key in ("loss", "queries", "switches", "rollbacks"):
            assert np.array_equal(res[pol][key], direct[pol][key])
    assert np.array_equal(res["P2"]["t_prom"], direct["P2"]["t_prom"], equal_nan=True)
    assert np.array_equal(res["P0"]["loss"], np.full(4, float(l0.sum())))
    assert np.array_equal(res["P1"]["switches"], np.ones(4))
    one = b3.run_episode(l0, l1, u[:, 2:3], 120, delay, base_err=0.1)
    for pol in ("P3b", "P6"):
        assert one[pol]["loss"][0] == res[pol]["loss"][2]
        assert one[pol]["queries"][0] == res[pol]["queries"][2]


def test_episode_u_column_depends_only_on_episode_and_seed():
    a, b = b3.episode_u(3, 5), b3.episode_u(3, 2)
    assert np.array_equal(a[:, :2], b) and not np.array_equal(a, b3.episode_u(4, 5))


def test_episode_offset_rule():
    s = b3.episode_plan(323629, 539383 - 323629)
    assert len(s) == 50 and s[0] == 323629 and s[1] - s[0] == 215754 // 50
    assert all(b - a >= b3.T_EP for a, b in itertools.pairwise(s))
    assert s[-1] + b3.T_EP <= 539383
    spam = b3.episode_plan(5594, 3730)
    assert spam == [5594]
    elec = b3.locked_plan("elec2")
    assert len(elec) == 4 and elec[0] == 36250 and elec[1] - elec[0] == 9062 // 4
    assert len(b3.locked_plan("weather")) == 3 and len(b3.locked_plan("bank")) == 8
    assert len(b3.locked_plan("rialto")) == 16 and len(b3.locked_plan("criteo")) == 50
    assert b3.locked_plan("criteo")[1] - b3.locked_plan("criteo")[0] == 6587211 // 50


def test_programme_rules():
    def mk(win, safe):
        return {"primary": {"WIN": win, "SAFE": safe}}

    ok = {f"s{i}": mk(i < 3, True) for i in range(7)}
    assert b3.programme(ok)["outcome"] == "SUCCESS"
    assert b3.programme({f"s{i}": mk(i < 1, True) for i in range(7)})["outcome"] == "PARTIAL"
    assert b3.programme({f"s{i}": mk(False, i != 0) for i in range(7)})["outcome"] == "PARTIAL"
    assert b3.programme({f"s{i}": mk(False, i > 1) for i in range(7)})["outcome"] == "FAIL"
