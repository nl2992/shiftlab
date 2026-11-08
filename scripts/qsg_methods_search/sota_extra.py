"""SOTA comparator expansion registry (docs/qsg_methods_search/sota_expansion/03_EXPERIMENT_PROTOCOL.md).

Union of every comparator already in the repository plus the 2026-11-06 fidelity ports
(e-SR, Shekhar-Ramdas RCS, label-clock ARW; byte-identical from
origin/claude/shiftlab-methods-strategy-dba13e). EQSDp arm B is imported unchanged from d3_extra.
All published-method entries are adapters (see 02_BASELINE_FIDELITY.md); never report them under
the paper's name alone.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (_SOTA, _SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from d3_extra import EXTRA as _D3
from eqs import EXTRA as _EQS
from han_arw import HanARWDeploymentAdapter
from hurdles import ChallengerGSE, Dwell, HoeffdingLCB, ScaledMargin, WaldLCB
from p1_extra import EXTRA as _P1
from shekhar_ramdas import ShekharRamdasDeploymentAdapter
from shin_esr import TwoSidedESRDeploymentAdapter
from v2_extra import EXTRA as _V2


def _mk(cls, nm, **kw):
    return lambda T, B, cs, cq, a, d, r: cls(T, B, cs, rng=r("EQSD"), name=nm, stake=False, **kw)


def _shekhar(name, stop_rule):
    return lambda T, B, cs, cq, a, d, r: ShekharRamdasDeploymentAdapter(
        T, B, a, rng=r(name), stop_rule=stop_rule, name=name
    )


def _esr(name, **kw):
    return lambda T, B, cs, cq, a, d, r: TwoSidedESRDeploymentAdapter(
        T, B, a, rng=r(name), name=name, **kw
    )


EXTRA = {**_V2, **_EQS, **_D3, **_P1}
# lambda = 0.97 extends the existing p1 hurdle grids (real streams prefer longer memory, M5).
for _g in (0.05, 0.1, 0.2, 0.3):
    EXTRA[f"wald_l0.97_g{_g}"] = _mk(WaldLCB, f"wald_l0.97_g{_g}", lam=0.97, gamma=_g)
for _g in (0.1, 0.2, 0.3, 0.45):
    EXTRA[f"hoef_l0.97_g{_g}"] = _mk(HoeffdingLCB, f"hoef_l0.97_g{_g}", lam=0.97, gamma=_g)
for _k in (0.05, 0.1, 0.2, 0.3):
    EXTRA[f"smarg_l0.97_k{_k}"] = _mk(ScaledMargin, f"smarg_l0.97_k{_k}", lam=0.97, kappa=_k)
for _s in (3, 5, 10, 20):
    EXTRA[f"dwell_l0.97_s{_s}"] = _mk(Dwell, f"dwell_l0.97_s{_s}", lam=0.97, k_streak=_s)
EXTRA.update(
    {
        "shekhar_ramdas_rcs_t3_anyexcl": _shekhar("shekhar_ramdas_rcs_t3_anyexcl", "any_excludes"),
        "han_arw_label_clock": lambda T, B, cs, cq, a, d, r: HanARWDeploymentAdapter(
            T, B, rng=r("han_arw_label_clock")
        ),
        "two_sided_esr_label_clock": _esr("two_sided_esr_label_clock"),
        "esr_rmmbets_fullalpha": _esr("esr_rmmbets_fullalpha", bets="rmm", side_alpha_fraction=1.0),
    }
)

for _l in (1.0, 0.97, 0.9):
    for _g in (0.1, 0.2, 0.3, 0.45):
        EXTRA[f"chalgse_l{_l}_g{_g}"] = _mk(ChallengerGSE, f"chalgse_l{_l}_g{_g}", lam=_l, gamma=_g)

FROZEN = "EQSDp_l0.9_g0.2"
# Fixed (untunable or guarantee-fixed) comparators, evaluated at their registered defaults.
FIXED = [
    "gong_zhang_paid_obs",
    "qiu_delayed_movement",
    "model_picker_adapter",
    "model_selector_causal",
    "online_llm_picker",
    "cams_adapter",
    "variance_min_ipw",
    "discern_style",
    "discern_style+QCE+front",
    "discern_design_floor",
    "discern_design_floor+front",
    "SMCS+retain-incumbent",
    "SMCS+QCE+front",
    "xu_acquisition_only",
    "xu+front_only",
    "gated_deployment",
    "gated_adaptive_range",
    "gated_adaptive_range+front",
    "two_sided_esr_label_clock",
    "esr_rmmbets_fullalpha",
    "shekhar_ramdas_rcs_t3_anyexcl",
    "han_arw_label_clock",
    "QSG",
    "economic_replacement",
    "CONTROL_never_switch",
]
# Tunable families: grid -> one config selected on development streams only.
FAMILIES = {
    "gongT": [k for k in _D3 if k.startswith("gongT_")],
    "upf": [k for k in _P1 if k.startswith("upf_")],
    "wald": [k for k in EXTRA if k.startswith("wald_l")],
    "hoef": [k for k in EXTRA if k.startswith("hoef_l")],
    "smarg": [k for k in EXTRA if k.startswith("smarg_l")],
    "dwell": [k for k in EXTRA if k.startswith("dwell_l")],
    "econF": [k for k in _EQS if k.startswith("econF_")],
    "chalgse": [k for k in EXTRA if k.startswith("chalgse_")],
}
# Configurations previously selected on synthetic development seeds (P1 Stage 1 / D3 / D1).
SYNTH_SELECTED = {
    "gongT": "gongT_w100_m10",
    "upf": "upf_d0.95_m50",
    "wald": "wald_l0.9_g0.2",
    "hoef": "hoef_l0.9_g0.45",
    "smarg": "smarg_l0.9_k0.2",
    "dwell": "dwell_l0.9_s5",
    "econF": "econF_mo5_m5",
    "chalgse": "chalgse_l1.0_g0.2",
}
DEV_POLICIES = [FROZEN, *FIXED, *[k for v in FAMILIES.values() for k in v]]
