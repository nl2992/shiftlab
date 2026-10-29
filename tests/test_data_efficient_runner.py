import numpy as np
import pytest

from scripts.run_data_efficient_prescreen import endpoint, original_alarms
from shiftlab.dive import data_efficient_source_panel as source


@pytest.mark.parametrize("fraction,expected", [(0.75, 0.8125), (0.50, 0.625)])
def test_late_onset_clock_is_monitor_relative(monkeypatch, fraction, expected):
    def generator(scenario, seed, config):
        assert scenario.name == "boundary_local_harm"
        assert config.change_fraction == expected
        assert config.n == 3200
        assert seed == 123
        raise RuntimeError("stop before any generation")

    monkeypatch.setattr(source, "_generate", generator)
    with pytest.raises(RuntimeError, match="stop before"):
        source.build_path(123, fraction, "cpu")


def test_pre_onset_alarm_and_budget_stop_do_not_improve_censored_delay():
    assert endpoint(1799, 1800) == {
        "first_alarm": 1799,
        "detected": False,
        "pre_onset_alarm": True,
        "delay_censored": 600,
    }
    assert endpoint(None, 1800)["delay_censored"] == 600
    assert endpoint(1800, 1800)["delay_censored"] == 0
    assert endpoint(2399, 1800)["delay_censored"] == 599


def test_neutral_source_tail_opens_sr_starts_without_false_alarm():
    record = {
        "source_original_logs": np.zeros(3),
        "values": np.zeros(3),
        "bounds": np.ones(3),
        "arm": "ppe_uniform",
    }
    rows = original_alarms(record)
    assert len(rows) == 4
    assert all(alarm is None for _, _, alarm in rows)
