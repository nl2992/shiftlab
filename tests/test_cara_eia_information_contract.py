from pathlib import Path

import numpy as np
import pytest
import torch


@pytest.fixture
def cara_runner(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import evaluate_cara_eia_frontier

    return evaluate_cara_eia_frontier


def test_cara_current_batch_uses_only_matured_prefix_rows(cara_runner) -> None:
    data = {
        "prefixes": [np.array([0]), np.array([1, 2])],
        "evaluations": [np.array([1]), np.array([3])],
        "event": np.array([1.0, 2.0, 3.0, 4.0]),
        "label_event": np.array([1.0, 2.0, 10.0, 4.0]),
        "y": np.array([0.0, 0.0, 0.0, 0.0]),
    }

    selected = cara_runner._maturity_indices(data, period=1, delay_hours=0)

    assert selected.tolist() == [1]


def test_cara_qdm_is_bounded_and_uses_fixed_feature_scaling(cara_runner) -> None:
    model = {
        "median": np.zeros(4),
        "mean": np.zeros(4),
        "scale": np.ones(4),
        "coefficient": np.zeros(4),
        "intercept": 0.0,
    }
    x = np.zeros((20, 4), dtype=np.float64)
    y = np.full(20, 0.5, dtype=np.float64)

    result = cara_runner._qdm(
        model,
        x,
        y,
        x,
        scale=1.0,
        scaler=model,
        device=torch.device("cpu"),
    )

    assert result == 0.5
