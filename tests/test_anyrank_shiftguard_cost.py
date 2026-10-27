"""Regression checks for AnyRank's transfer of binary decision costs."""

from __future__ import annotations

import numpy as np

from scripts.reproduce_anyrank_shiftguard import _binary_decision_cost
from shiftlab.dive.budgeted_promotion import _binary_costs


def test_anyrank_cost_mapping_matches_canonical_binary_costs() -> None:
    actions = np.asarray([1, 0])
    outcomes = np.asarray([0, 1])

    actual = _binary_decision_cost(actions[:, None], outcomes[None, :])
    expected = _binary_costs(actions[:, None], outcomes[None, :], fn=5.0, fp=1.0)

    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(actual, [[1.0, 0.0], [0.0, 5.0]])
