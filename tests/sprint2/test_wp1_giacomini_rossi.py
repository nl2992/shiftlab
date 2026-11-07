import numpy as np
import pytest

from scripts.sota_sprint.wp1_giacomini_rossi import gr_one_time_reversal


def test_gr_constant_zero_loss_differences_have_no_rejection():
    out = gr_one_time_reversal(np.zeros(2000))
    assert out["valid"] is False
    assert out["reason"] == "nonpositive_or_nonfinite_HAC_variance"


def test_gr_detects_strong_single_reversal_in_known_series():
    d = np.r_[np.full(1000, 0.5), np.full(1000, -0.5)]
    out = gr_one_time_reversal(d)
    assert out["valid"] is True
    assert out["reject"] is True
    assert out["LM2_reject"] is True
    assert 850 <= out["break_index_0based"] <= 1150
    assert out["pre_break_mean"] > 0 > out["post_break_mean"]


def test_gr_hac_uses_raw_loss_difference_cross_products_under_zero_mean_null():
    x = np.full(2000, 0.25)
    out = gr_one_time_reversal(x)
    lag = out["lag"]
    expected = 0.25 ** 2 * (1 + 2 * sum((1 - k / (lag + 1)) * (len(x) - k) / len(x)
                                        for k in range(1, lag + 1)))
    assert out["lrv"] == pytest.approx(expected)


def test_gr_rejects_unsupported_alpha_and_short_series():
    with pytest.raises(ValueError):
        gr_one_time_reversal(np.ones(100), alpha=0.025)
    with pytest.raises(ValueError):
        gr_one_time_reversal(np.arange(10.0))
