from scripts.calibrate_comparecast_weak_null import _cp_upper


def test_simultaneous_exact_upper_bound_is_below_alpha_for_zero_alarms():
    upper = _cp_upper(successes=0, trials=2000, alpha=0.025)

    assert 0 < upper < 0.05


def test_exact_upper_bound_is_one_when_every_stream_alarms():
    assert _cp_upper(successes=20, trials=20, alpha=0.025) == 1.0
