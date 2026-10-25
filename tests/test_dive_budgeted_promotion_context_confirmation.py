import pandas as pd
import pytest

from shiftlab.dive.budgeted_promotion_context_confirmation import (
    METHODS,
    PREVALENCES,
    PROXY_ERRORS,
    SIGNAL_STRENGTHS,
    _macro_contrasts,
)


def _toy_confirmation_detail():
    rows = []
    for prevalence in PREVALENCES:
        for signal in SIGNAL_STRENGTHS:
            for error in PROXY_ERRORS:
                scenario = f"p{prevalence}-s{signal}-e{error}"
                for seed in (1, 2, 3):
                    for method, offset in zip(METHODS, (0.0, 1.0, 3.0), strict=True):
                        rows.append(
                            {
                                "scenario": scenario,
                                "seed": seed,
                                "alpha_allocation": method,
                                "expected_postpromotion_net_gain": seed + offset,
                            }
                        )
    return pd.DataFrame(rows)


def test_confirmation_macro_contrasts_preserve_seed_blocks_and_cell_weights():
    contrasts = _macro_contrasts(_toy_confirmation_detail(), draws=1000).set_index("contrast")
    assert contrasts.loc["scout_context_policy_minus_rank", "mean_paired_difference"] == 3.0
    assert (
        contrasts.loc["scout_context_policy_minus_rank_context_volume", "mean_paired_difference"]
        == 2.0
    )
    assert contrasts.n_settings.eq(18).all()
    assert contrasts.n_seed_blocks.eq(3).all()
    assert contrasts.bootstrap_ci_low.eq(contrasts.bootstrap_ci_high).all()


def test_confirmation_macro_contrasts_reject_incomplete_cell_families():
    detail = _toy_confirmation_detail().loc[lambda frame: frame.scenario.ne("p0.1-s0.05-e0.0")]
    with pytest.raises(ValueError, match="expected 18 positive-signal cells"):
        _macro_contrasts(detail, draws=1000)
