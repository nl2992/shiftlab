import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.cli import generate
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import SCENARIOS, generate_chunks
from shiftlab.data.synthetic.oracle_spec import conditional_mean, conditional_scale, oracle_spec


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_scenario_has_serializable_regime_parameter_and_oracle_spec(scenario):
    config = SyntheticConfig(n=1000, scenario=scenario, severity=1.5)
    spec = oracle_spec(config)
    json.dumps(spec)
    assert spec["scenario"] == scenario
    assert spec["conditional_mean_formula"]
    assert spec["conditional_residual_law"]
    assert spec["regime_parameters"]
    assert all("effective_severity" in row for row in spec["regime_parameters"])
    assert all("parameter_values" in row for row in spec["regime_parameters"])


def test_concept_parameter_metadata_records_exact_baseline_and_shifted_coefficients():
    config = SyntheticConfig(n=1000, d=3, scenario="concept", severity=2.0)
    rows = oracle_spec(config)["regime_parameters"]
    assert rows[0]["parameter_values"]["linear_coefficients"] == [1.0, -0.9, 0.0]
    assert rows[-1]["parameter_values"]["linear_coefficients"] == [-1.0, -0.9, 0.0]


def test_discrete_parameter_metadata_keeps_every_declared_regime():
    config = SyntheticConfig(n=1000, scenario="concept", pattern="multiple", regimes=16)
    assert len(oracle_spec(config)["regime_parameters"]) == 16


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_independent_conditional_function_and_scale_match_generated_oracle(scenario):
    config = SyntheticConfig(n=1000, scenario=scenario, seed=88)
    frame, oracle = next(generate_chunks(config))
    features = np.stack(frame.features.to_numpy())
    weight = oracle.weight.to_numpy()
    expected_mean = conditional_mean(config, features, weight)
    assert np.max(np.abs(expected_mean - oracle.conditional_mean.to_numpy())) < 1e-10
    if scenario == "garch":
        standardized = (frame.target.to_numpy() - expected_mean) / config.noise
        variance = np.empty(len(standardized))
        burn = np.random.default_rng(config.seed + 701)
        burn.normal()
        previous_error, previous_variance = 0.0, 0.5
        for innovation in burn.normal(size=1000):
            previous_error = np.sqrt(previous_variance) * innovation
            previous_variance = 0.05 + 0.1 * previous_error**2 + 0.8 * previous_variance
        for index, error in enumerate(standardized):
            current = 0.05 + 0.1 * previous_error**2 + 0.8 * previous_variance
            variance[index] = current
            previous_error, previous_variance = error, current
        expected_scale = conditional_scale(config, features, weight, garch_variance=variance)
    else:
        expected_scale = conditional_scale(config, features, weight)
    assert np.max(np.abs(expected_scale - oracle.sigma.to_numpy())) < 1e-10


