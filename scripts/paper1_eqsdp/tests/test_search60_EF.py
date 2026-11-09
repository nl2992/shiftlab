# ruff: noqa: RUF012
"""Tests for search60 families E (E41-E50) and F (F51-F60)."""

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
for _p in (HERE, HERE / "search60", Path(__file__).resolve().parent):
    sys.path.insert(0, str(_p))
import compositor as comp
import modules_E as ME
import modules_F as MF
from test_search60_compositor import build, episode, run, spec, toy_losses  # noqa: F401

EF = [f"E{i}" for i in range(41, 51)] + [f"F{i}" for i in range(51, 61)]


@comp.register
class ZT1(comp.Module):
    """Test-only add-on: forces the incumbent during t in [300, 500) (the parent has promoted by then) (so E45 / F58 have a deviation)."""

    ID = "ZT1"
    FAMILY = "A"
    DEFAULTS: dict = {}
    SETTINGS = [{}, {}]

    def override_deploy(self, ctx):
        return 0 if 300 <= ctx.t < 500 else None


# parameter variants added to the two catalogue SETTINGS for the non-inertness test
EXTRA = {
    "E43": [{"risk_budget": 0.01}],
    "E44": [{"priors": "weak", "envelope": "mean"}],
    "E46": [{"shrink": 0.0, "weight_cap": 1000.0}],
    "E47": [{"threshold": 1.0, "reset": "hard"}],
    "E49": [{"age": 10, "confidence": 0.8, "few": 4}],
    "E50": [{"window": 6, "upper_q": 0.9}],
    "F52": [{"start": 1000}],
    "F56": [{"alert": 1, "burst": 5}],
    "F57": [{"fast_lambda": 0.8, "duration": 200}],
}
ADDON = {"E45": ["ZT1"], "F58": ["ZT1"]}


def mspec(mid, st=None, params=None, extra_ids=()):
    m = {"id": mid}
    if st is not None:
        m["setting"] = st
    if params:
        m["params"] = params
    mods = [m] + [{"id": i} for i in extra_ids]
    return {"name": f"ef_{mid}_{st}_{abs(hash(str(params))) % 10**6}", "modules": mods}


@pytest.mark.parametrize("mid", EF)
def test_registered_and_settings(mid):
    reg = comp.load_modules()
    cls = reg[mid]
    assert cls.FAMILY == mid[0] and len(cls.SETTINGS) == 2
    assert set(cls.SETTINGS[0]) <= set(cls.DEFAULTS) and set(cls.SETTINGS[1]) <= set(cls.DEFAULTS)


@pytest.mark.parametrize("mid", EF)
def test_constructs_and_runs(mid):
    for st in (0, 1):
        s = mspec(mid, st)
        r = run([s])[s["name"]]
        assert r["labels"] <= 200 and np.isfinite(r["net"])


@pytest.mark.parametrize("mid", EF)
def test_budget_delay_causality(mid):
    from simulator import check_no_future_access

    for budget in (12, 60, 200):
        s = {**spec(mid, 1), "name": f"efb_{mid}_{budget}"}
        pol = build(s)
        res, _ = episode(pol, budget=budget, seed=2)
        assert res.requested_labels <= budget
        assert not check_no_future_access(res, 100)
        assert all(r["event_id"] + 100 < 2000 for r in res.records if r["requested"])
    # guarded proxies: reading label/extra/context/query_probability raises
    pol = build({**spec(mid, 0), "name": f"efg_{mid}"})
    episode(pol, wrap=True, seed=3)


@pytest.mark.parametrize("mid", ["E41", "E47", "F54", "F56", "F59", "F60"])
def test_determinism(mid):
    s = mspec(mid, 1)
    a, b = run([s], seed=5)[s["name"]], run([s], seed=5)[s["name"]]
    assert (a["net"], a["labels"], a["switches"]) == (b["net"], b["labels"], b["switches"])


