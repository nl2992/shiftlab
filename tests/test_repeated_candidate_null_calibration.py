import torch

from scripts.calibrate_repeated_candidate_nulls import (
    CalibrationConfig,
    _context_flip_lookup,
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
    assert len(rows) == 100 * 3 * 3 * 3 * 6
    assert {row["candidate_count"] for row in rows} == {1, 5, 13}
    assert {row["rule"] for row in rows} == {
        "fixed_mixture",
        "fixed_mixture_half_alpha",
        "predictable_kelly",
        "pm_eb",
        "positive_betting",
        "hedged_positive",
    }
    assert all(row["true_mean_gain"] == 0.0 for row in rows)
    assert all(row["labels_used"] <= row["label_cap"] for row in rows)
    assert all(row["false_promotion"] == row["familywise_crossed"] for row in rows)
