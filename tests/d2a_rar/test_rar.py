"""Tests for the RAR PAPER_RECONSTRUCTION (arXiv:2611.02251v1). CPU-only, no river needed."""

import numpy as np
import pytest

from shiftlab.sota.rar import (
    CANARY1,
    CANARY2,
    HOLD_HARD,
    HOLD_SOFT,
    SERVING,
    STATES,
    AllLabelsPolicy,
    FractionLabelPolicy,
    LeakageError,
    RARConfig,
    RARController,
    ScriptedDetector,
    earliest_retrain_time,
    feasible_W_train,
    latency_estimate,
    run_stream,
    utility_at_rho,
)

TAU = 50


class Oracle:
    def __init__(self, err=0.0, invert=False):
        self.err, self.invert = err, invert

    def predict(self, x):
        y = int(x[0] > 0.5)
        if self.invert:
            y = 1 - y
        if self.err and (int(x[1] * 1e6) % 1000) / 1000.0 < self.err:
            y = 1 - y  # deterministic noise
        return y


class SeqFactory:
    """fit() returns the pre-programmed learners in order (first call = warm-up model)."""

    def __init__(self, learners):
        self.l = list(learners)

    def fit(self, X, y):
        return self.l.pop(0) if len(self.l) > 1 else self.l[0]


class AlwaysPass:
    def passes(self, ctx):
        return True


class ScriptedQuality:
    def __init__(self, bad):
        self.bad = bad
        self.t = -1

    def fit(self, X):
        pass

    def corrupt(self, x):
        self.t += 1
        return self.bad[0] <= self.t < self.bad[1]


def stream(T=12000, seed=0, thr=0.5):
    rng = np.random.default_rng(seed)
    X = rng.random((T, 3))
    return X, (X[:, 0] > thr).astype(int)


def cfg(**kw):
    base = {
        "tau": TAU,
        "warmup": 50,
        "W_train": 200,
        "W_ref": 100,
        "W_cur": 50,
        "g": 10,
        "detector_warmup": 1,
        "W1": 40,
        "W2": 60,
        "p1": 0.2,
        "kappa_short": 300,
        "kappa_long": 500,
        "kappa_min": 50,
        "m_clear": 40,
        "min_train": 10,
        "r2_run": 20,
        "interim_fracs": (0.5,),
        "mode": "full_rar",
    }
    base.update(kw)
    return RARConfig(**base)


def run(c, factories, X, y, fire=(100,), quality=None, **kw):
    return run_stream(
        X,
        y,
        c,
        SeqFactory(factories),
        ScriptedDetector(fire),
        quality=quality,
        gate3=AlwaysPass(),
        **kw,
    )


def events(res, name):
    return [e for e in res["log"] if e["event"] == name]


# ---------------------------------------------------------------- formulas from the paper
def test_paper_formulas_frozen_example():
    assert earliest_retrain_time(9500, 800, 0.7, 2700) == 9500 + 800 + 1890 - 1
    assert (
        latency_estimate(0, 800, 0.7, 2700, 300, 0.2, 600) == 6390
    )  # Eq. 5, L_D inside label wait
    assert feasible_W_train(800, 0.7) == pytest.approx(800 / 0.3)


@pytest.mark.parametrize("tau,theta,W", [(50, 0.7, 200), (1, 0.5, 120), (30, 0.9, 150)])
def test_earliest_retrain_matches_formula_in_simulation(tau, theta, W):
    X, y = stream(6000)
    c = cfg(tau=tau, theta_L=theta, W_train=W, warmup=50, g=10)
    res = run(c, [Oracle(), Oracle()], X, y, fire=(100,))
    fl = events(res, "detector_flag")[0]
    r = events(res, "action:retrain")[0]
    t_star = earliest_retrain_time(fl["t_hat_d"], tau, theta, W)
    assert r["t"] == t_star
    ctl = res["controller"]
    need = theta * W - 1e-9
    assert (
        ctl._labeled_in_window(fl["t_hat_d"], t_star - 1)
        < need
        <= ctl._labeled_in_window(fl["t_hat_d"], t_star)
    )


# ---------------------------------------------------------------- state machine
def test_commit_path_serving_canary1_canary2_serving():
    X, y = stream()
    res = run(cfg(), [Oracle(invert=True), Oracle()], X, y)  # bad incumbent, good challenger
    tr = [e["to"] for e in events(res, "transition")]
    assert tr[:3] == [CANARY1, CANARY2, SERVING]
    assert len(events(res, "commit")) == 1
    assert res["counts"]["retrain"] == 1 and res["counts"]["rollback"] == 0
    assert all(s in STATES for s in tr)


def test_rollback_r1_goes_to_soft_hold_and_expires():
    X, y = stream()
    res = run(cfg(), [Oracle(), Oracle(err=0.25)], X, y)
    rb = events(res, "action:rollback")
    assert len(rb) == 1 and rb[0]["cause"].startswith("R1")
    tr = events(res, "transition")
    assert [e["to"] for e in tr][:3] == [CANARY1, HOLD_SOFT, SERVING]
    hold = next(e for e in tr if e["to"] == HOLD_SOFT)
    ex = events(res, "hold_exit")[0]
    assert ex["reason"] == "expiry" and ex["t"] - hold["t"] == cfg().kappa_short


