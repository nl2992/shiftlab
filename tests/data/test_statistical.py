import numpy as np
import pytest
from scipy.special import expit
from scipy.stats import lognorm, norm
from scipy.stats import t as student_t

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


@pytest.mark.parametrize(
    "scenario",
    [
        "iid_regression",
        "target_variance",
        "conditional_variance",
        "heteroskedastic",
        "dependent_errors",
        "garch",
        "heavy_tailed",
        "asymmetric_errors",
        "tail_frequency",
        "extreme_events",
    ],
)
def test_oracle_radius_has_exactly_ninety_percent_mass_under_its_residual_law(scenario):
    config = SyntheticConfig(n=1200, scenario=scenario, seed=719, severity=1.5)
    _, oracle = next(generate_chunks(config))
    radius = oracle.radius_90.to_numpy(dtype=float)
    scale = oracle.sigma.to_numpy(dtype=float)
    kind = oracle.quantile_kind.iloc[0]

    assert np.isfinite(radius).all()
    assert (radius > 0).all()
    if kind in {"normal", "marginal_normal_dependent"}:
        mass = 2 * norm.cdf(radius / scale) - 1
    elif kind == "student_t5":
        mass = 2 * student_t.cdf(radius / scale * np.sqrt(5 / 3), df=5) - 1
    elif kind == "centered_lognormal":
        center, standardizer = np.exp(0.5), np.sqrt((np.e - 1) * np.e)
        upper = center + standardizer * radius / scale
        lower = center - standardizer * radius / scale
        lower_mass = np.where(lower > 0, lognorm.cdf(lower, s=1), 0.0)
        mass = lognorm.cdf(upper, s=1) - lower_mass
    elif kind == "normal_mixture":
        weight = oracle.weight.to_numpy(dtype=float)
        rare_rate = 0.01 + 0.1 * np.tanh(config.severity) * weight
        standardized_radius = radius / scale
        mass = (1 - rare_rate) * (2 * norm.cdf(standardized_radius) - 1) + rare_rate * (
            2 * norm.cdf(standardized_radius / 8) - 1
        )
    else:
        raise AssertionError(f"Unvalidated residual law: {kind}")

    assert np.max(np.abs(mass - 0.9)) < 1e-8


def test_ar1_autocorrelation():
    values = []
    for seed in [1, 2, 3]:
        frame, _ = next(
            generate_chunks(SyntheticConfig(n=10000, scenario="ar1", rho=0.7, seed=seed))
        )
        x = np.stack(frame.features)[:, 0]
        values.append(np.corrcoef(x[:-1], x[1:])[0, 1])
    assert abs(np.mean(values) - 0.7) < 0.025


@pytest.mark.parametrize("scenario", ["ar1", "arma", "garch"])
def test_temporal_processes_match_stationary_variance_and_dependence(scenario):
    """Check temporal generators against independent stationary-law formulas."""
    rho, theta, noise = 0.65, 0.3, 0.3
    expected_variance = {
        "ar1": 1.0,
        "arma": (1 + theta**2 + 2 * rho * theta) / (1 - rho**2),
        # omega / (1 - alpha - beta), with omega=.05, alpha=.1, beta=.8.
        "garch": 0.05 / (1 - 0.1 - 0.8),
    }[scenario]
    sample_variances, lag_one = [], []
    for seed in [11, 23, 37, 53, 71]:
        config = SyntheticConfig(n=30000, scenario=scenario, rho=rho, noise=noise, seed=seed)
        frame, oracle = next(generate_chunks(config))
        series = (
            np.stack(frame.features.to_numpy())[:, 0]
            if scenario in {"ar1", "arma"}
            else (frame.target.to_numpy() - oracle.conditional_mean.to_numpy()) / config.noise
        )
        series = series[1000:]
        sample_variances.append(np.var(series, ddof=1))
        lag_one.append(np.corrcoef(series[:-1], series[1:])[0, 1])
    assert abs(np.mean(sample_variances) - expected_variance) < 0.035 * expected_variance
    if scenario == "ar1":
        expected_lag_one = rho
    elif scenario == "arma":
        expected_lag_one = (rho + theta) * (1 + rho * theta) / (1 + theta**2 + 2 * rho * theta)
    else:
        # GARCH has zero linear autocorrelation and positive squared autocorrelation.
        expected_lag_one = 0.0
    assert abs(np.mean(lag_one) - expected_lag_one) < 0.025
    if scenario == "garch":
        squared_lag_one = []
        for seed in [11, 23, 37, 53, 71]:
            config = SyntheticConfig(n=30000, scenario=scenario, rho=rho, noise=noise, seed=seed)
            frame, oracle = next(generate_chunks(config))
            series = (frame.target.to_numpy() - oracle.conditional_mean.to_numpy())[1000:]
            squared = series**2
            squared_lag_one.append(np.corrcoef(squared[:-1], squared[1:])[0, 1])
        assert np.mean(squared_lag_one) > 0.05


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


