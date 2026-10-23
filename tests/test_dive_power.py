import pytest

from shiftlab.dive.power import paired_mcnemar_power, paired_mcnemar_sample_size


def test_paired_mcnemar_power_and_sample_size_are_monotone():
    kwargs = {
        "discordance_probability": 0.10,
        "candidate_win_probability_given_discordance": 5 / 6,
        "alpha": 0.05,
    }
    assert paired_mcnemar_power(60, **kwargs) == pytest.approx(0.3096097, abs=1e-6)
    assert paired_mcnemar_power(120, **kwargs) > paired_mcnemar_power(60, **kwargs)
    seeds = paired_mcnemar_sample_size(target_power=0.80, **kwargs)
    assert seeds == 151
    assert paired_mcnemar_power(seeds, **kwargs) >= 0.80
    assert paired_mcnemar_power(seeds - 1, **kwargs) < 0.80


def test_paired_mcnemar_power_rejects_invalid_planning_inputs():
    with pytest.raises(ValueError, match="discordance_probability"):
        paired_mcnemar_power(
            10,
            discordance_probability=0,
            candidate_win_probability_given_discordance=0.8,
        )
    with pytest.raises(ValueError, match="must exceed 0.5"):
        paired_mcnemar_power(
            10,
            discordance_probability=0.1,
            candidate_win_probability_given_discordance=0.5,
        )
