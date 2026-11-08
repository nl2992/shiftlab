"""Post-confirmation comparator panel registry (comparator_panel_protocol.md)."""

from d3_extra import EXTRA as _D3
from hurdles import Dwell, HoeffdingLCB, ScaledMargin, WaldLCB
from upf_style_switch_timing import make_upf_style_switch_timing


def _mk(cls, nm, **kw):
    return lambda T, B, cs, cq, a, d, r: cls(T, B, cs, rng=r("EQSD"), name=nm, stake=False, **kw)


def _upf(nm, **kw):
    return lambda T, B, cs, cq, a, d, r: make_upf_style_switch_timing(
        T, B, cs, cq, a, d, r, name=nm, **kw
    )


TUNE = {}
for _l in (0.9, 0.95):
    for _g in (0.05, 0.1, 0.2, 0.3):
        TUNE[f"wald_l{_l}_g{_g}"] = _mk(WaldLCB, f"wald_l{_l}_g{_g}", lam=_l, gamma=_g)
    for _g in (0.1, 0.2, 0.3, 0.45):
        TUNE[f"hoef_l{_l}_g{_g}"] = _mk(HoeffdingLCB, f"hoef_l{_l}_g{_g}", lam=_l, gamma=_g)
    for _k in (0.05, 0.1, 0.2, 0.3):
        TUNE[f"smarg_l{_l}_k{_k}"] = _mk(ScaledMargin, f"smarg_l{_l}_k{_k}", lam=_l, kappa=_k)
    for _s in (3, 5, 10, 20):
        TUNE[f"dwell_l{_l}_s{_s}"] = _mk(Dwell, f"dwell_l{_l}_s{_s}", lam=_l, k_streak=_s)
for _d in (0.5, 0.8, 0.95):
    for _m in (50, 100, 200):
        TUNE[f"upf_d{_d}_m{_m}"] = _upf(f"upf_d{_d}_m{_m}", delta=_d, m=_m)

REF = {
    k: _D3[k]
    for k in ("EQSDp_l0.95_g0.2", "EQSDp_l0.9_g0.2", "gongT_w100_m10", "qiu_delayed_movement")
}
EXTRA = {**TUNE, **REF}
FAMILIES = ("wald", "hoef", "smarg", "dwell", "upf")
