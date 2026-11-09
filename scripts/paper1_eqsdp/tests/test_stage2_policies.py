import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import stage1_policies as sp
import stage2_policies as sp2
import stage2_space as sps
import trace_run as tr


def toy_losses(seed=0, T=800, shift=300):
    rng = np.random.default_rng(seed)
    l0 = (rng.random(T) < 0.35).astype(np.int8)
    p1 = np.where(np.arange(T) < shift, 0.40, 0.20)
    l1 = (rng.random(T) < p1).astype(np.int8)
    return np.stack([l0, l1], axis=1)


def run(names, seed=0, budget=200, delay=30):
    rows = tr.run_policies(names, toy_losses(seed), delay, 0, seed, 77, "toy", budget)
    return {r["policy"]: r for r in rows}


def register(name, cfg):
    sp2.DYN[name] = sp2.stage2_factory(cfg, name)


C1 = {"rho0": 0.03, "s": 1.0, "h": 6, "floor": 0.1}


def test_default_equals_stage1_c1():
    register("t_full", dict(C1, bw=1.0, gs=0.0, stop_h=None))
    for seed in (1, 2, 3):
        r = run(["t_full", sp.c1_name(0.03, 1, 6)], seed=seed)
        assert r["t_full"]["net"] == r[sp.c1_name(0.03, 1, 6)]["net"]
        assert r["t_full"]["labels"] == r[sp.c1_name(0.03, 1, 6)]["labels"]


def test_gate_off_equals_stop_only_control():
    register("t_stop", {"rho0": 0.0, "stop_h": 900, "bw": 0.0, "gs": 0.0})
    for seed in (1, 2):
        r = run(["t_stop", "s1c1stop_H900"], seed=seed)
        assert r["t_stop"]["net"] == r["s1c1stop_H900"]["net"]


def test_gate_off_stop_off_equals_arm_r():
    register("t_plain", {"rho0": 0.0, "stop_h": None, "bw": 0.0, "gs": 0.0})
    r = run(["t_plain", tr.ARM_R], seed=4)
    assert r["t_plain"]["net"] == r[tr.ARM_R]["net"]


def test_wald_h_equals_stage1_wald_stop():
    r = run([sp2.wald_name(0.97, 0.2, 1100), "s1wald_stop_H1100"], seed=2)
    assert r[sp2.wald_name(0.97, 0.2, 1100)]["net"] == r["s1wald_stop_H1100"]["net"]


@pytest.mark.parametrize("budget", [12, 60])
def test_budget_respected(budget):
    register("t_g", dict(C1, bw=0.6, gs=1.2, stop_h=1000))
    names = ["t_g", sp2.wald_name(0.97, 0.2, 0, 0.5), sp2.armr_name(1500)]
    for r in run(names, seed=1, budget=budget).values():
        assert r["labels"] <= budget, r["policy"]


def test_deterministic():
    register("t_d", dict(C1, bw=0.6, gs=1.2, stop_h=1000))
    a, b = run(["t_d"], seed=5), run(["t_d"], seed=5)
    assert a["t_d"]["net"] == b["t_d"]["net"]


def test_module_g_changes_belief_only_when_autocorrelated():
    mk = sp2.stage2_factory({"gs": 1.0}, "g")
    pol = mk(800, 200, 5.0, 0.05, 0.1, 30, lambda n: np.random.default_rng(0))
    pol.n, pol.k = 40.0, 28.0
    q_indep = pol._q(0.2)
    pol.r = 0.6
    q_dep = pol._q(0.2)
    assert q_dep < q_indep  # wider posterior pushes the lower quantile down toward 1/2... for p>1/2
    pol.gs = 0.0
    assert pol._q(0.2) == q_indep


def test_module_b_weight_widens_reach_with_pending():
    mk = sp2.stage2_factory({"rho0": 0.03, "s": 1.0, "h": 0, "bw": 1.0}, "b")
    pol = mk(800, 200, 5.0, 0.05, 0.1, 30, lambda n: np.random.default_rng(0))
    pol.n, pol.k, pol.t = 40.0, 22.0, 300
    pol.pending = 12
    p_on = pol.p_cross(300)
    pol.bw = 0.0
    assert p_on >= pol.p_cross(300)


def test_policy_modules_never_touch_evaluator_fields():
    import ast

    bad = {"mean_gain", "oracle", "frac_on_wrong", "better", "labels", "label", "context",
           "l0", "l1", "losses", "regret", "gain"}  # fmt: skip
    tree = ast.parse((HERE / "stage2_policies.py").read_text(encoding="utf8"))
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert not (used & bad), used & bad


def test_space_mapping_covers_toggles_and_ranges():
    lo, hi = sps.to_cfg(np.zeros(sps.DIM)), sps.to_cfg(np.ones(sps.DIM))
    assert lo["rho0"] == 0.0 and lo["bw"] == 0.0 and lo["gs"] == 0.0 and lo["stop_h"] is None
    assert hi["stop_h"] == 1750 and hi["h"] == 12 and abs(hi["rho0"] - 0.2) < 1e-6
    assert 0.95 <= lo["lam"] <= hi["lam"] <= 0.995
    for m in ("B", "G", "stop", "gate"):
        assert sps.ablate(hi, m) != hi


def test_thinned_armr_inert_at_one_and_budgeted():
    r = run([sp2.armr_name(1100, 0.5), sp2.armr_name(1100), "s1c1stop_H1100"], seed=3, budget=30)
    assert r["s2armr_H1100"]["net"] == r["s1c1stop_H1100"]["net"]
    assert r["s2armr_H1100_k0.5"]["labels"] <= 30
