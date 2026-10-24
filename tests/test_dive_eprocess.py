import numpy as np
import pytest

from scripts.calibrate_pprm_block_mixture import _endpoint_stream_crossings
from shiftlab.dive.eprocess import (
    BoundedMeanEProcess,
    HorizonHedgedStartedMixtureEProcess,
    MultiTimescaleStartedKellyEProcess,
    PPIBlockConfidenceSequence,
    PPIBlockMixtureEProcess,
    PredictableBoundMeanEProcess,
    PredictableHedgedPositiveEProcess,
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableVarianceAdaptiveEProcess,
    StartedMixtureEProcess,
    VectorizedStartedMixtureEProcess,
)
from shiftlab.dive.estimators import prediction_powered_bound, prediction_powered_estimate
from shiftlab.dive.query import EvidenceDirectedQueryPolicy


def test_bounded_mean_eprocess_stays_one_at_zero_and_rejects_bound_violation():
    process = BoundedMeanEProcess(bound=1.0, alpha=0.05)
    assert process.log_e_value == pytest.approx(0.0)
    with pytest.raises(ValueError, match="bounded"):
        process.update(1.01)


def test_bounded_mean_eprocess_accepts_a_fixed_weighted_stake_mixture():
    process = BoundedMeanEProcess(bound=1.0, stakes=(0.01, 0.5), weights=(0.8, 0.2))
    assert process.predictable_stake == pytest.approx(0.108)
    process.update(0.5)
    expected = 0.8 * (1 + 0.01 * 0.5) + 0.2 * (1 + 0.5 * 0.5)
    assert np.exp(process.log_e_value) == pytest.approx(expected)
    updated_weights = np.array([0.8 * 1.005, 0.2 * 1.25]) / expected
    assert process.predictable_stake == pytest.approx(np.dot(updated_weights, (0.01, 0.5)))
    with pytest.raises(ValueError, match="weights"):
        BoundedMeanEProcess(bound=1.0, stakes=(0.1, 0.2), weights=(0.2, 0.2))


def test_predictable_bound_eprocess_uses_event_specific_bounds():
    process = PredictableBoundMeanEProcess(
        alpha=0.05,
        stakes=(0.25, 0.75),
        weights=(0.5, 0.5),
    )
    process.update(0.5, bound=1.0)
    process.update(-1.0, bound=2.0)
    expected = 0.5 * (1 + 0.25 * 0.5) * (1 - 0.25 / 2)
    expected += 0.5 * (1 + 0.75 * 0.5) * (1 - 0.75 / 2)
    assert np.exp(process.log_e_value) == pytest.approx(expected)
    assert process.n_updates == 2
    with pytest.raises(ValueError, match="bounded"):
        process.update(1.01, bound=1.0)
    with pytest.raises(ValueError, match="positive"):
        process.update(0.0, bound=0.0)


def test_variance_adaptive_stake_uses_only_prior_values_and_respects_global_bound():
    process = PredictableVarianceAdaptiveEProcess(bound=2.0)
    assert process.stake == pytest.approx(0.2)
    process.update(2.0)
    assert process.last_stake == pytest.approx(0.2)
    assert process.stake == pytest.approx(0.5)
    process.update(-2.0)
    assert process.last_stake == pytest.approx(0.5)
    assert process.log_e_value == pytest.approx(np.log(1.2) + np.log(0.5))
    with pytest.raises(ValueError, match="bounded"):
        process.update(2.01)


def test_predictable_plugin_empirical_bernstein_process_uses_published_increment():
    process = PredictablePlugInEmpiricalBernsteinEProcess(bound=2.0, alpha=0.05)
    assert process.stake == pytest.approx(0.5)
    expected_psi = (-np.log1p(-0.5) - 0.5) / 4
    expected_increment = 0.5 * (1.0 - 0.5) - expected_psi
    assert process.update(2.0) == pytest.approx(expected_increment)
    assert process.last_stake == pytest.approx(0.5)
    assert process.n_updates == 1
    assert process.predictive_mean == pytest.approx(0.75)
    assert process.predictive_variance == pytest.approx(0.15625)
    with pytest.raises(ValueError, match="bounded"):
        process.update(2.01)


def test_hedged_positive_branch_uses_bounded_predictable_bet():
    process = PredictableHedgedPositiveEProcess(bound=2.0, alpha=0.05)
    assert process.stake == pytest.approx(1.0)
    assert process.update(2.0) == pytest.approx(np.log(1.5))
    assert process.last_stake == pytest.approx(1.0)
    assert process.predictive_mean == pytest.approx(0.75)
    assert process.predictive_variance == pytest.approx(0.15625)

    lower_process = PredictableHedgedPositiveEProcess(bound=2.0, alpha=0.05)
    assert lower_process.update(-2.0) == pytest.approx(np.log(0.5))
    with pytest.raises(ValueError, match="bounded"):
        process.update(2.01)


