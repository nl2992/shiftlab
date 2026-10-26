import numpy as np

from scripts.replay_crsp_exchange_stratified_monitors import (
    ALPHA,
    BOUND,
    EXCHANGES,
    _future_harm_labels,
    _score_strata,
)
from shiftlab.dive.eprocess import BoundedMeanEProcess, PredictableStartedMixtureEProcess


def test_stratum_paths_match_scalar_eprocesses_and_equal_weight_mixture():
    daily = np.full((len(EXCHANGES), 32), np.nan)
    daily[0] = np.linspace(-0.01, 0.02, 32)
    daily[1, ::2] = 0.015
    daily[2, 3:] = -0.005

    paths, mixture = _score_strata(daily)
    starts = tuple(round(index * daily.shape[1] / 8) for index in range(8))
    for group in range(len(EXCHANGES)):
        fixed = BoundedMeanEProcess(bound=BOUND, alpha=ALPHA)
        restarted = PredictableStartedMixtureEProcess(alpha=ALPHA, starts=starts)
        for date, value in enumerate(daily[group]):
            if np.isfinite(value):
                fixed_log = fixed.update(float(value))
                started_log = restarted.update(float(value), bound=BOUND)
            else:
                fixed_log = fixed.log_e_value
                started_log = restarted.update(0.0, bound=BOUND)
            assert np.isclose(paths["fixed_stake_mixture"][group, date], fixed_log)
            assert np.isclose(paths["uniform_eight_start_mixture"][group, date], started_log)

    for method, group_paths in paths.items():
        assert np.allclose(
            mixture[method],
            np.logaddexp.reduce(group_paths - np.log(len(EXCHANGES)), axis=0),
        )


def test_future_harm_labels_use_only_strictly_later_dates():
    daily = np.zeros((len(EXCHANGES), 12), dtype=float)
    daily[0, 1:7] = 0.2
    daily[0, 0] = -0.2
    labels = _future_harm_labels(daily, horizon=10)
    assert labels[0, 0] == 1.0
    assert np.isnan(labels[0, -1])
