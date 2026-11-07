"""Unit tests for sprint-2 Family R (risk-adjusted decision architectures on the D2 gate)."""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import fam_a
import fam_r
from fam_r import EXTRA, LAMS, CondMeanEP, MarkovSUIPlus
from regimes import REGIMES
from simulator import check_budget_feasible, policy_rng, run_episode
from suite import stream_from_losses

CANDS = [
    "R2",
    "R2-qc",
    "R2-floor25",
    "R3-base",
    "R3-plugin",
    "R3-near",
    "R3-alloc",
    "R3-plugnear",
    "R4-both",
    "R4-comb",
    "R5",
    "R5-nopen",
    "R5-iidvar",
    "R6:D2-floor25",
    "R6:D2-always",
    "R:D2_replica",
]
CERTIFIED = [
    "R2",
    "R2-qc",
    "R2-floor25",
    "R3-base",
    "R3-plugin",
    "R3-near",
    "R3-alloc",
    "R3-plugnear",
    "R4-both",
    "R4-comb",
    "R6:D2-floor25",
    "R6:D2-always",
]


def _run(name, regime="F0_null", seed=0, T=2000, B=200, delay=None, alpha=0.05, extra=None):
    R = REGIMES[regime]
    losses = R.sample(np.random.default_rng(seed), T)
    preds, labels = stream_from_losses(losses, np.random.default_rng(seed + 1))
    d = R.delay if delay is None else delay
    fac = (extra or EXTRA)[name]
    pol = fac(T, B, 5.0, 0.05, alpha, d, lambda n: policy_rng(11, seed, n))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=d,
        budget=B,
        label_price=0.05,
        switch_cost=5.0,
        trace=True,
    )
    return pol, res


# ------------------------------------------------------------------ contract
@pytest.mark.parametrize("name", CANDS)
@pytest.mark.parametrize("regime", ["F9_highdis_better", "F0_null"])
def test_budget_never_exceeded(name, regime):
    for B in (30, 200):
        _, res = _run(name, regime, B=B, T=1200)
        assert res.requested_labels <= B
        assert not check_budget_feasible(res, B)
        assert res.refused_requests == 0
        assert all(0.0 <= r["query_probability"] <= 1.0 for r in res.records)


@pytest.mark.parametrize("name", CERTIFIED)
def test_no_promotion_on_short_null(name):
    promoted = 0
    for seed in range(12):
        _, res = _run(name, "F0_null", seed=seed, T=300, B=60, delay=10)
        promoted += any(r["deployed_model"] == 1 for r in res.records)
    assert promoted <= 2  # nominal level alpha/2 = .025 per run; P(Bin(12, .025) >= 3) < .004


def test_r5_short_null_and_kappa_monotone():
    prom = {k: 0 for k in (0.0, 1.645, 50.0)}
    for k in prom:
        ex = {"x": fam_r._g("x", evidence="econ", kappa=k)}
        for seed in range(12):
            _, res = _run("x", "F0_null", seed=seed, T=300, B=60, delay=10, extra=ex)
            prom[k] += any(r["deployed_model"] == 1 for r in res.records)
    assert prom[50.0] == 0
    assert prom[50.0] <= prom[1.645] <= prom[0.0]
    assert prom[1.645] <= 3


def test_replica_reproduces_d2_exactly():
    for regime, seed in (("F0_better", 0), ("F0_null", 2), ("F5_dep_null_r8", 1)):
        _, a = _run("D2", regime, seed=seed, extra=__import__("fam_d").EXTRA)
        _, b = _run("R:D2_replica", regime, seed=seed)
        assert a.net_cost == b.net_cost
        assert [r["deployed_model"] for r in a.records] == [r["deployed_model"] for r in b.records]
        assert [r["requested"] for r in a.records] == [r["requested"] for r in b.records]


# ------------------------------------------------------------------ R2: conditional-mean e-process
def test_ipw_factor_has_conditional_mean_one_plus_lam_a():
    """E over the query coin and the label of 1 + lam (Y - 1/2) = 1 + lam (p - 1/2), any q > 0."""
    for p in np.linspace(0, 1, 11):
        for q in (0.01, 0.2, 0.7, 1.0):
            y1 = 1.0 / q  # queried and challenger correct
            m = q * (p * (1 + LAMS * (y1 - 0.5)) + (1 - p) * (1 - LAMS / 2)) + (1 - q) * (
                1 - LAMS / 2
            )
            assert np.allclose(m, 1 + LAMS * (p - 0.5))


