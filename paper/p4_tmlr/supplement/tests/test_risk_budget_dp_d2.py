"""d = 2 RB-DP against the certified exact reference (gamma_cell, d = 2) and hand-checkable cases."""

from __future__ import annotations

import sys
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import linprog

from shiftlab.paper4.risk_budget_dp_d2 import RBDP2Config, _hull2, solve

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "theory_C")
)
from gamma_lib import gamma_cell  # noqa: E402

TOL = 1e-9
Z = F(0)


def cell(T, B, t01, t10, e0, e1, prior=F(1, 2), c=Z, k=Z, alpha=F(1, 10)):
    return dict(T=T, B=B, t01=t01, t10=t10, e0=e0, e1=e1, prior=prior, c=c, k=k, alpha=alpha)


CELLS = {
    "known_T4B2_asym": cell(4, 2, F(2, 5), F(1, 20), F(1, 10), F(3, 5), prior=Z),
    "anti_2/3_costs": cell(6, 2, F(2, 3), F(2, 3), F(1, 10), F(9, 10), c=F(1, 100), k=F(1, 20)),
    "anti_3/4_free": cell(7, 3, F(3, 4), F(3, 4), F(1, 10), F(9, 10)),
    "anti_9/10_hard": cell(
        7, 3, F(9, 10), F(9, 10), F(1, 10), F(19, 20), prior=Z, c=F(1, 100), alpha=F(1, 5)
    ),
    "persist_1/4_costs": cell(
        7, 2, F(1, 4), F(1, 4), F(1, 10), F(9, 10), prior=F(1, 3), c=F(1, 200), k=F(1, 20)
    ),
    "persist_1/10_free": cell(6, 3, F(1, 10), F(1, 10), F(1, 5), F(4, 5), alpha=F(1, 5)),
    "asym_19/20_7/10": cell(
        7, 3, F(19, 20), F(7, 10), F(1, 4), F(9, 10), k=F(1, 20), alpha=F(1, 5)
    ),
    "premium_cell": cell(
        7, 3, F(4, 5), F(3, 4), F(3, 20), F(19, 20), prior=F(1, 3), k=F(1, 20), alpha=F(1, 5)
    ),
    "B1_anti_3/4": cell(5, 1, F(3, 4), F(3, 4), F(1, 10), F(9, 10), c=F(1, 100), k=F(1, 20)),
    "B0_prior1": cell(5, 0, F(3, 4), F(3, 4), F(1, 10), F(9, 10), prior=F(1), k=F(1, 20)),
}

_REF: dict[str, dict] = {}


def ref(name: str) -> dict:
    if name not in _REF:
        _REF[name] = gamma_cell(d=2, **CELLS[name])
    return _REF[name]


def run(name: str, mode: str, n_w: int) -> dict:
    s = CELLS[name]
    return solve(
        RBDP2Config(
            T=s["T"], B=s["B"], t01=float(s["t01"]), t10=float(s["t10"]), e0=float(s["e0"]),
            e1=float(s["e1"]), prior1=float(s["prior"]), c=float(s["c"]), k=float(s["k"]),
            alpha=float(s["alpha"]), n_w_override=n_w, mode=mode,
        )
    )  # fmt: skip


def exact_bounds(name: str, mode: str) -> tuple[float, float]:
    g = ref(name)
    key = "IID" if mode == "iid" else "causal"
    return float(F(g["L_" + key])), float(F(g["U_" + key]))


def lattice_n(name: str) -> int:
    s = CELLS[name]
    return s["alpha"].denominator * 2 ** s["B"]


@pytest.mark.parametrize("mode", ["iid", "causal"])
@pytest.mark.parametrize("name", list(CELLS))
def test_dyadic_lattice_matches_exact(name, mode):
    """At N = d_alpha * 2^B the solver reproduces the certified optimum (observed, not proved)."""
    r = run(name, mode, lattice_n(name))
    lo, hi = exact_bounds(name, mode)
    own_risk = r["risk_iid"] if mode == "iid" else r["risk_causal"]
    alpha = float(CELLS[name]["alpha"])
    assert own_risk <= alpha + TOL
    assert r["U"] >= lo - TOL  # a feasible policy cannot beat the optimum
    assert r["U"] <= r["C0"] + TOL
    assert r["U"] <= r["dp_value"] + TOL  # merged policy is no worse than the table value
    assert abs(r["U"] - hi) <= TOL, (name, mode, r["U"], hi)


