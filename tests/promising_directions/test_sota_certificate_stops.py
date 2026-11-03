"""Tests for the certificate-triggered stopping comparators (DISCERN-style, gated deployment).

These are the comparators that decide whether the programme continues, so the tests check the
properties that make them *valid and strong*: nominal CS coverage, nonnegative wealth, a verdict
that fires on a clear effect and does not fire on a null, acquisition that actually stops, the
frozen issue-time propensity in the weighting, the hard budget, determinism and state round trip.
Seeds and sizes are CPU-sized and fixed; nothing here is a result of the research programme.
"""

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

SOTA = Path(__file__).resolve().parents[2] / "scripts/promising_directions/sota"
sys.path.insert(0, str(SOTA))
sys.path.insert(0, str(SOTA / "competitors"))

from certificate_stops import (
    PSI_MOPE,
    DiscernStyleStop,
    GatedDeploymentStop,
    MopeCS,
    MopeLowerCS,
    PrPlEBCS,
    _argmax_triangle,
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
P_MIN = 0.05
WMAX = 1.0 / P_MIN


def _stream(T, rho, p, seed):
    """Two models. They disagree w.p. rho; on disagreement the challenger is right w.p. p."""
    r = np.random.default_rng(seed)
    y = r.integers(0, 2, T)
    dis = r.random(T) < rho
    chal_right = r.random(T) < p
    chal = np.where(dis, np.where(chal_right, y, 1 - y), y)
    inc = np.where(dis, 1 - chal, chal)
    return np.stack([inc, chal], 1), y


def _make(kind, T, budget, seed, alpha=0.05, eps=0.0, **kw):
    rng = policy_rng(seed, 0, kind)
    if kind == "discern":
        return DiscernStyleStop(T, budget, alpha, eps, rng=rng, **kw)
    return GatedDeploymentStop(T, budget, alpha, rng=rng, **kw)


def _run(kind, rho, p, seed, T=2500, budget=600, **kw):
    preds, y = _stream(T, rho, p, seed)
    pol = _make(kind, T, budget, seed, **kw)
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=DELAY, budget=budget,
        label_price=0.1, switch_cost=1.0,
    )  # fmt: skip
    return pol, res


def _ht_stream(T, rho, p, q, rng):
    """(w, d) for a fixed query probability q: agree -> (1, 0); unqueried -> (0, 0)."""
    dis = rng.random(T) < rho
    cr = rng.random(T) < p
    lab = rng.random(T) < q
    w = np.where(dis, np.where(lab, 1.0 / q, 0.0), 1.0)
    d = np.where(dis & lab, np.where(cr, 1, -1), 0)
    return w, d


KINDS = ["discern", "gated"]


# ------------------------------------------------------------------ hand-computed arithmetic
def test_prpl_eb_first_step_by_hand():
    # delta=.05, t=1: sigma2_0 = (1/4)/1, mu_0 = 1/2, lambda = min(sqrt(2 ln 40/(.25 ln 2)), .5)
    cs = PrPlEBCS(0.05)
    cs.update(1.0)
    assert cs.last_lam == pytest.approx(0.5)
    psi_e = -math.log(0.5) - 0.5
    assert cs.sum_vpsi == pytest.approx(4 * (1.0 - 0.5) ** 2 * psi_e / 4.0)
    assert cs.sum_lam_w == pytest.approx(0.5)
    # lower end = (sum l W - sum v psi - ln(2/delta)) / sum l is negative, so the range clip holds
    assert cs.lo == 0.0
    assert cs.hi == 1.0


def test_psi_constant_and_lemma1():
    assert PSI_MOPE == pytest.approx(2 - 4 * math.log(2))
    x = np.linspace(-0.5, 5, 200)
    assert np.all(np.log1p(x) >= x + PSI_MOPE * x**2 - 1e-12)  # Karampatziakis Lemma 1