def test_cm_exact_expectation_under_weak_null_by_enumeration():
    """Brute force: a time-varying p sequence with every running average <= 1/2 but p_k > 1/2
    late (weak null holds, pointwise null fails). E[E_n] <= 1 exactly (sum over 2^n paths)."""
    ps = np.array([0.3, 0.35, 0.4, 0.45, 0.7, 0.6, 0.65, 0.55, 0.5, 0.5])
    assert np.all(np.cumsum(ps - 0.5) <= 1e-12) and (ps > 0.5).any()
    tot = 0.0
    for z in itertools.product((0, 1), repeat=len(ps)):
        pr = float(np.prod(np.where(np.array(z) == 1, ps, 1 - ps)))
        e = CondMeanEP()
        for zi in z:
            e.update(float(zi))
        tot += pr * e.value
    assert tot <= 1.0 + 1e-12


def test_cm_controls_weak_null_where_started_mixture_does_not():
    """Monte Carlo on a weak-null path (early p = .3, late p = .7, running average <= 1/2)."""
    rng = np.random.default_rng(7)
    ps = np.r_[np.full(120, 0.3), np.full(120, 0.7)]
    hits_cm = hits_sm = 0
    n = 300
    for _ in range(n):
        z = (rng.random(len(ps)) < ps).astype(int)
        cm, sm = CondMeanEP(), fam_r.StartedMixture(+1)
        mcm = msm = 0.0
        for zi in z:
            mcm = max(mcm, cm.update(float(zi)))
            msm = max(msm, sm.update(int(zi)))
        hits_cm += mcm >= 20
        hits_sm += msm >= 20
    assert hits_cm / n <= 0.05 + 2 * math.sqrt(0.05 * 0.95 / n)
    assert hits_sm / n >= 0.5  # the pointwise test rejects: its null is violated here


def test_ipw_cm_valid_with_adaptive_propensity():
    """IPW CM e-process, iid p = .5 null, q depends on the past (more queries after a hit)."""
    rng = np.random.default_rng(3)
    n, hits = 400, 0
    for _ in range(n):
        e, prev, mx = CondMeanEP(), 0, 0.0
        for _k in range(300):
            q = 0.9 if prev else 0.15
            r = int(rng.random() < 0.5)
            if rng.random() < q:
                mx = max(mx, e.update(r / q))
                prev = r
            else:
                mx = max(mx, e.update(0.0))
        hits += mx >= 20
    assert hits / n <= 0.05 + 2 * math.sqrt(0.05 * 0.95 / n)


def test_cm_has_power_on_iid_alternative():
    rng = np.random.default_rng(4)
    e = CondMeanEP()
    for zi in rng.random(200) < 0.7:
        e.update(float(zi))
    assert e.value >= 100


def test_ipw_test_freezes_after_budget():
    pol, res = _run("R2", "F0_null", seed=0, T=2000, B=40, delay=5)
    assert pol.ev["cmi"][0].frozen  # the budget ran out before any verdict
    assert pol.ev["cmi"][0].n <= sum(1 for r in res.records)


# ------------------------------------------------------------------ R3: Markov variants
def _exact_ll(z, ts, p, rho):
    a = rho ** np.diff(ts)
    m = a * z[:-1] + (1 - a) * p
    return np.log(p if z[0] else 1 - p) + np.sum(np.log(np.where(z[1:] == 1, m, 1 - m)))


VARIANTS = {
    "base": {},
    "plugin": {"beta": 0.5},
    "near": {"p_tilt": 1.0},
    "alloc": {"w_first": 0.9, "stride": 20},
    "plugnear": {"beta": 0.5, "p_tilt": 1.0},
}


def _mk(kw, **over):
    return MarkovSUIPlus(**{**fam_a._B, "n_rho": 40, "n_p": 15, **kw, **over})


def _run_seq(ev, z, ts):
    vals, prev = [], None
    for k in range(len(z)):
        vals.append(ev.update(int(z[k]), int(ts[k] - ts[k - 1]) if k else 0, prev))
        prev = int(z[k])
    return vals


@pytest.mark.parametrize("variant", list(VARIANTS))
def test_markov_variant_exact_expectation_brute_force(variant):
    """Enumerate all 2^11 outcome sequences (fixed irregular gaps): for several null (p, rho),
    E_theta[E_n] <= 1 (started mixture at the last step, which upper-bounds the e-process mass)."""
    n = 11
    ts = np.cumsum([0, 1, 3, 1, 2, 5, 1, 1, 4, 2, 1])
    kw = {**VARIANTS[variant], "rho_every": 1}
    seqs = list(itertools.product((0, 1), repeat=n))
    vals = []
    for z in seqs:
        vals.append(_run_seq(_mk(kw, stride=3 if "stride" not in kw else 4), np.array(z), ts)[-1])
    vals = np.array(vals)
    for p0, rho0 in ((0.5, 0.0), (0.5, 0.6), (0.5, 0.95), (0.4, 0.3), (0.5, 1.0 - 1e-9)):
        pr = np.array([math.exp(_exact_ll(np.array(z), ts, p0, rho0)) for z in seqs])
        assert abs(pr.sum() - 1) < 1e-9
        assert float(pr @ vals) <= 1.0 + 1e-9


