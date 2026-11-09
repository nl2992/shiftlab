import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import stage2_policies as sp2
import stage5_policies as sp5
import trace_run as tr

SPECS = {
    "t_r1": {"kind": "r1", "f": 0.2, "gap": 100, "cutoff": 1100},
    "t_cal": {"kind": "cal", "m": 30, "cutoff": 1100},
    "t_r2": {"kind": "r2", "mode": "evsi", "hz": 5e-4, "lam0": 0.05, "cutoff": 1100},
    "t_r2q": {"kind": "r2", "mode": "evsi", "hz": 5e-4, "rule": "quantile"},
    "t_r3": {"kind": "r2", "mode": "tail", "hz": 2e-3, "tau": 2.0},
    "t_tail": {"kind": "r2", "mode": "tail_only", "hz": 2e-3, "tau": 2.0},
    "t_ent": {"kind": "r2", "mode": "entropy", "hz": 5e-4, "theta": 2.5},
}


def toy_losses(seed=0, T=2000, shift=800):
    rng = np.random.default_rng(seed)
    l0 = (rng.random(T) < 0.35).astype(np.int8)
    p1 = np.where(np.arange(T) < shift, 0.20, 0.50)
    l1 = (rng.random(T) < p1).astype(np.int8)
    return np.stack([l0, l1], axis=1)


def run(names, seed=0, budget=200, delay=100):
    for n, s in SPECS.items():
        sp2.DYN[n] = sp5.make_factory(s, n)
    rows = tr.run_policies(names, toy_losses(seed), delay, 0, seed, 77, "toy", budget)
    return {r["policy"]: r for r in rows}


@pytest.mark.parametrize("budget", [12, 60])
def test_budget_respected(budget):
    for r in run(list(SPECS), seed=1, budget=budget).values():
        assert r["labels"] <= budget, r["policy"]


def test_deterministic():
    a, b = run(list(SPECS), seed=3), run(list(SPECS), seed=3)
    for k in SPECS:
        assert a[k]["net"] == b[k]["net"] and a[k]["labels"] == b[k]["labels"], k


def test_cutoff_inert_r1_equals_stage2_cutoff_reference():
    sp2.DYN["t_r1_off"] = sp5.make_factory({"kind": "r1", "rho0": 0.0, "cutoff": 1100}, "t_r1_off")
    for seed in (1, 2):
        rows = tr.run_policies(
            ["t_r1_off", "s2armr_H1100"], toy_losses(seed), 100, 0, seed, 77, "toy", 200
        )
        r = {x["policy"]: x for x in rows}
        assert r["t_r1_off"]["net"] == r["s2armr_H1100"]["net"]


def test_gap_rule_and_cutoff_in_trace():
    """Purchases never leave a gap > G before the cutoff while disagreements exist."""
    import c4_pilot
    from suite import build_suite, run_episode, stream_from_losses

    sp2.DYN["t_gap"] = sp5.make_factory(
        {"kind": "r1", "f": 0.0, "gap": 80, "cutoff": 1100, "rho0": 5.0}, "t_gap"
    )
    reg = tr.registry()
    ls = toy_losses(2)
    rng = np.random.default_rng(0)
    preds, labels = stream_from_losses(ls, rng)
    cfg = c4_pilot.CFG
    (pol,) = build_suite(2000, 200, 5.0, 0.05, cfg["alpha"], 100, 1, 2, names=["t_gap"], extra=reg)
    res = run_episode(
        pol, model_predictions=preds, labels=labels, delay=100, budget=200,
        label_price=0.05, switch_cost=5.0, trace=True,
    )  # fmt: skip
    buys = [r["event_id"] for r in res.records if r["requested"]]
    assert buys and max(buys) + 100 <= 2000 - 1100
    dis = np.flatnonzero(preds[:, 0] != preds[:, 1])
    last = 0
    for t in dis:
        if t + 100 > 2000 - 1100:
            break
        if t in buys:
            last = t
        else:
            assert t - last < 80 or t == last, (t, last)  # a disagreement past the gap is bought
    assert max(np.diff([0, *buys])) <= 80 + 40  # next disagreement after the gap, rate ~.3


def test_calendar_label_count():
    r = run(["t_cal"], seed=1)["t_cal"]
    assert 20 <= r["labels"] <= 30


class Guard:
    def __init__(self, obj, allowed):
        object.__setattr__(self, "o", obj)
        object.__setattr__(self, "a", allowed)

    def __getattr__(self, k):
        if k not in object.__getattribute__(self, "a"):
            raise AssertionError(f"evaluator field read: {k}")
        return getattr(object.__getattribute__(self, "o"), k)


class Wrapped:
    """Passes only whitelisted event / feedback fields to the policy."""

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


@pytest.mark.parametrize("name", list(SPECS))
def test_no_evaluator_field_read(name):
    import c4_pilot
    from suite import build_suite, run_episode, stream_from_losses

    sp2.DYN[name] = sp5.make_factory(SPECS[name], name)
    reg = tr.registry()
    ls = toy_losses(4)
    preds, labels = stream_from_losses(ls, np.random.default_rng(1))
    cfg = c4_pilot.CFG
    (pol,) = build_suite(2000, 200, 5.0, 0.05, cfg["alpha"], 100, 1, 2, names=[name], extra=reg)
    run_episode(
        Wrapped(pol), model_predictions=preds, labels=labels, delay=100, budget=200,
        label_price=0.05, switch_cost=5.0, trace=False,
    )  # fmt: skip


def test_preposterior_properties():
    f = sp5.HazardFilter(5e-4)
    # a locked-in posterior (p near .95, many labels): no pending, EVSI ~ 0, CVaR ~ 0
    w = np.exp(60 * np.log(f.p) + 3 * np.log1p(-f.p))
    w /= w.sum()
    ev, cv = sp5.preposterior(w, f, 0, 1, 0.3, 5.0, 0.2, 1500)
    assert abs(ev) < 1e-6 and cv < 1e-6
    # an undecided prior has positive value; Bayes mean rule => EVSI >= 0
    for pend in (0, 3, 10):
        ev, cv = sp5.preposterior(f.prior, f, pend, 0, 0.3, 5.0, 0.2, 1500)
        assert ev >= -1e-9 and cv >= ev - 1e-9
    assert sp5.preposterior(f.prior, f, 0, 0, 0.3, 5.0, 0.2, 1500)[0] > 0.05


def test_filter_hazard_restores_prior_mass():
    f = sp5.HazardFilter(2e-3)
    for _ in range(40):
        f.update(True, 10)
    w_now, w_late = f.at(10), f.at(2000)
    assert w_late[: len(w_late) // 2].sum() > w_now[: len(w_now) // 2].sum()
    assert abs(w_late.sum() - 1) < 1e-12


def test_evsi_k1_matches_preposterior_and_bundle_gains():
    import stage5_policies as s

    f = s.HazardFilter(1e-4)
    for z in (1, 0, 1, 0, 0):
        f.update(z, 100)
    w = f.at(120)
    ev1 = s.preposterior(w, f, 2, 0, 0.3, 5.0, 0.5, 1500, "mean")[0]
    assert abs(ev1 - s.evsi_k(w, f, 2, 1, 0, 0.3, 5.0, 0.5, 1500, "mean")) < 1e-9
    assert s.evsi_k(w, f, 2, 2, 0, 0.3, 5.0, 0.5, 1500, "mean") >= ev1
