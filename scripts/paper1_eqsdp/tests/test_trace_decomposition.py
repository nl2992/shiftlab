import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import trace_run as tr


@pytest.mark.parametrize("p_better", [0.2, 0.8])
def test_decompose_sums_exactly_random_paths(p_better):
    rng = np.random.default_rng(1)
    for _ in range(200):
        T = 200
        l0 = (rng.random(T) < 0.3 + 0.2 * (1 - p_better)).astype(int)
        l1 = (rng.random(T) < 0.3 + 0.2 * p_better).astype(int)
        dep = np.cumsum(rng.random(T) < 0.03) % 2
        n = int(rng.integers(0, 50))
        d = tr.decompose(dep, l0, l1, n)
        assert abs(d["gap"]) < 1e-9
        assert abs(sum(d[k] for k in tr.COMPONENTS) - d["regret"]) < 1e-9
        assert d["regret"] == pytest.approx(d["net"] - min(l0.sum(), l1.sum()))


def test_decompose_known_cases():
    l0 = np.array([1, 1, 1, 0, 0, 0])
    l1 = np.zeros(6, dtype=int)  # challenger better by 3
    d = tr.decompose([0, 0, 1, 1, 1, 1], l0, l1, 2)
    assert d["late_adoption"] == 2 and d["residual"] == 5 and d["reversal_churn"] == 0
    assert d["label_spend"] == pytest.approx(0.1) and d["false_promotion"] == 0
    z = np.zeros(6, dtype=int)
    d = tr.decompose([1, 1, 0, 0, 1, 1], z, np.array([1, 1, 0, 0, 1, 1]), 0)
    assert d["false_promotion"] == 9 and d["reversal_churn"] == 10 and d["regret"] == 19
    assert abs(d["gap"]) < 1e-9


def test_toy_run_matches_simulator_and_sums():
    rng = np.random.default_rng(3)
    T = 400
    base = rng.random(T)
    losses = np.stack([base < 0.4, base < 0.2], axis=1).astype(np.int8)
    for name in ("wald_l0.9_g0.2", "EQSDp_l0.98_g0.3", "CONTROL_never_switch"):
        (row,) = tr.run_policies([name], losses, 5, 0, 0, 123, "toy", 20, check_orig=(name,))
        assert row["net_orig"] == row["net"]
        total = sum(row[k] for k in tr.COMPONENTS)
        assert total == pytest.approx(row["regret"], abs=1e-9)
