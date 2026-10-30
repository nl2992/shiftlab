"""Regression tests for the novelty-validation programme (CPU-sized, deterministic)."""
import importlib.util, itertools, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
SC = ROOT / "research/novelty_validation_2026-10-30/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SC / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_h2c_reduces_to_cost_only_kelly_when_guided_by_itself():
    """Exact reduction: guiding with the tested statistic itself reproduces plain discounted Kelly."""
    x1 = load("x1_guidance_mechanism"); x1.Q = 0.1
    assert x1.identity_test() < 1e-12


def test_guidance_does_not_change_validity_in_null_worlds():
    """Counterexample regression: misleading Brier shift under a flat cost null keeps false alarms below alpha."""
    x1 = load("x1_guidance_mechanism"); x1.Q = 0.2
    r = x1.run("misleading null", 0.10, 0.30, 0.8, S=600, seed=11)
    assert r["h2c_false"] < 0.05 and r["cost_only_false"] < 0.05


def test_guidance_is_harmful_when_brier_opposes_cost():
    """Counterexample regression: cost up, Brier down => H2c power collapses relative to cost-only Kelly."""
    x1 = load("x1_guidance_mechanism"); x1.Q = 0.2
    r = x1.run("opposed", 0.13, 0.12, 0.8, S=600, seed=12)
    assert r["h2c_power"] + 0.03 < r["cost_only_power"]


def test_joint_dp_never_worse_than_separate_and_b0_equals_no_query():
    x2 = load("x2_joint_vs_separate_dp")
    for D in (0, 1):
        r = x2.instance(6, 0.5, 1.0, 0.05, 2, 0.9, 0.85, D)
        assert r["J"] <= min(r["S_ol"], r["S_us"], r["S_vo"], r["S_nq"], r["S_inc"]) + 1e-9
    j0 = x2.solve(6, 0.5, 1.0, 0.05, 0, 0.9, 0.85, 0)
    assert abs(j0 - x2.solve(6, 0.5, 1.0, 0.05, 0, 0.9, 0.85, 1)) < 1e-12  # no queries => delay is irrelevant
