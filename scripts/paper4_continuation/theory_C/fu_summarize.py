"""Aggregate the follow-up Lemma U grid, static search and Lagrangian-hull checks into one JSON.

usage: fu_summarize.py OUT.json
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter

from gamma_lib import save_refuse_overwrite

D = os.path.join(os.path.dirname(__file__), "../../../docs/paper4_continuation/theory_C")


def main():
    out = sys.argv[1]
    grid = sorted(glob.glob(os.path.join(D, "fu_lemmaU_T*.json")))
    rows = []
    for f in grid:
        rows += [r for r in json.load(open(f))["rows"] if "error" not in r]
    pos = [r for r in rows if r["positive"]]
    static = [r for r in rows if r["cell"]["t01"] == "0" and r["cell"]["t10"] == "0"]
    model_key = lambda r: tuple(r["cell"][k] for k in ("T", "B", "d", "t01", "t10", "e0", "e1", "prior"))  # noqa: E731
    pos_models = Counter(model_key(r) for r in pos)
    smallest = min(pos, key=lambda r: (r["cell"]["T"], r["cell"]["B"], -r["Gamma_lo_f"]))
    largest = max(pos, key=lambda r: r["Gamma_lo_f"])
    hull = {}
    for fam in ("static", "sympersist", "mixed"):
        f = os.path.join(D, f"fu_lagrangian_monotone_{fam}.json")
        if os.path.exists(f):
            rr = json.load(open(f))["rows"]
            uniq = {tuple(r["cell"]): r for r in rr}
            hull[fam] = {"unique_cells": len(uniq), "premise_z": sum(r["premise_z"] for r in uniq.values()),
                         "premise_tape": sum(r["premise_tape"] for r in uniq.values()),
                         "failures": [c for c, r in uniq.items() if not r["premise_z"]]}
    st = json.load(open(os.path.join(D, "fu_static_s31.json")))
    payload = {
        "script": "scripts/paper4_continuation/theory_C/fu_summarize.py",
        "grid_files": [os.path.basename(f) for f in grid],
        "grid_cells": len(rows), "grid_positive": len(pos),
        "grid_positive_with_M_marg": sum(r["M_marg"] for r in pos),
        "grid_positive_with_M_cond": sum(r["M_cond"] for r in pos),
        "grid_M_marg_cells": sum(r["M_marg"] for r in rows),
        "grid_M_cond_cells": sum(r["M_cond"] for r in rows),
        "grid_M_violated_cells": sum(not r["M_marg"] for r in rows),
        "grid_symmetric_persistent_cells": sum(
            r["cell"]["t01"] == r["cell"]["t10"] and r["cell"]["t01"] != "0" and r["cell"]["e0"] == "1/10"
            and r["cell"]["e1"] == "9/10" and r["cell"]["prior"] == "1/2" for r in rows),
        "grid_static_cells": len(static), "grid_static_positive": sum(r["positive"] for r in static),
        "grid_max_Gamma_hi_nonpositive": max(r["Gamma_hi_f"] for r in rows if not r["positive"]),
        "positive_models": [list(k) + [v] for k, v in pos_models.most_common()],
        "smallest_positive": smallest, "largest_positive": largest,
        "static_search": {k: st[k] for k in ("n_run", "n_positive", "n_M_violated", "n_iid_vertex_unsafe",
                                             "max_Gamma_hi")},
        "lagrangian_hull": hull,
    }
    save_refuse_overwrite(out, payload)
    print(json.dumps({k: v for k, v in payload.items() if k not in ("positive_models",)}, indent=1,
                     default=str)[:4000])
    print("positive models:", payload["positive_models"])


if __name__ == "__main__":
    main()
