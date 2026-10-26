import numpy as np
import torch

from scripts.evaluate_crsp_monitor_comparison import (
    _auc_ap,
    _daily_costs,
    _mmd_windows,
    _turnover_in_path,
    _two_way_block_interval,
)


def test_turnover_is_aligned_by_permno_and_includes_entry_and_exit():
    permno = np.array([1, 1, 2, 1, 2])
    dates = np.array([1, 2, 1, 3, 2])
    actions = np.array([1, 0, 1, 1, 0], dtype=np.int8)
    turnover = _turnover_in_path(actions, permno, dates)
    # PERMNO 1 path is 1,0,1: entry + two changes + exit; PERMNO 2 is 1,0.
    assert turnover.tolist() == [1.0, 1.0, 1.0, 2.0, 1.0]


def test_daily_costs_preserve_event_weighting_and_cost_sensitivity():
    y = np.array([0.02, -0.01, 0.03])
    candidate = np.array([1, 0, 1])
    reference = np.array([0, 1, 1])
    cand_turn = np.array([1.0, 1.0, 2.0])
    ref_turn = np.array([0.0, 1.0, 2.0])
    idx = np.array([0, 0, 1])
    sums, counts, diff = _daily_costs(y, candidate, reference, cand_turn, ref_turn, idx, 2, 5)
    assert counts.tolist() == [2.0, 1.0]
    np.testing.assert_allclose(sums, [diff[:2].sum(), diff[2]])
    assert diff[0] < 0


def test_two_way_bootstrap_runs_and_returns_ordered_interval():
    values = np.arange(30, dtype=np.float32).reshape(6, 5) / 100
    counts = np.ones_like(values)
    interval = _two_way_block_interval(
        values,
        counts,
        seed=7,
        device=torch.device("cpu"),
        replicates=50,
    )
    assert len(interval) == 2
    assert interval[0] <= interval[1]


def test_auc_and_average_precision_rank_positive_harm_scores():
    auc, ap, n_positive = _auc_ap(np.array([0.1, 0.9, 0.2, 0.8]), np.array([0, 1, 0, 1]))
    assert auc == 1.0
    assert ap == 1.0
    assert n_positive == 2


def test_mmd_windows_use_first_window_as_reference_and_skip_it_as_null_window():
    rng = np.random.default_rng(3)
    dates = np.repeat(np.arange(60, dtype=np.int32), 4)
    x = rng.normal(size=(len(dates), 3))
    scores, right_edges = _mmd_windows(x, dates, window=20, rng=rng, sample_size=32)
    assert scores.shape == (3,)
    assert right_edges.tolist() == [19, 39, 59]
