import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from scipy.stats import norm
from scipy.stats import t as student_t

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


def test_resource_cost_changes_only_in_the_declared_scenario_and_matches_oracle_spec():
    config = SyntheticConfig(n=1000, scenario="resource_cost", severity=2.0)
    _, oracle = next(generate_chunks(config))
    shifted = oracle.weight.to_numpy() == 1
    assert np.all(oracle.retrain_cost.to_numpy()[~shifted] == 10.0)
    assert np.all(oracle.retrain_cost.to_numpy()[shifted] == 30.0)
    declared = [
        row["parameter_values"]["retrain_cost"] for row in oracle_spec(config)["regime_parameters"]
    ]
    assert declared == [10.0, 30.0]

    _, stationary_oracle = next(
        generate_chunks(SyntheticConfig(n=1000, scenario="concept", severity=2.0))
    )
    assert np.all(stationary_oracle.retrain_cost.to_numpy() == 10.0)


def test_rare_cost_oracle_actions_follow_the_disclosed_expected_cost_threshold():
    config = SyntheticConfig(n=1000, scenario="rare_cost", severity=2.0)
    _, oracle = next(generate_chunks(config))
    probability = oracle.probability_positive.to_numpy()
    false_negative = oracle.fn_cost.to_numpy()
    expected = probability >= 1.0 / (1.0 + false_negative)
    assert np.array_equal(oracle.oracle_action.to_numpy(), expected)
    assert np.all(false_negative[oracle.weight.to_numpy() == 0] == 5.0)
    assert np.all(false_negative[oracle.weight.to_numpy() == 1] == 205.0)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_scenario_oracle_action_minimizes_disclosed_expected_cost(scenario):
    config = SyntheticConfig(n=1200, scenario=scenario, seed=417, severity=1.5)
    frame, oracle = next(generate_chunks(config))
    probability = oracle.probability_positive.to_numpy(dtype=float)
    false_negative = oracle.fn_cost.to_numpy(dtype=float)
    action = oracle.oracle_action.to_numpy(dtype=bool)
    feasible = np.asarray(
        [
            True if value is None else json.loads(value)["action_1_feasible"]
            for value in frame.decision_context
        ],
        dtype=bool,
    )

    # Independent derivation: action 1 costs 1-p; action 0 costs p*FN.
    expected_action = (probability >= 1.0 / (1.0 + false_negative)) & feasible
    expected_risk = np.where(action, 1.0 - probability, probability * false_negative)
    assert np.isfinite(probability).all()
    assert ((probability >= 0.0) & (probability <= 1.0)).all()
    assert np.array_equal(action, expected_action)
    assert np.allclose(oracle.oracle_risk.to_numpy(dtype=float), expected_risk, atol=1e-12)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_scenario_event_probability_matches_its_independent_response_law(scenario):
    config = SyntheticConfig(n=1200, scenario=scenario, seed=613, severity=1.5)
    frame, oracle = next(generate_chunks(config))
    features = np.stack(frame.features.to_numpy())
    weight = oracle.weight.to_numpy(dtype=float)
    severity = config.severity * weight
    mean = oracle.conditional_mean.to_numpy(dtype=float)
    scale = oracle.sigma.to_numpy(dtype=float)

    if scenario == "nonlinear_classification":
        expected = expit(features[:, 0] + features[:, 1] ** 2 - 1)
    elif scenario == "boundary_rotation":
        expected = expit(np.cos(severity) * features[:, 0] + np.sin(severity) * features[:, 1])
    elif scenario == "small_decision_covariate":
        expected = expit(200 * features[:, 0])
    elif scenario == "rare_high_cost":
        expected = 0.0001 + 0.005 * severity
    elif scenario in {"prior_shift", "imbalance"}:
        prior_logit = severity + (np.log(0.1 / 0.9) if scenario == "imbalance" else 0.0)
        expected = expit(2 * features[:, 0] + prior_logit)
    elif scenario == "label_corruption":
        flip_rate = np.minimum(0.45, severity / 5)
        clean = expit(features[:, 0] + features[:, 1] ** 2 - 1)
        expected = flip_rate + (1 - 2 * flip_rate) * clean
    elif scenario in {"heavy_tailed"}:
        expected = student_t.cdf(mean / scale * np.sqrt(5 / 3), df=5)
    elif scenario == "asymmetric_errors":
        boundary = np.exp(0.5) - mean / scale * np.sqrt((np.e - 1) * np.e)
        expected = np.where(boundary <= 0, 1.0, 1 - norm.cdf(np.log(np.maximum(boundary, 1e-300))))
    elif scenario in {"tail_frequency", "extreme_events"}:
        rare_rate = 0.01 + 0.1 * np.tanh(config.severity) * weight
        expected = (1 - rare_rate) * norm.cdf(mean / scale) + rare_rate * norm.cdf(
            mean / (8 * scale)
        )
    elif scenario == "garch":
        expected = norm.cdf(mean / scale)
    elif scenario == "dependent_errors":
        expected = norm.cdf(mean / config.noise)
    else:
        expected = norm.cdf(mean / scale)

    assert np.isfinite(expected).all()
    assert np.allclose(oracle.probability_positive.to_numpy(dtype=float), expected, atol=1e-12)


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
        "boundary_local_harm",
        "boundary_rotation",
    ],
)
@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_concept_cases_preserve_feature_law_and_match_conditional_oracle(scenario, severity):
    from scipy.special import expit

    for seed in [11, 23, 37, 53, 71]:
        config = SyntheticConfig(
            n=20000, d=3, scenario=scenario, severity=severity, seed=seed, chunk_size=5000
        )
        parts = list(generate_chunks(config))
        frame = pd.concat([item[0] for item in parts], ignore_index=True)
        oracle = pd.concat([item[1] for item in parts], ignore_index=True)
        features = np.stack(frame.features.to_numpy())
        weight = oracle.weight.to_numpy()
        baseline_x = features[weight == 0]
        if severity == 0:
            assert len(np.unique(weight)) == 1
            assert np.max(np.abs(baseline_x.mean(axis=0))) < 0.03
            assert np.max(np.abs(np.cov(baseline_x.T) - np.eye(3))) < 0.04
        else:
            shifted_x = features[weight == 1]
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
        elif scenario in {"boundary_local", "boundary_local_harm"}:
            expected = f + config.severity * weight * np.exp(-5 * np.abs(f))
        elif scenario == "boundary_rotation":
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
            if severity == 0:
                assert np.max(np.abs(oracle.sigma.to_numpy() - config.noise)) == 0
            else:
                assert np.mean(np.abs(oracle.sigma.to_numpy()[shifted] - config.noise)) > 0
        elif severity == 0:
            assert np.max(np.abs(expected - baseline_function)) < 1e-12
        else:
            assert np.mean(np.abs(expected[shifted] - baseline_function[shifted])) > 1e-3


def test_harmful_adaptation_has_stationary_data_and_evaluator_only_intervention_clock():
    base = SyntheticConfig(n=1000, d=4, scenario="iid_regression", seed=17)
    adapted = base.model_copy(
        update={"scenario": "harmful_adaptation", "pattern": "abrupt", "change_fraction": 0.6}
    )
    base_frame, base_oracle = zip(*generate_chunks(base), strict=True)
    adapted_frame, adapted_oracle = zip(*generate_chunks(adapted), strict=True)
    base_frame = pd.concat(base_frame, ignore_index=True)
    adapted_frame = pd.concat(adapted_frame, ignore_index=True)
    base_oracle = pd.concat(base_oracle, ignore_index=True)
    adapted_oracle = pd.concat(adapted_oracle, ignore_index=True)
    np.testing.assert_array_equal(base_frame.target, adapted_frame.target)
    np.testing.assert_array_equal(np.stack(base_frame.features), np.stack(adapted_frame.features))
    np.testing.assert_array_equal(
        base_oracle.probability_positive, adapted_oracle.probability_positive
    )
    assert set(adapted_oracle.regime_id) == {"baseline", "adaptation_intervention"}
    assert adapted_frame.regime_id.isna().all()
