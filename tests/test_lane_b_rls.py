"""Tests for the Lane B C2 RLS development check (scripts/lane_b/rls_exact_small.py)."""

from __future__ import annotations

import importlib.util
import itertools
import math
import sys
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


rls = _load("lane_b_rls_exact_small", "scripts/lane_b/rls_exact_small.py")
sep = _load("lane_b_separation_check_for_rls", "scripts/lane_b/separation_check.py")


# ------------------------------------------------------------------ seeds
def _overlap(a, b):
    return max(a[0], b[0]) <= min(a[1], b[1])


def _separation_check_used_ranges():
    used = []
    for k in range(24):  # first check: base + [0,1000) and base + [5000,6000)
        base = sep.SEED_BASE + k * sep.CELL_STRIDE
        used += [(base, base + 999), (base + sep.NULL_OFFSET, base + sep.NULL_OFFSET + 999)]
    for v in range(len(sep.VARIANTS)):  # K_alpha reference
        base = sep.SEED_BASE + 90000 + 1000 * v
        used.append((base, base + 999))
    for r_i, d_i, b_i in itertools.product(range(2), range(2), range(4)):  # corrective check
        base = sep.corrective_base(r_i, d_i, b_i)
        used.append((base, base + 1999))
    return used


def test_seed_ranges_registered_and_disjoint():
    alt = (rls.SEED_ALT, rls.SEED_ALT + 1999)
    null = (rls.SEED_NULL, rls.SEED_NULL + 1999)
    reg = {b.id: b for b in load_registry().blocks}
    blk = reg["lane_b_toy_development"]
    ovf = reg["lane_b_toy_first_check_overflow"]
    assert (blk.start, blk.end) == rls.SEED_BLOCK
    assert (ovf.start, ovf.end) == rls.OVERFLOW_BLOCK
    for rng in (alt, null):
        assert blk.start <= rng[0] and rng[1] <= blk.end
        assert not _overlap(rng, rls.OVERFLOW_BLOCK)
        for u in _separation_check_used_ranges() + list(rls.USED_RANGES):
            assert not _overlap(rng, u), (rng, u)
    assert not _overlap(alt, null)
    with pytest.raises(ValueError):
        rls.seed_list("alt", 2001)


# ------------------------------------------------------------------ closed forms
@pytest.mark.parametrize("sigma", [0, 1, 2, 3])
@pytest.mark.parametrize("d", [1, 2, 3, 4, 5, 8])
def test_jitter_floor_matches_bruteforce(sigma, d):
    g = rls.jitter_floor(sigma, d)
    assert g == pytest.approx(rls.jitter_floor_bruteforce(sigma, d))
    assert g <= rls.e_abs(sigma) + 1e-12
    if sigma >= 1:  # Proposition E1 scaling: g(sigma,d) >= min(sigma,d)/4
        assert g >= min(sigma, d) / 4 - 1e-12
    if d >= 2 * sigma + 1:
        assert g == pytest.approx(rls.e_abs(sigma))


def test_e_abs_matches_enumeration():
    for s in range(5):
        assert rls.e_abs(s) == pytest.approx(np.mean(np.abs(np.arange(-s, s + 1))))


def test_anytime_power_monotone_and_mc():
    p = [rls.anytime_power(n) for n in (10, 30, 60, 90)]
    assert all(a <= b + 1e-12 for a, b in itertools.pairwise(p))
    rng = np.random.default_rng(3)
    z = np.where(rng.random((20000, 60)) < 0.7, 1, -1)
    logw = np.cumsum(np.log1p(rls.DELTA * z), axis=1)
    mc = (logw.max(1) >= math.log(1 / rls.ALPHA) - 1e-12).mean()
    assert abs(mc - rls.anytime_power(60)) < 0.015
    # under the boundary null the fixed-stake wealth crosses with probability <= alpha
    assert rls.anytime_power(200, mean=0.0) <= rls.ALPHA


# ------------------------------------------------------------------ world
@pytest.mark.parametrize("sigma", [0, 1, 2])
def test_world_structure(sigma):
    w = rls.draw_world(rls.seed_list("alt", 50), sigma, "alt")
    assert np.all(np.abs(w["eta"]) <= sigma)
    tab = rls.Tables(sigma)
    for i in range(50):
        phi = w["phi"][i]
        for j in range(1, rls.S - 1):
            start = phi + j * rls.L + w["eta"][i, j + 1]
            assert w["good"][i, start : start + rls.W].all()
            assert not w["good"][i, start - 1] and not w["good"][i, start + rls.W]
        # nominal window of the true phase agrees with the realised state outside jitter zones
        nom = tab.nom[phi, : rls.T]
        assert (nom != w["good"][i]).sum() <= 2 * sigma * (rls.S + 2)
    assert set(np.unique(w["z"])) <= {-1, 1}