@pytest.mark.parametrize("mode", ["iid", "causal"])
@pytest.mark.parametrize("name", list(CELLS))
def test_coarse_grid_gap_bounded_by_step(name, mode):
    """Coarse N = 2 d_alpha: feasible, never below the optimum, gap <= 0.25 / N (envelope observed
    on 130 random cells: worst 0.011 at N = 10, i.e. about one grid step times a unit cost slope)."""
    n_w = 2 * CELLS[name]["alpha"].denominator
    r = run(name, mode, n_w)
    lo, hi = exact_bounds(name, mode)
    own_risk = r["risk_iid"] if mode == "iid" else r["risk_causal"]
    assert own_risk <= float(CELLS[name]["alpha"]) + TOL
    assert r["U"] >= lo - TOL
    assert r["U"] <= r["C0"] + TOL
    assert r["U"] - hi <= 0.25 / n_w


def test_known_cell_certified_values():
    iid = run("known_T4B2_asym", "iid", 20)
    cau = run("known_T4B2_asym", "causal", 20)
    assert iid["U"] == pytest.approx(8379231 / 5000000, abs=1e-12)
    assert cau["U"] == pytest.approx(523743 / 312500, abs=1e-12)
    assert iid["risk_causal"] > 0.1 + 1e-6  # the IID optimum is not causal-safe
    assert cau["risk_causal"] <= 0.1 + TOL


def test_premium_cell_positive_and_reproduced():
    g = ref("premium_cell")
    assert g["Gamma_positive_certified"]
    n_w = lattice_n("premium_cell")
    gamma = run("premium_cell", "causal", n_w)["U"] - run("premium_cell", "iid", n_w)["U"]
    assert gamma == pytest.approx(float(F(g["Gamma_lo"])), abs=1e-9)


def test_hand_checkable_B1():
    """T=3, B=1, frozen state S ~ Bern(1/2), e=(1/10, 9/10), no costs.

    Only a query at t=1 is informative (released before t=3). Unconstrained: cost 1/2 + 1/2 +
    (1/2)(0.18) + (1/2)(0.18) = 1.18. With alpha = 1/10 the learner promotes after label 1 with
    probability q = 1/5 (null risk q/2 = alpha): 1 + 1/2 - 0.32 q... = 1.436 in both modes.
    """
    for mode in ("causal", "iid"):
        kw = dict(T=3, B=1, t01=0.0, t10=0.0, e0=0.1, e1=0.9, prior1=0.5, mode=mode)
        free = solve(RBDP2Config(alpha=1.0, w_step_div=2, **kw))
        assert free["U"] == pytest.approx(1.18, abs=1e-12)
        con = solve(RBDP2Config(alpha=0.1, w_step_div=1, **kw))
        assert con["U"] == pytest.approx(1.436, abs=1e-12)
        assert con["dp_value"] == pytest.approx(1.436, abs=1e-12)
        assert con["risk_causal"] == pytest.approx(0.1, abs=1e-12)
        assert con["C0"] == pytest.approx(1.5)


def test_B0_matches_reference_and_uses_no_queries():
    r = run("B0_prior1", "causal", 20)
    lo, hi = exact_bounds("B0_prior1", "causal")
    assert abs(r["U"] - hi) <= TOL
    assert r["risk_causal"] <= 0.1 + TOL
    assert r["U"] < r["C0"] - 1e-6  # with prior 1 an unlabeled promotion pays


def test_uniform_belief_grid_is_feasible_and_close():
    """Interpolated belief grid: still exact-evaluated, still feasible, small gap."""
    s = CELLS["known_T4B2_asym"]
    cfg = RBDP2Config(
        T=s["T"], B=s["B"], t01=0.4, t10=0.05, e0=0.1, e1=0.6, prior1=0.0, alpha=0.1,
        n_w_override=20, mode="causal", belief_grid="uniform", n_beta=201,
    )  # fmt: skip
    r = solve(cfg)
    lo, hi = exact_bounds("known_T4B2_asym", "causal")
    assert r["risk_causal"] <= 0.1 + TOL
    assert lo - TOL <= r["U"] <= hi + 2e-3


@pytest.mark.parametrize("seed", range(4))
def test_hull2_matches_lp(seed):
    """2-D grid hull equals the min over mixtures (LP) and is below f, on random data and on
    degenerate (constant, planar) data."""
    rng = np.random.default_rng(seed)
    n = 4
    f = rng.random((n + 1, n + 1)) if seed < 2 else np.full((n + 1, n + 1), 0.3) + 0.1 * seed
    if seed == 3:
        f = 0.5 - 0.1 * np.add.outer(np.arange(n + 1), 2 * np.arange(n + 1)) / n
    h = _hull2(f).table
    assert np.all(h <= f + 1e-12)
    ii, jj = np.meshgrid(np.arange(n + 1), np.arange(n + 1), indexing="ij")
    pts = np.column_stack([ii.ravel(), jj.ravel()]).astype(float)
    for a in range(n + 1):
        for b in range(n + 1):
            res = linprog(
                f.ravel(),
                A_eq=np.vstack([pts.T, np.ones(len(pts))]),
                b_eq=[a, b, 1.0],
                bounds=(0, None),
                method="highs",
            )
            assert h[a, b] == pytest.approx(res.fun, abs=1e-9)
