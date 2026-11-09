"""New regime instances for the FLQ two-tier re-test (registered 2026-11-06, before any run).

Parameters differ from every existing F*/V*/W*/O* instance. Importing this module adds them to
``bench.SPRINT_REGIMES`` so ``screen.py`` can run them. See
docs/p2_benchmark/FLQ_TWO_TIER_PROTOCOL.md.
"""

from __future__ import annotations

from bench import SPRINT_REGIMES, _r

NEW = {
    r.name: r
    for r in [
        # Primary efficacy region: stationary or slowly varying improvements.
        _r("N_better_a", "stationary", [(0, 0.63)], dis=((0, 0.20),), tags=("alt",)),
        _r("N_better_b", "stationary", [(0, 0.68)], dis=((0, 0.12),), delay=30, tags=("alt",)),
        _r("N_better_c", "stationary", [(0, 0.60)], dis=((0, 0.35),), delay=150, tags=("alt",)),
        _r(
            "N_dep_better_r6",
            "dependence",
            [(0, 0.65)],
            dis=((0, 0.20),),
            rho=0.6,
            tags=("alt", "dep"),
        ),
        _r("N_near", "near", [(0, 0.56)], dis=((0, 0.30),), tags=("alt",)),
        _r("N_bursty", "budget", [(0, 0.64)], dis=((0, 0.20),), burst=0.85, tags=("alt",)),
        # Tier A (claimed iid conditional null).
        _r("N_null", "stationary", [(0, 0.5)], dis=((0, 0.30),), delay=50, tags=("null",)),
        # Tier B (dependent marginal nulls; outside the claimed null class).
        _r(
            "N_null_dep_r7",
            "dependence",
            [(0, 0.5)],
            dis=((0, 0.25),),
            rho=0.7,
            tags=("null", "dep"),
        ),
        _r(
            "N_null_dep_r9",
            "dependence",
            [(0, 0.5)],
            dis=((0, 0.20),),
            rho=0.9,
            tags=("null", "dep"),
        ),
        # Outside the declared region (reported, no gate).
        _r("N_late_800", "late", [(0, 0.40), (800, 0.68)], tags=("alt", "change")),
        _r("N_reversal_900", "reversal", [(0, 0.68), (900, 0.32)], tags=("change",)),
    ]
}

_clash = sorted(set(NEW) & set(SPRINT_REGIMES))
if _clash:
    raise RuntimeError(f"regime names already registered: {_clash}")
SPRINT_REGIMES.update(NEW)