def test_generated_dgp_json_carries_structured_oracle_specification(tmp_path):
    config = SyntheticConfig(
        n=300, d=3, scenario="concept", severity=1.0, chunk_size=100, output=str(tmp_path)
    )
    path = generate(config)
    truth = json.loads((Path(path) / "evaluator_only/dgp.json").read_text(encoding="utf-8"))
    structured = truth["structured_oracle_specification"]
    assert structured["conditional_mean_formula"] == "X0*(1-severity*w)-.9*X1"
    assert len(structured["regime_parameters"]) == 2
    manifest = json.loads((Path(path) / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["task_specs"][0]["task_id"] == "synthetic_concept"
    assert manifest["task_specs"][0]["task_kind"] == "regression"


def test_dependent_error_oracle_separates_marginal_and_history_conditional_targets():
    config = SyntheticConfig(
        n=12000, scenario="dependent_errors", rho=0.65, chunk_size=257, noise=0.5
    )
    generated = list(generate_chunks(config))
    frame = pd.concat([item[0] for item in generated], ignore_index=True)
    oracle = pd.concat([item[1] for item in generated], ignore_index=True)
    residual = frame.target.to_numpy() - oracle.conditional_mean_given_history.to_numpy()
    expected_variance = config.noise**2 * (1 - config.rho**2)
    assert abs(np.var(residual[1:]) - expected_variance) < 0.015
    covered = np.abs(residual[1:]) <= oracle.conditional_radius_90.to_numpy()[1:]
    assert abs(covered.mean() - 0.9) < 0.02
    marginal_residual = frame.target.to_numpy() - oracle.conditional_mean.to_numpy()
    assert abs(np.corrcoef(marginal_residual[:-1], marginal_residual[1:])[0, 1] - config.rho) < 0.03
    prior_standardized_error = np.r_[0.0, marginal_residual[:-1] / config.noise]
    expected_history_mean = conditional_mean(
        config,
        np.stack(frame.features.to_numpy()),
        oracle.weight.to_numpy(),
        prior_standardized_error,
    )
    assert (
        np.max(np.abs(expected_history_mean - oracle.conditional_mean_given_history.to_numpy()))
        < 1e-10
    )


@pytest.mark.parametrize(
    "scenario",
    [
        "concept",
        "sign_reversal",
        "nonlinear_response",
        "interaction",
        "latent_state",
        "conditional_variance",
        "boundary_local",
        "boundary_rotation",
    ],
)
def test_concept_cases_preserve_feature_law_and_match_conditional_oracle(scenario):
    config = SyntheticConfig(n=20000, d=3, scenario=scenario, severity=1.2, chunk_size=5000)
    parts = list(generate_chunks(config))
    frame = pd.concat([item[0] for item in parts], ignore_index=True)
    oracle = pd.concat([item[1] for item in parts], ignore_index=True)
    features = np.stack(frame.features.to_numpy())
    weight = oracle.weight.to_numpy()
    baseline_x, shifted_x = features[weight == 0], features[weight == 1]
    assert np.max(np.abs(baseline_x.mean(axis=0) - shifted_x.mean(axis=0))) < 0.06
    assert np.max(np.abs(np.cov(baseline_x.T) - np.cov(shifted_x.T))) < 0.08

    f = features[:, 0] - 0.9 * features[:, 1]
    baseline_function = f.copy()
    if scenario == "concept":
        expected = features[:, 0] * (1 - config.severity * weight) - 0.9 * features[:, 1]
    elif scenario == "sign_reversal":
        expected = (
            features[:, 0] * (1 - 2 * np.tanh(config.severity) * weight) - 0.9 * features[:, 1]
        )
    elif scenario == "nonlinear_response":
        expected = f + config.severity * weight * np.sin(features[:, 0])
    elif scenario == "interaction":
        expected = f + config.severity * weight * features[:, 0] * features[:, 1]
    elif scenario == "latent_state":
        expected = f + config.severity * weight
    elif scenario == "boundary_local":
        expected = f + config.severity * weight * np.exp(-5 * np.abs(f))
    elif scenario == "boundary_rotation":
        from scipy.special import expit

        expected = expit(
            np.cos(config.severity * weight) * features[:, 0]
            + np.sin(config.severity * weight) * features[:, 1]
        )
        baseline_function = expit(features[:, 0])
    else:
        expected = f
        expected_sigma = config.noise * (1 + config.severity * weight * np.abs(features[:, 0]))
        assert np.max(np.abs(oracle.sigma.to_numpy() - expected_sigma)) < 1e-10
    assert np.max(np.abs(oracle.conditional_mean.to_numpy() - expected)) < 1e-10
    shifted = weight == 1
    if scenario == "conditional_variance":
        assert np.mean(np.abs(oracle.sigma.to_numpy()[shifted] - config.noise)) > 0
    else:
        assert np.mean(np.abs(expected[shifted] - baseline_function[shifted])) > 1e-3
