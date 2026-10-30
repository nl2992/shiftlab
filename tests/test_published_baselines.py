import numpy as np
import pytest

from shiftlab.sota_search.combination_screen import make_world
from shiftlab.sota_search.published_baselines import (
    active_rcps_cost,
    ppi_batch_estimate,
    pprm_batch_cost,
    pr_empirical_bernstein,
)


def test_rcps_adapter_matches_independent_scalar_recurrence():
    s = make_world("abrupt", paths=1, horizon=100, seed=2)
    q, seed, delay = 0.5, 20, 3
    out = active_rcps_cost(s, frac=q, budget=100, delay=delay, seed=seed, return_wealth=True)
    mask = np.random.default_rng(seed).random((1, 100))[0] < q
    x = s["proxy"][0] + mask / q * (s["loss"][0] - s["proxy"][0]) - s["r0"]
    bets = np.zeros(100)
    factors = np.ones(100)
    mu, square, wealth = 0.0, 0.0, 1.0
    hi = 0.5 / (s["proxy_max"] * (1 / q - 1) + s["r0"])
    for t in range(100):
        if t >= delay:
            r = t - delay
            mu += x[r]
            square += x[r] ** 2
            wealth *= factors[r]
        assert np.log(wealth) == pytest.approx(out["logwealth"][0, t], abs=1e-12)
        bets[t] = np.clip(mu / (mu + square), 0, hi) if mu + square != 0 else 0
        factors[t] = 1 + bets[t] * x[t]


def test_rcps_budget_zero_and_hidden_future_outcomes():
    s = make_world("abrupt", paths=4, horizon=80, seed=8)
    zero = active_rcps_cost(s, budget=0, return_wealth=True)
    assert np.all(zero["logwealth"] == 0)
    a = active_rcps_cost(s, budget=12, delay=5, seed=3, return_wealth=True)
    assert a["labels"].max() <= 12
    altered = {**s, "loss": s["loss"].copy()}
    altered["loss"][:, 30:] = 1 - altered["loss"][:, 30:]
    b = active_rcps_cost(altered, budget=12, delay=5, seed=3, return_wealth=True)
    np.testing.assert_array_equal(a["logwealth"][:, :35], b["logwealth"][:, :35])


def test_ppi_batch_estimator_is_exactly_unbiased_on_finite_population():
    losses = np.array([0.1, 0.8, 0.3, 0.6])
    synthetic = np.array([0.3, 0.2, 0.5, 0.9])
    for eta in (0, 0.25, 1):
        estimates = [
            ppi_batch_estimate(losses[i], synthetic[i], np.delete(synthetic, i), eta)
            for i in range(4)
        ]
        assert np.mean(estimates) == pytest.approx(losses.mean(), abs=1e-15)


@pytest.mark.parametrize("monitor", [pr_empirical_bernstein, pprm_batch_cost])
def test_published_formula_wrappers_budget_and_release(monitor):
    s = make_world("abrupt", paths=4, horizon=100, seed=3)
    a = monitor(s, budget=8, delay=5, seed=6, return_wealth=True)
    assert a["labels"].max() <= 8
    np.testing.assert_allclose(a["logwealth"][:, :5], 0, atol=1e-12)
    z = monitor(s, budget=0, delay=5, return_wealth=True)
    np.testing.assert_allclose(z["logwealth"], 0, atol=1e-12)
    change = {**s, "loss": s["loss"].copy()}
    change["loss"][:, 25:] = 1 - change["loss"][:, 25:]
    b = monitor(change, budget=8, delay=5, seed=6, return_wealth=True)
    np.testing.assert_allclose(a["logwealth"][:, :30], b["logwealth"][:, :30], atol=1e-12)