def test_triangle_argmax_simple_cases():
    # linear objective b = (0, 1) with A = 0: maximiser is the vertex (0, 1/2)
    lam = _argmax_triangle(np.zeros((2, 2)), np.array([0.0, 1.0]), WMAX)
    assert lam == pytest.approx((0.0, 0.5))
    # no signal -> no bet
    assert _argmax_triangle(np.zeros((2, 2)), np.zeros(2), WMAX) == (0.0, 0.0)
    # interior optimum: A = I, b small -> -b/(2 psi) (psi < 0) is feasible and returned
    b = np.array([0.01, 0.02])
    lam = _argmax_triangle(np.eye(2), b, WMAX)
    assert lam == pytest.approx(tuple(-b / (2 * PSI_MOPE)), rel=1e-6)


# ------------------------------------------------------------------ nonnegative wealth
def test_mope_bets_in_C_and_wealth_factors_nonnegative():
    rng = np.random.default_rng(3)
    cs = MopeCS(0.05, WMAX)
    vs = np.linspace(0, 1, 11)
    for w, d in zip(*_ht_stream(400, 0.4, 0.8, 0.2, rng)):
        for half in (cs.plus, cs.minus):
            assert half.lam2 >= -1e-12
            assert half.lam1 + half.lam2 <= 0.5 + 1e-9
            assert half.lam1 * (1 - WMAX) + half.lam2 <= 0.5 + 1e-9
            # every possible next observation, at every test value, keeps >= half the wealth
            for ww in (0.0, 1.0, 3.0, WMAX):
                for rr in (0.0, 1.0):
                    for v in vs:
                        assert half.factor(ww, rr, float(v)) >= 0.5 - 1e-9
        cs.update(float(w), (float(d) + 1) / 2)


def test_eb_bets_in_range_and_endpoints_monotone():
    rng = np.random.default_rng(4)
    cs = PrPlEBCS(0.1)
    lo = hi = None
    for w in rng.random(300):
        cs.update(float(w))
        assert 0.0 < cs.last_lam <= cs.lam_max
        if lo is not None:
            assert cs.lo >= lo and cs.hi <= hi  # running intersection
        lo, hi = cs.lo, cs.hi


# ------------------------------------------------------------------ coverage
@pytest.mark.parametrize(
    "rho,p,q", [(0.3, 0.5, 0.3), (0.3, 0.8, 0.3), (0.5, 0.35, 0.1), (0.05, 0.5, 0.5)]
)
def test_confidence_sequences_cover_true_mean_uniformly_in_time(rho, p, q):
    """Both CSs must contain the true G at EVERY time with probability >= 1 - alpha."""
    alpha, n_runs, T = 0.1, 60, 300
    g = rho * (2 * p - 1)
    miss = {"eb": 0, "mope": 0}
    for s in range(n_runs):
        w, d = _ht_stream(T, rho, p, q, np.random.default_rng(s))
        eb, mope = PrPlEBCS(alpha), MopeCS(alpha, WMAX)
        bad = {"eb": False, "mope": False}
        for wi, di in zip(w, d):
            eb.update((wi * di + WMAX) / (2 * WMAX))
            mope.update(float(wi), (float(di) + 1) / 2)
            if not WMAX * (2 * eb.lo - 1) - 1e-9 <= g <= WMAX * (2 * eb.hi - 1) + 1e-9:
                bad["eb"] = True
            if not 2 * mope.v_lo - 1 - 1e-9 <= g <= 2 * mope.v_hi - 1 + 1e-9:
                bad["mope"] = True
        for k in miss:
            miss[k] += bad[k]
    # nominal rate alpha; allow three binomial standard deviations. These CSs are conservative,
    # so in practice the observed rate is far below alpha; the bound is what is asserted.
    tol = alpha + 3 * math.sqrt(alpha * (1 - alpha) / n_runs)
    assert miss["eb"] / n_runs <= tol
    assert miss["mope"] / n_runs <= tol


# ------------------------------------------------------------------ verdicts
@pytest.mark.parametrize("kind", KINDS)
def test_verdict_fires_and_deploys_on_clearly_better_challenger(kind):
    for seed in range(4):
        pol, res = _run(kind, 0.3, 0.85, seed)
        assert pol.stopped
        assert pol.verdict == ("safe" if kind == "discern" else "deploy")
        assert pol.deployed == 1
        assert res.deployment_switches == 1


