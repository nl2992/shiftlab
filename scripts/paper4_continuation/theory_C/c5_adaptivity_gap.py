"""C5: adaptivity gap under IID and full causal safety on small exact cells.

Calendar class = pre-promotion queries allowed only at the B declared slots of a calendar
(opportunity calendar, as in scripts/decompose_switching_calendar_gap.py; skipping a slot is
allowed). Post-promotion continuation is the unrestricted exact belief DP in both classes
(post-promotion queries do not affect first-promotion risk).
Reports, per cell: V_adaptive (IID, causal), best single calendar (IID, causal) and the
calendars attaining them.  Mixtures over calendars are NOT included (they can only lower
V_calendar; see doc).
usage: c5_adaptivity_gap.py OUT.json [CELLSET]   (CELLSET in {small, long}; default small)
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import combinations, product

import shiftlab.paper4.frontier_cuts_fast as fcf
from gamma_lib import gamma_cell, save_refuse_overwrite

ORIGINAL = fcf.FastGame


def calendar_class(calendar):
    slots = frozenset(calendar)

    class CalendarGame(ORIGINAL):
        def choices(self, history):
            remaining = self.config.budget - sum(q for _, q in history)
            time_ = len(history) + 1
            if any(a for a, _ in history):  # post-promotion: unrestricted (not used for risk)
                return tuple(product((0, 1), (0, 1) if remaining else (0,)))
            ok = remaining and time_ in slots
            return tuple(product((0, 1), (0, 1) if ok else (0,)))

    return CalendarGame


def run(cell, calendar=None):
    import gamma_lib

    if calendar is None:
        fcf.FastGame = ORIGINAL
        gamma_lib.FastGame = ORIGINAL
    else:
        cls = calendar_class(calendar)
        fcf.FastGame = cls
        gamma_lib.FastGame = cls
    try:
        r = gamma_cell(*cell, force_fcg=True)
    finally:
        fcf.FastGame = ORIGINAL
        gamma_lib.FastGame = ORIGINAL
    mid = lambda lo, hi: (F(lo) + F(hi)) / 2  # noqa: E731
    return {"V_IID": float(mid(r["L_IID"], r["U_IID"])), "V_causal": float(mid(r["L_causal"], r["U_causal"])),
            "V_IID_width": float(F(r["U_IID"]) - F(r["L_IID"])),
            "V_causal_width": float(F(r["U_causal"]) - F(r["L_causal"]))}


CELLS = {
    "C1_persistent": (5, 2, 1, F(1, 4), F(1, 4), F(1, 20), F(19, 20)),
    "C2_antipersistent": (5, 2, 1, F(9, 10), F(9, 10), F(1, 10), F(9, 10)),
    "P_d2": (5, 2, 2, F(1, 10), F(1, 10), F(1, 10), F(9, 10)),
    "asym_counterexample": (4, 2, 2, F(2, 5), F(1, 20), F(1, 10), F(3, 5), F(0), F(0), F(0)),
    "C3_antipersistent": (6, 3, 1, F(3, 4), F(3, 4), F(1, 20), F(19, 20)),
    "C4_persistent": (6, 3, 1, F(1, 4), F(1, 4), F(1, 20), F(19, 20)),
    "alt_T6_B2": (6, 2, 1, F(1), F(1), F(1, 10), F(9, 10)),
}

LONG_CELLS = {
    "P7_B2_d1_t1_10": (7, 2, 1, F(1, 10), F(1, 10), F(1, 10), F(9, 10)),
    "P7_B2_d2_t1_10": (7, 2, 2, F(1, 10), F(1, 10), F(1, 10), F(9, 10)),
    "P8_B2_d1_t1_20_e1_4": (8, 2, 1, F(1, 20), F(1, 20), F(1, 4), F(3, 4)),
    "A7_B2_d1_t3_4": (7, 2, 1, F(3, 4), F(3, 4), F(1, 20), F(19, 20)),
    "A8_B2_d2_t9_10": (8, 2, 2, F(9, 10), F(9, 10), F(1, 10), F(9, 10)),
    "asym7_B2_d2": (7, 2, 2, F(2, 5), F(1, 20), F(1, 10), F(3, 5), F(0), F(0), F(0)),
}


def main():
    out = sys.argv[1]
    cells = LONG_CELLS if len(sys.argv) > 2 and sys.argv[2] == "long" else CELLS
    started = time.time()
    res = {}
    for name, cell in cells.items():
        T, B = cell[0], cell[1]
        adaptive = run(cell)
        cals = {}
        for cal in combinations(range(1, T + 1), B):
            cals[str(cal)] = run(cell, cal)
        best_iid = min(cals, key=lambda c: cals[c]["V_IID"])
        best_c = min(cals, key=lambda c: cals[c]["V_causal"])
        row = {
            "cell": [str(x) for x in cell],
            "adaptive": adaptive,
            "best_calendar_IID": best_iid, "V_cal_IID": cals[best_iid]["V_IID"],
            "best_calendar_causal": best_c, "V_cal_causal": cals[best_c]["V_causal"],
            "Delta_IID": cals[best_iid]["V_IID"] - adaptive["V_IID"],
            "Delta_causal": cals[best_c]["V_causal"] - adaptive["V_causal"],
            "Gamma_adaptive": adaptive["V_causal"] - adaptive["V_IID"],
            "Gamma_best_calendar": cals[best_c]["V_causal"] - cals[best_iid]["V_IID"],
            "calendars": cals,
        }
        res[name] = row
        print(name, {k: row[k] for k in row if k not in ("calendars", "cell", "adaptive")}, flush=True)
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_C/c5_adaptivity_gap.py",
                                "seconds": time.time() - started, "cells": res})


if __name__ == "__main__":
    main()
