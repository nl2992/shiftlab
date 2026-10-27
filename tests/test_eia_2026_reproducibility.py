from __future__ import annotations

import pandas as pd
import pytest

from scripts.verify_eia_2026_reproducibility import compare_summary_frames


def test_summary_reproduction_ignores_only_machine_dependent_fit_time():
    expected = pd.DataFrame(
        {"policy": ["frozen", "weekly"], "rmse": [2.0, 1.5], "fit_seconds": [0.2, 0.4]}
    )
    replay = expected.copy()
    replay["fit_seconds"] = [0.8, 0.9]

    assert compare_summary_frames(expected, replay) == pytest.approx(0.6)


def test_summary_reproduction_rejects_metric_difference():
    expected = pd.DataFrame({"policy": ["weekly"], "rmse": [1.5], "fit_seconds": [0.4]})
    replay = expected.copy()
    replay.loc[0, "rmse"] = 1.6

    with pytest.raises(AssertionError):
        compare_summary_frames(expected, replay)


def test_summary_reproduction_requires_positive_finite_runtime():
    expected = pd.DataFrame({"policy": ["weekly"], "rmse": [1.5], "fit_seconds": [0.4]})
    replay = expected.copy()
    replay.loc[0, "fit_seconds"] = float("nan")

    with pytest.raises(ValueError, match="finite and positive"):
        compare_summary_frames(expected, replay)