def test_variance_adaptive_eprocess_controls_null_crossing_in_monte_carlo_check():
    rng = np.random.default_rng(28102026)
    crossings = 0
    streams = 400
    for _ in range(streams):
        process = PredictableVarianceAdaptiveEProcess(bound=1.0, alpha=0.05)
        for value in rng.choice([-1.0, 1.0], size=600):
            if process.update(float(value)) >= -np.log(0.05):
                crossings += 1
                break
    assert crossings / streams < 0.08


def test_evidence_directed_sampling_preserves_null_crossing_control_with_hard_cap():
    rng = np.random.default_rng(24102026)
    alpha = 0.05
    q_min = 0.05
    horizon = 400
    label_cap = 80
    streams = 300
    crossings = 0
    policy = EvidenceDirectedQueryPolicy(
        q_min=q_min,
        q_max=0.8,
        alpha=alpha,
        activation_fraction=0.05,
        urgency_power=0.5,
    )
    for _ in range(streams):
        process = BoundedMeanEProcess(bound=1 / q_min, alpha=alpha)
        queried = 0
        for _event in range(horizon):
            if queried >= label_cap:
                break
            q = policy.propensity(
                log_e_value=process.log_e_value,
                remaining_fraction=(label_cap - queried) / label_cap,
            )
            label_arrives = bool(rng.random() < q)
            value = 0.0
            if label_arrives:
                queried += 1
                gain = float(rng.choice((-1.0, 1.0)))
                value = gain / q
            process.update(value)
            if process.alarm:
                crossings += 1
                break
    # A one-sided 95% Monte Carlo upper endpoint is below 9% for this fixed-seed run.
    assert crossings / streams < 0.09


def test_prespecified_start_mixture_does_not_change_before_first_start():
    mixture = StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=(3, 7))
    assert mixture.log_e_value == pytest.approx(0.0)
    mixture.update(0.9)
    mixture.update(0.9)
    assert mixture.log_e_value == pytest.approx(0.0)
    mixture.update(0.9)
    assert mixture.log_e_value == pytest.approx(0.0)
    mixture.update(0.9)
    assert mixture.log_e_value > 0


def test_weighted_start_mixture_matches_fixed_convex_combination_of_components():
    starts = (0, 2, 5)
    weights = (0.6, 0.3, 0.1)
    values = (0.4, -0.2, 0.5, 0.1, -0.1, 0.6, -0.3)
    mixture = StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=starts, weights=weights)
    components = [BoundedMeanEProcess(bound=1.0, alpha=0.05) for _ in starts]
    for time, value in enumerate(values):
        for start, component in zip(starts, components, strict=True):
            if time >= start:
                component.update(value)
        mixture.update(value)
        expected = sum(
            weight * np.exp(component.log_e_value)
            for weight, component in zip(weights, components, strict=True)
        )
        assert np.exp(mixture.log_e_value) == pytest.approx(expected)
    with pytest.raises(ValueError, match="weights"):
        StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=starts, weights=(0.5, 0.5, 0.5))


@pytest.mark.parametrize("weights", [None, (0.6, 0.3, 0.1)])
def test_vectorized_started_mixture_matches_reference_event_by_event(weights):
    starts = (0, 2, 5)
    rng = np.random.default_rng(20261024)
    values = rng.uniform(-0.95, 0.95, size=80)
    reference = StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=starts, weights=weights)
    vectorized = VectorizedStartedMixtureEProcess(
        bound=1.0, alpha=0.05, starts=starts, weights=weights
    )
    assert vectorized.log_e_value == pytest.approx(reference.log_e_value, abs=1e-14)
    for value in values:
        expected = reference.update(float(value))
        actual = vectorized.update(float(value))
        assert actual == pytest.approx(expected, abs=1e-12)
        assert vectorized.alarm == reference.alarm


def test_multitimescale_started_kelly_is_predictable_and_respects_fixed_starts():
    process = MultiTimescaleStartedKellyEProcess(
        bound=1.0,
        alpha=0.05,
        starts=(2, 5),
        half_lives=(2.0, 8.0),
    )
    first_stakes = process.predictable_stakes.copy()
    assert np.all(first_stakes == 0)
    for value in (0.8, 0.6):
        process.update(value)
        assert process.log_e_value == pytest.approx(0.0)
    process.update(0.5)
    assert np.all(process.predictable_stakes[0] > 0)
    assert np.all(process.predictable_stakes[1] == 0)
    process.update(-0.2)
    assert np.isfinite(process.log_e_value)
    assert np.all(process.predictable_stakes <= 0.5)
    with pytest.raises(ValueError, match="bounded range"):
        process.update(1.01)


