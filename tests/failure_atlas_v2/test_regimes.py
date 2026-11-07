"""Regression tests for the Atlas v2 regime generator (a sign inversion was caught on 2026-11-03)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/failure_atlas_v2"))
from regimes import REGIMES, expected_oracle_path, hindsight_oracle_cost


def test_empirical_gain_matches_truth_sign_and_size():
    for name, r in REGIMES.items():
        L = np.concatenate([r.sample(np.random.default_rng(s)) for s in range(20)])
        g_emp = (L[:, 0] - L[:, 1]).mean()
        g_true = np.tile(r.truth_gain(), 20).mean()
        assert abs(g_emp - g_true) < 0.02, (name, g_emp, g_true)


def test_better_regime_has_positive_gain():
    L = REGIMES["F0_better"].sample(np.random.default_rng(0))
    assert (L[:, 0] - L[:, 1]).mean() > 0.03


def test_oracles():
    L = REGIMES["F1_late_800"].sample(np.random.default_rng(1))
    assert hindsight_oracle_cost(L, 5.0) <= min(L[:, 0].sum(), L[:, 1].sum() + 5.0)
    path = expected_oracle_path(REGIMES["F1_late_800"].truth_gain(), 5.0)
    assert path[:800].sum() == 0 and path[-1] == 1
