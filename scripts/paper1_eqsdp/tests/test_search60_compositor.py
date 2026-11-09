import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
for _p in (HERE, HERE / "search60"):
    sys.path.insert(0, str(_p))
import compositor as comp
import stage2_policies as sp2
import trace_run as tr

AB = [f"A{i:02d}" for i in range(1, 11)] + [f"B{i}" for i in range(11, 21)]
PARENT_NAMES = ["s2armr_H1100", "s2wald_l0.98_g0.3_H1100"]


def toy_losses(seed=0, T=2000, shift=800):
    rng = np.random.default_rng(seed)
    l0 = (rng.random(T) < 0.35).astype(np.int8)
    p1 = np.where(np.arange(T) < shift, 0.20, 0.50)
    l1 = (rng.random(T) < p1).astype(np.int8)
    return np.stack([l0, l1], axis=1)


def spec(mid, setting=1, **kw):
    return {"name": f"t_{mid}_{setting}", "modules": [{"id": mid, "setting": setting}], **kw}


def run(specs, seed=1, budget=200, delay=100, ep=0):
    comp.register_specs(specs)
    names = [comp.config_id(s) for s in specs]
    rows = tr.run_policies(names, toy_losses(seed), delay, ep, seed, 77, "toy", budget)
    return {r["policy"]: r for r in rows}


def build(spec_, delay=100, log=1, seed=1):
    """Build a ComposedPolicy through the real suite constructor."""
    import c4_pilot
    from suite import build_suite

    s = {**spec_, "log": log}
    comp.register_specs([s])
    (pol,) = build_suite(2000, 200, 5.0, 0.05, c4_pilot.CFG["alpha"], delay, seed, 2,
                         names=[comp.config_id(s)], extra=tr.registry())  # fmt: skip
    return pol


def episode(pol, seed=1, delay=100, budget=200, wrap=False):
    from suite import run_episode, stream_from_losses

    preds, labels = stream_from_losses(toy_losses(seed), np.random.default_rng(seed))
    p = Wrapped(pol) if wrap else pol
    res = run_episode(p, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                      label_price=0.05, switch_cost=5.0, trace=True)  # fmt: skip
    return res, preds


class Guard:
    def __init__(self, obj, allowed):
        object.__setattr__(self, "o", obj)
        object.__setattr__(self, "a", allowed)

    def __getattr__(self, k):
        if k not in object.__getattribute__(self, "a"):
            raise AssertionError(f"evaluator field read: {k}")
        return getattr(object.__getattribute__(self, "o"), k)


class Wrapped:
    def __init__(self, pol):
        self.p, self.name = pol, pol.name

    def predict(self, event):
        return self.p.predict(Guard(event, {"event_id", "t", "horizon", "model_predictions"}))

    def request_labels(self, event, rem):
        return self.p.request_labels(
            Guard(event, {"event_id", "t", "horizon", "model_predictions"}), rem
        )

    def observe(self, fbs):
        ok = {"event_id", "t_requested", "t_released", "model_losses"}
        self.p.observe([Guard(f, ok) for f in fbs])

    def decision_state(self):
        return self.p.decision_state()


# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("mid", AB)
def test_module_constructs_and_runs(mid):
    for st in (0, 1):
        r = run([spec(mid, st)])[f"t_{mid}_{st}"]
        assert r["labels"] <= 200 and np.isfinite(r["net"])


@pytest.mark.parametrize("mid", AB)
def test_budget_and_delay(mid):
    from simulator import check_no_future_access

    for budget in (12, 60):
        pol = build(spec(mid, 1))
        res, _ = episode(pol, budget=budget, seed=2)
        assert res.requested_labels <= budget
        assert not check_no_future_access(res, 100)
        buys = [r["event_id"] for r in res.records if r["requested"]]
        assert all(t + 100 < 2000 for t in buys)  # only releasable labels are bought


@pytest.mark.parametrize("mid", AB)
def test_no_evaluator_field_read(mid):
    for st, seed in ((1, 3), (0, 4)):
        episode(build(spec(mid, st)), wrap=True, seed=seed)


def test_cutoff_exception_logged():
    """Sentinels buy after the cutoff and every such purchase is a logged cutoff exception."""
    pol = build({"name": "t_sent", "modules": [{"id": "A01", "setting": 1}, {"id": "A10"}]})
    res, _ = episode(pol, seed=1)
    close = 2000 - 1100 - 100 + 1
    late = [r["event_id"] for r in res.records if r["requested"] and r["event_id"] >= close]
    assert late
    exc = [r for r in pol.log if r.get("cutoff_exception")]
    assert sorted(r["t"] for r in exc) == late
    assert all(r["closed"] and r["by"] for r in exc)
    # the parent alone never buys after the cutoff
    base = build({"name": "t_base"})
    res0, _ = episode(base, seed=1)
    assert not [r for r in res0.records if r["requested"] and r["event_id"] >= close]


