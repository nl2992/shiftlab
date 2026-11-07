"""SOTA sprint validation registry. Registered 2026-11-03 while family screening was running and
BEFORE any candidate was selected or any validation row existed.

Seeds: VAL_SEED_BASE (never used before) with 100 paired seeds per regime; null-safety checks on
NULL_SEEDS seeds at NULL_SEED_BASE. Regimes: the Atlas v2 V_* instances (previously run only with
seed base 2026110399, so these streams are fresh) plus new W_* instances below, whose parameters
differ from every development regime. Primary metric: paired Delta J vs the strongest applicable
published comparator chosen per regime on the same seeds; Holm correction over the regimes a claim
covers. A certified claim additionally requires promotion <= NULL_PROMOTION_BOUND on every null
regime here with the NULL_SEEDS check, and the Wilson 95% upper bound reported.
"""

from __future__ import annotations

from bench import SPRINT_REGIMES, _r

VAL_SEED_BASE = 2026110601
NULL_SEED_BASE = 2026110602
VAL_SEEDS = 100
NULL_SEEDS = 1000

NEW = {
    r.name: r
    for r in [
        _r(
            "W_better_dep_r7",
            "dependence",
            [(0, 0.66)],
            dis=((0, 0.22),),
            rho=0.7,
            tags=("alt", "dep"),
        ),
        _r(
            "W_better_dep_r9",
            "dependence",
            [(0, 0.68)],
            dis=((0, 0.2),),
            rho=0.9,
            tags=("alt", "dep"),
        ),
        _r(
            "W_null_dep_r9",
            "dependence",
            [(0, 0.5)],
            dis=((0, 0.22),),
            rho=0.9,
            tags=("null", "dep"),
        ),
        _r(
            "W_null_dep_r95",
            "dependence",
            [(0, 0.5)],
            dis=((0, 0.25),),
            rho=0.95,
            tags=("null", "dep"),
        ),
        _r(
            "W_worse_dep_r8",
            "dependence",
            [(0, 0.42)],
            dis=((0, 0.2),),
            rho=0.8,
            tags=("null", "dep"),
        ),
        _r(
            "W_late_1000",
            "late",
            [(0, 0.42), (1000, 0.72)],
            dis=((0, 0.22),),
            tags=("alt", "change"),
        ),
        _r("W_reversal_700", "reversal", [(0, 0.68), (700, 0.32)], tags=("change",)),
        _r("W_delay600_better", "delay", [(0, 0.64)], delay=600, tags=("alt",)),
    ]
}
SPRINT_REGIMES.update(NEW)

V_ATLAS = [
    "V_better_a",
    "V_better_b",
    "V_better_c",
    "V_dep_better_r5",
    "V_near",
    "V_bursty",
    "V_null",
    "V_worse",
    "V_null_dep_r5",
    "V_null_dep_r8",
    "V_late_600",
    "V_reversal_1000",
    "V_recurrent",
]
VAL_REGIMES = V_ATLAS + list(NEW)
NULL_REGIMES = [
    "V_null",
    "V_worse",
    "V_null_dep_r5",
    "V_null_dep_r8",
    "W_null_dep_r9",
    "W_null_dep_r95",
    "W_worse_dep_r8",
]
