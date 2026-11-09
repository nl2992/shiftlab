"""Phase 0/1 tests for families C (C21-C30) and D (D31-D40) of the search60 compositor."""

import sys
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
for _p in (HERE, HERE / "search60", Path(__file__).resolve().parent):
    sys.path.insert(0, str(_p))
import compositor as comp
from test_search60_compositor import build, episode, run, spec


class FB(NamedTuple):
    event_id: int
    t_requested: int
    t_released: int
    model_losses: tuple


class Ev(NamedTuple):
    event_id: int
    t: int
    horizon: int
    model_predictions: tuple


class CtxStub:
    """Minimal ctx for D37.hurdle(), which only reads ctx.parent.cs."""

    class parent:
        cs = 5.0


CD = [f"C{i}" for i in range(21, 31)] + [f"D{i}" for i in range(31, 41)]


def key(r):
    return (r["net"], r["labels"], r["switches"], r["loss"])


def scenario(name, seed=0, n=330):
    """Outcome sequences x_i = 1 when the challenger is correct, one released label per 3 events."""
    rng = np.random.default_rng(seed)
    i = np.arange(n)
    if name == "alt":  # challenger good / bad / good / bad blocks
        p = np.where((i // 40) % 2 == 0, 0.8, 0.2)
    elif name == "weak":  # slim edge that fades
        p = np.where(i < 130, 0.58, 0.42)
    elif name == "collapse":  # strong edge, then a sharp reversal
        p = np.where(i < 8, 0.9, 0.1)
    elif name == "blocky":  # runs of identical outcomes: strong lag-1 autocorrelation
        runs = rng.random(n // 10 + 1) < np.tile([0.8, 0.3], n // 20 + 1)[: n // 10 + 1]
        return np.repeat(runs, 10)[:n].astype(int)
    else:
        raise KeyError(name)
    return (rng.random(n) < p).astype(int)


SCENARIOS = [("alt", 0.04), ("weak", 0.03), ("collapse", 0.08), ("blocky", 0.05)]


def drive(spec_, name, rate, seed=0, delay=100, step=3):
    """Feed released labels / predictions straight to a ComposedPolicy (no simulator).

    Returns (policy, path of deployed models, number of purchases made by request_labels)."""
    pol = build(spec_, delay=delay, log=1, seed=seed + 1)
    par, path, bought = pol.parent, [], 0
    for i, x in enumerate(scenario(name, seed)):
        t = delay + i * step
        par.acq.n_disagree = rate * t
        par.pending = 1
        pol.observe([FB(i, t - delay, t, (int(x), 1 - int(x)))])
        ev = Ev(10_000 + i, t, 2000, (0, 1))
        path.append(pol.predict(ev))
        bought += int(pol.request_labels(ev, 200 - bought).requested)
    return pol, path, bought


def differs(mid, settings=(0, 1), seeds=(0, 1)):
    for name, rate in SCENARIOS:
        for seed in seeds:
            _, p0, b0 = drive({"name": "off"}, name, rate, seed)
            for st in settings:
                _, p1, b1 = drive(spec(mid, st), name, rate, seed)
                if p0 != p1 or b0 != b1:
                    return name, st, seed
    return None


def first_flip(log):
    return next((r["t"] for r in log if r["kind"] == "switch" and r["action"] == "allow"), None)


# ---------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def all_runs():
    """Every module, both settings, one run_policies call on the toy stream."""
    return run([spec(m, st) for m in CD for st in (0, 1)], seed=1)


@pytest.mark.parametrize("mid", CD)
def test_module_constructs_and_runs(mid, all_runs):
    for st in (0, 1):
        r = all_runs[f"t_{mid}_{st}"]
        assert r["labels"] <= 200 and np.isfinite(r["net"])


@pytest.mark.parametrize("mid", CD)
def test_budget_and_delay(mid):
    from simulator import check_no_future_access

    pol = build(spec(mid, 1))
    res, _ = episode(pol, budget=40, seed=2)
    assert res.requested_labels <= 40
    assert not check_no_future_access(res, 100)
    assert all(r["event_id"] + 100 < 2000 for r in res.records if r["requested"])


@pytest.mark.parametrize("mid", CD)
def test_no_evaluator_field_read(mid):
    episode(build(spec(mid, 1)), wrap=True, seed=3)


@pytest.mark.parametrize("mid", CD)
def test_determinism_under_seed(mid):
    a = drive(spec(mid, 1), "alt", 0.04, seed=3)
    b = drive(spec(mid, 1), "alt", 0.04, seed=3)
    assert a[1:] == b[1:]
    assert [r.get("reason") for r in a[0].log] == [r.get("reason") for r in b[0].log]


def test_full_episode_repeatable():
    a = run([spec("C26", 1)], seed=5)["t_C26_1"]
    b = run([spec("C26", 1)], seed=5)["t_C26_1"]
    assert key(a) == key(b)


@pytest.mark.parametrize("mid", CD)
def test_module_changes_behaviour(mid):
    """Guards against inert modules: some constructed stream / setting must differ from the parent."""
    assert differs(mid) is not None, f"{mid} identical to the parent on every constructed stream"


def test_c_posterior_engines_exclusive():
    for a, b in (("C21", "C24"), ("C25", "C26"), ("C29", "C30"), ("C21", "C30")):
        with pytest.raises(comp.UnsupportedCombo):
            comp.validate_spec({"modules": [a, b]})
    comp.validate_spec({"modules": ["C22", "C23", "C27", "C28", "C21", "D31", "D38"]})


NEUTRAL = [
    ("C21", {"mix": 0.0}),
    ("C29", {"priors": ((1.0, 1.0),)}),
    ("D34", {"gamma_enter": 0.3, "gamma_exit": 0.3}),
    ("D35", {"slope": 0.0}),
    ("D36", {"hazard": 1e-9, "floor_horizon": 0}),
    ("D37", {"hurdle_scale": 1.0}),
    ("D39", {"gamma_early": 0.3, "gamma_late": 0.3}),
    ("D40", {"band": 0.0}),
]


@pytest.mark.parametrize("mid,params", NEUTRAL)
def test_neutral_parameters_reproduce_parent(mid, params):
    """With the parent's own parameters an overlay re-derives the parent's rule: no hidden bias."""
    s = {"name": "neutral", "modules": [{"id": mid, "params": params}]}
    for name, rate in SCENARIOS[:3]:
        _, p0, b0 = drive({"name": "off"}, name, rate, 0)
        pol, p1, b1 = drive(s, name, rate, 0)
        assert (p0, b0) == (p1, b1)
        assert getattr(pol.mods[0], "n_veto", 0) == 0
        assert getattr(pol.mods[0], "n_override", 0) == 0


def test_wald_parent_overlay_runs():
    s = spec("D40", 1, parent={"kind": "wald", "lam": 0.98, "gamma": 0.3})
    _, path, _ = drive(s, "alt", 0.04)
    assert len(path) == 330


def test_c_veto_and_override_are_logged():
    pol, _, _ = drive(spec("C26", 1), "alt", 0.04)
    m = pol.mods[0]
    assert m.n_veto > 0 and m.n_override > 0 and m.n_veto + m.n_override == len(m.audit)
    assert any(r.get("action") == "veto" and "C26" in r["reason"] for r in pol.log)
    assert any(r["kind"] == "override" and "C26" in r["reason"] for r in pol.log)


def test_c_belief_internals():
    pol, _, _ = drive(spec("C27", 1), "blocky", 0.05)
    assert pol.mods[0].f < 1.0  # autocorrelated outcomes shrink the effective sample
    pol, _, _ = drive(spec("C23", 1), "collapse", 0.08)
    assert pol.mods[0].n_alarm >= 1
    s = {"name": "t22", "modules": [{"id": "C22", "params": {"surprise": 0.2}}]}
    pol, _, _ = drive(s, "alt", 0.04)
    assert pol.mods[0].n_alert >= 1
    pol, _, _ = drive(spec("C25", 1), "alt", 0.04)
    m = pol.mods[0]
    assert abs(m.w.sum() - 1.0) < 1e-9 and len(m.w) <= m.params["truncate"] + 1
    pol, _, _ = drive(spec("C28", 0), "alt", 0.04)
    assert 0 < pol.mods[0].n < len(pol.mods[0].items)  # age weights are below one
    pol, _, _ = drive(spec("C26", 1), "alt", 0.04)
    assert 0.0 <= pol.mods[0].pi <= 1.0
    pol, _, _ = drive(spec("C30", 0), "alt", 0.04)
    assert pol.mods[0].rn > 0 and 0 < pol.mods[0].rate(pol.ctx) <= 1


def test_d31_delays_first_promotion():
    base, _, _ = drive({"name": "off"}, "alt", 0.04)
    pol, _, _ = drive(spec("D31", 1), "alt", 0.04)
    assert any("D31" in r["reason"] for r in pol.log if r["kind"] == "switch")
    assert first_flip(pol.log) > first_flip(base.log)


def test_d32_extra_queries_and_probation_force():
    pol, _, b = drive(spec("D32", 1), "alt", 0.04)
    _, _, b0 = drive({"name": "off"}, "alt", 0.04)
    forced = [r for r in pol.log if r.get("source") == "force" and "D32" in r["by"]]
    assert forced and b >= b0
    n_prom = sum(1 for r in pol.log if r["kind"] == "switch" and r["proposal"].startswith("0->1"))
    assert len(forced) <= 10 * (n_prom + pol.mods[0].n_rollback + 1)


def test_d33_rolls_back_faster_than_parent():
    _, pb, _ = drive({"name": "off"}, "collapse", 0.08)
    pol, pp, _ = drive(spec("D33", 0), "collapse", 0.08)
    assert pol.mods[0].n_rollback >= 1
    assert any(r["kind"] == "override" and "D33" in r["reason"] for r in pol.log)

    def rev(path):
        return next((i for i in range(1, len(path)) if path[i - 1] == 1 and path[i] == 0), 10**9)

    assert rev(pp) <= rev(pb)


def test_d35_hurdle_grows_after_switches():
    pol, _, _ = drive(spec("D35", 1), "alt", 0.04)
    m = pol.mods[0]
    assert len(m.sw) >= 2 and m.hurdle(pol.ctx, pol.ctx.t, 0) > pol.parent.cs


def test_d37_alarm_lowers_promotion_hurdle():
    pol, _, _ = drive(spec("D37", 0), "alt", 0.04)
    m = pol.mods[0]
    assert m.n_alarm >= 1
    assert m.hurdle(CtxStub, m.until - 1, 0) < m.hurdle(CtxStub, m.until + 1, 0)


def test_d38_buys_cutoff_open_packets_only():
    pol, _, b = drive(spec("D38", 1), "weak", 0.03)
    _, _, b0 = drive({"name": "off"}, "weak", 0.03)
    forced = [r for r in pol.log if r.get("source") == "force"]
    assert forced and all(not r["closed"] and "D38" in r["by"] for r in forced)
    assert len(forced) <= 6 * 5 and b >= b0


def test_d40_band_vetoes_marginal_promotions():
    pol, _, _ = drive(spec("D40", 1), "weak", 0.03)
    assert pol.mods[0].n_veto >= 1
    assert any("D40" in r["reason"] for r in pol.log if r.get("action") == "veto")