def test_reserve_respected_and_logged():
    """B13 holds labels: before the window a purchase must leave the unused reserve."""
    pol = build({"name": "t_b13", "modules": [{"id": "B13", "params": {"reserve": 0.5}}]})
    res, _ = episode(pol, budget=80, seed=1)
    hold = round(0.5 * 200)  # reserve is a fraction of the contract B=200 (ctx.B)
    buys = [r for r in pol.log if r.get("action") == "buy" and r["t"] <= 800]
    assert all(r["remaining"] - 1 >= min(hold, r["remaining"] - 1) for r in buys)
    assert res.requested_labels <= 80
    # with B=200 and a 50% reserve the cap really binds
    pol2 = build({"name": "t_b13b", "modules": [{"id": "B13", "params": {"reserve": 0.9}}]})
    episode(pol2, budget=200, seed=1)
    assert any(r.get("reason") == "cap:reserve" for r in pol2.log)


def test_log_fields():
    pol = build({"name": "t_log", "modules": [{"id": "B16", "setting": 1}]})
    episode(pol)
    acq = [r for r in pol.log if r["kind"] == "acquire"]
    need = {"t", "module_ids", "p_parent", "p_final", "due", "remaining", "evidence", "action",
            "reason"}  # fmt: skip
    assert acq and all(need <= set(r) for r in acq)
    assert any(r["kind"] == "switch" and r["action"] == "allow" for r in pol.log)


@pytest.mark.parametrize("mid", ["A03", "B12", "B20"])
def test_randomized_repeatability(mid):
    a = run([spec(mid, 1)], seed=5)[f"t_{mid}_1"]
    b = run([spec(mid, 1)], seed=5)[f"t_{mid}_1"]
    assert (a["net"], a["labels"], a["switches"]) == (b["net"], b["labels"], b["switches"])


def test_toy_all_off_equals_parents():
    specs = [{"name": "off_e"},
             {"name": "off_w", "parent": {"kind": "wald", "lam": 0.98, "gamma": 0.3}},
             {"name": "off_w2", "parent": {"kind": "wald", "lam": 0.97, "gamma": 0.2}}]  # fmt: skip
    comp.register_specs(specs)
    for seed in (1, 2, 3):
        rows = tr.run_policies(
            ["off_e", "off_w", "off_w2", *PARENT_NAMES, "s2wald_l0.97_g0.2_H1100"],
            toy_losses(seed), 100, 0, seed, 77, "toy", 200)  # fmt: skip
        r = {x["policy"]: x for x in rows}
        for a, b in (("off_e", PARENT_NAMES[0]), ("off_w", PARENT_NAMES[1]),
                     ("off_w2", "s2wald_l0.97_g0.2_H1100")):  # fmt: skip
            assert (r[a]["net"], r[a]["loss"], r[a]["labels"], r[a]["switches"]) == (
                r[b]["net"], r[b]["loss"], r[b]["labels"], r[b]["switches"])  # fmt: skip


def test_all_off_bitwise_nine_datasets():
    """3 episodes x 2 seeds x 9 datasets: net, loss, labels, switches identical to the parents."""
    specs = [{"name": "off_e"},
             {"name": "off_w", "parent": {"kind": "wald", "lam": 0.98, "gamma": 0.3}}]  # fmt: skip
    comp.register_specs(specs)
    n_cmp = 0
    for ds, (p, delay, sb) in tr.sealed_paths().items():
        z = np.load(p)
        n = z["l0"].shape[0]
        for ep in sorted({1, n // 2, n - 2}):
            losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
            for seed in (0, 1):
                rows = tr.run_policies(["off_e", "off_w", *PARENT_NAMES], losses, delay, ep, seed,
                                       sb, ds, 200)  # fmt: skip
                r = {x["policy"]: x for x in rows}
                for a, b in (("off_e", PARENT_NAMES[0]), ("off_w", PARENT_NAMES[1])):
                    for f in ("net", "loss", "labels", "switches", "first_deploy"):
                        assert r[a][f] == r[b][f], (ds, ep, seed, a, f)
                    n_cmp += 1
    assert n_cmp >= 9 * 2 * 2 * 2  # >= 2 distinct episodes x 2 seeds x 2 parents per dataset


def test_unsupported_and_missing():
    with pytest.raises(comp.UnsupportedCombo):
        comp.validate_spec({"modules": ["C21", "C24"]})
    with pytest.raises(comp.UnsupportedCombo):
        comp.validate_spec({"modules": ["A01", "A01"]})
    with pytest.raises(comp.NotImplementedModule):
        comp.validate_spec({"modules": ["Z99"]})
    assert comp.UnsupportedCombo.status == "UNSUPPORTED_COMBO"


def test_wald_parent_with_module_runs():
    r = run([spec("A01", 1, parent={"kind": "wald", "lam": 0.98, "gamma": 0.3})])
    assert r["t_A01_1"]["labels"] > 0


def test_registry_leaves_parent_names_intact():
    comp.register_specs([{"name": "t_off"}])
    reg = tr.registry()
    assert "s2armr_H1100" in reg and "t_off" in reg
    assert sp2.DYN["t_off"] is not None
