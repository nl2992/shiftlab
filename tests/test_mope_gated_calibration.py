from __future__ import annotations

import numpy as np

from scripts.reproduce_mope_gated_calibration import (
    build_cell_streams,
    exact_binomial_interval,
    paired_bootstrap_interval,
    validate_mope_path,
)
from scripts.verify_mope_gated_calibration import bootstrap_interval, cp_interval, cp_upper


def test_context_design_has_registered_zero_and_nonzero_value_contrasts() -> None:
    gain_by_context = 0.24
    assert np.isclose(gain_by_context * (2 * 0.50 - 1), 0.0)
    assert np.isclose(gain_by_context * (2 * 0.75 - 1), 0.12)
    assert np.isclose(gain_by_context * (2 * 0.25 - 1), -0.12)


def test_stream_builder_uses_target_over_logger_weights_and_binary_rewards() -> None:
    uniforms = np.array(
        [
            [
                [0.1, 0.1, 0.05],
                [0.1, 0.9, 0.20],
                [0.9, 0.1, 0.50],
                [0.9, 0.9, 0.95],
            ]
        ]
    )

    streams = build_cell_streams(uniforms, context1_probability=0.5)

    assert np.allclose(streams[0, :, 0], [1.6, 0.4, 0.4, 1.6])
    assert np.array_equal(streams[0, :, 1], [1.0, 0.0, 1.0, 0.0])
    assert np.all((streams[:, :, 0] >= 0.4 - 1e-12) & (streams[:, :, 0] <= 1.6 + 1e-12))


def test_stream_builder_rejects_invalid_uniforms() -> None:
    with np.testing.assert_raises(ValueError):
        build_cell_streams(np.array([[[1.0, 0.5, 0.5]]]), context1_probability=0.5)


def test_exact_binomial_interval_handles_zero_and_all_successes() -> None:
    lower0, upper0 = exact_binomial_interval(0, 1000)
    lower1, upper1 = exact_binomial_interval(1000, 1000)

    assert lower0 == 0.0 and 0.0 < upper0 < 0.01
    assert lower1 < 1.0 and upper1 == 1.0


def test_empty_mope_confidence_set_is_recorded_not_treated_as_path_error() -> None:
    lower = np.array([-0.2, -0.1, 0.2])
    upper = np.array([0.3, 0.1, 0.1])

    assert validate_mope_path(lower, upper, horizon=3)


def test_mope_path_rejects_nonmonotone_endpoints() -> None:
    lower = np.array([-0.2, -0.3, 0.0])
    upper = np.array([0.3, 0.2, 0.1])

    with np.testing.assert_raises(RuntimeError):
        validate_mope_path(lower, upper, horizon=3)


def test_independent_verifier_recomputes_exact_and_paired_intervals() -> None:
    assert cp_interval(0, 1000) == exact_binomial_interval(0, 1000)
    assert cp_upper(0, 1000, 1 - 0.05 / 7) < 0.01
    values = np.array([0.0, 1.0, -1.0, 1.0])
    assert bootstrap_interval(values, seed=42, replicates=100) == paired_bootstrap_interval(
        values, seed=42, replicates=100
    )
