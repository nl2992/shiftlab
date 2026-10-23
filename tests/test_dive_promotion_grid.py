import numpy as np
import pandas as pd

from scripts.analyze_promotion_grid import summarize
from shiftlab.dive.promotion_grid import (
    PromotionGridConfig,
    _fixed_horizon_gate,
    run_promotion_grid,
)


def test_fixed_horizon_gate_distinguishes_clear_benefit_from_null():
    assert not _fixed_horizon_gate(np.zeros(100), bound=1.0, alpha=0.05)
    assert _fixed_horizon_gate(np.full(100, 0.5), bound=1.0, alpha=0.05)


def test_candidate_grid_is_frozen_and_outputs_forward_deployment_metrics(tmp_path):
    config = PromotionGridConfig(
        n=1000,
        d=8,
        seeds=1,
        seed_offset=770001,
        scenario_subset=("stationary",),
        device="cpu",
    )
    report_path = run_promotion_grid(config, tmp_path)
    candidate_path = tmp_path / "metrics/promotion_grid_candidates.parquet"
    strategy_path = tmp_path / "metrics/promotion_grid_strategies.parquet"
    assert report_path.is_file()
    candidates = pd.read_parquet(candidate_path)
    strategies = pd.read_parquet(strategy_path)
    assert len(candidates) == 1 + 4 * 3
    assert candidates.candidate_index_validation_rank.tolist() == list(range(1, 14))
    assert candidates.alpha_i.sum() <= config.alpha
    assert candidates.exact_policy_copy_null.any()
    assert candidates.training_cutoff.max() < candidates.validation_end.min()
    assert candidates.validation_end.nunique() == 1
    assert candidates.monitor_start.min() == candidates.validation_end.iloc[0]
    assert (candidates.monitor_end > candidates.monitor_start).all()
    assert set(strategies.strategy) == {
        "never_promote",
        "validation_always_promote",
        "fixed_horizon_grid_gate",
        "sequential_grid_gate",
    }
    assert np.isfinite(strategies.post_expected_net_gain_total).all()


def test_promotion_grid_summary_uses_seed_paired_intervals(tmp_path):
    input_dir = tmp_path / "run"
    metrics = input_dir / "metrics"
    metrics.mkdir(parents=True)
    rows = []
    values = {
        "never_promote": (0.0, 0.0),
        "sequential_grid_gate": (2.0, 4.0),
        "validation_always_promote": (2.0, 4.0),
    }
    for strategy, gains in values.items():
        for seed, gain in enumerate(gains, start=1):
            rows.append(
                {
                    "scenario": "test",
                    "seed": seed,
                    "strategy": strategy,
                    "promoted": strategy != "never_promote",
                    "post_expected_net_gain_total": gain,
                    "post_realized_net_gain_total": gain,
                    "false_promotion_post_nongain": False,
                }
            )
    pd.DataFrame(rows).to_parquet(metrics / "promotion_grid_strategies.parquet", index=False)

    report = summarize(input_dir, tmp_path / "summary.md").read_text(encoding="utf-8")

    assert "sequential − never | 3.000 [-9.706, 15.706]" in report
    assert "sequential − always | 0.000 [0.000, 0.000]" in report
