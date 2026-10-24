import numpy as np

from shiftlab.dive.risk_proxy_stress_grid import _paired_bootstrap


def test_paired_seed_bootstrap_is_deterministic_and_ordered():
    values = np.asarray([0.1, 0.2, 0.3, 0.4])
    first = _paired_bootstrap(values, seed=91)
    second = _paired_bootstrap(values, seed=91)
    assert first == second
    assert first[0] <= values.mean() <= first[1]
