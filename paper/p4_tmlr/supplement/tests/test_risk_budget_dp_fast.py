"""Fast RB-DP against the reference solver and the certified exact values (delay d = 1 cells)."""

from __future__ import annotations

import dataclasses
import sys
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pytest

from shiftlab.paper4 import risk_budget_dp as ref_mod
from shiftlab.paper4 import risk_budget_dp_fast as fast_mod
from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, solve

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "theory_C")
)
from gamma_lib import gamma_cell  # noqa: E402

TOL = 1e-9
C0, K0 = F(1, 100), F(1, 10)

CELLS = {
    "T5B2_t.9": dict(T=5, B=2, t01=F(9, 10), t10=F(9, 10), e0=F(1, 10), e1=F(9, 10), c=C0, k=K0),
    "T6B3_t.75": dict(T=6, B=3, t01=F(3, 4), t10=F(3, 4), e0=F(1, 20), e1=F(19, 20), c=C0, k=K0),
    "T6B2_free": dict(T=6, B=2, t01=F(3, 4), t10=F(3, 4), e0=F(1, 10), e1=F(9, 10), c=F(0), k=F(0)),
    "T5B1_free": dict(T=5, B=1, t01=F(2, 3), t10=F(2, 3), e0=F(1, 5), e1=F(4, 5), c=F(0), k=F(0)),
    "T5B2_asym": dict(
        T=5, B=2, t01=F(2, 5), t10=F(1, 20), e0=F(1, 10), e1=F(3, 5), prior=F(0), c=F(0), k=F(0)
    ),
    "T7B2_persist": dict(
        T=7, B=2, t01=F(1, 4), t10=F(1, 4), e0=F(1, 10), e1=F(9, 10), c=F(1, 200), k=F(1, 20)
    ),
    "T4B3_alpha.2": dict(
        T=4, B=3, t01=F(1, 2), t10=F(1, 3), e0=F(1, 5), e1=F(4, 5), c=C0, k=K0, alpha=F(1, 5)
    ),
}

_REF: dict[str, dict] = {}
_OLD: dict[tuple[str, str, int], dict] = {}


def _exact(name: str) -> dict:
    if name not in _REF:
        _REF[name] = gamma_cell(d=1, **dict(CELLS[name]))
    return _REF[name]


def _kwargs(name: str, mode: str, w_step_div: int = 10) -> dict:
    s = CELLS[name]
    return dict(
        T=s["T"],
        B=s["B"],
        t01=float(s["t01"]),
        t10=float(s["t10"]),
        e0=float(s["e0"]),
        e1=float(s["e1"]),
        prior1=float(s.get("prior", F(1, 2))),
        c=float(s["c"]),
        k=float(s["k"]),
        alpha=float(s.get("alpha", F(1, 10))),
        n_beta=201,
        w_step_div=w_step_div,
        mode=mode,
    )


def _old(name: str, mode: str, w_step_div: int = 10) -> dict:
    key = (name, mode, w_step_div)
    if key not in _OLD:
        _OLD[key] = ref_mod.solve(ref_mod.RBDPConfig(**_kwargs(name, mode, w_step_div)))
    return _OLD[key]


@pytest.mark.parametrize("mode", ["causal", "iid"])
@pytest.mark.parametrize("name", list(CELLS))
def test_matches_reference_solver_and_exact_value(name: str, mode: str) -> None:
    out = solve(RBDPConfig(check_split=True, **_kwargs(name, mode)))
    old = _old(name, mode)
    # the merge-based split equals the brute-force split at every DP step
    assert out["split_gap"] <= 1e-12
    assert abs(out["U"] - old["U"]) <= TOL
    assert abs(out["L"] - old["L"]) <= TOL
    # and the sandwich still brackets the certified exact value, as in the reference tests
    ref = _exact(name)
    key = ("L_causal", "U_causal") if mode == "causal" else ("L_IID", "U_IID")
    l_ref, u_ref = float(F(ref[key[0]])), float(F(ref[key[1]]))
    assert out["L"] <= u_ref + TOL, "lower bound above the certified exact upper bound"
    assert l_ref <= out["U"] + TOL, "policy beats the certified exact lower bound"
    assert out["L"] <= out["U"] + TOL
    alpha = float(CELLS[name].get("alpha", F(1, 10)))
    risk = out["risk_causal"] if mode == "causal" else out["risk_iid"]
    assert risk <= alpha + TOL
    assert out["U"] <= out["C0"] + TOL


def test_finer_grid_matches_reference_and_tightens() -> None:
    name, mode = "T5B2_t.9", "causal"
    out = solve(RBDPConfig(check_split=True, **_kwargs(name, mode, 20)))
    old = _old(name, mode, 20)
    assert out["split_gap"] <= 1e-12
    assert abs(out["U"] - old["U"]) <= TOL
    assert abs(out["L"] - old["L"]) <= TOL
    assert out["L"] > _old(name, mode, 10)["L"]


def test_compute_flags() -> None:
    kw = _kwargs("T5B2_t.9", "causal")
    full = solve(RBDPConfig(**kw))
    low = solve(RBDPConfig(compute_upper=False, **kw))
    upp = solve(RBDPConfig(compute_lower=False, **kw))
    assert low["L"] == full["L"] and np.isnan(low["U"])
    assert upp["U"] == full["U"] and np.isnan(upp["L"])


def test_config_is_field_compatible_with_reference() -> None:
    ref_fields = {f.name for f in dataclasses.fields(ref_mod.RBDPConfig)}
    fast_fields = {f.name for f in dataclasses.fields(RBDPConfig)}
    assert ref_fields <= fast_fields
    assert fast_fields - ref_fields == {
        "compute_lower",
        "compute_upper",
        "check_split",
        "lattice_exact",
    }


