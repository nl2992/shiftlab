"""RB-DP sandwich [L, U] against the certified exact reference (delay d = 1 cells)."""

from __future__ import annotations

import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from shiftlab.paper4.risk_budget_dp import RBDPConfig, solve

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts/paper4_continuation/theory_C")
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


def _ref(name: str) -> dict:
    if name not in _REF:
        spec = dict(CELLS[name])
        _REF[name] = gamma_cell(d=1, **spec)
    return _REF[name]


def _config(name: str, mode: str) -> RBDPConfig:
    s = CELLS[name]
    return RBDPConfig(
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
        w_step_div=10,
        mode=mode,
    )


@pytest.mark.parametrize("mode", ["causal", "iid"])
@pytest.mark.parametrize("name", list(CELLS))
def test_exact_value_inside_sandwich(name: str, mode: str) -> None:
    ref = _ref(name)
    key = ("L_causal", "U_causal") if mode == "causal" else ("L_IID", "U_IID")
    l_ref, u_ref = float(F(ref[key[0]])), float(F(ref[key[1]]))
    out = solve(_config(name, mode))
    alpha = float(CELLS[name].get("alpha", F(1, 10)))
    print(
        f"\n[{name}/{mode}] ref=[{l_ref:.8f},{u_ref:.8f}] L={out['L']:.8f} U={out['U']:.8f} "
        f"U-L={out['U'] - out['L']:.2e} risk_c={out['risk_causal']:.6f} "
        f"risk_i={out['risk_iid']:.6f} t={out['time_total']:.1f}s"
    )
    assert out["L"] <= u_ref + TOL, "lower bound above the certified exact upper bound"
    assert l_ref <= out["U"] + TOL, "policy beats the certified exact lower bound"
    assert out["L"] <= out["U"] + TOL
    risk = out["risk_causal"] if mode == "causal" else out["risk_iid"]
    assert risk <= alpha + TOL
    assert out["U"] <= out["C0"] + TOL


def test_rejects_delay_other_than_one() -> None:
    with pytest.raises(ValueError):
        RBDPConfig(T=5, B=1, t01=0.5, t10=0.5, e0=0.1, e1=0.9, delay=2)


def test_zero_budget_matches_reference() -> None:
    spec = dict(T=5, B=0, t01=F(3, 4), t10=F(3, 4), e0=F(1, 10), e1=F(9, 10), c=F(0), k=F(1, 10))
    ref = gamma_cell(d=1, **spec)
    cfg = RBDPConfig(
        T=5, B=0, t01=0.75, t10=0.75, e0=0.1, e1=0.9, c=0.0, k=0.1, n_beta=101, w_step_div=10
    )
    out = solve(cfg)
    assert float(F(ref["L_causal"])) <= out["U"] + TOL
    assert out["L"] <= float(F(ref["U_causal"])) + TOL
