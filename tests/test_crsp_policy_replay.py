import numpy as np
import pandas as pd
import torch

from scripts.evaluate_crsp_policy_replay import _block_interval, _ridge_predictions, _turnover


def test_turnover_charges_entries_switches_and_terminal_closes():
    frame = pd.DataFrame({"permno": [1, 1, 1, 2, 2]})
    actions = np.array([1, 1, 0, 0, 1], dtype=np.int8)
    assert _turnover(actions, frame).tolist() == [1.0, 0.0, 1.0, 0.0, 2.0]


def test_gpu_or_cpu_ridge_uses_training_only_imputation_and_returns_finite_values():
    train_x = np.array([[0.0, 2.0], [1.0, np.nan], [2.0, 6.0], [3.0, 8.0]])
    train_y = np.array([0.1, 0.2, 0.3, 0.4])
    test_x = np.array([[4.0, np.nan], [5.0, 10.0]])
    prediction, model = _ridge_predictions(train_x, train_y, test_x, device=torch.device("cpu"))
    assert prediction.shape == (2,)
    assert np.isfinite(prediction).all()
    assert "Ridge(alpha=1)" in model


def test_date_block_interval_is_reproducible():
    sums = np.arange(40, dtype=np.float64)
    counts = np.ones(40, dtype=np.float64)
    first = _block_interval(sums, counts, seed=42)
    second = _block_interval(sums, counts, seed=42)
    assert first == second
    assert first[0] < first[1]
