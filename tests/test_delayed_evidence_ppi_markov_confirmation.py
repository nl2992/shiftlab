import json
from pathlib import Path

import numpy as np
import pytest

from shiftlab.dive.delayed_evidence_directed_ppi import Config
from shiftlab.dive.delayed_evidence_ppi_markov_confirmation import (
    HARM_SHIFT,
    _harm_outcomes,
    run,
)


def test_markov_harm_outcomes_have_registered_conditional_mean_and_support():
    count = 40_000
    regimes = np.tile(np.array([0, 1]), count // 2)
    outcomes = _harm_outcomes(
        Config(n_target=count, device="cpu"),
        seed=812,
        regimes=regimes,
        onset=count // 2,
    )
    amplitudes = np.where(regimes == 1, 1.0, 0.55)
    assert np.all(np.isclose(np.abs(outcomes), amplitudes))
    assert abs(float(outcomes[: count // 2].mean())) < 0.015
    for regime in (0, 1):
        post_mean = float(outcomes[count // 2 :][regimes[count // 2 :] == regime].mean())
        assert post_mean == pytest.approx(HARM_SHIFT, abs=0.015)
    assert np.allclose(np.abs(outcomes), amplitudes)


def test_markov_harm_confirmation_smoke_matches_passing_calibration(tmp_path: Path):
    root = Path(__file__).parents[1]
    calibration = root / "outputs/delayed_evidence_ppi_markov_calibration_1000/manifest.json"
    output = tmp_path / "markov_harm_smoke"
    run(
        Config(seeds=2, seed_offset=20292000, device="cpu"),
        output,
        calibration_manifest=calibration,
    )
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["rows"] == 4
    assert manifest["scenario"] == "boundary_harm"
    assert manifest["result"]["candidate_mean_labels"] <= 480
    assert manifest["result"]["uniform_mean_labels"] <= 480


def test_markov_harm_confirmation_refuses_wrong_harm_shift(tmp_path: Path):
    config = Config(seeds=2, seed_offset=20292000, harm_shift=0.1, device="cpu")
    with pytest.raises(ValueError, match="frozen Markov alternative"):
        run(
            config,
            tmp_path / "bad_harm",
            calibration_manifest=Path("missing-manifest.json"),
        )
