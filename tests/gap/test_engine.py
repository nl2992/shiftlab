import numpy as np
import pytest

from shiftlab.gap import audit
from shiftlab.gap import engine as E
from shiftlab.gap import worlds as W
from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

S, T = 60, 2000


@pytest.fixture(scope="module")
def sim():
    return g.simulate(g.World(kind="concept", delta=2.0, shape="abrupt", t0=800), S, 1001)


@pytest.fixture(scope="module")
def stream():
    w = W.LogitWorld(regimes=(W.Regime(), W.Regime("concept", 2.0)))
    return W.make_stream(w, S, 11, z=W.scheduled_regimes("abrupt", T, 800)[None].repeat(S, 0))


def test_legacy_parity_pprm_tight_and_hg(sim, monkeypatch):
    st = E.ensure_stream(sim)
    U = np.random.default_rng(5).random((S, T))
    orig = np.random.default_rng

    class R:
        def __init__(self, s):
            self.s = s

        def random(self, shape):
            return U.T if shape == (T, S) else orig(self.s).random(shape)

    monkeypatch.setattr(E.np.random, "default_rng", lambda s=None: R(s) if s == 10005 else orig(s))
    for kw, legacy in (
        ({}, det.pprm_tight(sim, frac=0.1, delay=5, lseed=5, tol=0.0)),
        (
            {"gamma": 0.99, "gate_w": 100},
            det.fix_brier(sim, frac=0.1, delay=5, lseed=5, tol=0.0, gamma=0.99, gate_w=100),
        ),
    ):
        cfg = E.Cfg(risk="brier", frac=0.1, cap_mode="x", release="legacy", unq_delay=True, **kw)
        out = E.run(st, cfg, delay=5, qseed=5)
        assert np.abs(out["logW"] - legacy).max() < 1e-5


def test_exact_finite_support_cap():
    rows = audit.exact_cap_check()
    assert all(r["E_factor_sup_cap"] == pytest.approx(1.0, abs=1e-12) for r in rows)
    assert all(
        r["E_factor_x_cap"] > 1.0 + 1e-3 for r in rows
    )  # legacy cap is not a supermartingale step


def test_hard_budget_pathwise(stream):
    for pacing in ("none", "const", "remaining", "info_value", "reserve", "two_stage"):
        cfg = E.Cfg(risk="brier", frac=0.05, budget=60, pacing=pacing, alloc="uniform")
        out = E.run(stream, cfg, delay=5, qseed=3)
        assert out["labels"].max() <= 60, pacing
    out = E.run(stream, E.Cfg(risk="brier", frac=0.5, budget=40), delay=0, qseed=3)
    assert out["labels"].max() == 40 and (out["exhaust_t"] < T).all()


def test_budget_exhaustion_freezes_wealth(stream):
    out = E.run(stream, E.Cfg(risk="brier", frac=0.5, budget=40), delay=0, qseed=3)
    for i in range(S):
        t_ex = out["exhaust_t"][i]
        assert np.allclose(out["logW"][i, t_ex + 1 :], out["logW"][i, t_ex], atol=1e-6)


def test_causality_future_events_do_not_change_past(stream):
    base = E.run(stream, E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100), delay=5, qseed=2)
    pert = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in stream.items()}
    for k in ("loss", "brier", "proxy_brier", "proxy_cost", "p", "score"):
        pert[k][:, 1200:] = np.random.default_rng(9).random(pert[k][:, 1200:].shape) * 0.2
    out = E.run(pert, E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100), delay=5, qseed=2)
    assert np.array_equal(base["logW"][:, :1200], out["logW"][:, :1200])
    assert not np.array_equal(base["logW"][:, 1300:], out["logW"][:, 1300:])


def test_label_value_released_only_after_delay(stream):
    cfg = E.Cfg(risk="brier", frac=0.3)
    base = E.run(stream, cfg, delay=5, qseed=2)
    pert = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in stream.items()}
    pert["brier"][:, 1000] += 0.7  # change one realised loss
    out = E.run(pert, cfg, delay=5, qseed=2)
    assert np.array_equal(base["logW"][:, :1005], out["logW"][:, :1005])


def test_seed_reproducibility_and_common_random_numbers(stream):
    cfg = E.Cfg(risk="brier", frac=0.2, gamma=0.99, gate_w=100)
    a, b = E.run(stream, cfg, delay=5, qseed=4), E.run(stream, cfg, delay=5, qseed=4)
    assert np.array_equal(a["logW"], b["logW"])
    c = E.run(stream, cfg, delay=5, qseed=5)
    assert not np.array_equal(a["labels"], c["labels"])
    # arms with the same query probability query the same events (paired design)
    d = E.run(stream, E.Cfg(risk="brier", frac=0.2), delay=5, qseed=4)
    assert np.array_equal(a["labels"], d["labels"])


def test_parent_modified_identities(stream):
    parent = E.run(stream, E.Cfg(risk="brier", frac=0.2), delay=5, qseed=1)
    same = [
        E.Cfg(risk="brier", frac=0.2, rel="hard", rel_fallback="none"),
        E.Cfg(risk="brier", frac=0.2, alloc="mix", mix=(1.0, 0.0, 0.0)),
        E.Cfg(risk="brier", frac=0.2, gamma=1.0, gate_w=None),
    ]
    for cfg in same:
        out = E.run(stream, cfg, delay=5, qseed=1)
        assert np.allclose(out["logW"], parent["logW"], atol=1e-5), cfg


def test_prefix_equals_arrived_under_fixed_delay(stream):
    a = E.run(
        stream, E.Cfg(risk="brier", frac=0.2, release="prefix", unq_delay=True), delay=5, qseed=1
    )
    b = E.run(
        stream, E.Cfg(risk="brier", frac=0.2, release="arrived", unq_delay=True), delay=5, qseed=1
    )
    assert np.allclose(a["logW"], b["logW"], atol=1e-5)


def test_world_truth_separates_dimensions():
    w = W.LogitWorld(
        regimes=(
            W.Regime(),
            W.Regime("cov_benign", 3.0),
            W.Regime("concept", 2.0),
            W.Regime("cost", fn=20.0),
        )
    )
    eff = W.regime_effects(w)
    assert eff[1, 0] > 0.1 and abs(eff[1, 2]) < 0.03  # large discrepancy, no harm
    assert eff[2, 2] > 0.1  # concept shift harms
    assert eff[3, 0] < 0.01 and eff[3, 2] > 0.1  # cost change: zero discrepancy, large harm
