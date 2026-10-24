import pytest

from shiftlab.dive.start_prior_robust_mix import (
    StartPriorRobustMixConfig,
    mixture_weights,
    run_start_prior_robust_mix,
)


@pytest.mark.parametrize("rho", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_fixed_prior_blends_are_convex_and_match_endpoints(rho):
    weights = mixture_weights(rho)
    assert len(weights) == 8
    assert all(weight > 0 for weight in weights)
    assert sum(weights) == pytest.approx(1.0)


def test_prior_blend_rejects_invalid_mixture_weight():
    with pytest.raises(ValueError, match="rho"):
        mixture_weights(-0.01)


def test_cpu_smoke_writes_development_artifacts(tmp_path):
    alternatives, ranking, manifest = run_start_prior_robust_mix(
        tmp_path,
        StartPriorRobustMixConfig(
            streams_per_cell=1,
            null_streams=2,
            alternative_seed_offset=20290000,
            null_seed_offset=20291000,
            n_events=120,
            device="cpu",
        ),
    )
    assert len(alternatives) == 18 * 5
    assert set(ranking.rho) == {0.0, 0.25, 0.5, 0.75, 1.0}
    assert manifest["selected_rho_development_only"] in {0.0, 0.25, 0.5, 0.75, 1.0}
    assert (tmp_path / "alternative_metrics.parquet").is_file()
    assert (tmp_path / "null_metrics.parquet").is_file()