@pytest.mark.parametrize("kind", KINDS)
def test_verdict_keeps_incumbent_on_clearly_worse_challenger(kind):
    fired = 0
    for seed in range(4):
        pol, res = _run(kind, 0.3, 0.2, seed)
        assert pol.deployed == 0 and res.deployment_switches == 0
        assert pol.verdict in ("", "regression", "discard")
        fired += pol.stopped
    assert fired >= 3  # a clear regression should be called, not merely not-promoted


@pytest.mark.parametrize("kind", KINDS)
def test_no_false_deployment_on_a_null(kind):
    """Challenger exactly as good as the incumbent: promotion has probability <= alpha."""
    alpha, n = 0.1, 40
    promoted = 0
    for seed in range(n):
        pol, _ = _run(kind, 0.3, 0.5, seed, T=700, budget=250, alpha=alpha)
        promoted += pol.deployed
    assert promoted / n <= alpha + 3 * math.sqrt(alpha * (1 - alpha) / n)


def test_eps_tolerance_promotes_a_marginally_worse_challenger_but_strict_does_not():
    """DISCERN's Safe(eps): certify 'not worse by more than eps'. With eps=0 the same stream
    must NOT promote (G < 0); a generous eps can."""
    strict = tolerant = 0
    for seed in range(4):
        # G = rho(2p-1) = 0.4 * (-0.1) = -0.04: marginally worse
        ps, _ = _run("discern", 0.4, 0.45, seed, T=4000, budget=1500, eps=0.0)
        pt, _ = _run("discern", 0.4, 0.45, seed, T=4000, budget=1500, eps=0.5)
        strict += ps.deployed
        tolerant += pt.deployed
    assert strict == 0
    assert tolerant >= 3


def test_tier0_zero_label_certificate_when_models_nearly_agree():
    T = 3000
    preds, y = _stream(T, 0.0, 0.5, 0)  # identical models: disagreement rate exactly 0
    pol = DiscernStyleStop(T, 100, 0.05, 0.1, rng=policy_rng(0, 0, "t0"), tier0=True)
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=DELAY, budget=100, label_price=0.1,
        switch_cost=1.0,
    )  # fmt: skip
    assert pol.verdict == "safe" and pol.stopped
    assert res.requested_labels == 0
    # Tier 1 alone also certifies with zero labels here (agreements are exact zeros in the
    # increment stream), but no earlier than the dedicated rho CS does
    off = DiscernStyleStop(T, 100, 0.05, 0.1, rng=policy_rng(0, 0, "t0"))
    run_episode(off, model_predictions=preds, labels=y, delay=DELAY, budget=100,
                label_price=0.1, switch_cost=1.0)  # fmt: skip
    assert off.stopped and off.verdict == "safe"
    assert pol.stop_event <= off.stop_event


# ------------------------------------------------------------------ acquisition stops
@pytest.mark.parametrize("kind", KINDS)
def test_acquisition_stops_once_a_verdict_fires(kind):
    preds, y = _stream(2500, 0.3, 0.9, 1)
    pol = _make(kind, 2500, 600, 1)

    class Spy:
        name = pol.name

        def __init__(self):
            self.log = []

        def predict(self, e):
            return pol.predict(e)

        def request_labels(self, e, rem):
            before = pol.stopped
            req = pol.request_labels(e, rem)
            self.log.append((before, req.requested))
            return req

        def observe(self, fb):
            pol.observe(fb)

        def decision_state(self):
            return pol.decision_state()

    spy = Spy()
    res = run_episode(spy, model_predictions=preds, labels=y, delay=DELAY, budget=600,
                      label_price=0.1, switch_cost=1.0)  # fmt: skip
    assert pol.stopped
    assert not any(before and req for before, req in spy.log)  # nothing bought after the stop
    assert any(before for before, _ in spy.log)  # and the episode did continue past it
    assert res.requested_labels < 600  # the point of the comparator: budget left unspent


@pytest.mark.parametrize("kind", KINDS)
def test_unresolved_null_spends_budget_without_stopping(kind):
    pol, res = _run(kind, 0.3, 0.5, 0, T=700, budget=60)
    assert not pol.stopped
    assert res.requested_labels == 60  # nothing certified, so it keeps buying until the cap


