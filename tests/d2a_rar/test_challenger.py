"""Tests for the Challenger PAPER_RECONSTRUCTION (arXiv 2512.18390)."""

import numpy as np
import pytest

from shiftlab.sota.challenger import (
    CONTINUE,
    DISCARD,
    SWITCH,
    Economics,
    gse_decide,
    integer_oracle_epoch,
    lse_decide,
    oracle_value,
    ose_decide,
    run_gse,
    run_lse,
    run_ose,
    stopping_epoch_thm31,
    t_dagger_asymptotic,
)
from shiftlab.sota.challenger.values import Economics as E2

assert E2 is Economics


def curve(N, g_star=0.10, g0=0.9, alpha=0.5):
    return g_star - g0 * np.asarray(N, float) ** (-alpha)


def test_value_formula_matches_paper_identity():
    e = Economics(n=100, T=1000, c=0.002, c_s=5.0)
    for t, G in [(10, 0.03), (500, -0.01), (999, 0.2)]:
        vs = -e.c * e.n * e.T - e.c_s + e.n * (e.T - t) * G  # paper Eq. 2
        assert e.v_switch(t, G) == pytest.approx(vs)
        assert e.v_discard(t) == pytest.approx(-e.c * e.n * t)
        assert e.delta_v(t, G) == pytest.approx(-e.c_s + e.n * (e.T - t) * (G - e.c))


def test_discounted_reduces_to_undiscounted_at_beta_one_and_is_finite_below():
    a = Economics(n=10, T=50, c=0.1, c_s=2.0, beta=1.0)
    b = Economics(n=10, T=50, c=0.1, c_s=2.0, beta=0.999999)
    assert a.delta_v(7, 0.4) == pytest.approx(b.delta_v(7, 0.4), rel=1e-3)
    d = Economics(n=10, T=50, c=0.1, c_s=2.0, beta=0.9)
    assert np.isfinite(d.v_switch(7, 0.4)) and d.v_switch(7, 0.4) != a.v_switch(7, 0.4)


def test_thm31_stopping_rule_equals_bruteforce_oracle_on_unit_grid():
    # Native analytic result: with T_D = T, the stopping rule picks argmax_t Phi(t); feasible switch iff max Phi >= cT + c_s/n.
    for T, alpha, g0 in [(2000, 0.5, 0.9), (5000, 1.0, 0.5), (20000, 0.3, 0.8)]:
        n = 10
        e = Economics(n=n, T=T, c=0.0005, c_s=0.0)
        t = np.arange(1, T + 1)
        G = curve(n * t, 0.10, g0, alpha)
        k_rule = stopping_epoch_thm31(e, t, G)
        k_orc = integer_oracle_epoch(e, t, G)
        assert k_orc is not None
        assert k_rule == k_orc
        phi = (T - t) * G
        assert (phi.max() >= e.c * T + e.c_s / n) == (oracle_value(e, t, G)[0] > 0)


def test_prop32_asymptotic_scaling_ratio_tends_to_one():
    n, g_star, g0, alpha = 10, 0.10, 0.9, 0.5
    ratios = []
    for T in [10**3, 10**4, 10**5, 10**6]:
        e = Economics(n=n, T=T, c=0.0, c_s=0.0)
        t = np.arange(1, T)
        G = curve(n * t, g_star, g0, alpha)
        k = integer_oracle_epoch(e, t, G)
        ratios.append(t[k] / t_dagger_asymptotic(T, n, g_star, g0, alpha))
    assert abs(ratios[-1] - 1) < abs(ratios[0] - 1) + 1e-9
    assert abs(ratios[-1] - 1) < 0.05
    # exponent: oracle time scales ~ T^(1/(1+alpha))
    slope = np.polyfit(
        np.log([1e3, 1e4, 1e5, 1e6]), np.log(ratios) + np.log([1e3, 1e4, 1e5, 1e6]) / (1 + alpha), 1
    )[0]
    assert slope == pytest.approx(1 / (1 + alpha), abs=0.03)


def test_infeasible_switch_is_discarded_by_oracle():
    e = Economics(n=10, T=100, c=1.0, c_s=0.0)  # per-sample hurdle far above g*
    t = np.arange(1, 100)
    G = curve(10 * t)
    assert oracle_value(e, t, G) == (0.0, None)


