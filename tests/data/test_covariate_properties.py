import numpy as np
import pytest

from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks

PURE_COVARIATE_SCENARIOS = [
    "mean",
    "feature_variance",
    "covariance_rotation",
    "correlation",
    "mixture_weights",
    "new_component",
    "feature_tail",
    "feature_skew",
    "irrelevant",
]


def collect(scenario, *, seed=31, d=4, severity=1.0):
    config = SyntheticConfig(
        n=30000, d=d, seed=seed, scenario=scenario, chunk_size=5000, severity=severity
    )
    parts = list(generate_chunks(config))
    features = np.concatenate([np.stack(frame.features.to_numpy()) for frame, _ in parts])
    oracle = np.concatenate([frame.conditional_mean.to_numpy() for _, frame in parts])
    return features, oracle


@pytest.mark.parametrize("scenario", PURE_COVARIATE_SCENARIOS)
@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_pure_covariate_scenarios_preserve_the_specified_conditional_mean(scenario, severity):
    features, conditional_mean = collect(scenario, severity=severity)
    expected = features[:, 0] - 0.9 * features[:, 1]
    assert np.max(np.abs(conditional_mean - expected)) < 1e-10


@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_mean_and_variance_changes_match_their_analytic_moments(severity):
    mean_x, _ = collect("mean", d=2, severity=severity)
    mean_delta = np.mean(mean_x[15000:, 0]) - np.mean(mean_x[:15000, 0])
    assert abs(mean_delta - severity) < 0.06

    variance_x, _ = collect("feature_variance", d=2, severity=severity)
    before = np.var(variance_x[:15000, 0], ddof=1)
    after = np.var(variance_x[15000:, 0], ddof=1)
    assert abs(before - 1.0) < 0.05
    assert abs(after - (1 + severity) ** 2) < 0.15


@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_rotated_covariance_matches_matrix_formula_in_both_regimes(severity):
    features, _ = collect("covariance_rotation", d=2, severity=severity)
    angle = severity
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    expected = rotation @ np.diag([1.0, 4.0]) @ rotation.T
    before = np.cov(features[:15000].T)
    after = np.cov(features[15000:].T)
    assert np.max(np.abs(before - np.diag([1.0, 4.0]))) < 0.08
    assert np.max(np.abs(after - expected)) < 0.15


@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_correlation_mixture_and_new_component_match_analytic_targets(severity):
    correlated, _ = collect("correlation", d=2, severity=severity)
    expected_r = 0.9 * np.tanh(severity)
    assert abs(np.corrcoef(correlated[15000:].T)[0, 1] - expected_r) < 0.025

    mixture, _ = collect("mixture_weights", d=2, severity=severity)
    expected_mixture_mean = 4 * (0.5 + 0.4 * np.tanh(severity)) - 2
    assert abs(np.mean(mixture[15000:, 0]) - expected_mixture_mean) < 0.08

    new_component, _ = collect("new_component", d=2, severity=severity)
    expected_new_component_mean = 4 * (0.3 * np.tanh(severity))
    assert abs(np.mean(new_component[15000:, 0]) - expected_new_component_mean) < 0.08


def test_tail_and_skew_changes_match_distributional_direction():
    heavy, _ = collect("feature_tail", d=2)
    before_kurtosis = (
        np.mean((heavy[:15000, 0] - heavy[:15000, 0].mean()) ** 4) / np.var(heavy[:15000, 0]) ** 2
    )
    after_kurtosis = (
        np.mean((heavy[15000:, 0] - heavy[15000:, 0].mean()) ** 4) / np.var(heavy[15000:, 0]) ** 2
    )
    assert after_kurtosis > before_kurtosis + 0.8

    skewed, _ = collect("feature_skew", d=2)
    values = skewed[15000:, 0]
    skewness = np.mean((values - values.mean()) ** 3) / np.std(values) ** 3
    assert skewness > 1.0


def test_irrelevant_feature_moves_without_changing_oracle_function():
    features, conditional_mean = collect("irrelevant", d=4)
    assert abs(np.mean(features[15000:, -1]) - np.mean(features[:15000, -1]) - 1.0) < 0.06
    assert np.max(np.abs(conditional_mean - (features[:, 0] - 0.9 * features[:, 1]))) < 1e-10
