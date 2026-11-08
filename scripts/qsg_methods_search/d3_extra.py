"""D3 registry: tuned Gong-Zhang grid, EQS-D paced grid, frozen D2 winner, comparators."""

from eqs import EXTRA as _EQS
from eqs_d import EQSD
from eqs_d import EXTRA as _EQSD
from r6_policies import EXTRA as _R6
from r6_policies import GongZhangPaidObsPolicy


class GongTuned(GongZhangPaidObsPolicy):
    def __init__(self, T, budget, delay, cs, rng, name, window, margin):
        super().__init__(T, budget, delay, cs, rng, name)
        self.gamma = 1.0 - 1.0 / window
        self.margin = float(margin)

    def _decide(self, t):
        cs = self.cs
        self.cs = cs + self.margin
        try:
            super()._decide(t)
        finally:
            self.cs = cs


def _gong(nm, w, m):
    return lambda T, B, cs, cq, a, d, r: GongTuned(
        T, B, d, cs, r("GongZhangPaidObsPolicy"), nm, w, m
    )


def _eqsd(nm, **kw):
    return lambda T, B, cs, cq, a, d, r: EQSD(T, B, cs, rng=r("EQSD"), name=nm, **kw)


EXTRA = {}
for _w in (100, 200, 400, 800):
    for _m in (0, 5, 10, 20):
        EXTRA[f"gongT_w{_w}_m{_m}"] = _gong(f"gongT_w{_w}_m{_m}", _w, _m)
for _l in (0.9, 0.95, 0.98):
    for _g in (0.1, 0.2, 0.3, 0.5):
        EXTRA[f"EQSDp_l{_l}_g{_g}"] = _eqsd(f"EQSDp_l{_l}_g{_g}", lam=_l, gamma=_g, stake=False)
EXTRA["EQSD_l0.95_g0.2_pcinf_mf1.0"] = _EQSD["EQSD_l0.95_g0.2_pcinf_mf1.0"]
EXTRA.update({k: _R6[k] for k in ("gong_zhang_paid_obs", "qiu_delayed_movement")})
EXTRA["econF_mo5_m5"] = _EQS["econF_mo5_m5"]
NAMES = list(EXTRA) + ["CONTROL_never_switch"]

# D4 ablation (registered in development_protocol.md §D4): point estimate + additive margin on
# the same label-clock evidence. Isolates quantile hysteresis from the evidence clock.
D4 = {}
for _l in (0.9, 0.95):
    for _m in (5, 10, 20, 40):
        D4[f"EQSDp_l{_l}_g0.5_m{_m}"] = _eqsd(
            f"EQSDp_l{_l}_g0.5_m{_m}", lam=_l, gamma=0.5, stake=False, margin=_m
        )
D4.update(
    {
        k: EXTRA[k]
        for k in (
            "EQSDp_l0.9_g0.2",
            "EQSDp_l0.95_g0.2",
            "gongT_w100_m10",
            "EQSD_l0.95_g0.2_pcinf_mf1.0",
        )
    }
)

# C3 frozen confirmation arm set (synthetic_confirmation_protocol.md)
CONFIRM = {
    k: EXTRA[k]
    for k in (
        "EQSDp_l0.95_g0.2",
        "EQSDp_l0.9_g0.2",
        "gongT_w100_m10",
        "qiu_delayed_movement",
        "gong_zhang_paid_obs",
        "econF_mo5_m5",
        "EQSD_l0.95_g0.2_pcinf_mf1.0",
    )
}
CONFIRM.update({k: D4[k] for k in ("EQSDp_l0.95_g0.5_m10", "EQSDp_l0.95_g0.5_m20")})
