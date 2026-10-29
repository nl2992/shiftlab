"""Tests for the Lane B D2 split-clock development Monte Carlo (scripts/lane_b/split_clock_small.py)."""

from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from shiftlab.seed_registry import load_registry

_ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, _ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


sc = _load("lane_b_split_clock_small", "scripts/lane_b/split_clock_small.py")
P = sc.Params()
SPECS = {s.name: s for s in sc.arm_specs(P)}


def _cell(world="reversal", q=0.8, delta_b=0.0, index=0):
    return {"world": world, "q": q, "shift": "x", "delta_b": delta_b, "index": index}


def test_seed_block_is_registered_and_used_ranges_fit():
    blocks = {b.id: b for b in load_registry().blocks}
    b = blocks["lane_b_d2_split_clock_development"]
    assert (b.start, b.end) == sc.SEED_BLOCK
    n_cells = len(sc.cells())
    assert sc.SEED_BLOCK[0] + n_cells * sc.SEEDS_PER_CELL - 1 < sc.CALIB_SEED_START
    last_calib = sc.CALIB_SEED_START + (len(sc.QUALITIES) - 1) * 1000 + P.n_calib - 1
    assert last_calib <= sc.SEED_BLOCK[1]


def test_sign_agreement_matches_quality():
    for q in sc.QUALITIES:
        env = sc.make_env(_cell(world="null", q=q), replace(P, b0=0.0), 200, seed_start=1)
        agree = np.mean(np.sign(env.S) == np.sign(env.Z))
        assert abs(agree - q) < 0.02


def test_bias_shift_applies_only_after_reversal():
    env = sc.make_env(_cell(delta_b=0.8), P, 50, seed_start=7)
    sf = env.sigma_f
    for i in range(5):
        nu = env.nu[i]
        resid = env.S[i] - P.beta * env.Z[i]
        assert abs(resid[:nu].mean() - P.b0) < 4 * sf / math.sqrt(nu)
        assert abs(resid[nu:].mean() - (P.b0 + 0.8)) < 4 * sf / math.sqrt(P.T - nu)


@pytest.mark.parametrize("name", sorted(SPECS))
def test_hard_budget_never_exceeded(name):
    env = sc.make_env(_cell(delta_b=0.5), P, 60, seed_start=11)
    o = sc.simulate(env, SPECS[name], P, h=6.0)
    cost = P.c_g * o["Qg"].sum(1) + P.c_f * o["Qf"].sum(1)
    assert np.all(cost <= P.B + 1e-9)
    assert np.allclose(cost, o["spent"])


def test_no_gold_promotion_before_any_gold_label_can_arrive():
    p = replace(P, d_g=P.T + 1)  # no gold label is ever released
    env = sc.make_env(_cell(), p, 50, seed_start=13)
    for name in ("gold_only", "cstar_0.25", "twophase_1.00", "adaptive_1.00"):
        o = sc.simulate(env, SPECS[name], p, h=6.0)
        assert not o["promoted"].any()


def test_promotion_time_respects_gold_delay():
    env = sc.make_env(_cell(), P, 100, seed_start=17)
    o = sc.simulate(env, SPECS["twophase_1.00"], P, h=6.0)
    # log(20)/log(1.36) > 9 positive labels are needed, the first released at round d_g.
    assert o["t_promo"][o["promoted"]].min() >= P.d_g + 9


def test_gold_promotion_valid_under_null_but_surrogate_only_is_not():
    env = sc.make_env(_cell(world="null", q=0.8), P, 600, seed_start=19)
    g = sc.simulate(env, SPECS["gold_only"], P, h=6.0)["promoted"].mean()
    a = sc.simulate(env, SPECS["adaptive_1.00"], P, h=6.0)["promoted"].mean()
    s = sc.simulate(env, SPECS["surrogate_only"], P, h=6.0)["promoted"].mean()
    assert g <= 0.08 and a <= 0.08  # Ville: <= alpha = 0.05, plus Monte Carlo slack
    assert s >= 0.3  # optimistic bias b0 drives invalid promotions


def test_fast_labels_never_enter_gold_eprocess():
    """Changing every fast label leaves the gold-only path untouched."""
    env = sc.make_env(_cell(), P, 40, seed_start=23)
    o1 = sc.simulate(env, SPECS["gold_only"], P, h=6.0)
    env.S[:] = 100.0
    o2 = sc.simulate(env, SPECS["gold_only"], P, h=6.0)
    assert np.array_equal(o1["t_promo"], o2["t_promo"])
    assert np.array_equal(o1["t_roll"], o2["t_roll"])


def test_hidden_bias_shift_blinds_fast_change_detector():
    """delta_b = 2 beta Delta cancels the reversal in the fast mean: only gold can roll back."""
    env = sc.make_env(_cell(q=0.8, delta_b=0.8), P, 300, seed_start=29)
    spec = replace(SPECS["twophase_1.00"], gold_backstop=False)
    o = sc.simulate(env, spec, P, h=7.0)
    pre = o["promoted"] & (o["t_promo"] < env.nu)
    caught_after = o["rolled"] & (o["t_roll"] >= env.nu)
    assert (pre & caught_after).sum() / max(1, pre.sum()) < 0.15
    env0 = sc.make_env(_cell(q=0.8, delta_b=0.0), P, 300, seed_start=29)
    o0 = sc.simulate(env0, spec, P, h=7.0)
    pre0 = o0["promoted"] & (o0["t_promo"] < env0.nu)
    caught0 = o0["rolled"] & (o0["t_roll"] >= env0.nu)
    assert (pre0 & caught0).sum() / max(1, pre0.sum()) > 0.8


def test_regret_accounting_on_trivial_paths():
    env = sc.make_env(_cell(), P, 5, seed_start=31)
    never = sc.Spec("never", 0.0, 0.0, 0.0, 0.0, gold_backstop=False)
    o = sc.simulate(env, never, P)
    assert np.allclose(o["regret"], P.delta * env.nu)
    assert np.all(o["switches"] == 0) and np.all(o["spent"] == 0)


def test_calibrate_h_hits_target():
    p = replace(P, n_calib=200)
    h, fr = sc.calibrate_h(SPECS["gold_only"], 0.8, p)
    assert fr <= p.target_false_rollback
    assert h in sc.H_GRID
