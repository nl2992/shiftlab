import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import stage1_policies as sp
import trace_run as tr

ALL = sorted(sp.registry_entries())


def toy_losses(seed=0, T=800, shift=300):
    rng = np.random.default_rng(seed)
    l0 = (rng.random(T) < 0.35).astype(np.int8)
    p1 = np.where(np.arange(T) < shift, 0.40, 0.20)
    l1 = (rng.random(T) < p1).astype(np.int8)
    return np.stack([l0, l1], axis=1)


def run(names, seed=0, budget=200, delay=30):
    return tr.run_policies(names, toy_losses(seed), delay, 0, seed, 77, "toy", budget)


def by_policy(rows):
    return {r["policy"]: r for r in rows}


def test_inert_hooks_equal_arm_r_exactly():
    rows = by_policy(run([tr.ARM_R, "s1base", "s1c1_r0_s0_h0", "s1c5_degenerate"], seed=3))
    ref = rows[tr.ARM_R]
    for k in ("s1base", "s1c1_r0_s0_h0", "s1c5_degenerate"):
        assert rows[k]["net"] == ref["net"], k
        assert rows[k]["labels"] == ref["labels"] and rows[k]["switches"] == ref["switches"], k


@pytest.mark.parametrize("budget", [12, 60])
def test_every_policy_respects_budget(budget):
    for r in run(ALL, seed=1, budget=budget):
        assert r["labels"] <= budget, r["policy"]


def test_deterministic_under_seed():
    names = [sp.c1_name(0.03, 1, 6), sp.c2_name(1000, 50, 0.5), sp.c5_name(0.5, 0.3, 0.05)]
    a, b = run(names, seed=5), run(names, seed=5)
    assert [r["net"] for r in a] == [r["net"] for r in b]
    c = run(names, seed=6)
    assert [r["net"] for r in a] != [r["net"] for r in c]


def test_policies_never_touch_evaluator_fields():
    import ast

    tree = ast.parse((HERE / "stage1_policies.py").read_text(encoding="utf8"))
    bad = {"mean_gain", "oracle", "frac_on_wrong", "better", "labels", "label", "context",
           "l0", "l1", "losses", "regret", "gain"}  # fmt: skip
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not (used & bad), used & bad


def test_c1_counts_inflight_labels_as_pending():
    pol = sp.registry_entries()[sp.c1_name(0.03, 1, 0)](800, 200, 5.0, 0.05, 0.1, 30, _R)
    pol.n, pol.k, pol.t = 40.0, 22.0, 300
    p0 = pol.p_cross(300)
    pol.pending = 12  # twelve in-flight labels widen what can still happen
    assert pol.p_cross(300) >= p0


def test_c1_gate_zero_when_horizon_too_short():
    pol = sp.registry_entries()[sp.c1_name(0.03, 1, 6)](800, 200, 5.0, 0.05, 0.1, 30, _R)
    pol.n, pol.k = 40.0, 22.0
    assert pol.p_cross(790) == 0.0


def _R(name):
    return np.random.default_rng(abs(hash(name)) % 2**31)


def test_inert_wald_stop_equals_reference_wald():
    rows = by_policy(run(["wald_l0.97_g0.2", "s1wald_inert", "s1wald_stop_H300"], seed=2))
    assert rows["s1wald_inert"]["net"] == rows["wald_l0.97_g0.2"]["net"]
    assert rows["s1wald_stop_H300"]["labels"] <= rows["wald_l0.97_g0.2"]["labels"]
