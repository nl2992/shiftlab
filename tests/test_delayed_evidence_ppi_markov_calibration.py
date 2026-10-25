import numpy as np

from shiftlab.dive.delayed_evidence_directed_ppi import Config
from shiftlab.dive.delayed_evidence_directed_ppi_markov_calibration import generate


def test_markov_variance_null_has_persistent_scale_and_fresh_fair_signs():
    config = Config(n_source=180, n_target=800, max_delay=4, device="cpu")
    _, _, _, outcomes, _, _, regimes, _ = generate(config, seed=501)
    amplitudes = np.abs(outcomes)
    assert np.allclose(np.unique(amplitudes), [0.55, 1.0])
    assert np.corrcoef(regimes[:-1], regimes[1:])[0, 1] > 0.7
    signs = outcomes / amplitudes
    assert abs(float(signs.mean())) < 0.15
