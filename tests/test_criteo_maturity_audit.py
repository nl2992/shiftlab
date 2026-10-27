import numpy as np

from scripts.audit_criteo_maturity import _curve_cutoffs


def test_curve_cutoffs_include_each_full_day_and_exact_stream_end():
    start = 0.0
    end = 2 * 86_400 + 12
    cutoffs = _curve_cutoffs(start, end)
    np.testing.assert_array_equal(cutoffs, [0.0, 86_400.0, 172_800.0, end])


def test_exact_day_span_does_not_add_duplicate_or_extra_cutoff():
    cutoffs = _curve_cutoffs(500.0, 500.0 + 3 * 86_400)
    assert len(cutoffs) == 4
    assert cutoffs[-1] - cutoffs[0] == 3 * 86_400
