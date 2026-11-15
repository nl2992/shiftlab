import numpy as np
import pytest

from shiftlab.paper3.riskbudget import BennettMixture


def test_d_zero_and_delta_zero():
    assert BennettMixture(0.05, 0.5).D(0) == 0.0
    b0 = BennettMixture(0.0, 1.0)
    assert b0.D(0) == 0.0
    with pytest.raises(ValueError):
        b0.D(1.0)
    with pytest.raises(ValueError):
        BennettMixture(0.0, 0.5)


@pytest.mark.parametrize("pi_min", [1.0, 0.5, 0.25, 0.1])
@pytest.mark.parametrize("delta", [0.01, 0.05, 0.2])
def test_d_monotone_and_close_to_gaussian(pi_min, delta):
    bm = BennettMixture(delta, pi_min)
    vs = np.linspace(0, 600, 3001)
    d = np.array([bm.D(v) for v in vs])
    assert np.all(np.diff(d) >= 0) and d[0] == 0.0
    # near the sqrt(2 V ln(m/delta)) Gaussian rate (m = grid size) for moderate V, pi_min >= .25
    if pi_min >= 0.25:
        for v in (50.0, 200.0, 500.0):
            g = np.sqrt(2 * v * np.log(len(bm.lams) / delta))
            assert g <= bm.D(v) <= 1.25 * g


def _crossing_rate(x, pi, delta, reps, rng):
    bm = BennettMixture(delta, pi)
    n = len(x)
    q = rng.random((reps, n)) < pi
    M = np.cumsum(x[None, :] * (1.0 - q / pi), axis=1)
    V = np.arange(1, n + 1) * (1.0 / pi - 1.0)
    Dv = np.array([bm.D(v) for v in V])
    return float(np.mean(np.any(M > Dv[None, :], axis=1)))


@pytest.mark.parametrize("delta", [0.05, 0.1])
@pytest.mark.parametrize("pi", [0.25, 0.5])
def test_lemma1_monte_carlo(delta, pi):
    n, reps = 400, 4000
    rng = np.random.default_rng(123)
    seqs = {
        "plus": np.ones(n),
        "minus": -np.ones(n),
        "alt": np.where(np.arange(n) % 2 == 0, 1.0, -1.0),
        "rand": rng.uniform(-1, 1, n),
        "half_then_minus": np.r_[np.ones(n // 2), -np.ones(n - n // 2)],
    }
    tol = 3 * np.sqrt(delta * (1 - delta) / reps)
    for name, x in seqs.items():
        rate = _crossing_rate(x, pi, delta, reps, rng)
        assert rate <= delta + tol, f"{name} pi={pi} delta={delta}: crossing rate {rate:.4f}"
