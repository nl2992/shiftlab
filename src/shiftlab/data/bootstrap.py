"""Moving-block bootstrap for descriptive mean differences within approximately stationary windows."""

import numpy as np


def mean_difference_interval(reference, current, block_length=None, repeats=500, seed=42):
    """Return percentile interval; assumes weak dependence and stationarity within each window.

    This does not correct confounding, missing-data selection, multiple comparisons or regime
    changes inside a window. Independent samples from overlapping block means approximate means
    of concatenated moving-block resamples without materializing full resampled series.
    """
    a, b = np.asarray(reference, dtype=float), np.asarray(current, dtype=float)
    if min(len(a), len(b)) < 20 or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Need >=20 finite observations per window")
    length = block_length or max(2, int(np.sqrt(min(len(a), len(b)))))
    if not 1 <= length <= min(len(a), len(b)):
        raise ValueError("Invalid block length")
    rng = np.random.default_rng(seed)
    samples = []
    for values in [a, b]:
        block_means = np.convolve(values, np.ones(length) / length, mode="valid")
        samples.append(
            rng.choice(
                block_means, size=(repeats, int(np.ceil(len(values) / length))), replace=True
            ).mean(axis=1)
        )
    lower, upper = np.quantile(samples[1] - samples[0], [0.025, 0.975])
    return {
        "mean_difference_ci_low": float(lower),
        "mean_difference_ci_high": float(upper),
        "bootstrap_block_length": length,
        "bootstrap_repeats": repeats,
    }
