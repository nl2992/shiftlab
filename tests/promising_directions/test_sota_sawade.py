"""Tests for the Sawade, Landwehr & Scheffer (NeurIPS 2012) comparator."""

import itertools
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))

from competitors.sawade import (
    CalibratedPosterior,
    SawadeActiveNeq,
    SawadeCalibrated,
    derivation4_weight,
    introspective_delta,
    propensity,
    sampling_distribution,
    solve_scale,
)
from simulator import (
    Event,
    ReleasedFeedback,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

DELAY = 3


def _stream(T=1500, seed=0, acc=(0.78, 0.72), signal=1.5, d=2):
    """Context-dependent binary labels; two hard classifiers with given accuracies.

    Synthetic: the repository has no real-data files in this worktree, so the calibrated-vs-
    active!= measurement below is on this generator and says nothing about rialto/ldpa."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(T, d))
    y = (rng.random(T) < 1 / (1 + np.exp(-signal * x[:, 0]))).astype(int)
    preds = np.stack([np.where(rng.random(T) < a, y, 1 - y) for a in acc], axis=1)
    return preds, y, x


def _dev_and_locked(seed=0, **kw):
    preds, y, x = _stream(T=3000, seed=seed, **kw)
    return (preds[:1500], y[:1500], x[:1500]), (preds[1500:], y[1500:], x[1500:])


def _make(kind, dev, T, B, seed=0, **kw):
    dp, dy, dx = dev
    rng = policy_rng(seed, 0, f"sawade_{kind}")
    if kind == "neq":
        return SawadeActiveNeq(T, B, rng=rng, delay=DELAY, dev_preds=dp, **kw)
    post = CalibratedPosterior.fit(dx, dp, dy)
    return SawadeCalibrated(
        T, B, rng=rng, delay=DELAY, dev_preds=dp, dev_context=dx, posterior=post, **kw
    )


# ----------------------------------------------------------------- Derivation 4, by hand
def test_derivation4_hand_computed():
    # pool of 4: (f1,f2) = (1,0), (0,1), (1,1), (0,0); p(y=1|x) = .8, .3, .5, .9
    f1, f2 = np.array([1, 0, 1, 0]), np.array([0, 1, 1, 0])
    p = np.array([0.8, 0.3, 0.5, 0.9])
    # E l1 - E l2: item1 (1-.8) - .8 = -.6 ; item2 .3 - (1-.3) = -.4 ; agreement 0
    delta = introspective_delta(f1, f2, p)
    assert np.isclose(delta, (-0.6 - 0.4) / 4) and np.isclose(delta, -0.25)
    w = derivation4_weight(f1, f2, p, delta)
    # item1, f1>f2: sqrt(1 - 2*(-.25)*(1-1.6) + .0625) = sqrt(.7625)
    assert np.isclose(w[0], np.sqrt(0.7625))
    # item2, f1<f2: sqrt(1 + 2*(-.25)*(1-.6) + .0625) = sqrt(.8625)
    assert np.isclose(w[1], np.sqrt(0.8625))
    assert np.allclose(w[2:], 0.25)  # |Delta| on agreement
    q, _ = sampling_distribution(f1, f2, p)
    assert np.isclose(q.sum(), 1.0) and np.isclose(q[0], np.sqrt(0.7625) / w.sum())
    # independent check of item1 straight from Theorem 1: E_y (l1 - l2 - Delta)^2
    direct = 0.8 * (0 - 1 - delta) ** 2 + 0.2 * (1 - 0 - delta) ** 2
    assert np.isclose(w[0] ** 2, direct)


def test_theorem1_matches_derivation4_by_enumeration():
    rng = np.random.default_rng(3)
    f1, f2 = rng.integers(0, 2, 40), rng.integers(0, 2, 40)
    p = rng.uniform(0.05, 0.95, 40)
    delta = introspective_delta(f1, f2, p)
    w = derivation4_weight(f1, f2, p, delta)
    l1 = np.stack([(f1 != 0).astype(float), (f1 != 1).astype(float)], 1)  # loss at y=0,1
    l2 = np.stack([(f2 != 0).astype(float), (f2 != 1).astype(float)], 1)
    py = np.stack([1 - p, p], 1)
    thm = np.sqrt((py * (l1 - l2 - delta) ** 2).sum(1))
    assert np.allclose(w, thm)


# ----------------------------------------------------------------- active!=
def test_active_neq_is_uniform_on_disagreement():
    dev = _dev_and_locked(1)[0]
    pol = _make("neq", dev, T=500, B=60)
    assert pol.delta == 0.0
    ev = lambda t, a, b: Event(t, t, 500, np.array([a, b]), None)
    pis = [pol.event_propensity(ev(10, a, b), 60) for a, b in [(0, 1), (1, 0), (0, 1)]]
    assert pis[0] > 0 and np.allclose(pis, pis[0])
    assert pol.event_propensity(ev(10, 1, 1), 60) == 0.0
    assert pol.event_propensity(ev(10, 0, 0), 60) == 0.0
    # q* over a pool is exactly uniform on the disagreement set
    preds = dev[0]
    q, d = sampling_distribution(preds[:, 0], preds[:, 1], np.full(len(preds), 0.5))
    dis = preds[:, 0] != preds[:, 1]
    assert d == 0.0 and np.allclose(q[dis], 1 / dis.sum()) and np.all(q[~dis] == 0)


def test_floor_is_positive_and_scale_hits_target():
    q = np.array([0.0, 1.0, 1.0, 0.1, 0.5])
    c = solve_scale(q, 0.05, 0.3)
    pi = propensity(q, c, 0.05)
    assert np.isclose(pi.mean(), 0.3, atol=1e-6)
    assert pi[0] == 0.0 and np.all(pi[1:] >= 0.05) and np.all(pi <= 1)


# ----------------------------------------------------------------- calibration vs active!=
def test_calibrated_differs_from_active_neq_report(capsys):
    """Measure whether calibration recovers instance information on a two-model, 0/1 problem."""
    rows = []
    for label, acc in [
        ("close models (.78/.72)", (0.78, 0.72)),
        ("far models (.90/.55)", (0.90, 0.55)),
    ]:
        dev, locked = _dev_and_locked(7, acc=acc)
        T, B = len(locked[1]), 150
        neq, cal = _make("neq", dev, T, B), _make("cal", dev, T, B)
        neq2 = _make("neq", dev, T, B, seed=1234)  # same design, other coins: the null overlap
        # exact analytic bound on instance information within the disagreement region
        d = abs(cal.delta)
        lo, hi = 1 - d, 1 + d
        post = cal.posterior
        p_all = post.p1(locked[2], locked[0])
        dis = locked[0][:, 0] != locked[0][:, 1]
        w = derivation4_weight(locked[0][:, 0], locked[0][:, 1], p_all, cal.delta)
        assert w[dis].min() >= lo - 1e-9 and w[dis].max() <= hi + 1e-9
        spread = w[dis].max() / w[dis].min()
        assert spread <= (1 + d) / (1 - d) + 1e-9
        agree_mass = w[~dis].sum() / w.sum()
        # realised queries on the same locked stream
        res = {}
        for nm, pol in [("neq", neq), ("cal", cal), ("neq2", neq2)]:
            r = run_episode(
                pol,
                model_predictions=locked[0],
                labels=locked[1],
                contexts=locked[2],
                delay=DELAY,
                budget=B,
                label_price=0.0,
                switch_cost=0.0,
            )
            res[nm] = np.array([x["requested"] for x in r.records], bool)
        a, b = res["neq"], res["cal"]
        jac = (a & b).sum() / max((a | b).sum(), 1)
        c2 = res["neq2"]
        jac_null = (a & c2).sum() / max((a | c2).sum(), 1)
        frac_cal_on_agree = (b & ~dis).sum() / max(b.sum(), 1)
        # correlation of frozen propensities across disagreement events
        cs, ns = [], []
        for t in np.where(dis)[0]:
            if t >= neq.window // 2:
                break
            ev = Event(int(t), int(t), T, locked[0][t], locked[2][t])
            cs.append(cal.event_propensity(ev, B))
            ns.append(neq.event_propensity(ev, B))
        cs, ns = np.array(cs), np.array(ns)
        rel_sd = float(np.std(cs / ns) / np.mean(cs / ns))
        rows.append(
            (
                label,
                cal.delta,
                spread,
                (1 + d) / (1 - d),
                agree_mass,
                jac,
                jac_null,
                frac_cal_on_agree,
                rel_sd,
            )
        )
    with capsys.disabled():
        print("\nSAWADE calibrated vs active!= (synthetic locked stream; T=1500, B=150)")
        print(
            "regime | Delta_theta | max/min q~ on disagreement | analytic bound | "
            "q~ mass on agreement | Jaccard(cal vs neq) | Jaccard(neq vs neq, other coins) | calibrated queries on agreement | "
            "rel. sd of pi_cal/pi_neq over disagreement"
        )
        for r in rows:
            print(
                f"{r[0]} | {r[1]:+.3f} | {r[2]:.3f} | {r[3]:.3f} | {r[4]:.3f} | {r[5]:.3f} "
                f"| {r[6]:.3f} | {r[7]:.3f} | {r[8]:.3f}"
            )
    # structural facts that hold whatever the data: bounded instance information
    for r in rows:
        assert r[2] <= r[3] + 1e-9
    # and more instance information when the models differ more
    assert rows[1][2] > rows[0][2]


# ----------------------------------------------------------------- estimator
def test_ht_difference_is_unbiased_by_enumeration():
    # N=7 events, arbitrary inclusion probabilities, arbitrary paired loss differences.
    pi = np.array([0.9, 0.5, 0.25, 0.7, 0.1, 0.6, 0.35])
    d = np.array([1, -1, 1, 0, 1, -1, 1], dtype=float)  # l0 - l1
    e = 0.0
    for z in itertools.product([0, 1], repeat=len(pi)):
        z = np.array(z)
        prob = np.prod(np.where(z == 1, pi, 1 - pi))
        e += prob * np.sum(z * d / pi)
    assert np.isclose(e, d.sum())


def test_policy_ht_matches_truth_in_expectation_with_frozen_propensities():
    """Run the real policy many times with the simulator; HT sum should average to the truth."""
    dev, locked = _dev_and_locked(2)
    preds, y = locked[0][:600], locked[1][:600]
    truth = float(((preds[:, 0] != y).astype(int) - (preds[:, 1] != y).astype(int)).sum())
    ests = []
    for s in range(300):
        pol = SawadeActiveNeq(
            600, 80, rng=np.random.default_rng(s), delay=DELAY, dev_preds=dev[0], window_frac=1.0
        )
        run_episode(
            pol,
            model_predictions=preds,
            labels=y,
            delay=DELAY,
            budget=80,
            label_price=0.0,
            switch_cost=0.0,
        )
        # events whose label would arrive after the horizon are lost; tolerate via count
        ests.append(pol.ht_diff)
    ests = np.array(ests)
    se = ests.std(ddof=1) / np.sqrt(len(ests))
    # releases past the horizon are never observed (last DELAY events), a known small bias
    lag_bias = float(
        (
            (preds[-DELAY:, 0] != y[-DELAY:]).astype(int)
            - (preds[-DELAY:, 1] != y[-DELAY:]).astype(int)
        ).sum()
    )
    assert abs(ests.mean() - (truth - lag_bias)) < 4 * se + 1.0


def test_frozen_issue_time_propensity_is_used():
    dev = _dev_and_locked(3)[0]
    pol = _make("neq", dev, T=300, B=40)
    fb = ReleasedFeedback(
        event_id=5,
        t_requested=5,
        t_released=8,
        label=1,
        model_losses=np.array([1, 0], dtype=np.int8),
        query_probability=0.25,
    )
    pol.observe([fb])
    # weight is exactly 1/0.25 whatever the policy would compute now
    assert np.isclose(pol.ht_diff, 4.0) and np.isclose(pol.w_sum, 4.0)
    assert np.allclose(pol.risk_estimates(), [1.0, 0.0])
    bad = ReleasedFeedback(5, 5, 8, 1, np.array([1, 0], dtype=np.int8), 0.0)
    try:
        pol.observe([bad])
        raised = False
    except ValueError:
        raised = True
    assert raised


# ----------------------------------------------------------------- episodes
def test_budget_feasible_pathwise_and_no_future_access():
    dev, locked = _dev_and_locked(4)
    for kind in ("neq", "cal"):
        for B in (5, 40, 400):
            pol = _make(kind, dev, T=len(locked[1]), B=B, seed=B)
            r = run_episode(
                pol,
                model_predictions=locked[0],
                labels=locked[1],
                contexts=locked[2],
                delay=DELAY,
                budget=B,
                label_price=1.0,
                switch_cost=1.0,
            )
            assert check_budget_feasible(r, B) == []
            assert check_no_future_access(r, DELAY) == []
            assert r.requested_labels <= B
            assert r.deployment_switches <= 1
            assert all(
                not x["requested"] or x["query_probability"] >= pol.p_floor for x in r.records
            )


def test_deploys_better_challenger_and_keeps_better_incumbent():
    dev, locked = _dev_and_locked(5, acc=(0.6, 0.9))
    pol = _make("neq", dev, T=len(locked[1]), B=120)
    r = run_episode(
        pol,
        model_predictions=locked[0],
        labels=locked[1],
        delay=DELAY,
        budget=120,
        label_price=0.0,
        switch_cost=0.0,
    )
    assert r.records[-1]["deployed_model"] == 1 and r.deployment_switches == 1
    # nothing is deployed before the window closes and every label has come back
    first = next(x["event_id"] for x in r.records if x["deployed_model"] == 1)
    assert first >= pol.last_release - DELAY
    dev2, locked2 = _dev_and_locked(5, acc=(0.9, 0.6))
    pol2 = _make("neq", dev2, T=len(locked2[1]), B=120)
    r2 = run_episode(
        pol2,
        model_predictions=locked2[0],
        labels=locked2[1],
        delay=DELAY,
        budget=120,
        label_price=0.0,
        switch_cost=0.0,
    )
    assert r2.deployment_switches == 0


def test_determinism_and_state_roundtrip():
    dev, locked = _dev_and_locked(6)
    out = []
    for _ in range(2):
        pol = _make("cal", dev, T=len(locked[1]), B=60, seed=11)
        r = run_episode(
            pol,
            model_predictions=locked[0],
            labels=locked[1],
            contexts=locked[2],
            delay=DELAY,
            budget=60,
            label_price=0.0,
            switch_cost=0.0,
        )
        out.append(
            [(x["requested"], x["query_probability"], x["deployed_model"]) for x in r.records]
        )
    assert out[0] == out[1]
    s = pol.state_dict()
    pol2 = _make("cal", dev, T=len(locked[1]), B=60, seed=99)
    pol2.load_state_dict(s)
    assert pol2.state_dict()["n_observed"] == s["n_observed"] and pol2.deployed == pol.deployed
