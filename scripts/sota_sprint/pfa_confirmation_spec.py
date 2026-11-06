"""Fresh validation regimes registered for the PFA-SR deployment-transfer screen."""

from __future__ import annotations

from bench import SPRINT_REGIMES, _r

NEW = {
    r.name: r
    for r in [
        _r("PFA_confirm_persistent", "persistent", [(0, 0.68)], dis=((0, 0.25),), tags=("alt",)),
        _r("PFA_confirm_near", "near", [(0, 0.57)], dis=((0, 0.25),), tags=("alt",)),
        _r(
            "PFA_confirm_delay_scarce",
            "delayed",
            [(0, 0.67)],
            dis=((0, 0.22),),
            delay=400,
            tags=("alt", "delay"),
        ),
        _r("PFA_confirm_null", "null", [(0, 0.5)], dis=((0, 0.25),), tags=("null",)),
    ]
}
SPRINT_REGIMES.update(NEW)