def test_rollback_r3_sanity_vs_majority():
    X, y = stream(thr=0.2)  # 80% class 1; inverted challenger
    res = run(cfg(), [Oracle(), Oracle(invert=True)], X, y)
    assert events(res, "action:rollback")[0]["cause"] in ("R3", "R1_interim")


def test_rollback_r2_corruption_goes_to_hard_hold_without_override():
    X, y = stream()
    res = run(cfg(), [Oracle(), Oracle()], X, y, quality=ScriptedQuality((300, 700)))
    rb = events(res, "action:rollback")
    assert rb and rb[0]["cause"] == "R2"
    to = [e["to"] for e in events(res, "transition")]
    assert HOLD_HARD in to
    assert not events(res, "emergency_override")
    ex = events(res, "hold_exit")[0]
    assert ex["reason"] == "clean_run" and ex["t"] >= 700 + cfg().m_clear - 1


def test_timeout_fails_closed_with_rollback_and_alert():
    X, y = stream()
    res = run(cfg(kappa_canary_mult=0.1), [Oracle(), Oracle()], X, y)
    assert events(res, "action:rollback")[0]["cause"] == "timeout"
    assert any(e.get("kind") == "canary_timeout" for e in events(res, "action:alert"))


def test_dead_band_reverts_without_rollback_cost():
    X, y = stream()
    res = run(cfg(z_commit=1.0), [Oracle(), Oracle()], X, y)  # identical models: z = 0 < 1
    assert events(res, "dead_band_discard") and not events(res, "action:rollback")
    assert res["counts"]["rollback"] == 0 and res["counts"]["retrain"] == 1


def test_gate2_blocks_until_labels_and_alerts_A1():
    X, y = stream()
    res = run(cfg(), [Oracle(), Oracle()], X, y)
    a1 = [e for e in events(res, "action:alert") if e.get("kind") == "A1"]
    assert len(a1) == 1 and a1[0]["t"] < events(res, "action:retrain")[0]["t"]


def test_gate3_native_blocks_retrain_when_no_degradation():
    X, y = stream()
    res = run_stream(
        X, y, cfg(), SeqFactory([Oracle(), Oracle()]), ScriptedDetector((100,))
    )  # native Gate 3
    assert res["counts"]["retrain"] == 0
    assert any(e.get("kind") == "A2" for e in events(res, "action:alert"))


# ---------------------------------------------------------------- label release
def test_no_label_before_release_in_harness():
    X, y = stream(3000)
    seen = []

    class Spy(RARController):
        def _observe(self, t, i, yi):
            seen.append((t, i))
            super()._observe(t, i, yi)

    run(cfg(), [Oracle(), Oracle()], X, y, controller_cls=Spy)
    assert seen and all(t == i + TAU for t, i in seen)


def test_controller_rejects_early_or_unrequested_labels():
    X, y = stream(200)
    ctl = RARController(cfg(), SeqFactory([Oracle()]), ScriptedDetector(()))
    ctl.start(X[:50], y[:50])
    ctl.step(0, X[50])
    with pytest.raises(LeakageError):
        ctl.step(1, X[51], [(0, int(y[50]))])  # t=1 < 0 + tau
    ctl2 = RARController(
        cfg(tau=0),
        SeqFactory([Oracle()]),
        ScriptedDetector(()),
        label_policy=FractionLabelPolicy(2),
    )
    ctl2.start(X[:50], y[:50])
    ctl2.step(0, X[50])
    ctl2.step(1, X[51])  # instance 1 not requested
    with pytest.raises(LeakageError):
        ctl2.step(2, X[52], [(1, 1)])


def test_pending_labels_never_released_at_end():
    X, y = stream(2000)
    res = run(cfg(), [Oracle(), Oracle()], X, y)
    assert sum(res["controller"].labeled) == len(y) - 50 - TAU


# ---------------------------------------------------------------- canary routed-label accounting
def test_canary_routed_label_counts():
    X, y = stream()
    res = run(cfg(), [Oracle(invert=True), Oracle()], X, y)
    ctl = res["controller"]
    p = events(res, "stage1_pass")[0]
    assert p["n"] == cfg().W1
    s1 = [i for i in range(len(ctl.stage)) if ctl.stage[i] == 1]
    routed = [i for i in s1 if ctl.routed[i]]
    assert abs(len(routed) / len(s1) - cfg().p1) < 0.01  # stratified interleaving
    assert all(ctl.p_new[i] != -1 for i in routed) and all(
        ctl.p_new[i] == -1 for i in s1 if not ctl.routed[i]
    )
    assert sum(1 for i in routed if i + TAU <= p["t"]) == cfg().W1  # unrouted never counted
    s2 = [i for i in range(len(ctl.stage)) if ctl.stage[i] == 2]
    assert s2 and all(ctl.routed[i] for i in s2)
    c2 = events(res, "commit")[0]
    assert sum(1 for i in s2 if i + TAU <= c2["t"]) == cfg().W2


