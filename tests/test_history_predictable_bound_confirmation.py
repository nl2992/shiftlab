import numpy as np
import pytest

from scripts.confirm_history_predictable_query_bounds import (
    DEFAULT_SEED,
    exact_one_sided_upper,
    paired_bootstrap_interval,
    run_confirmation,
)


def test_exact_one_sided_upper_handles_zero_and_nonzero_counts():
    assert exact_one_sided_upper(0, 1000, 0.05) == pytest.approx(1 - 0.05 ** (1 / 1000))
    assert 0 < exact_one_sided_upper(5, 1000, 0.05) < 0.02


def test_paired_bootstrap_is_reproducible_and_centered():
    values = np.array([0.1, 0.2, 0.3, 0.4])
    first = paired_bootstrap_interval(values, seed=13)
    second = paired_bootstrap_interval(values, seed=13)
    assert first == second
    assert first[0] < values.mean() < first[1]


def test_confirmation_primary_margin_is_prespecified():
    from scripts.confirm_history_predictable_query_bounds import DEFAULT_STREAMS

    assert DEFAULT_SEED == 27104027
    assert DEFAULT_STREAMS == 4000


def test_confirmation_rejects_seed_overlap_with_development(tmp_path):
    with pytest.raises(ValueError, match="confirmation seeds must start"):
        run_confirmation(
            streams=100,
            seed=DEFAULT_SEED - 1,
            device_name="cpu",
            output=tmp_path / "overlap",
        )
