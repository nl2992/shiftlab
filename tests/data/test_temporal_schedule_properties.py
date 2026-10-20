import numpy as np
import pytest
from scipy.special import expit

from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic.generators import STATIONARY, schedule

PATTERNS = [
    "abrupt",
    "multiple",
    "linear",
    "sigmoid",
    "recurring",
    "hmm",
    "seasonal",
    "temporary",
    "variable_dwell",
    "oblivious_adversarial",
]


@pytest.mark.parametrize("pattern", PATTERNS)
def test_schedule_weights_and_recorded_boundaries_match_pattern_definition(pattern):
    config = SyntheticConfig(
        n=5000,
        scenario="concept",
        pattern=pattern,
        seed=173,
        regimes=5,
        review_period=100,
        change_fraction=0.4,
        transition_fraction=0.1,
    )
    weights, truth = schedule(config)
    t = np.arange(config.n)
    tau, width = int(config.n * config.change_fraction), int(config.n * config.transition_fraction)
    if pattern == "abrupt":
        expected = (t >= tau).astype(float)
    elif pattern == "multiple":
        cuts = np.linspace(0, config.n, config.regimes + 1, dtype=int)[1:-1]
        expected = np.searchsorted(cuts, t, side="right") / (config.regimes - 1)
    elif pattern == "linear":
        expected = np.clip((t - tau) / width, 0, 1)
    elif pattern == "sigmoid":
        u = np.clip((t - tau) / width, 0, 1)
        expected = (expit(12 * (u - 0.5)) - expit(-6)) / (expit(6) - expit(-6))
    elif pattern == "recurring":
        cuts = np.linspace(0, config.n, config.regimes + 1, dtype=int)[1:-1]
        expected = np.searchsorted(cuts, t, side="right") % 2
    elif pattern == "seasonal":
        expected = np.where(t < tau, 0.0, 0.5 * (1 - np.cos(2 * np.pi * (t - tau) / width)))
    elif pattern == "temporary":
        expected = ((t >= tau) & (t < tau + width)).astype(float)
    elif pattern == "variable_dwell":
        cuts = np.sort(
            np.random.default_rng(config.seed + 900).choice(
                np.arange(1, config.n), config.regimes - 1, replace=False
            )
        )
        expected = np.searchsorted(cuts, t, side="right") % 2
    elif pattern == "oblivious_adversarial":
        cuts = np.arange(1, config.n, config.review_period)
        cuts = cuts[cuts >= tau]
        expected = np.searchsorted(cuts, t, side="right") % 2
    else:
        assert pattern == "hmm"
        assert set(np.unique(weights)) <= {0.0, 1.0}
        assert not np.any(np.diff(weights[:tau]) != 0)
        switches = np.flatnonzero(np.diff(weights) != 0) + 1
        assert truth["change_times"] == switches.tolist()
        assert truth["transition_intervals"] == []
        assert np.array_equal(weights, schedule(config)[0])
        return

    np.testing.assert_allclose(weights, expected, atol=1e-12)
    if pattern in {"linear", "sigmoid"}:
        assert truth["change_times"] == []
        assert truth["transition_intervals"] == [[tau, tau + width]]
    elif pattern == "seasonal":
        assert truth["change_times"] == []
        assert truth["transition_intervals"] == [[tau, config.n - 1]]
    else:
        expected_changes = (np.flatnonzero(np.diff(expected) != 0) + 1).tolist()
        assert truth["change_times"] == expected_changes
        assert truth["transition_intervals"] == []


@pytest.mark.parametrize("scenario", sorted(STATIONARY))
def test_stationary_scenarios_override_nonstationary_weight_schedules(scenario):
    config = SyntheticConfig(
        n=2000,
        scenario=scenario,
        pattern="recurring",
        regimes=5,
        severity=3,
    )
    weights, truth = schedule(config)
    assert not weights.any()
    assert truth == {"change_times": [], "transition_intervals": []}


def test_zero_strength_clears_temporal_schedule_regardless_of_pattern():
    for pattern in PATTERNS:
        config = SyntheticConfig(
            n=2000,
            scenario="concept",
            pattern=pattern,
            severity=0,
            regimes=5,
        )
        weights, truth = schedule(config)
        assert not weights.any()
        assert truth == {"change_times": [], "transition_intervals": []}


def test_hidden_markov_switch_frequency_matches_configured_dwell_rate():
    n, tau, width = 30000, 6000, 600
    switch_rates = []
    for seed in [11, 23, 37, 53, 71]:
        config = SyntheticConfig(
            n=n,
            scenario="concept",
            pattern="hmm",
            seed=seed,
            change_fraction=tau / n,
            transition_fraction=width / n,
        )
        weights, truth = schedule(config)
        changes = np.flatnonzero(np.diff(weights) != 0) + 1
        assert not np.any(changes < tau)
        assert truth["change_times"] == changes.tolist()
        switch_rates.append(float(np.mean(np.diff(weights[tau:]) != 0)))
    expected_rate = 1 / width
    tolerance = 5 * np.sqrt(expected_rate * (1 - expected_rate) / (5 * (n - tau)))
    assert abs(np.mean(switch_rates) - expected_rate) < tolerance
