import numpy as np
import pytest

from scripts.reproduce_timans_risk_monitor_paired_cost import _timans_logs
from shiftlab.dive.comparison_betting_engines import replay_engine
from shiftlab.dive.eprocess import (
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableVarianceAdaptiveEProcess,
)
from shiftlab.dive.predictable_bound_replay import DEFAULT_STAKES, replay_mixture_log_e


def test_fixed08_matches_existing_default_mixture_replay():
    values = np.array([0.1, -0.2, 0.4, -0.3, 0.0])
    bounds = np.array([0.5, 0.8, 0.7, 0.6, 0.9])
    np.testing.assert_array_equal(
        replay_engine(values, bounds, "fixed08"),
        replay_mixture_log_e(values, bounds, alpha=0.05),
    )


def test_fixed1_matches_existing_replay_with_default_stakes_plus_one():
    values = np.array([0.5, -0.6, 0.25, 0.0])
    bounds = 1.0
    np.testing.assert_array_equal(
        replay_engine(values, bounds, "fixed1"),
        replay_mixture_log_e(values, bounds, alpha=0.05, stakes=(*DEFAULT_STAKES, 1.0)),
    )


def test_scalar_and_vector_bounds_replay_the_same_normalized_stream():
    values = np.array([0.1, -0.25, 0.3, -0.4])
    bounds = np.array([0.5, 1.0, 0.75, 0.8])
    normalized = values / bounds
    for engine in ("fixed08", "fixed1", "plugin", "pm_eb"):
        np.testing.assert_allclose(
            replay_engine(values, bounds, engine),
            replay_engine(normalized, 1.0, engine),
        )


def test_predictable_plugin_uses_unit_normalized_scores_and_stake_cap():
    values = np.array([0.2, 0.1, 0.3, -0.2])
    bounds = np.array([0.5, 0.8, 0.75, 1.0])
    reference = PredictableVarianceAdaptiveEProcess(bound=1.0, max_stake=0.99)
    expected = np.array([reference.update(float(x)) for x in values / bounds])
    np.testing.assert_array_equal(replay_engine(values, bounds, "plugin"), expected)
    assert reference.last_stake <= 0.99


def test_pm_eb_uses_unit_normalized_scores():
    values = np.array([0.2, -0.1, 0.35, 0.05])
    bounds = np.array([0.5, 0.7, 0.8, 0.9])
    reference = PredictablePlugInEmpiricalBernsteinEProcess(bound=1.0)
    expected = np.array([reference.update(float(x)) for x in values / bounds])
    np.testing.assert_array_equal(replay_engine(values, bounds, "pm_eb"), expected)


@pytest.mark.parametrize(
    ("engine", "rule"),
    [
        ("timans_approx_grapa", "approx_grapa"),
        ("timans_grapa", "grapa"),
    ],
)
def test_timans_engines_match_existing_verified_replay(engine, rule):
    values = np.linspace(-0.8, 0.9, 137)
    bounds = np.linspace(1.0, 1.5, len(values))
    score = 0.5 + 0.5 * values / bounds
    expected = _timans_logs(score, rule=rule, epsilon=0.5, alpha=0.05, burn_in=100)
    np.testing.assert_array_equal(replay_engine(values, bounds, engine), expected)


@pytest.mark.parametrize(
    "engine",
    [
        "fixed08",
        "fixed1",
        "plugin",
        "pm_eb",
        "timans_approx_grapa",
        "timans_grapa",
    ],
)
def test_future_changes_do_not_change_replayed_prefix(engine):
    values = np.linspace(-0.5, 0.7, 140)
    bounds = np.linspace(0.8, 1.4, len(values))
    changed = values.copy()
    changed[75:] = np.linspace(0.7, -0.6, len(changed) - 75)
    original_logs = replay_engine(values, bounds, engine)
    changed_logs = replay_engine(changed, bounds, engine)
    np.testing.assert_array_equal(original_logs[:75], changed_logs[:75])


@pytest.mark.parametrize(
    ("values", "bounds", "engine", "alpha"),
    [
        ([], 1.0, "fixed08", 0.05),
        ([[0.1, 0.2]], 1.0, "fixed08", 0.05),
        ([0.1, np.nan], 1.0, "fixed08", 0.05),
        ([0.1, 0.2], [1.0], "fixed08", 0.05),
        ([0.1], 0.0, "fixed08", 0.05),
        ([0.1], np.inf, "fixed08", 0.05),
        ([1.1], 1.0, "fixed08", 0.05),
        ([0.1], 1.0, "unknown", 0.05),
        ([0.1], 1.0, "fixed08", 0.0),
        ([0.1], 1.0, "fixed08", 1.0),
    ],
)
def test_replay_engine_rejects_invalid_support_and_configuration(values, bounds, engine, alpha):
    with pytest.raises(ValueError):
        replay_engine(values, bounds, engine, alpha=alpha)
