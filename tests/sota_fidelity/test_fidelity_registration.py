"""The 2026-11-06 fidelity comparators build through the common suite and respect the contract."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "scripts/failure_atlas_v2_flq", ROOT / "scripts/sota_sprint"):
    sys.path.insert(0, str(p))

import importlib.util

import bench
from fidelity_extras import EXTRA, FIDELITY_INFO, OPTIONAL_DEPENDENCY
from suite import build_suite, run_metrics


def test_registry_is_opt_in_and_consistent():
    assert list(EXTRA) == bench.FIDELITY_ADAPTERS_20261106 == list(FIDELITY_INFO)
    assert not set(EXTRA) & set(bench.ALL_COMPARATORS)


def test_each_adapter_runs_one_short_episode_within_budget():
    T, B, delay = 400, 40, 20
    rng = np.random.default_rng(0)
    p = np.r_[np.full(T // 2, 0.5), np.full(T - T // 2, 0.2)]
    losses = np.stack([rng.random(T) < 0.5, rng.random(T) < p], axis=1).astype(int)
    gain = 0.5 - p
    # entries backed by an optional extra (river) run only where the package is installed
    names = [n for n in EXTRA if n not in OPTIONAL_DEPENDENCY
             or importlib.util.find_spec(OPTIONAL_DEPENDENCY[n]) is not None]
    pols = build_suite(T, B, 5.0, 0.05, 0.05, delay, 0, 2026110601,
                       names=names, extra=EXTRA)
    assert [pol.name for pol in pols] == names
    for pol in pols:
        m = run_metrics(pol, losses, gain, delay=delay, budget=B, cq=0.05, cs=5.0,
                        stream_rng=np.random.default_rng(1))
        assert m["labels"] <= B
        assert np.isfinite(m["net"])
