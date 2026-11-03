import itertools
import math

import numpy as np
import pytest

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.atlas_dependence_baselines import (
    DEP_METHODS,
    MarkovLREProcess,
    build_dep,
    null_sup_loglik,
)
from shiftlab.dive.switching_explore import (
    Config,
    Stream,
    build_method,
    make_bernoulli_stream,
    run,
)

NAMES = list(DEP_METHODS)
ALPHA = 0.1


def test_registry_shape():
    for fac, gated, note in DEP_METHODS.values():
        assert callable(fac) and gated is True and isinstance(note, str)


def test_null_sup_matches_grid():
    q0 = 0.55
    rng = np.random.default_rng(0)
    for _ in range(4):
        z = (rng.random(40) < 0.8).astype(int)
        n = np.zeros(4)
        for p, c in itertools.pairwise(z):
            n[2 * p + c] += 1
        v = null_sup_loglik(n[None], q0)[0]
        best = -math.inf
        for a in np.linspace(1e-4, 1 - 1e-4, 300):
            for b in np.linspace(1e-4, 1 - 1e-4, 300):
                if a / (1 - b + a) <= q0:
                    ll = (
                        n[1] * math.log(a)
                        + n[0] * math.log(1 - a)
                        + n[3] * math.log(b)
                        + n[2] * math.log(1 - b)
                    )
                    best = max(best, ll)
        assert best - 1e-9 <= v <= best + 0.05


def test_markov_eprocess_grows_on_favourable():
    ep = MarkovLREProcess(0.55, 0.1, 60)
    rng = np.random.default_rng(1)
    for z in rng.random(60) < 0.9:
        ep.update_z(int(z))
    assert ep.alarm


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("d", [1, 10])
@pytest.mark.parametrize("B", [15, 75])
def test_runs_within_budget(name, d, B):
    cfg = Config(T=300, B=B, d=d, seed=3)
    for seed in range(3):
        st = make_bernoulli_stream(np.random.default_rng(seed), 300, (0.1, 0.9))
        r = run(st, build_dep(name, cfg), cfg)
        assert r.queries <= B


@pytest.mark.parametrize("name", NAMES)
def test_non_peeking(name):
    T, d, t0 = 300, 10, 150
    cfg = Config(T=T, B=30, d=d, seed=5)
    for seed in range(3):
        st = make_bernoulli_stream(np.random.default_rng(seed), T, (0.1, 0.9))
        y = st.loss0.copy()
        y[t0:] = 1.0 - y[t0:]
        st2 = Stream(y, 1.0 - y, st.truth)
        a = run(st, build_dep(name, cfg), cfg)
        b = run(st2, build_dep(name, cfg), cfg)
        assert np.array_equal(a.actions[: t0 + d], b.actions[: t0 + d])
        assert np.array_equal(a.query_mask[: t0 + d], b.query_mask[: t0 + d])


def _fp_rate(name, rho, bt, d, n, T=300):
    cell = fa.Family3CellSpec(rho, 0.3, 0.6, "strong", "harmful", d, bt, T=T).null_twin()
    k = 0
    for sd in range(n):
        st = fa.make_stream(cell, sd)
        cfg = cell.config(sd)
        r = fa.run_for(cell, st, build_dep(name, cfg), cfg)
        k += int((r.fp_regime or 0) > 0)
    return k / n


@pytest.mark.parametrize("name", NAMES)
def test_boundary_null_validity_rho0(name):
    n = 300
    rate = _fp_rate(name, 0.0, 0.25, 1, n)
    assert rate <= ALPHA + 2 * math.sqrt(ALPHA * (1 - ALPHA) / n)


@pytest.mark.parametrize("name", NAMES)
def test_report_rho08_null(name, capsys):
    n = 100
    rate = _fp_rate(name, 0.8, 0.25, 1, n)
    with capsys.disabled():
        print(f"\n[rho=0.8, B/T=0.25, d=1, n={n}] {name}: false promotion {rate:.3f}")
    assert 0.0 <= rate <= 1.0  # reported, not asserted against alpha


@pytest.mark.parametrize("name", NAMES)
def test_power_late_onset(name, capsys):
    """Strong late-onset stream (onset at 0.3 T, p = 0.1 -> 0.95): beats no_switch."""
    T, B, d = 300, 100, 5
    gains, wins = [], 0
    for seed in range(20):
        cfg = Config(T=T, B=B, d=d, seed=seed)
        path = np.zeros(T, dtype=int)
        path[int(0.3 * T) :] = 1
        st = make_bernoulli_stream(np.random.default_rng(seed), T, (0.1, 0.95), path=path)
        r = run(st, build_dep(name, cfg), cfg)
        ns = run(st, build_method("no_switch"), cfg)
        gains.append(ns.cost - r.cost)
        wins += r.promotions > 0
    with capsys.disabled():
        print(f"\n[power] {name}: promoted {wins}/20, mean gain vs no_switch {np.mean(gains):.2f}")
    assert wins >= 5 and float(np.mean(gains)) > 0
