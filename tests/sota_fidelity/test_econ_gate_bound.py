"""The hindsight veto-gate DP equals brute force over accept/veto choices."""

import itertools
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_fidelity"))

from econ_gate_bound import best_veto_gate  # noqa: E402


def _brute(desired, cost, cs):
    T = len(desired)
    props = np.flatnonzero(desired != np.r_[0, desired[:-1]])
    best = float("inf")
    for choice in itertools.product([0, 1], repeat=len(props)):
        a, path, sw = 0, np.empty(T, int), 0
        acc = dict(zip(props.tolist(), choice))
        for t in range(T):
            if acc.get(t) and a != desired[t]:
                a, sw = int(desired[t]), sw + 1
            path[t] = a
        best = min(best, cost[np.arange(T), path].sum() + cs * sw)
    return best


def test_dp_matches_brute_force():
    rng = np.random.default_rng(0)
    for _ in range(300):
        T = int(rng.integers(1, 25))
        desired = (rng.random(T) < rng.random()).astype(int)
        cost = rng.normal(size=(T, 2))
        cs = float(rng.uniform(0, 3))
        got, path, nsw = best_veto_gate(desired, cost, cs)
        assert np.isclose(got, _brute(desired, cost, cs))
        # path is feasible and its cost matches the reported value
        assert np.isclose(cost[np.arange(T), path].sum() + cs * nsw, got)
        changes = np.flatnonzero(path != np.r_[0, path[:-1]])
        assert all(desired[t] != (desired[t - 1] if t else 0) and path[t] == desired[t] for t in changes)


def test_gate_never_worse_than_base_or_never():
    rng = np.random.default_rng(1)
    for _ in range(100):
        T = 50
        desired = (rng.random(T) < 0.5).astype(int)
        cost = rng.random((T, 2))
        cs = 0.5
        got, _, _ = best_veto_gate(desired, cost, cs)
        base = cost[np.arange(T), desired].sum() + cs * np.sum(np.diff(np.r_[0, desired]) != 0)
        assert got <= base + 1e-12 and got <= cost[:, 0].sum() + 1e-12
