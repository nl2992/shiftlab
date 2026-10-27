import numpy as np
import pytest

from scripts.evaluate_upf_eia_frontier import _exact_oracle


def test_oracle_schedule_starts_after_initial_offline_model():
    performance = np.full((5, 5), np.nan)
    performance[1, 2:] = 0.5
    performance[2, 2:] = [0.1, 0.9, 0.9]
    performance[3, 3:] = [0.1, 0.9]
    performance[4, 4] = 0.1

    schedule, objective = _exact_oracle(
        performance,
        alpha=0.0,
        initial_model=1,
    )

    assert schedule == (True, True, True)
    assert objective == pytest.approx(0.3)


def test_oracle_can_keep_initial_model_when_updates_cost_more():
    performance = np.full((5, 5), np.nan)
    performance[1, 2:] = 0.2
    performance[2, 2:] = 0.19
    performance[3, 3:] = 0.19
    performance[4, 4] = 0.19

    schedule, objective = _exact_oracle(
        performance,
        alpha=1.0,
        initial_model=1,
    )

    assert schedule == (False, False, False)
    assert objective == pytest.approx(0.6)
