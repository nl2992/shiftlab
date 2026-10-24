from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.run_predictable_stake_portfolio import (
    DEFAULT_SEED,
    ETAS,
    STAKES,
    analyze,
    predictable_weights,
    run,
)


def test_predictable_weights_are_simplex_functions_of_past_wealth():
    prior_wealth = np.array([[0.0, 1.0, -0.5], [2.0, -1.0, 0.25]])
    for eta in ETAS:
        weights = predictable_weights(prior_wealth, float(eta))
        assert weights.shape == prior_wealth.shape
        assert np.all(np.isfinite(weights))
        assert np.all(weights >= 0)
        np.testing.assert_allclose(weights.sum(axis=1), 1.0, atol=1e-15)


def test_predictable_convex_factor_has_conditional_mean_at_most_one():
    past_wealth = np.array([[0.7, -0.2, 0.1, -1.4, 0.3]])
    increments = np.array([1.0, -1.0])
    probabilities = np.array([0.4, 0.6])  # strictly negative conditional mean
    for eta in ETAS:
        weights = predictable_weights(past_wealth, float(eta))
        factors = 1 + increments[:, None] * np.asarray(STAKES)[None, :]
        portfolio_factors = (factors[:, None, :] * weights[None, :, :]).sum(axis=2)
        conditional_means = probabilities @ portfolio_factors[:, 0]
        assert np.all(portfolio_factors >= 0)
        assert conditional_means <= 1 + 1e-12


def test_eta_one_portfolio_update_is_fixed_mixture_update():
    rng = np.random.default_rng(318)
    log_wealth = rng.normal(size=(19, len(STAKES)))
    normalized_increments = rng.uniform(-1, 1, size=(19, 1))
    factors = 1 + normalized_increments * np.asarray(STAKES)[None, :]
    prior = np.full(len(STAKES), 1 / len(STAKES))
    weights = predictable_weights(log_wealth, 1.0)
    portfolio_growth = np.sum(weights * factors, axis=1)
    old_fixed = np.log(np.sum(np.exp(log_wealth) * prior, axis=1))
    new_fixed = np.log(np.sum(np.exp(log_wealth) * factors * prior, axis=1))
    np.testing.assert_allclose(np.log(portfolio_growth), new_fixed - old_fixed, atol=1e-12)


def test_predictable_weights_reject_invalid_state():
    with pytest.raises(ValueError, match="finite streams-by-stakes"):
        predictable_weights(np.array([[np.nan, 0.0]]), 1.0)
    with pytest.raises(ValueError, match="nonnegative"):
        predictable_weights(np.zeros((1, 2)), -0.1)


def test_development_smoke_preserves_paths_and_eta_one_identity(tmp_path):
    output = tmp_path / "portfolio"
    run(
        streams=30,
        seed=DEFAULT_SEED,
        horizon=100,
        device_name="cpu",
        output=output,
    )
    metrics = pd.read_parquet(output / "metrics/stream_metrics.parquet")
    assert len(metrics) == 30 * 6 * len(ETAS)
    assert metrics["budget_respected"].all()
    assert metrics["bound_violations"].sum() == 0
    paths = metrics.pivot(
        index=["scenario", "stream_id"],
        columns="eta",
        values=["labels_queried", "events_processed", "registered_events"],
    )
    for field in ("labels_queried", "events_processed", "registered_events"):
        for eta in ETAS:
            assert paths[(field, 1.0)].equals(paths[(field, float(eta))])
    contrasts = pd.read_csv(output / "metrics/paired_detection_contrasts.csv")
    assert set(contrasts["candidate_eta"]) == {float(value) for value in ETAS if value != 1.0}
    assert (output / "reports/manifest.json").exists()


def test_analysis_uses_paired_seed_macro_contrasts():
    rows = []
    for scenario, base, candidate in (
        ("markov_volatility_harm_d0.04", 0, 1),
        ("markov_volatility_harm_d0.20", 1, 1),
        ("markov_volatility_harm_d0.40", 0, 0),
        ("markov_volatility_harm_d0.60", 0, 1),
    ):
        for stream_id in range(30):
            for eta in ETAS:
                detected = candidate if eta == 0.75 else base
                rows.append(
                    {
                        "scenario": scenario,
                        "eta": eta,
                        "stream_id": stream_id,
                        "post_onset_detection": bool(detected),
                        "labels_queried": 10,
                        "evaluator_cumulative_expected_harm_cost": 0.0,
                        "false_escalation": False,
                        "onset_reached": True,
                        "events_processed": 100,
                        "detection_delay_event_time": np.nan,
                        "detection_delay_wall_time": np.nan,
                    }
                )
    _summary, contrasts = analyze(pd.DataFrame(rows), seed=9)
    primary = contrasts[
        (contrasts["metric"] == "post_onset_detection") & (contrasts["candidate_eta"] == 0.75)
    ].iloc[0]
    assert primary["mean_difference"] == pytest.approx(0.5)
    assert primary["paired_seed_count"] == 30