def test_ose_sign_rule():
    e = Economics(n=10, T=100, c=0.01, c_s=3.0)
    assert ose_decide(e, 20, 0.5) == SWITCH
    assert ose_decide(e, 20, 0.0) == DISCARD
    assert ose_decide(e, 99, 0.03) == DISCARD  # one step left cannot recoup c_s


def test_gse_rules_cases():
    e = Economics(n=100, T=1000, c=0.01, c_s=1.0)
    # strong positive: V^LB_switch > 0 -> switch right away
    assert gse_decide(e, 100, 0.5, 0.1, 0.5, last=False) == SWITCH
    # V^UB_switch < 0 and DeltaV^LB <= 0 -> discard (hopelessly negative gap)
    assert gse_decide(e, 100, -0.5, 0.1, 0.5, last=False) == DISCARD
    # ambiguous (huge confidence width) -> continue
    assert gse_decide(e, 100, 0.0, 50.0, 0.5, last=False) == CONTINUE
    # last epoch falls back to DeltaV sign
    assert gse_decide(e, 100, 0.0, 50.0, 0.5, last=True) == DISCARD
    assert gse_decide(e, 100, 0.2, 50.0, 0.5, last=True) == SWITCH


def test_gse_larger_gamma_never_switches_earlier():
    n, T = 100, 4000
    e = Economics(n=n, T=T, c=0.002, c_s=0.0)
    ep = [5, 10, 20, 40, 80, 160, 320, 640]
    g = curve(np.array(ep) * n, 0.10, 0.9, 0.5)
    ks = [run_gse(e, ep, g, gamma).epoch_idx for gamma in (0.0, 0.5, 2.0)]
    assert ks == sorted(ks)


def test_lse_is_causal_no_peeking_at_future_gaps():
    e = Economics(n=100, T=4000, c=0.002)
    ep = [5, 10, 20, 40, 80, 160]
    g = list(curve(np.array(ep) * 100, 0.10, 0.9, 0.5))
    base = [lse_decide(e, ep, g, k, variant="LSEc") for k in range(3)]
    g2 = g[:3] + [99.0, -99.0, 5.0]
    assert base == [lse_decide(e, ep, g2, k, variant="LSEc") for k in range(3)]


def test_lse_noiseless_stops_when_further_wait_cannot_pay_and_matches_oracle_sign():
    n, T = 100, 4000
    e = Economics(n=n, T=T, c=0.002, c_s=0.0)
    ep = [5, 10, 20, 40, 80, 160, 320, 640, 1280]
    g = curve(np.array(ep) * n, 0.10, 0.9, 0.5)
    out = run_lse(e, ep, g, variant="LSE")
    assert out.decision == (SWITCH if oracle_value(e, ep, g)[1] is not None else DISCARD)
    assert out.epoch_idx < len(ep) - 1  # stopped early, before the last epoch


def test_lsec_slope_is_at_least_two_point_lse_slope():
    # Remark 4.3: confidence-adjusted slope >= unadjusted two-point slope.
    from shiftlab.sota.challenger.algorithms import _lse_slope

    e = Economics(n=100, T=4000, c=0.002)
    ep = [5, 10, 20, 40]
    for g in ([0.01, 0.03, 0.05, 0.06], [0.05, 0.04, 0.045, 0.03]):
        for k in range(1, 4):
            sc = _lse_slope(e, ep, g[: k + 1], k, variant="LSEc", gamma=0.1, rho=0.5, w=2)
            su = _lse_slope(e, ep, g[: k + 1], k, variant="LSE", gamma=0.1, rho=0.5, w=2)
            assert sc >= su - 1e-12


def test_run_ose_and_degenerate_last_epoch():
    e = Economics(n=10, T=100, c=0.01)
    ep = [10, 50]
    g = [0.3, 0.3]
    assert run_ose(e, ep, g, 0).decision == SWITCH
    assert run_gse(e, ep[:1], g[:1], 0.1).epoch_idx == 0
    assert lse_decide(e, ep, g, 1) in (SWITCH, DISCARD)
