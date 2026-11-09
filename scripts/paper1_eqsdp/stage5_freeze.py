"""Build docs/paper1_eqsdp/16_RECOVERY_FREEZE.json from the even-episode selections (A, B, C).

  python stage5_freeze.py
Writes the JSON only; commit and push it BEFORE running stage5_odd.py (which refuses otherwise).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage5_run as r5
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage5"
FREEZE = ROOT / "docs/paper1_eqsdp/16_RECOVERY_FREEZE.json"


def main():
    sa, sb, sc, sd = (json.loads((OUT / f"selection_{k}.json").read_text()) for k in "ABCD")
    r2 = sa["r2"]
    kw = (r2["hz"], r2["lam0"], r2["cutoff"], r2["rule"])
    cal1, cal2 = sb["r1_control_calendar"], sb["r2_extra_calendar"]
    ent, to = sb["r2_control_entropy"], sc["r3_ablation_tail_only"]
    specs = {
        r2["name"]: r5.r2_spec(*kw),
        sb["r1"]["name"]: r5.r1_spec(sb["r1"]["f"], sb["r1"]["G"], sb["r1"]["cutoff"]),
        cal1["name"]: {"kind": "cal", "m": cal1["m"], "cutoff": cal1["cutoff"]},
        cal2["name"]: {"kind": "cal", "m": cal2["m"], "cutoff": cal2["cutoff"]},
        ent["name"]: {"kind": "r2", "mode": "entropy", "hz": r2["hz"], "cutoff": r2["cutoff"],
                      "theta": ent["theta"], "rule": r2["rule"]},
        sc["r3"]["name"]: r5.r2_spec(*kw, "tail", sc["r3"]["tau"]),
        sd["roll"]["name"]: r5.roll_spec(r2, sd["roll"]["kmax"]),
        to["name"]: r5.r2_spec(*kw, "tail_only", to["tau"]),
    }  # fmt: skip
    fz = {
        "stage": "5 recovery freeze (docs/paper1_eqsdp/15_STAGE3_FAILURE_TRACE_AND_RECOVERY.md section 3)",
        "written": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "contract": {"B": 200, "c_q": 0.05, "c_s": 5, "T": 2000, "policy_seeds": 10,
                     "split": "odd episodes, episode index kept in the seed derivation"},
        "references": {"eqsdp_cutoff": sa["eq_ref"], "wald_cutoff": sa["wald_ref"]},
        "also_run": [tr.ARM_R, "wald_l0.97_g0.2", "s2armr_H1100"],
        "specs": specs,
        "roles": {
            "R1": sb["r1"]["name"], "R1_control_calendar": cal1["name"],
            "R2": r2["name"], "R2_control_entropy": ent["name"], "R2_extra_calendar": cal2["name"],
            "R3": sc["r3"]["name"], "R3_ablation_tail_only": to["name"],
            "R3_ablation_no_tail": r2["name"], "R2_roll": sd["roll"]["name"],
        },
        "selection": {"A": sa, "B": sb, "C": sc, "D": sd},
        "advance_criterion": (
            "odd episodes, vs BOTH references: (1) paired mean dJ < 0 with 95% stratified "
            "episode-bootstrap CI upper end < 0; (2) dL/T <= +0.1 pp; (3) CVaR95 of per-episode "
            "excess cost (regret vs hindsight best fixed model) <= 1.10 x the reference's; "
            "(4) no dataset with paired mean dJ > +1% of that dataset's reference J"
        ),
    }  # fmt: skip
    FREEZE.write_text(json.dumps(fz, indent=1))
    print("wrote", FREEZE)


if __name__ == "__main__":
    main()
