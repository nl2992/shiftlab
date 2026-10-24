from __future__ import annotations

import numpy as np

from scripts.analyze_pprm_block_mixture_confirmation import _holm, _paired_summary


def test_paired_summary_uses_matched_discordant_streams() -> None:
    result = _paired_summary(
        np.array([True, True, False, False]),
        np.array([True, False, True, False]),
    )
    assert result["streams"] == 4
    assert result["mixture_only"] == 1
    assert result["comparator_only"] == 1
    assert result["rate_difference_mixture_minus_comparator"] == 0
    assert result["difference_bootstrap_95_low"] <= 0 <= result["difference_bootstrap_95_high"]
    assert result["mcnemar_exact_p"] == 1


def test_holm_adjustment_is_monotone_and_never_below_raw_p() -> None:
    raw = [0.01, 0.04, 0.03]
    adjusted = _holm(raw)
    assert adjusted == [0.03, 0.06, 0.06]
    assert np.all(np.asarray(adjusted) >= raw)
