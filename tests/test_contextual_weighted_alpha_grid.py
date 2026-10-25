import numpy as np
import pytest

from shiftlab.dive.contextual_weighted_alpha_grid import (
    _alpha_weights,
    _posterior_harm_probability,
    generate_proxy_streams,
    run_grid,
)


def test_pilot_weight_allocations_are_positive_and_sum_to_one():
    weights = _alpha_weights(np.array([480, 20]))
    assert set(weights) == {"equal_alpha", "volume_weighted_alpha", "rare_protected_alpha"}
    for allocation in weights.values():
        assert np.all(allocation > 0)
        assert np.isclose(allocation.sum(), 1.0)
    assert weights["rare_protected_alpha"][1] > weights["equal_alpha"][1]
    assert weights["volume_weighted_alpha"][0] > weights["equal_alpha"][0]


def test_proxy_posterior_and_generated_visible_context_means():
    p_proxy, q_safe, q_harm = _posterior_harm_probability(0.25, 0.10)
    assert np.isclose(p_proxy, 0.30)
    assert np.isclose(q_safe, 0.25 * 0.10 / 0.70)
    assert np.isclose(q_harm, 0.25 * 0.90 / 0.30)
    features, gains, expected, contexts, pilot = generate_proxy_streams(
        scenario="heterogeneous_reversal",
        seeds=3,
        horizon=200,
        true_harmful_prevalence=0.25,
        proxy_error_rate=0.10,
        seed=42,
        device="cpu",
    )
    assert features.shape == (3, 400, 1)
    assert set(np.unique(features)) == {0.0, 1.0}
    assert gains.shape == (3, 400)
    assert set(np.unique(gains)) <= {-1.0, 5.0}
    assert np.isclose(expected[:200].mean(), 1.0)
    assert np.isclose(expected[200:][contexts[200:] == 0].mean(), 0.3689285714)
    assert np.isclose(expected[200:][contexts[200:] == 1].mean(), -0.2525)
    assert pilot.shape == (2,) and pilot.sum() == 500

    with pytest.raises(ValueError, match="leave both contexts represented"):
        generate_proxy_streams(
            scenario="heterogeneous_reversal",
            seeds=1,
            horizon=200,
            true_harmful_prevalence=0.0001,
            proxy_error_rate=0.0,
            seed=43,
            device="cpu",
        )


def test_weighted_alpha_grid_cpu_smoke(tmp_path):
    metrics, contrasts, manifest = run_grid(
        tmp_path,
        seeds=2,
        horizon=200,
        true_harmful_prevalences=(0.25,),
        proxy_error_rates=(0.10,),
        intervention_cost_multipliers=(1.0,),
        budget_rates=(0.40,),
        device="cpu",
        bootstrap_replicates=100,
    )
    assert manifest["status"] == "development_only_no_independent_calibration_or_confirmation"
    assert manifest["all_alpha_weights_from_pre_stream_unlabeled_pilot"]
    assert manifest["all_label_caps_respected"]
    assert set(metrics.method) == {
        "continue",
        "global_gate",
        "equal_alpha",
        "volume_weighted_alpha",
        "rare_protected_alpha",
    }
    assert metrics.budget_respected.all()
    assert not contrasts.empty
    assert (
        (contrasts.method == "volume_weighted_alpha") & (contrasts.reference == "equal_alpha")
    ).any()
    assert (tmp_path / "metrics.parquet").is_file()
    assert (tmp_path / "manifest.json").is_file()
