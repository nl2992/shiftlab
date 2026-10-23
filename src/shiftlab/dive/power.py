"""Exact planning calculations for paired binary detection outcomes."""

from __future__ import annotations

import numpy as np
from scipy.stats import binom


def paired_mcnemar_power(
    seeds: int,
    *,
    discordance_probability: float,
    candidate_win_probability_given_discordance: float,
    alpha: float = 0.05,
) -> float:
    """Exact prospective power for a one-sided paired McNemar test of equal rates.

    Seeds are independent clusters. Each seed is concordant with probability
    1 minus discordance_probability; conditional on discordance, the candidate wins
    with the supplied probability. The null is equality of paired marginal detection
    probabilities (candidate-minus-reference equals zero), not a positive-margin null.
    """
    if isinstance(seeds, bool) or not isinstance(seeds, (int, np.integer)) or seeds < 1:
        raise ValueError("seeds must be a positive integer")
    if not 0 < discordance_probability <= 1:
        raise ValueError("discordance_probability must lie in (0, 1]")
    if not 0.5 < candidate_win_probability_given_discordance <= 1:
        raise ValueError("candidate win probability must exceed 0.5 and be at most 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")

    discordant = np.arange(seeds + 1)
    conditional_power = np.zeros(seeds + 1, dtype=float)
    for count in discordant[1:]:
        wins = np.arange(count + 1)
        p_null_upper = binom.sf(wins - 1, count, 0.5)
        critical = np.flatnonzero(p_null_upper <= alpha)
        if critical.size:
            first_rejection = int(critical[0])
            conditional_power[count] = binom.sf(
                first_rejection - 1,
                count,
                candidate_win_probability_given_discordance,
            )
    return float(
        np.dot(
            binom.pmf(discordant, seeds, discordance_probability),
            conditional_power,
        )
    )


def paired_mcnemar_sample_size(
    *,
    discordance_probability: float,
    candidate_win_probability_given_discordance: float,
    target_power: float = 0.80,
    alpha: float = 0.05,
    maximum_seeds: int = 10_000,
) -> int:
    """Smallest independent seed count achieving target plug-in McNemar power."""
    if not 0 < target_power < 1:
        raise ValueError("target_power must lie in (0, 1)")
    if isinstance(maximum_seeds, bool) or not isinstance(maximum_seeds, int) or maximum_seeds < 1:
        raise ValueError("maximum_seeds must be a positive integer")
    for seeds in range(1, maximum_seeds + 1):
        if (
            paired_mcnemar_power(
                seeds,
                discordance_probability=discordance_probability,
                candidate_win_probability_given_discordance=candidate_win_probability_given_discordance,
                alpha=alpha,
            )
            >= target_power
        ):
            return seeds
    raise ValueError("target power was not reached by maximum_seeds")
