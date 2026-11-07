"""Comparators added by the 2026-11-06 SOTA fidelity programme (opt-in, ``extra=`` of ``build_suite``).

Each entry passed retrieve -> independent check -> lead review -> implement -> lead code review; the
records are in ``docs/sota_fidelity/LEDGER.md``. All are T3 common-contract adaptations and must be
reported under these names, never under the paper's name alone. They are kept out of the default
``build_suite`` makers and out of ``bench.ALL_COMPARATORS`` so historical panels are unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

SOTA = Path(__file__).resolve().parents[1] / "promising_directions/sota"
for _p in (SOTA, SOTA / "competitors"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from han_arw import HanARWDeploymentAdapter
from river_page_hinkley import RiverPageHinkleyDeploymentAdapter
from shekhar_ramdas import ShekharRamdasDeploymentAdapter
from shin_esr import TwoSidedESRDeploymentAdapter
from upf_style_switch_timing import make_upf_style_switch_timing

# name -> (display label, null actually tested; same codes as sota_sprint/bench2.NULL_TESTED)
FIDELITY_INFO = {
    "shekhar_ramdas_rcs_t3": (
        "Shekhar-Ramdas RCS, common-contract adapter (T3), paper joint rule",
        "V1 only under i.i.d. label-order pre-change data (joint rule)",
    ),
    "shekhar_ramdas_rcs_t3_anyexcl": (
        "Shekhar-Ramdas RCS, common-contract adapter (T3), any-excludes deviation",
        "V1 (label-order conditional mean of queried disagreement outcomes)",
    ),
    "han_arw_label_clock": ("label-clock ARW, common-contract adapter (T3) [Han+24]", "none"),
    "upf_style_switch_timing_T3": (
        "UPF-style cost-aware switch timing (T3) [after Regol+25; not UPF]",
        "none",
    ),
    "two_sided_esr_label_clock": (
        ("two-sided e-SR (Algorithm 3 bets, start at every label), label clock, common-contract "
         "adapter (T3) [after Shin+24; not the authors' algorithm]"),
        "V1 under the label-order conditional-mean null (rmm_matched finite-horizon calibration)",
    ),
    "river_page_hinkley_t3": (
        "river Page-Hinkley (T1 detector), common-contract adapter (T3)", "none",
    ),
}

# Entries whose underlying package is an optional extra (name -> import name). The adapter module
# imports it lazily, so registration works without it; running the adapter needs `--extra drift`.
OPTIONAL_DEPENDENCY = {"river_page_hinkley_t3": "river"}


def _shekhar(stop_rule):
    def make(T, budget, cs, cq, alpha, delay, r):
        name = "shekhar_ramdas_rcs_t3" + ("_anyexcl" if stop_rule == "any_excludes" else "")
        return ShekharRamdasDeploymentAdapter(T, budget, alpha, rng=r(name), stop_rule=stop_rule,
                                              name=name)
    return make


EXTRA = {
    "shekhar_ramdas_rcs_t3": _shekhar("joint"),
    "shekhar_ramdas_rcs_t3_anyexcl": _shekhar("any_excludes"),
    "han_arw_label_clock": lambda T, budget, cs, cq, alpha, delay, r: HanARWDeploymentAdapter(
        T, budget, rng=r("han_arw_label_clock")),
    "upf_style_switch_timing_T3": make_upf_style_switch_timing,
    "two_sided_esr_label_clock": lambda T, budget, cs, cq, alpha, delay, r: (
        TwoSidedESRDeploymentAdapter(T, budget, alpha, rng=r("two_sided_esr_label_clock"))),
    "river_page_hinkley_t3": lambda T, budget, cs, cq, alpha, delay, r: (
        RiverPageHinkleyDeploymentAdapter(T, budget, rng=r("river_page_hinkley_t3"))),
}