@pytest.mark.parametrize("mode", ["causal", "iid"])
@pytest.mark.parametrize("name", list(CELLS))
def test_lattice_exact_lower_bound_is_tight_and_valid(name: str, mode: str) -> None:
    out = solve(RBDPConfig(lattice_exact=True, **_kwargs(name, mode)))
    ref = _exact(name)
    key = ("L_causal", "U_causal") if mode == "causal" else ("L_IID", "U_IID")
    l_ref, u_ref = float(F(ref[key[0]])), float(F(ref[key[1]]))
    assert out["L"] <= u_ref + TOL, "lattice lower bound above the certified exact upper bound"
    assert l_ref <= out["L"] + TOL, "lattice lower bound below the certified exact value"
    assert out["L"] <= out["U"] + TOL
    assert abs(out["U"] - out["L"]) <= TOL
    assert out["L"] >= solve(RBDPConfig(**_kwargs(name, mode)))["L"] - TOL


@pytest.mark.parametrize("name", ["T6B3_t.75", "T7B2_persist", "T4B3_alpha.2", "T5B2_asym"])
def test_lattice_value_is_invariant_under_refinement(name: str) -> None:
    """Refining the lattice 3x (a different, non-dyadic refinement) does not lower the DP value."""
    for mode in ("causal", "iid"):
        base = RBDPConfig(lattice_exact=True, compute_upper=False, **_kwargs(name, mode))
        n_lat = base.n_w
        alpha = base.alpha
        fine = RBDPConfig(
            **{**_kwargs(name, mode), "w_step_div": round(3 * n_lat * alpha)},
            compute_lower=False,
        )
        assert fine.n_w == 3 * n_lat
        assert abs(solve(fine)["dp_upper_value"] - solve(base)["L"]) <= 1e-12


def test_lattice_denominator() -> None:
    cfg = RBDPConfig(T=3, B=3, t01=0.5, t10=0.5, e0=0.1, e1=0.9, alpha=0.2, lattice_exact=True)
    assert cfg.n_w == 5 * 8
    with pytest.raises(ValueError):
        RBDPConfig(
            T=3, B=1, t01=0.5, t10=0.5, e0=0.1, e1=0.9, alpha=0.123456789, lattice_exact=True
        ).n_w  # noqa: B018


def _convex_rows(rng: np.random.Generator, rows: int, width: int) -> np.ndarray:
    inc = np.sort(
        -(rng.random((rows, width - 1)) ** rng.integers(1, 4)), axis=1
    )  # convex, decreasing
    inc[rng.random(inc.shape) < 0.3] = 0.0  # flat stretches
    inc = np.sort(inc, axis=1)
    return np.concatenate([np.zeros((rows, 1)), np.cumsum(inc, axis=1)], axis=1) + rng.random()


@pytest.mark.parametrize("mode", ["causal", "iid"])
@pytest.mark.parametrize("lower", [False, True])
def test_split_matches_brute_force_on_random_convex_rows(mode: str, lower: bool) -> None:
    rng = np.random.default_rng(7)
    for N in (1, 2, 5, 17, 40):
        cfg = RBDPConfig(
            T=2, B=1, t01=0.5, t10=0.5, e0=0.1, e1=0.9, w_step_div=2, mode=mode, check_split=True
        )
        solver = fast_mod._Solver(cfg)
        solver.N, solver.Nw = N, N + 1
        solver._build_w_tables()
        for _ in range(20):
            A = rng.random((6, 1)) * _convex_rows(rng, 6, N + 1)
            Bm = rng.random((6, 1)) * _convex_rows(rng, 6, N + 1)
            val, arg = solver._split_fast(A, Bm, lower)
            brute, _ = solver._split_brute(A, Bm, lower)
            assert np.abs(val - brute).max() <= 1e-12
            i1, pen = solver.split[lower]
            j = np.arange(N + 1)
            achieved = A[np.arange(6)[:, None], arg] + Bm[np.arange(6)[:, None], i1[j, arg]]
            assert np.abs(achieved - brute).max() <= 1e-12
            assert np.isfinite(pen[j, arg]).all()


def test_hull_matches_reference_hull() -> None:
    rng = np.random.default_rng(3)
    for trial in range(120):
        rows, width = int(rng.integers(1, 6)), int(rng.integers(2, 60))
        f = rng.random((rows, width))
        if trial % 3 == 1:
            f = -np.cumsum(rng.random((rows, width)), axis=1) + (rng.random((rows, width)) < 0.3)
        h0, p0, n0 = ref_mod._lower_hull(f)
        h1, p1, n1 = fast_mod._lower_hull(f)
        assert np.abs(h0 - h1).max() <= 1e-12
        assert (p0 == p1).all() and (n0 == n1).all()
        # the pruning fallback agrees with gift wrapping
        assert (fast_mod._vertices_prune(f) == fast_mod._vertices_march(f, max_steps=0)).all()
        assert (fast_mod._vertices_prune(f) == fast_mod._vertices_march(f, max_steps=2)).all()


def test_rejects_delay_other_than_one() -> None:
    with pytest.raises(ValueError):
        RBDPConfig(T=5, B=1, t01=0.5, t10=0.5, e0=0.1, e1=0.9, delay=2)


def test_start_belief_one_gives_finite_bounds():
    """Regression: beta1 = 1 duplicated the last belief grid point and made L = NaN."""
    import math

    cfg = RBDPConfig(
        T=5, B=2, t01=1.0, t10=0.1, e0=0.1, e1=0.9, prior1=0.0, alpha=0.1, mode="causal", n_beta=201, lattice_exact=True
    )
    out = solve(cfg)
    assert math.isfinite(out["L"]) and out["L"] <= out["U"] + 1e-9
