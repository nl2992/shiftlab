import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "audit_b3", Path(__file__).resolve().parents[2] / "scripts/retrospective_audit/recompute_b3.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(episode, costs):
    return {
        "episode": episode,
        "setting": "test",
        "policies": {
            p: {"cost_seeds": costs, "mean_cost": float(np.mean(costs)), "mean_labels": 2}
            for p in ("P0", "P1", "P2", "P3b", "P6")
        },
    }


def test_duplicate_episode_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        module.reconstruct([row(0, [1, 2]), row(0, [1, 2])], "test", np.random.default_rng(1))


def test_inconsistent_raw_mean_rejected():
    r = row(0, [1, 2])
    r["policies"]["P0"]["mean_cost"] = 9
    with pytest.raises(ValueError, match="mean mismatch"):
        module.reconstruct([r], "test", np.random.default_rng(1))


def test_low_episode_count_keeps_conditional_scope():
    result = module.reconstruct([row(0, [1, 2])], "test", np.random.default_rng(1))
    assert result["paired"]["P3b_minus_P0"] == {"mean": 0.0, "lo": 0.0, "hi": 0.0}
    assert result["uncertainty_scope"] == "conditional query randomization on these fixed episodes"