@pytest.mark.parametrize("variant", ["plugin", "plugnear"])
def test_plugin_numerator_is_a_probability(variant):
    """Single start, no started mixture: sum_z Q(z) = 1 for the beta-mixed numerator."""
    n = 10
    ts = np.cumsum([0, 2, 1, 1, 3, 1, 2, 1, 1, 2])
    tot = 0.0
    for z in itertools.product((0, 1), repeat=n):
        ev = _mk({**VARIANTS[variant], "rho_every": 1}, started=False)
        _run_seq(ev, np.array(z), ts)
        _c0, a0, p0 = ev.starts[0]
        num = fam_a._lse(
            np.array(
                [math.log(0.5) + fam_a._lse(ev.alogpi + ev.acum - a0), math.log(0.5) + ev.pcum - p0]
            )
        )
        tot += math.exp(num)
    assert abs(tot - 1.0) < 1e-9


@pytest.mark.parametrize("variant", list(VARIANTS))
def test_markov_variant_denominator_dominates_null(variant):
    rng = np.random.default_rng(1)
    for p0, rho0 in ((0.5, 0.0), (0.5, 0.9), (0.4, 0.5)):
        z, ts = _queried(rng, 60, p0, rho0)
        ev = _mk(VARIANTS[variant], started=False)
        _run_seq(ev, z, ts)
        ub = float(ev.cum.max())
        for p in np.linspace(0.01, 0.5, 15):
            for rho in np.r_[0.0, np.linspace(0.05, 0.999, 15)]:
                assert _exact_ll(z, ts, p, rho) <= ub + 1e-9


def _queried(rng, n, p, rho, dis=0.2):
    s = rng.random() < p
    z, ts, t = [], [], 0
    while len(z) < n:
        t += 1
        if rng.random() >= rho:
            s = rng.random() < p
        if rng.random() < dis:
            z.append(int(s))
            ts.append(t)
    return np.array(z), np.array(ts)


def test_near_prior_normalised():
    ev = _mk({"p_tilt": 1.0})
    assert abs(np.exp(ev.alogpi).sum() - 1) < 1e-12


# ------------------------------------------------------------------ R4: combination rules
class _Fake:
    def __init__(self, v):
        self.value = v


def _gate(evidence):
    pol = fam_r._g("g", evidence=evidence)(
        500, 50, 5.0, 0.05, 0.05, 5, lambda n: policy_rng(0, 0, n)
    )
    return pol


def test_both_requires_both_latched_and_comb_averages():
    g = _gate("both")
    thr = 2.0 / g.alpha
    g.ev = {"cmi": (_Fake(thr + 1), _Fake(0.0)), "mk": (fam_r.CondMeanEP(), fam_r.CondMeanEP())}
    g.ev["mk"][0].logw[:] = 0.0
    g._decide()
    assert g.latched["cmi"] and not g.latched["mk"] and not g.cert_ok
    g.ev["cmi"] = (_Fake(0.5), _Fake(0.0))  # cmi drops back; its crossing stays latched
    g.ev["mk"] = (_Fake(thr * 2), _Fake(0.0))
    g._decide()
    assert g.cert_ok
    c = _gate("comb")
    c.ev = {"cmi": (_Fake(thr * 1.5), _Fake(0.0)), "mk": (_Fake(thr * 0.4), _Fake(0.0))}
    c._decide()
    assert not c.cert_ok  # mean .95 thr
    c.ev["mk"] = (_Fake(thr * 0.6), _Fake(0.0))
    c._decide()
    assert c.cert_ok


# ------------------------------------------------------------------ R5: economic value
def test_econ_value_penalty_and_persistence_inflation():
    g = _gate("econ")
    g.ez = [1] * 30 + [0] * 10
    g.et = list(range(0, 200, 5))
    g.n_dis = 40
    v0, u0 = g.econ_value(200)
    g.rho_hat = 0.9
    v1, u1 = g.econ_value(200)
    assert v1 < v0 and u1 > u0  # dependence widens the interval
    g.kappa = 0.0
    v2, u2 = g.econ_value(200)
    assert abs(v2 - u2) < 1e-12 and v2 > v0
