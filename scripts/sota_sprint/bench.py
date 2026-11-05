"""SOTA sprint frozen benchmark specification (Agent E). Registered 2026-11-03 before any sprint run.

Contract: T=2000, B=200, c_q=.05, c_s=5, alpha=.05, common simulator, paired streams.
Development screening uses seed base DEV_SEED_BASE (never used before). Validation seeds and the
validation regime set are registered separately, after screening and before any validation run.

Regimes: the locked Atlas v2 FLQ discovery registry (F0-F9) plus sprint additions below, which
target conditions the earlier atlas covered thinly (strong dependence under an alternative, very
long delay, very late change, short transient, early reversal, rare-observation null). A regime
name may carry ``@B<budget>`` to run that regime at another hard budget (budget-tightness axis).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLQ = ROOT / "scripts/failure_atlas_v2_flq"
if str(FLQ) not in sys.path:
    sys.path.insert(0, str(FLQ))

from regimes import ALL_REGIMES, Regime, _r  # noqa: E402

CONTRACT = dict(T=2000, budget=200, cq=0.05, cs=5.0, alpha=0.05)
DEV_SEED_BASE = 2026110501
DEV_SEEDS = 20
# Registered null-safety bound: Wilson-style upper tolerance used in Atlas v2 Amendment 2 for 100
# seeds at nominal .05. Point estimates on 20 dev seeds are screening diagnostics only.
NULL_PROMOTION_BOUND = 0.0936

SPRINT_ADDITIONS: dict[str, Regime] = {r.name: r for r in [
    _r("S_dep_better_r95", "dependence", [(0, 0.65)], rho=0.95, tags=("alt", "dep")),
    _r("S_dep_better_r8_d25", "dependence", [(0, 0.65)], dis=((0, 0.25),), rho=0.8,
       tags=("alt", "dep")),
    _r("S_delay800_better", "delay", [(0, 0.65)], delay=800, tags=("alt",)),
    _r("S_late_1500", "late", [(0, 0.4), (1500, 0.75)], tags=("alt", "change")),
    _r("S_transient_short", "transient", [(0, 0.45), (600, 0.75), (900, 0.45)],
       tags=("change",)),
    _r("S_reversal_400", "reversal", [(0, 0.7), (400, 0.3)], tags=("change",)),
    _r("S_rare_null", "rare", [(0, 0.5)], dis=((0, 0.03),), tags=("null",)),
]}

SPRINT_REGIMES: dict[str, Regime] = {**ALL_REGIMES, **SPRINT_ADDITIONS}


def parse_regime(name: str) -> tuple[Regime, int | None]:
    """``F0_better@B100`` -> (regime, 100); plain name -> (regime, None)."""
    base, _, b = name.partition("@B")
    return SPRINT_REGIMES[base], (int(b) if b else None)


# Comparator classes. These names describe comparator provenance and target, not exact author-code
# fidelity; see docs/promising_directions/sota/SOTA_IMPLEMENTATION_VALIDATION.md. A published
# certificate must itself address the paired deployment null. Xu's paper controls prediction-set
# risk; our Xu adapter combines its acquisition component with ShiftLab's own certificate, so Xu
# belongs in ACQUISITION_ADAPTERS rather than this class.
REGISTERED_CERTIFIED_PUBLISHED = [
    "gated_deployment", "gated_adaptive_range", "gated_adaptive_range+front",
    "discern_style", "discern_design_floor", "SMCS+retain-incumbent", "xu_acquisition_only",
]
CERTIFIED_PUBLISHED = [p for p in REGISTERED_CERTIFIED_PUBLISHED if p != "xu_acquisition_only"]
ACQUISITION_ADAPTERS = ["xu_acquisition_only"]
# Fast online selectors, whose native objective does not itself certify the paired deployment null.
UNCERTIFIED_PUBLISHED = [
    "model_picker_adapter", "model_selector_causal", "online_llm_picker", "cams_adapter",
    "cams_max_adapter",
    "variance_min_ipw", "gong_zhang_paid_obs", "qiu_delayed_movement", "ryabchenko_capacity",
]
INTERNAL = ["P7s_settled", "QSG", "QSG-env8", "gated_deployment+QCE+front", "rmm:gated_deployment+RMM",
            "rmm:LRMD"]
CONTROLS = ["CONTROL_never_switch", "economic_replacement"]
ALL_COMPARATORS = CERTIFIED_PUBLISHED + ACQUISITION_ADAPTERS + UNCERTIFIED_PUBLISHED + INTERNAL + CONTROLS

# A cheap comparator panel for 20-seed screening (strongest of each class on Atlas v2 evidence).
SCREEN_PANEL = ["CONTROL_never_switch", "gated_adaptive_range", "gated_adaptive_range+front",
                "discern_style", "discern_design_floor", "SMCS+retain-incumbent",
                "xu_acquisition_only", "model_picker_adapter", "cams_adapter", "cams_max_adapter",
                "model_selector_causal", "economic_replacement", "QSG", "QSG-env8",
                "rmm:gated_deployment+RMM", "rmm:LRMD", "P7s_settled"]

# Development screening environments (each candidate uses >= 4: two targeted, one null/adverse,
# one outside its advantage region). Families choose from this list; nothing else is screened.
DEV_ENVS = [
    "F0_better", "F0_null", "F0_worse", "F1_late_800", "F1_late_1200", "F2_transient",
    "F3_reversal_800", "F4_recurrent", "F5_dep_null_r8", "F5_dep_better_r8", "F5_dep_null_r95",
    "F6_delay400_better", "F7_near_better", "F8_rare_better", "F9_bursty_better",
    "F9_highdis_better", *SPRINT_ADDITIONS, "F0_better@B100", "F0_better@B400",
]
