import pytest

from shiftlab.dive.prediction_powered_evalues import prediction_powered_factor


def factor_mean(score, proxy, q, stake):
    a = prediction_powered_factor(
        proxy_factor=1 + stake * proxy, queried=True, propensity=q,
        lower=1 - stake, upper=1 + stake, observed_factor=1 + stake * score,
    )
    b = prediction_powered_factor(
        proxy_factor=1 + stake * proxy, queried=False, propensity=q,
        lower=1 - stake, upper=1 + stake,
    )
    return q * a + (1 - q) * b


def test_context_queries_and_correlated_proxies_preserve_fixed_stake_mean():
    positive = factor_mean(1, -0.8, 0.8, 0.1)
    negative = factor_mean(-1, 0.7, 0.2, 0.1)
    assert (positive + negative) / 2 == pytest.approx(1)


def test_context_stakes_need_stronger_null_than_marginal_mean_zero():
    positive = factor_mean(1, 0, 1, 0.2)
    negative = factor_mean(-1, 0, 1, 0.01)
    assert (positive + negative) / 2 > 1