@pytest.mark.parametrize("probability_positive", [0.4, 0.5])
def test_multitimescale_started_kelly_terminal_e_value_under_small_null_enumeration(
    probability_positive,
):
    from itertools import product

    horizon = 6
    process_kwargs = {
        "bound": 1.0,
        "alpha": 0.05,
        "starts": (0, 2, 4),
        "half_lives": (2.0, 8.0),
    }
    expected = 0.0
    for stream in product((-1.0, 1.0), repeat=horizon):
        probability = np.prod(
            [probability_positive if value > 0 else 1 - probability_positive for value in stream]
        )
        process = MultiTimescaleStartedKellyEProcess(**process_kwargs)
        for value in stream:
            process.update(value)
        expected += probability * np.exp(process.log_e_value)
    assert expected <= 1.0 + 1e-12


def test_multihorizon_mixture_matches_a_fixed_convex_mixture_of_horizon_processes():
    horizons = (8, 12, 16)
    horizon_weights = (0.2, 0.5, 0.3)
    fractions = (0.0, 0.25, 0.5, 0.75)
    start_weights = (0.1, 0.2, 0.3, 0.4)
    hedge = HorizonHedgedStartedMixtureEProcess(
        bound=1.0,
        alpha=0.05,
        horizons=horizons,
        horizon_weights=horizon_weights,
        start_fractions=fractions,
        start_weights=start_weights,
    )
    horizon_processes = [
        StartedMixtureEProcess(
            bound=1.0,
            alpha=0.05,
            starts=tuple(round(horizon * fraction) for fraction in fractions),
            weights=start_weights,
        )
        for horizon in horizons
    ]
    values = (0.4, -0.2, 0.5, 0.1, -0.1, 0.6, -0.3, 0.2, 0.4, -0.1, 0.3, 0.5)
    for value in values:
        hedge.update(value)
        for process in horizon_processes:
            process.update(value)
        expected = sum(
            weight * np.exp(process.log_e_value)
            for weight, process in zip(horizon_weights, horizon_processes, strict=True)
        )
        assert np.exp(hedge.log_e_value) == pytest.approx(expected)


def test_multihorizon_mixture_merges_duplicate_starts_and_rejects_bad_weights():
    process = HorizonHedgedStartedMixtureEProcess(
        bound=1.0,
        alpha=0.05,
        horizons=(4, 8),
        horizon_weights=(0.5, 0.5),
        start_fractions=(0.0, 0.5, 1.0),
        start_weights=(0.25, 0.5, 0.25),
    )
    assert process.starts == (0, 2, 4, 8)
    assert process.weights.sum() == pytest.approx(1.0)
    with pytest.raises(ValueError, match="horizon_weights"):
        HorizonHedgedStartedMixtureEProcess(
            bound=1.0,
            alpha=0.05,
            horizons=(4, 8),
            horizon_weights=(0.5, 0.4),
            start_fractions=(0.0, 0.5),
            start_weights=(0.5, 0.5),
        )


def test_bounded_eprocess_null_crossing_is_small_in_independent_simulation():
    rng = np.random.default_rng(7)
    crossings = 0
    for _ in range(400):
        process = BoundedMeanEProcess(bound=1.0, alpha=0.05)
        for value in rng.choice([-1.0, 1.0], size=500):
            if process.update(float(value)) >= -np.log(0.05):
                crossings += 1
                break
    # A finite Monte Carlo check of a proof-level guarantee, not its replacement.
    assert crossings / 400 < 0.07


def test_fixed_worst_case_bound_remains_safe_with_feature_adaptive_query_rates():
    rng = np.random.default_rng(17)
    crossings = 0
    for _ in range(250):
        process = BoundedMeanEProcess(bound=prediction_powered_bound(1.0, 0.1), alpha=0.05)
        for _ in range(300):
            proxy = float(rng.uniform(-0.7, 0.7))
            propensity = 0.1 + 0.7 * abs(proxy)
            outcome = float(rng.choice([-1.0, 1.0]))
            queried = bool(rng.random() < propensity)
            estimate = prediction_powered_estimate(
                proxy, queried, outcome if queried else None, propensity
            )
            if process.update(estimate) >= -np.log(0.05):
                crossings += 1
                break
    assert crossings / 250 < 0.08