@pytest.mark.parametrize("scenario", ["nonlinear_classification", "boundary_rotation"])
@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_classification_labels_calibrate_to_independent_probability_formula(scenario, severity):
    observed, expected, variances, probability_errors = [], [], [], []
    for seed in [11, 23, 37, 53, 71]:
        config = SyntheticConfig(
            n=20000, d=4, scenario=scenario, severity=severity, seed=seed, chunk_size=5000
        )
        parts = list(generate_chunks(config))
        features = np.concatenate([np.stack(frame.features.to_numpy()) for frame, _ in parts])
        targets = np.concatenate([frame.target.to_numpy() for frame, _ in parts])
        weights = np.concatenate([oracle.weight.to_numpy() for _, oracle in parts])
        probabilities = np.concatenate(
            [oracle.probability_positive.to_numpy() for _, oracle in parts]
        )
        if scenario == "nonlinear_classification":
            formula = expit(features[:, 0] + features[:, 1] ** 2 - 1)
        else:
            formula = expit(
                np.cos(severity * weights) * features[:, 0]
                + np.sin(severity * weights) * features[:, 1]
            )
        probability_errors.append(float(np.max(np.abs(probabilities - formula))))
        observed.append(float(targets.sum()))
        expected.append(float(formula.sum()))
        variances.append(float(np.sum(formula * (1 - formula))))
    expected_total = sum(expected)
    # Independent Bernoulli draws have this conditional variance; aggregate independent streams.
    variance = sum(variances)
    assert max(probability_errors) < 1e-12
    assert abs(sum(observed) - expected_total) < 5 * np.sqrt(variance)


@pytest.mark.parametrize("severity", [0.0, 0.5, 2.0])
def test_feedback_change_matches_configured_delay_and_missingness_rates(severity):
    seeds = [11, 23, 37, 53, 71]
    baseline_missing, shifted_missing = [], []
    baseline_total = shifted_total = 0
    for seed in seeds:
        config = SyntheticConfig(
            n=20000,
            scenario="feedback_change",
            severity=severity,
            delay=3,
            missing=0.1,
            seed=seed,
            chunk_size=5000,
        )
        parts = list(generate_chunks(config))
        event_time = np.concatenate([frame.event_time.to_numpy() for frame, _ in parts])
        available_time = np.concatenate(
            [frame.label_available_time.to_numpy(dtype=float) for frame, _ in parts]
        )
        weights = np.concatenate([oracle.weight.to_numpy() for _, oracle in parts])
        for regime, records, expected_delay, expected_missing in [
            (0, baseline_missing, 3, 0.1),
            (
                1,
                shifted_missing,
                3 + int(np.rint(20 * severity)),
                min(0.95, 0.1 + 0.2 * np.tanh(severity)),
            ),
        ]:
            selected = weights == regime
            if not selected.any():
                assert severity == 0.0 and regime == 1
                continue
            observed = available_time[selected]
            finite = np.isfinite(observed)
            assert np.unique(observed[finite] - event_time[selected][finite]).tolist() == [
                expected_delay
            ]
            records.append((int((~finite).sum()), len(observed)))
            if regime == 0:
                baseline_total += len(observed)
            else:
                shifted_total += len(observed)

    for records, expected_rate in [
        (baseline_missing, 0.1),
        (shifted_missing, min(0.95, 0.1 + 0.2 * np.tanh(severity))),
    ]:
        if not records:
            continue
        missing = sum(count for count, _ in records)
        total = sum(count for _, count in records)
        expected_missing = expected_rate * total
        standard_error = np.sqrt(expected_rate * (1 - expected_rate) * total)
        assert abs(missing - expected_missing) < 5 * standard_error
    assert baseline_total > 0
    assert shifted_total == 0 if severity == 0 else shifted_total > 0


@pytest.mark.parametrize(
    "scenario", __import__("shiftlab.data.synthetic", fromlist=["SCENARIOS"]).SCENARIOS
)
def test_all_scenario_oracle_risk_reference(scenario):
    differences = []
    reference_variances = []
    for seed in [71, 83, 97]:
        for frame, oracle in generate_chunks(SyntheticConfig(n=3000, scenario=scenario, seed=seed)):
            positive = frame.target.to_numpy() > 0
            action = oracle.oracle_action.to_numpy()
            realized = np.where(action, ~positive, oracle.fn_cost.to_numpy() * positive)
            differences.extend(realized - oracle.oracle_risk.to_numpy())
            p = oracle.probability_positive.to_numpy()
            outcome_cost = np.where(action, 1.0, oracle.fn_cost.to_numpy())
            reference_variances.extend(outcome_cost**2 * p * (1 - p))
    values = np.asarray(differences)
    # Oracle Bernoulli variance remains nonzero when a finite sample sees no rare event.
    # Sample variance alone can badly understate uncertainty for rare, high-cost outcomes.
    reference_se = np.sqrt(np.sum(reference_variances)) / len(values)
    assert abs(values.mean()) < max(0.02, 8 * reference_se, 8 * values.std() / np.sqrt(len(values)))
