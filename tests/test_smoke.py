import numpy as np

from shiftlab.data import make_stream
from shiftlab.methods import weighted_conformal_quantile
from shiftlab.metrics import interval_coverage


def test_stream_reproducible():
    a = make_stream(seed=1)
    b = make_stream(seed=1)
    assert np.array_equal(a.X, b.X) and np.array_equal(a.y, b.y)
    assert a.regime.sum() == 1500


def test_conformal_quantile():
    assert weighted_conformal_quantile(np.arange(1, 10), alpha=0.2) == 8


def test_interval_coverage():
    assert interval_coverage(np.array([0, 2]), np.array([-1, -1]), np.array([1, 1])) == 0.5


def test_experiment_imports():
    from experiments.paper1_decision_drift import run as one
    from experiments.paper2_conformal_shift import run as two
    from experiments.paper3_cost_aware_adapt import run as three

    assert one(seed=1)["post_mse"] >= 0
    assert 0 <= two(seed=1)["fixed_post_coverage"] <= 1
    assert three(seed=1, policy="none")["num_retrains"] == 0
