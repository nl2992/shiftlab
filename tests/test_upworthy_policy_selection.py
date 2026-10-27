"""Tests for the fixed-horizon Upworthy policy-selection task contract."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from shiftlab.dive.upworthy_policy_selection import (
    equal_test_contrasts,
    filter_eligible_tests,
    package_text,
    select_package_indices,
    tune_and_fit,
    week_cluster_bootstrap,
)


def arm_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "created_at": [
                "2013-02-01 00:00:00",
                "2013-02-01 00:00:00",
                "2013-06-25 00:00:00",
                "2013-06-24 00:00:00",
                "2015-01-01 00:00:00",
                "2015-01-01 00:00:00",
            ],
            "clickability_test_id": ["a", "a", "b", "b", "c", "c"],
            "headline": [
                "Better headline",
                "Another story",
                "Bad date",
                "Good date",
                "Text one",
                "Text two",
            ],
            "excerpt": ["same", "same", "same", "same", "story", "story"],
            "impressions": [100, 100, 100, 100, 100, 100],
            "clicks": [20, 10, 30, 10, 15, 14],
            "test_week": [201305, 201305, 201326, 201326, 201501, 201501],
            "winner": [False, True, True, False, True, False],
            "Problem": ["false", "false", "false", "false", "true", "false"],
        }
    )


def test_risk_date_or_publisher_problem_flag_removes_entire_test() -> None:
    eligible, counts = filter_eligible_tests(arm_frame())
    assert counts == {
        "input_tests": 3,
        "risk_window_tests": 2,
        "invalid_count_tests": 0,
        "singleton_tests": 0,
        "eligible_tests": 1,
        "eligible_arms": 2,
    }
    assert eligible["clickability_test_id"].unique().tolist() == ["a"]


def test_selector_uses_text_tie_break_and_returns_one_arm_per_test() -> None:
    frame = arm_frame().iloc[:2].reset_index(drop=True)
    predictions = np.array([0.4, 0.4])
    selected = select_package_indices(frame, predictions)
    assert selected.tolist() == [1]
    assert package_text(frame)[1] < package_text(frame)[0]


def test_equal_test_contrast_compares_to_uniform_over_arms() -> None:
    frame = arm_frame().iloc[:2].reset_index(drop=True)
    predictions = np.array([0.9, 0.1])
    result = equal_test_contrasts(frame, predictions)
    assert result.loc[0, "selected_ctr"] == pytest.approx(0.2)
    assert result.loc[0, "uniform_reference_ctr"] == pytest.approx(0.15)
    assert result.loc[0, "delta_ctr"] == pytest.approx(0.05)
    assert result.loc[0, "best_arm_ctr_evaluator_only"] == pytest.approx(0.2)


def test_week_cluster_bootstrap_is_reproducible_and_needs_multiple_weeks() -> None:
    frame = pd.DataFrame(
        {
            "test_week": [1, 1, 2, 2],
            "delta_ctr": [0.1, 0.2, -0.1, 0.0],
            "selected_ctr": [0.4, 0.5, 0.2, 0.3],
            "uniform_reference_ctr": [0.3, 0.3, 0.3, 0.3],
        }
    )
    first = week_cluster_bootstrap(frame, n_bootstrap=500, seed=7)
    second = week_cluster_bootstrap(frame, n_bootstrap=500, seed=7)
    assert first == second
    assert first["week_clusters"] == 2
    with pytest.raises(ValueError, match="At least two week clusters"):
        week_cluster_bootstrap(frame.assign(test_week=1), n_bootstrap=500)


def test_grouped_cv_fit_returns_finite_package_probabilities() -> None:
    rows = []
    for test_id in range(10):
        rows.extend(
            [
                {
                    "clickability_test_id": f"t{test_id}",
                    "headline": "good news story",
                    "excerpt": "common article excerpt",
                    "clicks": 20,
                    "impressions": 100,
                    "test_week": 201401 + test_id,
                },
                {
                    "clickability_test_id": f"t{test_id}",
                    "headline": "ordinary update story",
                    "excerpt": "common article excerpt",
                    "clicks": 10,
                    "impressions": 100,
                    "test_week": 201401 + test_id,
                },
            ]
        )
    policy, scores = tune_and_fit(pd.DataFrame(rows), c_grid=(0.1, 1.0))
    predictions = policy.predict(package_text(pd.DataFrame(rows)))
    assert policy.c_value in {0.1, 1.0}
    assert set(scores) == {"0.1", "1.0"}
    assert np.isfinite(predictions).all()
    assert len(predictions) == len(rows)
