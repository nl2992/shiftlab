import numpy as np
import torch

from shiftlab.dive.eprocess import PredictableVarianceAdaptiveEProcess
from shiftlab.dive.residual_variance_pva_grid import (
    PVAConfig,
    _vectorized_pva,
    pva_grid,
)


def test_pva_grid_matches_scalar_reference_with_padded_streams():
    increments = np.asarray(
        [[0.2, -0.1, 0.3, np.nan], [-0.2, 0.1, -0.05, 0.25]],
        dtype=float,
    )
    bounds = np.asarray([1.0, 0.8])
    configs = (
        PVAConfig(1.0, 0.0, 0.05, 0.25),
        PVAConfig(4.0, 0.05, 0.25, 0.50),
        PVAConfig(16.0, 0.10, 0.75, 0.80),
    )

    result = _vectorized_pva(increments, bounds, configs, device=torch.device("cpu"))
    for config_index, candidate in enumerate(configs):
        for stream_index, bound in enumerate(bounds):
            reference = PredictableVarianceAdaptiveEProcess(
                bound=bound,
                prior_strength=candidate.prior_strength,
                prior_mean=candidate.prior_mean,
                prior_second_moment=candidate.prior_second_moment,
                max_stake=candidate.max_stake,
            )
            log_values = []
            first_crossing = -1
            for time, value in enumerate(increments[stream_index]):
                if not np.isfinite(value):
                    continue
                log_values.append(reference.update(float(value)))
                if first_crossing < 0 and reference.alarm:
                    first_crossing = time
            assert np.isclose(
                result["final_log_e"][config_index, stream_index], reference.log_e_value
            )
            assert np.isclose(
                result["peak_log_e"][config_index, stream_index], max(0.0, *log_values)
            )
            assert result["first_crossing"][config_index, stream_index] == first_crossing
            assert result["updates"][stream_index] == len(log_values)


def test_pva_development_grid_has_expected_cardinality_and_fixed_parameters():
    candidates = pva_grid()
    assert len(candidates) == 81
    assert len({candidate.name for candidate in candidates}) == 81
