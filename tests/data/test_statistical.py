import numpy as np
import pytest

from shiftlab.data.bootstrap import mean_difference_interval
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks


@pytest.mark.parametrize(
    "scenario",
    [
        "iid_regression",
        "mean",
        "concept",
        "target_variance",
        "heteroskedastic",
        "heavy_tailed",
        "asymmetric_errors",
        "tail_frequency",
    ],
)
def test_oracle_moments_and_quantiles_replicated(scenario):
    means, coverages = [], []
    for seed in [101, 202, 303]:
        c = SyntheticConfig(n=12000, scenario=scenario, seed=seed)
        residuals, covered = [], []
        for frame, oracle in generate_chunks(c):
            error = frame.target.to_numpy() - oracle.conditional_mean.to_numpy()
            residuals.extend(error)
            covered.extend(abs(error) <= oracle.radius_90.to_numpy())
        means.append(np.mean(residuals))
        coverages.append(np.mean(covered))
    assert abs(np.mean(means)) < 0.03
    assert abs(np.mean(coverages) - 0.9) < 0.02


def test_ar1_autocorrelation():
    values = []
    for seed in [1, 2, 3]:
        frame, _ = next(
            generate_chunks(SyntheticConfig(n=10000, scenario="ar1", rho=0.7, seed=seed))
        )
        x = np.stack(frame.features)[:, 0]
        values.append(np.corrcoef(x[:-1], x[1:])[0, 1])
    assert abs(np.mean(values) - 0.7) < 0.025


def test_block_bootstrap_is_reproducible():
    rng = np.random.default_rng(21)
    a, b = rng.normal(size=2000), rng.normal(loc=2, size=2000)
    first = mean_difference_interval(a, b)
    assert first == mean_difference_interval(a, b)
    assert first["mean_difference_ci_low"] < 2 < first["mean_difference_ci_high"]
    assert first["bootstrap_block_length"] > 1


def test_label_prior_and_covariance():
    priors = []
    for seed in [1, 2, 3]:
        frame, _ = next(
            generate_chunks(
                SyntheticConfig(n=10000, scenario="prior_shift", severity=1.0, seed=seed)
            )
        )
        priors.append(frame.target.iloc[5000:].mean())
    assert abs(np.mean(priors) - 1 / (1 + np.exp(-1))) < 0.02
    for scenario in ["covariance_rotation", "correlation"]:
        frame, _ = next(generate_chunks(SyntheticConfig(n=5000, scenario=scenario)))
        covariance = np.cov(np.stack(frame.features)[2500:, :2].T)
        assert np.linalg.eigvalsh(covariance).min() > 0


@pytest.mark.parametrize(
    "scenario", __import__("shiftlab.data.synthetic", fromlist=["SCENARIOS"]).SCENARIOS
)
def test_all_scenario_oracle_risk_reference(scenario):
    differences = []
    for seed in [71, 83, 97]:
        for frame, oracle in generate_chunks(SyntheticConfig(n=3000, scenario=scenario, seed=seed)):
            positive = frame.target.to_numpy() > 0
            action = oracle.oracle_action.to_numpy()
            realized = np.where(action, ~positive, oracle.fn_cost.to_numpy() * positive)
            differences.extend(realized - oracle.oracle_risk.to_numpy())
    values = np.asarray(differences)
    assert abs(values.mean()) < max(0.02, 8 * values.std() / np.sqrt(len(values)))
