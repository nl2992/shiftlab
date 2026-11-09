"""Stage 5 even-episode (selection) runner.

  python stage5_run.py A      # F0 reference grids + R2 grid (+ quantile-rule pilot)
  python stage5_run.py B      # needs outputs/paper1_eqsdp/stage5/selection_A.json (from stage5_analysis.py A)
  python stage5_run.py C      # needs selection_B.json: R3 grid, tail-only grid
Odd episodes are run only by stage5_odd.py (refuses to start without a pushed freeze commit).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage5_eval as e5
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage5"
H_GRID = (900, 1100, 1300)
EQ_NAMES = [tr.ARM_R] + [f"s2armr_H{h}" for h in H_GRID]
WALD_LG = [(lam, g) for lam in (0.97, 0.98) for g in (0.2, 0.3)]
WALD_NAMES = [f"wald_l{lam}_g{g}" for lam, g in WALD_LG] + [
    f"s2wald_l{lam}_g{g}_H{h}" for lam, g in WALD_LG for h in H_GRID
]
R2_HZ, R2_LAM0, R2_CUT = (1e-4, 5e-4, 2e-3), (0.0, 0.05), (1100, None)
CAL_M = (10, 15, 20, 25, 30, 40, 50, 60, 80, 100, 130, 160, 200)
ENT_THETA = tuple(
    round(x, 2) for x in (0.6, 1.0, 1.4, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.4, 3.6)
)
R1_F, R1_G = (0.1, 0.2, 0.3), (50, 100, 200)
TAU = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0)


def cut_tag(c):
    return "none" if c is None else str(c)


def r2_name(hz, lam0, cut, rule="mean", mode="evsi", tau=None):
    base = f"s5{mode}_h{hz:g}_l{lam0:g}_c{cut_tag(cut)}"
    base += "" if rule == "mean" else f"_{rule}"
    return base + ("" if tau is None else f"_t{tau:g}")


def r2_spec(hz, lam0, cut, rule="mean", mode="evsi", tau=1.0):
    return {"kind": "r2", "mode": mode, "hz": hz, "lam0": lam0, "cutoff": cut, "rule": rule,
            "tau": tau}  # fmt: skip


def r1_name(f, g, cut):
    return f"s5r1_f{f:g}_G{g}_c{cut_tag(cut)}"


def r1_spec(f, g, cut):
    return {"kind": "r1", "f": f, "gap": g, "cutoff": cut}


def cal_name(m, cut):
    return f"s5cal_m{m}_c{cut_tag(cut)}"


def ent_name(hz, cut, theta):
    return f"s5ent_h{hz:g}_c{cut_tag(cut)}_th{theta:g}"


def specs_A():
    sp = {}
    for hz in R2_HZ:
        for lam0 in R2_LAM0:
            for cut in R2_CUT:
                sp[r2_name(hz, lam0, cut)] = r2_spec(hz, lam0, cut)
    for cut in R2_CUT:  # pilot: arm R's own quantile rule inside the preposterior
        sp[r2_name(5e-4, 0.0, cut, "quantile")] = r2_spec(5e-4, 0.0, cut, "quantile")
    return sp


def main():
    which = sys.argv[1]
    d = OUT / "even"
    if which == "A":
        names = [*EQ_NAMES, "wald_l0.97_g0.2", *WALD_NAMES]
        names = list(dict.fromkeys(names))
        e5.run_specs(names, specs_A(), "even", d / "A")
    elif which == "B":
        sel = json.loads((OUT / "selection_A.json").read_text())
        hstar, r2 = sel["eq_cutoff"], sel["r2"]
        sp = {}
        for f in R1_F:
            for g in R1_G:
                sp[r1_name(f, g, hstar)] = r1_spec(f, g, hstar)
        for m in CAL_M:
            sp[cal_name(m, hstar)] = {"kind": "cal", "m": m, "cutoff": hstar}
        for th in ENT_THETA:
            sp[ent_name(r2["hz"], r2["cutoff"], th)] = {
                "kind": "r2", "mode": "entropy", "hz": r2["hz"], "cutoff": r2["cutoff"],
                "theta": th, "rule": r2["rule"],
            }  # fmt: skip
        for m in CAL_M:  # calendars for the R2 cutoff too (extra control for R2 label count)
            sp.setdefault(
                cal_name(m, r2["cutoff"]), {"kind": "cal", "m": m, "cutoff": r2["cutoff"]}
            )
        e5.run_specs([], sp, "even", d / "B")
    elif which == "C":
        sel = json.loads((OUT / "selection_A.json").read_text())
        r2 = sel["r2"]
        sp = {}
        for tau in TAU:
            for mode in ("tail", "tail_only"):
                sp[r2_name(r2["hz"], r2["lam0"], r2["cutoff"], r2["rule"], mode, tau)] = r2_spec(
                    r2["hz"], r2["lam0"], r2["cutoff"], r2["rule"], mode, tau
                )
        e5.run_specs([], sp, "even", d / "C")
    else:
        raise SystemExit("A | B | C")


if __name__ == "__main__":
    main()
