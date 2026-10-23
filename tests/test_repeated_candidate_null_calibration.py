import numpy as np
import torch

from scripts.calibrate_repeated_candidate_nulls import (
    CalibrationConfig,
    _context_flip_lookup,
    _predictable_process_weights,
    _simulate_scenario,
)


def test_candidate_rules_flip_balanced_contexts_and_each_incumbent_action():
    lookup = _context_flip_lookup(torch.device("cpu"))
    incumbent_one = (torch.arange(32) & 1).bool()
    assert torch.equal(lookup.sum(dim=0), torch.full((13,), 16))
    assert torch.equal(
        lookup[incumbent_one].sum(dim=0),
        torch.full((13,), 8),
    )
    assert torch.equal(
        lookup[~incumbent_one].sum(dim=0),
        torch.full((13,), 8),
    )


def test_constructed_null_and_alternatives_have_exact_expected_gains_and_variance():
    contexts = torch.arange(32)
    incumbent = (contexts & 1).numpy().astype(int)
    flips = _context_flip_lookup(torch.device("cpu")).numpy()
    candidates = incumbent[:, None] ^ flips
    for p_one, p_zero, expected_mean in (
        (0.10, 0.10, 0.0),
        (0.06, 0.14, 0.12),
        (0.14, 0.06, -0.12),
    ):
        p = np.where(incumbent == 1, p_one, p_zero)
        incumbent_y0 = np.where(incumbent == 1, 1.0, 0.0)
        candidate_y0 = np.where(candidates == 1, 1.0, 0.0)
        incumbent_y1 = np.where(incumbent == 1, 0.0, 5.0)
        candidate_y1 = np.where(candidates == 1, 0.0, 5.0)
        gain_y0 = incumbent_y0[:, None] - candidate_y0
        gain_y1 = incumbent_y1[:, None] - candidate_y1
        conditional_mean = (1 - p[:, None]) * gain_y0 + p[:, None] * gain_y1
        assert np.allclose(conditional_mean.mean(axis=0), expected_mean)
        assert np.any(gain_y0 != gain_y1)


def test_online_process_weights_are_normalized_predictable_and_exploration_hedged():
    past_log_evalues = torch.tensor([[0.0, 0.0, 0.0, 0.0], [100.0, -5.0, 2.0, 0.0]])
    weights = _predictable_process_weights(past_log_evalues)
    assert torch.allclose(weights.sum(dim=-1), torch.ones(2, dtype=weights.dtype))
    assert torch.all(weights >= 0.025)
    assert torch.allclose(weights[0], torch.full((4,), 0.25, dtype=weights.dtype))


def test_non_degenerate_null_grid_respects_hard_caps_and_emits_all_rules():
    config = CalibrationConfig(streams=100, horizon=100, seed=101, device="cpu")
    generator = torch.Generator(device="cpu").manual_seed(config.seed)
    shape = (config.horizon, config.streams)
    contexts = torch.randint(0, 32, shape, generator=generator)
    outcomes = torch.rand(shape, generator=generator, dtype=torch.float64)
    queries = torch.rand(shape, generator=generator, dtype=torch.float64)
    rows = _simulate_scenario(
        scenario="aggregate_zero",
        p_incumbent_one=0.1,
        p_incumbent_zero=0.1,
        true_mean_gain=0.0,
        contexts=contexts,
        outcome_uniforms=outcomes,
        query_uniforms=queries,
        config=config,
        device=torch.device("cpu"),
    )
    assert len(rows) == 100 * 3 * 3 * 3 * 7
    assert {row["candidate_count"] for row in rows} == {1, 5, 13}
    assert {row["rule"] for row in rows} == {
        "fixed_mixture",
        "fixed_mixture_half_alpha",
        "predictable_kelly",
        "pm_eb",
        "positive_betting",
        "hedged_positive",
        "online_process_mixture",
    }
    assert all(row["true_mean_gain"] == 0.0 for row in rows)
    assert all(row["labels_used"] <= row["label_cap"] for row in rows)
    assert all(row["false_promotion"] == row["familywise_crossed"] for row in rows)
