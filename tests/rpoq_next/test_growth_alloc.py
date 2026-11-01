import numpy as np

from shiftlab.dive.rpoq_next.growth_alloc import allocate, growth, neyman


def test_second_moment_formula_matches_simulation():
    rng = np.random.default_rng(0)
    mu, h, q, n = 0.3, 0.2, 0.25, 400_000
    y = np.clip(mu + 0.4 * rng.standard_normal(n), -1, 1)
    r_hat = np.mean((y - h) ** 2)
    mu_hat = y.mean()
    x = h + (rng.random(n) < q) * (y - h) / q
    assert abs(x.mean() - mu_hat) < 0.02
    assert abs(np.mean(x**2) - (2 * h * mu_hat - h**2 + r_hat / q)) < 0.05


def test_growth_increases_with_signal_and_is_zero_without():
    q = np.array([0.1, 0.5, 1.0])
    assert np.all(growth(0.0, 0.0, 0.2, q, 1.0) == 0)
    assert np.all(growth(0.4, 0.0, 0.2, q, 1.0) > growth(0.2, 0.0, 0.2, q, 1.0))


def test_allocations_meet_budget_and_differ_by_signal():
    mu = np.array([0.4, 0.4, 0.05, 0.05])
    r = np.array([0.2, 0.8, 0.2, 0.8])
    h = np.zeros(4)
    qg = allocate(mu, h, r, budget=2.0, bound=1.0)
    qn = neyman(r, budget=2.0)
    assert abs(qg.sum() - 2.0) < 0.25 and abs(qn.sum() - 2.0) < 1e-6
    # Neyman ignores signal: equal-r contexts get equal q. Growth-aware favours high-signal ones.
    assert qn[0] == qn[2] and qg[0] > qg[2]
