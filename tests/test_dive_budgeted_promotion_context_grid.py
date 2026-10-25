import pandas as pd

from shiftlab.dive.budgeted_promotion_context_grid import _macro_signal_contrasts


def test_context_grid_macro_contrasts_average_fixed_cells_with_seed_pairing():
    rows = []
    for prevalence in (0.1, 0.5, 0.9):
        for signal in (0.05, 0.10):
            for error in (0.0, 0.1, 0.25):
                scenario = f"p{prevalence}-s{signal}-e{error}"
                for seed in (1, 2, 3):
                    for allocation, gain in (
                        ("rank", float(seed)),
                        ("rank_context_equal", float(seed) + 1),
                        ("rank_context_volume", float(seed) + 2),
                    ):
                        rows.append(
                            {
                                "scenario": scenario,
                                "context_signal_strength": signal,
                                "budget_rate": 0.4,
                                "seed": seed,
                                "alpha_allocation": allocation,
                                "expected_postpromotion_net_gain": gain,
                            }
                        )
    contrasts = _macro_signal_contrasts(pd.DataFrame(rows), draws=1000).set_index("contrast")
    assert contrasts.loc["rank_context_volume_minus_rank", "mean_paired_difference"] == 2.0
    assert (
        contrasts.loc["rank_context_volume_minus_rank_context_equal", "mean_paired_difference"]
        == 1.0
    )
    assert contrasts.n_settings.eq(18).all()
    assert contrasts.n_seed_blocks.eq(3).all()
    assert contrasts.bootstrap_ci_low.eq(contrasts.bootstrap_ci_high).all()
