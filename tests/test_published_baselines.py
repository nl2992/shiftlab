import numpy as np
import pytest

from shiftlab.sota_search.combination_screen import make_world
from shiftlab.sota_search.published_baselines import active_rcps_cost


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