# ------------------------------------------------------------------ frozen issue-time propensity
@pytest.mark.parametrize("kind", KINDS)
def test_weight_uses_issue_time_propensity_from_feedback(kind):
    pol = _make(kind, 100, 100, 0)
    seen = []
    orig = pol._ingest

    def spy(w, d, ref):
        seen.append((w, d))
        orig(w, d, ref)

    pol._ingest = spy
    # drive events until one label is requested (disagreeing predictions every event)
    t = 0
    while True:
        ev = Event(event_id=t, t=t, horizon=100, model_predictions=np.array([0, 1]))
        req = pol.request_labels(ev, 100)
        if req.requested:
            break
        t += 1
    # the policy froze req.probability at issue; the released feedback carries its OWN value,
    # and the weight must be 1/that value, not 1/(any later recomputation of the pacer).
    fb = ReleasedFeedback(
        event_id=t, t_requested=t, t_released=t + DELAY, label=1,
        model_losses=np.array([1, 0], dtype=np.int8), query_probability=0.25,
    )  # fmt: skip
    pol.observe([fb])
    assert req.probability != 0.25  # so the two candidate weights are distinguishable
    assert (4.0, 1) in seen  # w = 1/0.25 from the feedback, d = l0 - l1 = +1


# ------------------------------------------------------------------ feasibility, determinism
@pytest.mark.parametrize("kind", KINDS)
def test_pathwise_budget_feasible_and_no_future_access(kind):
    for seed in range(3):
        _, res = _run(kind, 0.4, 0.5, seed, T=600, budget=25)
        assert check_budget_feasible(res, 25) == []
        assert check_no_future_access(res, DELAY) == []
        assert res.refused_requests == 0
        assert res.requested_labels <= 25


@pytest.mark.parametrize("kind", KINDS)
def test_deterministic_given_seed(kind):
    a, ra = _run(kind, 0.3, 0.7, 5, T=800, budget=100)
    b, rb = _run(kind, 0.3, 0.7, 5, T=800, budget=100)
    assert ra.records == rb.records
    assert a.state_dict() == b.state_dict()


# ------------------------------------------------------------------ state round trip
@pytest.mark.parametrize("kind", KINDS)
def test_state_dict_round_trip_resumes_identically(kind):
    T, budget = 500, 80
    preds, y = _stream(T, 0.3, 0.6, 2)
    pol = _make(kind, T, budget, 2)
    calls, snap = [], {}
    half = T // 2

    class Rec:
        name = pol.name

        def predict(self, e):
            return pol.predict(e)

        def request_labels(self, e, rem):
            if e.t == half:
                snap["s"] = json.loads(json.dumps(pol.state_dict()))  # must be JSON-clean
                snap["deployed"] = pol.deployed
            req = pol.request_labels(e, rem)
            if e.t >= half:
                calls.append(("req", e, rem, (req.requested, req.probability)))
            return req

        def observe(self, fb):
            pol.observe(fb)
            if snap:
                calls.append(("obs", fb, None, None))

        def decision_state(self):
            return pol.decision_state()

    run_episode(Rec(), model_predictions=preds, labels=y, delay=DELAY, budget=budget,
                label_price=0.1, switch_cost=1.0)  # fmt: skip
    clone = _make(kind, T, budget, 99)  # different seed: the restored RNG must override it
    clone.load_state_dict(copy.deepcopy(snap["s"]))
    for tag, a, b, expected in calls:
        if tag == "req":
            r = clone.request_labels(a, b)
            assert (r.requested, r.probability) == expected
        else:
            clone.observe(a)
    assert clone.state_dict() == pol.state_dict()
    assert clone.deployed == pol.deployed


def test_constructor_validation():
    rng = policy_rng(0, 0, "v")
    with pytest.raises(ValueError):
        DiscernStyleStop(100, 10, 1.5, 0.0, rng=rng)
    with pytest.raises(ValueError):
        DiscernStyleStop(100, 10, 0.05, -0.1, rng=rng)
    with pytest.raises(ValueError):
        PrPlEBCS(0.05, lam_max=1.0)
    with pytest.raises(ValueError):
        MopeLowerCS(0.05, 1.0)