def test_served_prediction_ledgered_not_shadow():
    X, y = stream()
    res = run(cfg(), [Oracle(invert=True), Oracle()], X, y)
    ctl = res["controller"]
    for i in range(len(y) - 50):
        assert res["correct"][i] == float(ctl.served[i] == y[50 + i])
        if ctl.stage[i] == 1 and not ctl.routed[i]:
            assert ctl.served[i] == ctl.p_old[i]
        if ctl.stage[i] in (1, 2) and ctl.routed[i]:
            assert ctl.served[i] == ctl.p_new[i]


# ---------------------------------------------------------------- objective accounting
def test_objective_each_cost_charged_once_per_action():
    X, y = stream()
    for factories in ([Oracle(invert=True), Oracle()], [Oracle(), Oracle(err=0.25)]):
        c = cfg(rho=7.0)
        res = run(c, factories, X, y)
        n = {k: len(events(res, "action:" + k)) for k in ("retrain", "alert", "rollback")}
        for k, v in n.items():
            assert res["counts"][k] == v
        U = (
            res["n_correct"]
            - 7.0 * n["retrain"]
            - 0.05 * 7.0 * n["alert"]
            - 0.2 * 7.0 * n["rollback"]
        )
        assert res["U"] == pytest.approx(U)
        assert utility_at_rho(res, 7.0, c) == pytest.approx(U)
    assert (
        n["retrain"] == 1 and n["rollback"] == 1
    )  # rolled-back retrain pays C_r and C_b once each


def test_utility_affine_in_rho_for_cost_blind():
    X, y = stream()
    r = run(cfg(rho=1.0), [Oracle(invert=True), Oracle()], X, y)
    u1, u5, u10 = (utility_at_rho(r, k, cfg()) for k in (1, 5, 10))
    assert (u10 - u5) / 5 == pytest.approx((u5 - u1) / 4)


# ---------------------------------------------------------------- baselines / modes
def test_cost_aware_binary_gate():
    X, y = stream()
    y = y.copy()
    y[100:] = 1 - y[100:]  # incumbent (Oracle) good before the flip, bad after
    lo = run_stream(
        X,
        y,
        cfg(mode="cost_aware_binary", rho=1e-6),
        SeqFactory([Oracle(), Oracle(invert=True)]),
        ScriptedDetector((100,)),
    )
    hi = run_stream(
        X,
        y,
        cfg(mode="cost_aware_binary", rho=1e9),
        SeqFactory([Oracle(), Oracle(invert=True)]),
        ScriptedDetector((100,)),
    )
    assert lo["counts"]["retrain"] == 1 and hi["counts"]["retrain"] == 0
    g = events(hi, "cost_gate")[0]
    assert g["H"] >= cfg().W_train and not g["passes"]


def test_no_response_never_acts_and_binary_has_no_canary():
    X, y = stream()
    nr = run_stream(
        X, y, cfg(mode="no_response"), SeqFactory([Oracle(invert=True)]), ScriptedDetector((100,))
    )
    assert sum(nr["counts"].values()) == 0
    b = run_stream(
        X,
        y,
        cfg(mode="binary"),
        SeqFactory([Oracle(invert=True), Oracle()]),
        ScriptedDetector((100,)),
    )
    assert b["counts"]["retrain"] == 1 and not events(b, "transition") and b["acc"] > nr["acc"]


# ---------------------------------------------------------------- hooks
def test_label_request_hook_swap():
    X, y = stream(3000)
    base = run(cfg(), [Oracle(), Oracle()], X, y)
    same = run(cfg(), [Oracle(), Oracle()], X, y, label_policy=AllLabelsPolicy())
    assert base["counts"] == same["counts"] and np.array_equal(base["correct"], same["correct"])
    half = run(cfg(), [Oracle(), Oracle()], X, y, label_policy=FractionLabelPolicy(2))
    n = len(y) - 50
    assert half["controller"].n_requested == (n + 1) // 2


def test_gate_rule_hook_swap():
    X, y = stream()

    class Never:
        def passes(self, ctx):
            return False

    blocked = run_stream(
        X, y, cfg(), SeqFactory([Oracle(), Oracle()]), ScriptedDetector((100,)), gate2=Never()
    )
    assert blocked["counts"]["retrain"] == 0
    open_ = run_stream(
        X,
        y,
        cfg(min_train=1),
        SeqFactory([Oracle(), Oracle()]),
        ScriptedDetector((100,)),
        gate2=AlwaysPass(),
        gate3=AlwaysPass(),
    )
    assert open_["counts"]["retrain"] == 1
    fl = events(open_, "detector_flag")[0]
    r = events(open_, "action:retrain")[0]
    assert r["t"] == fl["t"]
