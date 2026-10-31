"""Wrapper to run a betting_on_predictions main with reduced pool size / repetitions.
Usage: python bop_run.py <repo_dir> <main.py relative> <procs> <reps> [<seed_offset> <results_subdir>]
Rewrites only, in memory (repo files untouched): `processes=130` -> procs; `"num_of_repititions": 500` -> reps;
optionally adds `"initial_seed": seed_offset` to every config (distinct seeds per rep chunk) and redirects
`results/simulations/` -> `results/<results_subdir>/` (one dir per chunk, merged by full_merge.py).
Stubs the `tabpfn` import (only needed by the health-care experiment, not run here)."""

import os
import re
import sys
import types

repo, mod, procs, reps = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
seed_offset = int(sys.argv[5]) if len(sys.argv) > 5 else None
subdir = sys.argv[6] if len(sys.argv) > 6 else None
# tabpfn is only used by the Section-7 health-care experiment; stub it so algs.py imports
# (NOT installed: avoids a model download). Pool workers re-import this module under spawn, so the stub is set at module level.
os.chdir(repo)
sys.path.insert(0, repo)
_t = types.ModuleType("tabpfn")
_t.TabPFNClassifier = object
sys.modules["tabpfn"] = _t
if __name__ == "__main__":
    with open(os.path.join(repo, mod), encoding="utf8") as source_file:
        src = source_file.read()
    src = src.replace("processes=130", f"processes={procs}")
    extra = f', "initial_seed": {seed_offset}' if seed_offset is not None else ""
    src = re.sub(r'"num_of_repititions":\s*\d+', f'"num_of_repititions": {reps}{extra}', src)
    if subdir:
        src = src.replace("results/simulations/", f"results/{subdir}/")
    exec(compile(src, mod, "exec"), {"__name__": "__main__", "__file__": os.path.join(repo, mod)})  # noqa: S102 - Execute the explicitly selected experiment entry point.