def test_common_random_numbers_across_sigma():
    a = rls.draw_world(rls.seed_list("alt", 20), 1, "alt")
    b = rls.draw_world(rls.seed_list("alt", 20), 2, "alt")
    assert np.array_equal(a["phi"], b["phi"])
    assert np.array_equal(a["uq"], b["uq"])


# ------------------------------------------------------------------ posterior
def test_posterior_matches_bruteforce_enumeration():
    sigma, n_lab = 1, 9
    tab = rls.Tables(sigma)
    rng = np.random.default_rng(11)
    times = np.sort(rng.choice(np.arange(5, 70), size=n_lab, replace=False))
    zs = rng.choice([-1.0, 1.0], size=n_lab)
    post = rls.Posterior(1, tab)
    for s, zz in zip(times, zs):
        post.update(np.array([0]), int(s), np.array([zz]))
    lp = post.logpost()[0]
    etas = np.arange(-sigma, sigma + 1)
    brute = np.empty(rls.L)
    for ph in range(rls.L):
        wins = sorted({int(tab.g[ph, s]) for s in times})
        tot = 0.0
        for combo in itertools.product(etas, repeat=len(wins)):
            eta_of = dict(zip(wins, combo))
            ll = 0.0
            for s, zz in zip(times, zs):
                g = int(tab.g[ph, s])
                u = s - ph - g * rls.L
                good = eta_of[g] <= u < eta_of[g] + rls.W
                ll += math.log((1 + zz * rls.DELTA * (2 * good - 1)) / 2)
            tot += math.exp(ll) / len(etas) ** len(wins)
        brute[ph] = math.log(tot)
    assert np.allclose(lp, brute, atol=1e-9)


def test_posterior_concentrates_with_many_labels():
    tab = rls.Tables(0)
    w = rls.draw_world(rls.seed_list("alt", 5), 0, "alt")
    post = rls.Posterior(5, tab)
    for s in range(rls.T):
        post.update(np.arange(5), s, w["z"][:, s].astype(float))
    assert np.array_equal(post.logpost().argmax(1), w["phi"])


# ------------------------------------------------------------------ causality, budget, validity
LEARNING = ("rls", "mle_uniform", "mle_active", "ts_forecaster", "exp4", "reactive")


@pytest.mark.parametrize("arm", LEARNING)
@pytest.mark.parametrize("d", [1, 4])
def test_no_lookahead_and_budget(arm, d):
    n, B = 12, 30
    cell = rls.Cell(1, d, B, "alt")
    tab = rls.Tables(1)
    w1 = rls.draw_world(rls.seed_list("alt", n), 1, "alt")
    t0 = 150
    w2 = dict(w1)
    w2["z"] = w1["z"].copy()
    w2["z"][:, t0:] = -w2["z"][:, t0:]
    r1 = rls.simulate(arm, w1, cell, tab, return_paths=True)
    r2 = rls.simulate(arm, w2, cell, tab, return_paths=True)
    # outcomes from t0 on are first visible at t0 + d: everything decided before must coincide
    assert np.array_equal(r1["A"][:, : t0 + d], r2["A"][:, : t0 + d])
    assert np.array_equal(r1["Q"][:, : t0 + d], r2["Q"][:, : t0 + d])
    assert np.allclose(r1["stake"][:, : t0 + d], r2["stake"][:, : t0 + d])
    for r in (r1, r2):
        assert (r["Q"].sum(1) <= B).all()
        assert (r["stake"] >= 0).all() and (r["stake"] <= rls.STAKE_MAX).all()
        # no candidate deployment before the gate fires
        for i in range(n):
            pt = int(r["promo_t"][i])
            assert not r["A"][i, :pt].any()


@pytest.mark.parametrize("arm", ["rls", "ts_forecaster", "reactive"])
def test_null_false_promotion_smoke(arm):
    n = 300
    cell = rls.Cell(1, 1, 60, "zero")
    w = rls.draw_world(rls.seed_list("null", n), 1, "zero")
    r = rls.simulate(arm, w, cell, rls.Tables(1))
    rate = r["promoted"].mean()
    assert rate <= rls.ALPHA + 3 * math.sqrt(rls.ALPHA * (1 - rls.ALPHA) / n)


def test_oracle_and_references():
    n = 40
    cell = rls.Cell(2, 1, 30, "alt")
    tab = rls.Tables(2)
    w = rls.draw_world(rls.seed_list("alt", n), 2, "alt")
    orc = rls.simulate("oracle", w, cell, tab)
    never = rls.simulate("never", w, cell, tab)
    assert np.all(never["net_cost"] == 0)
    # oracle earns about S * (Delta (W - 2E|eta|) - 2k) in expectation
    target = -rls.S * rls.oracle_period_gain(2)
    assert abs(orc["net_cost"].mean() - target) < 3.0
    # oracle per-boundary loss is near Delta E|eta| + k
    assert abs(np.nanmean(orc["per_boundary"]) - (rls.DELTA * rls.e_abs(2) + rls.K_SWITCH)) < 0.1