def test_log_spaced_stake_mixture_null_crossing_is_small_in_independent_simulation():
    rng = np.random.default_rng(37)
    stakes = tuple(np.geomspace(1 / 1024, 0.99, 13))
    crossings = 0
    for _ in range(300):
        process = BoundedMeanEProcess(bound=1.0, alpha=0.05, stakes=stakes)
        for value in rng.choice([-1.0, 1.0], size=500):
            if process.update(float(value)) >= -np.log(0.05):
                crossings += 1
                break
    assert crossings / 300 < 0.08


def test_ppi_block_confidence_sequence_detects_persistent_excess_and_checks_support():
    process = PPIBlockConfidenceSequence(max_reliance=1.0, threshold=0.6, alpha=0.05)
    assert not process.alarm
    for _ in range(1_000):
        process.update(0.9)
    assert process.alarm
    assert process.lower_bound > 0.6
    with pytest.raises(ValueError, match="support"):
        process.update(2.01)


def test_ppi_block_confidence_sequence_matches_cm_eb_formula():
    process = PPIBlockConfidenceSequence(
        max_reliance=0.0,
        threshold=0.5,
        alpha=0.05,
        lambda_count=4,
    )
    estimates = (0.4, 0.8)
    for estimate in estimates:
        process.update(estimate)
    forecast_errors = (0.4 - 0.5) ** 2 + (0.8 - 0.4) ** 2
    excess_sum = sum(estimates) - len(estimates) * 0.5
    psi = -np.log1p(-process.lambdas) - process.lambdas
    expected = np.logaddexp.reduce(
        process.log_weights + process.lambdas * excess_sum - psi * forecast_errors
    )
    assert process.sum_squared_prediction_errors == pytest.approx(forecast_errors)
    assert process.log_crossing_statistic == pytest.approx(expected)


def test_ppi_block_confidence_sequence_exact_small_null_enumeration():
    from itertools import product

    horizon = 8
    crossings = 0
    for stream in product((0.0, 1.0), repeat=horizon):
        process = PPIBlockConfidenceSequence(
            max_reliance=0.0,
            threshold=0.5,
            alpha=0.05,
            lambda_count=8,
            root_iterations=24,
        )
        for value in stream:
            process.update(value)
            if process.alarm:
                crossings += 1
                break
    # Every sequence has probability 2^-horizon under Bernoulli(1/2).
    # This exact finite null enumeration checks optional-look behavior.
    assert crossings / 2**horizon <= 0.05


def test_ppi_block_mixture_detects_persistent_excess_and_checks_exact_null():
    from itertools import product

    horizon = 8
    for weight in (0.1, 0.25, 0.5, 0.75, 0.9):
        crossings = 0
        for stream in product((0.0, 1.0), repeat=horizon):
            process = PPIBlockMixtureEProcess(max_reliance=0.0, threshold=0.5, alpha=0.05)
            for value in stream:
                process.update(value)
                if process.alarm_at_weight(weight):
                    crossings += 1
                    break
        assert crossings / 2**horizon <= 0.05

    process = PPIBlockMixtureEProcess(max_reliance=0.1, threshold=0.51, alpha=0.05)
    for _ in range(1_000):
        process.update(0.9)
    assert process.alarm
    for invalid_weight in (0.0, 1.0, float("nan")):
        with pytest.raises(ValueError, match="cm_eb_weight"):
            process.log_e_value_at_weight(invalid_weight)


def test_vectorized_endpoint_calibration_matches_scalar_eprocess_paths():
    rng = np.random.default_rng(821)
    upper_draws = rng.random((8, 32)) < 0.51
    vectorized = _endpoint_stream_crossings(
        upper_draws,
        threshold=0.51,
        max_reliance=0.1,
        alpha=0.05,
        device="cpu",
    )
    for stream_index, stream in enumerate(upper_draws):
        process = PPIBlockMixtureEProcess(max_reliance=0.1, threshold=0.51, alpha=0.05)
        crossed = dict.fromkeys(vectorized, False)
        for is_upper in stream:
            estimate = 1.1 if is_upper else -0.1
            process.update(estimate)
            crossed["CM-EB"] |= process.cm_eb.alarm
            crossed["positive_betting"] |= process.positive_betting.alarm
            for weight in (0.1, 0.25, 0.5, 0.75, 0.9):
                crossed[f"mixture_w={weight:g}"] |= process.alarm_at_weight(weight)
        for method, did_cross in crossed.items():
            assert vectorized[method][stream_index] == did_cross
