import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location("confirmation_draft", Path(__file__).with_name("sota_confirmation_draft.py"))
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


def test_exact_zero_error_bound_and_familywise_monotonicity():
    assert draft.binomial_upper(0, 2000) == pytest.approx(1 - 0.05 ** (1 / 2000))
    assert draft.binomial_upper(0, 2000, family_size=20) > draft.binomial_upper(0, 2000)
    assert draft.binomial_upper(2000, 2000) == 1
    with pytest.raises(ValueError):
        draft.binomial_upper(1, 0)


def test_bootstrap_preserves_world_pairing():
    x = np.arange(100, dtype=float)
    result = draft.paired_world_interval(x + 2, x, replications=200)
    assert result["mean_difference"] == result["lower"] == result["upper"] == 2
    with pytest.raises(ValueError):
        draft.paired_world_interval(np.zeros((2, 2)), np.zeros((2, 2)))


def test_freeze_refuses_overwrite_provenance_change_and_mutated_candidate(tmp_path):
    path = tmp_path / "freeze.json"
    params = dict(candidates=[{"mechanism": "fixture"}], source_hash="a" * 64,
                  generator_hash="b" * 64, seed_specification={"namespace": "fixture_only"},
                  protocol_hash="c" * 64)
    digest = draft.freeze(path, **params)
    check = {key: params[key] for key in ("source_hash", "generator_hash", "protocol_hash")}
    draft.require_freeze(path, expected_body_hash=digest, **check)
    with pytest.raises(FileExistsError):
        draft.freeze(path, **params)
    with pytest.raises(ValueError, match="changed"):
        draft.require_freeze(path, expected_body_hash=digest, **{**check, "source_hash": "d" * 64})
    payload = json.loads(path.read_text())
    payload["body"]["candidates"][0]["mechanism"] = "changed"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="mismatch"):
        draft.require_freeze(path, expected_body_hash=digest, **check)
