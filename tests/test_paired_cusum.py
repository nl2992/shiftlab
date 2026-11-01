import numpy as np

from shiftlab.sota_search.paired_cusum import paired_cusum


def test_pending_requests_count_and_no_early_label():
    stream = {"loss": np.ones((1, 10)), "candidate_loss": np.zeros((1, 10))}
    r = paired_cusum(stream, [0], [0.5], frac=1, budget=10, delay=3, margin=0.1, switch_cost=0)
    assert r["first"][0, 0] == 3
    assert r["labels"][0, 0] == 3
    assert r["decision_cost"][0, 0] == 3


def test_no_budget_no_signal():
    stream = {"loss": np.ones((2, 10)), "candidate_loss": np.zeros((2, 10))}
    r = paired_cusum(stream, [0, 0.1], [0.5, 0.5], budget=0)
    assert np.all(r["maximum"] == 0)
    assert np.all(r["first"] == 10)
    assert np.all(r["labels"] == 0)


def test_cusum_matches_scalar_recurrence():
    gains = np.array([0.8, -0.4, 0.2, -0.9, 0.5])
    stream = {
        "loss": np.maximum(gains, 0)[None, :],
        "candidate_loss": np.maximum(-gains, 0)[None, :],
    }
    r = paired_cusum(stream, [0.1], frac=1, budget=5, delay=1, margin=0, switch_cost=0)
    value, maximum = 0, 0
    for gain in gains[:-1]:
        value = max(0, value + gain - 0.1)
        maximum = max(value, maximum)
    np.testing.assert_allclose(r["maximum"], maximum)
