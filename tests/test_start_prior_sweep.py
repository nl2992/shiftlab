import numpy as np
import pytest

from shiftlab.dive.delayed_calibration import _restart_log_e_values
from shiftlab.dive.eprocess import StartedMixtureEProcess
from shiftlab.dive.start_prior_sweep import (
    PRIOR_SHAPES,
    StartPriorSweepConfig,
    beta_start_weights,
    run_start_prior_sweep,
)


def test_beta_priors_have_the_expected_start_time_order_and_normalization():
    early = beta_start_weights(*PRIOR_SHAPES["early_beta_1_2"])
    late = beta_start_weights(*PRIOR_SHAPES["late_beta_2_1"])
    center = beta_start_weights(*PRIOR_SHAPES["center_beta_2_2"])
    edge = beta_start_weights(*PRIOR_SHAPES["edge_beta_half_half"])
    assert np.isclose(sum(early), 1)
    assert np.isclose(sum(late), 1)
    assert early[0] > early[-1]
    assert late[-1] > late[0]
    assert center[3] > center[0]
    assert edge[0] > edge[3]
    assert np.all(np.asarray([early, late, center, edge]) > 0)


def test_vectorized_weighted_start_path_matches_online_process():
    values = np.asarray([0.4, -0.2, 0.5, 0.1, -0.1, 0.6, -0.3])
    starts = (0, 2, 5)
    weights = (0.6, 0.3, 0.1)
    vectorized = _restart_log_e_values(values, bound=1.0, starts=starts, start_weights=weights)
    online = StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=starts, weights=weights)
    for index, value in enumerate(values):
        online.update(float(value))
        assert vectorized[index] == pytest.approx(online.log_e_value)


def test_small_start_prior_sweep_writes_paired_development_artifacts(tmp_path):
    config = StartPriorSweepConfig(
        seeds=2,
        seed_offset=73,
        n_events=120,
        query_rates=(0.5,),
        harm_onsets=(0.5,),
        harm_increases=(0.12,),
        device="cpu",
    )
    frame, ranking, manifest = run_start_prior_sweep(tmp_path, config)
    assert len(frame) == 2 * 6
    assert len(ranking) == 6
    assert manifest["resolved_devices"] == ["cpu"]
    assert manifest["selected_prior_for_fresh_validation"] in set(ranking.method)
    assert (tmp_path / "start_prior_development.parquet").is_file()
    assert (tmp_path / "cell_summary.csv").is_file()
    assert (tmp_path / "prior_ranking.csv").is_file()
    assert (tmp_path / "results.md").is_file()
