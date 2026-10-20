import numpy as np
import pytest
from scipy.special import expit

from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks


@pytest.mark.parametrize(
    ("scenario", "base_logit"),
    [("prior_shift", 0.0), ("imbalance", np.log(0.1 / 0.9))],
)
def test_class_prior_shift_preserves_class_conditional_feature_law(scenario, base_logit):
    observed_prior, negative_means, positive_means = [], [], []
    for seed in [11, 23, 37, 53, 71]:
        config = SyntheticConfig(n=30000, scenario=scenario, seed=seed, severity=1)
        frames = list(generate_chunks(config))
        X = np.concatenate([np.stack(frame.features.to_numpy()) for frame, _ in frames])
        y = np.concatenate([frame.target.to_numpy() for frame, _ in frames])
        weight = np.concatenate([oracle.weight.to_numpy() for _, oracle in frames])
        shifted = weight == 1
        observed_prior.append(float(y[shifted].mean()))
        negative_means.append(float(X[shifted & (y == 0), 0].mean()))
        positive_means.append(float(X[shifted & (y == 1), 0].mean()))
    expected_prior = expit(base_logit + 1)
    assert abs(np.mean(observed_prior) - expected_prior) < 0.015
    assert abs(np.mean(negative_means) + 1) < 0.05
    assert abs(np.mean(positive_means) - 1) < 0.05


def test_symmetric_label_corruption_matches_independent_posterior_formula():
    config = SyntheticConfig(n=50000, scenario="label_corruption", seed=91, severity=1)
    frames = list(generate_chunks(config))
    X = np.concatenate([np.stack(frame.features.to_numpy()) for frame, _ in frames])
    y = np.concatenate([frame.target.to_numpy() for frame, _ in frames])
    probability = np.concatenate([oracle.probability_positive.to_numpy() for _, oracle in frames])
    weight = np.concatenate([oracle.weight.to_numpy() for _, oracle in frames])
    rate = np.minimum(0.45, config.severity * weight / 5)
    clean = expit(X[:, 0] + X[:, 1] ** 2 - 1)
    expected = rate + (1 - 2 * rate) * clean
    assert np.max(np.abs(probability - expected)) < 1e-12
    for regime in [0, 1]:
        selected = weight == regime
        assert abs(y[selected].mean() - expected[selected].mean()) < 4 * np.sqrt(
            np.mean(expected[selected] * (1 - expected[selected])) / selected.sum()
        )


@pytest.mark.parametrize("scenario", ["target_level", "target_variance", "tail_frequency"])
@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_regression_target_shifts_match_independent_conditional_moments(scenario, severity):
    regimes = [0] if severity == 0 else [0, 1]
    mean_errors, variance_errors = ({regime: [] for regime in regimes} for _ in range(2))
    for seed in [11, 23, 37, 53, 71]:
        config = SyntheticConfig(
            n=30000, scenario=scenario, seed=seed, severity=severity, noise=0.3
        )
        frames = list(generate_chunks(config))
        X = np.concatenate([np.stack(frame.features.to_numpy()) for frame, _ in frames])
        y = np.concatenate([frame.target.to_numpy() for frame, _ in frames])
        weight = np.concatenate([oracle.weight.to_numpy() for _, oracle in frames])
        residual = y - (X[:, 0] - 0.9 * X[:, 1])
        for regime in regimes:
            selected = weight == regime
            values = residual[selected]
            severity_weight = severity * float(regime)
            expected_mean = severity_weight if scenario == "target_level" else 0.0
            expected_variance = 0.3**2
            if scenario == "target_variance":
                expected_variance *= (1 + severity_weight) ** 2
            elif scenario == "tail_frequency":
                rare_rate = 0.01 + 0.1 * np.tanh(severity) * float(regime)
                expected_variance *= 1 + 63 * rare_rate
            mean_errors[regime].append(abs(float(values.mean()) - expected_mean))
            variance_errors[regime].append(
                abs(float(values.var(ddof=1)) - expected_variance) / expected_variance
            )
    assert max(np.mean(errors) for errors in mean_errors.values()) < 0.02
    tolerance = 0.06 if scenario == "tail_frequency" else 0.025
    assert max(np.mean(errors) for errors in variance_errors.values()) < tolerance