@pytest.mark.parametrize("mid", [m for m in EF if m != "E46"])
def test_not_inert(mid):
    """The module changes labels, net or switches against the all-off parent on some constructed
    stream / setting / parameter variant (E45 and F58 are paired with a deviating add-on)."""
    variants = [mspec(mid, 0, None, ADDON.get(mid, ())), mspec(mid, 1, None, ADDON.get(mid, ()))]
    variants += [mspec(mid, None, p, ADDON.get(mid, ())) for p in EXTRA.get(mid, [])]
    base_ids = ADDON.get(mid, ())
    off = {"name": f"ef_off_{mid}", "modules": [{"id": i} for i in base_ids]}
    changed = False
    for seed in (1, 2, 3):
        res = run([off, *variants], seed=seed)
        o = res[off["name"]]
        for v in variants:
            r = res[v["name"]]
            changed |= (r["labels"], r["switches"], round(r["net"], 6)) != (
                o["labels"], o["switches"], round(o["net"], 6))  # fmt: skip
        if changed:
            break
    assert changed, f"{mid} is inert on the toy streams"


def test_e45_alone_is_inert_and_fallback_works():
    off = {"name": "ef45_off"}
    alone = {"name": "ef45_alone", "modules": [{"id": "E45", "setting": 0}]}
    paired = {"name": "ef45_pair", "modules": [{"id": "E45", "setting": 0}, {"id": "ZT1"}]}
    zt = {"name": "ef45_zt", "modules": [{"id": "ZT1"}]}
    r = run([off, alone, paired, zt], seed=2)
    f = lambda x: (x["labels"], x["switches"], round(x["net"], 6))
    assert f(r["ef45_off"]) == f(r["ef45_alone"])
    assert f(r["ef45_pair"]) != f(r["ef45_zt"])


def test_post_mixture_widens_when_stale():
    class FB:
        def __init__(self, d, tq):
            self.d, self.t_requested = d, tq

    po = ME.Post(0.002)
    for i in range(40):
        po.add(FB(1, i * 5))
    a0, b0 = po.eff(200)
    a1, b1 = po.eff(1500)  # 1300 events without a fresh label -> reset mass grows
    v = lambda a, b: a * b / ((a + b) ** 2 * (a + b + 1))
    assert v(a1, b1) > v(a0, b0)
    st = ME.Post(0.0)
    for i in range(40):
        st.add(FB(1, i * 5))
    a2, b2 = st.eff(1500)
    assert v(a2, b2) < v(a1, b1)  # a stationary posterior never widens


def test_voi_properties():
    v = ME.voi(7.0, 5.0, 0, 1, 0, 0.3, 150.0, 5.0)
    assert v > 0
    assert (
        ME.voi(70.0, 50.0, 0, 1, 0, 0.3, 150.0, 5.0) < v
    )  # same mean, tight posterior: less to learn
    assert ME.voi(7.0, 5.0, 0, 3, 0, 0.3, 150.0, 5.0) >= v  # a bundle is worth at least one label
    assert ME.voi(7.0, 5.0, 2, 1, 0, 0.3, 150.0, 5.0) >= 0  # pending labels are integrated out
    assert ME.voi(7.0, 5.0, 0, 1, 0, 0.3, 0.0, 5.0) == 0.0


def test_f59_params_frozen_and_loadable():
    par = MF.load_f59()
    assert par["ref"] > 0 and "logistic" in par
    x = [0.5, 0.5, 0.1, 0.3, 0.5, 0.2, -0.2, 0.0, 0.2, 0.3]
    for model, depth in (("tree", 2), ("tree", 3), ("logistic", 2)):
        s = MF.F59(
            {"model": model, "depth": depth}, comp.Ctx(None, 2000, 200, 100, 1100), None
        )._score(x)
        assert 0.0 <= s <= 1.0
    if "episodes_used" in par:  # trained on development (even) episodes only
        assert all(ep % 2 == 0 for _, ep in par["episodes_used"])


def test_e46_ipw_veto_unit():
    """E46 acts only at a switch proposal; on a clean toy stream the parent's first promotion is far
    above the threshold, so the module is checked at unit level: a heavily down-weighted evidence
    stream makes the corrected payback fail and the proposal is vetoed."""
    pol = build({"name": "ef46u", "modules": [{"id": "E46", "setting": 1}]})
    m, c = pol.mods[0], pol.ctx
    c.parent.k, c.parent.n, c.parent.t = 8.0, 10.0, 200
    m.sw, m.sk = 10.0, 5.0  # IPW says p = .5 although the plain rate is .8
    prop = comp.Proposal(200, 0, 1)
    m.on_switch_proposal(c, prop)
    assert not prop.allow
    m.sw, m.sk = 10.0, 8.0  # IPW agrees with the plain rate
    prop = comp.Proposal(200, 0, 1)
    m.on_switch_proposal(c, prop)
    assert prop.allow
