from fractions import Fraction as F

from shiftlab.paper3.payback.exact import (
    brute_force_min_error_sum,
    crossing_probability,
    crossing_probability_exact_fraction,
    history_laws,
    hoeffding_naive_trigger,
    min_error_sum,
    mixture_rho,
    mixture_trigger,
    payback_of,
    reversal_world_means,
    wald_naive_trigger,
)


def _rule(
    released,
):  # adaptive: query unless the last released label was -1 and we already hold >=2
    return not (len(released) >= 2 and released[-1][1] == -1)


def test_reversal_impossibility_exact():
    tau, d, h, k = 5, 2, 6, F(1)
    base, delta = F(1, 4), F(1, 2)
    plus, minus = reversal_world_means(tau, d, base, delta, diverge_from=tau - d + 1)
    assert payback_of(plus, tau, h, k) > 0 > payback_of(minus, tau, h, k)
    lp = history_laws(tau, d, plus, _rule)
    lm = history_laws(tau, d, minus, _rule)
    assert lp == lm  # identical history law
    assert min_error_sum(lp, lm) == 1  # type I + type II >= 1 for EVERY rule
    assert brute_force_min_error_sum(lp, lm) == 1


def test_one_observed_label_breaks_the_impossibility_exactly():
    tau, d = 5, 2
    plus, minus = reversal_world_means(
        tau, d, F(1, 4), F(1, 2), diverge_from=tau - d
    )  # label tau-d differs
    lp, lm = history_laws(tau, d, plus, lambda r: True), history_laws(tau, d, minus, lambda r: True)
    e = min_error_sum(lp, lm)
    assert e < 1
    assert brute_force_min_error_sum(lp, lm) == e


def test_naive_optional_continuation_counterexample_numbers():
    alpha, mu0 = 0.05, 0.1  # k/h = 0.1: the world sits exactly on the null boundary
    one_look = crossing_probability(
        hoeffding_naive_trigger(mu0, alpha), 100, mu0
    ) - crossing_probability(hoeffding_naive_trigger(mu0, alpha), 99, mu0)
    p100 = crossing_probability(hoeffding_naive_trigger(mu0, alpha), 100, mu0)
    p1000 = crossing_probability(hoeffding_naive_trigger(mu0, alpha), 1000, mu0)
    w100 = crossing_probability(wald_naive_trigger(mu0, 1.645), 100, mu0)
    assert p100 > alpha  # 0.0501: already invalid at 100 looks
    assert p1000 > 1.8 * alpha
    assert w100 > 5 * alpha
    assert one_look < alpha


def test_float_dp_matches_exact_rational():
    trig = hoeffding_naive_trigger(0.1, 0.05)
    a = crossing_probability(trig, 40, 0.1)
    b = crossing_probability_exact_fraction(trig, 40, F(1, 10))
    assert abs(a - float(b)) < 1e-12


def test_mixture_cs_valid_exactly():
    for alpha in (0.2, 0.05, 0.01):
        for mu0 in (0.0, 0.1, 0.5):
            for m_star in (20, 200):
                trig = mixture_trigger(mu0, alpha, mixture_rho(alpha, m_star))
                p = crossing_probability(trig, 1500, mu0)
                assert p <= alpha, (alpha, mu0, m_star, p)
