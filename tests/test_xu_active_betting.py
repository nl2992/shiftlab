from __future__ import annotations

import math

import pytest

from shiftlab.dive.xu_active_betting import (
    XuActivePairedEProcess,
    xu_maximum_stake,
    xu_minimum_query_probability,
    xu_paired_betting_factor,
    xu_variance_query_policy,
)


def test_factor_matches_xu_paper_after_paired_cost_affine_transform() -> None:
    bound = 4.0
    stake = 0.4
    q = 0.7
    proxy_z = 1.0
    observed_z = 2.0
    factor = xu_paired_betting_factor(
        proxy_excess_cost=proxy_z,
        queried=True,
        propensity=q,
        stake=stake,
        bound=bound,
        observed_excess_cost=observed_z,
    )

    # Xu: 1 + λ(θ - rhat_R - L/q(R-rhat_R));
    # R=1/2-Z/(2B), θ=1/2, rhat_R=1/2-proxy_z/(2B).
    expected = 1 + stake * (
        proxy_z / (2 * bound) + (observed_z / (2 * bound) - proxy_z / (2 * bound)) / q
    )
    assert factor == pytest.approx(expected)
    assert factor > 0


def test_query_no_query_average_recovers_full_feedback_base_factor() -> None:
    q, stake, bound, proxy, observed = 0.4, 0.4, 5.0, -1.0, 2.0
    queried = xu_paired_betting_factor(
        proxy_excess_cost=proxy,
        queried=True,
        propensity=q,
        stake=stake,
        bound=bound,
        observed_excess_cost=observed,
    )
    skipped = xu_paired_betting_factor(
        proxy_excess_cost=proxy,
        queried=False,
        propensity=q,
        stake=stake,
        bound=bound,
    )
    assert q * queried + (1 - q) * skipped == pytest.approx(1 + stake * observed / (2 * bound))


def test_full_feedback_q_one_reduces_to_unpredicted_xu_factor() -> None:
    stake, bound, proxy, observed = 1.1, 3.0, 2.0, -1.5
    factor = xu_paired_betting_factor(
        proxy_excess_cost=proxy,
        queried=True,
        propensity=1.0,
        stake=stake,
        bound=bound,
        observed_excess_cost=observed,
    )
    assert factor == pytest.approx(1 + stake * observed / (2 * bound))


def test_xu_query_floor_and_stake_cap_are_inverse() -> None:
    for q_min in (0.2, 0.5, 1.0):
        cap = xu_maximum_stake(minimum_propensity=q_min)
        assert xu_minimum_query_probability(stake=cap) == pytest.approx(q_min)
        assert xu_minimum_query_probability(stake=0.8 * cap) < q_min


def test_stake_below_floor_cap_keeps_extreme_corrected_factor_positive() -> None:
    q_min = 0.25
    stake = 0.9 * xu_maximum_stake(minimum_propensity=q_min)
    factor = xu_paired_betting_factor(
        proxy_excess_cost=1.0,
        queried=True,
        propensity=q_min,
        stake=stake,
        bound=1.0,
        observed_excess_cost=-1.0,
    )
    assert factor > 0


def test_source_stake_cap_allows_zero_factor_at_support_endpoint() -> None:
    q_min = 0.25
    cap = xu_maximum_stake(minimum_propensity=q_min)
    factor = xu_paired_betting_factor(
        proxy_excess_cost=1.0,
        queried=True,
        propensity=q_min,
        stake=cap,
        bound=1.0,
        observed_excess_cost=-1.0,
    )
    assert factor == pytest.approx(0.0, abs=1e-12)


def test_process_accepts_cap_endpoint_and_tracks_zero_in_log_wealth() -> None:
    q_min = 0.25
    cap = xu_maximum_stake(minimum_propensity=q_min)
    process = XuActivePairedEProcess(
        bound=1.0,
        stake=cap,
        minimum_propensity=q_min,
    )
    assert (
        process.update(
            proxy_excess_cost=1.0,
            queried=True,
            propensity=q_min,
            observed_excess_cost=-1.0,
        )
        == 0.0
    )
    assert process.log_wealth == float("-inf")


def test_process_full_query_matches_q_one_factor_and_log_product() -> None:
    process = XuActivePairedEProcess(bound=2.0, stake=0.5, minimum_propensity=0.5)
    f1 = xu_paired_betting_factor(
        proxy_excess_cost=0.4,
        queried=True,
        propensity=1.0,
        stake=0.5,
        bound=2.0,
        observed_excess_cost=1.0,
    )
    f2 = xu_paired_betting_factor(
        proxy_excess_cost=-0.4,
        queried=True,
        propensity=1.0,
        stake=0.5,
        bound=2.0,
        observed_excess_cost=-0.5,
    )
    process.update(
        proxy_excess_cost=0.4,
        queried=True,
        propensity=1.0,
        observed_excess_cost=1.0,
    )
    wealth = process.update(
        proxy_excess_cost=-0.4,
        queried=True,
        propensity=1.0,
        observed_excess_cost=-0.5,
    )
    assert process.log_wealth == pytest.approx(math.log(f1) + math.log(f2))
    assert wealth == pytest.approx(f1 * f2)


def test_process_accumulates_factors_and_does_not_receive_skipped_label() -> None:
    process = XuActivePairedEProcess(bound=2.0, stake=0.5, minimum_propensity=0.42)
    first = process.update(
        proxy_excess_cost=0.2,
        queried=False,
        propensity=0.45,
    )
    second = process.update(
        proxy_excess_cost=0.3,
        queried=True,
        propensity=0.45,
        observed_excess_cost=1.0,
    )
    assert first == pytest.approx(1 + 0.5 * 0.2 / 4)
    assert second == pytest.approx(first * (1 + 0.5 * (0.3 / 4 + (1 / 4 - 0.3 / 4) / 0.45)))
    assert process.log_wealth == pytest.approx(math.log(second))
    with pytest.raises(ValueError, match="must not be supplied"):
        process.update(
            proxy_excess_cost=0.0,
            queried=False,
            propensity=0.45,
            observed_excess_cost=0.1,
        )


def test_variance_query_wrapper_uses_sqrt_residual_moment_and_valid_floor() -> None:
    policy = xu_variance_query_policy(
        target_rate=0.5,
        minimum_propensity=0.35,
        maximum_propensity=0.9,
        stake=0.4,
    )
    assert policy.method == "variance"
    assert policy.variance_power == pytest.approx(0.5)
    with pytest.raises(ValueError, match="validity floor"):
        xu_variance_query_policy(
            target_rate=0.2,
            minimum_propensity=0.1,
            maximum_propensity=0.8,
            stake=0.4,
        )
