"""Shekhar-Ramdas RCS-Detector: T2 core identities, coverage, spending, and T3 adapter smoke tests."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for p in (SOTA, SOTA / "competitors", ROOT / "scripts/failure_atlas_v2_flq"):
    sys.path.insert(0, str(p))

from regimes import REGIMES
from shekhar_ramdas import (
    HoeffdingCS,
    RCSDetector,
    ShekharRamdasDeploymentAdapter,
    hoeffding_lambda,
    spending_alpha,
)
from simulator import (
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)


def test_lambda_schedules_and_cap():
    a = 0.9
    c = 8 * math.log(2 / a)
    for i in (1, 2):  # cap binds
        assert hoeffding_lambda(i, a, "main") == 1.0
    assert hoeffding_lambda(3, a, "appendix") == pytest.approx(math.sqrt(c / 12))
    assert hoeffding_lambda(5, a, "main") == pytest.approx(math.sqrt(c / (5 * math.log(6))))
    assert hoeffding_lambda(5, a, "appendix") == pytest.approx(math.sqrt(c / 30))
    assert hoeffding_lambda(4, a, "main") == pytest.approx(0.9961332513, abs=1e-9)
    # the cap holds for tiny i at small alpha, and i=1 (log 2) is fine
    for sched in ("main", "appendix"):
        assert all(hoeffding_lambda(i, 0.001, sched) <= 1.0 for i in range(1, 50))
    assert hoeffding_lambda(1, 0.5, "main") == 1.0
    with pytest.raises(ValueError):
        hoeffding_lambda(1, 0.5, "code")


def test_midpoint_and_half_width_hand_computed():
    a, xs = 0.9, [1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
    lams = [1.0, 1.0, 1.0, 0.9961332513, 0.8444222930, 0.7396862231]  # main schedule, values above
    cs = HoeffdingCS(a, "main")
    for n, x in enumerate(xs, 1):
        cs.update(x)
        s = sum(lams[:n])
        mid = sum(l * v for l, v in zip(lams[:n], xs[:n])) / s
        hw = (math.log(2 / a) + sum(l * l for l in lams[:n]) / 8) / s
        assert cs.mid == pytest.approx(mid, abs=1e-8)
        assert cs.half_width == pytest.approx(hw, abs=1e-8)
    # first step: weight 1 on X_1 only (no skipped observation, no pseudo-weight)
    c1 = HoeffdingCS(0.05)
    c1.update(0.7)
    assert c1.mid == pytest.approx(0.7)
    assert c1.half_width == pytest.approx(math.log(40) + 1 / 8)


def test_cs_started_at_n_includes_x_n_and_rcs_matches_scalar_cs():
    rng = np.random.default_rng(1)
    x = rng.random(40)
    for level in ("constant", "spending"):
        det = RCSDetector(0.3, level=level)
        for v in x:
            det.update(float(v))
        for m in (1, 5, 17, 40):
            a = spending_alpha(0.3, m) if level == "spending" else 0.3
            ref = HoeffdingCS(a)
            for v in x[m - 1:]:  # CS started at m uses X_m, X_{m+1}, ...
                ref.update(float(v))
            lo, hi = det.cs_interval(m)
            assert (lo, hi) == pytest.approx((ref.lo, ref.hi), abs=1e-12)
    one = RCSDetector(0.3)
    one.update(0.25)
    one.update(0.9)
    # CS started at 2 saw only X_2=0.9: its midpoint is X_2, so its interval is centred there
    ref = HoeffdingCS(0.3)
    ref.update(0.9)
    assert ref.mid == pytest.approx(0.9)
    assert one.cs_interval(2) == pytest.approx((ref.lo, ref.hi))


def test_intervals_are_nested_and_inside_unit_interval():
    cs = HoeffdingCS(0.1)
    rng = np.random.default_rng(0)
    prev = (0.0, 1.0)
    for v in rng.random(200):
        lo, hi = cs.update(float(v))
        assert prev[0] <= lo and hi <= prev[1] and 0.0 <= lo and hi <= 1.0
        prev = (lo, hi)


def test_hoeffding_cs_time_uniform_coverage_beta():
    alpha, n, reps, mu = 0.2, 300, 1500, 0.4
    rng = np.random.default_rng(7)
    miss = 0
    for _ in range(reps):
        cs = HoeffdingCS(alpha)
        for v in rng.beta(2.0, 2.0 * (1 - mu) / mu, n):
            lo, hi = cs.update(float(v))
            if not lo <= mu <= hi:
                miss += 1
                break
    rate = miss / reps
    se = math.sqrt(alpha * (1 - alpha) / reps)
    assert rate <= alpha + 3 * se, rate  # conservative CS: expect rate << alpha


def _alarm_rate(p, *, level, alpha, n, reps, theta0=(0.5, 1.0), seed=0):
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(reps):
        det = RCSDetector(alpha, theta0=theta0, level=level)
        for v in (rng.random(n) < p).astype(float):
            if det.update(float(v)):
                hits += 1
                break
    return hits / reps


def test_remark_2_5_spending_false_alarm_bound_at_boundary_null():
    # Boundary of Theta0 = [1/2, 1] (E[Y]=1/2): the hardest null. Large alpha makes it a real test.
    alpha, reps = 0.5, 1000
    r_sp = _alarm_rate(0.5, level="spending", alpha=alpha, n=120, reps=reps)
    se = math.sqrt(alpha * (1 - alpha) / reps)
    assert r_sp <= alpha + 3 * se
    # also at the contract alpha
    assert _alarm_rate(0.5, level="spending", alpha=0.05, n=200, reps=300, seed=1) <= 0.05 + 3 * math.sqrt(0.05 * 0.95 / 300)
    # constant-level CSs are narrower, so alarms are a pathwise superset of spending alarms
    r_c = _alarm_rate(0.5, level="constant", alpha=alpha, n=120, reps=reps)
    assert r_c >= r_sp


def test_detection_under_large_change_and_no_detection_when_inside_theta0():
    rng = np.random.default_rng(3)
    det = RCSDetector(0.05, theta0=(0.5, 1.0), level="spending")
    stop = next((i for i, v in enumerate((rng.random(300) < 0.2).astype(float), 1) if det.update(float(v))), None)
    assert stop is not None and stop < 100 and det.tau == stop
    det2 = RCSDetector(0.05, theta0=(0.5, 1.0), level="spending")
    assert not any(det2.update(float(v)) for v in (rng.random(200) < 0.8).astype(float))
    # non-partitioned (Problem 1.1): a mean shift is detected with no knowledge of Theta0
    det3 = RCSDetector(0.05, level="spending")
    x = np.r_[(rng.random(150) < 0.2), (rng.random(300) < 0.8)].astype(float)
    t = next((i for i, v in enumerate(x, 1) if det3.update(float(v))), None)
    assert t is not None and t > 150


def test_lorden_form_equivalence_for_singleton_theta0():
    # Proposition 3.1: for Theta0={theta0} RCS stops iff some CS (started at m) excludes theta0.
    rng = np.random.default_rng(11)
    th, alpha = 0.5, 0.3
    for _ in range(40):
        x = (rng.random(80) < rng.choice([0.5, 0.35])).astype(float)
        det = RCSDetector(alpha, theta0=(th, th))
        tau = next((i for i, v in enumerate(x, 1) if det.update(float(v))), None)
        css = [HoeffdingCS(alpha) for _ in x]
        lorden = None
        for n in range(1, len(x) + 1):
            for m in range(1, n + 1):
                css[m - 1].update(float(x[n - 1]))
            if any(not c.lo <= th <= c.hi for c in css[:n]):
                lorden = n
                break
        assert tau == lorden


def test_window_stops_no_earlier_than_full_and_state_roundtrip():
    rng = np.random.default_rng(5)
    x = (rng.random(150) < 0.25).astype(float)
    full, win = RCSDetector(0.05, theta0=(0.5, 1.0)), RCSDetector(0.05, theta0=(0.5, 1.0), window=10)
    for v in x:
        full.update(float(v))
        win.update(float(v))
    assert full.tau is not None and (win.tau is None or win.tau >= full.tau)
    a, b = RCSDetector(0.05, theta0=(0.5, 1.0), level="spending"), RCSDetector(0.05, theta0=(0.5, 1.0), level="spending")
    for v in x[:50]:
        a.update(float(v))
    b.load_state_dict(a.state_dict())
    for v in x[50:80]:
        assert a.update(float(v)) == b.update(float(v))
    assert a.interval == b.interval


# ----------------------------------------------------------------------------- adapter
def _stream(losses, seed):
    r = np.random.default_rng(seed)
    labels = r.integers(0, 2, losses.shape[0])
    return labels[:, None].astype(int) ^ losses.astype(int), labels


def _run(regime, seed, *, T=2000, budget=200, delay=100, alpha=0.05, losses=None):
    reg = REGIMES[regime]
    if losses is None:
        losses = reg.sample(np.random.default_rng(1000 + seed), T)
    preds, labels = _stream(losses, 500 + seed)
    pol = ShekharRamdasDeploymentAdapter(T, budget, alpha, rng=policy_rng(seed, 0, "sr"))
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                      label_price=0.05, switch_cost=5.0)
    return pol, res, losses


@pytest.mark.parametrize("regime", ["F0_null", "F3_reversal_800"])
def test_adapter_budget_delay_and_determinism(regime):
    for seed in range(3):
        _, res, _ = _run(regime, seed)
        assert check_budget_feasible(res, 200) == [] and check_no_future_access(res, 100) == []
        assert res.refused_requests == 0
        _, res2, _ = _run(regime, seed)
        assert [r["deployed_model"] for r in res.records] == [r["deployed_model"] for r in res2.records]
        assert [r["requested"] for r in res.records] == [r["requested"] for r in res2.records]


def test_adapter_decisions_do_not_depend_on_future_events():
    T, t0 = 1200, 700
    base = REGIMES["F3_reversal_800"].sample(np.random.default_rng(42), T)
    other = base.copy()
    other[t0:] = REGIMES["F0_worse"].sample(np.random.default_rng(43), T)[t0:]
    pa, pb = _stream(base, 9), _stream(other, 9)
    # identical label draws; predictions equal on [0, t0) because the loss streams agree there
    assert np.array_equal(pa[0][:t0], pb[0][:t0]) and np.array_equal(pa[1], pb[1])
    runs = []
    for preds, labels in (pa, pb):
        pol = ShekharRamdasDeploymentAdapter(T, 200, 0.05, rng=policy_rng(3, 0, "sr"))
        runs.append(run_episode(pol, model_predictions=preds, labels=labels, delay=100, budget=200,
                                label_price=0.05, switch_cost=5.0))
    # deployment at t0 uses labels released by t0 (events < t0 only); the request at t0 reads event t0
    for key, upto in (("deployed_model", t0 + 1), ("requested", t0)):
        assert [r[key] for r in runs[0].records[:upto]] == [r[key] for r in runs[1].records[:upto]]
    assert runs[0].deployment_switches != runs[1].deployment_switches  # the streams do differ later


def test_adapter_state_dict_roundtrip():
    T = 600
    losses = REGIMES["F0_better"].sample(np.random.default_rng(2), T)
    preds, labels = _stream(losses, 2)
    pol = ShekharRamdasDeploymentAdapter(T, 200, 0.05, rng=policy_rng(1, 0, "sr"))
    run_episode(pol, model_predictions=preds, labels=labels, delay=50, budget=200, label_price=0.05, switch_cost=5.0)
    clone = ShekharRamdasDeploymentAdapter(T, 200, 0.05, rng=policy_rng(9, 9, "sr"))
    clone.load_state_dict(pol.state_dict())
    assert clone.state_dict()["rcs"] == pol.state_dict()["rcs"]
    assert (clone.deployed, clone.phase) == (pol.deployed, pol.phase)


def test_adapter_promotes_on_clear_advantage_and_rolls_back_on_reversal():
    # Strong, easy regimes only: a qualitative smoke check, not evidence of performance.
    T, delay = 2000, 100
    promoted = rolled = 0
    for seed in range(5):
        losses = np.zeros((T, 2), dtype=np.int8)
        r = np.random.default_rng(seed)
        on = r.random(T) < 0.5
        good = np.where(np.arange(T) < 800, r.random(T) < 0.95, r.random(T) < 0.05)
        losses[:, 0] = np.where(on, good, 0)
        losses[:, 1] = np.where(on, ~good, 0)
        pol, _, _ = _run("F0_null", seed, T=T, delay=delay, losses=losses)
        promoted += pol.promoted_at_label > 0
        rolled += pol.rolled_back_at_label > 0
    assert promoted >= 4 and rolled >= 3


# ------------------------------------------------------------------ stop_rule (ShiftLab deviation)
def _drift_rate(rule, reps=300, alpha=0.05, seed=0):
    # Composite non-stationary null: Y-mean 1.0 for 60 labels then 0.5; every mean lies in Theta0=[.5,1].
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(reps):
        det = RCSDetector(alpha, theta0=(0.5, 1.0), level="spending", stop_rule=rule)
        x = np.r_[rng.random(60) < 1.0, rng.random(200) < 0.5].astype(float)
        hits += any(det.update(float(v)) for v in x)
    return hits / reps


def test_joint_rule_false_alarms_under_drift_within_theta0_but_any_excludes_does_not():
    alpha, reps = 0.05, 300
    se = math.sqrt(alpha * (1 - alpha) / reps)
    assert _drift_rate("joint", reps) > 0.5  # clearly elevated (observed 1.0)
    assert _drift_rate("any_excludes", reps) <= alpha + 3 * se


@pytest.mark.parametrize("alpha,n,reps", [(0.5, 120, 600), (0.05, 200, 300)])
def test_both_stop_rules_control_false_alarms_on_iid_boundary_null(alpha, n, reps):
    se = math.sqrt(alpha * (1 - alpha) / reps)
    for rule in ("joint", "any_excludes"):
        rng = np.random.default_rng(21)
        hits = 0
        for _ in range(reps):
            det = RCSDetector(alpha, theta0=(0.5, 1.0), level="spending", stop_rule=rule)
            hits += any(det.update(float(v)) for v in (rng.random(n) < 0.5))
        assert hits / reps <= alpha + 3 * se, rule


def test_any_excludes_detects_large_change_and_implies_joint_and_matches_lorden():
    rng = np.random.default_rng(3)
    x = (rng.random(300) < 0.2).astype(float)
    taus = {}
    for rule in ("joint", "any_excludes"):
        det = RCSDetector(0.05, theta0=(0.5, 1.0), level="spending", stop_rule=rule)
        taus[rule] = next((i for i, v in enumerate(x, 1) if det.update(float(v))), None)
    assert taus["any_excludes"] is not None and taus["any_excludes"] < 100
    assert taus["joint"] <= taus["any_excludes"]  # every any_excludes alarm is a joint alarm
    # singleton Theta0: the rules coincide (Proposition 3.1 / Lorden form)
    for seed in range(20):
        y = (np.random.default_rng(seed).random(80) < 0.4).astype(float)
        t = []
        for rule in ("joint", "any_excludes"):
            det = RCSDetector(0.3, theta0=(0.5, 0.5), stop_rule=rule)
            t.append(next((i for i, v in enumerate(y, 1) if det.update(float(v))), None))
        assert t[0] is not None  # joint stops by the first exclusion
        assert t[1] is None or t[1] >= t[0]  # instantaneous check can only stop later or equal


def test_adapter_stop_rule_option():
    T = 600
    losses = REGIMES["F0_better"].sample(np.random.default_rng(2), T)
    preds, labels = _stream(losses, 2)
    pol = ShekharRamdasDeploymentAdapter(T, 200, 0.05, rng=policy_rng(1, 0, "sr"), stop_rule="any_excludes",
                                         name="shekhar_ramdas_rcs_t3_anyexcl")
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=50, budget=200, label_price=0.05,
                      switch_cost=5.0)
    assert pol.rcs.stop_rule == "any_excludes" and check_budget_feasible(res, 200) == []
    with pytest.raises(ValueError):
        RCSDetector(0.05, stop_rule="nope")
